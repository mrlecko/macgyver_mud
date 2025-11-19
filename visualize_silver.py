#!/usr/bin/env python3
"""
Visualization tools for Silver Gauge geometric analysis.

This module provides various visualization strategies for understanding
the geometric structure of active inference decisions.
"""

import json
import sys
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from neo4j import GraphDatabase
import config
from scoring_silver import build_silver_stamp


def extract_silver_data(session) -> List[Dict[str, Any]]:
    """Extract all silver stamps from Neo4j."""
    result = session.run("""
        MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
        WHERE s.silver_stamp IS NOT NULL
        RETURN e.episode_id AS episode_id,
               e.reward_mode AS reward_mode,
               e.door_state AS door_state,
               e.escaped AS escaped,
               s.step_index AS step_index,
               s.silver_stamp AS silver_json,
               s.p_before AS p_before
        ORDER BY e.created_at, s.step_index
    """)

    data = []
    for record in result:
        stamp = json.loads(record["silver_json"])
        data.append({
            'episode_id': record['episode_id'],
            'reward_mode': record['reward_mode'],
            'door_state': record['door_state'],
            'escaped': record['escaped'],
            'step_index': record['step_index'],
            'p_before': record['p_before'],
            **stamp  # Unpack all stamp fields
        })

    return data


def plot_phase_diagram(data: List[Dict], output_file='phase_diagram.png'):
    """
    Plot decisions in (k_explore, k_efficiency) space with time colormap.

    This visualizes the geometric "shape space" of decisions and how
    they evolve over time.
    """
    if not data:
        print("No data to plot")
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    k_explores = [d['k_explore'] for d in data]
    k_efficiencies = [d['k_efficiency'] for d in data]
    timesteps = range(len(data))

    # Scatter with time colormap
    scatter = ax.scatter(k_explores, k_efficiencies,
                         c=timesteps, cmap='viridis',
                         s=100, alpha=0.7, edgecolors='black',
                         linewidths=1)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Timestep', fontsize=12)

    # Annotate quadrants
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(0.5, color='gray', linestyle='--', alpha=0.3, linewidth=1)

    # Quadrant labels
    ax.text(0.75, 0.75, 'Balanced\nExploration',
            ha='center', va='center', alpha=0.4, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.2))
    ax.text(0.25, 0.75, 'Pure\nExploration',
            ha='center', va='center', alpha=0.4, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.2))
    ax.text(0.75, 0.25, 'Efficient\nExploitation',
            ha='center', va='center', alpha=0.4, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.2))
    ax.text(0.25, 0.25, 'Inefficient\nExploitation',
            ha='center', va='center', alpha=0.4, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.2))

    ax.set_xlabel('k_explore (0=pure exploit, 1=balanced)', fontsize=12)
    ax.set_ylabel('k_efficiency (0=poor, 1=excellent)', fontsize=12)
    ax.set_title('Decision Geometry Phase Diagram', fontsize=14, weight='bold')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")


