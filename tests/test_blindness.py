
import unittest
from environments.domain4_textworld.text_parser import TextWorldParser

class TestBlindness(unittest.TestCase):
    def setUp(self):
        self.parser = TextWorldParser()
        
    def test_complex_description(self):
        """
        Test a complex observation that regex should fail to parse.
        """
        # A complex description not using standard "You see..." patterns
        observation = """
        -= Dusty Attic =-
        The room is filled with cobwebs.
        Hidden beneath the dirty rug, you spot a small brass key.
        On the shelf, obscured by books, lies a dusty tome.
        """
        
        # Try to extract objects
        objects = self.parser.extract_visible_objects(observation)
        
        print(f"\nInput: {observation}")
        print(f"Extracted: {objects}")
        
        # We EXPECT this to fail (return empty or incomplete)
        # If it succeeds, our regex is better than we thought (or the test is bad)
        expected_objects = ['small brass key', 'dusty tome']
        
        # Check if we found the key
        found_key = any('key' in obj for obj in objects)
        found_tome = any('tome' in obj for obj in objects)
        
        if not found_key:
            print("❌ FAILED to see 'small brass key'")
        if not found_tome:
            print("❌ FAILED to see 'dusty tome'")
            
        # Assert that we DO find them (this assertion will likely fail, proving blindness)
        self.assertTrue(found_key, "Parser is blind to 'hidden beneath...'")
        self.assertTrue(found_tome, "Parser is blind to 'obscured by...'")

if __name__ == '__main__':
    unittest.main()
