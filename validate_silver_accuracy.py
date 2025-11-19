#!/usr/bin/env python3
"""
Validate that Silver Gauge produces accurate results without changing behavior.

This script verifies:
1. Silver stamp values are mathematically correct
2. Agent makes identical decisions with/without silver
3. Silver scores correlate with base scores
4. Geometric invariants hold (HM <= GM <= AM)
"""

import sys
from scoring import score_skill_detailed, entropy
from scoring_silver import build_silver_stamp, harmonic_mean, geometric_mean, arithmetic_mean
import math


def validate_pythagorean_invariants():
    """Test that HM <= GM <= AM holds for all reasonable inputs."""
    print("=" * 60)
    print("VALIDATION 1: Pythagorean Mean Invariants")
    print("=" * 60)

    test_cases = [
        (1.0, 1.0),
        (1.0, 10.0),
        (2.0, 8.0),
        (0.5, 4.5),
        (100.0, 1.0),
    ]

    all_pass = True
    for a, b in test_cases:
        hm = harmonic_mean(a, b)
        gm = geometric_mean(a, b)
        am = arithmetic_mean(a, b)

        invariant_holds = hm <= gm <= am
        status = "✓" if invariant_holds else "✗"

        print(f"{status} ({a}, {b}): HM={hm:.3f} <= GM={gm:.3f} <= AM={am:.3f}")

        if not invariant_holds:
            all_pass = False

    print(f"\nResult: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def validate_shape_coefficients():
    """Test that shape coefficients are in valid range [0, 1]."""
    print("=" * 60)
    print("VALIDATION 2: Shape Coefficient Bounds")
    print("=" * 60)

    skills = ["peek_door", "try_door", "go_window"]
    beliefs = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    costs = [1.0, 1.5, 2.0]

    all_pass = True
    violations = []

    for skill, cost in zip(skills, costs):
        for p in beliefs:
            stamp = build_silver_stamp(skill, cost, p)

            k_explore = stamp['k_explore']
            k_efficiency = stamp['k_efficiency']

            if not (0.0 <= k_explore <= 1.0):
                all_pass = False
                violations.append(f"{skill} @ p={p}: k_explore={k_explore:.3f}")

            if not (0.0 <= k_efficiency <= 1.0):
                all_pass = False
                violations.append(f"{skill} @ p={p}: k_efficiency={k_efficiency:.3f}")

    if violations:
        print("✗ Violations found:")
        for v in violations:
            print(f"  {v}")
    else:
        print("✓ All shape coefficients in [0, 1]")
        print(f"  Tested: {len(skills) * len(beliefs)} combinations")

    print(f"\nResult: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def validate_base_score_preservation():
    """Test that base_score in silver stamp matches original scoring."""
    print("=" * 60)
    print("VALIDATION 3: Base Score Preservation")
    print("=" * 60)

    skills_data = [
        {"name": "peek_door", "cost": 1.0},
        {"name": "try_door", "cost": 1.5},
        {"name": "go_window", "cost": 2.0}
    ]
    beliefs = [0.1, 0.3, 0.5, 0.7, 0.9]

    all_pass = True
    max_error = 0.0

    for skill in skills_data:
        for p in beliefs:
            # Original scoring
            original = score_skill_detailed(skill, p)
            original_score = original['total_score']

            # Silver scoring
            stamp = build_silver_stamp(skill['name'], skill['cost'], p)
            silver_base_score = stamp['base_score']

            # They should be identical
            error = abs(original_score - silver_base_score)
            max_error = max(max_error, error)

            if error > 1e-6:
                print(f"✗ {skill['name']} @ p={p}: "
                      f"original={original_score:.4f}, silver={silver_base_score:.4f}, "
                      f"error={error:.6f}")
                all_pass = False

    if all_pass:
        print(f"✓ All base scores match (max error: {max_error:.9f})")
        print(f"  Tested: {len(skills_data) * len(beliefs)} combinations")

    print(f"\nResult: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def validate_component_consistency():
    """Test that silver stamp components match original scoring components."""
    print("=" * 60)
    print("VALIDATION 4: Component Consistency")
    print("=" * 60)

    skill = {"name": "peek_door", "cost": 1.0}
    p = 0.5

    # Original components
    original = score_skill_detailed(skill, p)

    # Silver components
    stamp = build_silver_stamp(skill['name'], skill['cost'], p)

    checks = [
        ('goal_value', original['goal_value'], stamp['goal_value']),
        ('info_gain', original['info_gain'], stamp['info_gain']),
        ('cost', original['cost'], stamp['cost']),
    ]

    all_pass = True
    for name, orig, silver in checks:
        error = abs(orig - silver)
        status = "✓" if error < 1e-6 else "✗"
        print(f"{status} {name:12s}: original={orig:.4f}, silver={silver:.4f}, error={error:.9f}")
        if error >= 1e-6:
            all_pass = False

    print(f"\nResult: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def validate_geometric_interpretability():
    """Test that geometric interpretations make sense."""
    print("=" * 60)
    print("VALIDATION 5: Geometric Interpretability")
    print("=" * 60)

    # Test case 1: Pure exploration (peek at p=0.5)
    stamp1 = build_silver_stamp("peek_door", 1.0, 0.5)
    print("Test 1: Pure Exploration (peek_door @ p=0.5)")
    print(f"  goal={stamp1['goal_value']:.3f}, info={stamp1['info_gain']:.3f}")
    print(f"  k_explore={stamp1['k_explore']:.3f} (expected: low, since goal=0)")
    print(f"  entropy={stamp1['entropy']:.3f} (expected: 1.0 at p=0.5)")

    check1 = stamp1['goal_value'] == 0.0 and stamp1['info_gain'] > 0.9
    print(f"  Status: {'✓ PASS' if check1 else '✗ FAIL'}")
    print()

    # Test case 2: Pure exploitation (try_door at p=0.9)
    stamp2 = build_silver_stamp("try_door", 1.5, 0.9)
    print("Test 2: Pure Exploitation (try_door @ p=0.9)")
    print(f"  goal={stamp2['goal_value']:.3f}, info={stamp2['info_gain']:.3f}")
    print(f"  k_explore={stamp2['k_explore']:.3f} (expected: low, since info=0)")
    print(f"  k_efficiency={stamp2['k_efficiency']:.3f} (expected: high, good benefit/cost)")

    check2 = stamp2['info_gain'] == 0.0 and stamp2['goal_value'] > 5.0
    print(f"  Status: {'✓ PASS' if check2 else '✗ FAIL'}")
    print()

    # Test case 3: Balanced (when both goal and info are comparable)
    # This doesn't naturally occur in this domain, but we can verify the math
    # For balanced: if goal ≈ info, then k_explore → 1.0
    a, b = 5.0, 5.0
    hm = harmonic_mean(a, b)
    gm = geometric_mean(a, b)
    am = arithmetic_mean(a, b)
    k = gm / am

    print("Test 3: Balanced Input (a=5.0, b=5.0)")
    print(f"  HM={hm:.3f}, GM={gm:.3f}, AM={am:.3f}")
    print(f"  k={k:.3f} (expected: 1.0 for balanced)")

    check3 = abs(k - 1.0) < 1e-6
    print(f"  Status: {'✓ PASS' if check3 else '✗ FAIL'}")
    print()

    all_pass = check1 and check2 and check3
    print(f"Result: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def validate_decision_invariance():
    """Test that silver doesn't change which action wins."""
    print("=" * 60)
    print("VALIDATION 6: Decision Invariance")
    print("=" * 60)

    skills = [
        {"name": "peek_door", "cost": 1.0},
        {"name": "try_door", "cost": 1.5},
        {"name": "go_window", "cost": 2.0}
    ]

    test_beliefs = [0.1, 0.3, 0.5, 0.7, 0.9]

    all_pass = True

    for p in test_beliefs:
        # Score using original method
        original_scores = [(score_skill_detailed(s, p)['total_score'], s['name'])
                          for s in skills]
        original_scores.sort(reverse=True)
        original_winner = original_scores[0][1]

        # Score using silver (should use same base_score)
        silver_scores = [(build_silver_stamp(s['name'], s['cost'], p)['base_score'], s['name'])
                        for s in skills]
        silver_scores.sort(reverse=True)
        silver_winner = silver_scores[0][1]

        match = original_winner == silver_winner
        status = "✓" if match else "✗"

        print(f"{status} p={p:.1f}: original={original_winner:12s}, silver={silver_winner:12s}")

        if not match:
            all_pass = False

    print(f"\nResult: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def validate_all_values_finite():
    """Test that all stamp values are finite (no NaN, no Inf)."""
    print("=" * 60)
    print("VALIDATION 7: All Values Finite")
    print("=" * 60)

    skills = ["peek_door", "try_door", "go_window"]
    costs = [1.0, 1.5, 2.0]
    beliefs = [0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0]

    all_pass = True
    violations = []

    for skill, cost in zip(skills, costs):
        for p in beliefs:
            stamp = build_silver_stamp(skill, cost, p)

            for key, value in stamp.items():
                if isinstance(value, (int, float)) and not math.isfinite(value):
                    all_pass = False
                    violations.append(f"{skill} @ p={p}: {key}={value}")

    if violations:
        print("✗ Non-finite values found:")
        for v in violations:
            print(f"  {v}")
    else:
        print(f"✓ All values finite")
        print(f"  Tested: {len(skills) * len(beliefs)} stamps × {len(stamp)} fields")

    print(f"\nResult: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print()
    return all_pass


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("SILVER GAUGE ACCURACY VALIDATION")
    print("=" * 60)
    print()

    results = []

    results.append(("Pythagorean Invariants", validate_pythagorean_invariants()))
    results.append(("Shape Coefficient Bounds", validate_shape_coefficients()))
    results.append(("Base Score Preservation", validate_base_score_preservation()))
    results.append(("Component Consistency", validate_component_consistency()))
    results.append(("Geometric Interpretability", validate_geometric_interpretability()))
    results.append(("Decision Invariance", validate_decision_invariance()))
    results.append(("All Values Finite", validate_all_values_finite()))

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8s} {name}")

    all_passed = all(r[1] for r in results)

    print()
    print("=" * 60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
        print("Silver Gauge is accurate and preserves agent behavior.")
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("Review failures above.")
    print("=" * 60)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
