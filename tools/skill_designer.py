#!/usr/bin/env python3
"""
Skill Designer - Geometric Lens Tool #3

Design skills with target geometric properties.
Systematic skill creation using k-values.
"""

import numpy as np
import matplotlib.pyplot as plt


def calculate_k_explore(goal, info):
    """Calculate k_explore from goal and info values."""
    if goal <= 0 or info <= 0:
        return 0.0

    gm = np.sqrt(goal * info)
    am = (goal + info) / 2

    if am == 0:
        return 1.0

    return gm / am


def design_skill_for_target_k(target_k, goal_value=None, info_value=None):
    """
    Design a skill with target k_explore value.

    Given target k and one dimension, solve for the other.

    k = GM/AM = sqrt(goal*info) / ((goal+info)/2)

    If we have goal, solve for info:
    k = sqrt(goal*info) / ((goal+info)/2)
    k*(goal+info)/2 = sqrt(goal*info)
    [k*(goal+info)/2]^2 = goal*info
    k^2*(goal+info)^2/4 = goal*info

    Let g=goal, i=info, k=target:
    k^2*(g+i)^2/4 = g*i
    k^2*g^2/4 + k^2*g*i/2 + k^2*i^2/4 = g*i
    k^2*i^2/4 + k^2*g*i/2 - g*i = -k^2*g^2/4
    k^2*i^2/4 + i*(k^2*g/2 - g) = -k^2*g^2/4

    Quadratic: a*i^2 + b*i + c = 0
    a = k^2/4
    b = k^2*g/2 - g = g*(k^2/2 - 1)
    c = -k^2*g^2/4
    """

    if target_k <= 0 or target_k >= 1:
        raise ValueError("target_k must be in (0, 1)")

    if goal_value is not None and info_value is not None:
        raise ValueError("Specify either goal OR info, not both")

    if goal_value is None and info_value is None:
        # Default: choose reasonable goal value
        goal_value = 2.0

    if goal_value is not None:
        g = goal_value
        k = target_k

        # Quadratic coefficients
        a = k**2 / 4
        b = g * (k**2 / 2 - 1)
        c = -k**2 * g**2 / 4

        # Solve quadratic
        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            raise ValueError(f"No real solution for target_k={target_k} with goal={goal_value}")

        # Take positive root
        info_value = (-b + np.sqrt(discriminant)) / (2*a)

    else:  # info_value is not None
        i = info_value
        k = target_k

        # Similar quadratic for goal
        a = k**2 / 4
        b = i * (k**2 / 2 - 1)
        c = -k**2 * i**2 / 4

        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            raise ValueError(f"No real solution for target_k={target_k} with info={info_value}")

        goal_value = (-b + np.sqrt(discriminant)) / (2*a)

    # Verify
    actual_k = calculate_k_explore(goal_value, info_value)

    return {
        'goal': goal_value,
        'info': info_value,
        'target_k': target_k,
        'actual_k': actual_k,
        'error': abs(actual_k - target_k)
    }


def suggest_cost(goal, info):
    """Suggest reasonable cost based on goal and info values."""
    # Cost should be less than benefit
    # Heuristic: cost = 0.3 * (goal + info) to 0.5 * (goal + info)
    benefit = goal + info
    suggested_min = 0.3 * benefit
    suggested_max = 0.5 * benefit

    return (suggested_min + suggested_max) / 2


def generate_portfolio_with_target_ks(k_values):
    """Generate a portfolio of skills with specific k-values."""
    skills = []

    for target_k in k_values:
        try:
            skill_params = design_skill_for_target_k(target_k, goal_value=2.0)
            cost = suggest_cost(skill_params['goal'], skill_params['info'])

            skills.append({
                'target_k': target_k,
                'goal': skill_params['goal'],
                'info': skill_params['info'],
                'cost': cost,
                'actual_k': skill_params['actual_k']
            })
        except ValueError as e:
            print(f"⚠ Could not create skill for k={target_k}: {e}")

    return skills


