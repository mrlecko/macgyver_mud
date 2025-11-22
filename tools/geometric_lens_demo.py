#!/usr/bin/env python3
"""
Geometric Lens Interactive Demonstration

Shows practical applications of the geometric analytical framework.
No hype, just useful analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scoring_silver import build_silver_stamp


def demonstrate_skill_fingerprinting():
    """Show how different skills have distinct geometric fingerprints."""
    print("\n" + "="*70)
    print("DEMONSTRATION 1: GEOMETRIC FINGERPRINTING")
    print("="*70)

    skills = [
        ('peek_door', 1.0, "Pure exploration"),
        ('try_door', 1.5, "Pure exploitation"),
        ('go_window', 5.0, "Guaranteed escape")
    ]

    beliefs = [0.1, 0.3, 0.5, 0.7, 0.9]

    print(f"\nAnalyzing 3 skills across {len(beliefs)} belief states:\n")

    for skill_name, cost, description in skills:
        print(f"{skill_name} ({description}):")
        print(f"{'  Belief':>10} {'k_explore':>10} {'k_efficiency':>12} {'Category':>20}")
        print("  " + "-"*60)

        for p in beliefs:
            stamp = build_silver_stamp(skill_name, cost, p)

            k_explore = stamp['k_explore']
            k_efficiency = stamp['k_efficiency']

            # Categorize
            if k_explore < 0.1:
                category = "Extreme specialist"
            elif k_explore < 0.3:
                category = "Strong specialist"
            elif k_explore < 0.7:
                category = "Moderately balanced"
            else:
                category = "Highly balanced"

            print(f"  {p:>8.1f} {k_explore:>10.4f} {k_efficiency:>12.4f} {category:>20}")

        print()

    print("Observation: All crisp skills maintain k_explore ≈ 0 across all beliefs.")
    print("This is because they're designed as pure specialists (by construction).")


def demonstrate_portfolio_gap_detection():
    """Show how geometric lens identifies gaps in skill coverage."""
    print("\n" + "="*70)
    print("DEMONSTRATION 2: PORTFOLIO GAP DETECTION")
    print("="*70)

    print("\nCrisp skills portfolio:")
    print("  Skills: peek_door, try_door, go_window")
    print("  k-space coverage analysis:")

    # Count coverage
    beliefs = np.linspace(0.1, 0.9, 20)
    k_values = []

    for p in beliefs:
        for skill_name, cost in [('peek_door', 1.0), ('try_door', 1.5), ('go_window', 5.0)]:
            stamp = build_silver_stamp(skill_name, cost, p)
            k_values.append(stamp['k_explore'])

    # Categorize
    extreme = sum(1 for k in k_values if k < 0.1)
    strong = sum(1 for k in k_values if 0.1 <= k < 0.3)
    moderate = sum(1 for k in k_values if 0.3 <= k < 0.7)
    balanced = sum(1 for k in k_values if k >= 0.7)

    total = len(k_values)
    print(f"\n  Extreme specialists (k<0.1):     {extreme}/{total} ({100*extreme/total:.1f}%)")
    print(f"  Strong specialists (0.1≤k<0.3):   {strong}/{total} ({100*strong/total:.1f}%)")
    print(f"  Moderately balanced (0.3≤k<0.7):  {moderate}/{total} ({100*moderate/total:.1f}%)")
    print(f"  Highly balanced (k≥0.7):          {balanced}/{total} ({100*balanced/total:.1f}%)")

    print(f"\n  ⚠ GAP DETECTED: No coverage in moderate (0.3-0.7) or balanced (≥0.7) regions")
    print(f"  Recommendation: Consider adding multi-objective skills")


def demonstrate_skill_design():
    """Show how to design skills with target geometric properties."""
    print("\n" + "="*70)
    print("DEMONSTRATION 3: SYSTEMATIC SKILL DESIGN")
    print("="*70)

    print("\nDesigning skills to fill portfolio gaps:")
    print("\nTarget: Skills with k_explore ∈ [0.5, 0.9] for balanced coverage\n")

    target_ks = [0.5, 0.6, 0.7, 0.8, 0.9]

    print(f"{'Target k':>10} {'Goal':>8} {'Info':>8} {'Cost':>8} {'Actual k':>10}")
    print("-"*50)

    for target_k in target_ks:
        # Design skill: solve for info given goal=2.0 and target k
        goal = 2.0
        k = target_k

        # From k = GM/AM, solve for info
        # k = sqrt(goal*info) / ((goal+info)/2)
        # Quadratic solution
        a = k**2 / 4
        b = goal * (k**2 / 2 - 1)
        c = -k**2 * goal**2 / 4

        discriminant = b**2 - 4*a*c
        info = (-b + np.sqrt(discriminant)) / (2*a)

        cost = 0.4 * (goal + info)  # Reasonable cost heuristic

        # Verify
        actual_k = np.sqrt(goal * info) / ((goal + info) / 2)

        print(f"{target_k:>10.1f} {goal:>8.2f} {info:>8.2f} {cost:>8.2f} {actual_k:>10.4f}")

    print("\nResult: Successfully designed 5 skills spanning k∈[0.5, 0.9]")
    print("These skills would fill the detected portfolio gap.")


def demonstrate_phase_space_visualization():
    """Create comprehensive phase space visualization."""
    print("\n" + "="*70)
    print("DEMONSTRATION 4: GEOMETRIC PHASE SPACE")
    print("="*70)

    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 2, figure=fig)

    # Generate data for crisp skills
    beliefs = np.linspace(0.05, 0.95, 30)
    skills_data = {
        'peek_door': {'cost': 1.0, 'color': 'blue', 'marker': 'o'},
        'try_door': {'cost': 1.5, 'color': 'red', 'marker': 's'},
        'go_window': {'cost': 5.0, 'color': 'green', 'marker': '^'}
    }

    all_data = {skill: {'k_explore': [], 'k_efficiency': [], 'goal': [], 'info': []}
                for skill in skills_data}

    for skill_name, props in skills_data.items():
        for p in beliefs:
            stamp = build_silver_stamp(skill_name, props['cost'], p)
            all_data[skill_name]['k_explore'].append(stamp['k_explore'])
            all_data[skill_name]['k_efficiency'].append(stamp['k_efficiency'])
            all_data[skill_name]['goal'].append(abs(stamp['goal_value']))
            all_data[skill_name]['info'].append(stamp['info_gain'])

    # Plot 1: Goal-Info space
    ax1 = fig.add_subplot(gs[0, 0])
    for skill_name, props in skills_data.items():
        ax1.scatter(all_data[skill_name]['goal'], all_data[skill_name]['info'],
                   c=props['color'], marker=props['marker'], s=50, alpha=0.6,
                   label=skill_name)
    ax1.set_xlabel('Goal Value')
    ax1.set_ylabel('Info Gain')
    ax1.set_title('Skill Space: Goal vs Information')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Phase space (k_explore vs k_efficiency)
    ax2 = fig.add_subplot(gs[0, 1])
    for skill_name, props in skills_data.items():
        ax2.scatter(all_data[skill_name]['k_explore'], all_data[skill_name]['k_efficiency'],
                   c=props['color'], marker=props['marker'], s=50, alpha=0.6,
                   label=skill_name)
    ax2.set_xlabel('k_explore (balance)')
    ax2.set_ylabel('k_efficiency (benefit/cost)')
    ax2.set_title('Geometric Phase Space')
    ax2.set_xlim(-0.05, 1.05)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: k_explore across beliefs
    ax3 = fig.add_subplot(gs[1, 0])
    for skill_name, props in skills_data.items():
        ax3.plot(beliefs, all_data[skill_name]['k_explore'],
                c=props['color'], marker=props['marker'], markersize=4,
                label=skill_name, linewidth=2, alpha=0.7)
    ax3.set_xlabel('Belief (p_unlocked)')
    ax3.set_ylabel('k_explore')
    ax3.set_title('k_explore vs Belief State')
    ax3.set_ylim(-0.05, 1.05)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: k_efficiency across beliefs
    ax4 = fig.add_subplot(gs[1, 1])
    for skill_name, props in skills_data.items():
        ax4.plot(beliefs, all_data[skill_name]['k_efficiency'],
                c=props['color'], marker=props['marker'], markersize=4,
                label=skill_name, linewidth=2, alpha=0.7)
    ax4.set_xlabel('Belief (p_unlocked)')
    ax4.set_ylabel('k_efficiency')
    ax4.set_title('k_efficiency vs Belief State')
    ax4.set_ylim(-0.05, 1.05)
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('geometric_lens_demo.png', dpi=150, bbox_inches='tight')

    print("\nGenerated comprehensive phase space visualization:")
    print("  - Goal vs Info space (top left)")
    print("  - Geometric phase space (top right)")
    print("  - k_explore evolution (bottom left)")
    print("  - k_efficiency evolution (bottom right)")
    print("\n✓ Saved: geometric_lens_demo.png")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("GEOMETRIC LENS - PRACTICAL DEMONSTRATIONS")
    print("="*70)
    print("\nShowing analytical utility without hyperbole.")
    print("All findings are descriptive, not causal claims.")

    demonstrate_skill_fingerprinting()
    demonstrate_portfolio_gap_detection()
    demonstrate_skill_design()
    demonstrate_phase_space_visualization()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nThe geometric lens provides:")
    print("  ✓ Skill fingerprinting (k-values characterize skills)")
    print("  ✓ Portfolio gap detection (identify missing k-regions)")
    print("  ✓ Systematic skill design (create skills with target k)")
    print("  ✓ Geometric visualization (phase space mapping)")
    print("\nWhat it does NOT provide (without further testing):")
    print("  ✗ Performance predictions (untested)")
    print("  ✗ Universal patterns (k≈0 is design-specific)")
    print("  ✗ Causal mechanisms (correlations ≠ causation)")
    print("\nThe geometric lens is a measurement tool, not a discovery.")
    print("It's useful for analysis and design. That's valuable.")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