def plot_belief_geometry(output_file='belief_geometry.png'):
    """
    Show how geometry changes with belief state for each skill.

    This reveals how decision shape adapts to uncertainty.
    """
    beliefs = np.linspace(0, 1, 50)
    skills = [
        {'name': 'peek_door', 'cost': 1.0, 'color': 'blue', 'label': 'Peek Door'},
        {'name': 'try_door', 'cost': 1.5, 'color': 'green', 'label': 'Try Door'},
        {'name': 'go_window', 'cost': 2.0, 'color': 'red', 'label': 'Go Window'}
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for skill in skills:
        k_explores = []
        k_efficiencies = []

        for p in beliefs:
            stamp = build_silver_stamp(skill['name'], skill['cost'], p)
            k_explores.append(stamp['k_explore'])
            k_efficiencies.append(stamp['k_efficiency'])

        axes[0].plot(beliefs, k_explores,
                     label=skill['label'], linewidth=2.5,
                     color=skill['color'], alpha=0.8)
        axes[1].plot(beliefs, k_efficiencies,
                     label=skill['label'], linewidth=2.5,
                     color=skill['color'], alpha=0.8)

    # k_explore plot
    axes[0].set_xlabel('Belief p(unlocked)', fontsize=12)
    axes[0].set_ylabel('k_explore', fontsize=12)
    axes[0].set_title('Exploration Shape vs Belief', fontsize=14, weight='bold')
    axes[0].legend(fontsize=10)
    axes[0].grid(alpha=0.3)
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(-0.05, 1.05)

    # Add interpretation zones
    axes[0].axhspan(0, 0.3, alpha=0.1, color='red', label='_')
    axes[0].axhspan(0.3, 0.7, alpha=0.1, color='yellow', label='_')
    axes[0].axhspan(0.7, 1.0, alpha=0.1, color='green', label='_')

    # k_efficiency plot
    axes[1].set_xlabel('Belief p(unlocked)', fontsize=12)
    axes[1].set_ylabel('k_efficiency', fontsize=12)
    axes[1].set_title('Efficiency Shape vs Belief', fontsize=14, weight='bold')
    axes[1].legend(fontsize=10)
    axes[1].grid(alpha=0.3)
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(-0.05, 1.05)

    # Add interpretation zones
    axes[1].axhspan(0, 0.3, alpha=0.1, color='red', label='_')
    axes[1].axhspan(0.3, 0.7, alpha=0.1, color='yellow', label='_')
    axes[1].axhspan(0.7, 1.0, alpha=0.1, color='green', label='_')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")


def plot_policy_comparison(data: List[Dict], output_file='policy_comparison.png'):
    """
    Compare different policies (reward modes) on geometric dimensions.

    Uses a multi-panel visualization to show distributions and statistics.
    """
    # Group by reward mode
    modes = {}
    for d in data:
        mode = d.get('reward_mode', 'unknown')
        if mode not in modes:
            modes[mode] = []
        modes[mode].append(d)

    if len(modes) < 2:
        print("Need at least 2 reward modes for comparison")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    mode_list = list(modes.keys())
    colors = ['steelblue', 'coral', 'green', 'purple']

    # Plot 1: k_explore distribution
    for i, mode in enumerate(mode_list):
        k_explores = [d['k_explore'] for d in modes[mode]]
        axes[0, 0].hist(k_explores, bins=20, alpha=0.6,
                        label=mode, color=colors[i % len(colors)])

    axes[0, 0].set_xlabel('k_explore', fontsize=11)
    axes[0, 0].set_ylabel('Frequency', fontsize=11)
    axes[0, 0].set_title('Exploration Balance Distribution', fontsize=12, weight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(alpha=0.3)

    # Plot 2: k_efficiency distribution
    for i, mode in enumerate(mode_list):
        k_efficiencies = [d['k_efficiency'] for d in modes[mode]]
        axes[0, 1].hist(k_efficiencies, bins=20, alpha=0.6,
                        label=mode, color=colors[i % len(colors)])

    axes[0, 1].set_xlabel('k_efficiency', fontsize=11)
    axes[0, 1].set_ylabel('Frequency', fontsize=11)
    axes[0, 1].set_title('Efficiency Distribution', fontsize=12, weight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(alpha=0.3)

    # Plot 3: k_explore vs k_efficiency scatter
    for i, mode in enumerate(mode_list):
        k_explores = [d['k_explore'] for d in modes[mode]]
        k_efficiencies = [d['k_efficiency'] for d in modes[mode]]
        axes[1, 0].scatter(k_explores, k_efficiencies,
                          alpha=0.5, s=50, label=mode,
                          color=colors[i % len(colors)])

    axes[1, 0].set_xlabel('k_explore', fontsize=11)
    axes[1, 0].set_ylabel('k_efficiency', fontsize=11)
    axes[1, 0].set_title('Geometric Shape Space', fontsize=12, weight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(alpha=0.3)
    axes[1, 0].axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    axes[1, 0].axvline(0.5, color='gray', linestyle='--', alpha=0.3)

    # Plot 4: Statistics table
    axes[1, 1].axis('off')

    stats_text = "Geometric Statistics\n" + "="*40 + "\n\n"

    for mode in mode_list:
        k_explores = [d['k_explore'] for d in modes[mode]]
        k_efficiencies = [d['k_efficiency'] for d in modes[mode]]

        stats_text += f"{mode}:\n"
        stats_text += f"  k_explore:    {np.mean(k_explores):.3f} ± {np.std(k_explores):.3f}\n"
        stats_text += f"  k_efficiency: {np.mean(k_efficiencies):.3f} ± {np.std(k_efficiencies):.3f}\n"
        stats_text += f"  n_samples:    {len(k_explores)}\n\n"

    axes[1, 1].text(0.1, 0.9, stats_text, fontsize=10, family='monospace',
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.suptitle('Policy Geometric Comparison', fontsize=16, weight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")


def plot_temporal_evolution(data: List[Dict], output_file='temporal_evolution.png'):
    """
    Show how geometric properties evolve over episodes.

    Groups data by episode and plots time series.
    """
    # Group by episode
    episodes = {}
    for d in data:
        ep_id = d['episode_id']
        if ep_id not in episodes:
            episodes[ep_id] = []
        episodes[ep_id].append(d)

    # Compute per-episode statistics
    ep_ids = sorted(episodes.keys())
    avg_k_explores = []
    avg_k_efficiencies = []
    success_rates = []

    for ep_id in ep_ids:
        ep_data = episodes[ep_id]
        avg_k_explores.append(np.mean([d['k_explore'] for d in ep_data]))
        avg_k_efficiencies.append(np.mean([d['k_efficiency'] for d in ep_data]))
        success_rates.append(1.0 if ep_data[0].get('escaped', False) else 0.0)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # k_explore evolution
    axes[0].plot(ep_ids, avg_k_explores, linewidth=2, color='steelblue',
                 marker='o', markersize=4, alpha=0.7)
    axes[0].fill_between(ep_ids, 0, avg_k_explores, alpha=0.2, color='steelblue')
    axes[0].set_ylabel('Avg k_explore', fontsize=12)
    axes[0].set_title('Geometric Evolution Over Episodes', fontsize=14, weight='bold')
    axes[0].grid(alpha=0.3)
    axes[0].axhline(0.5, color='gray', linestyle='--', alpha=0.3)

    # k_efficiency evolution
    axes[1].plot(ep_ids, avg_k_efficiencies, linewidth=2, color='coral',
                 marker='o', markersize=4, alpha=0.7)
    axes[1].fill_between(ep_ids, 0, avg_k_efficiencies, alpha=0.2, color='coral')
    axes[1].set_ylabel('Avg k_efficiency', fontsize=12)
    axes[1].grid(alpha=0.3)
    axes[1].axhline(0.5, color='gray', linestyle='--', alpha=0.3)

    # Success rate
    axes[2].bar(ep_ids, success_rates, color='green', alpha=0.6, width=0.8)
    axes[2].set_xlabel('Episode ID', fontsize=12)
    axes[2].set_ylabel('Success', fontsize=12)
    axes[2].set_ylim(-0.1, 1.1)
    axes[2].set_yticks([0, 1])
    axes[2].set_yticklabels(['Failed', 'Success'])
    axes[2].grid(alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")


def plot_skill_comparison(output_file='skill_comparison.png'):
    """
    Compare geometric properties of all skills at different belief levels.

    This shows how each skill's shape changes with uncertainty.
    """
    skills = [
        {'name': 'peek_door', 'cost': 1.0, 'color': 'blue'},
        {'name': 'try_door', 'cost': 1.5, 'color': 'green'},
        {'name': 'go_window', 'cost': 2.0, 'color': 'red'}
    ]

    beliefs = [0.1, 0.3, 0.5, 0.7, 0.9]

    fig, ax = plt.subplots(figsize=(12, 8))

    x_positions = np.arange(len(beliefs))
    width = 0.25

    for i, skill in enumerate(skills):
        k_explores = []
        k_efficiencies = []

        for p in beliefs:
            stamp = build_silver_stamp(skill['name'], skill['cost'], p)
            k_explores.append(stamp['k_explore'])
            k_efficiencies.append(stamp['k_efficiency'])

        # Plot k_explore as bars
        ax.bar(x_positions + i*width, k_explores,
               width, label=f"{skill['name']} (k_explore)",
               color=skill['color'], alpha=0.6)

        # Plot k_efficiency as lines
        ax.plot(x_positions + i*width, k_efficiencies,
                marker='o', markersize=8, linewidth=2,
                color=skill['color'], linestyle='--',
                label=f"{skill['name']} (k_efficiency)")

    ax.set_xlabel('Belief p(unlocked)', fontsize=12)
    ax.set_ylabel('Coefficient Value', fontsize=12)
    ax.set_title('Skill Geometric Properties vs Belief', fontsize=14, weight='bold')
    ax.set_xticks(x_positions + width)
    ax.set_xticklabels([f"{p:.1f}" for p in beliefs])
    ax.legend(fontsize=9, loc='best')
    ax.grid(alpha=0.3, axis='y')
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")


def main():
    """Generate all visualizations."""
    print("\n" + "="*60)
    print("SILVER GAUGE VISUALIZATION SUITE")
    print("="*60 + "\n")

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Extract data
        print("Extracting silver data from Neo4j...")
        data = extract_silver_data(session)

        if not data:
            print("WARNING: No silver data found in database.")
            print("Run some episodes first with silver gauge enabled.\n")
            print("Example:")
            print("  python runner.py --door-state locked")
            print()
            # Still generate skill comparison (doesn't need DB data)
            print("Generating skill comparison (theory-based)...")
            plot_skill_comparison()
            print("\nGenerating belief-geometry plot (theory-based)...")
            plot_belief_geometry()
        else:
            print(f"Found {len(data)} silver data points from {len(set(d['episode_id'] for d in data))} episodes\n")

            # Generate visualizations
            print("Generating visualizations...\n")

            print("1. Phase Diagram")
            plot_phase_diagram(data)

            print("2. Belief-Geometry Plot")
            plot_belief_geometry()

            print("3. Policy Comparison")
            plot_policy_comparison(data)

            print("4. Temporal Evolution")
            plot_temporal_evolution(data)

            print("5. Skill Comparison")
            plot_skill_comparison()

    driver.close()

    print("\n" + "="*60)
    print("VISUALIZATION COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    print("  - phase_diagram.png")
    print("  - belief_geometry.png")
    print("  - policy_comparison.png")
    print("  - temporal_evolution.png")
    print("  - skill_comparison.png")
    print()


if __name__ == "__main__":
    try:
        import matplotlib
        # Use non-interactive backend if running headless
        matplotlib.use('Agg')
    except ImportError:
        print("ERROR: matplotlib not installed")
        print("Install with: pip install matplotlib")
        sys.exit(1)

    main()
