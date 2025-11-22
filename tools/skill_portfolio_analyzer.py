#!/usr/bin/env python3
"""
Skill Portfolio Analyzer - Geometric Lens Tool #1

Analyzes the k-space coverage of a skill set.
No performance claims, just descriptive geometry.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring import expected_goal_value, expected_info_gain
from scoring_silver import build_silver_stamp
import math


def calculate_k_explore(goal, info, eps=1e-9):
    """Calculate k_explore from goal and info."""
    g = max(0.0, abs(goal)) + eps
    i = max(0.0, info) + eps
    gm = math.sqrt(g * i)
    am = (g + i) / 2
    return gm / am if am > 0 else 0.0


def calculate_k_efficiency(goal, info, cost, eps=1e-9):
    """Calculate k_efficiency from goal, info, and cost."""
    g = max(0.0, abs(goal)) + eps
    i = max(0.0, info) + eps
    c = max(0.0, cost) + eps
    benefit = g + i
    gm = math.sqrt(benefit * c)
    am = (benefit + c) / 2
    return gm / am if am > 0 else 0.0


def analyze_skill_at_belief(skill, p_unlocked):
    """Calculate geometric properties of skill at given belief."""
    # Use silver stamp for accurate calculation
    stamp = build_silver_stamp(skill['name'], skill.get('cost', 1.0), p_unlocked)

    goal = stamp['goal_value']
    info = stamp['info_gain']
    cost = stamp['cost']
    k_explore = stamp['k_explore']
    k_efficiency = stamp['k_efficiency']

    return {
        'skill': skill['name'],
        'p_unlocked': p_unlocked,
        'goal': goal,
        'info': info,
        'cost': cost,
        'k_explore': k_explore,
        'k_efficiency': k_efficiency
    }


def analyze_portfolio(skills, belief_points=None):
    """
    Analyze geometric properties of skill portfolio.

    Returns descriptive statistics about k-space coverage.
    """
    if belief_points is None:
        belief_points = [0.1, 0.3, 0.5, 0.7, 0.9]

    results = []
    for p in belief_points:
        for skill in skills:
            analysis = analyze_skill_at_belief(skill, p)
            results.append(analysis)

    return results


def plot_k_space_coverage(results, output_path='k_space_coverage.png'):
    """Visualize k-space coverage of skill portfolio."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Extract data
    k_explore_vals = [r['k_explore'] for r in results]
    k_efficiency_vals = [r['k_efficiency'] for r in results]
    goal_vals = [r['goal'] for r in results]
    info_vals = [r['info'] for r in results]

    # 1. k_explore distribution
    ax = axes[0, 0]
    ax.hist(k_explore_vals, bins=20, alpha=0.7, edgecolor='black')
    ax.set_xlabel('k_explore')
    ax.set_ylabel('Frequency')
    ax.set_title('k_explore Distribution')
    ax.axvline(np.mean(k_explore_vals), color='red', linestyle='--',
               label=f'Mean: {np.mean(k_explore_vals):.2f}')
    ax.legend()

    # 2. k_efficiency distribution
    ax = axes[0, 1]
    ax.hist(k_efficiency_vals, bins=20, alpha=0.7, edgecolor='black', color='green')
    ax.set_xlabel('k_efficiency')
    ax.set_ylabel('Frequency')
    ax.set_title('k_efficiency Distribution')
    ax.axvline(np.mean(k_efficiency_vals), color='red', linestyle='--',
               label=f'Mean: {np.mean(k_efficiency_vals):.2f}')
    ax.legend()

    # 3. Goal-Info space
    ax = axes[1, 0]
    scatter = ax.scatter(goal_vals, info_vals, c=k_explore_vals,
                        cmap='viridis', alpha=0.6, s=100)
    ax.set_xlabel('Goal Value')
    ax.set_ylabel('Info Gain')
    ax.set_title('Goal-Info Space (color = k_explore)')
    plt.colorbar(scatter, ax=ax, label='k_explore')

    # 4. Phase space
    ax = axes[1, 1]
    scatter = ax.scatter(k_explore_vals, k_efficiency_vals,
                        c=goal_vals, cmap='plasma', alpha=0.6, s=100)
    ax.set_xlabel('k_explore (balance)')
    ax.set_ylabel('k_efficiency (benefit/cost)')
    ax.set_title('Geometric Phase Space (color = goal)')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    plt.colorbar(scatter, ax=ax, label='Goal Value')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved visualization: {output_path}")

    return fig


