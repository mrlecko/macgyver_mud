#!/usr/bin/env python3
"""
Visualization comparing crisp (specialist) vs balanced (multi-objective) skills.

This demonstrates why balanced skills are superior for:
1. Genuine multi-objective decision-making
2. Interpretable k_explore metrics
3. Richer policy analysis
"""

import matplotlib.pyplot as plt
import numpy as np
from scoring_silver import build_silver_stamp, geometric_mean, arithmetic_mean, _ensure_positive
from scoring_balanced import score_balanced_skill_detailed

# Set up high-quality plots
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9


def plot_k_explore_comparison():
    """Compare k_explore values for crisp vs balanced skills."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Crisp skills
    crisp_skills = [
        ("peek_door", 1.0),
        ("try_door", 1.5),
        ("go_window", 2.0)
    ]

    # Balanced skills
    balanced_skills = [
        {"name": "probe_and_try", "cost": 2.0, "goal_fraction": 0.6, "info_fraction": 0.4},
        {"name": "informed_window", "cost": 2.2, "goal_fraction": 0.8, "info_fraction": 0.3},
        {"name": "exploratory_action", "cost": 2.5, "goal_fraction": 0.7, "info_fraction": 0.7},
        {"name": "adaptive_peek", "cost": 1.3, "goal_fraction": 0.4, "info_fraction": 0.6}
    ]

    p = 0.5  # Test at maximum uncertainty

    # Plot 1: k_explore distribution
    crisp_k_explores = []
    for name, cost in crisp_skills:
        stamp = build_silver_stamp(name, cost, p)
        crisp_k_explores.append(stamp['k_explore'])

    balanced_k_explores = []
    for skill in balanced_skills:
        details = score_balanced_skill_detailed(skill, p)
        g = _ensure_positive(abs(details["goal_value"]))
        i = _ensure_positive(details["info_gain"])
        gm_gi = geometric_mean(g, i)
        am_gi = arithmetic_mean(g, i)
        k_explore = gm_gi / am_gi if am_gi > 0 else 0.0
        balanced_k_explores.append(k_explore)

    x_crisp = np.arange(len(crisp_skills))
    x_balanced = np.arange(len(balanced_skills))

    ax1.bar(x_crisp, crisp_k_explores, color='#e74c3c', alpha=0.7, label='Crisp Skills')
    ax1.set_xticks(x_crisp)
    ax1.set_xticklabels([s[0] for s in crisp_skills], rotation=45, ha='right')
    ax1.set_ylabel('k_explore (0=imbalanced, 1=balanced)')
    ax1.set_title('Crisp Skills: Pure Specialists\n(k_explore ≈ 0)')
    ax1.set_ylim([0, 1])
    ax1.axhline(0.3, color='gray', linestyle='--', alpha=0.5, label='Balanced threshold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.legend()

    ax2.bar(x_balanced, balanced_k_explores, color='#27ae60', alpha=0.7, label='Balanced Skills')
    ax2.set_xticks(x_balanced)
    ax2.set_xticklabels([s['name'] for s in balanced_skills], rotation=45, ha='right')
    ax2.set_ylabel('k_explore (0=imbalanced, 1=balanced)')
    ax2.set_title('Balanced Skills: Multi-Objective\n(k_explore ∈ [0.3, 0.9])')
    ax2.set_ylim([0, 1])
    ax2.axhline(0.3, color='gray', linestyle='--', alpha=0.5, label='Balanced threshold')
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig('k_explore_comparison.png')
    print("✓ Saved k_explore_comparison.png")
    plt.close()


def plot_goal_info_space():
    """Plot skills in (goal, info) space to show multi-objective nature."""
    fig, ax = plt.subplots(figsize=(10, 8))

    p = 0.5

    # Crisp skills
    crisp_skills = [
        ("peek_door", 1.0),
        ("try_door", 1.5),
        ("go_window", 2.0)
    ]

    crisp_goals = []
    crisp_infos = []
    for name, cost in crisp_skills:
        stamp = build_silver_stamp(name, cost, p)
        crisp_goals.append(stamp['goal_value'])
        crisp_infos.append(stamp['info_gain'])

    # Balanced skills
    balanced_skills = [
        {"name": "probe_and_try", "cost": 2.0, "goal_fraction": 0.6, "info_fraction": 0.4},
        {"name": "informed_window", "cost": 2.2, "goal_fraction": 0.8, "info_fraction": 0.3},
        {"name": "exploratory_action", "cost": 2.5, "goal_fraction": 0.7, "info_fraction": 0.7},
        {"name": "adaptive_peek", "cost": 1.3, "goal_fraction": 0.4, "info_fraction": 0.6}
    ]

    balanced_goals = []
    balanced_infos = []
    balanced_names = []
    for skill in balanced_skills:
        details = score_balanced_skill_detailed(skill, p)
        balanced_goals.append(details['goal_value'])
        balanced_infos.append(details['info_gain'])
        balanced_names.append(skill['name'])

    # Plot crisp skills
    ax.scatter(crisp_goals, crisp_infos, s=200, c='#e74c3c', alpha=0.7,
               marker='s', label='Crisp Skills (Specialists)', edgecolors='black', linewidth=2)
    for i, (name, _) in enumerate(crisp_skills):
        ax.annotate(name, (crisp_goals[i], crisp_infos[i]),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='#e74c3c', alpha=0.3),
                   fontsize=9)

    # Plot balanced skills
    ax.scatter(balanced_goals, balanced_infos, s=200, c='#27ae60', alpha=0.7,
               marker='o', label='Balanced Skills (Multi-Objective)', edgecolors='black', linewidth=2)
    for i, name in enumerate(balanced_names):
        ax.annotate(name, (balanced_goals[i], balanced_infos[i]),
                   xytext=(-10, -20), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='#27ae60', alpha=0.3),
                   fontsize=9)

    # Add quadrant labels
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(2, color='gray', linestyle='--', alpha=0.3)

    ax.text(0.5, 0.8, 'Pure\nExploration', ha='center', va='center',
            fontsize=11, alpha=0.4, weight='bold')
    ax.text(3.5, 0.8, 'Balanced\nMulti-Objective', ha='center', va='center',
            fontsize=11, alpha=0.4, weight='bold', color='#27ae60')
    ax.text(3.5, 0.1, 'Pure\nExploitation', ha='center', va='center',
            fontsize=11, alpha=0.4, weight='bold')

    ax.set_xlabel('Goal Value', fontsize=12)
    ax.set_ylabel('Information Gain', fontsize=12)
    ax.set_title('Skills in Goal-Information Space\n(Balanced skills occupy multi-objective region)',
                fontsize=14, weight='bold')
    ax.grid(alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)

    plt.tight_layout()
    plt.savefig('goal_info_space.png')
    print("✓ Saved goal_info_space.png")
    plt.close()


def plot_k_explore_vs_belief():
    """Show how k_explore changes with belief for both policy types."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    beliefs = np.linspace(0, 1, 50)

    # Crisp skills
    for name, cost in [("peek_door", 1.0), ("try_door", 1.5), ("go_window", 2.0)]:
        k_explores = []
        for p in beliefs:
            stamp = build_silver_stamp(name, cost, p)
            k_explores.append(stamp['k_explore'])
        ax1.plot(beliefs, k_explores, linewidth=2, label=name, marker='o', markersize=3, alpha=0.7)

    ax1.set_xlabel('Belief p(unlocked)', fontsize=11)
    ax1.set_ylabel('k_explore', fontsize=11)
    ax1.set_title('Crisp Skills: k_explore vs Belief\n(Always near zero - pure specialists)', fontsize=12, weight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax1.set_ylim([-0.05, 1.05])

    # Balanced skills
    balanced_skills = [
        {"name": "probe_and_try", "cost": 2.0, "goal_fraction": 0.6, "info_fraction": 0.4},
        {"name": "informed_window", "cost": 2.2, "goal_fraction": 0.8, "info_fraction": 0.3},
        {"name": "exploratory_action", "cost": 2.5, "goal_fraction": 0.7, "info_fraction": 0.7},
        {"name": "adaptive_peek", "cost": 1.3, "goal_fraction": 0.4, "info_fraction": 0.6}
    ]

    for skill in balanced_skills:
        k_explores = []
        for p in beliefs:
            details = score_balanced_skill_detailed(skill, p)
            g = _ensure_positive(abs(details["goal_value"]))
            i = _ensure_positive(details["info_gain"])
            gm_gi = geometric_mean(g, i)
            am_gi = arithmetic_mean(g, i)
            k_explore = gm_gi / am_gi if am_gi > 0 else 0.0
            k_explores.append(k_explore)
        ax2.plot(beliefs, k_explores, linewidth=2, label=skill['name'], marker='o', markersize=3, alpha=0.7)

    ax2.set_xlabel('Belief p(unlocked)', fontsize=11)
    ax2.set_ylabel('k_explore', fontsize=11)
    ax2.set_title('Balanced Skills: k_explore vs Belief\n(Stays in balanced range [0.3, 0.9])', fontsize=12, weight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    ax2.set_ylim([-0.05, 1.05])
    ax2.axhline(0.3, color='gray', linestyle='--', alpha=0.5)
    ax2.axhline(0.7, color='gray', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig('k_explore_vs_belief.png')
    print("✓ Saved k_explore_vs_belief.png")
    plt.close()


def plot_phase_diagram_comparison():
    """Compare policies in (k_explore, k_efficiency) phase space."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    p = 0.5

    # Crisp skills - multiple beliefs
    beliefs_test = [0.1, 0.3, 0.5, 0.7, 0.9]
    colors_crisp = plt.cm.Reds(np.linspace(0.4, 0.9, len(beliefs_test)))

    for idx, p_test in enumerate(beliefs_test):
        k_explores = []
        k_efficiencies = []
        for name, cost in [("peek_door", 1.0), ("try_door", 1.5), ("go_window", 2.0)]:
            stamp = build_silver_stamp(name, cost, p_test)
            k_explores.append(stamp['k_explore'])
            k_efficiencies.append(stamp['k_efficiency'])

        ax1.scatter(k_explores, k_efficiencies, s=100, c=[colors_crisp[idx]],
                   alpha=0.7, edgecolors='black', linewidth=1,
                   label=f'p={p_test}')

    ax1.set_xlabel('k_explore (0=imbalanced, 1=balanced)', fontsize=11)
    ax1.set_ylabel('k_efficiency (0=poor, 1=excellent)', fontsize=11)
    ax1.set_title('Crisp Policy Phase Diagram\n(Clustered at k_explore ≈ 0)', fontsize=12, weight='bold')
    ax1.set_xlim([-0.05, 1.05])
    ax1.set_ylim([0.6, 1.05])
    ax1.grid(alpha=0.3)
    ax1.legend(loc='lower right', fontsize=8)

    # Balanced skills
    colors_balanced = plt.cm.Greens(np.linspace(0.4, 0.9, len(beliefs_test)))

    for idx, p_test in enumerate(beliefs_test):
        k_explores = []
        k_efficiencies = []
        for skill in [
            {"name": "probe_and_try", "cost": 2.0, "goal_fraction": 0.6, "info_fraction": 0.4},
            {"name": "informed_window", "cost": 2.2, "goal_fraction": 0.8, "info_fraction": 0.3},
            {"name": "exploratory_action", "cost": 2.5, "goal_fraction": 0.7, "info_fraction": 0.7},
            {"name": "adaptive_peek", "cost": 1.3, "goal_fraction": 0.4, "info_fraction": 0.6}
        ]:
            details = score_balanced_skill_detailed(skill, p_test)
            g = _ensure_positive(abs(details["goal_value"]))
            i = _ensure_positive(details["info_gain"])
            c_val = _ensure_positive(details["cost"])

            gm_gi = geometric_mean(g, i)
            am_gi = arithmetic_mean(g, i)
            k_explore = gm_gi / am_gi if am_gi > 0 else 0.0

            gm_gc = geometric_mean(g + i, c_val)
            am_gc = arithmetic_mean(g + i, c_val)
            k_efficiency = gm_gc / am_gc if am_gc > 0 else 0.0

            k_explores.append(k_explore)
            k_efficiencies.append(k_efficiency)

        ax2.scatter(k_explores, k_efficiencies, s=100, c=[colors_balanced[idx]],
                   alpha=0.7, edgecolors='black', linewidth=1,
                   label=f'p={p_test}')

    ax2.set_xlabel('k_explore (0=imbalanced, 1=balanced)', fontsize=11)
    ax2.set_ylabel('k_efficiency (0=poor, 1=excellent)', fontsize=11)
    ax2.set_title('Balanced Policy Phase Diagram\n(Distributed across multi-objective space)', fontsize=12, weight='bold')
    ax2.set_xlim([-0.05, 1.05])
    ax2.set_ylim([0.6, 1.05])
    ax2.axvline(0.3, color='gray', linestyle='--', alpha=0.5)
    ax2.axvline(0.7, color='gray', linestyle='--', alpha=0.5)
    ax2.grid(alpha=0.3)
    ax2.legend(loc='lower right', fontsize=8)

    plt.tight_layout()
    plt.savefig('phase_diagram_comparison.png')
    print("✓ Saved phase_diagram_comparison.png")
    plt.close()


def main():
    """Generate all comparison visualizations."""
    print("=" * 70)
    print("GENERATING BALANCED vs CRISP VISUALIZATIONS")
    print("=" * 70)
    print()

    plot_k_explore_comparison()
    plot_goal_info_space()
    plot_k_explore_vs_belief()
    plot_phase_diagram_comparison()

    print()
    print("=" * 70)
    print("✓ ALL VISUALIZATIONS COMPLETE")
    print("=" * 70)
    print()
    print("Generated files:")
    print("  1. k_explore_comparison.png     - Bar chart comparing k_explore values")
    print("  2. goal_info_space.png          - Skills in (goal, info) space")
    print("  3. k_explore_vs_belief.png      - How k_explore changes with belief")
    print("  4. phase_diagram_comparison.png - Geometric phase space comparison")
    print()
    print("KEY INSIGHT:")
    print("  Crisp skills:    k_explore ≈ 0    (pure specialists)")
    print("  Balanced skills: k_explore ∈ [0.3, 0.9] (genuine multi-objective)")
    print()


if __name__ == "__main__":
    main()
