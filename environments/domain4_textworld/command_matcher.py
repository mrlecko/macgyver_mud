"""
Command Matcher - Match action goals to admissible commands

Philosophy:
- Action goal is what we WANT to do: "take key"
- Admissible command is what we CAN do: "take golden key from table"
- Match using token overlap: more tokens in common = better match
"""
from typing import List, Tuple


class CommandMatcher:
    """
    Match action goals to admissible commands using token overlap.

    Uses simple but effective heuristic: count how many goal tokens
    appear in each command, pick command with highest overlap.
    """

    def __init__(self):
        """Initialize matcher."""
        # Stop words to ignore in matching (very common words)
        self.stop_words = {'the', 'a', 'an', 'from', 'to', 'in', 'on', 'at', 'with'}

    def match(self, goal: str, commands: List[str]) -> str:
        """
        Find command that best matches goal.

        Args:
            goal: Action goal (e.g., "take key")
            commands: List of admissible commands

        Returns:
            Best matching command

        Examples:
            >>> matcher = CommandMatcher()
            >>> matcher.match("take key", ["take golden key", "examine key"])
            'take golden key'
        """
        # Edge case: no commands available
        if not commands or len(commands) == 0:
            return "look"  # Safe fallback

        # Edge case: empty goal
        if not goal or not goal.strip():
            return commands[0]  # Return first command

        # Tokenize goal (remove stop words for better matching)
        goal_tokens = self._tokenize(goal, remove_stop_words=False)

        # Score each command
        scored_commands = []
        for cmd in commands:
            score = self._score_command(goal_tokens, cmd)
            scored_commands.append((score, cmd))

        # Sort by score (descending)
        scored_commands.sort(reverse=True, key=lambda x: x[0])

        # Return best match
        return scored_commands[0][1]

    def _tokenize(self, text: str, remove_stop_words: bool = False) -> set:
        """
        Tokenize text into lowercase words.

        Args:
            text: Text to tokenize
            remove_stop_words: Whether to filter out stop words

        Returns:
            Set of tokens
        """
        # Lowercase and split on whitespace
        tokens = text.lower().split()

        # Optionally remove stop words
        if remove_stop_words:
            tokens = [t for t in tokens if t not in self.stop_words]

        return set(tokens)

    def _score_command(self, goal_tokens: set, command: str) -> float:
        """
        Score how well command matches goal tokens.

        Scoring:
        - Base score: (tokens in common) / (goal tokens)
        - Bonus: +0.5 if first token matches (action verb bonus)

        Args:
            goal_tokens: Set of goal tokens
            command: Command string to score

        Returns:
            Match score (higher = better)
        """
        if not goal_tokens:
            return 0.0

        # Tokenize command
        cmd_tokens = self._tokenize(command, remove_stop_words=False)

        # Count overlapping tokens
        overlap = goal_tokens & cmd_tokens
        overlap_count = len(overlap)

        # Base score: overlap ratio
        base_score = overlap_count / len(goal_tokens)

        # Bonus: First token match (action verb is usually first)
        # This helps prefer "take key" over "examine key" when goal is "take"
        first_goal_token = list(goal_tokens)[0] if goal_tokens else ""
        first_cmd_token = command.lower().split()[0] if command else ""

        verb_bonus = 0.5 if first_goal_token == first_cmd_token else 0.0

        return base_score + verb_bonus


if __name__ == "__main__":
    """Quick manual tests."""
    matcher = CommandMatcher()

    print("=" * 70)
    print("COMMAND MATCHER TESTS")
    print("=" * 70)

    # Test 1: Exact match
    print("\nTest 1: Exact match")
    goal1 = "go east"
    commands1 = ["go east", "go west", "look"]
    result1 = matcher.match(goal1, commands1)
    print(f"  Goal: {goal1}")
    print(f"  Commands: {commands1}")
    print(f"  Match: {result1}")
    assert result1 == "go east"

    # Test 2: Partial match
    print("\nTest 2: Partial token match")
    goal2 = "take key"
    commands2 = ["take golden key", "examine key", "look"]
    result2 = matcher.match(goal2, commands2)
    print(f"  Goal: {goal2}")
    print(f"  Commands: {commands2}")
    print(f"  Match: {result2}")
    assert result2 == "take golden key"

    # Test 3: Best overlap wins
    print("\nTest 3: Best overlap")
    goal3 = "unlock door with key"
    commands3 = ["unlock door with golden key", "unlock door", "examine door"]
    result3 = matcher.match(goal3, commands3)
    print(f"  Goal: {goal3}")
    print(f"  Commands: {commands3}")
    print(f"  Match: {result3}")
    assert result3 == "unlock door with golden key"

    # Test 4: Empty commands
    print("\nTest 4: Empty commands (fallback)")
    goal4 = "take key"
    commands4 = []
    result4 = matcher.match(goal4, commands4)
    print(f"  Goal: {goal4}")
    print(f"  Commands: {commands4}")
    print(f"  Match: {result4}")
    assert result4 == "look"

    # Test 5: Verb preference
    print("\nTest 5: Verb preference (first token match)")
    goal5 = "examine painting"
    commands5 = ["examine painting on wall", "take painting", "look"]
    result5 = matcher.match(goal5, commands5)
    print(f"  Goal: {goal5}")
    print(f"  Commands: {commands5}")
    print(f"  Match: {result5}")
    # Should prefer "examine" over "take" due to verb bonus
    assert result5 == "examine painting on wall"

    print("\n" + "=" * 70)
    print("✅ All manual tests passed!")
    print("=" * 70)
