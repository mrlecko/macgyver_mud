"""
Statistical utilities for validation experiments.

Provides hypothesis testing, effect size calculation, and result interpretation
with conservative statistical practices.
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any
import warnings

warnings.filterwarnings('ignore')


def compute_summary_stats(data: List[float]) -> Dict[str, float]:
    """
    Compute summary statistics for a dataset.

    Args:
        data: List of numeric values

    Returns:
        Dict with mean, median, std, sem, ci95
    """
    arr = np.array(data)
    n = len(arr)

    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    sem = std / np.sqrt(n) if n > 0 else np.nan

    # 95% confidence interval
    ci95 = stats.t.interval(0.95, n-1, loc=mean, scale=sem) if n > 1 else (np.nan, np.nan)

    return {
        'n': n,
        'mean': mean,
        'median': np.median(arr),
        'std': std,
        'sem': sem,
        'ci95_lower': ci95[0],
        'ci95_upper': ci95[1],
        'min': np.min(arr),
        'max': np.max(arr)
    }


def independent_t_test(group1: List[float], group2: List[float],
                       alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform independent samples t-test.

    Args:
        group1: First group data
        group2: Second group data
        alpha: Significance level (default 0.05)

    Returns:
        Dict with test results and interpretation
    """
    arr1 = np.array(group1)
    arr2 = np.array(group2)

    # Check assumptions
    n1, n2 = len(arr1), len(arr2)
    if n1 < 3 or n2 < 3:
        return {
            'valid': False,
            'reason': 'Insufficient sample size (need n >= 3 per group)'
        }

    # Levene's test for equal variances
    levene_stat, levene_p = stats.levene(arr1, arr2)
    equal_var = levene_p > 0.05

    # Independent t-test
    t_stat, p_value = stats.ttest_ind(arr1, arr2, equal_var=equal_var)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(((n1-1)*np.var(arr1, ddof=1) + (n2-1)*np.var(arr2, ddof=1)) / (n1+n2-2))
    cohens_d = (np.mean(arr1) - np.mean(arr2)) / pooled_std if pooled_std > 0 else np.nan

    # Interpretation
    significant = p_value < alpha

    if abs(cohens_d) < 0.2:
        effect = 'negligible'
    elif abs(cohens_d) < 0.5:
        effect = 'small'
    elif abs(cohens_d) < 0.8:
        effect = 'medium'
    else:
        effect = 'large'

    return {
        'valid': True,
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': significant,
        'alpha': alpha,
        'cohens_d': cohens_d,
        'effect_size': effect,
        'equal_variance': equal_var,
        'levene_p': levene_p,
        'mean_diff': np.mean(arr1) - np.mean(arr2),
        'interpretation': _interpret_t_test(significant, cohens_d, effect)
    }


def paired_t_test(before: List[float], after: List[float],
                  alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform paired samples t-test.

    Args:
        before: Before condition data
        after: After condition data
        alpha: Significance level

    Returns:
        Dict with test results
    """
    arr_before = np.array(before)
    arr_after = np.array(after)

    if len(arr_before) != len(arr_after):
        return {
            'valid': False,
            'reason': 'Paired samples must have equal length'
        }

    if len(arr_before) < 3:
        return {
            'valid': False,
            'reason': 'Insufficient sample size (need n >= 3)'
        }

    # Paired t-test
    t_stat, p_value = stats.ttest_rel(arr_before, arr_after)

    # Effect size for paired samples
    diff = arr_after - arr_before
    cohens_d = np.mean(diff) / np.std(diff, ddof=1)

    significant = p_value < alpha

    if abs(cohens_d) < 0.2:
        effect = 'negligible'
    elif abs(cohens_d) < 0.5:
        effect = 'small'
    elif abs(cohens_d) < 0.8:
        effect = 'medium'
    else:
        effect = 'large'

    return {
        'valid': True,
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': significant,
        'alpha': alpha,
        'cohens_d': cohens_d,
        'effect_size': effect,
        'mean_diff': np.mean(diff),
        'interpretation': _interpret_t_test(significant, cohens_d, effect)
    }


def anova_one_way(groups: Dict[str, List[float]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform one-way ANOVA.

    Args:
        groups: Dict mapping group names to data lists
        alpha: Significance level

    Returns:
        Dict with ANOVA results
    """
    group_data = [np.array(data) for data in groups.values()]
    group_names = list(groups.keys())

    # Check sample sizes
    if any(len(g) < 2 for g in group_data):
        return {
            'valid': False,
            'reason': 'All groups need n >= 2'
        }

    # One-way ANOVA
    f_stat, p_value = stats.f_oneway(*group_data)

    significant = p_value < alpha

    # Effect size (eta-squared)
    grand_mean = np.mean(np.concatenate(group_data))
    ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in group_data)
    ss_total = sum((x - grand_mean)**2 for g in group_data for x in g)
    eta_squared = ss_between / ss_total if ss_total > 0 else np.nan

    if eta_squared < 0.01:
        effect = 'negligible'
    elif eta_squared < 0.06:
        effect = 'small'
    elif eta_squared < 0.14:
        effect = 'medium'
    else:
        effect = 'large'

    return {
        'valid': True,
        'f_statistic': f_stat,
        'p_value': p_value,
        'significant': significant,
        'alpha': alpha,
        'eta_squared': eta_squared,
        'effect_size': effect,
        'groups': group_names,
        'group_means': {name: np.mean(groups[name]) for name in group_names},
        'interpretation': _interpret_anova(significant, eta_squared, effect)
    }


