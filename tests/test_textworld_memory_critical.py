
import unittest
from unittest.mock import MagicMock, call
import sys

# Mock neo4j to avoid import issues
mock_neo4j = MagicMock()
sys.modules['neo4j'] = mock_neo4j

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from critical_state import CriticalState

class TestTextWorldMemoryCritical(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)

    def test_detect_stuck_state(self):
        """Test detection of being stuck (critical state via scarcity or low reward)."""
        # Simulate no score change for many steps with low steps remaining
        self.agent.reward_history = [0] * 20
        self.agent.current_step = 85
        self.agent.max_steps = 100
        self.agent.distance_to_goal = 20.0

        # Get critical state from monitor
        agent_state = self.agent.get_agent_state_for_critical_monitor()
        critical_state = self.agent.critical_monitor.evaluate(agent_state)

        # Should detect some critical state (likely SCARCITY)
        self.assertNotEqual(critical_state, CriticalState.FLOW,
                           "Should detect critical state when stuck (no reward, low steps)")

    def test_detect_not_stuck(self):
        """Test that we are in FLOW state when making progress."""
        self.agent.reward_history = [0] * 9 + [1]  # Recent reward
        self.agent.current_step = 20
        self.agent.max_steps = 100
        self.agent.distance_to_goal = 10.0
        self.agent.location_history = ['Room A', 'Room B', 'Room C']  # No loops

        # Get critical state from monitor
        agent_state = self.agent.get_agent_state_for_critical_monitor()
        critical_state = self.agent.critical_monitor.evaluate(agent_state)

        # Should be in FLOW or HUBRIS (good states), not PANIC/DEADLOCK/SCARCITY
        self.assertNotIn(critical_state, [CriticalState.PANIC, CriticalState.DEADLOCK, CriticalState.SCARCITY],
                        "Should not be in bad critical state when making progress")

    def test_save_episode_memory(self):
        """Test saving episode to Neo4j."""
        # Setup dummy episode data
        self.agent.observation_history = [
            {'step': 0, 'observation': 'Room A', 'feedback': ''},
            {'step': 1, 'observation': 'Room B', 'feedback': ''}
        ]
        self.agent.action_history = [
            {'step': 0, 'action': 'go north', 'score': 5.0}
        ]
        self.agent.reward_history = [0, 10]
        self.agent.beliefs['current_room'] = 'Room B'
        
        self.agent.save_episode()
        
        # Verify Neo4j interaction
        # We expect at least one call to session.run to create the Episode node
        self.assertTrue(self.mock_session.run.called, "Should call session.run to save memory")
        
        # Check if Cypher query contains expected labels
        calls = self.mock_session.run.call_args_list
        cypher_queries = [c[0][0] for c in calls]
        
        # Look for Episode creation
        has_create_episode = any("CREATE (e:Episode" in q or "MERGE (e:Episode" in q for q in cypher_queries)
        self.assertTrue(has_create_episode, "Should execute Cypher to create Episode node")

if __name__ == '__main__':
    unittest.main()
