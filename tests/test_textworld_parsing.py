
import unittest
from environments.domain4_textworld.text_parser import TextWorldParser

class TestTextWorldParsing(unittest.TestCase):
    def setUp(self):
        self.parser = TextWorldParser()

    def test_extract_room_name(self):
        """Test extraction of room name from standard TextWorld header."""
        observation = """
-= Kitchen =-
You are in a kitchen. It seems to be pretty standard.
You can see a closed fridge.
"""
        room_name = self.parser.extract_room_name(observation)
        self.assertEqual(room_name, "Kitchen")

    def test_extract_room_name_complex(self):
        """Test extraction with different formatting or noise."""
        observation = """
-= Master Bedroom =-
You are in a master bedroom.
"""
        room_name = self.parser.extract_room_name(observation)
        self.assertEqual(room_name, "Master Bedroom")
        
    def test_extract_room_name_none(self):
        """Test behavior when no room header is present."""
        observation = "You look around but see nothing special."
        room_name = self.parser.extract_room_name(observation)
        self.assertIsNone(room_name)

    def test_extract_objects_simple(self):
        """Test extraction of objects from 'You see' patterns."""
        observation = "You see a key and a chest."
        objects = self.parser.extract_visible_objects(observation)
        self.assertIn("key", objects)
        self.assertIn("chest", objects)

    def test_extract_objects_make_out(self):
        """Test extraction from 'You can make out' pattern."""
        observation = "You can make out a safe. The safe is empty!"
        objects = self.parser.extract_visible_objects(observation)
        self.assertIn("safe", objects)

    def test_extract_objects_list(self):
        """Test extraction from comma-separated lists."""
        observation = "You see a apple, a banana and a orange."
        objects = self.parser.extract_visible_objects(observation)
        self.assertIn("apple", objects)
        self.assertIn("banana", objects)
        self.assertIn("orange", objects)

    def test_extract_inventory_simple(self):
        """Test extraction from 'You are carrying' pattern."""
        text = "You are carrying: a lamp and a sword."
        inventory = self.parser.extract_inventory(text)
        self.assertIn("lamp", inventory)
        self.assertIn("sword", inventory)

    def test_extract_inventory_nothing(self):
        """Test extraction when carrying nothing."""
        text = "You are carrying nothing."
        inventory = self.parser.extract_inventory(text)
        self.assertEqual(inventory, [])

if __name__ == '__main__':
    unittest.main()
