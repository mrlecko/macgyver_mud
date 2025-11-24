#!/usr/bin/env python3
"""
Test suite for CommandMatcher (TDD approach)

Tests action goal to command matching logic.
"""
import sys
import pytest

sys.path.insert(0, '/home/juancho/macgyver_mud')


class TestCommandMatcher:
    """Test suite for command matching logic."""

    def setup_method(self):
        """Setup runs before each test."""
        from environments.domain4_textworld.command_matcher import CommandMatcher
        self.matcher = CommandMatcher()

    def test_exact_match(self):
        """Test exact string match."""
        goal = "go east"
        commands = ["go east", "go west", "go north", "look"]

        result = self.matcher.match(goal, commands)

        assert result == "go east"

    def test_partial_token_match(self):
        """Test matching with partial token overlap."""
        goal = "take key"
        commands = ["take golden key", "examine key", "drop key", "look"]

        result = self.matcher.match(goal, commands)

        # Should prefer "take golden key" (both tokens match)
        assert result == "take golden key"

    def test_best_overlap_wins(self):
        """Test that highest token overlap wins."""
        goal = "unlock door with key"
        commands = [
            "unlock door with golden key",  # 4/4 tokens match
            "unlock door",                   # 2/4 tokens match
            "examine door",                  # 1/4 tokens match
            "look"                          # 0/4 tokens match
        ]

        result = self.matcher.match(goal, commands)

        assert result == "unlock door with golden key"

    def test_verb_object_matching(self):
        """Test matching action verb + object."""
        goal = "examine painting"
        commands = ["examine painting on wall", "take painting", "look at wall", "go north"]

        result = self.matcher.match(goal, commands)

        # Should match "examine painting on wall" (both tokens)
        assert result == "examine painting on wall"

    def test_synonym_handling_via_tokens(self):
        """Test that token overlap handles minor variations."""
        goal = "pick up key"
        commands = ["take key", "get key", "examine key", "drop key"]

        result = self.matcher.match(goal, commands)

        # Won't match verb synonym, but should match "key" token
        assert "key" in result

    def test_object_specificity_matters(self):
        """Test matching specific vs generic object names."""
        goal = "take golden key"
        commands = ["take golden key", "take rusty key", "take chest", "look"]

        result = self.matcher.match(goal, commands)

        # Should prefer "take golden key" (all tokens match)
        assert result == "take golden key"

    def test_fallback_to_first_command(self):
        """Test fallback when no good match exists."""
        goal = "fly to the moon"
        commands = ["go north", "go south", "look", "inventory"]

        result = self.matcher.match(goal, commands)

        # Should return some valid command (likely first)
        assert result in commands

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        goal = "TAKE KEY"
        commands = ["take golden key", "examine key", "look"]

        result = self.matcher.match(goal, commands)

        assert result == "take golden key"

    def test_empty_commands_list(self):
        """Test edge case: empty command list."""
        goal = "take key"
        commands = []

        result = self.matcher.match(goal, commands)

        # Should return safe fallback
        assert result == "look"

    def test_preposition_handling(self):
        """Test matching with prepositions (from, into, on, etc)."""
        goal = "take nest from table"
        commands = ["take nest of spiders from table", "put nest on table", "examine table"]

        result = self.matcher.match(goal, commands)

        # Best overlap should be "take nest of spiders from table"
        assert result == "take nest of spiders from table"

    def test_preference_for_action_verb(self):
        """Test that action verb is weighted in matching."""
        goal = "unlock door"
        commands = ["unlock door with key", "examine door", "go through door"]

        result = self.matcher.match(goal, commands)

        # Should prefer "unlock door with key" (verb + object match)
        assert result == "unlock door with key"

    def test_multi_word_objects(self):
        """Test objects with multiple words."""
        goal = "examine dusty tome"
        commands = [
            "examine dusty tome on shelf",
            "examine tome",
            "take dusty tome",
            "look"
        ]

        result = self.matcher.match(goal, commands)

        # "examine dusty tome on shelf" has all tokens
        assert result == "examine dusty tome on shelf"

    def test_directional_commands(self):
        """Test direction matching."""
        goal = "move east"
        commands = ["go east", "go west", "examine compass", "look"]

        result = self.matcher.match(goal, commands)

        # "go east" matches "east" token
        assert result == "go east"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
