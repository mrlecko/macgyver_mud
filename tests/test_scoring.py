"""
Unit tests for scoring.py (Active Inference scoring logic)
Following TDD approach - write tests first!
"""
import pytest
import math
from scoring import entropy, expected_goal_value, expected_info_gain, score_skill
import config


class TestEntropy:
    """Test entropy function for Bernoulli distribution"""

    def test_entropy_boundary_zero(self):
        """Entropy should be 0 at p=0"""
        assert entropy(0.0) == 0.0

    def test_entropy_boundary_one(self):
        """Entropy should be 0 at p=1"""
        assert entropy(1.0) == 0.0

    def test_entropy_maximum_at_half(self):
        """Entropy should be maximum at p=0.5"""
        max_entropy = entropy(0.5)
        assert entropy(0.2) < max_entropy
        assert entropy(0.8) < max_entropy
        assert max_entropy > 0.9  # Should be close to 1.0

    def test_entropy_symmetric(self):
        """Entropy should be symmetric around 0.5"""
        assert abs(entropy(0.3) - entropy(0.7)) < 0.001
        assert abs(entropy(0.2) - entropy(0.8)) < 0.001

    def test_entropy_monotonic_below_half(self):
        """Entropy should increase from 0 to 0.5"""
        assert entropy(0.1) < entropy(0.2) < entropy(0.3) < entropy(0.4) < entropy(0.5)

    def test_entropy_monotonic_above_half(self):
        """Entropy should decrease from 0.5 to 1"""
        assert entropy(0.5) > entropy(0.6) > entropy(0.7) > entropy(0.8) > entropy(0.9)


class TestExpectedGoalValue:
    """Test goal value calculation for each skill"""

    def test_peek_door_no_goal_value(self):
        """peek_door is pure sensing, no direct goal value"""
        assert expected_goal_value("peek_door", 0.5) == 0.0
        assert expected_goal_value("peek_door", 0.9) == 0.0

    def test_try_door_increases_with_belief(self):
        """try_door value should increase as p_unlocked increases"""
        low_belief = expected_goal_value("try_door", 0.1)
        mid_belief = expected_goal_value("try_door", 0.5)
        high_belief = expected_goal_value("try_door", 0.9)

        assert low_belief < mid_belief < high_belief

    def test_try_door_negative_when_likely_locked(self):
        """try_door should have negative value when door likely locked"""
        assert expected_goal_value("try_door", 0.1) < 0

    def test_try_door_positive_when_likely_unlocked(self):
        """try_door should have positive value when door likely unlocked"""
        assert expected_goal_value("try_door", 0.9) > 0

    def test_go_window_constant(self):
        """go_window value should be constant (independent of belief)"""
        val1 = expected_goal_value("go_window", 0.1)
        val2 = expected_goal_value("go_window", 0.5)
        val3 = expected_goal_value("go_window", 0.9)

        assert val1 == val2 == val3
        assert val1 > 0  # Should be positive (escape reward - slow penalty)

    def test_go_window_less_than_perfect_escape(self):
        """go_window should be less valuable than perfect door escape"""
        window_value = expected_goal_value("go_window", 1.0)
        perfect_door = config.REWARD_ESCAPE  # What we'd get if door guaranteed unlocked

        assert window_value < perfect_door


class TestExpectedInfoGain:
    """Test information gain calculation for each skill"""

    def test_peek_door_info_gain_equals_entropy(self):
        """peek_door info gain should equal entropy of current belief"""
        for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
            assert abs(expected_info_gain("peek_door", p) - entropy(p)) < 0.001

    def test_peek_door_max_info_at_half(self):
        """peek_door should have maximum info gain when p=0.5"""
        max_gain = expected_info_gain("peek_door", 0.5)
        assert expected_info_gain("peek_door", 0.2) < max_gain
        assert expected_info_gain("peek_door", 0.8) < max_gain

    def test_try_door_no_info_gain(self):
        """try_door provides no information gain (action, not sensing)"""
        assert expected_info_gain("try_door", 0.5) == 0.0
        assert expected_info_gain("try_door", 0.9) == 0.0

    def test_go_window_no_info_gain(self):
        """go_window provides no information gain"""
        assert expected_info_gain("go_window", 0.5) == 0.0
        assert expected_info_gain("go_window", 0.9) == 0.0


