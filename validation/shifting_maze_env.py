"""
Shifting Maze Environment - Hubris Validation Scenario

This environment implements "The Turkey Problem":
- Phase 1 (steps 1-8): A consistent, rewarding path exists (A → B → C → GOAL)
- Phase 2 (steps 9+): The environment silently shifts, making the old path dangerous
- A new path becomes available, but requires exploration to discover

This tests whether the Hubris protocol can detect overconfidence and prevent
catastrophic failure when the environment changes unexpectedly.
"""

class ShiftingMazeEnv:
    """
    A discrete maze environment that shifts its reward structure mid-episode.

    States: A, B, C, D, GOAL, TRAP
    Actions: move_to_X (where X is an adjacent state)

    Phase 1 (steps 1-8):
        A → B: +1.0 (safe)
        B → C: +1.0 (safe)
        C → GOAL: +10.0 (success)

    Phase 2 (steps 9+):
        A → B: +0.5 (subtle warning - reduced reward)
        B → C: leads to TRAP (-10.0, episode ends)
        A → D: +1.0 (new safe path)
        D → GOAL: +10.0 (success)
    """

    def __init__(self, phase_shift_step=9):
        """
        Args:
            phase_shift_step: Step number when environment shifts (default: 9)
        """
        self.state = "A"
        self.global_step_count = 0  # Total steps across all episodes
        self.episode_step_count = 0  # Steps within current episode
        self.phase_shift_step = phase_shift_step
        self.done = False
        self.episode_reward = 0.0
        self.total_reward = 0.0

        # Track state transitions for debugging
        self.history = []

    def reset(self):
        """Reset environment to initial state (new episode, keeps global step count)."""
        self.state = "A"
        self.episode_step_count = 0
        self.done = False
        self.episode_reward = 0.0
        # DON'T reset global_step_count - it tracks across episodes!
        return self.state

    def hard_reset(self):
        """Complete reset including global step count."""
        self.state = "A"
        self.global_step_count = 0
        self.episode_step_count = 0
        self.done = False
        self.episode_reward = 0.0
        self.total_reward = 0.0
        self.history = []
        return self.state

    def get_available_actions(self):
        """
        Get available actions from current state.

        Returns:
            List of action names (strings)
        """
        if self.done:
            return []

        if self.state == "A":
            if self.global_step_count < self.phase_shift_step - 3:
                return ["move_to_B"]
            else:
                # After shift (or shortly before), new path opens
                return ["move_to_B", "move_to_D"]

        elif self.state == "B":
            return ["move_to_C"]

        elif self.state == "C":
            if self.global_step_count < self.phase_shift_step:
                return ["move_to_GOAL"]
            else:
                # After shift, C leads to trap
                return ["move_to_TRAP"]

        elif self.state == "D":
            return ["move_to_GOAL"]

        elif self.state == "GOAL" or self.state == "TRAP":
            return []

        return []

    def step(self, action):
        """
        Execute action and return result.

        Args:
            action: Action name (string)

        Returns:
            tuple: (next_state, reward, done, info)
        """
        if self.done:
            return self.state, 0.0, True, {"error": "Episode already finished", "total_reward": self.total_reward}

        self.global_step_count += 1
        self.episode_step_count += 1
        reward = 0.0
        prev_state = self.state
        info = {
            "global_step": self.global_step_count,
            "episode_step": self.episode_step_count,
            "phase": "Phase 1" if self.global_step_count < self.phase_shift_step else "Phase 2",
            "prev_state": prev_state
        }

        # Phase 1: Normal path
        if self.global_step_count < self.phase_shift_step:
            if action == "move_to_B" and self.state == "A":
                self.state = "B"
                reward = 1.0
            elif action == "move_to_C" and self.state == "B":
                self.state = "C"
                reward = 1.0
            elif action == "move_to_GOAL" and self.state == "C":
                self.state = "GOAL"
                reward = 10.0
                # Don't set done yet, just mark success
                info["success"] = "Reached goal via old path"
            else:
                reward = -1.0  # Invalid action
                info["error"] = f"Invalid action {action} from {self.state}"

        # Phase 2: Shifted environment
        else:
            if action == "move_to_B" and self.state == "A":
                self.state = "B"
                reward = 0.5  # Reduced reward (subtle warning)
                info["warning"] = "Reward decreased - environment may have changed"

            elif action == "move_to_D" and self.state == "A":
                self.state = "D"
                reward = 1.0
                info["discovery"] = "New path discovered!"

            elif action == "move_to_C" and self.state == "B":
                # This now leads to trap!
                self.state = "TRAP"
                reward = -10.0
                self.done = True
                info["trap"] = "Catastrophic failure - followed outdated path"

            elif action == "move_to_GOAL" and self.state == "D":
                self.state = "GOAL"
                reward = 10.0
                info["success"] = "Found new safe path to goal"

            elif action == "move_to_TRAP" and self.state == "C":
                self.state = "TRAP"
                reward = -10.0
                self.done = True
                info["trap"] = "Caught in trap after phase shift"

            else:
                reward = -1.0
                info["error"] = f"Invalid action {action} from {self.state}"

        self.episode_reward += reward
        self.total_reward += reward
        self.history.append({
            "global_step": self.global_step_count,
            "action": action,
            "reward": reward,
            "state": self.state
        })

        info["episode_reward"] = self.episode_reward
        info["total_reward"] = self.total_reward

        # Check if we reached a terminal state (GOAL or TRAP)
        if self.state in ["GOAL", "TRAP"]:
            # Mark as terminal but don't auto-reset
            info["terminal"] = True
            # Return the terminal state itself
            return self.state, reward, True, info

        return self.state, reward, self.done, info

    def get_state_info(self):
        """Get current environment state information."""
        return {
            "current_state": self.state,
            "global_step_count": self.global_step_count,
            "episode_step_count": self.episode_step_count,
            "phase": "Phase 1" if self.global_step_count < self.phase_shift_step else "Phase 2",
            "done": self.done,
            "episode_reward": self.episode_reward,
            "total_reward": self.total_reward,
            "available_actions": self.get_available_actions()
        }


