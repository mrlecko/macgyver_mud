"""
Plotting utilities for validation experiments.

Provides standardized visualizations for experimental results.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


def plot_condition_comparison(conditions: Dict[str, List[float]],
                              title: str = "Condition Comparison",
                              ylabel: str = "Performance",
                              save_path: str = None):
    """
    Plot boxplot comparison of conditions with individual points.

    Args:
        conditions: Dict mapping condition names to data lists
        title: Plot title
        ylabel: Y-axis label
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    condition_names = list(conditions.keys())
    data = [conditions[name] for name in condition_names]

    # Boxplot
    bp = ax.boxplot(data, labels=condition_names, patch_artist=True,
                   showmeans=True, meanline=True)

    # Color boxes
    colors = plt.cm.Set3(np.linspace(0, 1, len(condition_names)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    # Add individual points with jitter
    for i, (name, values) in enumerate(conditions.items(), 1):
        y = values
        x = np.random.normal(i, 0.04, size=len(y))
        ax.scatter(x, y, alpha=0.3, s=20, color='black')

    ax.set_ylabel(ylabel, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")

    plt.show()


def plot_distribution_comparison(conditions: Dict[str, List[float]],
                                 title: str = "Distribution Comparison",
                                 xlabel: str = "Value",
                                 save_path: str = None):
    """
    Plot overlaid histograms/KDE of conditions.

    Args:
        conditions: Dict mapping condition names to data lists
        title: Plot title
        xlabel: X-axis label
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for name, data in conditions.items():
        ax.hist(data, bins=20, alpha=0.4, label=name, density=True)
        # KDE overlay
        from scipy.stats import gaussian_kde
        if len(data) > 1:
            kde = gaussian_kde(data)
            x_range = np.linspace(min(data), max(data), 100)
            ax.plot(x_range, kde(x_range), linewidth=2, label=f'{name} (KDE)')

    ax.set_xlabel(xlabel, fontweight='bold')
    ax.set_ylabel('Density', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")

    plt.show()


def plot_scatter_with_regression(x: List[float], y: List[float],
                                 xlabel: str = "X",
                                 ylabel: str = "Y",
                                 title: str = "Correlation Plot",
                                 save_path: str = None):
    """
    Scatter plot with regression line and confidence interval.

    Args:
        x: X values
        y: Y values
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter
    ax.scatter(x, y, alpha=0.6, s=50, edgecolors='black', linewidth=0.5)

    # Regression line
    from scipy.stats import linregress
    slope, intercept, r_value, p_value, std_err = linregress(x, y)

    x_line = np.array([min(x), max(x)])
    y_line = slope * x_line + intercept

    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'y = {slope:.3f}x + {intercept:.3f}')

    # Add stats text
    stats_text = f'r = {r_value:.3f}\nr² = {r_value**2:.3f}\np = {p_value:.4f}'
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel(xlabel, fontweight='bold')
    ax.set_ylabel(ylabel, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")

    plt.show()


def plot_k_distribution(k_values: List[float],
                       title: str = "k-Coefficient Distribution",
                       highlight_zones: bool = True,
                       save_path: str = None):
    """
    Plot k-value distribution with specialist/generalist zones.

    Args:
        k_values: List of k-coefficients
        title: Plot title
        highlight_zones: Whether to shade specialist/generalist zones
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Histogram
    n, bins, patches = ax.hist(k_values, bins=30, alpha=0.7, edgecolor='black',
                               color='steelblue', density=True)

    # KDE overlay
    from scipy.stats import gaussian_kde
    if len(k_values) > 1:
        kde = gaussian_kde(k_values)
        x_range = np.linspace(0, 1, 200)
        ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')

    if highlight_zones:
        # Specialist zone (k < 0.5)
        ax.axvspan(0, 0.5, alpha=0.2, color='red', label='Specialist (k < 0.5)')
        # Generalist zone (k > 0.5)
        ax.axvspan(0.5, 1.0, alpha=0.2, color='green', label='Generalist (k > 0.5)')
        # k≈0 line
        ax.axvline(0.05, color='darkred', linestyle='--', linewidth=2,
                  label='k≈0 threshold', alpha=0.7)

    ax.set_xlabel('k-coefficient', fontweight='bold')
    ax.set_ylabel('Density', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(0, 1)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Add statistics
    mean_k = np.mean(k_values)
    median_k = np.median(k_values)
    pct_specialist = 100 * np.mean(np.array(k_values) < 0.5)

    stats_text = f'Mean: {mean_k:.3f}\nMedian: {median_k:.3f}\n< 0.5: {pct_specialist:.1f}%'
    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")

    plt.show()


def plot_performance_over_episodes(episode_data: Dict[str, List[List[float]]],
                                   title: str = "Performance Over Episodes",
                                   ylabel: str = "Performance",
                                   save_path: str = None):
    """
    Plot performance trajectories over episodes with confidence bands.

    Args:
        episode_data: Dict mapping condition names to lists of episode trajectories
        title: Plot title
        ylabel: Y-axis label
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.tab10(np.linspace(0, 1, len(episode_data)))

    for (name, trajectories), color in zip(episode_data.items(), colors):
        # Convert to array for easier computation
        arr = np.array(trajectories)
        mean_traj = np.mean(arr, axis=0)
        std_traj = np.std(arr, axis=0)
        sem_traj = std_traj / np.sqrt(len(trajectories))

        episodes = np.arange(len(mean_traj))

        # Plot mean
        ax.plot(episodes, mean_traj, label=name, color=color, linewidth=2)

        # Confidence band (95% CI)
        ci = 1.96 * sem_traj
        ax.fill_between(episodes, mean_traj - ci, mean_traj + ci,
                        alpha=0.2, color=color)

    ax.set_xlabel('Episode', fontweight='bold')
    ax.set_ylabel(ylabel, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")

    plt.show()


def plot_heatmap(data: np.ndarray, xlabels: List[str], ylabels: List[str],
                title: str = "Heatmap",
                xlabel: str = "X", ylabel: str = "Y",
                cmap: str = "coolwarm",
                save_path: str = None):
    """
    Plot heatmap with annotations.

    Args:
        data: 2D array of values
        xlabels: X-axis labels
        ylabels: Y-axis labels
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        cmap: Colormap name
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(data, cmap=cmap, aspect='auto')

    # Set ticks
    ax.set_xticks(np.arange(len(xlabels)))
    ax.set_yticks(np.arange(len(ylabels)))
    ax.set_xticklabels(xlabels)
    ax.set_yticklabels(ylabels)

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate cells
    for i in range(len(ylabels)):
        for j in range(len(xlabels)):
            text = ax.text(j, i, f'{data[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)

    ax.set_xlabel(xlabel, fontweight='bold')
    ax.set_ylabel(ylabel, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to: {save_path}")

    plt.show()
