
import re
from typing import Optional, List, Dict

class TextWorldParser:
    """
    Parses raw text observations from TextWorld into structured data.
    """
    def __init__(self):
        pass

    def extract_room_name(self, text: str) -> Optional[str]:
        """
        Extracts the room name from the observation header.
        Expected format: "-= Room Name =-"
        """
        match = re.search(r"-=\s*(.*?)\s*=-", text)
        if match:
            return match.group(1).strip()
        return None

    def extract_visible_objects(self, text: str) -> List[str]:
        """
        Extracts visible objects from the text.
        Handles patterns like:
        - "You see a [obj], a [obj] and a [obj]."
        - "You can make out a [obj]."
        """
        objects = []
        
        # Patterns to look for
        patterns = [
            r"You see (.*?)\.",
            r"You can see (.*?)\.",
            r"You can make out (.*?)\."
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(1)
                # Split by comma and 'and'
                # "a key, a chest and a map" -> ["a key", "a chest", "a map"]
                items = re.split(r",| and ", content)
                for item in items:
                    item = item.strip()
                    if not item:
                        continue
                    
                    # Clean up determiners
                    # "a key" -> "key"
                    clean_item = re.sub(r"^(a|an|the)\s+", "", item, flags=re.IGNORECASE)
                    objects.append(clean_item)
                    
        return objects

    def extract_inventory(self, text: str) -> List[str]:
        """
        Extracts inventory items from text.
        Expected format: "You are carrying: a [item], a [item]."
        """
        if "You are carrying nothing" in text:
            return []
            
        match = re.search(r"You are carrying: (.*?)(?:\.|$)", text, re.IGNORECASE)
        if match:
            content = match.group(1)
            items = re.split(r",| and ", content)
            inventory = []
            for item in items:
                item = item.strip()
                if not item:
                    continue
                clean_item = re.sub(r"^(a|an|the)\s+", "", item, flags=re.IGNORECASE)
                inventory.append(clean_item)
            return inventory
            
        return []
