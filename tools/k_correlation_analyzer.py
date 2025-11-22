#!/usr/bin/env python3
"""
K-Correlation Analyzer - Geometric Lens Tool #4

Analyzes correlations between k-values and episode outcomes.
Descriptive statistics, no causal claims.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def get_episode_data(session, limit=100):
    """Get episode-level aggregated k-values and outcomes."""
    query = """
    MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
    WHERE s.silver_stamp IS NOT NULL
    WITH e, s, apoc.convert.fromJsonMap(s.silver_stamp) AS stamp
    ORDER BY s.step_index
    WITH e,
         collect(stamp.k_explore) AS k_explores,
         collect(stamp.k_efficiency) AS k_efficiencies,
         collect(s.success) AS successes,
         count(s) AS step_count
    WHERE size(k_explores) > 0
    WITH e,
         k_explores,
         k_efficiencies,
         successes,
         step_count,
         reduce(sum = 0.0, x IN k_explores | sum + x) / size(k_explores) AS mean_k_explore,
         reduce(sum = 0.0, x IN k_efficiencies | sum + x) / size(k_efficiencies) AS mean_k_efficiency
    RETURN e.id AS episode_id,
           e.door_state AS door_state,
           mean_k_explore,
           reduce(min_val = k_explores[0], x IN k_explores | CASE WHEN x < min_val THEN x ELSE min_val END) AS min_k_explore,
           reduce(max_val = k_explores[0], x IN k_explores | CASE WHEN x > max_val THEN x ELSE max_val END) AS max_k_explore,
           k_explores[0] AS initial_k_explore,
           k_explores[-1] AS final_k_explore,
           mean_k_efficiency,
           any(s IN successes WHERE s = true) AS success,
           step_count
    ORDER BY e.created_at DESC
    LIMIT $limit
    """

    result = session.run(query, limit=limit)

    data = []
    for record in result:
        data.append({
            'episode_id': record['episode_id'],
            'door_state': record['door_state'],
            'mean_k_explore': record['mean_k_explore'],
            'min_k_explore': record['min_k_explore'],
            'max_k_explore': record['max_k_explore'],
            'initial_k_explore': record['initial_k_explore'],
            'final_k_explore': record['final_k_explore'],
            'mean_k_efficiency': record['mean_k_efficiency'],
            'success': record['success'],
            'step_count': record['step_count']
        })

    return data


def analyze_correlations(data):
    """Calculate correlations between k-values and outcomes."""
    if not data:
        return {}

    # Extract variables
    mean_k_explore = np.array([d['mean_k_explore'] for d in data])
    mean_k_efficiency = np.array([d['mean_k_efficiency'] for d in data])
    step_count = np.array([d['step_count'] for d in data])
    success = np.array([1 if d['success'] else 0 for d in data])

    results = {}

    # Only calculate if there's variance
    if np.std(mean_k_explore) > 1e-6:
        # k_explore vs step count
        r_explore_steps, p_explore_steps = stats.pearsonr(mean_k_explore, step_count)
        results['k_explore_vs_steps'] = {
            'r': r_explore_steps,
            'p': p_explore_steps,
            'significant': p_explore_steps < 0.05
        }

        # k_explore vs success
        if len(np.unique(success)) > 1:  # Need variation in success
            r_explore_success, p_explore_success = stats.pointbiserialr(success, mean_k_explore)
            results['k_explore_vs_success'] = {
                'r': r_explore_success,
                'p': p_explore_success,
                'significant': p_explore_success < 0.05
            }
    else:
        results['k_explore_note'] = "No variance in k_explore (all values identical)"

    if np.std(mean_k_efficiency) > 1e-6:
        # k_efficiency vs step count
        r_efficiency_steps, p_efficiency_steps = stats.pearsonr(mean_k_efficiency, step_count)
        results['k_efficiency_vs_steps'] = {
            'r': r_efficiency_steps,
            'p': p_efficiency_steps,
            'significant': p_efficiency_steps < 0.05
        }

        # k_efficiency vs success
        if len(np.unique(success)) > 1:
            r_efficiency_success, p_efficiency_success = stats.pointbiserialr(success, mean_k_efficiency)
            results['k_efficiency_vs_success'] = {
                'r': r_efficiency_success,
                'p': p_efficiency_success,
                'significant': p_efficiency_success < 0.05
            }
    else:
        results['k_efficiency_note'] = "No variance in k_efficiency"

    return results


def plot_correlations(data, output_path='k_correlations.png'):
    """Visualize relationships between k-values and outcomes."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    mean_k_explore = [d['mean_k_explore'] for d in data]
    mean_k_efficiency = [d['mean_k_efficiency'] for d in data]
    step_count = [d['step_count'] for d in data]
    success = [d['success'] for d in data]

    # 1. k_explore vs step count
    ax = axes[0, 0]
    ax.scatter(mean_k_explore, step_count, alpha=0.6)
    ax.set_xlabel('Mean k_explore')
    ax.set_ylabel('Step Count')
    ax.set_title('k_explore vs Episode Length')
    ax.grid(True, alpha=0.3)

    if np.std(mean_k_explore) > 1e-6:
        # Add trend line
        z = np.polyfit(mean_k_explore, step_count, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(mean_k_explore), max(mean_k_explore), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)

    # 2. k_efficiency vs step count
    ax = axes[0, 1]
    ax.scatter(mean_k_efficiency, step_count, alpha=0.6, color='green')
    ax.set_xlabel('Mean k_efficiency')
    ax.set_ylabel('Step Count')
    ax.set_title('k_efficiency vs Episode Length')
    ax.grid(True, alpha=0.3)

    if np.std(mean_k_efficiency) > 1e-6:
        z = np.polyfit(mean_k_efficiency, step_count, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(mean_k_efficiency), max(mean_k_efficiency), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)

    # 3. k_explore by success
    ax = axes[1, 0]
    success_k = [d['mean_k_explore'] for d in data if d['success']]
    failure_k = [d['mean_k_explore'] for d in data if not d['success']]

    if success_k and failure_k:
        ax.violinplot([success_k, failure_k], positions=[1, 2], showmeans=True)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['Success', 'Failure'])
        ax.set_ylabel('Mean k_explore')
        ax.set_title('k_explore Distribution by Outcome')
    else:
        ax.text(0.5, 0.5, 'Insufficient data\n(all success or all failure)',
               ha='center', va='center', transform=ax.transAxes)
    ax.grid(True, alpha=0.3)

    # 4. k_efficiency by success
    ax = axes[1, 1]
    success_eff = [d['mean_k_efficiency'] for d in data if d['success']]
    failure_eff = [d['mean_k_efficiency'] for d in data if not d['success']]

    if success_eff and failure_eff:
        ax.violinplot([success_eff, failure_eff], positions=[1, 2], showmeans=True)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['Success', 'Failure'])
        ax.set_ylabel('Mean k_efficiency')
        ax.set_title('k_efficiency Distribution by Outcome')
    else:
        ax.text(0.5, 0.5, 'Insufficient data\n(all success or all failure)',
               ha='center', va='center', transform=ax.transAxes)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved correlation visualization: {output_path}")


