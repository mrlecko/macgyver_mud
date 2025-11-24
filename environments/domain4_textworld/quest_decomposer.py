"""
Quest Decomposer - Parse TextWorld quests into action sequences

Philosophy:
- TextWorld quests are natural language instructions with temporal logic
- Extract sequential actions: "First X, then Y, finally Z" → ["X", "Y", "Z"]
- Keep it simple: regex-based parsing with cleanup heuristics
"""
import re
from typing import List


class QuestDecomposer:
    """
    Decompose TextWorld quests into ordered action sequences.

    Uses pattern matching to identify temporal markers and split quest
    into discrete action steps.
    """

    def __init__(self):
        """Initialize decomposer with regex patterns."""
        # Temporal markers that indicate sequence
        self.temporal_markers = [
            r'\bfirst\b',
            r'\bthen\b',
            r'\bafter that\b',
            r'\bfinally\b',
            r'\bnext\b',
            r'\band then\b',
            r'\bafter which\b',
            r'\bsubsequently\b'
        ]

        # Filler phrases to remove
        self.filler_phrases = [
            r'\byou should\b',
            r'\byou need to\b',
            r'\byou can\b',
            r'\byou could\b',
            r'\bit would be (good|great|fantastic|nice) if (you )?(could|would|can)\b',
            r'\bplease\b',
            r'\bkindly\b',
            r'^\s*if\s+',  # Leading "if"
        ]

    def decompose(self, quest: str) -> List[str]:
        """
        Break quest into ordered action sequence.

        Args:
            quest: Natural language quest description

        Returns:
            List of action goals (ordered)

        Examples:
            >>> decomposer = QuestDecomposer()
            >>> decomposer.decompose("First, go east. Then, take key.")
            ['go east', 'take key']
        """
        if not quest or not quest.strip():
            return []

        # Step 1: Normalize quest text
        normalized = self._normalize_text(quest)

        # Step 2: Split on temporal markers
        steps = self._split_on_temporal_markers(normalized)

        # Step 3: Split on punctuation (fallback for implicit sequence)
        if len(steps) <= 1:
            steps = self._split_on_punctuation(normalized)

        # Step 4: Clean up each step
        cleaned_steps = []
        for step in steps:
            # Clean might return multiple steps (if sentence has multiple actions)
            cleaned_list = self._clean_step(step)
            for cleaned in cleaned_list:
                if cleaned:
                    cleaned_steps.append(cleaned)

        # Step 5: Filter out meta-commentary
        filtered_steps = self._filter_meta_commentary(cleaned_steps)

        return filtered_steps

    def _normalize_text(self, text: str) -> str:
        """
        Normalize quest text for parsing.

        - Convert to lowercase
        - Remove extra whitespace
        - Normalize punctuation
        """
        # Lowercase for consistent matching
        text = text.lower()

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Ensure punctuation has space after
        text = re.sub(r'([.!?])([a-z])', r'\1 \2', text)

        return text.strip()

    def _split_on_temporal_markers(self, text: str) -> List[str]:
        """
        Split text on temporal markers (first, then, finally, etc).

        Returns:
            List of text chunks
        """
        # Build regex pattern that matches any temporal marker
        pattern = '|'.join(self.temporal_markers)

        # Split on temporal markers
        chunks = re.split(f'({pattern})', text, flags=re.IGNORECASE)

        # Combine marker with following text
        # Input: ['', 'first', ' go east. ', 'then', ' take key.']
        # Output: ['first go east', 'then take key']
        combined = []
        i = 0
        while i < len(chunks):
            chunk = chunks[i].strip()
            if not chunk:
                i += 1
                continue

            # Check if this is a temporal marker
            is_marker = any(re.match(f'^{marker}$', chunk, re.IGNORECASE)
                          for marker in self.temporal_markers)

            if is_marker and i + 1 < len(chunks):
                # Combine marker with next chunk
                combined.append(chunk + ' ' + chunks[i + 1].strip())
                i += 2
            else:
                combined.append(chunk)
                i += 1

        # Remove temporal markers from start of each chunk
        cleaned = []
        for chunk in combined:
            for marker in self.temporal_markers:
                chunk = re.sub(f'^{marker}\\s*', '', chunk, flags=re.IGNORECASE)
            chunk = chunk.strip(' ,.')
            if chunk:
                cleaned.append(chunk)

        return cleaned

    def _split_on_punctuation(self, text: str) -> List[str]:
        """
        Split text on sentence boundaries (periods, exclamation marks).

        Fallback for quests without explicit temporal markers.
        """
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!]+\s+', text)

        # Filter out empty sentences
        filtered = [s.strip() for s in sentences if s.strip()]

        return filtered

    def _clean_step(self, step: str) -> List[str]:
        """
        Clean individual step text.

        - Remove filler phrases
        - Remove leading/trailing punctuation
        - Strip whitespace
        - May return multiple steps if one sentence contains multiple actions

        Returns:
            List of cleaned action strings
        """
        result = []

        # Split on period if multiple sentences in one step
        # This handles "...table. With the nest, place..." → separate steps
        if '.' in step:
            parts = step.split('.')
            for part in parts:
                part = part.strip()
                if part:
                    cleaned = self._clean_single_step(part)
                    if cleaned:
                        result.append(cleaned)
        else:
            cleaned = self._clean_single_step(step)
            if cleaned:
                result.append(cleaned)

        return result

    def _clean_single_step(self, step: str) -> str:
        """Clean a single step string."""
        # Remove filler phrases
        for pattern in self.filler_phrases:
            step = re.sub(pattern, '', step, flags=re.IGNORECASE)

        # Additional aggressive cleanup for common patterns
        step = re.sub(r'^it would be \w+ if ', '', step, flags=re.IGNORECASE)
        step = re.sub(r'^you (could|can|should|would) ', '', step, flags=re.IGNORECASE)
        step = re.sub(r'^with (the |a )?[^,]+,\s*', '', step, flags=re.IGNORECASE)  # "With the nest of spiders, ..."

        # Remove leading/trailing punctuation and whitespace
        step = step.strip(' ,.!?;:')

        # Normalize internal whitespace
        step = re.sub(r'\s+', ' ', step)

        return step

    def _filter_meta_commentary(self, steps: List[str]) -> List[str]:
        """
        Filter out meta-commentary that isn't an action.

        Examples of meta-commentary:
        - "here is your task for today"
        - "that's it"
        - "you do"
        - "who's got a virtual machine"
        """
        meta_patterns = [
            r"^here (is|are) (your|the) (task|mission|objective)",
            r"^that'?s (it|all|everything)",
            r"^(you do|you've got|you have)",
            r"^who'?s got",
            r"^about to play",
            r"^with the .+, you can",  # "With the key, you can unlock..." (this describes consequence, not action)
        ]

        filtered = []
        for step in steps:
            # Check if step matches any meta pattern
            is_meta = any(re.search(pattern, step, re.IGNORECASE) for pattern in meta_patterns)

            if not is_meta:
                # Additional heuristic: Steps should typically have a verb
                # But don't filter too aggressively
                filtered.append(step)

        return filtered


