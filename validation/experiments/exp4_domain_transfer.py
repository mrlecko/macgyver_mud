"""
Experiment 4: Domain Transfer

Test if Silver Gauge k-clustering transfers to new domains.

Hypothesis: The k≈0 clustering phenomenon should appear in other crisp decision domains,
demonstrating that Silver Gauge captures domain-invariant structure.

Controls:
- Fixed random seed for reproducibility
- Two new simple domains: Foraging, Navigation
- Same k-calculation methodology
- Statistical comparison across domains

Metrics:
- K-distribution in each domain
- Clustering statistics comparison
- Cross-domain k-coefficient correlation

Statistical test: Chi-square goodness of fit per domain
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from pathlib import Path
from scipy import stats

# Import validation utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.experiment_utils import ExperimentRunner, set_seed
from utils.stats_utils import compute_summary_stats, bootstrap_ci
from utils.plot_utils import plot_k_distribution


# ============================================================================
# Domain Implementations
# ============================================================================

class ForagingDomain:
    """
    Simple foraging domain: agent decides whether to forage or relocate.

    State: belief about food availability (p_food_available)
    Actions:
    - search_area: Information-gathering (reveals food state)
    - forage_here: Exploit current area
    - move_to_new_area: Safe fallback (guaranteed small reward)
    """

    @staticmethod
    def calculate_goal_value(action: str, p_food: float) -> float:
        """Calculate expected goal value for an action."""
        if action == 'search_area':
            return 0.0  # Pure information gathering

        elif action == 'forage_here':
            # Risky: high reward if food present, penalty if not
            return p_food * 10.0 - (1 - p_food) * 3.0

        elif action == 'move_to_new_area':
            # Safe: guaranteed small reward
            return 4.0

        return 0.0

    @staticmethod
    def calculate_info_gain(action: str, p_food: float) -> float:
        """Calculate expected information gain."""
        if action == 'search_area':
            # Direct observation of food state
            return _entropy(p_food)

        elif action == 'forage_here':
            # Might reveal info through success/failure
            return 0.3 * _entropy(p_food)

        elif action == 'move_to_new_area':
            # No info about current area
            return 0.0

        return 0.0

    @staticmethod
    def get_actions():
        """Get all available actions with costs."""
        return [
            {'name': 'search_area', 'cost': 1.0},
            {'name': 'forage_here', 'cost': 1.5},
            {'name': 'move_to_new_area', 'cost': 2.0}
        ]


class NavigationDomain:
    """
    Simple navigation domain: agent chooses route to destination.

    State: belief about shortcut safety (p_shortcut_safe)
    Actions:
    - scout_shortcut: Check if shortcut is safe
    - take_shortcut: Risky fast route
    - take_main_road: Safe slow route
    """

    @staticmethod
    def calculate_goal_value(action: str, p_safe: float) -> float:
        """Calculate expected goal value for an action."""
        if action == 'scout_shortcut':
            return 0.0  # Pure information gathering

        elif action == 'take_shortcut':
            # Risky: fast if safe, dangerous if not
            return p_safe * 10.0 - (1 - p_safe) * 5.0

        elif action == 'take_main_road':
            # Safe but slow
            return 5.0

        return 0.0

    @staticmethod
    def calculate_info_gain(action: str, p_safe: float) -> float:
        """Calculate expected information gain."""
        if action == 'scout_shortcut':
            # Direct observation
            return _entropy(p_safe)

        elif action == 'take_shortcut':
            # Might learn through outcome
            return 0.2 * _entropy(p_safe)

        elif action == 'take_main_road':
            # No info about shortcut
            return 0.0

        return 0.0

    @staticmethod
    def get_actions():
        """Get all available actions with costs."""
        return [
            {'name': 'scout_shortcut', 'cost': 1.0},
            {'name': 'take_shortcut', 'cost': 1.2},
            {'name': 'take_main_road', 'cost': 2.5}
        ]


class MacGyverDomain:
    """
    Original MacGyver domain for comparison.
    """

    @staticmethod
    def calculate_goal_value(action: str, p_unlocked: float) -> float:
        """Calculate expected goal value."""
        if action == 'peek_door':
            return 0.0

        elif action == 'try_door':
            return p_unlocked * 10.0 - (1 - p_unlocked) * 3.0

        elif action == 'go_window':
            return 10.0 - 6.0  # Reward - slow penalty

        return 0.0

    @staticmethod
    def calculate_info_gain(action: str, p_unlocked: float) -> float:
        """Calculate expected information gain."""
        if action == 'peek_door':
            return _entropy(p_unlocked)
        elif action == 'try_door':
            return 0.0
        elif action == 'go_window':
            return 0.0
        return 0.0

    @staticmethod
    def get_actions():
        """Get all available actions with costs."""
        return [
            {'name': 'peek_door', 'cost': 1.0},
            {'name': 'try_door', 'cost': 1.5},
            {'name': 'go_window', 'cost': 2.0}
        ]


def _entropy(p: float) -> float:
    """Calculate binary entropy."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    q = 1.0 - p
    return -(p * np.log2(p) + q * np.log2(q))


