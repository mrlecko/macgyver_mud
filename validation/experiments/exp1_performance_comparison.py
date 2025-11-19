"""
Experiment 1: Performance Comparison

Test whether skill mode (crisp, balanced, hybrid) affects agent performance.

Hypothesis: Balanced/hybrid skills should perform better in high-uncertainty scenarios.

Controls:
- Fixed random seed for reproducibility
- Same number of trials per condition
- Same initial belief states (0.5 - maximum uncertainty)
- Same environment parameters
- 50/50 split of locked/unlocked doors

Metrics:
- Success rate (percentage of episodes that escape)
- Average steps to goal
- Escapes via door percentage (vs window)

Statistical test: One-way ANOVA + pairwise t-tests with Bonferroni correction
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from pathlib import Path
from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime

# Import validation utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.experiment_utils import ExperimentRunner, set_seed, extract_metric
from utils.stats_utils import compute_summary_stats, anova_one_way
from utils.plot_utils import plot_condition_comparison, plot_distribution_comparison


def run_single_trial(driver, skill_mode: str, door_state: str, trial_id: int) -> dict:
    """
    Run a single trial episode.

    Args:
        driver: Neo4j driver
        skill_mode: "crisp", "balanced", or "hybrid"
        door_state: "locked" or "unlocked"
        trial_id: Trial identifier for reproducibility

    Returns:
        Dict with trial results
    """
    with driver.session(database="neo4j") as session:
        runtime = AgentRuntime(
            session=session,
            door_state=door_state,
            initial_belief=0.5,  # Maximum uncertainty
            skill_mode=skill_mode,
            use_procedural_memory=False,  # Pure active inference
            adaptive_params=False
        )

        episode_id = runtime.run_episode(max_steps=5)
        trace = runtime.get_trace()

        # Determine escape method
        escaped_via_door = False
        escaped_via_window = False

        if runtime.escaped and len(trace) > 0:
            last_skill = trace[-1]['skill']
            if last_skill == 'try_door':
                escaped_via_door = True
            elif last_skill == 'go_window':
                escaped_via_window = True

        return {
            'episode_id': episode_id,
            'trial_id': trial_id,
            'skill_mode': skill_mode,
            'door_state': door_state,
            'escaped': runtime.escaped,
            'steps': runtime.step_count,
            'escaped_via_door': escaped_via_door,
            'escaped_via_window': escaped_via_window,
            'trace': trace
        }


def run_condition_trials(driver, skill_mode: str, n_trials: int = 100,
                        locked_pct: float = 0.5) -> list:
    """
    Run multiple trials for a given skill mode condition.

    Args:
        driver: Neo4j driver
        skill_mode: "crisp", "balanced", or "hybrid"
        n_trials: Number of trials to run
        locked_pct: Percentage of trials with locked door

    Returns:
        List of trial result dicts
    """
    results = []
    n_locked = int(n_trials * locked_pct)

    # Create balanced door state sequence
    door_states = ['locked'] * n_locked + ['unlocked'] * (n_trials - n_locked)
    np.random.shuffle(door_states)

    for trial_id, door_state in enumerate(door_states):
        result = run_single_trial(driver, skill_mode, door_state, trial_id)
        results.append(result)

        if (trial_id + 1) % 20 == 0:
            print(f"  Progress: {trial_id + 1}/{n_trials}", end='\r')

    print(f"  Completed: {n_trials}/{n_trials}")
    return results


def analyze_results(runner: ExperimentRunner, conditions: dict) -> dict:
    """
    Analyze experiment results and perform statistical tests.

    Args:
        runner: ExperimentRunner instance with collected data
        conditions: Dict mapping condition names to their data

    Returns:
        Dict with analysis results
    """
    analysis = {}

    # Extract metrics for each condition
    metrics = {}

    for condition_name in ['crisp', 'balanced', 'hybrid']:
        data = runner.get_condition_data(condition_name)

        # Success rate
        success_rate = np.mean([r['escaped'] for r in data]) * 100

        # Average steps (only for successful escapes)
        successful = [r for r in data if r['escaped']]
        avg_steps = np.mean([r['steps'] for r in successful]) if successful else np.nan

        # Escape via door percentage
        door_escapes = [r for r in data if r['escaped_via_door']]
        door_pct = (len(door_escapes) / len(data)) * 100 if data else 0

        metrics[condition_name] = {
            'success_rate': success_rate,
            'avg_steps': avg_steps,
            'door_escape_pct': door_pct,
            'n_trials': len(data),
            'n_successful': len(successful)
        }

    analysis['metrics'] = metrics

    # Statistical tests

    # 1. One-way ANOVA for success rates
    success_data = {
        'crisp': [1.0 if r['escaped'] else 0.0 for r in runner.get_condition_data('crisp')],
        'balanced': [1.0 if r['escaped'] else 0.0 for r in runner.get_condition_data('balanced')],
        'hybrid': [1.0 if r['escaped'] else 0.0 for r in runner.get_condition_data('hybrid')]
    }

    anova_result = anova_one_way(success_data, alpha=0.05)
    analysis['anova_success'] = anova_result

    # 2. One-way ANOVA for average steps (successful escapes only)
    steps_data = {}
    for condition_name in ['crisp', 'balanced', 'hybrid']:
        successful = [r for r in runner.get_condition_data(condition_name) if r['escaped']]
        steps_data[condition_name] = [r['steps'] for r in successful]

    anova_steps = anova_one_way(steps_data, alpha=0.05)
    analysis['anova_steps'] = anova_steps

    # 3. Pairwise comparisons (if ANOVA significant)
    if anova_result['significant']:
        from utils.stats_utils import independent_t_test, bonferroni_correction

        pairs = [
            ('crisp', 'balanced'),
            ('crisp', 'hybrid'),
            ('balanced', 'hybrid')
        ]

        pairwise_results = {}
        p_values = []

        for cond1, cond2 in pairs:
            test_result = independent_t_test(success_data[cond1], success_data[cond2])
            pairwise_results[f'{cond1}_vs_{cond2}'] = test_result
            if test_result['valid']:
                p_values.append(test_result['p_value'])

        # Bonferroni correction
        if p_values:
            correction = bonferroni_correction(p_values, alpha=0.05)
            pairwise_results['bonferroni_correction'] = correction

        analysis['pairwise_tests'] = pairwise_results

    return analysis


def generate_plots(runner: ExperimentRunner, results_dir: Path):
    """
    Generate visualization plots for the experiment.

    Args:
        runner: ExperimentRunner with collected data
        results_dir: Directory to save plots
    """
    # Extract success rates as binary data
    success_data = {
        'crisp': [1.0 if r['escaped'] else 0.0 for r in runner.get_condition_data('crisp')],
        'balanced': [1.0 if r['escaped'] else 0.0 for r in runner.get_condition_data('balanced')],
        'hybrid': [1.0 if r['escaped'] else 0.0 for r in runner.get_condition_data('hybrid')]
    }

    # Extract steps data (successful only)
    steps_data = {}
    for condition in ['crisp', 'balanced', 'hybrid']:
        successful = [r for r in runner.get_condition_data(condition) if r['escaped']]
        steps_data[condition] = [r['steps'] for r in successful]

    # Plot 1: Success rate comparison
    plot_condition_comparison(
        success_data,
        title="Experiment 1: Success Rate by Skill Mode",
        ylabel="Success (1=escaped, 0=failed)",
        save_path=results_dir / "exp1_success_comparison.png"
    )

    # Plot 2: Steps comparison (for successful escapes)
    plot_condition_comparison(
        steps_data,
        title="Experiment 1: Steps to Escape by Skill Mode",
        ylabel="Number of Steps",
        save_path=results_dir / "exp1_steps_comparison.png"
    )

    # Plot 3: Distribution of steps
    plot_distribution_comparison(
        steps_data,
        title="Experiment 1: Distribution of Steps to Escape",
        xlabel="Number of Steps",
        save_path=results_dir / "exp1_steps_distribution.png"
    )


def print_report(analysis: dict):
    """
    Print formatted experiment report.

    Args:
        analysis: Analysis results dictionary
    """
    print("\n" + "="*80)
    print("EXPERIMENT 1: PERFORMANCE COMPARISON")
    print("="*80)
    print()

    print("METRICS BY CONDITION:")
    print("-"*80)
    for condition, metrics in analysis['metrics'].items():
        print(f"\n{condition.upper()}:")
        print(f"  Success Rate:       {metrics['success_rate']:.1f}%")
        print(f"  Avg Steps:          {metrics['avg_steps']:.2f}")
        print(f"  Door Escape %:      {metrics['door_escape_pct']:.1f}%")
        print(f"  Trials (Successful):{metrics['n_trials']} ({metrics['n_successful']})")

    print("\n" + "-"*80)
    print("STATISTICAL TESTS:")
    print("-"*80)

    # ANOVA results
    anova = analysis['anova_success']
    print(f"\nOne-way ANOVA (Success Rate):")
    print(f"  F-statistic:   {anova['f_statistic']:.4f}")
    print(f"  p-value:       {anova['p_value']:.4f}")
    print(f"  Significant:   {anova['significant']}")
    print(f"  Effect size:   {anova['effect_size']} (η² = {anova['eta_squared']:.4f})")
    print(f"  Interpretation: {anova['interpretation']}")

    anova_steps = analysis['anova_steps']
    print(f"\nOne-way ANOVA (Average Steps):")
    print(f"  F-statistic:   {anova_steps['f_statistic']:.4f}")
    print(f"  p-value:       {anova_steps['p_value']:.4f}")
    print(f"  Significant:   {anova_steps['significant']}")
    print(f"  Effect size:   {anova_steps['effect_size']} (η² = {anova_steps['eta_squared']:.4f})")
    print(f"  Interpretation: {anova_steps['interpretation']}")

    # Pairwise tests (if performed)
    if 'pairwise_tests' in analysis:
        print("\nPairwise Comparisons (with Bonferroni correction):")
        correction = analysis['pairwise_tests'].get('bonferroni_correction', {})
        corrected_alpha = correction.get('corrected_alpha', 0.05)
        print(f"  Corrected α = {corrected_alpha:.4f}")

        for pair_name, result in analysis['pairwise_tests'].items():
            if pair_name == 'bonferroni_correction':
                continue
            if result['valid']:
                print(f"\n  {pair_name}:")
                print(f"    p-value:     {result['p_value']:.4f}")
                print(f"    Significant: {result['p_value'] < corrected_alpha}")
                print(f"    Cohen's d:   {result['cohens_d']:.3f} ({result['effect_size']})")

    print("\n" + "="*80)


def main():
    """
    Main experiment execution function.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 1: PERFORMANCE COMPARISON")
    print("="*80)
    print("\nTesting whether skill mode affects agent performance.")
    print("Conditions: crisp, balanced, hybrid")
    print("Trials per condition: 100")
    print("Door states: 50% locked, 50% unlocked")
    print()

    # Set random seed for reproducibility
    set_seed(42)

    # Initialize experiment runner
    runner = ExperimentRunner(
        experiment_name="exp1_performance_comparison",
        results_dir="validation/results"
    )

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    try:
        # Run experiments for each condition
        conditions = ['crisp', 'balanced', 'hybrid']

        for condition in conditions:
            print(f"\nRunning condition: {condition}")
            print(f"  Trials: 100")

            results = run_condition_trials(
                driver=driver,
                skill_mode=condition,
                n_trials=100,
                locked_pct=0.5
            )

            # Store results
            runner.results['raw_data'][condition] = results
            runner.results['conditions'][condition] = {
                'n_trials': len(results),
                'skill_mode': condition
            }

        # Analyze results
        print("\nAnalyzing results...")
        analysis = analyze_results(runner, runner.results['conditions'])

        # Add analysis to results
        runner.results['analysis'] = analysis

        # Generate plots
        print("Generating plots...")
        results_dir = Path("validation/results")
        generate_plots(runner, results_dir)

        # Save results
        filepath = runner.save_results()

        # Print report
        print_report(analysis)

        return analysis

    finally:
        driver.close()


if __name__ == "__main__":
    main()