if __name__ == "__main__":
    """Quick manual test."""
    decomposer = QuestDecomposer()

    # Test 1: Simple quest
    print("Test 1: Simple quest")
    quest1 = "First, move east. Then, take the key. Finally, unlock the door."
    steps1 = decomposer.decompose(quest1)
    print(f"  Quest: {quest1}")
    print(f"  Steps: {steps1}")
    print()

    # Test 2: TextWorld typical format
    print("Test 2: TextWorld typical format")
    quest2 = (
        "Who's got a virtual machine and is about to play through an fast paced "
        "round of TextWorld? You do! Here is your task for today. First, it would "
        "be fantastic if you could move east. And then, recover the nest of spiders "
        "from the table within the restroom. With the nest of spiders, you can place "
        "the nest of spiders inside the dresser. That's it!"
    )
    steps2 = decomposer.decompose(quest2)
    print(f"  Quest: {quest2[:80]}...")
    print(f"  Steps:")
    for i, step in enumerate(steps2, 1):
        print(f"    {i}. {step}")
    print()

    # Test 3: No temporal markers
    print("Test 3: No temporal markers (punctuation-based)")
    quest3 = "Take the key. Unlock the door. Go north."
    steps3 = decomposer.decompose(quest3)
    print(f"  Quest: {quest3}")
    print(f"  Steps: {steps3}")
    print()

    # Test 4: Empty quest
    print("Test 4: Edge case (empty)")
    quest4 = ""
    steps4 = decomposer.decompose(quest4)
    print(f"  Quest: '{quest4}'")
    print(f"  Steps: {steps4}")
