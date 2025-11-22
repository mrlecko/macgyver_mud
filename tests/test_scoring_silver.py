"""
Tests for the silver gauge scoring module.

Following TDD: write tests FIRST, then implement.
"""

import pytest
import math
import json


class TestPythagoreanMeans:
    """Test the basic Pythagorean mean implementations."""

    def test_harmonic_mean_basic(self):
        """HM of equal values should equal that value."""
        from scoring_silver import harmonic_mean
        assert harmonic_mean(4.0, 4.0) == pytest.approx(4.0)

    def test_geometric_mean_basic(self):
        """GM of equal values should equal that value."""
        from scoring_silver import geometric_mean
        assert geometric_mean(4.0, 4.0) == pytest.approx(4.0)

    def test_arithmetic_mean_basic(self):
        """AM of equal values should equal that value."""
        from scoring_silver import arithmetic_mean
        assert arithmetic_mean(4.0, 4.0) == pytest.approx(4.0)

    def test_means_ordering_holds(self):
        """For positive values: HM ≤ GM ≤ AM (with equality iff values equal)."""
        from scoring_silver import harmonic_mean, geometric_mean, arithmetic_mean

        a, b = 2.0, 8.0
        hm = harmonic_mean(a, b)
        gm = geometric_mean(a, b)
        am = arithmetic_mean(a, b)

        assert hm <= gm <= am
        # Specific values for 2 and 8:
        # HM = 2*2*8/(2+8) = 32/10 = 3.2
        # GM = sqrt(2*8) = sqrt(16) = 4.0
        # AM = (2+8)/2 = 5.0
        assert hm == pytest.approx(3.2)
        assert gm == pytest.approx(4.0)
        assert am == pytest.approx(5.0)

    def test_harmonic_mean_imbalance_penalty(self):
        """HM should strongly penalize imbalanced pairs."""
        from scoring_silver import harmonic_mean

        # 1 and 100: HM should be close to 1 (the bottleneck)
        hm = harmonic_mean(1.0, 100.0)
        # HM = 2/(1/1 + 1/100) = 2/(1.01) ≈ 1.98
        assert hm < 2.0
        assert hm > 1.5

    def test_geometric_mean_balance(self):
        """GM is the balanced multiplicative mean."""
        from scoring_silver import geometric_mean

        # 4 and 9: GM = sqrt(36) = 6
        assert geometric_mean(4.0, 9.0) == pytest.approx(6.0)

    def test_ensure_positive_clamps_negative(self):
        """Negative values should be clamped to small positive epsilon."""
        from scoring_silver import _ensure_positive

        result = _ensure_positive(-5.0)
        assert result > 0.0
        assert result < 0.01  # Should be tiny epsilon