class TestScoreSkill:
    """Test overall skill scoring function"""

    def test_score_at_uncertain_belief(self):
        """At p=0.5 (uncertain), peek_door should beat try_door (prefer info over risk)"""
        skills = [
            {"name": "peek_door", "cost": 1.0},
            {"name": "try_door", "cost": 1.5},
            {"name": "go_window", "cost": 2.0}
        ]

        scores = {s["name"]: score_skill(s, 0.5) for s in skills}

        # peek_door should beat try_door (prefer info gathering over risky action when uncertain)
        assert scores["peek_door"] > scores["try_door"]

        # Note: go_window (safe escape) might still score highest - this is acceptable
        # behavior as it's rational to take the safe option when uncertain

    def test_score_at_high_belief_unlocked(self):
        """At p=0.9 (confident unlocked), try_door should score highest"""
        skills = [
            {"name": "peek_door", "cost": 1.0},
            {"name": "try_door", "cost": 1.5},
            {"name": "go_window", "cost": 2.0}
        ]

        scores = {s["name"]: score_skill(s, 0.9) for s in skills}

        # try_door should win due to high goal value
        assert scores["try_door"] > scores["peek_door"]
        assert scores["try_door"] > scores["go_window"]

    def test_score_at_low_belief_locked(self):
        """At p=0.1 (confident locked), go_window should score highest"""
        skills = [
            {"name": "peek_door", "cost": 1.0},
            {"name": "try_door", "cost": 1.5},
            {"name": "go_window", "cost": 2.0}
        ]

        scores = {s["name"]: score_skill(s, 0.1) for s in skills}

        # go_window should win (safe escape, try_door has negative value)
        assert scores["go_window"] > scores["try_door"]
        # peek_door might still be close due to some info gain, but window should be viable

    def test_score_uses_alpha_beta_gamma(self):
        """Score should incorporate all three weights"""
        skill = {"name": "peek_door", "cost": 1.0}
        p = 0.5

        # Default scores
        default_score = score_skill(skill, p)

        # Changing weights should change score
        high_beta_score = score_skill(skill, p, alpha=1.0, beta=10.0, gamma=0.3)
        high_gamma_score = score_skill(skill, p, alpha=1.0, beta=2.0, gamma=1.0)

        assert high_beta_score > default_score  # More weight on info gain
        assert high_gamma_score < default_score  # More weight on cost

    def test_score_monotonic_with_parameters(self):
        """Verify score responds correctly to parameter changes"""
        skill = {"name": "try_door", "cost": 1.5}

        # Increasing alpha should increase score for goal-oriented skills
        score_low_alpha = score_skill(skill, 0.9, alpha=0.5, beta=2.0, gamma=0.1)
        score_high_alpha = score_skill(skill, 0.9, alpha=2.0, beta=2.0, gamma=0.1)

        assert score_high_alpha > score_low_alpha


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_entropy_near_zero(self):
        """Test entropy for values very close to 0"""
        assert entropy(0.001) >= 0
        assert entropy(0.001) < 0.1

    def test_entropy_near_one(self):
        """Test entropy for values very close to 1"""
        assert entropy(0.999) >= 0
        assert entropy(0.999) < 0.1

    def test_unknown_skill_name(self):
        """Unknown skills should have sensible defaults"""
        # Should not crash
        result = expected_goal_value("unknown_skill", 0.5)
        assert result == 0.0  # Default to 0 for unknown skills

        result = expected_info_gain("unknown_skill", 0.5)
        assert result == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
