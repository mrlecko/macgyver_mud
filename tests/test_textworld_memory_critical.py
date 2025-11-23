
import unittest
from unittest.mock import MagicMock, call
import sys

# Mock neo4j to avoid import issues
mock_neo4j = MagicMock()
sys.modules['neo4j'] = mock_neo4j

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

class TestTextWorldMemoryCritical(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)
        
    def test_detect_stuck_state(self):
        """Test detection of being stuck (critical state)."""
        # Simulate no score change for many steps
        self.agent.reward_history = [0] * 20
        self.agent.current_step = 20
        
        is_critical = self.agent.check_critical_state()
        self.assertTrue(is_critical, "Should detect critical state when stuck (no reward for 20 steps)")
        
    def test_detect_not_stuck(self):
        """Test that we are not stuck if getting rewards."""
        self.agent.reward_history = [0] * 19 + [1]
        self.agent.current_step = 20
        
        is_critical = self.agent.check_critical_state()
        self.assertFalse(is_critical, "Should not be critical if recently rewarded")

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