class TestBuildSilverStamp:
    """Test the build_silver_stamp function."""

    def test_build_silver_stamp_returns_dict(self):
        """Should return a dictionary."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)
        assert isinstance(stamp, dict)

    def test_build_silver_stamp_has_required_keys(self):
        """Should have all required keys."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)

        required_keys = [
            "stamp_version",
            "skill_name",
            "p_unlocked",
            "goal_value",
            "info_gain",
            "cost",
            "base_score",
            "hm_goal_info",
            "gm_goal_info",
            "am_goal_info",
            "hm_goalinfo_cost",
            "gm_goalinfo_cost",
            "am_goalinfo_cost",
            "k_explore",
            "k_efficiency",
            "entropy",
            "silver_score",
        ]

        for key in required_keys:
            assert key in stamp, f"Missing key: {key}"

    def test_build_silver_stamp_is_json_serializable(self):
        """Should be JSON-serializable."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)
        json_str = json.dumps(stamp)
        assert isinstance(json_str, str)

        # Round-trip test
        recovered = json.loads(json_str)
        assert recovered["skill_name"] == "peek_door"

    def test_shape_coefficients_in_valid_range(self):
        """k_explore and k_efficiency should be in [0, 1]."""
        from scoring_silver import build_silver_stamp

        for p in [0.1, 0.5, 0.9]:
            for skill in ["peek_door", "try_door", "go_window"]:
                stamp = build_silver_stamp(skill, 1.0, p)

                assert 0.0 <= stamp["k_explore"] <= 1.0
                assert 0.0 <= stamp["k_efficiency"] <= 1.0

    def test_silver_stamp_at_p_half(self):
        """At p=0.5 (maximum uncertainty), info gain should be high."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)

        # At p=0.5, entropy is maximal (1.0)
        assert stamp["entropy"] == pytest.approx(1.0, abs=0.01)

        # peek_door should have high info gain at p=0.5
        assert stamp["info_gain"] > 0.0

    def test_silver_stamp_at_p_high(self):
        """At p=0.9 (high certainty), info gain should be lower."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.9)

        # At p=0.9, entropy is lower than at p=0.5
        assert stamp["entropy"] < 1.0

    def test_silver_stamp_at_p_low(self):
        """At p=0.1 (low certainty door unlocked), info gain still matters."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.1)

        # Entropy should be similar to p=0.9 (symmetric around 0.5)
        assert stamp["entropy"] < 1.0

    def test_silver_score_reasonable_magnitude(self):
        """silver_score should be in reasonable range compared to base_score."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)

        base = stamp["base_score"]
        silver = stamp["silver_score"]

        # silver_score = base_score * (0.5 + 0.5 * shape_multiplier)
        # where shape_multiplier is in [0, 1]
        # So silver_score should be in [0.5*base, base]
        if base > 0:
            assert 0.5 * base <= silver <= base
        else:
            # If base is negative, silver should still be reasonable
            assert abs(silver) <= abs(base) * 1.5

    def test_silver_stamp_all_skills(self):
        """Should work for all three skills."""
        from scoring_silver import build_silver_stamp

        skills = [
            ("peek_door", 1.0),
            ("try_door", 1.5),
            ("go_window", 2.0),
        ]

        for skill_name, cost in skills:
            stamp = build_silver_stamp(skill_name, cost, 0.5)
            assert stamp["skill_name"] == skill_name
            assert stamp["cost"] == cost


class TestShapeCoefficients:
    """Test the shape coefficient calculations."""

    def test_k_explore_balanced_when_goal_info_equal(self):
        """When goal and info are equal, k_explore should be near 1.0."""
        from scoring_silver import build_silver_stamp

        # peek_door at p=0.5 has goal≈0 and info≈high
        # try_door at certain p might have balanced goal and info
        # This is more of a sanity check that the formula works

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)
        # k_explore = GM/AM where GM = sqrt(goal*info), AM = (goal+info)/2

        goal = abs(stamp["goal_value"])
        info = stamp["info_gain"]
        gm = stamp["gm_goal_info"]
        am = stamp["am_goal_info"]

        if am > 0:
            expected_k = gm / am
            assert stamp["k_explore"] == pytest.approx(expected_k, abs=0.01)

    def test_k_explore_low_when_imbalanced(self):
        """When goal and info are very imbalanced, k_explore should be low."""
        # This depends on the specific skill and belief
        # Just check that it's in valid range
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("go_window", 2.0, 0.5)
        # go_window has no info gain, so k_explore should be low
        assert 0.0 <= stamp["k_explore"] <= 1.0

    def test_k_efficiency_reasonable(self):
        """k_efficiency should reflect cost-effectiveness."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)
        # k_efficiency = GM(goal+info, cost) / AM(goal+info, cost)

        assert 0.0 <= stamp["k_efficiency"] <= 1.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_cost_handled(self):
        """Should handle zero cost gracefully."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 0.0, 0.5)
        # With _ensure_positive, cost becomes epsilon
        assert stamp["cost"] >= 0.0
        assert stamp["k_efficiency"] >= 0.0

    def test_extreme_belief_values(self):
        """Should handle p near 0 and 1."""
        from scoring_silver import build_silver_stamp

        # p very close to 0
        stamp_low = build_silver_stamp("peek_door", 1.0, 0.01)
        assert stamp_low["entropy"] >= 0.0

        # p very close to 1
        stamp_high = build_silver_stamp("peek_door", 1.0, 0.99)
        assert stamp_high["entropy"] >= 0.0

    def test_all_numeric_values(self):
        """All numeric values should be finite floats."""
        from scoring_silver import build_silver_stamp

        stamp = build_silver_stamp("peek_door", 1.0, 0.5)

        for key, value in stamp.items():
            if key != "stamp_version" and key != "skill_name":
                assert isinstance(value, (int, float))
                assert math.isfinite(value), f"{key} is not finite: {value}"
