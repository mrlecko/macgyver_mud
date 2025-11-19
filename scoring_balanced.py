"""
Balanced scoring for multi-objective skills.

This module extends the base scoring to handle "balanced" skills that
provide BOTH goal value AND information gain simultaneously.

The key difference from base scoring:
- Base skills: pure specialists (goal XOR info)
- Balanced skills: genuine multi-objective (goal AND info)

This creates k_explore ∈ [0.3, 0.7] instead of k_explore ≈ 0.
"""

from typing import Dict, Any
from scoring import entropy, expected_goal_value, expected_info_gain
import config

# Use config values for weights
ALPHA = config.ALPHA
BETA = config.BETA
GAMMA = config.GAMMA


def score_balanced_skill_detailed(skill: Dict[str, Any], p_unlocked: float) -> Dict[str, Any]:
    """
    Score a balanced skill that provides both goal value AND information gain.

    Args:
        skill: Skill dict with 'name', 'cost', 'goal_fraction', 'info_fraction'
        p_unlocked: Current belief that door is unlocked

    Returns:
        Dict with detailed scoring breakdown
    """
    skill_name = skill["name"]
    cost = skill["cost"]

    # Get the fractions from skill metadata
    goal_frac = skill.get("goal_fraction", 0.5)
    info_frac = skill.get("info_fraction", 0.5)

    # Compute base components
    # For balanced skills, we use fractions of the pure skill values

    if skill_name == "probe_and_try":
        # Combines try_door goal + peek_door info
        base_goal = expected_goal_value("try_door", p_unlocked)
        base_info = expected_info_gain("peek_door", p_unlocked)
        goal = goal_frac * base_goal
        info = info_frac * base_info

    elif skill_name == "informed_window":
        # Combines go_window goal + peek_door info
        base_goal = expected_goal_value("go_window", p_unlocked)
        base_info = expected_info_gain("peek_door", p_unlocked)
        goal = goal_frac * base_goal
        info = info_frac * base_info

    elif skill_name == "exploratory_action":
        # High on both dimensions
        base_goal = max(expected_goal_value("try_door", p_unlocked),
                       expected_goal_value("go_window", p_unlocked))
        base_info = expected_info_gain("peek_door", p_unlocked)
        goal = goal_frac * base_goal
        info = info_frac * base_info

    elif skill_name == "adaptive_peek":
        # Balanced between peek and try
        base_goal = expected_goal_value("try_door", p_unlocked)
        base_info = expected_info_gain("peek_door", p_unlocked)
        goal = goal_frac * base_goal
        info = info_frac * base_info

    else:
        # Fallback: generic balanced skill
        base_goal = expected_goal_value("try_door", p_unlocked)
        base_info = expected_info_gain("peek_door", p_unlocked)
        goal = goal_frac * base_goal
        info = info_frac * base_info

    # Active inference score
    total_score = ALPHA * goal + BETA * info - GAMMA * cost

    return {
        "skill_name": skill_name,
        "p_unlocked": p_unlocked,
        "goal_value": goal,
        "info_gain": info,
        "cost": cost,
        "goal_component": ALPHA * goal,
        "info_component": BETA * info,
        "cost_component": GAMMA * cost,
        "total_score": total_score,
        "entropy": entropy(p_unlocked),
        # Additional metadata
        "goal_fraction": goal_frac,
        "info_fraction": info_frac,
        "skill_kind": "balanced"
    }


def demonstrate_balanced_vs_crisp():
    """
    Demonstrate the difference in k_explore between crisp and balanced skills.
    """
    from scoring import score_skill_detailed
    from scoring_silver import build_silver_stamp

    print("=" * 70)
    print("BALANCED vs CRISP SKILLS: k_explore Comparison")
    print("=" * 70)
    print()

    # Test at p=0.5 (maximum uncertainty)
    p = 0.5
    print(f"Belief: p(unlocked) = {p}\n")

    print("CRISP SKILLS (Pure Specialists):")
    print("-" * 70)
    crisp_skills = [
        ("peek_door", 1.0),
        ("try_door", 1.5),
        ("go_window", 2.0)
    ]

    for name, cost in crisp_skills:
        stamp = build_silver_stamp(name, cost, p)
        print(f"{name:20} k_explore={stamp['k_explore']:.4f}  "
              f"goal={stamp['goal_value']:6.2f}  info={stamp['info_gain']:.3f}")

    print("\nBALANCED SKILLS (Multi-Objective):")
    print("-" * 70)

    # Manually compute balanced skill stamps
    balanced_skills = [
        {"name": "probe_and_try", "cost": 2.0, "goal_fraction": 0.6, "info_fraction": 0.4},
        {"name": "informed_window", "cost": 2.2, "goal_fraction": 0.8, "info_fraction": 0.3},
        {"name": "exploratory_action", "cost": 2.5, "goal_fraction": 0.7, "info_fraction": 0.7},
        {"name": "adaptive_peek", "cost": 1.3, "goal_fraction": 0.4, "info_fraction": 0.6}
    ]

    for skill in balanced_skills:
        details = score_balanced_skill_detailed(skill, p)

        # Compute silver metrics manually
        from scoring_silver import geometric_mean, arithmetic_mean, _ensure_positive

        g = _ensure_positive(abs(details["goal_value"]))
        i = _ensure_positive(details["info_gain"])
        c = _ensure_positive(details["cost"])

        gm_gi = geometric_mean(g, i)
        am_gi = arithmetic_mean(g, i)
        k_explore = gm_gi / am_gi if am_gi > 0 else 0.0

        gm_gc = geometric_mean(g + i, c)
        am_gc = arithmetic_mean(g + i, c)
        k_efficiency = gm_gc / am_gc if am_gc > 0 else 0.0

        print(f"{skill['name']:20} k_explore={k_explore:.4f}  "
              f"goal={details['goal_value']:6.2f}  info={details['info_gain']:.3f}  "
              f"k_efficiency={k_efficiency:.3f}")

    print("\n" + "=" * 70)
    print("INSIGHT: Balanced skills have k_explore ∈ [0.3, 0.7]")
    print("         Crisp skills have k_explore ≈ 0.0")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_balanced_vs_crisp()
