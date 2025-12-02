"""
Silver-gauge scoring helpers for the Neo-MacGyver demo.

This module does **not** replace the existing active-inference scoring.
Instead it wraps the existing `scoring.score_skill_detailed(...)`
and compresses the components (goal, information gain, cost) into a
small set of **Pythagorean mean**-based invariants:

  - HM  (harmonic mean)  — "series / bottleneck" view
  - GM  (geometric mean) — "balanced / multiplicative" view
  - AM  (arithmetic mean) — "simple average" view

The pattern is:

  1. Use the existing active-inference logic to compute:
     - goal_value        (expected goal contribution)
     - info_gain         (expected information gain)
     - cost              (action cost)
     - total_score       (α·goal + β·info − γ·cost)

  2. Wrap these three numbers in simple Pythagorean means to get a
     **shape-aware stamp** of the decision:
     - HM/GM/AM over (goal, info)   → exploration "shape"
     - HM/GM/AM over (goal+info, cost) → efficiency "shape"

  3. Return a small dictionary (the *silver stamp*) that can be
     attached to a Step node as JSON. This makes the decision policy
     introspectable and gives you something you can query in Neo4j
     later without changing the baseline behaviour of the agent.

Why is this called "silver"?
-----------------------------
In the larger metrology work this innovation is from, we treat
Pythagorean means + small rational fields as a kind of "silver gauge"
– a way of summarising trade-offs (here: goal vs information vs cost)
in a very compact, algebraic form.

For this demo you don't need any of the heavy metrology background.
You just need to know that:

  - We NEVER change the original active-inference score here.
    The agent can still pick actions based on the existing scalar
    `total_score` that comes from `scoring.py`.

  - The silver stamp is **additional structure** that we log on each
    Step so we can visualise and analyse behaviour later.

  - All of the maths is simple, well-behaved, and positive-domain
    (means are only applied to non-negative numbers).

You can safely ignore this file if you only care about behaviour,
but it's a very nice extra talking point when you want to show
"this isn't just a toy – we can also *measure* the trade-offs in a
principled way".
"""

from __future__ import annotations

import math
from typing import Dict, Any

# We reuse the existing detailed scoring as our input
from scoring import score_skill_detailed, entropy


def _ensure_positive(x: float, eps: float = 1e-9) -> float:
    """Clamp a value into the non-negative domain and add a tiny epsilon.

    The Pythagorean means expect strictly positive inputs. We:
      - clamp negatives to 0
      - add a small epsilon so 0 → eps (avoiding division by zero)
    """
    return max(0.0, float(x)) + eps


def harmonic_mean(a: float, b: float) -> float:
    """Harmonic mean of two positive numbers.

    HM is naturally suited to "bottleneck" or "series" situations,
    and strongly down-weights imbalanced pairs (1 and 100 → ~1.98).
    """
    a = _ensure_positive(a)
    b = _ensure_positive(b)
    return 2.0 / (1.0 / a + 1.0 / b)


def geometric_mean(a: float, b: float) -> float:
    """Geometric mean of two positive numbers.

    GM is the natural "balanced" mean for multiplicative trade-offs.
    It sits between HM and AM and is invariant under common scaling.
    """
    a = _ensure_positive(a)
    b = _ensure_positive(b)
    return math.sqrt(a * b)


def arithmetic_mean(a: float, b: float) -> float:
    """Simple arithmetic mean of two positive numbers."""
    a = _ensure_positive(a)
    b = _ensure_positive(b)
    return 0.5 * (a + b)