def _ensure_positive(x: float, eps: float = 1e-9) -> float:
    """Ensure positive value for mean calculations."""
    return max(0.0, float(x)) + eps


def _harmonic_mean(a: float, b: float) -> float:
    """Harmonic mean of two positive numbers."""
    a = _ensure_positive(a)
    b = _ensure_positive(b)
    return 2.0 / (1.0 / a + 1.0 / b)


def _geometric_mean(a: float, b: float) -> float:
    """Geometric mean of two positive numbers."""
    a = _ensure_positive(a)
    b = _ensure_positive(b)
    return np.sqrt(a * b)


def _arithmetic_mean(a: float, b: float) -> float:
    """Arithmetic mean of two positive numbers."""
    a = _ensure_positive(a)
    b = _ensure_positive(b)
    return 0.5 * (a + b)


def calculate_k_explore(domain, action: dict, belief: float) -> float:
    """
    Calculate k_explore coefficient for an action in a domain.

    Args:
        domain: Domain class with calculation methods
        action: Action dict with name and cost
        belief: Belief probability

    Returns:
        k_explore value
    """
    goal = abs(domain.calculate_goal_value(action['name'], belief))
    info = domain.calculate_info_gain(action['name'], belief)

    # Pythagorean means for exploration shape
    g = _ensure_positive(goal)
    i = _ensure_positive(info)

    hm_gi = _harmonic_mean(g, i)
    gm_gi = _geometric_mean(g, i)
    am_gi = _arithmetic_mean(g, i)

    # k_explore coefficient
    k_explore = gm_gi / am_gi if am_gi > 0 else 0.0

    return k_explore


def sample_domain_k_space(domain, n_samples: int = 500,
                          belief_values: list = None) -> list:
    """
    Sample k-space for a domain.

    Args:
        domain: Domain class
        n_samples: Number of samples
        belief_values: List of belief values to test

    Returns:
        List of k_explore values
    """
    if belief_values is None:
        belief_values = np.linspace(0.1, 0.9, 9)

    k_values = []
    actions = domain.get_actions()

    # Sample with varied costs
    for _ in range(n_samples):
        # Randomly select action and belief
        action = actions[np.random.randint(len(actions))].copy()
        belief = np.random.choice(belief_values)

        # Vary cost slightly
        action['cost'] = action['cost'] * np.random.uniform(0.7, 1.3)

        k = calculate_k_explore(domain, action, belief)
        k_values.append(k)

    return k_values


