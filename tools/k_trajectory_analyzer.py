#!/usr/bin/env python3
"""
k-Trajectory Analyzer - Geometric Lens Tool #2

Analyzes how geometric properties evolve during episodes.
Descriptive analysis, no causal claims.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import os


def get_episode_k_trajectory(session, episode_id):
    """Extract k-trajectory from Neo4j episode."""
    query = """
    MATCH (e:Episode {id: $episode_id})-[:HAS_STEP]->(s:Step)
    WHERE s.silver_stamp IS NOT NULL
    WITH s, apoc.convert.fromJsonMap(s.silver_stamp) AS stamp
    RETURN s.step_index AS step,
           s.p_before AS belief,
           stamp.k_explore AS k_explore,
           stamp.k_efficiency AS k_efficiency,
           stamp.skill_name AS skill,
           s.success AS success
    ORDER BY s.step_index
    """
    result = session.run(query, episode_id=episode_id)

    trajectory = []
    for record in result:
        trajectory.append({
            'step': record['step'],
            'belief': record['belief'],
            'k_explore': record['k_explore'],
            'k_efficiency': record['k_efficiency'],
            'skill': record['skill'],
            'success': record['success']
        })

    return trajectory


def get_all_episode_trajectories(session, limit=50):
    """Get k-trajectories from multiple episodes."""
    query = """
    MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
    WHERE s.silver_stamp IS NOT NULL
    WITH DISTINCT e
    RETURN e.id AS episode_id
    ORDER BY e.created_at DESC
    LIMIT $limit
    """
    result = session.run(query, limit=limit)

    trajectories = []
    for record in result:
        traj = get_episode_k_trajectory(session, record['episode_id'])
        if traj:
            trajectories.append(traj)

    return trajectories


def analyze_trajectory_shape(trajectory):
    """Characterize the shape of a k-trajectory."""
    k_values = [t['k_explore'] for t in trajectory]

    if len(k_values) < 2:
        return {'trend': 'insufficient_data'}

    # Linear trend
    steps = np.arange(len(k_values))
    slope, _ = np.polyfit(steps, k_values, 1)

    # Monotonicity
    differences = np.diff(k_values)
    monotonic_decrease = all(d <= 0 for d in differences)
    monotonic_increase = all(d >= 0 for d in differences)

    return {
        'trend': 'decreasing' if slope < -0.01 else 'increasing' if slope > 0.01 else 'flat',
        'slope': slope,
        'monotonic_decrease': monotonic_decrease,
        'monotonic_increase': monotonic_increase,
        'initial_k': k_values[0],
        'final_k': k_values[-1],
        'mean_k': np.mean(k_values),
        'std_k': np.std(k_values),
        'range_k': max(k_values) - min(k_values)
    }


def plot_trajectories(trajectories, output_path='k_trajectories.png'):
    """Visualize k-trajectories."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Individual k_explore trajectories
    ax = axes[0, 0]
    for traj in trajectories[:20]:  # Plot first 20 to avoid clutter
        k_vals = [t['k_explore'] for t in traj]
        steps = range(len(k_vals))
        ax.plot(steps, k_vals, alpha=0.3, linewidth=1)

    ax.set_xlabel('Step')
    ax.set_ylabel('k_explore')
    ax.set_title(f'k_explore Trajectories (n={min(20, len(trajectories))})')
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)

    # 2. Mean trajectory with std bands
    ax = axes[0, 1]
    max_steps = max(len(t) for t in trajectories)
    mean_traj = []
    std_traj = []

    for step in range(max_steps):
        k_at_step = [t[step]['k_explore'] for t in trajectories if step < len(t)]
        if k_at_step:
            mean_traj.append(np.mean(k_at_step))
            std_traj.append(np.std(k_at_step))

    steps = range(len(mean_traj))
    ax.plot(steps, mean_traj, 'b-', linewidth=2, label='Mean')
    ax.fill_between(steps,
                     np.array(mean_traj) - np.array(std_traj),
                     np.array(mean_traj) + np.array(std_traj),
                     alpha=0.3, label='±1 std')
    ax.set_xlabel('Step')
    ax.set_ylabel('k_explore')
    ax.set_title('Mean k_explore Trajectory')
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Distribution of slopes
    ax = axes[1, 0]
    shapes = [analyze_trajectory_shape(t) for t in trajectories]
    slopes = [s['slope'] for s in shapes if s['trend'] != 'insufficient_data']

    ax.hist(slopes, bins=20, alpha=0.7, edgecolor='black')
    ax.axvline(0, color='red', linestyle='--', label='Zero slope')
    ax.axvline(np.mean(slopes), color='blue', linestyle='--',
               label=f'Mean: {np.mean(slopes):.3f}')
    ax.set_xlabel('Slope (k_explore change per step)')
    ax.set_ylabel('Frequency')
    ax.set_title('Trajectory Slope Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Initial vs Final k_explore
    ax = axes[1, 1]
    initial_k = [s['initial_k'] for s in shapes if s['trend'] != 'insufficient_data']
    final_k = [s['final_k'] for s in shapes if s['trend'] != 'insufficient_data']

    ax.scatter(initial_k, final_k, alpha=0.5, s=50)
    ax.plot([0, 1], [0, 1], 'r--', label='No change')
    ax.set_xlabel('Initial k_explore')
    ax.set_ylabel('Final k_explore')
    ax.set_title('Initial vs Final k_explore')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved trajectory visualization: {output_path}")


def print_trajectory_summary(trajectories):
    """Print descriptive statistics about trajectories."""
    shapes = [analyze_trajectory_shape(t) for t in trajectories]
    valid_shapes = [s for s in shapes if s['trend'] != 'insufficient_data']

    print("\n" + "="*60)
    print("K-TRAJECTORY ANALYSIS - GEOMETRIC LENS")
    print("="*60)

    print(f"\nEpisodes analyzed: {len(trajectories)}")
    print(f"Valid trajectories: {len(valid_shapes)}")

    if not valid_shapes:
        print("⚠ No valid trajectories found")
        return

    # Trend distribution
    trends = {}
    for s in valid_shapes:
        trends[s['trend']] = trends.get(s['trend'], 0) + 1

    print(f"\nTrend distribution:")
    for trend, count in trends.items():
        pct = 100 * count / len(valid_shapes)
        print(f"  {trend}: {count} ({pct:.1f}%)")

    # Slope statistics
    slopes = [s['slope'] for s in valid_shapes]
    print(f"\nSlope statistics:")
    print(f"  Mean:   {np.mean(slopes):.4f}")
    print(f"  Median: {np.median(slopes):.4f}")
    print(f"  Std:    {np.std(slopes):.4f}")

    # Monotonicity
    mono_dec = sum(1 for s in valid_shapes if s['monotonic_decrease'])
    mono_inc = sum(1 for s in valid_shapes if s['monotonic_increase'])

    print(f"\nMonotonicity:")
    print(f"  Monotonic decrease: {mono_dec} ({100*mono_dec/len(valid_shapes):.1f}%)")
    print(f"  Monotonic increase: {mono_inc} ({100*mono_inc/len(valid_shapes):.1f}%)")

    # k_explore range
    initial_k = [s['initial_k'] for s in valid_shapes]
    final_k = [s['final_k'] for s in valid_shapes]

    print(f"\nk_explore values:")
    print(f"  Initial - Mean: {np.mean(initial_k):.3f}, Std: {np.std(initial_k):.3f}")
    print(f"  Final   - Mean: {np.mean(final_k):.3f}, Std: {np.std(final_k):.3f}")

    # Observation (not claim)
    mean_slope = np.mean(slopes)
    if mean_slope < -0.01:
        print(f"\nObservation: Mean slope is negative ({mean_slope:.4f})")
        print("  → k_explore tends to decrease over episodes")
        print("  (Note: Descriptive observation, not causal claim)")
    elif mean_slope > 0.01:
        print(f"\nObservation: Mean slope is positive ({mean_slope:.4f})")
        print("  → k_explore tends to increase over episodes")
    else:
        print(f"\nObservation: Mean slope near zero ({mean_slope:.4f})")
        print("  → k_explore relatively stable during episodes")

    print("\n" + "="*60)


def main():
    """Run k-trajectory analysis."""
    # Connect to Neo4j
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session(database="neo4j") as session:
            print("Fetching episode trajectories from Neo4j...")
            trajectories = get_all_episode_trajectories(session, limit=50)

            if not trajectories:
                print("⚠ No episodes with silver gauge data found")
                print("  Run some episodes first: python runner.py")
                return

            print(f"✓ Loaded {len(trajectories)} episodes")

            print_trajectory_summary(trajectories)
            plot_trajectories(trajectories)

            print("\n✓ Analysis complete.")
            print("  Generated: k_trajectories.png")

    finally:
        driver.close()


if __name__ == '__main__':
    main()
