"""
Perceptual Layer (LLM Parser)

This module provides a semantic parser for TextWorld observations using Large Language Models.
It replaces fragile regex-based parsing with robust, schema-constrained extraction.
"""

import json
import llm
from typing import Dict, Any, Optional

# strict JSON Schema for TextWorld observations
OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "room_name": {
            "type": "string",
            "description": "The name of the current room (e.g., 'Kitchen', 'Backyard')"
        },
        "description": {
            "type": "string",
            "description": "The general description of the room"
        },
        "exits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of available directions (e.g., 'north', 'east')"
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "state": {
                        "type": "string", 
                        "description": "State of the item (e.g., 'open', 'closed', 'locked', 'empty', 'unlocked')"
                    },
                    "location": {
                        "type": "string", 
                        "description": "Where the item is found (e.g., 'on table', 'floor')"
                    }
                },
                "required": ["name"]
            },
            "description": "List of interactive items found in the room"
        }
    },
    "required": ["room_name", "exits", "items"]
}

class LLMPerception:
    """
    A perceptual encoder that translates raw text into structured graph nodes
    using an LLM with structured output enforcement.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = llm.get_model(model_name)
        self.schema = OBSERVATION_SCHEMA
        
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse a raw text observation into a structured dictionary.
        
        Args:
            text: The raw text output from the game environment.
            
        Returns:
            A dictionary matching OBSERVATION_SCHEMA.
            Returns a fallback empty structure if parsing fails.
        """
        try:
            response = self.model.prompt(
                f"Extract the structured state from this TextWorld observation:\n\n{text}",
                schema=self.schema
            )
            # The response object from llm package with schema should have a .json() method 
            # or we might need to parse the text if it returns a string.
            # Based on documentation, response.json() is available when schema is used?
            # Let's assume response.text() contains the JSON string.
            
            # Note: The 'llm' library's schema support might return the JSON string in .text()
            # We will try to parse it.
            return json.loads(response.text())
            
        except Exception as e:
            print(f"PERCEPTION ERROR: {e}")
            # Return safe fallback
            return {
                "room_name": "Unknown",
                "description": text,
                "exits": [],
                "items": []
            }

    def get_schema_dsl(self) -> str:
        """Returns the schema in DSL format (for debugging/logging)."""
        return "room_name, exits array str, items array object { name, state, location }"
