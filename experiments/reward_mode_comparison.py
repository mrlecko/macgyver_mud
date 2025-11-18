#!/usr/bin/env python3
"""
Reward Mode Comparison - Demonstrates the importance of reward design

Compares two reward modes:
1. NAIVE: Lower window penalty (shows metric gaming)
2. STRATEGIC: Higher window penalty (encourages information-gathering)

This demonstrates:
- Same memory mechanism, different outcomes
- Importance of reward design in AI systems
- How agents optimize what you measure, not what you intend
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config as base_config
from agent_runtime import AgentRuntime
from graph_model import get_skill_stats, get_agent
import statistics
from scipy import stats as scipy_stats
import json
import importlib


def reset_memory(session):
    """Reset all memory to clean state"""
    session.run("""
        MATCH (stats:SkillStats)
        SET stats.total_uses = 0,
            stats.successful_episodes = 0,
            stats.failed_episodes = 0,
            stats.uncertain_uses = 0,
            stats.uncertain_successes = 0,
            stats.confident_locked_uses = 0,
            stats.confident_locked_successes = 0,
            stats.confident_unlocked_uses = 0,
            stats.confident_unlocked_successes = 0
    """)

    session.run("""
        MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
        SET meta.episodes_completed = 0,
            meta.beta = 6.0
    """)


def run_experiment_with_mode(session, reward_mode, num_episodes=50):
    """
    Run experiment with specified reward mode

    Args:
        reward_mode: "naive" or "strategic"
        num_episodes: Number of episodes to run
    """
    # Set environment variable and reload config
    os.environ["REWARD_MODE"] = reward_mode
    import config
    importlib.reload(config)

    print(f"\n{'='*80}")
    print(f"EXPERIMENT: {reward_mode.upper()} Reward Mode")
    print(f"  SLOW_PENALTY: {config.SLOW_PENALTY}")
    print(f"  Episodes: {num_episodes}")
    print(f"{'='*80}\n")

    # Reset memory before experiment
    reset_memory(session)

    results = {
        "reward_mode": reward_mode,
        "slow_penalty": config.SLOW_PENALTY,
        "episodes": [],
    }

    steps_history = []

    for i in range(num_episodes):
        # Alternate door states
        door_state = "unlocked" if i % 2 == 0 else "locked"

        # Create agent
        agent = AgentRuntime(
            session,
            door_state=door_state,
            initial_belief=0.5,
            use_procedural_memory=True,
            adaptive_params=False  # Focus on memory, not adaptation for clarity
        )

        # Run episode
        agent.run_episode(max_steps=5)

        # Get trace
        trace = agent.get_trace()

        # Record results
        episode_result = {
            "episode_num": i + 1,
            "door_state": door_state,
            "steps": agent.step_count,
            "escaped": agent.escaped,
            "skills_used": [step["skill"] for step in trace]
        }

        results["episodes"].append(episode_result)
        steps_history.append(agent.step_count)

        # Progress update
        if (i + 1) % 10 == 0:
            recent_steps = steps_history[-10:]
            recent_avg = sum(recent_steps) / len(recent_steps)

            # Show sample traces
            sample_traces = [ep["skills_used"] for ep in results["episodes"][-3:]]
            print(f"  Episodes {i-8:2d}-{i+1:2d}: avg {recent_avg:.2f} steps")
            for idx, trace in enumerate(sample_traces):
                ep_num = i + 1 - (2 - idx)
                door = results["episodes"][ep_num-1]["door_state"]
                print(f"    Ep{ep_num}: ({door:8s}) {' → '.join(trace)}")

    # Compute statistics
    early_steps = steps_history[:10]
    late_steps = steps_history[-10:]

    results["statistics"] = {
        "mean_steps": statistics.mean(steps_history),
        "std_steps": statistics.stdev(steps_history) if len(steps_history) > 1 else 0,
        "early_mean": statistics.mean(early_steps),
        "late_mean": statistics.mean(late_steps),
        "improvement_pct": (statistics.mean(early_steps) - statistics.mean(late_steps)) / statistics.mean(early_steps) * 100
    }

    # Get final skill statistics
    skill_usage = {}
    for ep in results["episodes"]:
        for skill in ep["skills_used"]:
            skill_usage[skill] = skill_usage.get(skill, 0) + 1

    results["skill_usage"] = skill_usage

    # Get skill stats from graph
    skill_stats = {}
    for skill in ["peek_door", "try_door", "go_window"]:
        stats = get_skill_stats(session, skill)
        skill_stats[skill] = {
            "uses": stats["overall"]["uses"],
            "success_rate": stats["overall"]["success_rate"]
        }

    results["skill_stats"] = skill_stats

    return results


def compare_results(naive_results, strategic_results):
    """Compare and analyze both reward modes"""
    print(f"\n{'='*80}")
    print("COMPARATIVE ANALYSIS")
    print(f"{'='*80}\n")

    # Print statistics side-by-side
    print("[NAIVE MODE - Allows Metric Gaming]")
    print(f"  SLOW_PENALTY: {naive_results['slow_penalty']}")
    print(f"  Mean steps: {naive_results['statistics']['mean_steps']:.2f} ± {naive_results['statistics']['std_steps']:.2f}")
    print(f"  Learning curve: {naive_results['statistics']['early_mean']:.2f} → {naive_results['statistics']['late_mean']:.2f} ({naive_results['statistics']['improvement_pct']:+.1f}%)")

    print(f"\n  Skill usage:")
    total_naive = sum(naive_results["skill_usage"].values())
    for skill, count in sorted(naive_results["skill_usage"].items(), key=lambda x: x[1], reverse=True):
        pct = count / total_naive * 100
        print(f"    {skill:15s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n  Sample late episodes (41-45):")
    for ep in naive_results["episodes"][40:45]:
        skills_str = " → ".join(ep["skills_used"])
        print(f"    Ep{ep['episode_num']:2d} ({ep['door_state']:8s}): {skills_str} ({ep['steps']} steps)")

    print(f"\n[STRATEGIC MODE - Encourages Information-Gathering]")
    print(f"  SLOW_PENALTY: {strategic_results['slow_penalty']}")
    print(f"  Mean steps: {strategic_results['statistics']['mean_steps']:.2f} ± {strategic_results['statistics']['std_steps']:.2f}")
    print(f"  Learning curve: {strategic_results['statistics']['early_mean']:.2f} → {strategic_results['statistics']['late_mean']:.2f} ({strategic_results['statistics']['improvement_pct']:+.1f}%)")

    print(f"\n  Skill usage:")
    total_strategic = sum(strategic_results["skill_usage"].values())
    for skill, count in sorted(strategic_results["skill_usage"].items(), key=lambda x: x[1], reverse=True):
        pct = count / total_strategic * 100
        print(f"    {skill:15s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n  Sample late episodes (41-45):")
    for ep in strategic_results["episodes"][40:45]:
        skills_str = " → ".join(ep["skills_used"])
        print(f"    Ep{ep['episode_num']:2d} ({ep['door_state']:8s}): {skills_str} ({ep['steps']} steps)")

    # Statistical comparison
    print(f"\n{'='*80}")
    print("STATISTICAL SIGNIFICANCE")
    print(f"{'='*80}\n")

    naive_steps = [ep["steps"] for ep in naive_results["episodes"]]
    strategic_steps = [ep["steps"] for ep in strategic_results["episodes"]]

    t_stat, p_value = scipy_stats.ttest_ind(naive_steps, strategic_steps)
    print(f"[Naive vs Strategic]")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  p-value: {p_value:.4f}")
    if p_value < 0.05:
        print(f"  ✅ Statistically significant difference (p < 0.05)")
    else:
        print(f"  ⚠️  Not statistically significant (p >= 0.05)")

    # Pedagogical analysis
    print(f"\n{'='*80}")
    print("PEDAGOGICAL INSIGHTS")
    print(f"{'='*80}\n")

    # Check for metric gaming in naive mode
    naive_window_pct = naive_results["skill_usage"].get("go_window", 0) / total_naive * 100
    strategic_window_pct = strategic_results["skill_usage"].get("go_window", 0) / total_strategic * 100

    print(f"[Metric Gaming Detection]")
    if naive_window_pct > 60:
        print(f"  ✅ NAIVE mode shows metric gaming: {naive_window_pct:.0f}% go_window usage")
        print(f"     Agent learned to spam the 'safe but lazy' option")
    else:
        print(f"  ⚠️  NAIVE mode did not show expected metric gaming")

    if strategic_window_pct < 40:
        print(f"  ✅ STRATEGIC mode reduces lazy behavior: {strategic_window_pct:.0f}% go_window usage")
        print(f"     Agent maintains information-gathering behavior")
    else:
        print(f"  ⚠️  STRATEGIC mode still shows high window usage: {strategic_window_pct:.0f}%")

    print(f"\n[Key Lessons]")
    print(f"  1. Same memory mechanism → Different behaviors")
    print(f"  2. Agents optimize what you MEASURE, not what you INTEND")
    print(f"  3. Reward design is CRITICAL for desired outcomes")
    print(f"  4. 'Naive' mode demonstrates real AI alignment challenges")

    return {
        "naive": naive_results,
        "strategic": strategic_results,
        "comparison": {
            "t_statistic": t_stat,
            "p_value": p_value,
            "naive_window_pct": naive_window_pct,
            "strategic_window_pct": strategic_window_pct
        }
    }


def main():
    """Run comparative experiments"""
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*20 + "REWARD MODE COMPARISON" + " "*37 + "║")
    print("║" + " "*15 + "Demonstrating Importance of Reward Design" + " "*22 + "║")
    print("╚" + "="*78 + "╝")

    driver = GraphDatabase.driver(
        base_config.NEO4J_URI,
        auth=(base_config.NEO4J_USER, base_config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Run naive mode experiment
        naive_results = run_experiment_with_mode(session, "naive", num_episodes=50)

        # Run strategic mode experiment
        strategic_results = run_experiment_with_mode(session, "strategic", num_episodes=50)

        # Compare and analyze
        full_results = compare_results(naive_results, strategic_results)

        # Save results
        output_file = "experiments/reward_mode_comparison.json"
        os.makedirs("experiments", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(full_results, f, indent=2)

        print(f"\n\n📊 Full results saved to: {output_file}")

    driver.close()


if __name__ == "__main__":
    main()