if __name__ == "__main__":
    # Quick test
    print("=== Shifting Maze Environment Test ===\n")

    env = ShiftingMazeEnv(phase_shift_step=9)

    # Phase 1: Normal path
    print("Phase 1: Learning the golden path (steps 1-8)")
    for episode in range(2):
        state = env.reset()
        print(f"\nEpisode {episode+1}:")
        state, reward, done, info = env.step("move_to_B")
        print(f"  Global step {info['global_step']}: A → {state} (reward: {reward:+.1f})")
        state, reward, done, info = env.step("move_to_C")
        print(f"  Global step {info['global_step']}: B → {state} (reward: {reward:+.1f})")
        state, reward, done, info = env.step("move_to_GOAL")
        print(f"  Global step {info['global_step']}: C → {state} (reward: {reward:+.1f}, episode total: {info['episode_reward']:+.1f})")

    # Phase 2: The shift
    print("\n\nPhase 2: The betrayal (at step 9)")
    env.reset()

    # Complete 1 more episode to reach step 9
    env.step("move_to_B")
    env.step("move_to_C")
    env.step("move_to_GOAL")
    env.reset()

    print(f"\nGlobal step: {env.global_step_count}, Phase shift at: {env.phase_shift_step}")
    print(f"Available actions from A: {env.get_available_actions()}")

    # Show trap path
    print("\n  Testing old path (A → B → C) in Phase 2:")
    state, reward, done, info = env.step("move_to_B")
    print(f"    Global step {info['global_step']}: A → {state} (reward: {reward:+.1f}) {info.get('warning', '')}")
    state, reward, done, info = env.step("move_to_C")
    print(f"    Global step {info['global_step']}: B → {state} (reward: {reward:+.1f}) - {info.get('trap', '')}")
    print(f"    Done: {done}, Episode reward: {info['episode_reward']:+.1f}")

    # Show new path
    env.hard_reset()
    # Get to phase 2
    for episode in range(3):
        env.step("move_to_B")
        env.step("move_to_C")
        env.step("move_to_GOAL")
        env.reset()

    print("\n  Testing new path (A → D → GOAL) in Phase 2:")
    print(f"  Global step before: {env.global_step_count}, Available: {env.get_available_actions()}")
    state, reward, done, info = env.step("move_to_D")
    print(f"    Global step {info['global_step']}: A → {state} (reward: {reward:+.1f}) - {info.get('discovery', '')}")
    state, reward, done, info = env.step("move_to_GOAL")
    print(f"    Global step {info['global_step']}: D → {state} (reward: {reward:+.1f}) - {info.get('success', '')}")
    print(f"    Done: {done}, Episode reward: {info['episode_reward']:+.1f}")

    print("\n✓ Environment test complete")