def print_correlation_summary(correlations, data):
    """Print summary of correlation analysis."""
    print("\n" + "="*60)
    print("K-VALUE CORRELATION ANALYSIS - GEOMETRIC LENS")
    print("="*60)

    print(f"\nDataset size: {len(data)} episodes")

    success_rate = sum(1 for d in data if d['success']) / len(data) if data else 0
    print(f"Success rate: {100*success_rate:.1f}%")

    mean_steps = np.mean([d['step_count'] for d in data]) if data else 0
    print(f"Mean steps per episode: {mean_steps:.2f}")

    print(f"\nCorrelation Results:")
    print("-"*60)

    if 'k_explore_note' in correlations:
        print(f"\nk_explore: {correlations['k_explore_note']}")
    else:
        if 'k_explore_vs_steps' in correlations:
            corr = correlations['k_explore_vs_steps']
            sig_marker = "**" if corr['significant'] else ""
            print(f"\nk_explore vs Step Count:")
            print(f"  Correlation: r={corr['r']:.3f}, p={corr['p']:.4f} {sig_marker}")
            print(f"  Interpretation: {'Significant' if corr['significant'] else 'Not significant'}")

        if 'k_explore_vs_success' in correlations:
            corr = correlations['k_explore_vs_success']
            sig_marker = "**" if corr['significant'] else ""
            print(f"\nk_explore vs Success:")
            print(f"  Correlation: r={corr['r']:.3f}, p={corr['p']:.4f} {sig_marker}")
            print(f"  Interpretation: {'Significant' if corr['significant'] else 'Not significant'}")

    if 'k_efficiency_note' in correlations:
        print(f"\nk_efficiency: {correlations['k_efficiency_note']}")
    else:
        if 'k_efficiency_vs_steps' in correlations:
            corr = correlations['k_efficiency_vs_steps']
            sig_marker = "**" if corr['significant'] else ""
            print(f"\nk_efficiency vs Step Count:")
            print(f"  Correlation: r={corr['r']:.3f}, p={corr['p']:.4f} {sig_marker}")
            print(f"  Interpretation: {'Significant' if corr['significant'] else 'Not significant'}")

        if 'k_efficiency_vs_success' in correlations:
            corr = correlations['k_efficiency_vs_success']
            sig_marker = "**" if corr['significant'] else ""
            print(f"\nk_efficiency vs Success:")
            print(f"  Correlation: r={corr['r']:.3f}, p={corr['p']:.4f} {sig_marker}")
            print(f"  Interpretation: {'Significant' if corr['significant'] else 'Not significant'}")

    print("\n" + "="*60)
    print("NOTE: These are descriptive correlations, not causal claims.")
    print("Correlation does not imply causation.")
    print("="*60)


def main():
    """Run correlation analysis."""
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session(database="neo4j") as session:
            print("Fetching episode data from Neo4j...")
            data = get_episode_data(session, limit=100)

            if not data:
                print("⚠ No episodes with silver gauge data found")
                return

            print(f"✓ Loaded {len(data)} episodes")

            correlations = analyze_correlations(data)
            print_correlation_summary(correlations, data)
            plot_correlations(data)

            print("\n✓ Analysis complete.")
            print("  Generated: k_correlations.png")

    finally:
        driver.close()


if __name__ == '__main__':
    main()
