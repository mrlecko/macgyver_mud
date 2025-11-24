
import unittest
from environments.domain4_textworld.llm_parser import LLMParser

class TestNeuralPerception(unittest.TestCase):
    def setUp(self):
        self.parser = LLMParser()
        
    def test_complex_description_with_neural_parser(self):
        """
        Test that LLMParser can handle the complex observation.
        """
        observation = """
        -= Dusty Attic =-
        The room is filled with cobwebs.
        Hidden beneath the dirty rug, you spot a small brass key.
        On the shelf, obscured by books, lies a dusty tome.
        """
        
        # Use the Neural Parser
        objects = self.parser.extract_visible_objects(observation)
        
        print(f"\n[Neural] Input: {observation}")
        print(f"[Neural] Extracted: {objects}")
        
        # This time, we expect success
        self.assertIn('small brass key', objects)
        self.assertIn('dusty tome', objects)
        
    def test_regex_fallback(self):
        """
        Test that it still works for simple cases (System 1).
        """
        simple_obs = "You see a apple."
        objects = self.parser.extract_visible_objects(simple_obs)
        self.assertIn('apple', objects)

if __name__ == '__main__':
    unittest.main()
