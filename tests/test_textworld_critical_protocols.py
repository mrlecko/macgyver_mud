"""
Test critical state protocol integration in TextWorldCognitiveAgent.

Tests the hardening improvements:
1. Critical state detection
2. Protocol application (PANIC, DEADLOCK, SCARCITY, etc.)
3. Error handling and defensive programming
4. Coefficient tuning effects
"""
import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock neo4j to avoid import issues in test environment
mock_neo4j = MagicMock()
sys.modules['neo4j'] = mock_neo4j

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from critical_state import CriticalState


class TestCriticalStateProtocols(unittest.TestCase):
    """Test critical state protocol integration."""

    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)

    def test_critical_monitor_initialization(self):
        """Test that critical state monitor is properly initialized."""
        self.assertIsNotNone(self.agent.critical_monitor)
        self.assertEqual(self.agent.current_critical_state, CriticalState.FLOW)

    def test_location_tracking(self):
        """Test that location changes are tracked for deadlock detection."""
        # Simulate room changes
        obs1 = "-= Room A =-\nYou are in room A."
        obs2 = "-= Room B =-\nYou are in room B."

        self.agent.update_beliefs(obs1, "")
        self.assertIn("Room A", self.agent.location_history)

        self.agent.update_beliefs(obs2, "")
        self.assertIn("Room B", self.agent.location_history)

        self.assertEqual(len(self.agent.location_history), 2)

    def test_panic_protocol_activation(self):
        """Test PANIC protocol triggers on high entropy."""
        # Manually set high entropy state
        self.agent.current_step = 10
        self.agent.max_steps = 100

        # Create many unknown objects (high entropy)
        self.agent.beliefs['objects'] = {
            f'obj{i}': {'examined_count': 0} for i in range(15)
        }

        # Get agent state
        agent_state = self.agent.get_agent_state_for_critical_monitor()

        # Entropy should be high
        self.assertGreater(agent_state.entropy, 0.3)

    def test_deadlock_protocol_activation(self):
        """Test DEADLOCK protocol triggers on loop pattern."""
        # Simulate A -> B -> A -> B pattern
        self.agent.location_history = ['Room A', 'Room B', 'Room A', 'Room B']

        agent_state = self.agent.get_agent_state_for_critical_monitor()
        critical_state = self.agent.critical_monitor.evaluate(agent_state)

        # Should detect deadlock
        self.assertEqual(critical_state, CriticalState.DEADLOCK)

    def test_scarcity_protocol_activation(self):
        """Test SCARCITY protocol triggers when running out of steps."""
        # Set low steps remaining, high distance
        self.agent.current_step = 95
        self.agent.max_steps = 100
        self.agent.distance_to_goal = 15.0

        agent_state = self.agent.get_agent_state_for_critical_monitor()
        critical_state = self.agent.critical_monitor.evaluate(agent_state)

        # Should detect scarcity
        self.assertEqual(critical_state, CriticalState.SCARCITY)

    def test_protocol_action_override(self):
        """Test that protocols can override normal EFE action selection."""
        commands = ['go north', 'go south', 'examine key', 'look', 'inventory']

        # Test PANIC protocol (should prefer safe actions)
        panic_action = self.agent.apply_critical_state_protocol(
            CriticalState.PANIC, commands
        )
        self.assertIsNotNone(panic_action)
        self.assertIn(panic_action, ['examine key', 'look', 'inventory'])

        # Test FLOW state (should return None - use normal EFE)
        flow_action = self.agent.apply_critical_state_protocol(
            CriticalState.FLOW, commands
        )
        self.assertIsNone(flow_action)

    def test_deadlock_protocol_breaks_loops(self):
        """Test DEADLOCK protocol avoids recently used actions."""
        commands = ['go north', 'go south', 'go east', 'look']

        # Simulate recent back-and-forth
        self.agent.action_history = [
            {'action': 'go north', 'step': 1, 'score': 1.0},
            {'action': 'go south', 'step': 2, 'score': 1.0},
            {'action': 'go north', 'step': 3, 'score': 1.0},
            {'action': 'go south', 'step': 4, 'score': 1.0}
        ]

        action = self.agent.apply_critical_state_protocol(
            CriticalState.DEADLOCK, commands
        )

        # Should avoid 'go north' and 'go south'
        self.assertNotIn(action, ['go north', 'go south'])

    def test_input_validation_invalid_commands(self):
        """Test that invalid commands are filtered out."""
        # Mix of valid and invalid commands
        commands = ['go north', None, '', 123, 'look', [], 'examine key']

        action = self.agent.select_action(commands, None)

        # Should still select a valid action
        self.assertIn(action, ['go north', 'look', 'examine key'])

    def test_input_validation_empty_commands(self):
        """Test fallback when no valid commands."""
        action = self.agent.select_action([], None)
        self.assertEqual(action, "look")

        action = self.agent.select_action(None, None)
        self.assertEqual(action, "look")

    def test_memory_bonus_defensive_checks(self):
        """Test that memory bonus doesn't crash on missing data."""
        # No current room
        bonus = self.agent.calculate_memory_bonus('go north')
        self.assertEqual(bonus, 0.0)

        # Current room set but not in rooms dict
        self.agent.beliefs['current_room'] = 'Mystery Room'
        bonus = self.agent.calculate_memory_bonus('go north')
        self.assertEqual(bonus, 0.0)

        # Current room in dict but no description
        self.agent.beliefs['rooms'] = {'Mystery Room': {}}
        bonus = self.agent.calculate_memory_bonus('go north')
        self.assertEqual(bonus, 0.0)

    def test_save_episode_error_handling(self):
        """Test that save_episode doesn't crash on DB errors."""
        # Mock session that raises error
        self.agent.session = MagicMock()
        self.agent.session.run.side_effect = Exception("DB connection failed")

        # Should not raise exception
        try:
            self.agent.save_episode()
        except Exception as e:
            self.fail(f"save_episode raised exception: {e}")

    def test_coefficient_tuning_effects(self):
        """Test that tuned coefficients favor goal-directed actions."""
        self.agent.beliefs['current_room'] = 'Test Room'
        self.agent.beliefs['rooms'] = {'Test Room': {'description': 'A test room'}}

        # Score exploration vs exploitation actions
        score_explore = self.agent.score_action('look', self.agent.beliefs)
        score_exploit = self.agent.score_action('take key', self.agent.beliefs)

        # With tuned coefficients, exploitation should score higher
        # (alpha=3.0 for goal value > beta=2.0 for entropy)
        self.assertGreater(score_exploit, score_explore,
                          "Goal-directed action should score higher than pure exploration")

    def test_reset_clears_critical_state(self):
        """Test that reset properly clears critical state tracking."""
        # Set some state
        self.agent.location_history = ['Room A', 'Room B']
        self.agent.current_critical_state = CriticalState.PANIC
        self.agent.distance_to_goal = 5.0

        # Reset
        self.agent.reset()

        # Should be cleared
        self.assertEqual(len(self.agent.location_history), 0)
        self.assertEqual(self.agent.current_critical_state, CriticalState.FLOW)
        self.assertEqual(self.agent.distance_to_goal, 20.0)

    def test_distance_updates_on_reward(self):
        """Test that distance estimate updates when receiving reward."""
        self.agent.distance_to_goal = 20.0

        # Simulate a step with reward
        commands = ['look']
        self.agent.step(
            observation="-= Room =-\nA room.",
            feedback="",
            reward=1.0,
            done=False,
            admissible_commands=commands,
            quest=None
        )

        # Distance should decrease
        self.assertLess(self.agent.distance_to_goal, 20.0)


class TestRobustnessEdgeCases(unittest.TestCase):
    """Test edge cases and robustness."""

    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)

    def test_scoring_with_empty_history(self):
        """Test that scoring works with no history."""
        score = self.agent.score_action('look', self.agent.beliefs)
        self.assertIsInstance(score, float)

    def test_critical_state_with_minimal_data(self):
        """Test critical state evaluation with minimal agent data."""
        # Empty histories
        agent_state = self.agent.get_agent_state_for_critical_monitor()

        critical_state = self.agent.critical_monitor.evaluate(agent_state)

        # Should default to FLOW or another safe state
        self.assertIsInstance(critical_state, CriticalState)

    def test_protocol_with_no_matching_commands(self):
        """Test protocols when no commands match their criteria."""
        # Only movement commands
        commands = ['go north', 'go south', 'go east', 'go west']

        # PANIC wants safe commands (look, examine, inventory)
        action = self.agent.apply_critical_state_protocol(
            CriticalState.PANIC, commands
        )

        # Should fall back gracefully (None to use EFE, or pick something)
        # Implementation might return None or pick best available
        self.assertTrue(action is None or action in commands)


if __name__ == '__main__':
    unittest.main()
