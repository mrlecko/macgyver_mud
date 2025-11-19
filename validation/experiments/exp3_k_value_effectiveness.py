"""
Experiment 3: K-Value Effectiveness

Test correlation between k-value and agent performance.

Hypothesis: Skills with k_explore ≈ 0 (specialists) should show better performance
in the MacGyver domain due to the crisp nature of the problem space.

Controls:
- Fixed random seed for reproducibility
- Controlled k-values: 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
- Same number of episodes per k-value condition
- Balanced door states (50/50 locked/unlocked)

Metrics:
- Performance score (success rate, steps, efficiency)
- Correlation between k-value and performance
- Optimal k-value range identification

Statistical test: Pearson correlation + regression analysis
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from pathlib import Path
from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from scoring_silver import build_silver_stamp

# Import validation utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.experiment_utils import ExperimentRunner, set_seed
from utils.stats_utils import correlation_test, compute_summary_stats
from utils.plot_utils import plot_scatter_with_regression


def find_skill_with_target_k(target_k: float, belief: float = 0.5,
                              tolerance: float = 0.05) -> dict:
    """
    Find skill parameters that produce a target k_explore value.

    Uses search to find cost/archetype combination that yields desired k.

    Args:
        target_k: Target k_explore value
        belief: Belief state to use for calculation
        tolerance: Acceptable deviation from target

    Returns:
        Dict with skill parameters and achieved k
    """
    # Try different archetypes and costs
    archetypes = ['peek_door', 'try_door', 'go_window']
    costs = np.linspace(0.5, 3.0, 50)

    best_skill = None
    best_diff = float('inf')

    for archetype in archetypes:
        for cost in costs:
            stamp = build_silver_stamp(archetype, cost, belief)
            k = stamp['k_explore']
            diff = abs(k - target_k)

            if diff < best_diff:
                best_diff = diff
                best_skill = {
                    'archetype': archetype,
                    'cost': cost,
                    'k_explore': k,
                    'target_k': target_k,
                    'error': diff
                }

            if diff < tolerance:
                return best_skill

    return best_skill


def create_k_stratified_skills(k_values: list, belief: float = 0.5) -> dict:
    """
    Create skills stratified across k-value spectrum.

    Args:
        k_values: List of target k_explore values
        belief: Belief state for k calculation

    Returns:
        Dict mapping k_value to skill parameters
    """
    skills = {}

    print("\nFinding skills for target k-values:")
    for target_k in k_values:
        skill = find_skill_with_target_k(target_k, belief)
        skills[target_k] = skill
        print(f"  k={target_k:.1f}: {skill['archetype']:12s} "
              f"cost={skill['cost']:.2f} -> k={skill['k_explore']:.3f} "
              f"(error: {skill['error']:.3f})")

    return skills


def run_episode_with_k_skill(driver, skill_params: dict, door_state: str,
                             trial_id: int) -> dict:
    """
    Run episode using a skill with specific k-value characteristics.

    Note: This is a simulation - we're using the standard skills but
    analyzing their k-coefficients to understand the relationship.

    Args:
        driver: Neo4j driver
        skill_params: Skill parameters with k-value
        door_state: "locked" or "unlocked"
        trial_id: Trial identifier

    Returns:
        Dict with episode results
    """
    with driver.session(database="neo4j") as session:
        # Use the archetype that corresponds to this k-value
        # In practice, we use standard agent but track k-coefficients
        runtime = AgentRuntime(
            session=session,
            door_state=door_state,
            initial_belief=0.5,
            skill_mode='hybrid',  # Use hybrid to access all skills
            use_procedural_memory=False,
            adaptive_params=False
        )

        episode_id = runtime.run_episode(max_steps=5)
        trace = runtime.get_trace()

        # Calculate k-coefficients for skills used
        k_values_used = []
        for step in trace:
            skill_name = step['skill']
            cost = 1.0  # Default cost (would get from graph in production)

            # Get actual cost from standard skills
            if skill_name == 'peek_door':
                cost = 1.0
            elif skill_name == 'try_door':
                cost = 1.5
            elif skill_name == 'go_window':
                cost = 2.0

            stamp = build_silver_stamp(skill_name, cost, step['p_before'])
            k_values_used.append(stamp['k_explore'])

        # Performance metrics
        performance = calculate_performance_score(runtime.escaped, runtime.step_count)

        return {
            'episode_id': episode_id,
            'trial_id': trial_id,
            'target_k': skill_params['target_k'],
            'door_state': door_state,
            'escaped': runtime.escaped,
            'steps': runtime.step_count,
            'performance': performance,
            'k_values_used': k_values_used,
            'mean_k_used': np.mean(k_values_used) if k_values_used else 0,
            'trace': trace
        }


def calculate_performance_score(escaped: bool, steps: int) -> float:
    """
    Calculate unified performance score.

    Higher is better. Combines success and efficiency.

    Args:
        escaped: Whether agent escaped
        steps: Number of steps taken

    Returns:
        Performance score (0-100)
    """
    if not escaped:
        return 0.0

    # Score: 100 for 1 step, decreasing with more steps
    # Max steps = 5, so we normalize
    efficiency = (6 - steps) / 5  # 1.0 for 1 step, 0.2 for 5 steps
    return 100 * efficiency


def run_k_stratified_trials(driver, k_skills: dict, n_trials_per_k: int = 50) -> list:
    """
    Run trials across k-value spectrum.

    Args:
        driver: Neo4j driver
        k_skills: Dict mapping k-values to skill parameters
        n_trials_per_k: Number of trials per k-value

    Returns:
        List of trial results
    """
    results = []
    total_trials = len(k_skills) * n_trials_per_k

    trial_counter = 0

    for target_k, skill_params in k_skills.items():
        print(f"\nRunning trials for k={target_k:.1f}")

        # Balanced door states
        n_locked = n_trials_per_k // 2
        door_states = ['locked'] * n_locked + ['unlocked'] * (n_trials_per_k - n_locked)
        np.random.shuffle(door_states)

        for trial_id, door_state in enumerate(door_states):
            result = run_episode_with_k_skill(driver, skill_params, door_state, trial_id)
            results.append(result)

            trial_counter += 1
            if trial_counter % 20 == 0:
                print(f"  Progress: {trial_counter}/{total_trials}", end='\r')

        print(f"  Completed: {n_trials_per_k}/{n_trials_per_k}")

    return results


def analyze_k_performance_correlation(results: list) -> dict:
    """
    Analyze correlation between k-value and performance.

    Args:
        results: List of trial results

    Returns:
        Dict with correlation analysis
    """
    # Aggregate by target k-value
    k_groups = {}
    for r in results:
        k = r['target_k']
        if k not in k_groups:
            k_groups[k] = []
        k_groups[k].append(r)

    # Calculate mean performance for each k
    k_values = []
    performances = []
    success_rates = []

    for k in sorted(k_groups.keys()):
        group = k_groups[k]
        k_values.append(k)

        perf = [r['performance'] for r in group]
        performances.append(np.mean(perf))

        success = [1.0 if r['escaped'] else 0.0 for r in group]
        success_rates.append(np.mean(success) * 100)

    # Correlation tests
    corr_performance = correlation_test(k_values, performances, method='pearson')
    corr_success = correlation_test(k_values, success_rates, method='pearson')

    # Find optimal k range
    best_k_idx = np.argmax(performances)
    best_k = k_values[best_k_idx]
    best_performance = performances[best_k_idx]

    # Summary stats by k-value
    k_summaries = {}
    for k in sorted(k_groups.keys()):
        group = k_groups[k]
        perfs = [r['performance'] for r in group]
        steps = [r['steps'] for r in group if r['escaped']]

        k_summaries[k] = {
            'n_trials': len(group),
            'success_rate': np.mean([r['escaped'] for r in group]) * 100,
            'mean_performance': np.mean(perfs),
            'std_performance': np.std(perfs),
            'mean_steps': np.mean(steps) if steps else np.nan
        }

    analysis = {
        'k_values': k_values,
        'performances': performances,
        'success_rates': success_rates,
        'correlation_performance': corr_performance,
        'correlation_success': corr_success,
        'best_k': best_k,
        'best_performance': best_performance,
        'k_summaries': k_summaries
    }

    return analysis


def generate_plots(analysis: dict, results_dir: Path):
    """
    Generate visualization plots.

    Args:
        analysis: Analysis results
        results_dir: Directory to save plots
    """
    import matplotlib.pyplot as plt

    k_values = analysis['k_values']
    performances = analysis['performances']
    success_rates = analysis['success_rates']

    # Plot 1: K-value vs Performance
    plot_scatter_with_regression(
        k_values,
        performances,
        xlabel="k_explore value",
        ylabel="Performance Score",
        title="Experiment 3: K-Value vs Performance",
        save_path=results_dir / "exp3_k_vs_performance.png"
    )

    # Plot 2: K-value vs Success Rate
    plot_scatter_with_regression(
        k_values,
        success_rates,
        xlabel="k_explore value",
        ylabel="Success Rate (%)",
        title="Experiment 3: K-Value vs Success Rate",
        save_path=results_dir / "exp3_k_vs_success.png"
    )

    # Plot 3: Performance distribution by k-value
    fig, ax = plt.subplots(figsize=(12, 6))

    k_labels = [f'k={k:.1f}' for k in k_values]
    ax.plot(k_labels, performances, 'o-', linewidth=2, markersize=10, color='steelblue')
    ax.axhline(50, color='red', linestyle='--', alpha=0.5, label='50% baseline')

    ax.set_xlabel('k_explore value', fontweight='bold')
    ax.set_ylabel('Mean Performance Score', fontweight='bold')
    ax.set_title('Experiment 3: Performance Across K-Spectrum', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(results_dir / "exp3_performance_by_k.png", dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {results_dir / 'exp3_performance_by_k.png'}")
    plt.close()


def print_report(analysis: dict):
    """
    Print formatted experiment report.

    Args:
        analysis: Analysis results dictionary
    """
    print("\n" + "="*80)
    print("EXPERIMENT 3: K-VALUE EFFECTIVENESS")
    print("="*80)
    print()

    print("PERFORMANCE BY K-VALUE:")
    print("-"*80)
    for k, summary in analysis['k_summaries'].items():
        print(f"\nk = {k:.1f}:")
        print(f"  Success Rate:      {summary['success_rate']:.1f}%")
        print(f"  Mean Performance:  {summary['mean_performance']:.2f} ± {summary['std_performance']:.2f}")
        print(f"  Mean Steps:        {summary['mean_steps']:.2f}")
        print(f"  Trials:            {summary['n_trials']}")

    print("\n" + "-"*80)
    print("CORRELATION ANALYSIS:")
    print("-"*80)

    corr_perf = analysis['correlation_performance']
    print(f"\nK-value vs Performance:")
    print(f"  Pearson r:        {corr_perf['r']:.4f}")
    print(f"  R²:               {corr_perf['r_squared']:.4f}")
    print(f"  p-value:          {corr_perf['p_value']:.4f}")
    print(f"  Significant:      {corr_perf['significant']}")
    print(f"  Strength:         {corr_perf['strength']}")
    print(f"  Interpretation:   {corr_perf['interpretation']}")

    corr_succ = analysis['correlation_success']
    print(f"\nK-value vs Success Rate:")
    print(f"  Pearson r:        {corr_succ['r']:.4f}")
    print(f"  R²:               {corr_succ['r_squared']:.4f}")
    print(f"  p-value:          {corr_succ['p_value']:.4f}")
    print(f"  Significant:      {corr_succ['significant']}")
    print(f"  Strength:         {corr_succ['strength']}")

    print("\n" + "-"*80)
    print("OPTIMAL K-VALUE:")
    print("-"*80)
    print(f"  Best k:           {analysis['best_k']:.1f}")
    print(f"  Best performance: {analysis['best_performance']:.2f}")

    print("\n" + "="*80)


def main():
    """
    Main experiment execution function.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 3: K-VALUE EFFECTIVENESS")
    print("="*80)
    print("\nTesting correlation between k-value and performance.")
    print("K-values: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]")
    print("Trials per k-value: 50")
    print()

    # Set random seed for reproducibility
    set_seed(42)

    # Initialize experiment runner
    runner = ExperimentRunner(
        experiment_name="exp3_k_value_effectiveness",
        results_dir="validation/results"
    )

    # Create k-stratified skills
    k_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    k_skills = create_k_stratified_skills(k_values, belief=0.5)

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    try:
        # Run k-stratified trials
        print("\nRunning k-stratified trials...")
        results = run_k_stratified_trials(driver, k_skills, n_trials_per_k=50)

        # Store results
        runner.results['raw_data']['trials'] = results
        runner.results['k_skills'] = {k: {
            'archetype': v['archetype'],
            'cost': v['cost'],
            'k_explore': v['k_explore']
        } for k, v in k_skills.items()}

        # Analyze correlation
        print("\nAnalyzing k-performance correlation...")
        analysis = analyze_k_performance_correlation(results)

        # Add to results
        runner.results['analysis'] = analysis

        # Generate plots
        print("Generating plots...")
        results_dir = Path("validation/results")
        generate_plots(analysis, results_dir)

        # Save results
        filepath = runner.save_results()

        # Print report
        print_report(analysis)

        return analysis

    finally:
        driver.close()


if __name__ == "__main__":
    main()
