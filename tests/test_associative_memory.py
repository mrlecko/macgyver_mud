import unittest
from unittest.mock import MagicMock
import sys

# Mock neo4j
sys.modules['neo4j'] = MagicMock()

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
# We will create this class shortly
# from environments.domain4_textworld.memory_system import MemoryRetriever 

class TestAssociativeMemory(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)
        
        # Mock the memory retriever
        self.agent.memory = MagicMock()
        
        # Set dummy room so memory calculation proceeds
        self.agent.beliefs['current_room'] = 'Test Room'
        self.agent.beliefs['rooms'] = {'Test Room': {'description': 'A test room'}}
        
    def test_memory_impact_on_score(self):
        """
        Test that positive memories increase action score and negative ones decrease it.
        """
        # Scenario: 'eat apple' was good in the past
        self.agent.memory.retrieve_relevant_memories.return_value = [
            {'action': 'eat apple', 'outcome': 'positive', 'confidence': 0.9}
        ]
        
        score_good = self.agent.score_action('eat apple', self.agent.beliefs)
        
        # Scenario: 'eat poison' was bad in the past
        self.agent.memory.retrieve_relevant_memories.return_value = [
            {'action': 'eat poison', 'outcome': 'negative', 'confidence': 0.9}
        ]
        
        score_bad = self.agent.score_action('eat poison', self.agent.beliefs)
        
        print(f"Score Good: {score_good}, Score Bad: {score_bad}")
        self.assertGreater(score_good, score_bad, "Positive memories should yield higher scores than negative ones")

    def test_unknown_action_neutral(self):
        """
        Test that actions with no memory have neutral memory impact.
        """
        self.agent.memory.retrieve_relevant_memories.return_value = []
        
        score_neutral = self.agent.score_action('jump', self.agent.beliefs)
        
        # Compare with known good/bad from previous test logic (conceptually)
        # Here we just ensure it runs without error and returns a float
        self.assertIsInstance(score_neutral, float)

if __name__ == '__main__':
    unittest.main()
