"""
Scoring logic for Active Inference agent
Implements simplified active inference: balance goal value, info gain, and cost
"""
import math
import config


def entropy(p: float) -> float:
    """
    Calculate entropy for a Bernoulli distribution with parameter p.

    Entropy measures uncertainty:
    - H(p) = 0 when p=0 or p=1 (certain)
    - H(p) is maximum at p=0.5 (maximally uncertain)

    Args:
        p: Probability in [0, 1]

    Returns:
        Entropy value in [0, 1] (using log base 2)
    """
    # Handle boundary cases to avoid log(0)
    if p <= 0.0 or p >= 1.0:
        return 0.0

    q = 1.0 - p

    # Entropy = -p*log2(p) - q*log2(q)
    return -(p * math.log2(p) + q * math.log2(q))


def expected_goal_value(skill_name: str, p_unlocked: float) -> float:
    """
    Calculate expected goal value for a skill given current belief.

    Goal value represents how likely the skill is to achieve the objective
    (escaping the room) and how good/bad that outcome is.

    Args:
        skill_name: Name of the skill
        p_unlocked: Current belief that door is unlocked (0 to 1)

    Returns:
        Expected value (can be positive or negative)
    """
    if skill_name == "peek_door":
        # Peeking doesn't directly achieve the goal
        return 0.0

    elif skill_name == "try_door":
        # Expected value = p(success) * reward - p(failure) * penalty
        # If door unlocked: escape (positive)
        # If door locked: get stuck (negative)
        p_locked = 1.0 - p_unlocked
        return (p_unlocked * config.REWARD_ESCAPE -
                p_locked * config.PENALTY_FAIL)

    elif skill_name == "go_window":
        # Window always works, but has a slow penalty
        return config.REWARD_ESCAPE - config.SLOW_PENALTY

    else:
        # Unknown skill: default to 0
        return 0.0


def expected_info_gain(skill_name: str, p_unlocked: float) -> float:
    """
    Calculate expected information gain for a skill.

    Information gain measures how much a skill reduces uncertainty
    about hidden state.

    Args:
        skill_name: Name of the skill
        p_unlocked: Current belief that door is unlocked (0 to 1)

    Returns:
        Expected information gain (0 or more)
    """
    if skill_name == "peek_door":
        # Peeking directly observes door state
        # Info gain = current entropy (will be resolved after observation)
        return entropy(p_unlocked)

    elif skill_name == "try_door":
        # Trying door could give info if it fails, but we model as pure action
        # (Conservative: assume primary purpose is acting, not sensing)
        return 0.0

    elif skill_name == "go_window":
        # Window doesn't provide info about door state
        return 0.0

    else:
        # Unknown skill: no info gain
        return 0.0


def score_skill(skill: dict, p_unlocked: float,
                alpha: float = None, beta: float = None, gamma: float = None) -> float:
    """
    Score a skill using active inference principles.

    Score = α * ExpectedGoalValue + β * ExpectedInfoGain - γ * Cost

    This captures the core active inference trade-off:
    - Exploitation: pursue high goal value
    - Exploration: pursue high information gain
    - Efficiency: avoid high costs

    Args:
        skill: Dictionary with keys 'name', 'cost', etc.
        p_unlocked: Current belief that door is unlocked
        alpha: Weight for goal value (default from config)
        beta: Weight for information gain (default from config)
        gamma: Weight for cost (default from config)

    Returns:
        Overall score (higher is better)
    """
    # Use config defaults if not specified
    if alpha is None:
        alpha = config.ALPHA
    if beta is None:
        beta = config.BETA
    if gamma is None:
        gamma = config.GAMMA

    skill_name = skill.get("name", "unknown")
    cost = skill.get("cost", 1.0)

    goal = expected_goal_value(skill_name, p_unlocked)
    info = expected_info_gain(skill_name, p_unlocked)

    score = alpha * goal + beta * info - gamma * cost

    return score


# Utility function for debugging/verbose mode
def score_skill_detailed(skill: dict, p_unlocked: float,
                         alpha: float = None, beta: float = None, gamma: float = None) -> dict:
    """
    Score a skill and return detailed breakdown.

    Returns:
        Dictionary with score components
    """
    if alpha is None:
        alpha = config.ALPHA
    if beta is None:
        beta = config.BETA
    if gamma is None:
        gamma = config.GAMMA

    skill_name = skill.get("name", "unknown")
    cost = skill.get("cost", 1.0)

    goal = expected_goal_value(skill_name, p_unlocked)
    info = expected_info_gain(skill_name, p_unlocked)
    total = alpha * goal + beta * info - gamma * cost

    return {
        "skill_name": skill_name,
        "p_unlocked": p_unlocked,
        "goal_value": goal,
        "info_gain": info,
        "cost": cost,
        "weighted_goal": alpha * goal,
        "weighted_info": beta * info,
        "weighted_cost": gamma * cost,
        "total_score": total
    }


if __name__ == "__main__":
    # Quick manual test
    print("=== Scoring Module Test ===\n")

    # Test entropy
    print("Entropy at different belief values:")
    for p in [0.0, 0.2, 0.5, 0.8, 1.0]:
        print(f"  p={p:.1f}: H={entropy(p):.3f}")

    print("\nSkill scores at p_unlocked=0.5 (uncertain):")
    skills = [
        {"name": "peek_door", "cost": 1.0},
        {"name": "try_door", "cost": 1.5},
        {"name": "go_window", "cost": 2.0}
    ]
    for skill in skills:
        details = score_skill_detailed(skill, 0.5)
        print(f"  {skill['name']:12s}: score={details['total_score']:6.2f} "
              f"(goal={details['weighted_goal']:5.2f}, "
              f"info={details['weighted_info']:5.2f}, "
              f"cost={details['weighted_cost']:5.2f})")

    print("\nSkill scores at p_unlocked=0.9 (confident unlocked):")
    for skill in skills:
        details = score_skill_detailed(skill, 0.9)
        print(f"  {skill['name']:12s}: score={details['total_score']:6.2f} "
              f"(goal={details['weighted_goal']:5.2f}, "
              f"info={details['weighted_info']:5.2f}, "
              f"cost={details['weighted_cost']:5.2f})")

    print("\nSkill scores at p_unlocked=0.1 (confident locked):")
    for skill in skills:
        details = score_skill_detailed(skill, 0.1)
        print(f"  {skill['name']:12s}: score={details['total_score']:6.2f} "
              f"(goal={details['weighted_goal']:5.2f}, "
              f"info={details['weighted_info']:5.2f}, "
              f"cost={details['weighted_cost']:5.2f})")
