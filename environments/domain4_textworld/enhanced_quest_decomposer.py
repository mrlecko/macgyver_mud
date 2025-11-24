"""
Enhanced LLM-Based Quest Decomposer for TextWorld

Uses LLM with few-shot examples to extract ONLY actionable steps from verbose quests.
Handles narrative fluff, meta-commentary, and complex natural language.
"""

import subprocess
import json
import re
from typing import List


class EnhancedQuestDecomposer:
    """
    LLM-based quest decomposer with few-shot prompting.
    
    Extracts actionable steps from TextWorld quests that often contain:
    - Narrative preamble ("Welcome to TextWorld!")
    - Meta-commentary ("Here is your task for today")
    - Politeness markers ("if it's not too much trouble")
    - Victory conditions ("and once you've done that, you win")
    """
    
    def __init__(self):
        """Initialize decomposer."""
        self.fallback_decomposer = None  # Keep regex fallback for emergencies
    
    def decompose(self, quest: str) -> List[str]:
        """
        Extract actionable steps from quest using LLM.
        
        Args:
            quest: Natural language quest description (may be verbose)
        
        Returns:
            List of actionable steps (cleaned, ordered)
        
        Example:
            >>> decomposer = EnhancedQuestDecomposer()
            >>> quest = "Welcome! Here's your task. First, go north. Then take the key."
            >>> decomposer.decompose(quest)
            ['go north', 'take key']
        """
        if not quest or not quest.strip():
            return []
        
        # Try LLM-based extraction
        try:
            steps = self._llm_decompose(quest)
            if steps:
                return steps
        except Exception as e:
            print(f"   ⚠️  LLM decomposition failed: {e}")
        
        # Fallback to regex-based (from original decomposer)
        return self._fallback_decompose(quest)
    
    def _llm_decompose(self, quest: str) -> List[str]:
        """
        Use LLM to extract actionable steps with few-shot prompting.
        """
        prompt = self._build_prompt(quest)
        
        # Call LLM via CLI (use default model)
        result = subprocess.run(
            ['llm', prompt],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"LLM call failed: {result.stderr}")
        
        # Parse JSON response
        response = result.stdout.strip()
        
        # Extract JSON from response (LLM might add explanation)
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            steps = json.loads(json_match.group(0))
        else:
            # Try parsing whole response
            steps = json.loads(response)
        
        # Validate and clean
        cleaned_steps = []
        for step in steps:
            if isinstance(step, str) and step.strip():
                # Light cleanup
                cleaned = step.strip().lower()
                cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
                cleaned_steps.append(cleaned)
        
        return cleaned_steps
    
    def _build_prompt(self, quest: str) -> str:
        """
        Build few-shot prompt with positive and negative examples.
        """
        prompt = f"""Extract ONLY the actionable steps from this TextWorld quest.

RULES:
1. Return ONLY physical actions the player must perform
2. EXCLUDE narrative preamble, greetings, and meta-commentary
3. EXCLUDE victory conditions and endings
4. EXCLUDE politeness markers and filler phrases
5. Return steps as a JSON array of strings
6. Steps should be simple commands (go, take, put, open, unlock, etc.)

POSITIVE EXAMPLES (what TO extract):

Example 1:
Quest: "Welcome to TextWorld! Here is your task. First, go north. Then, take the key from the table. Finally, unlock the door."
Output: ["go north", "take key from table", "unlock door"]

Example 2:
Quest: "Get ready to explore! Your mission today: move east, then retrieve the apple from the basket, and place it in the box. That's it!"
Output: ["move east", "retrieve apple from basket", "place apple in box"]

Example 3:
Quest: "Who's got time for games? You do! First off, if it's not too much trouble, head to the kitchen. After that, take the teapot from the bowl. And then, put the teapot in the refrigerator. Once you've done that, you win!"
Output: ["head to kitchen", "take teapot from bowl", "put teapot in refrigerator"]

NEGATIVE EXAMPLES (what NOT to extract):

Bad Output 1: ["get ready to explore", "that's it"]  # ❌ Meta-commentary
Bad Output 2: ["here is your task", "you win"]  # ❌ Not actions
Bad Output 3: ["welcome to textworld"]  # ❌ Greeting

NOW EXTRACT STEPS FROM THIS QUEST:

Quest: "{quest}"

Output (JSON array only):"""
        
        return prompt
    
    def _fallback_decompose(self, quest: str) -> List[str]:
        """
        Regex-based fallback (simple version of original decomposer).
        """
        # Normalize
        text = quest.lower().strip()
        
        # Remove common preamble
        text = re.sub(r'^.*(here is|here\'s) (your|the) (task|mission|objective)[^.!]*[.!]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^welcome[^.!]*[.!]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^who\'?s got[^.!]*[.!]\s*', '', text, flags=re.IGNORECASE)
        
        # Remove endings
        text = re.sub(r'\s*(and )?(once|when) you\'?ve done that[^.!]*[.!]\s*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*that\'?s (it|all)[^.!]*[.!]\s*$', '', text, flags=re.IGNORECASE)
        
        # Split on temporal markers and punctuation
        temporal_markers = r'\b(first|then|next|after that|finally|and then)\s*(,)?\s*'
        parts = re.split(temporal_markers, text, flags=re.IGNORECASE)
        
        # Clean parts
        steps = []
        for part in parts:
            if not part or part.strip() in ['first', 'then', 'next', 'after that', 'finally', 'and then', ',']:
                continue
            
            # Clean
            clean = part.strip(' ,.!?')
            clean = re.sub(r'^(if it\'?s not too much trouble,?\s*)', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'^(you (should|need to|can|could)\s*)', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'\s+', ' ', clean)
            
            if clean and len(clean) > 3:  # Min length filter
                steps.append(clean)
        
        return steps[:10]  # Max 10 steps


# Quick test
if __name__ == "__main__":
    decomposer = EnhancedQuestDecomposer()
    
    # Test with problematic quest from benchmark
    quest1 = """Get ready to pick stuff up and put it in places, because you've just entered TextWorld! Here is your task for today. First off, if it's not too much trouble, I need you to make an effort to take a trip north. Then, go to the east. After that, retrieve the teapot from the bowl in the cookhouse. And then, deposit the teapot into the refrigerator in the cookhouse. And once you've done that, you win!"""
    
    print("Test Quest 1:")
    print(f"  Original: {quest1[:80]}...")
    steps1 = decomposer.decompose(quest1)
    print(f"  Steps ({len(steps1)}):")
    for i, step in enumerate(steps1, 1):
        print(f"    {i}. {step}")
    print()
    
    # Test with simple quest
    quest2 = "First, go north. Then, take the key. Finally, unlock the door."
    print("Test Quest 2:")
    print(f"  Original: {quest2}")
    steps2 = decomposer.decompose(quest2)
    print(f"  Steps: {steps2}")
