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
In the larger metrology work this demo plugs into, we treat
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

    goal = abs(details["goal_value"])      # magnitude of goal contribution
    info = max(0.0, details["info_gain"]) # info is already >=0 in this demo
    cost_val = max(0.0, details["cost"])

    # Protect means with positive-domain clamp
    g = _ensure_positive(goal)
    i = _ensure_positive(info)
    c = _ensure_positive(cost_val)

    # --- Exploration bundle: goal vs information ---
    hm_gi = harmonic_mean(g, i)
    gm_gi = geometric_mean(g, i)
    am_gi = arithmetic_mean(g, i)

    # Exploration shape coefficient in [0, 1].
    # - High when goal and info are comparable
    # - Low when one dominates (very unbalanced)
    k_explore = gm_gi / am_gi if am_gi > 0 else 0.0

    # --- Efficiency bundle: (goal+info) vs cost ---
    g_plus_i = _ensure_positive(g + i)
    hm_gc = harmonic_mean(g_plus_i, c)
    gm_gc = geometric_mean(g_plus_i, c)
    am_gc = arithmetic_mean(g_plus_i, c)

    # Efficiency coefficient: high when goal+info comfortably beats cost
    k_efficiency = gm_gc / am_gc if am_gc > 0 else 0.0

    # Base entropy (uncertainty) at this belief, for reference
    H = entropy(p_unlocked)

    # We DO NOT change the core decision scalar, but we provide
    # a slightly rescaled "silver_score" which compresses the
    # exploration/efficiency shape into a single multiplier.
    base_score = details["total_score"]
    shape_multiplier = 0.5 * (k_explore + k_efficiency)  # in [0, 1]
    silver_score = base_score * (0.5 + 0.5 * shape_multiplier)

    return {
        "stamp_version": "silver_v1",
        "skill_name": skill_name,
        "p_unlocked": float(p_unlocked),
        # Original components
        "goal_value": float(details["goal_value"]),
        "info_gain": float(details["info_gain"]),
        "cost": float(details["cost"]),
        "base_score": float(base_score),
        # Pythagorean means – exploration
        "hm_goal_info": float(hm_gi),
        "gm_goal_info": float(gm_gi),
        "am_goal_info": float(am_gi),
        # Pythagorean means – efficiency
        "hm_goalinfo_cost": float(hm_gc),
        "gm_goalinfo_cost": float(gm_gc),
        "am_goalinfo_cost": float(am_gc),
        # Dimensionless shape coefficients
        "k_explore": float(k_explore),
        "k_efficiency": float(k_efficiency),
        # Entropy at this belief (for reference)
        "entropy": float(H),
        # Softly rescaled score (does NOT affect behaviour unless you choose to)
        "silver_score": float(silver_score),
    }
