#!/usr/bin/env python3
"""
Learning Curve Experiments - Comprehensive Analysis

Compares:
1. Baseline (no memory)
2. Memory only
3. Memory + Adaptive params

Metrics:
- Average steps per episode
- Success rate
- Skill selection patterns
- Statistical significance

RED TEAM Critical Questions:
- Is improvement real or noise?
- Is the problem too simple (ceiling effect)?
- Does memory actually help or just lucky?
- What is the pedagogical value?
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from graph_model import get_skill_stats, get_agent
import statistics
from scipy import stats as scipy_stats
import json


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


def run_experiment(session, condition_name, num_episodes, use_memory, adaptive, door_pattern="alternating"):
    """
    Run a learning experiment under specific conditions

    Args:
        condition_name: Name for this condition
        num_episodes: How many episodes to run
        use_memory: Enable procedural memory
        adaptive: Enable adaptive parameters
        door_pattern: "alternating", "random", "locked", "unlocked"
    """
    print(f"\n{'='*80}")
    print(f"EXPERIMENT: {condition_name}")
    print(f"  Episodes: {num_episodes}")
    print(f"  Memory: {use_memory}, Adaptive: {adaptive}")
    print(f"  Door pattern: {door_pattern}")
    print(f"{'='*80}\n")

    # Reset memory before each experiment
    reset_memory(session)

    results = {
        "condition": condition_name,
        "episodes": [],
        "use_memory": use_memory,
        "adaptive": adaptive
    }

    for i in range(num_episodes):
        # Determine door state
        if door_pattern == "alternating":
            door_state = "unlocked" if i % 2 == 0 else "locked"
        elif door_pattern == "random":
            import random
            door_state = random.choice(["locked", "unlocked"])
        else:
            door_state = door_pattern  # "locked" or "unlocked"

        # Create agent
        agent = AgentRuntime(
            session,
            door_state=door_state,
            initial_belief=0.5,
            use_procedural_memory=use_memory,
            adaptive_params=adaptive
        )

        # Run episode
        episode_id = agent.run_episode(max_steps=5)

        # Get trace
        trace = agent.get_trace()

        # Record results
        episode_result = {
            "episode_num": i + 1,
            "door_state": door_state,
            "steps": agent.step_count,
            "escaped": agent.escaped,
            "trace": [
                {
                    "skill": step["skill"],
                    "observation": step["observation"]
                }
                for step in trace
            ]
        }

        results["episodes"].append(episode_result)

        # Progress update
        if (i + 1) % 10 == 0:
            recent_steps = [ep["steps"] for ep in results["episodes"][-10:]]
            recent_avg = sum(recent_steps) / len(recent_steps)
            print(f"  Episodes {i-8:2d}-{i+1:2d}: avg {recent_avg:.2f} steps")

    return results


def analyze_results(all_results):
    """Analyze and compare experimental results"""
    print(f"\n{'='*80}")
    print("ANALYSIS: Comparing Conditions")
    print(f"{'='*80}\n")

    summary = {}

    for result in all_results:
        condition = result["condition"]

        steps = [ep["steps"] for ep in result["episodes"]]
        escaped = [ep["escaped"] for ep in result["episodes"]]

        # Overall metrics
        mean_steps = statistics.mean(steps)
        std_steps = statistics.stdev(steps) if len(steps) > 1 else 0
        success_rate = sum(escaped) / len(escaped)

        # Learning curve (early vs late)
        split_point = len(steps) // 2
        early_steps = steps[:split_point]
        late_steps = steps[split_point:]

        early_mean = statistics.mean(early_steps)
        late_mean = statistics.mean(late_steps)

        improvement = (early_mean - late_mean) / early_mean * 100 if early_mean > 0 else 0

        summary[condition] = {
            "mean_steps": mean_steps,
            "std_steps": std_steps,
            "success_rate": success_rate,
            "early_mean": early_mean,
            "late_mean": late_mean,
            "improvement_pct": improvement
        }

        print(f"[{condition}]")
        print(f"  Mean steps: {mean_steps:.2f} ± {std_steps:.2f}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Learning curve: {early_mean:.2f} → {late_mean:.2f} ({improvement:+.1f}%)")
        print()

    return summary


def statistical_tests(all_results):
    """Perform statistical significance tests"""
    print(f"\n{'='*80}")
    print("STATISTICAL TESTS")
    print(f"{'='*80}\n")

    if len(all_results) < 2:
        print("Need at least 2 conditions to compare")
        return

    # Extract conditions
    baseline = None
    memory = None
    adaptive = None

    for result in all_results:
        if result["condition"] == "Baseline (No Memory)":
            baseline = [ep["steps"] for ep in result["episodes"]]
        elif result["condition"] == "Memory Only":
            memory = [ep["steps"] for ep in result["episodes"]]
        elif result["condition"] == "Memory + Adaptive":
            adaptive = [ep["steps"] for ep in result["episodes"]]

    # Compare Memory vs Baseline
    if baseline and memory:
        t_stat, p_value = scipy_stats.ttest_ind(baseline, memory)
        print(f"[Memory vs Baseline]")
        print(f"  t-statistic: {t_stat:.3f}")
        print(f"  p-value: {p_value:.4f}")
        if p_value < 0.05:
            print(f"  ✅ Statistically significant (p < 0.05)")
        else:
            print(f"  ⚠️  Not statistically significant (p >= 0.05)")
        print()

    # Compare Adaptive vs Baseline
    if baseline and adaptive:
        t_stat, p_value = scipy_stats.ttest_ind(baseline, adaptive)
        print(f"[Memory+Adaptive vs Baseline]")
        print(f"  t-statistic: {t_stat:.3f}")
        print(f"  p-value: {p_value:.4f}")
        if p_value < 0.05:
            print(f"  ✅ Statistically significant (p < 0.05)")
        else:
            print(f"  ⚠️  Not statistically significant (p >= 0.05)")
        print()

    # Compare Memory vs Adaptive
    if memory and adaptive:
        t_stat, p_value = scipy_stats.ttest_ind(memory, adaptive)
        print(f"[Memory+Adaptive vs Memory Only]")
        print(f"  t-statistic: {t_stat:.3f}")
        print(f"  p-value: {p_value:.4f}")
        if p_value < 0.05:
            print(f"  ✅ Statistically significant (p < 0.05)")
        else:
            print(f"  ⚠️  Not statistically significant (p >= 0.05)")
        print()


def skill_usage_analysis(session, all_results):
    """Analyze how skill usage patterns change"""
    print(f"\n{'='*80}")
    print("SKILL USAGE PATTERNS")
    print(f"{'='*80}\n")

    for result in all_results:
        condition = result["condition"]
        print(f"[{condition}]")

        # Count skill usage
        skill_counts = {}
        for episode in result["episodes"]:
            for step in episode["trace"]:
                skill = step["skill"]
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        total_actions = sum(skill_counts.values())

        for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / total_actions * 100
            print(f"  {skill:15s}: {count:3d} times ({pct:5.1f}%)")

        print()


def pedagogical_assessment(summary):
    """Critical assessment of pedagogical value"""
    print(f"\n{'='*80}")
    print("PEDAGOGICAL ASSESSMENT (RED TEAM)")
    print(f"{'='*80}\n")

    issues = []
    strengths = []

    # Check for ceiling effect
    baseline = summary.get("Baseline (No Memory)", {})
    if baseline.get("mean_steps", 10) < 2.5:
        issues.append("⚠️  CEILING EFFECT: Problem is very easy (baseline already ~2 steps)")
        issues.append("   → Learning gains may be marginal due to problem simplicity")

    # Check for learning
    memory = summary.get("Memory Only", {})
    if memory.get("improvement_pct", 0) > 5:
        strengths.append("✅ LEARNING DETECTED: Clear improvement over time")
    else:
        issues.append("⚠️  WEAK LEARNING: Improvement less than 5%")

    # Check memory benefit
    if memory.get("mean_steps", 10) < baseline.get("mean_steps", 10):
        benefit_pct = (baseline["mean_steps"] - memory["mean_steps"]) / baseline["mean_steps"] * 100
        strengths.append(f"✅ MEMORY HELPS: {benefit_pct:.1f}% reduction in steps")
    else:
        issues.append("❌ MEMORY DOESN'T HELP: No improvement over baseline")

    print("STRENGTHS:")
    for strength in strengths:
        print(f"  {strength}")

    print("\nISSUES:")
    for issue in issues:
        print(f"  {issue}")

    print("\nPEDAGOGICAL RECOMMENDATIONS:")
    if baseline.get("mean_steps", 10) < 2.5:
        print("  • Problem may be TOO SIMPLE for demonstrating learning")
        print("  • Consider: more complex scenarios, more skills, hidden states")
        print("  • Current value: Shows memory MECHANISM, not dramatic learning")
    else:
        print("  • Problem complexity is appropriate for demonstration")

    print("\n  • HONEST FRAMING:")
    print("    - This demonstrates 'procedural memory accumulation'")
    print("    - NOT 'solves previously unsolvable problems'")
    print("    - Shows refinement and optimization, not discovery")


def main():
    """Run comprehensive learning curve experiments"""
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*20 + "LEARNING CURVE EXPERIMENTS" + " "*32 + "║")
    print("║" + " "*15 + "Comprehensive Analysis with Statistics" + " "*25 + "║")
    print("╚" + "="*78 + "╝")

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    all_results = []

    with driver.session(database="neo4j") as session:
        # Experiment 1: Baseline (no memory)
        results_baseline = run_experiment(
            session,
            "Baseline (No Memory)",
            num_episodes=30,
            use_memory=False,
            adaptive=False
        )
        all_results.append(results_baseline)

        # Experiment 2: Memory only
        results_memory = run_experiment(
            session,
            "Memory Only",
            num_episodes=50,
            use_memory=True,
            adaptive=False
        )
        all_results.append(results_memory)

        # Experiment 3: Memory + Adaptive
        results_adaptive = run_experiment(
            session,
            "Memory + Adaptive",
            num_episodes=50,
            use_memory=True,
            adaptive=True
        )
        all_results.append(results_adaptive)

        # Analyze results
        summary = analyze_results(all_results)

        # Statistical tests
        statistical_tests(all_results)

        # Skill usage patterns
        skill_usage_analysis(session, all_results)

        # Pedagogical assessment
        pedagogical_assessment(summary)

        # Save results
        output_file = "experiments/learning_curve_results.json"
        os.makedirs("experiments", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump({
                "summary": summary,
                "all_results": all_results
            }, f, indent=2)

        print(f"\n\n📊 Full results saved to: {output_file}")

    driver.close()


if __name__ == "__main__":
    main()