def analyze_domain_clustering(k_values: list, domain_name: str,
                              threshold: float = 0.05) -> dict:
    """
    Analyze k-clustering for a domain.

    Args:
        k_values: List of k_explore values
        domain_name: Name of the domain
        threshold: Near-zero threshold

    Returns:
        Analysis dict
    """
    k_array = np.array(k_values)

    # Statistics
    stats = compute_summary_stats(k_values)

    # Clustering
    near_zero = k_array < threshold
    proportion_near_zero = np.mean(near_zero)

    # Bootstrap CI
    lower_ci, upper_ci = bootstrap_ci(
        near_zero.astype(float),
        statistic=np.mean,
        n_bootstrap=5000,
        alpha=0.05
    )

    # Zone analysis
    specialist_zone = k_array < 0.5
    specialist_pct = np.mean(specialist_zone) * 100

    # Chi-square goodness of fit
    bins = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
    observed_counts, _ = np.histogram(k_array, bins=bins)
    expected_proportions = [0.70, 0.15, 0.10, 0.04, 0.01]
    expected_counts = np.array(expected_proportions) * len(k_values)

    chi2_stat, p_value = stats.chisquare(observed_counts, expected_counts)

    return {
        'domain_name': domain_name,
        'n_samples': len(k_values),
        'statistics': stats,
        'proportion_near_zero': proportion_near_zero,
        'ci_95': (lower_ci, upper_ci),
        'specialist_percentage': specialist_pct,
        'chi2_statistic': chi2_stat,
        'chi2_p_value': p_value,
        'clustering_confirmed': proportion_near_zero > 0.6,  # Lower threshold for transfer
        'k_values': k_values
    }


def compare_domains(domain_analyses: dict) -> dict:
    """
    Compare k-clustering across domains.

    Args:
        domain_analyses: Dict mapping domain names to analysis results

    Returns:
        Comparison results
    """
    domain_names = list(domain_analyses.keys())

    # Compare clustering proportions
    proportions = {name: analysis['proportion_near_zero']
                  for name, analysis in domain_analyses.items()}

    # Compare specialist percentages
    specialist_pcts = {name: analysis['specialist_percentage']
                      for name, analysis in domain_analyses.items()}

    # Cross-domain consistency test
    # H0: All domains show similar clustering
    chi2_values = [analysis['chi2_statistic'] for analysis in domain_analyses.values()]
    p_values = [analysis['chi2_p_value'] for analysis in domain_analyses.values()]

    all_confirm_clustering = all(analysis['clustering_confirmed']
                                 for analysis in domain_analyses.values())

    return {
        'domain_names': domain_names,
        'near_zero_proportions': proportions,
        'specialist_percentages': specialist_pcts,
        'chi2_values': chi2_values,
        'chi2_p_values': p_values,
        'all_domains_cluster': all_confirm_clustering,
        'mean_clustering': np.mean(list(proportions.values())),
        'std_clustering': np.std(list(proportions.values()))
    }


