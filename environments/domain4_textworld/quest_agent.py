"""
Quest Agent - Minimal agent for TextWorld quest completion

Philosophy:
- TextWorld quests are sequential instructions, not exploration problems
- Decompose quest → Match actions → Track progress → Execute
- Keep it simple: ~200 lines vs 2500 for cognitive architecture
"""
import sys
from typing import List

# Add project root to path for imports
sys.path.insert(0, '/home/juancho/macgyver_mud')

from environments.domain4_textworld.quest_decomposer import QuestDecomposer
from environments.domain4_textworld.command_matcher import CommandMatcher


class QuestAgent:
    """
    Minimal agent for TextWorld quest execution.

    Architecture:
    1. Decompose quest into ordered action sequence
    2. For each step: match goal → admissible command
    3. Track progress → advance when step succeeds
    4. Loop prevention → try alternative if stuck
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize quest agent.

        Args:
            verbose: Print debug information
        """
        self.verbose = verbose

        # Components
        self.decomposer = QuestDecomposer()
        self.matcher = CommandMatcher()

        # Quest state
        self.steps = []               # List of action goals
        self.current_step = 0         # Which step we're on (0-indexed)

        # Execution state
        self.last_action = ""         # Last action taken
        self.action_count = 0         # Total actions taken
        self.same_action_count = 0    # Consecutive same actions
        self.last_obs = ""            # Last observation text

        if self.verbose:
            print("\n" + "=" * 70)
            print("🎯 QUEST AGENT INITIALIZED")
            print("=" * 70)
            print("Components:")
            print("  ✅ Quest Decomposer (parse quest → action sequence)")
            print("  ✅ Command Matcher (match goal → admissible command)")
            print("  ✅ Progress Tracker (advance on success)")
            print("  ✅ Loop Prevention (avoid getting stuck)")
            print("=" * 70 + "\n")

    def reset(self, quest: str):
        """
        Reset agent for new episode.

        Args:
            quest: Quest description from TextWorld
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print("🔄 EPISODE RESET")
            print("=" * 70)
            print(f"📝 Quest: {quest[:80]}{'...' if len(quest) > 80 else ''}")
            print()

        # Decompose quest
        self.steps = self.decomposer.decompose(quest)

        # Reset state
        self.current_step = 0
        self.last_action = ""
        self.action_count = 0
        self.same_action_count = 0
        self.last_obs = ""

        if self.verbose:
            print("📋 Quest decomposed into steps:")
            for i, step in enumerate(self.steps, 1):
                print(f"   {i}. {step}")
            print()
            print(f"✅ Ready to execute {len(self.steps)} steps")
            print("=" * 70 + "\n")

    def step(self, observation: str, reward: float, admissible_commands: List[str]) -> str:
        """
        Execute one step of the agent.

        Args:
            observation: Current observation text
            reward: Reward received from last action
            admissible_commands: List of valid commands

        Returns:
            Action to execute
        """
        self.action_count += 1

        if self.verbose:
            print(f"{'─' * 70}")
            print(f"STEP {self.action_count}")
            print(f"{'─' * 70}")

        # Check if we should advance to next step
        # Advance if: (1) we got reward, OR (2) observation changed significantly
        should_advance = False

        if reward > 0 and self.current_step < len(self.steps) - 1:
            should_advance = True
            if self.verbose:
                print(f"   ✅ Step completed! (reward: {reward:+.1f})")

        # Also check if observation changed (heuristic for progress without reward)
        elif self._observation_changed(observation) and self.current_step < len(self.steps) - 1:
            # Only advance if we've taken at least one action for current goal
            if self.action_count > self.current_step:
                should_advance = True
                if self.verbose:
                    print(f"   ✅ Step likely completed (observation changed)")

        if should_advance:
            self.current_step += 1
            self.same_action_count = 0  # Reset loop counter on progress

            if self.verbose:
                print(f"   Progress: {self.current_step}/{len(self.steps)}")

        # Check if quest is complete
        if self.current_step >= len(self.steps):
            if self.verbose:
                print(f"   🎉 Quest complete!")
            return "look"  # Safe fallback

        # Get current goal
        goal = self.steps[self.current_step]

        if self.verbose:
            print(f"   🎯 Current goal: {goal}")
            print(f"   📍 Step: {self.current_step + 1}/{len(self.steps)}")

        # Handle empty commands (shouldn't happen, but defensive)
        if not admissible_commands or len(admissible_commands) == 0:
            if self.verbose:
                print(f"   ⚠️  No admissible commands! Fallback to 'look'")
            return "look"

        # Match goal to command
        action = self.matcher.match(goal, admissible_commands)

        # Loop prevention: If same action repeating, try alternative
        if action == self.last_action:
            self.same_action_count += 1

            # After 3 repetitions, try something different
            if self.same_action_count >= 3:
                if self.verbose:
                    print(f"   ⚠️  Same action repeated {self.same_action_count} times")
                    print(f"      Trying alternative...")

                # Filter out the stuck action
                filtered_commands = [c for c in admissible_commands if c != action]

                if filtered_commands:
                    action = self.matcher.match(goal, filtered_commands)
                    self.same_action_count = 0  # Reset counter

                    if self.verbose:
                        print(f"      Alternative: {action}")
        else:
            self.same_action_count = 0

        # Track state
        self.last_action = action
        self.last_obs = observation

        if self.verbose:
            print(f"   ⚡ Action: {action}")
            print()

        return action

    def _observation_changed(self, observation: str) -> bool:
        """
        Check if observation changed significantly from last step.

        Uses simple text similarity heuristic.

        Args:
            observation: Current observation text

        Returns:
            True if observation changed significantly
        """
        if not self.last_obs:
            return False  # First step, nothing to compare

        # Tokenize observations
        prev_words = set(self.last_obs.lower().split())
        curr_words = set(observation.lower().split())

        if not prev_words or not curr_words:
            return False

        # Calculate similarity (Jaccard index)
        common = prev_words & curr_words
        total = prev_words | curr_words
        similarity = len(common) / len(total)

        # Changed if less than 60% similar
        return similarity < 0.6

    def get_progress(self) -> dict:
        """
        Get current progress information.

        Returns:
            Dict with progress metrics
        """
        return {
            'current_step': self.current_step,
            'total_steps': len(self.steps),
            'progress_ratio': self.current_step / len(self.steps) if self.steps else 0.0,
            'action_count': self.action_count,
            'current_goal': self.steps[self.current_step] if self.current_step < len(self.steps) else "Complete"
        }


if __name__ == "__main__":
    """Quick manual test with mock environment."""
    print("=" * 70)
    print("QUEST AGENT MANUAL TEST")
    print("=" * 70)

    agent = QuestAgent(verbose=True)

    # Test quest
    quest = "First, move east. Then, take the nest from the table. Finally, place the nest in the dresser."

    # Reset
    agent.reset(quest)

    # Simulate environment steps
    scenarios = [
        {
            'obs': "You are in a room. You see a table.",
            'reward': 0.0,
            'commands': ["go east", "go west", "examine table", "look"],
        },
        {
            'obs': "You moved east. You see a table with a nest on it.",
            'reward': 0.0,
            'commands': ["take nest of spiders from table", "examine nest", "go west"],
        },
        {
            'obs': "You took the nest.",
            'reward': 0.5,
            'commands': ["put nest on table", "insert nest into dresser", "examine nest"],
        },
        {
            'obs': "You placed the nest in the dresser.",
            'reward': 1.0,
            'commands': ["look", "inventory"],
        },
    ]

    print("\n" + "=" * 70)
    print("SIMULATED EPISODE")
    print("=" * 70)

    for i, scenario in enumerate(scenarios):
        action = agent.step(
            scenario['obs'],
            scenario['reward'],
            scenario['commands']
        )

        print(f"Environment response:")
        print(f"  Observation: {scenario['obs'][:60]}...")
        print(f"  Reward: {scenario['reward']:+.1f}")
        print()

    # Final progress
    progress = agent.get_progress()
    print("=" * 70)
    print("FINAL PROGRESS")
    print("=" * 70)
    print(f"Steps: {progress['current_step']}/{progress['total_steps']}")
    print(f"Progress: {progress['progress_ratio']:.0%}")
    print(f"Actions taken: {progress['action_count']}")
    print("=" * 70)
