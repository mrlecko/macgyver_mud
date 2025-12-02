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
        base = config.REWARD_ESCAPE - config.SLOW_PENALTY
        # In robust mode, treat window as a fallback to encourage multi-step planning
        if config.ENABLE_ROBUST_SCENARIO:
            base -= 2.0
        return base
    elif config.ENABLE_ROBUST_SCENARIO and skill_name in {"search_key", "disable_alarm", "jam_door", "try_door_stealth"}:
        p_locked = 1.0 - p_unlocked
        if skill_name == "search_key":
            return 0.5  # enables unlock path
        if skill_name == "disable_alarm":
            return 0.2  # reduces risk
        if skill_name == "jam_door":
            return -0.1  # may backfire
        if skill_name == "try_door_stealth":
            return (p_unlocked * config.REWARD_ESCAPE -
                    p_locked * config.PENALTY_FAIL * 0.5)

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
        info = entropy(p_unlocked)
        if config.ENABLE_ROBUST_SCENARIO:
            # Damp peeking in robust mode to encourage multi-step strategies
            info *= 0.5
        return info

    elif skill_name == "try_door":
        # Trying door could give info if it fails, but we model as pure action
        # (Conservative: assume primary purpose is acting, not sensing)
        return 0.0

    elif skill_name == "go_window":
        # Window doesn't provide info about door state
        return 0.0
    elif config.ENABLE_ROBUST_SCENARIO and skill_name in {"search_key", "disable_alarm", "jam_door", "try_door_stealth"}:
        if skill_name == "search_key":
            return entropy(p_unlocked) * 0.5
        if skill_name == "disable_alarm":
            return 0.1
        if skill_name == "jam_door":
            return entropy(p_unlocked) * 0.2
        if skill_name == "try_door_stealth":
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


# ============================================================================
# Memory-Influenced Scoring (Procedural Memory Integration)
# ============================================================================

def score_skill_with_memory(skill: dict, p_unlocked: float,
                           skill_stats: dict = None,
                           context: dict = None,
                           memory_weight: float = 0.5,
                           epistemic_bonus: float = 0.0) -> tuple:
    """
    Score skill using both theoretical model and empirical memory.

    Combines active inference (theory) with procedural memory (experience).

    Args:
        skill: Skill dict with 'name', 'cost'
        p_unlocked: Current belief probability
        skill_stats: Historical performance from get_skill_stats()
        context: Context dict (e.g., belief_category)
        memory_weight: How much to weight empirical data (0-1)
        epistemic_bonus: Exploration bonus for underexplored skills

    Returns:
        Tuple of (final_score, explanation_dict)
    """
    # Base theoretical score from active inference
    theoretical_score = score_skill(skill, p_unlocked)

    # If no memory or insufficient data, return theory plus any epistemic bonus
    if not skill_stats or skill_stats["overall"]["uses"] == 0:
        final_score = theoretical_score + epistemic_bonus
        return final_score, {
            "theoretical_score": theoretical_score,
            "memory_bonus": 0.0,
            "confidence": 0.0,
            "final_score": final_score,
            "epistemic_bonus": epistemic_bonus,
            "reasoning": (
                f"Theory: {theoretical_score:.2f} | "
                f"No memory | Explore: {epistemic_bonus:+.2f} | "
                f"Final: {final_score:.2f}"
            )
        }

    # Select appropriate stats based on context
    if context and "belief_context" in skill_stats:
        # Use context-specific stats if available and confident
        if skill_stats["belief_context"]["confidence"] > 0.3:
            relevant_stats = skill_stats["belief_context"]
            context_type = "context-specific"
        else:
            # Fall back to overall if context data is sparse
            relevant_stats = skill_stats["overall"]
            context_type = "overall (sparse context)"
    else:
        relevant_stats = skill_stats["overall"]
        context_type = "overall"

    success_rate = relevant_stats["success_rate"]
    confidence = relevant_stats["confidence"]
    uses = relevant_stats["uses"]

    # Calculate memory bonus
    # Map success_rate [0,1] to bonus range [-3, +3]
    # Scale by confidence (more data = trust more)
    raw_bonus = (success_rate - 0.5) * 6.0  # [-3, +3]
    memory_bonus = raw_bonus * confidence * memory_weight

    # Combine: theory + memory + exploration
    final_score = theoretical_score + memory_bonus + epistemic_bonus

    # Build human-readable explanation
    reasoning = (
        f"Theory: {theoretical_score:.2f} | "
        f"Memory ({context_type}, n={uses}): "
        f"{success_rate:.0%} success → {memory_bonus:+.2f}"
    )

    if epistemic_bonus != 0:
        reasoning += f" | Explore: {epistemic_bonus:+.2f}"

    reasoning += f" | Final: {final_score:.2f}"

    explanation = {
        "theoretical_score": theoretical_score,
        "memory_bonus": memory_bonus,
        "epistemic_bonus": epistemic_bonus,
        "confidence": confidence,
        "success_rate": success_rate,
        "sample_size": uses,
        "context_type": context_type,
        "final_score": final_score,
        "reasoning": reasoning
    }

    return final_score, explanation


def compute_epistemic_value(p_unlocked: float, skill_stats: dict,
                            episodes_completed: int,
                            min_samples: int = 10) -> float:
    """
    Compute epistemic (information-seeking) value bonus.

    Early in learning, favor actions that gather diverse information.
    This implements exploration bonuses that decay as we gain experience.

    Args:
        p_unlocked: Current belief
        skill_stats: Historical performance data
        episodes_completed: Total episodes so far
        min_samples: Minimum samples we want per skill

    Returns:
        Epistemic bonus (positive for underexplored skills)
    """
    # Early learning phase: higher epistemic value (decays over first 20 episodes)
    learning_phase = max(0, 1.0 - episodes_completed / 20.0)

    # Exploration need: encourage skills with fewer samples
    uses = skill_stats["overall"]["uses"]
    exploration_need = max(0, min_samples - uses) / min_samples

    # Epistemic bonus (decays as we gain experience)
    epistemic_bonus = learning_phase * exploration_need * 2.0

    return epistemic_bonus


def score_all_skills_with_memory(skills: list, p_unlocked: float,
                                 skill_stats_dict: dict = None,
                                 context: dict = None,
                                 episodes_completed: int = 0,
                                 memory_weight: float = 0.5,
                                 verbose: bool = False) -> list:
    """
    Score all skills with memory and return sorted list.

    Args:
        skills: List of skill dicts
        p_unlocked: Current belief
        skill_stats_dict: Dict mapping skill_name -> stats
        context: Context for filtering stats
        episodes_completed: Number of episodes completed
        memory_weight: Weight for empirical data
        verbose: Include detailed explanations

    Returns:
        List of (score, skill, explanation) tuples, sorted by score descending
    """
    scored_skills = []

    for skill in skills:
        skill_name = skill["name"]

        # Get stats for this skill
        stats = skill_stats_dict.get(skill_name) if skill_stats_dict else None

        # Compute epistemic bonus (exploration)
        if stats and episodes_completed < 20:
            epistemic = compute_epistemic_value(p_unlocked, stats, episodes_completed)
        else:
            epistemic = 0.0

        # Score with memory
        score, explanation = score_skill_with_memory(
            skill, p_unlocked,
            skill_stats=stats,
            context=context,
            memory_weight=memory_weight,
            epistemic_bonus=epistemic
        )

        if verbose:
            scored_skills.append((score, skill, explanation))
        else:
            scored_skills.append((score, skill, None))

    # Sort by score descending
    scored_skills.sort(key=lambda x: x[0], reverse=True)

    return scored_skills


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