def generate_plots(domain_analyses: dict, results_dir: Path):
    """
    Generate visualization plots.

    Args:
        domain_analyses: Dict of domain analysis results
        results_dir: Directory to save plots
    """
    import matplotlib.pyplot as plt

    # Plot 1: K-distribution for each domain
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (domain_name, analysis) in enumerate(domain_analyses.items()):
        ax = axes[idx]
        k_values = analysis['k_values']

        ax.hist(k_values, bins=30, alpha=0.7, edgecolor='black',
               color='steelblue', density=True)

        # Add zones
        ax.axvspan(0, 0.5, alpha=0.2, color='red', label='Specialist (k<0.5)')
        ax.axvspan(0.5, 1.0, alpha=0.2, color='green', label='Generalist (k≥0.5)')
        ax.axvline(0.05, color='darkred', linestyle='--', linewidth=2,
                  label='k≈0 threshold')

        ax.set_xlabel('k_explore', fontweight='bold')
        ax.set_ylabel('Density', fontweight='bold')
        ax.set_title(f'{domain_name} Domain', fontweight='bold')
        ax.set_xlim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add stats
        stats = analysis['statistics']
        prop = analysis['proportion_near_zero']
        stats_text = f'Mean: {stats["mean"]:.3f}\n<0.05: {prop*100:.1f}%'
        ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(results_dir / "exp4_domain_comparison.png", dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {results_dir / 'exp4_domain_comparison.png'}")
    plt.close()

    # Plot 2: Cross-domain clustering comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    domain_names = list(domain_analyses.keys())
    proportions = [domain_analyses[name]['proportion_near_zero'] * 100
                  for name in domain_names]
    cis = [domain_analyses[name]['ci_95'] for name in domain_names]
    errors = [(p/100 - ci[0])*100 for p, ci in zip(proportions, cis)]

    x_pos = np.arange(len(domain_names))
    ax.bar(x_pos, proportions, yerr=errors, capsize=10, alpha=0.7,
          color='steelblue', edgecolor='black', linewidth=1.5)
    ax.axhline(60, color='red', linestyle='--', linewidth=2,
              label='60% clustering threshold', alpha=0.7)

    ax.set_xlabel('Domain', fontweight='bold')
    ax.set_ylabel('% with k < 0.05', fontweight='bold')
    ax.set_title('Experiment 4: K≈0 Clustering Across Domains',
                fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(domain_names)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(results_dir / "exp4_clustering_comparison.png", dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {results_dir / 'exp4_clustering_comparison.png'}")
    plt.close()


def print_report(domain_analyses: dict, comparison: dict):
    """
    Print formatted experiment report.

    Args:
        domain_analyses: Domain analysis results
        comparison: Cross-domain comparison results
    """
    print("\n" + "="*80)
    print("EXPERIMENT 4: DOMAIN TRANSFER")
    print("="*80)
    print()

    print("CLUSTERING ANALYSIS BY DOMAIN:")
    print("-"*80)

    for domain_name, analysis in domain_analyses.items():
        print(f"\n{domain_name.upper()} DOMAIN:")
        stats = analysis['statistics']
        print(f"  Mean k_explore:       {stats['mean']:.4f}")
        print(f"  Median k_explore:     {stats['median']:.4f}")
        print(f"  Std deviation:        {stats['std']:.4f}")
        print(f"  Proportion k < 0.05:  {analysis['proportion_near_zero']*100:.1f}%")
        print(f"  95% CI:               [{analysis['ci_95'][0]*100:.1f}%, {analysis['ci_95'][1]*100:.1f}%]")
        print(f"  Specialist zone:      {analysis['specialist_percentage']:.1f}%")
        print(f"  χ² statistic:         {analysis['chi2_statistic']:.4f}")
        print(f"  χ² p-value:           {analysis['chi2_p_value']:.4f}")
        print(f"  Clustering confirmed: {analysis['clustering_confirmed']}")

    print("\n" + "-"*80)
    print("CROSS-DOMAIN COMPARISON:")
    print("-"*80)
    print(f"\nAll domains show clustering: {comparison['all_domains_cluster']}")
    print(f"Mean clustering across domains: {comparison['mean_clustering']*100:.1f}%")
    print(f"Std clustering across domains:  {comparison['std_clustering']*100:.1f}%")

    print("\nClustering proportions:")
    for domain, prop in comparison['near_zero_proportions'].items():
        print(f"  {domain:12s}: {prop*100:.1f}%")

    print("\n" + "="*80)


def main():
    """
    Main experiment execution function.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 4: DOMAIN TRANSFER")
    print("="*80)
    print("\nTesting if Silver Gauge clustering transfers to new domains.")
    print("Domains: MacGyver, Foraging, Navigation")
    print("Samples per domain: 500")
    print()

    # Set random seed for reproducibility
    set_seed(42)

    # Initialize experiment runner
    runner = ExperimentRunner(
        experiment_name="exp4_domain_transfer",
        results_dir="validation/results"
    )

    # Define domains
    domains = {
        'MacGyver': MacGyverDomain,
        'Foraging': ForagingDomain,
        'Navigation': NavigationDomain
    }

    # Sample k-space for each domain
    domain_analyses = {}

    for domain_name, domain_class in domains.items():
        print(f"\nSampling k-space for {domain_name} domain...")
        k_values = sample_domain_k_space(domain_class, n_samples=500)

        print(f"Analyzing clustering...")
        analysis = analyze_domain_clustering(k_values, domain_name, threshold=0.05)
        domain_analyses[domain_name] = analysis

    # Cross-domain comparison
    print("\nComparing across domains...")
    comparison = compare_domains(domain_analyses)

    # Store results
    runner.results['domain_analyses'] = {
        name: {k: v for k, v in analysis.items() if k != 'k_values'}
        for name, analysis in domain_analyses.items()
    }
    runner.results['comparison'] = comparison

    # Generate plots
    print("Generating plots...")
    results_dir = Path("validation/results")
    generate_plots(domain_analyses, results_dir)

    # Save results
    filepath = runner.save_results()

    # Print report
    print_report(domain_analyses, comparison)

    return domain_analyses, comparison


if __name__ == "__main__":
    main()
