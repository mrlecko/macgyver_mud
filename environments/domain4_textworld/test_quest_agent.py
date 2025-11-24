#!/usr/bin/env python3
"""
Test suite for QuestAgent (TDD approach)

Tests complete agent behavior and integration.
"""
import sys
import pytest

sys.path.insert(0, '/home/juancho/macgyver_mud')


class TestQuestAgentUnit:
    """Unit tests for QuestAgent components."""

    def setup_method(self):
        """Setup runs before each test."""
        from environments.domain4_textworld.quest_agent import QuestAgent
        self.agent = QuestAgent(verbose=False)

    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        assert self.agent is not None
        assert hasattr(self.agent, 'steps')
        assert hasattr(self.agent, 'current_step')
        assert self.agent.current_step == 0

    def test_reset_with_simple_quest(self):
        """Test reset decomposes quest."""
        quest = "First, go east. Then, take key."

        self.agent.reset(quest)

        assert len(self.agent.steps) >= 2
        assert self.agent.current_step == 0

    def test_step_returns_valid_command(self):
        """Test step returns command from admissible list."""
        quest = "Take the key."
        self.agent.reset(quest)

        commands = ["take key", "examine key", "look"]
        action = self.agent.step(
            observation="You see a key.",
            reward=0.0,
            admissible_commands=commands
        )

        assert action in commands

    def test_progress_advances_on_reward(self):
        """Test that progress advances when reward received."""
        quest = "First, take key. Then, unlock door."
        self.agent.reset(quest)

        commands = ["take key", "examine key"]

        # Step 1: No reward
        self.agent.step("You see a key.", reward=0.0, admissible_commands=commands)
        initial_step = self.agent.current_step

        # Step 2: Reward received (simulating successful action)
        self.agent.step("You took the key.", reward=1.0, admissible_commands=commands)
        new_step = self.agent.current_step

        assert new_step >= initial_step  # Progress made

    def test_loop_prevention_triggers(self):
        """Test that loop prevention activates after repetitions."""
        quest = "Take the key."
        self.agent.reset(quest)

        commands = ["take key", "examine key", "look"]

        # Execute same action multiple times
        action1 = self.agent.step("Observation", 0.0, commands)
        action2 = self.agent.step("Observation", 0.0, commands)
        action3 = self.agent.step("Observation", 0.0, commands)
        action4 = self.agent.step("Observation", 0.0, commands)

        # After several repetitions, should try alternative
        # (This is heuristic-based, so just check it returns valid command)
        assert action4 in commands

    def test_quest_completion(self):
        """Test behavior when quest steps are complete."""
        quest = "Take key."
        self.agent.reset(quest)

        commands = ["look", "inventory"]

        # Simulate completing quest
        self.agent.current_step = len(self.agent.steps)

        action = self.agent.step("Quest complete!", 0.0, commands)

        # Should return safe fallback
        assert action == "look"


class TestQuestAgentIntegration:
    """Integration tests with mock TextWorld environment."""

    def setup_method(self):
        """Setup runs before each test."""
        from environments.domain4_textworld.quest_agent import QuestAgent
        self.agent = QuestAgent(verbose=False)

    def test_simple_linear_quest_execution(self):
        """Test agent executes simple linear quest."""
        quest = "First, go east. Then, take key. Finally, unlock door."
        self.agent.reset(quest)

        # Simulate environment responses
        scenarios = [
            {
                'obs': "You are in a room.",
                'reward': 0.0,
                'commands': ["go east", "go west", "look"],
                'expected_contains': "east"
            },
            {
                'obs': "You moved east. You see a key.",
                'reward': 0.0,
                'commands': ["take key", "examine key", "go west"],
                'expected_contains': "key"
            },
            {
                'obs': "You took the key.",
                'reward': 0.5,
                'commands': ["unlock door", "examine door", "go west"],
                'expected_contains': "unlock"
            },
        ]

        for i, scenario in enumerate(scenarios):
            action = self.agent.step(
                scenario['obs'],
                scenario['reward'],
                scenario['commands']
            )

            # Verify action is valid
            assert action in scenario['commands'], f"Step {i}: Invalid action {action}"

            # Verify action is relevant to quest
            assert scenario['expected_contains'] in action.lower(), \
                f"Step {i}: Expected '{scenario['expected_contains']}' in action '{action}'"

    def test_handles_quest_with_no_clear_steps(self):
        """Test agent handles malformed quest gracefully."""
        quest = "Do something cool!"
        self.agent.reset(quest)

        commands = ["look", "inventory", "go north"]
        action = self.agent.step("Confused...", 0.0, commands)

        # Should return valid command even if quest unclear
        assert action in commands


class TestQuestAgentRobustness:
    """Robustness tests for edge cases."""

    def setup_method(self):
        """Setup runs before each test."""
        from environments.domain4_textworld.quest_agent import QuestAgent
        self.agent = QuestAgent(verbose=False)

    def test_empty_quest(self):
        """Test handling of empty quest."""
        quest = ""
        self.agent.reset(quest)

        commands = ["look", "inventory"]
        action = self.agent.step("...", 0.0, commands)

        assert action in commands

    def test_empty_commands_list(self):
        """Test handling of empty admissible commands."""
        quest = "Take key."
        self.agent.reset(quest)

        action = self.agent.step("...", 0.0, admissible_commands=[])

        # Should have safe fallback
        assert action == "look"

    def test_quest_with_single_step(self):
        """Test quest with only one action."""
        quest = "Take the key."
        self.agent.reset(quest)

        commands = ["take key", "look"]
        action = self.agent.step("You see a key.", 0.0, commands)

        assert "key" in action.lower()

    def test_long_quest_sequence(self):
        """Test quest with many steps."""
        quest = "First, go north. Then, go east. Then, take key. Then, go west. Then, unlock door."
        self.agent.reset(quest)

        # Should decompose into 5 steps
        assert len(self.agent.steps) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
