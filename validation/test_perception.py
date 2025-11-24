"""
Verification Script for Perceptual Layer
Tests the LLMPerception class against sample TextWorld observations.
"""

import unittest
from perception.llm_parser import LLMPerception

# Sample 1: Simple Kitchen
SAMPLE_KITCHEN = """
You are in a kitchen. An ordinary room. You can see a closed fridge here. 
There is a table here. On the table you see an apple and a knife.
There is a stove here.
Exits: north, east.
"""

# Sample 2: Complex Living Room
SAMPLE_LIVING_ROOM = """
You find yourself in a living room. It's quite cozy.
You see a sofa. On the sofa is a remote control.
There is a TV stand here. On the TV stand is a TV.
You can also see a wooden door to the west. It is locked.
A glass door leads south. It is open.
Exits: north, south, west.
"""

class TestPerception(unittest.TestCase):
    def setUp(self):
        self.perception = LLMPerception(model_name="gpt-4o-mini")
        
    def test_kitchen_parsing(self):
        print("\nTesting Kitchen Parsing...")
        result = self.perception.parse(SAMPLE_KITCHEN)
        print(f"Result: {result}")
        
        self.assertEqual(result["room_name"].lower(), "kitchen")
        self.assertIn("north", result["exits"])
        self.assertIn("east", result["exits"])
        
        item_names = [i["name"].lower() for i in result["items"]]
        self.assertIn("fridge", item_names)
        self.assertIn("apple", item_names)
        self.assertIn("knife", item_names)
        self.assertIn("table", item_names)
        
        # Check attributes
        fridge = next(i for i in result["items"] if i["name"].lower() == "fridge")
        self.assertEqual(fridge["state"], "closed")
        
        apple = next(i for i in result["items"] if i["name"].lower() == "apple")
        self.assertIn("table", apple["location"].lower())

    def test_living_room_parsing(self):
        print("\nTesting Living Room Parsing...")
        result = self.perception.parse(SAMPLE_LIVING_ROOM)
        print(f"Result: {result}")
        
        self.assertEqual(result["room_name"].lower(), "living room")
        self.assertIn("west", result["exits"])
        
        item_names = [i["name"].lower() for i in result["items"]]
        self.assertIn("sofa", item_names)
        self.assertIn("remote control", item_names)
        self.assertIn("wooden door", item_names)
        
        # Check door states
        door = next(i for i in result["items"] if i["name"].lower() == "wooden door")
        self.assertEqual(door["state"], "locked")

if __name__ == '__main__':
    unittest.main()