def print_portfolio_summary(results):
    """Print descriptive statistics about portfolio."""
    k_explore_vals = [r['k_explore'] for r in results]
    k_efficiency_vals = [r['k_efficiency'] for r in results]

    print("\n" + "="*60)
    print("SKILL PORTFOLIO ANALYSIS - GEOMETRIC LENS")
    print("="*60)

    print(f"\nTotal skill×belief combinations: {len(results)}")

    print(f"\nk_explore (exploration balance):")
    print(f"  Mean:   {np.mean(k_explore_vals):.3f}")
    print(f"  Median: {np.median(k_explore_vals):.3f}")
    print(f"  Std:    {np.std(k_explore_vals):.3f}")
    print(f"  Min:    {np.min(k_explore_vals):.3f}")
    print(f"  Max:    {np.max(k_explore_vals):.3f}")

    print(f"\nk_efficiency (benefit/cost ratio):")
    print(f"  Mean:   {np.mean(k_efficiency_vals):.3f}")
    print(f"  Median: {np.median(k_efficiency_vals):.3f}")
    print(f"  Std:    {np.std(k_efficiency_vals):.3f}")
    print(f"  Min:    {np.min(k_efficiency_vals):.3f}")
    print(f"  Max:    {np.max(k_efficiency_vals):.3f}")

    # Coverage analysis
    k_explore_bins = {
        'Extreme specialists (k<0.1)': sum(1 for k in k_explore_vals if k < 0.1),
        'Strong specialists (k<0.3)': sum(1 for k in k_explore_vals if 0.1 <= k < 0.3),
        'Moderately balanced (k<0.7)': sum(1 for k in k_explore_vals if 0.3 <= k < 0.7),
        'Highly balanced (k>=0.7)': sum(1 for k in k_explore_vals if k >= 0.7)
    }

    print(f"\nk_explore Coverage:")
    for category, count in k_explore_bins.items():
        pct = 100 * count / len(k_explore_vals)
        print(f"  {category}: {count} ({pct:.1f}%)")

    # Identify gaps
    print(f"\nGaps in k-space:")
    if k_explore_bins['Moderately balanced (k<0.7)'] == 0:
        print("  ⚠ No skills in moderate range (0.3-0.7)")
    if k_explore_bins['Highly balanced (k>=0.7)'] == 0:
        print("  ⚠ No highly balanced skills (k>=0.7)")
    if max(k_explore_vals) < 0.5:
        print(f"  ⚠ Maximum k_explore is only {max(k_explore_vals):.2f}")
        print("    Consider adding multi-objective skills")

    print("\n" + "="*60)


def main():
    """Run portfolio analysis on MacGyver MUD skills."""
    # Define crisp skills
    skills = [
        {'name': 'peek_door', 'cost': 1.0},
        {'name': 'try_door', 'cost': 1.5},
        {'name': 'go_window', 'cost': 5.0}
    ]

    print("Analyzing crisp skill portfolio...")
    results = analyze_portfolio(skills)
    print_portfolio_summary(results)
    plot_k_space_coverage(results, 'portfolio_crisp.png')

    # Now with balanced skills added
    skills_with_balanced = skills + [
        {'name': 'probe_and_try', 'cost': 2.0},
        {'name': 'informed_window', 'cost': 3.5},
        {'name': 'exploratory_action', 'cost': 2.5},
        {'name': 'adaptive_peek', 'cost': 1.8}
    ]

    print("\n\nAnalyzing portfolio with balanced skills added...")
    results_balanced = analyze_portfolio(skills_with_balanced)
    print_portfolio_summary(results_balanced)
    plot_k_space_coverage(results_balanced, 'portfolio_hybrid.png')

    print("\n✓ Analysis complete.")
    print("  Generated: portfolio_crisp.png, portfolio_hybrid.png")


if __name__ == '__main__':
    main()