def correlation_test(x: List[float], y: List[float],
                     method: str = 'pearson',
                     alpha: float = 0.05) -> Dict[str, Any]:
    """
    Compute correlation and test significance.

    Args:
        x: First variable
        y: Second variable
        method: 'pearson' or 'spearman'
        alpha: Significance level

    Returns:
        Dict with correlation results
    """
    arr_x = np.array(x)
    arr_y = np.array(y)

    if len(arr_x) != len(arr_y):
        return {
            'valid': False,
            'reason': 'Variables must have same length'
        }

    if len(arr_x) < 3:
        return {
            'valid': False,
            'reason': 'Need at least 3 data points'
        }

    # Correlation
    if method == 'pearson':
        r, p_value = stats.pearsonr(arr_x, arr_y)
    elif method == 'spearman':
        r, p_value = stats.spearmanr(arr_x, arr_y)
    else:
        return {
            'valid': False,
            'reason': f'Unknown method: {method}'
        }

    significant = p_value < alpha

    # Interpret strength
    abs_r = abs(r)
    if abs_r < 0.1:
        strength = 'negligible'
    elif abs_r < 0.3:
        strength = 'weak'
    elif abs_r < 0.5:
        strength = 'moderate'
    elif abs_r < 0.7:
        strength = 'strong'
    else:
        strength = 'very strong'

    return {
        'valid': True,
        'r': r,
        'r_squared': r**2,
        'p_value': p_value,
        'significant': significant,
        'alpha': alpha,
        'strength': strength,
        'method': method,
        'interpretation': _interpret_correlation(r, p_value, significant, strength)
    }


def bootstrap_ci(data: List[float], statistic=np.mean,
                 n_bootstrap: int = 10000, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval.

    Args:
        data: Data to bootstrap
        statistic: Function to compute statistic (default: mean)
        n_bootstrap: Number of bootstrap samples
        alpha: Significance level

    Returns:
        (lower_bound, upper_bound) tuple
    """
    arr = np.array(data)
    n = len(arr)

    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(arr, size=n, replace=True)
        bootstrap_stats.append(statistic(sample))

    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

    return lower, upper


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.

    Args:
        p_values: List of p-values
        alpha: Family-wise error rate

    Returns:
        Dict with corrected significance
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests

    significant = [p < corrected_alpha for p in p_values]

    return {
        'n_tests': n_tests,
        'alpha': alpha,
        'corrected_alpha': corrected_alpha,
        'original_p_values': p_values,
        'significant': significant,
        'n_significant': sum(significant)
    }


# Helper functions

def _interpret_t_test(significant: bool, cohens_d: float, effect: str) -> str:
    """Generate interpretation text for t-test."""
    if not significant:
        return f"No significant difference found (effect size: {effect}, d={cohens_d:.3f})"
    else:
        direction = "higher" if cohens_d > 0 else "lower"
        return f"Significant difference found: Group 1 is {direction} (effect size: {effect}, d={cohens_d:.3f})"


def _interpret_anova(significant: bool, eta_squared: float, effect: str) -> str:
    """Generate interpretation text for ANOVA."""
    if not significant:
        return f"No significant differences among groups (effect size: {effect}, η²={eta_squared:.3f})"
    else:
        return f"Significant differences found among groups (effect size: {effect}, η²={eta_squared:.3f})"


def _interpret_correlation(r: float, p_value: float, significant: bool, strength: str) -> str:
    """Generate interpretation text for correlation."""
    direction = "positive" if r > 0 else "negative"
    if not significant:
        return f"No significant correlation (r={r:.3f}, p={p_value:.3f})"
    else:
        return f"Significant {direction} {strength} correlation (r={r:.3f}, p={p_value:.3f})"


def format_result_table(results: Dict[str, Any]) -> str:
    """Format statistical results as readable table."""
    lines = []
    lines.append("=" * 60)
    lines.append("STATISTICAL TEST RESULTS")
    lines.append("=" * 60)

    for key, value in results.items():
        if isinstance(value, float):
            lines.append(f"{key:20s}: {value:.4f}")
        elif isinstance(value, bool):
            lines.append(f"{key:20s}: {value}")
        elif isinstance(value, str):
            lines.append(f"{key:20s}: {value}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k:18s}: {v}")

    lines.append("=" * 60)
    return "\n".join(lines)
