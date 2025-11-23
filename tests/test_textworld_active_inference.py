import unittest
from unittest.mock import MagicMock
import sys

# Mock neo4j to avoid import issues in test environment
mock_neo4j = MagicMock()
sys.modules['neo4j'] = mock_neo4j

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

class TestTextWorldActiveInference(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)
        
    def test_penalize_loops(self):
        """Test that repeating the same action sequence is penalized."""
        # Simulate history of going back and forth
        self.agent.action_history = [
            {'action': 'go north', 'step': 1},
            {'action': 'go south', 'step': 2},
            {'action': 'go north', 'step': 3}
        ]
        self.agent.beliefs['current_room'] = 'Room A'
        
        # Score 'go south' (repeating loop) vs 'go east' (new action)
        score_loop = self.agent.score_action('go south', self.agent.beliefs)
        score_new = self.agent.score_action('go east', self.agent.beliefs)
        
        # New action should have higher score (lower cost)
        self.assertGreater(score_new, score_loop, "Looping action should be penalized")

    def test_reward_exploration(self):
        """Test that exploring new rooms is rewarded (Entropy reduction)."""
        # Setup beliefs where 'Room B' is known but 'Room C' is unknown
        self.agent.beliefs['rooms'] = {
            'Room A': {'visited': True},
            'Room B': {'visited': True}
        }
        # We can't easily simulate "unknown room" without map knowledge,
        # but we can test that 'look' (info gain) is valued when uncertainty is high.
        
        # For now, let's test that 'examine' unknown object is better than known
        self.agent.beliefs['objects'] = {
            'known_obj': {'examined_count': 1},
            'unknown_obj': {'examined_count': 0}
        }
        
        score_known = self.agent.score_action('examine known_obj', self.agent.beliefs)
        score_unknown = self.agent.score_action('examine unknown_obj', self.agent.beliefs)
        
        self.assertGreater(score_unknown, score_known, "Examining unknown object should be preferred")

    def test_goal_seeking(self):
        """Test that actions leading to reward are prioritized."""
        # This is harder to test without a world model, but we can check
        # if the agent prioritizes 'take' if it hasn't held the item before.
        
        self.agent.beliefs['inventory'] = []
        score_take = self.agent.score_action('take key', self.agent.beliefs)
        score_wait = self.agent.score_action('wait', self.agent.beliefs)
        
        self.assertGreater(score_take, score_wait, "Taking items should be prioritized (goal value)")

if __name__ == '__main__':
    unittest.main()
