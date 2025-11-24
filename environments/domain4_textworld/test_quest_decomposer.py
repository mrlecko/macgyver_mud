#!/usr/bin/env python3
"""
Test suite for QuestDecomposer (TDD approach)

Tests quest parsing and temporal logic extraction.
"""
import sys
import pytest

# Add project root to path
sys.path.insert(0, '/home/juancho/macgyver_mud')


class TestQuestDecomposer:
    """Test suite for quest decomposition logic."""

    def setup_method(self):
        """Setup runs before each test."""
        from environments.domain4_textworld.quest_decomposer import QuestDecomposer
        self.decomposer = QuestDecomposer()

    def test_simple_quest_with_first_then_finally(self):
        """Test basic temporal markers: first, then, finally."""
        quest = "First, move east. Then, take the key. Finally, unlock the door."

        steps = self.decomposer.decompose(quest)

        assert len(steps) == 3
        assert "east" in steps[0].lower()
        assert "key" in steps[1].lower()
        assert "unlock" in steps[2].lower()
        assert "door" in steps[2].lower()

    def test_quest_with_and_then_markers(self):
        """Test 'and then' as temporal marker."""
        quest = "Go north and then examine the painting and then take the key."

        steps = self.decomposer.decompose(quest)

        assert len(steps) == 3
        assert "north" in steps[0].lower()
        assert "examine" in steps[1].lower() or "painting" in steps[1].lower()
        assert "key" in steps[2].lower()

    def test_textworld_typical_quest(self):
        """Test actual TextWorld quest format."""
        quest = (
            "Who's got a virtual machine and is about to play through an fast paced "
            "round of TextWorld? You do! Here is your task for today. First, it would "
            "be fantastic if you could move east. And then, recover the nest of spiders "
            "from the table within the restroom. With the nest of spiders, you can place "
            "the nest of spiders inside the dresser. That's it!"
        )

        steps = self.decomposer.decompose(quest)

        # Should extract 3 core actions
        assert len(steps) >= 3

        # Check key actions are present
        steps_text = ' '.join(steps).lower()
        assert "east" in steps_text
        assert "nest" in steps_text or "recover" in steps_text
        assert "dresser" in steps_text or "place" in steps_text

    def test_quest_without_temporal_markers(self):
        """Test quest with implicit sequence (commas/periods)."""
        quest = "Take the key. Unlock the door. Go north."

        steps = self.decomposer.decompose(quest)

        assert len(steps) == 3
        assert "key" in steps[0].lower()
        assert "unlock" in steps[1].lower()
        assert "north" in steps[2].lower()

    def test_quest_with_filler_words(self):
        """Test removal of filler phrases."""
        quest = "First, you should move east. Then it would be good if you could take the key."

        steps = self.decomposer.decompose(quest)

        assert len(steps) == 2
        # Filler words should be removed
        assert "you should" not in steps[0].lower()
        assert "it would be good" not in steps[1].lower()
        # Core actions remain
        assert "east" in steps[0].lower()
        assert "key" in steps[1].lower()

    def test_empty_quest(self):
        """Test edge case: empty quest."""
        quest = ""

        steps = self.decomposer.decompose(quest)

        assert isinstance(steps, list)
        assert len(steps) == 0

    def test_single_action_quest(self):
        """Test quest with only one action."""
        quest = "Take the golden key from the table."

        steps = self.decomposer.decompose(quest)

        assert len(steps) == 1
        assert "key" in steps[0].lower()
        assert "table" in steps[0].lower()

    def test_quest_preserves_object_details(self):
        """Test that specific object names are preserved."""
        quest = "First, take the golden key. Then, unlock the ornate chest."

        steps = self.decomposer.decompose(quest)

        assert "golden key" in steps[0].lower() or ("golden" in steps[0].lower() and "key" in steps[0].lower())
        assert "ornate chest" in steps[1].lower() or ("ornate" in steps[1].lower() and "chest" in steps[1].lower())

    def test_quest_with_complex_actions(self):
        """Test quest with multi-word action verbs."""
        quest = "First, pick up the key. Then, put the key into the lock. Finally, turn the key."

        steps = self.decomposer.decompose(quest)

        assert len(steps) == 3
        assert any("pick" in s.lower() or "up" in s.lower() for s in [steps[0]])
        assert "key" in steps[1].lower() and "lock" in steps[1].lower()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
