
print("DEBUG: Starting test_graph_mind execution")
import unittest
from unittest.mock import MagicMock
import sys
# Mock neo4j
sys.modules['neo4j'] = MagicMock()

import networkx as nx
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.llm_parser import LLMParser

class TestGraphMind(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)
        
    def test_graph_initialization(self):
        """
        Test that the agent initializes with a graph.
        """
        self.assertIsInstance(self.agent.knowledge_graph, nx.DiGraph)
        
    def test_triplet_extraction(self):
        """
        Test that the parser can extract triplets from text.
        """
        text = "Hidden beneath the dirty rug, you spot a small brass key."
        triplets = self.agent.parser.extract_triplets(text)
        
        print(f"\nInput: {text}")
        print(f"Triplets: {triplets}")
        
        # We expect: ('small brass key', 'located_under', 'dirty rug')
        expected = ('small brass key', 'located_under', 'dirty rug')
        self.assertIn(expected, triplets)
        
    def test_graph_update(self):
        """
        Test that update_beliefs populates the graph.
        """
        observation = "Hidden beneath the dirty rug, you spot a small brass key."
        self.agent.update_beliefs(observation)
        
        # Check if nodes and edges exist
        self.assertTrue(self.agent.knowledge_graph.has_node('small brass key'))
        self.assertTrue(self.agent.knowledge_graph.has_node('dirty rug'))
        self.assertTrue(self.agent.knowledge_graph.has_edge('small brass key', 'dirty rug'))
        
        # Check edge attribute
        edge_data = self.agent.knowledge_graph.get_edge_data('small brass key', 'dirty rug')
        self.assertEqual(edge_data['relation'], 'located_under')

if __name__ == '__main__':
    unittest.main()