def plot_skill_design_space(output_path='skill_design_space.png'):
    """Visualize the skill design space."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Create grid of (goal, info) values
    goals = np.linspace(0.1, 5, 50)
    infos = np.linspace(0.1, 1, 50)
    G, I = np.meshgrid(goals, infos)

    # Calculate k_explore for each point
    K = np.zeros_like(G)
    for i in range(G.shape[0]):
        for j in range(G.shape[1]):
            K[i, j] = calculate_k_explore(G[i, j], I[i, j])

    # 1. Contour plot of k_explore
    ax = axes[0]
    contour = ax.contourf(G, I, K, levels=20, cmap='viridis')
    ax.contour(G, I, K, levels=[0.3, 0.5, 0.7, 0.9], colors='white',
               linewidths=2, linestyles='--')
    ax.set_xlabel('Goal Value')
    ax.set_ylabel('Info Gain')
    ax.set_title('k_explore Landscape')
    plt.colorbar(contour, ax=ax, label='k_explore')

    # Add example skills
    examples = [
        (0.0, 1.0, 'peek\n(k≈0)'),
        (3.0, 0.0, 'try\n(k≈0)'),
        (2.0, 0.7, 'balanced\n(k≈0.8)'),
    ]
    for goal, info, label in examples:
        if goal > 0 and info > 0:
            ax.plot(goal, info, 'r*', markersize=15)
            ax.text(goal, info+0.05, label, ha='center', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    # 2. k-values across different ratios
    ax = axes[1]
    ratios = np.linspace(0.1, 10, 100)  # goal/info ratio
    k_values_by_ratio = []

    for ratio in ratios:
        goal = 2.0  # Fixed goal
        info = goal / ratio
        k = calculate_k_explore(goal, info)
        k_values_by_ratio.append(k)

    ax.plot(ratios, k_values_by_ratio, 'b-', linewidth=2)
    ax.axhline(0.5, color='r', linestyle='--', label='k=0.5 (moderate balance)')
    ax.axhline(0.7, color='g', linestyle='--', label='k=0.7 (high balance)')
    ax.axhline(0.9, color='orange', linestyle='--', label='k=0.9 (very balanced)')
    ax.set_xlabel('Goal/Info Ratio')
    ax.set_ylabel('k_explore')
    ax.set_title('k_explore vs Goal/Info Ratio')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved design space visualization: {output_path}")


def main():
    """Demonstrate skill design tool."""
    print("="*60)
    print("SKILL DESIGNER - GEOMETRIC LENS TOOL")
    print("="*60)

    # Design skills with specific k-values
    target_ks = [0.2, 0.4, 0.6, 0.8, 0.95]

    print(f"\nDesigning skills with target k-values: {target_ks}")
    print("\n" + "-"*60)

    for target_k in target_ks:
        skill = design_skill_for_target_k(target_k, goal_value=2.0)
        cost = suggest_cost(skill['goal'], skill['info'])

        print(f"\nTarget k_explore: {target_k:.2f}")
        print(f"  Goal:      {skill['goal']:.3f}")
        print(f"  Info:      {skill['info']:.3f}")
        print(f"  Cost:      {cost:.3f}")
        print(f"  Actual k:  {skill['actual_k']:.4f}")
        print(f"  Error:     {skill['error']:.6f}")

    # Generate portfolio with uniform k-coverage
    print("\n" + "="*60)
    print("GENERATING PORTFOLIO WITH UNIFORM K-COVERAGE")
    print("="*60)

    k_targets = np.linspace(0.1, 0.95, 10)
    portfolio = generate_portfolio_with_target_ks(k_targets)

    print(f"\nGenerated {len(portfolio)} skills:")
    for i, skill in enumerate(portfolio):
        print(f"  Skill {i+1}: k={skill['actual_k']:.2f}, "
              f"goal={skill['goal']:.2f}, info={skill['info']:.2f}, "
              f"cost={skill['cost']:.2f}")

    # Visualize design space
    plot_skill_design_space()

    print("\n✓ Skill design tool demonstration complete.")
    print("  Generated: skill_design_space.png")


if __name__ == '__main__':
    main()
