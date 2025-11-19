"""
Experiment 2: K-Space Coverage

Test if k≈0 clustering emerges naturally from random skill combinations.

Hypothesis: The Silver Gauge k_explore metric should cluster near k≈0 (specialist zone)
for most randomly generated skill combinations, demonstrating that the MacGyver domain
naturally favors specialist strategies.

Controls:
- Fixed random seed for reproducibility
- 1000 random skill combinations
- Systematic sampling across parameter space
- Multiple belief states tested

Metrics:
- Percentage of skills with k < 0.05 (near-zero specialist)
- Distribution of k_explore values
- Clustering statistics

Statistical test: Bootstrap CI for proportion of k < 0.05
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from pathlib import Path
from scipy import stats

# Import silver gauge scoring
from scoring_silver import build_silver_stamp

# Import validation utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.experiment_utils import ExperimentRunner, set_seed
from utils.stats_utils import bootstrap_ci, compute_summary_stats
from utils.plot_utils import plot_k_distribution


def generate_random_skill(skill_id: int) -> dict:
    """
    Generate a random skill with varied cost parameters.

    Args:
        skill_id: Unique identifier for this skill

    Returns:
        Dict with skill parameters
    """
    # Use different skill archetypes
    archetypes = ['peek_door', 'try_door', 'go_window']
    archetype = archetypes[skill_id % 3]

    # Vary cost randomly
    cost = np.random.uniform(0.5, 3.0)

    return {
        'skill_id': skill_id,
        'archetype': archetype,
        'cost': cost
    }


def calculate_k_explore_for_skill(skill: dict, p_unlocked: float) -> float:
    """
    Calculate k_explore coefficient for a skill at given belief.

    Args:
        skill: Skill dict with archetype and cost
        p_unlocked: Belief probability

    Returns:
        k_explore value
    """
    stamp = build_silver_stamp(
        skill_name=skill['archetype'],
        cost=skill['cost'],
        p_unlocked=p_unlocked
    )

    return stamp['k_explore']


def run_k_space_sampling(n_samples: int = 1000,
                         belief_values: list = None) -> list:
    """
    Sample k-space by generating random skills and computing k_explore.

    Args:
        n_samples: Number of random skill combinations to test
        belief_values: List of belief values to test (default: [0.1, 0.3, 0.5, 0.7, 0.9])

    Returns:
        List of result dicts
    """
    if belief_values is None:
        belief_values = [0.1, 0.3, 0.5, 0.7, 0.9]

    results = []

    for i in range(n_samples):
        skill = generate_random_skill(i)

        for p_unlocked in belief_values:
            k_explore = calculate_k_explore_for_skill(skill, p_unlocked)

            results.append({
                'skill_id': skill['skill_id'],
                'archetype': skill['archetype'],
                'cost': skill['cost'],
                'p_unlocked': p_unlocked,
                'k_explore': k_explore
            })

        if (i + 1) % 200 == 0:
            print(f"  Progress: {i + 1}/{n_samples}", end='\r')

    print(f"  Completed: {n_samples}/{n_samples}")
    return results


def analyze_k_distribution(results: list, threshold: float = 0.05) -> dict:
    """
    Analyze the distribution of k_explore values.

    Args:
        results: List of result dicts with k_explore values
        threshold: Threshold for "near-zero" classification (default: 0.05)

    Returns:
        Dict with analysis results
    """
    k_values = [r['k_explore'] for r in results]
    k_array = np.array(k_values)

    # Basic statistics
    stats_summary = compute_summary_stats(k_values)

    # Proportion near k≈0
    near_zero = k_array < threshold
    proportion_near_zero = np.mean(near_zero)

    # Bootstrap confidence interval for proportion
    lower_ci, upper_ci = bootstrap_ci(
        near_zero.astype(float),
        statistic=np.mean,
        n_bootstrap=10000,
        alpha=0.05
    )

    # Test hypothesis: >80% should cluster near k≈0
    hypothesis_threshold = 0.80
    hypothesis_supported = proportion_near_zero > hypothesis_threshold

    # Distribution analysis
    specialist_zone = k_array < 0.5  # k < 0.5
    generalist_zone = k_array >= 0.5  # k >= 0.5

    specialist_pct = np.mean(specialist_zone) * 100
    generalist_pct = np.mean(generalist_zone) * 100

    # Clustering analysis (by belief state)
    belief_clustering = {}
    for belief in [0.1, 0.3, 0.5, 0.7, 0.9]:
        belief_data = [r for r in results if abs(r['p_unlocked'] - belief) < 0.01]
        belief_k = [r['k_explore'] for r in belief_data]
        belief_near_zero = np.mean(np.array(belief_k) < threshold)

        belief_clustering[belief] = {
            'mean_k': np.mean(belief_k),
            'median_k': np.median(belief_k),
            'proportion_near_zero': belief_near_zero
        }

    analysis = {
        'n_samples': len(results),
        'threshold': threshold,
        'statistics': stats_summary,
        'proportion_near_zero': proportion_near_zero,
        'ci_95': (lower_ci, upper_ci),
        'hypothesis_threshold': hypothesis_threshold,
        'hypothesis_supported': hypothesis_supported,
        'specialist_percentage': specialist_pct,
        'generalist_percentage': generalist_pct,
        'belief_clustering': belief_clustering,
        'k_values': k_values  # For plotting
    }

    return analysis


def test_goodness_of_fit(k_values: list) -> dict:
    """
    Test if k-values follow expected clustering pattern.

    Uses chi-square goodness of fit to test if distribution matches
    expected pattern (most values near 0, few near 1).

    Args:
        k_values: List of k_explore values

    Returns:
        Dict with test results
    """
    k_array = np.array(k_values)

    # Define bins for clustering test
    bins = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
    observed_counts, _ = np.histogram(k_array, bins=bins)

    # Expected distribution (hypothesis: most near 0)
    # Expected: 70% in [0, 0.1], 15% in [0.1, 0.3], 10% in [0.3, 0.5], 4% in [0.5, 0.7], 1% in [0.7, 1.0]
    expected_proportions = [0.70, 0.15, 0.10, 0.04, 0.01]
    expected_counts = np.array(expected_proportions) * len(k_values)

    # Chi-square goodness of fit
    chi2_stat, p_value = stats.chisquare(observed_counts, expected_counts)

    # Interpretation
    significant = p_value < 0.05

    return {
        'chi2_statistic': chi2_stat,
        'p_value': p_value,
        'significant': significant,
        'bins': bins,
        'observed_counts': observed_counts.tolist(),
        'expected_counts': expected_counts.tolist(),
        'interpretation': _interpret_goodness_of_fit(significant, p_value)
    }


def _interpret_goodness_of_fit(significant: bool, p_value: float) -> str:
    """Generate interpretation for goodness of fit test."""
    if significant:
        return (f"Distribution differs from expected clustering pattern (p={p_value:.4f}). "
                "May indicate different clustering behavior than hypothesized.")
    else:
        return (f"Distribution consistent with expected clustering pattern (p={p_value:.4f}). "
                "Supports hypothesis of k≈0 clustering.")


def generate_plots(analysis: dict, results_dir: Path):
    """
    Generate visualization plots for k-space coverage.

    Args:
        analysis: Analysis results dict
        results_dir: Directory to save plots
    """
    import matplotlib.pyplot as plt

    k_values = analysis['k_values']

    # Plot 1: K-distribution with zones
    plot_k_distribution(
        k_values,
        title="Experiment 2: k_explore Distribution (1000 random skills)",
        highlight_zones=True,
        save_path=results_dir / "exp2_k_distribution.png"
    )

    # Plot 2: K-distribution by belief state
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    belief_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    for idx, belief in enumerate(belief_values):
        ax = axes[idx]

        # Extract k-values for this belief
        from scoring_silver import build_silver_stamp
        belief_k = []
        for i in range(200):  # Sample subset
            skill_name = ['peek_door', 'try_door', 'go_window'][i % 3]
            cost = np.random.uniform(0.5, 3.0)
            stamp = build_silver_stamp(skill_name, cost, belief)
            belief_k.append(stamp['k_explore'])

        ax.hist(belief_k, bins=20, alpha=0.7, edgecolor='black', color='steelblue')
        ax.axvline(0.05, color='red', linestyle='--', linewidth=2, label='k=0.05')
        ax.set_xlabel('k_explore', fontweight='bold')
        ax.set_ylabel('Frequency', fontweight='bold')
        ax.set_title(f'p_unlocked = {belief:.1f}', fontweight='bold')
        ax.set_xlim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

    # Remove extra subplot
    fig.delaxes(axes[5])

    plt.tight_layout()
    plt.savefig(results_dir / "exp2_k_by_belief.png", dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {results_dir / 'exp2_k_by_belief.png'}")
    plt.close()


def print_report(analysis: dict, goodness_of_fit: dict):
    """
    Print formatted experiment report.

    Args:
        analysis: Analysis results dictionary
        goodness_of_fit: Goodness of fit test results
    """
    print("\n" + "="*80)
    print("EXPERIMENT 2: K-SPACE COVERAGE")
    print("="*80)
    print()

    print("OVERVIEW:")
    print("-"*80)
    print(f"Total samples:        {analysis['n_samples']}")
    print(f"Threshold (k≈0):      {analysis['threshold']}")
    print(f"Hypothesis:           >{analysis['hypothesis_threshold']*100:.0f}% should cluster near k≈0")
    print()

    print("RESULTS:")
    print("-"*80)
    stats = analysis['statistics']
    print(f"Mean k_explore:       {stats['mean']:.4f}")
    print(f"Median k_explore:     {stats['median']:.4f}")
    print(f"Std deviation:        {stats['std']:.4f}")
    print(f"Min/Max:              {stats['min']:.4f} / {stats['max']:.4f}")
    print()

    print("CLUSTERING ANALYSIS:")
    print("-"*80)
    print(f"Proportion k < {analysis['threshold']}:  {analysis['proportion_near_zero']*100:.1f}%")
    print(f"95% CI:               [{analysis['ci_95'][0]*100:.1f}%, {analysis['ci_95'][1]*100:.1f}%]")
    print(f"Hypothesis supported: {analysis['hypothesis_supported']}")
    print()
    print(f"Specialist zone (k<0.5): {analysis['specialist_percentage']:.1f}%")
    print(f"Generalist zone (k≥0.5): {analysis['generalist_percentage']:.1f}%")
    print()

    print("CLUSTERING BY BELIEF STATE:")
    print("-"*80)
    for belief, clustering in analysis['belief_clustering'].items():
        print(f"\np_unlocked = {belief:.1f}:")
        print(f"  Mean k:           {clustering['mean_k']:.4f}")
        print(f"  Median k:         {clustering['median_k']:.4f}")
        print(f"  % near zero:      {clustering['proportion_near_zero']*100:.1f}%")

    print("\n" + "-"*80)
    print("STATISTICAL TEST:")
    print("-"*80)
    print(f"\nChi-square Goodness of Fit:")
    print(f"  χ² statistic:     {goodness_of_fit['chi2_statistic']:.4f}")
    print(f"  p-value:          {goodness_of_fit['p_value']:.4f}")
    print(f"  Significant:      {goodness_of_fit['significant']}")
    print(f"  Interpretation:   {goodness_of_fit['interpretation']}")

    print("\n" + "="*80)


def main():
    """
    Main experiment execution function.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 2: K-SPACE COVERAGE")
    print("="*80)
    print("\nTesting if k≈0 clustering emerges naturally.")
    print("Samples: 1000 random skill combinations")
    print("Belief states: [0.1, 0.3, 0.5, 0.7, 0.9]")
    print()

    # Set random seed for reproducibility
    set_seed(42)

    # Initialize experiment runner
    runner = ExperimentRunner(
        experiment_name="exp2_k_space_coverage",
        results_dir="validation/results"
    )

    # Run k-space sampling
    print("Generating random skill combinations and computing k_explore...")
    results = run_k_space_sampling(n_samples=1000)

    # Store results
    runner.results['raw_data']['k_space_samples'] = results

    # Analyze k-distribution
    print("\nAnalyzing k-distribution...")
    analysis = analyze_k_distribution(results, threshold=0.05)

    # Goodness of fit test
    goodness_of_fit = test_goodness_of_fit(analysis['k_values'])

    # Add to results
    runner.results['analysis'] = analysis
    runner.results['goodness_of_fit'] = goodness_of_fit

    # Generate plots
    print("Generating plots...")
    results_dir = Path("validation/results")
    generate_plots(analysis, results_dir)

    # Save results
    filepath = runner.save_results()

    # Print report
    print_report(analysis, goodness_of_fit)

    return analysis


if __name__ == "__main__":
    main()