def build_silver_stamp(skill_name: str, cost: float, p_unlocked: float) -> Dict[str, Any]:
    """Build a *silver gauge* stamp for a single skill at a given belief.

    Inputs
    ------
    skill_name:
        Name of the skill (e.g. "peek_door", "try_door", "go_window").
    cost:
        Cost value stored on the Skill node (used by the baseline scoring).
    p_unlocked:
        Current belief that the door is unlocked, in [0, 1].

    What this does
    --------------
    1. Calls the existing detailed scoring function to get:
         - goal_value, info_gain, cost, total_score, etc.

    2. Converts goal/info/cost into strictly positive numbers so we
       can safely feed them into the means (we work with magnitudes).

    3. Computes two small Pythagorean-mean bundles:

         (A) Exploration shape    – between |goal| and info
         (B) Efficiency shape     – between (|goal|+info) and cost

       Each bundle gives us HM/GM/AM for that pair.

    4. Derives two dimensionless *shape coefficients* in [0, 1]:

         k_explore  ~ how balanced goal vs info are
         k_efficiency ~ how friendly the goal+info is relative to cost

       These are derived as GM/AM ratios (1.0 = perfectly balanced).

    5. Returns a dictionary that can be JSON-encoded and stored as
       `Step.silver_stamp` in the graph. We also include a
       `silver_score` field which is just a lightly-rescaled version
       of the baseline total score – so you can plot it if you like,
       but the baseline behaviour is preserved.

    This function is *pure* – no database access, no side effects.
    """
    # 1) Baseline detailed scoring from existing module
    skill = {"name": skill_name, "cost": cost}
    details = score_skill_detailed(skill, p_unlocked)

    # Raw components
    goal_raw = float(details["goal_value"])         # may be negative
    info_raw = float(details["info_gain"])          # non-negative in this demo
    cost_raw = float(details["cost"])               # non-negative
    goal_sign = -1.0 if goal_raw < 0 else (1.0 if goal_raw > 0 else 0.0)

    # Weighted (policy-aligned) components
    wg_raw = float(details.get("weighted_goal", goal_raw))
    wi_raw = float(details.get("weighted_info", info_raw))
    wc_raw = float(details.get("weighted_cost", cost_raw))

    # Protect means with positive-domain clamp (use magnitudes)
    g = _ensure_positive(abs(goal_raw))
    i = _ensure_positive(max(0.0, info_raw))
    c = _ensure_positive(max(0.0, cost_raw))
    wg = _ensure_positive(abs(wg_raw))
    wi = _ensure_positive(max(0.0, wi_raw))
    wc = _ensure_positive(max(0.0, wc_raw))

    # --- Exploration bundle: goal vs information ---
    hm_gi = harmonic_mean(g, i)
    gm_gi = geometric_mean(g, i)
    am_gi = arithmetic_mean(g, i)

    # Exploration shape coefficient in [0, 1].
    # - High when goal and info are comparable
    # - Low when one dominates (very unbalanced)
    k_explore = gm_gi / am_gi if am_gi > 0 else 0.0

    # --- Exploration bundle (weighted): |weighted_goal| vs weighted_info ---
    hm_wg_wi = harmonic_mean(wg, wi)
    gm_wg_wi = geometric_mean(wg, wi)
    am_wg_wi = arithmetic_mean(wg, wi)
    k_explore_balance = gm_wg_wi / am_wg_wi if am_wg_wi > 0 else 0.0

    # --- Efficiency bundle (weighted): (value = wg+wi) vs wc ---
    value = _ensure_positive(wg + wi)
    hm_value_cost = harmonic_mean(value, wc)
    gm_value_cost = geometric_mean(value, wc)
    am_value_cost = arithmetic_mean(value, wc)

    # Balance/tension (knife-edge): high when value and cost are comparable
    k_eff_balance = gm_value_cost / am_value_cost if am_value_cost > 0 else 0.0

    # ROI/advantage: high when value comfortably exceeds cost (monotone)
    k_eff_roi = float(value / (value + wc)) if (value + wc) > 0 else 0.0

    # Backwards-compatible alias
    k_efficiency = k_eff_balance

    # Base entropy (uncertainty) at this belief, for reference
    H = entropy(p_unlocked)

    # We DO NOT change the core decision scalar, but we provide
    # a slightly rescaled "silver_score" which compresses the
    # exploration/efficiency shape into a single multiplier.
    base_score = details["total_score"]
    # Use exploration balance and ROI as preview multiplier
    shape_multiplier = 0.5 * (k_explore_balance + k_eff_roi)  # in [0, 1]
    silver_score = base_score * (0.5 + 0.5 * shape_multiplier)

    return {
        "stamp_version": "silver_v2",
        "skill_name": skill_name,
        "p_unlocked": float(p_unlocked),
        # Entropy for reference
        "entropy": float(H),
        # Raw components (keep originals)
        "goal_value": float(goal_raw),
        "goal_sign": float(goal_sign),
        "info_gain": float(info_raw),
        "cost": float(cost_raw),
        # Weighted components for analysis
        "weighted_goal": float(wg_raw),
        "weighted_info": float(wi_raw),
        "weighted_cost": float(wc_raw),
        "base_score": float(base_score),
        # Pythagorean means – exploration (raw)
        "hm_goal_info": float(hm_gi),
        "gm_goal_info": float(gm_gi),
        "am_goal_info": float(am_gi),
        # Pythagorean means – exploration (weighted)
        "hm_wgoal_winfo": float(hm_wg_wi),
        "gm_wgoal_winfo": float(gm_wg_wi),
        "am_wgoal_winfo": float(am_wg_wi),
        # Pythagorean means – efficiency (weighted)
        "hm_value_cost": float(hm_value_cost),
        "gm_value_cost": float(gm_value_cost),
        "am_value_cost": float(am_value_cost),
        # Backwards-compat: provide old efficiency mean keys based on raw (goal+info, cost)
        # so existing tools/tests continue to work.
        "hm_goalinfo_cost": float(harmonic_mean(_ensure_positive(g + i), c)),
        "gm_goalinfo_cost": float(geometric_mean(_ensure_positive(g + i), c)),
        "am_goalinfo_cost": float(arithmetic_mean(_ensure_positive(g + i), c)),
        # Dimensionless shape coefficients
        "k_explore": float(k_explore),
        "k_explore_balance": float(k_explore_balance),
        "k_eff_balance": float(k_eff_balance),
        "k_eff_roi": float(k_eff_roi),
        "k_efficiency": float(k_efficiency),
        # Softly rescaled score (does NOT affect behaviour unless you choose to)
        "silver_score": float(silver_score),
    }
