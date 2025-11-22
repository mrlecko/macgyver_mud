"""
Tests for balanced skill mode in runner

Tests the --skill-mode flag integration:
- crisp: Only use base skills (peek, try, window)
- balanced: Only use balanced skills (probe_and_try, etc.)
- hybrid: Use all skills

Uses TDD approach: tests written before implementation.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# Module under test (will implement after tests)
# Import will be tested in individual tests


class TestGetSkills:
    """Test the basic get_skills function works"""

    def test_get_skills_returns_list(self):
        """get_skills should return a list of skill dicts"""
        from graph_model import get_skills

        session = Mock()
        session.run.return_value = []

        skills = get_skills(session, "agent_id")
        assert isinstance(skills, list)

    def test_get_skills_includes_kind_field(self):
        """Each skill dict should have a 'kind' field"""
        from graph_model import get_skills

        session = Mock()
        mock_record = {
            "name": "peek_door",
            "cost": 1.0,
            "kind": "sense",
            "description": "Test"
        }
        session.run.return_value = [mock_record]

        skills = get_skills(session, "agent_id")
        assert len(skills) > 0
        assert "kind" in skills[0]


class TestFilterSkillsByMode:
    """Test the filter_skills_by_mode function"""

    def setup_method(self):
        """Create test skills"""
        self.crisp_skills = [
            {"name": "peek_door", "kind": "sense", "cost": 1.0},
            {"name": "try_door", "kind": "act", "cost": 1.5},
            {"name": "go_window", "kind": "act", "cost": 2.0}
        ]

        self.balanced_skills = [
            {"name": "probe_and_try", "kind": "balanced", "cost": 2.0,
             "goal_fraction": 0.6, "info_fraction": 0.4},
            {"name": "informed_window", "kind": "balanced", "cost": 2.2,
             "goal_fraction": 0.8, "info_fraction": 0.3},
            {"name": "exploratory_action", "kind": "balanced", "cost": 2.5,
             "goal_fraction": 0.7, "info_fraction": 0.7},
            {"name": "adaptive_peek", "kind": "balanced", "cost": 1.3,
             "goal_fraction": 0.4, "info_fraction": 0.6}
        ]

        self.all_skills = self.crisp_skills + self.balanced_skills

    def test_filter_crisp_mode(self):
        """crisp mode should return only non-balanced skills"""
        from graph_model import filter_skills_by_mode

        result = filter_skills_by_mode(self.all_skills, "crisp")

        assert len(result) == 3
        assert all(s["kind"] != "balanced" for s in result)
        assert any(s["name"] == "peek_door" for s in result)
        assert any(s["name"] == "try_door" for s in result)
        assert any(s["name"] == "go_window" for s in result)

    def test_filter_balanced_mode(self):
        """balanced mode should return only balanced skills"""
        from graph_model import filter_skills_by_mode

        result = filter_skills_by_mode(self.all_skills, "balanced")

        assert len(result) == 4
        assert all(s["kind"] == "balanced" for s in result)
        assert any(s["name"] == "probe_and_try" for s in result)
        assert any(s["name"] == "informed_window" for s in result)
        assert any(s["name"] == "exploratory_action" for s in result)
        assert any(s["name"] == "adaptive_peek" for s in result)

    def test_filter_hybrid_mode(self):
        """hybrid mode should return all skills"""
        from graph_model import filter_skills_by_mode

        result = filter_skills_by_mode(self.all_skills, "hybrid")

        assert len(result) == 7
        # Should have both crisp and balanced
        assert any(s["kind"] != "balanced" for s in result)
        assert any(s["kind"] == "balanced" for s in result)

    def test_filter_invalid_mode_raises_error(self):
        """Invalid mode should raise ValueError"""
        from graph_model import filter_skills_by_mode

        with pytest.raises(ValueError, match="Invalid skill_mode"):
            filter_skills_by_mode(self.all_skills, "invalid")

    def test_filter_with_empty_list(self):
        """Filtering empty list should return empty list"""
        from graph_model import filter_skills_by_mode

        result = filter_skills_by_mode([], "crisp")
        assert result == []

    def test_filter_preserves_skill_properties(self):
        """Filtering should not modify skill dictionaries"""
        from graph_model import filter_skills_by_mode

        result = filter_skills_by_mode(self.all_skills, "balanced")

        # Check a balanced skill has all expected properties
        probe = next(s for s in result if s["name"] == "probe_and_try")
        assert "goal_fraction" in probe
        assert "info_fraction" in probe
        assert probe["goal_fraction"] == 0.6
        assert probe["info_fraction"] == 0.4


class TestAgentRuntimeWithSkillMode:
    """Test AgentRuntime integration with skill modes"""

    @patch('agent_runtime.get_skills')
    @patch('agent_runtime.get_agent')
    @patch('agent_runtime.get_initial_belief')
    def test_agent_runtime_accepts_skill_mode(self, mock_belief, mock_agent, mock_skills):
        """AgentRuntime should accept skill_mode parameter"""
        from agent_runtime import AgentRuntime

        mock_agent.return_value = {"id": "agent_1"}
        mock_belief.return_value = 0.5
        mock_skills.return_value = [
            {"name": "peek_door", "kind": "sense", "cost": 1.0}
        ]

        session = Mock(spec=Session)

        # Should accept skill_mode parameter
        runtime = AgentRuntime(
            session,
            door_state="unlocked",
            skill_mode="crisp"
        )

        assert hasattr(runtime, 'skill_mode')
        assert runtime.skill_mode == "crisp"

    @patch('agent_runtime.get_skills')
    @patch('agent_runtime.filter_skills_by_mode')
    @patch('agent_runtime.get_agent')
    @patch('agent_runtime.get_initial_belief')
    def test_agent_runtime_filters_skills_on_init(self, mock_belief, mock_agent,
                                                   mock_filter, mock_skills):
        """AgentRuntime should filter skills based on mode during initialization"""
        from agent_runtime import AgentRuntime

        mock_agent.return_value = {"id": "agent_1"}
        mock_belief.return_value = 0.5

        all_skills = [
            {"name": "peek_door", "kind": "sense", "cost": 1.0},
            {"name": "probe_and_try", "kind": "balanced", "cost": 2.0}
        ]
        mock_skills.return_value = all_skills
        mock_filter.return_value = [all_skills[1]]  # Only balanced skill

        session = Mock(spec=Session)

        runtime = AgentRuntime(
            session,
            door_state="unlocked",
            skill_mode="balanced"
        )

        # Should have called filter with correct mode
        mock_filter.assert_called_once()
        call_args = mock_filter.call_args
        assert call_args[0][1] == "balanced"


class TestRunnerCommandLine:
    """Test runner.py command line argument parsing"""

    def test_parse_args_accepts_skill_mode(self):
        """parse_args should accept --skill-mode flag"""
        from runner import parse_args

        with patch('sys.argv', ['runner.py', '--door-state', 'unlocked',
                                '--skill-mode', 'crisp']):
            args = parse_args()
            assert hasattr(args, 'skill_mode')
            assert args.skill_mode == 'crisp'

    def test_parse_args_validates_skill_mode(self):
        """parse_args should only accept valid skill modes"""
        from runner import parse_args

        # Valid modes should work
        for mode in ['crisp', 'balanced', 'hybrid']:
            with patch('sys.argv', ['runner.py', '--door-state', 'unlocked',
                                    '--skill-mode', mode]):
                args = parse_args()
                assert args.skill_mode == mode

    def test_parse_args_default_skill_mode(self):
        """parse_args should default to hybrid mode"""
        from runner import parse_args

        with patch('sys.argv', ['runner.py', '--door-state', 'unlocked']):
            args = parse_args()
            assert hasattr(args, 'skill_mode')
            assert args.skill_mode == 'hybrid'


class TestScoringIntegration:
    """Test that scoring works with balanced skills"""

    def test_balanced_skill_scoring_has_both_components(self):
        """Balanced skills should have non-zero goal AND info"""
        from scoring_balanced import score_balanced_skill_detailed

        skill = {
            "name": "probe_and_try",
            "cost": 2.0,
            "goal_fraction": 0.6,
            "info_fraction": 0.4
        }

        result = score_balanced_skill_detailed(skill, p_unlocked=0.5)

        # Should have both components
        assert result["goal_value"] > 0, "Balanced skill should have goal value"
        assert result["info_gain"] > 0, "Balanced skill should have info gain"

        # Should have the fractions
        assert "goal_fraction" in result
        assert "info_fraction" in result

    def test_agent_runtime_can_score_balanced_skills(self):
        """AgentRuntime should be able to score balanced skills"""
        # This is an integration test that will validate the full flow
        # We'll test this after implementation
        pass


class TestBalancedSkillSimulation:
    """Test that balanced skills can be simulated in episodes"""

    def test_balanced_skill_produces_observations(self):
        """Balanced skills should produce valid observations"""
        # These skills need observation simulation logic
        # Will implement along with the feature
        pass

    def test_balanced_skill_updates_belief(self):
        """Balanced skills should update agent belief appropriately"""
        # Balanced skills provide partial information
        # Belief updates should reflect this
        pass


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.integration
    def test_run_episode_with_crisp_mode(self):
        """Full episode should work with crisp mode"""
        # Will test with real Neo4j after implementation
        pass

    @pytest.mark.integration
    def test_run_episode_with_balanced_mode(self):
        """Full episode should work with balanced mode"""
        # Will test with real Neo4j after implementation
        pass

    @pytest.mark.integration
    def test_run_episode_with_hybrid_mode(self):
        """Full episode should work with hybrid mode"""
        # Will test with real Neo4j after implementation
        pass


# Run tests to confirm they fail (TDD red phase)
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
