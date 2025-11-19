"""
Experiment utilities for running controlled validation tests.

Provides experiment running, result collection, and reproducibility utilities.
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Callable
from datetime import datetime


class ExperimentRunner:
    """
    Run experiments with proper controls and result tracking.
    """

    def __init__(self, experiment_name: str, results_dir: str = "validation/results"):
        self.experiment_name = experiment_name
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            'experiment_name': experiment_name,
            'timestamp': datetime.now().isoformat(),
            'conditions': {},
            'raw_data': {},
            'summary': {}
        }

    def run_condition(self, condition_name: str, trial_func: Callable,
                      n_trials: int = 100, **kwargs) -> List[Any]:
        """
        Run a single experimental condition with multiple trials.

        Args:
            condition_name: Name of this condition
            trial_func: Function that runs one trial, returns result
            n_trials: Number of trials to run
            **kwargs: Additional arguments to pass to trial_func

        Returns:
            List of trial results
        """
        print(f"\nRunning condition: {condition_name}")
        print(f"  Trials: {n_trials}")

        results = []
        start_time = time.time()

        for trial in range(n_trials):
            if (trial + 1) % 20 == 0:
                print(f"  Progress: {trial + 1}/{n_trials}", end='\r')

            result = trial_func(**kwargs)
            results.append(result)

        elapsed = time.time() - start_time
        print(f"  Completed in {elapsed:.2f}s")

        self.results['conditions'][condition_name] = {
            'n_trials': n_trials,
            'elapsed_time': elapsed,
            'kwargs': kwargs
        }

        self.results['raw_data'][condition_name] = results

        return results

    def save_results(self, filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.experiment_name}_{timestamp}.json"

        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n✓ Results saved to: {filepath}")
        return filepath

    def add_summary(self, key: str, value: Any):
        """Add summary statistics or interpretation."""
        self.results['summary'][key] = value

    def get_condition_data(self, condition_name: str) -> List[Any]:
        """Retrieve raw data for a condition."""
        return self.results['raw_data'].get(condition_name, [])


def set_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    print(f"✓ Random seed set to: {seed}")


def extract_metric(results: List[Dict], metric_name: str) -> List[float]:
    """
    Extract a specific metric from results dictionaries.

    Args:
        results: List of result dicts
        metric_name: Key to extract (supports dot notation for nested)

    Returns:
        List of extracted values
    """
    values = []

    for result in results:
        if '.' in metric_name:
            # Handle nested keys like 'stats.mean'
            keys = metric_name.split('.')
            value = result
            for key in keys:
                value = value.get(key, None)
                if value is None:
                    break
        else:
            value = result.get(metric_name, None)

        if value is not None:
            values.append(value)

    return values


def compare_conditions(data: Dict[str, List[float]], metric_name: str = "value") -> Dict:
    """
    Compare multiple conditions and return formatted comparison.

    Args:
        data: Dict mapping condition names to lists of values
        metric_name: Name of the metric being compared

    Returns:
        Dict with comparison summary
    """
    from .stats_utils import compute_summary_stats

    comparison = {
        'metric': metric_name,
        'conditions': {}
    }

    for condition_name, values in data.items():
        stats = compute_summary_stats(values)
        comparison['conditions'][condition_name] = stats

    # Find best condition (highest mean)
    best_condition = max(comparison['conditions'].items(),
                        key=lambda x: x[1]['mean'])

    comparison['best_condition'] = {
        'name': best_condition[0],
        'mean': best_condition[1]['mean'],
        'ci95': (best_condition[1]['ci95_lower'], best_condition[1]['ci95_upper'])
    }

    return comparison


def load_experiment_results(filepath: str) -> Dict:
    """Load saved experiment results from JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)


def print_progress_bar(iteration: int, total: int, prefix: str = '',
                       suffix: str = '', length: int = 50):
    """Print a progress bar."""
    percent = 100 * (iteration / float(total))
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent:.1f}% {suffix}', end='')
    if iteration == total:
        print()


class ConditionComparator:
    """
    Compare multiple experimental conditions with statistical tests.
    """

    def __init__(self, conditions: Dict[str, List[float]]):
        """
        Args:
            conditions: Dict mapping condition names to result lists
        """
        self.conditions = conditions
        self.n_conditions = len(conditions)

    def pairwise_comparisons(self, alpha: float = 0.05) -> Dict:
        """
        Perform all pairwise t-tests with Bonferroni correction.

        Returns:
            Dict with all pairwise comparison results
        """
        from .stats_utils import independent_t_test, bonferroni_correction
        from itertools import combinations

        condition_names = list(self.conditions.keys())
        pairs = list(combinations(condition_names, 2))

        results = {}
        p_values = []

        for cond1, cond2 in pairs:
            data1 = self.conditions[cond1]
            data2 = self.conditions[cond2]

            test_result = independent_t_test(data1, data2, alpha=alpha)

            if test_result['valid']:
                p_values.append(test_result['p_value'])
                results[f"{cond1}_vs_{cond2}"] = test_result

        # Bonferroni correction
        if p_values:
            correction = bonferroni_correction(p_values, alpha=alpha)
            results['bonferroni_correction'] = correction

        return results

    def anova(self, alpha: float = 0.05) -> Dict:
        """
        Perform one-way ANOVA across all conditions.

        Returns:
            ANOVA results
        """
        from .stats_utils import anova_one_way

        return anova_one_way(self.conditions, alpha=alpha)

    def rank_conditions(self) -> List[tuple]:
        """
        Rank conditions by mean performance.

        Returns:
            List of (condition_name, mean) tuples, sorted descending
        """
        means = [(name, np.mean(data)) for name, data in self.conditions.items()]
        return sorted(means, key=lambda x: x[1], reverse=True)


def create_experiment_report(experiment_name: str, results: Dict,
                            statistical_tests: Dict) -> str:
    """
    Create a formatted text report of experiment results.

    Args:
        experiment_name: Name of experiment
        results: Experiment results dict
        statistical_tests: Dict of statistical test results

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"EXPERIMENT REPORT: {experiment_name}")
    lines.append("=" * 80)
    lines.append(f"Timestamp: {results.get('timestamp', 'unknown')}")
    lines.append("")

    # Conditions summary
    lines.append("CONDITIONS:")
    lines.append("-" * 80)
    for cond_name, cond_info in results.get('conditions', {}).items():
        n_trials = cond_info.get('n_trials', 0)
        elapsed = cond_info.get('elapsed_time', 0)
        lines.append(f"  {cond_name}: {n_trials} trials ({elapsed:.2f}s)")

    lines.append("")

    # Statistical tests
    lines.append("STATISTICAL TESTS:")
    lines.append("-" * 80)
    for test_name, test_result in statistical_tests.items():
        lines.append(f"\n{test_name}:")
        if isinstance(test_result, dict):
            for key, value in test_result.items():
                if key == 'interpretation':
                    lines.append(f"  → {value}")
                elif isinstance(value, float):
                    lines.append(f"  {key}: {value:.4f}")
                elif not isinstance(value, (dict, list)):
                    lines.append(f"  {key}: {value}")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)
