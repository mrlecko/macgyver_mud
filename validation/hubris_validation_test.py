"""
Hubris Protocol Validation Test

This test demonstrates that the Hubris protocol can prevent catastrophic failure
in environments with silent regime shifts (The Turkey Problem).

Scenario:
1. Agent learns a successful path over 8 steps
2. At step 9, the environment silently shifts
3. The old "safe" path now leads to a trap
4. A new path becomes available

Expected Outcomes:
- Baseline Agent: Falls into trap (follows learned pattern blindly)
- Hubris-Aware Agent: Detects overconfidence, explores, finds new path
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shifting_maze_env import ShiftingMazeEnv
from critical_state import CriticalStateMonitor, CriticalState, AgentState
import config


class BaselineAgent:
    """
    Standard Active Inference agent without critical state monitoring.
    Will exploit learned patterns without questioning them.
    """

    def __init__(self):
        self.name = "Baseline (Greedy)"
        self.learned_path = ["move_to_B", "move_to_C", "move_to_GOAL"]
        self.path_index = 0
        self.reward_history = []
        self.state_history = []

    def reset(self):
        """Reset agent state."""
        self.path_index = 0
        self.reward_history = []
        self.state_history = []

    def select_action(self, available_actions):
        """
        Select action based on learned pattern.
        Simple greedy exploitation.
        """
        # Follow learned path
        if self.learned_path[self.path_index % 3] in available_actions:
            action = self.learned_path[self.path_index % 3]
        else:
            # Fallback: take first available action
            action = available_actions[0] if available_actions else None

        self.path_index += 1
        return action

    def observe(self, state, reward, done, info):
        """Record observation."""
        self.reward_history.append(reward)
        self.state_history.append(state)


class HubrisAwareAgent:
    """
    Agent with Hubris protocol enabled.
    Will detect overconfidence and force exploration when success streak is too long.
    """

    def __init__(self):
        self.name = "Hubris-Aware (Skeptical)"
        self.monitor = CriticalStateMonitor()
        self.learned_path = ["move_to_B", "move_to_C", "move_to_GOAL"]
        self.path_index = 0
        self.reward_history = []
        self.state_history = []
        self.entropy = 0.05  # Start confident (low entropy)
        self.hubris_triggered = False
        self.hubris_trigger_step = None
        self.successful_episodes = 0  # Track consecutive successful episodes

    def reset(self):
        """Reset agent state for new episode (keeps successful_episodes counter)."""
        self.path_index = 0
        # Don't reset monitor or successful_episodes - track across episodes!

    def select_action(self, available_actions, step_count):
        """
        Select action based on learned pattern + critical state monitoring.
        """
        # Build reward history for hubris check: use successful_episodes as proxy
        # Simulate consecutive high rewards (1.0 per successful episode)
        simulated_rewards = [10.0] * min(self.successful_episodes, 10)

        # Check for Hubris
        agent_state = AgentState(
            entropy=self.entropy,
            history=self.state_history[-10:],
            steps=100,  # High value (not scarce)
            dist=10,
            rewards=simulated_rewards,  # Use successful episode streak
            error=0.0
        )

        critical_state = self.monitor.evaluate(agent_state)

        # Optionally enable debug output
        # if self.successful_episodes >= 2 and step_count >= 7 and step_count <= 18:
        #     print(f"    [DEBUG] Step {step_count}: Episodes={self.successful_episodes}, Entropy={self.entropy:.3f}, "
        #           f"Rewards={len(simulated_rewards)}, State={critical_state}, Actions={available_actions}")

        # If Hubris detected OR previously triggered (stays active), force exploration
        if critical_state == CriticalState.HUBRIS or (self.hubris_triggered and self.successful_episodes >= 2):
            if not self.hubris_triggered:
                self.hubris_triggered = True
                self.hubris_trigger_step = step_count
                print(f"    🚨 HUBRIS DETECTED at step {step_count}")
                print(f"       Icarus Protocol: Forcing skeptical exploration")
                print(f"       Episodes: {self.successful_episodes}, Entropy: {self.entropy:.3f}")

            # Explore: choose action NOT in learned path
            # CRITICAL: Only explore at decision points, not when stuck
            if len(available_actions) > 1:
                for action in available_actions:
                    if action not in self.learned_path:
                        print(f"       → Exploring new action: {action}")
                        return action

            # If no new actions available or only one option, continue with normal behavior
            # (This prevents getting stuck at states with only one action)

        # Normal behavior: follow learned path
        if self.learned_path[self.path_index % 3] in available_actions:
            action = self.learned_path[self.path_index % 3]
        else:
            action = available_actions[0] if available_actions else None

        self.path_index += 1
        return action

    def observe(self, state, reward, done, info):
        """Record observation and update entropy."""
        self.reward_history.append(reward)
        self.state_history.append(state)

        # Track successful episodes (reaching GOAL)
        if done and state == "GOAL":
            self.successful_episodes += 1
            # After multiple successes, become more confident (lower entropy)
            self.entropy = max(0.02, 0.15 - (self.successful_episodes * 0.02))
        elif done and state == "TRAP":
            # Reset on failure
            self.successful_episodes = 0
            self.entropy = 0.15


def run_agent(agent_class, num_episodes=4, verbose=True):
    """
    Run agent through the shifting maze scenario.

    Args:
        agent_class: Agent class to instantiate
        num_episodes: Number of episodes to run (must be >= 4 to trigger shift)
        verbose: Print detailed output

    Returns:
        dict: Results including total reward, success rate, hubris info
    """
    env = ShiftingMazeEnv(phase_shift_step=9)
    agent = agent_class()

    total_reward = 0.0
    episode_rewards = []
    catastrophic_failure = False

    if verbose:
        print(f"\n{'='*60}")
        print(f"Running: {agent.name}")
        print(f"{'='*60}")

    for episode in range(num_episodes):
        env.reset()
        agent.reset()

        if verbose:
            print(f"\nEpisode {episode + 1}:")

        episode_reward = 0.0
        step_in_episode = 0

        while not env.done and step_in_episode < 10:
            available_actions = env.get_available_actions()

            if not available_actions:
                break

            # Agent selects action
            if isinstance(agent, HubrisAwareAgent):
                action = agent.select_action(available_actions, env.global_step_count)
            else:
                action = agent.select_action(available_actions)

            # Execute action
            state, reward, done, info = env.step(action)
            agent.observe(state, reward, done, info)

            episode_reward += reward
            step_in_episode += 1

            if verbose:
                phase_marker = "🔄" if env.global_step_count >= env.phase_shift_step else "  "
                print(f"  {phase_marker} Step {env.global_step_count}: {info['prev_state']} → {state} "
                      f"(reward: {reward:+.1f})")

                if "warning" in info:
                    print(f"       ⚠️  {info['warning']}")
                if "trap" in info:
                    print(f"       💀 {info['trap']}")
                    catastrophic_failure = True
                if "discovery" in info:
                    print(f"       ✨ {info['discovery']}")
                if "success" in info:
                    print(f"       ✅ {info['success']}")

        episode_rewards.append(episode_reward)
        total_reward += episode_reward

        if verbose:
            print(f"  Episode Reward: {episode_reward:+.1f}")

    results = {
        "agent_name": agent.name,
        "total_reward": total_reward,
        "episode_rewards": episode_rewards,
        "catastrophic_failure": catastrophic_failure,
        "final_episode_reward": episode_rewards[-1] if episode_rewards else 0.0
    }

    if isinstance(agent, HubrisAwareAgent):
        results["hubris_triggered"] = agent.hubris_triggered
        results["hubris_trigger_step"] = agent.hubris_trigger_step

    if verbose:
        print(f"\nTotal Reward: {total_reward:+.1f}")
        print(f"Catastrophic Failure: {catastrophic_failure}")
        if isinstance(agent, HubrisAwareAgent) and agent.hubris_triggered:
            print(f"Hubris Trigger: Step {agent.hubris_trigger_step}")

    return results


def validate_hubris_protocol():
    """
    Main validation function.
    Compares baseline vs hubris-aware agent.
    """
    print("\n" + "="*70)
    print("HUBRIS PROTOCOL VALIDATION TEST")
    print("Scenario: The Turkey Problem (Shifting Maze)")
    print("="*70)

    # Ensure config is set for Hubris detection
    # Lower threshold since we only have 2 successful episodes before the shift
    config.CRITICAL_THRESHOLDS["HUBRIS_STREAK"] = 2  # Trigger after 2 successful episodes
    config.CRITICAL_THRESHOLDS["HUBRIS_ENTROPY"] = 0.15  # Entropy must be below this

    # Run baseline
    print("\n[TEST 1: BASELINE AGENT]")
    print("Expected: Falls into trap after environment shift")
    baseline_results = run_agent(BaselineAgent, num_episodes=4, verbose=True)

    # Run hubris-aware
    print("\n[TEST 2: HUBRIS-AWARE AGENT]")
    print("Expected: Detects overconfidence, explores, avoids trap")
    hubris_results = run_agent(HubrisAwareAgent, num_episodes=4, verbose=True)

    # Analysis
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)

    print(f"\nBaseline Agent:")
    print(f"  Total Reward: {baseline_results['total_reward']:+.1f}")
    print(f"  Catastrophic Failure: {baseline_results['catastrophic_failure']}")

    print(f"\nHubris-Aware Agent:")
    print(f"  Total Reward: {hubris_results['total_reward']:+.1f}")
    print(f"  Catastrophic Failure: {hubris_results['catastrophic_failure']}")
    print(f"  Hubris Triggered: {hubris_results.get('hubris_triggered', False)}")
    if hubris_results.get('hubris_trigger_step'):
        print(f"  Trigger Step: {hubris_results['hubris_trigger_step']}")

    # Verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)

    success_criteria = {
        "baseline_fails": baseline_results['catastrophic_failure'],
        "hubris_succeeds": not hubris_results['catastrophic_failure'],
        "hubris_triggers": hubris_results.get('hubris_triggered', False),
        "reward_delta": hubris_results['total_reward'] > baseline_results['total_reward']
    }

    all_passed = all(success_criteria.values())

    print(f"\n✓ Baseline falls into trap: {success_criteria['baseline_fails']}")
    print(f"✓ Hubris agent avoids trap: {success_criteria['hubris_succeeds']}")
    print(f"✓ Hubris protocol triggers: {success_criteria['hubris_triggers']}")
    print(f"✓ Hubris agent scores higher: {success_criteria['reward_delta']} "
          f"(Δ = {hubris_results['total_reward'] - baseline_results['total_reward']:+.1f})")

    if all_passed:
        print("\n🎉 ALL VALIDATION CRITERIA PASSED")
        print("\nConclusion: The Hubris protocol successfully prevents catastrophic failure")
        print("when an agent becomes overconfident after a success streak, and the")
        print("environment shifts unexpectedly.")
        return True
    else:
        print("\n❌ VALIDATION FAILED")
        failed = [k for k, v in success_criteria.items() if not v]
        print(f"Failed criteria: {', '.join(failed)}")
        return False


if __name__ == "__main__":
    success = validate_hubris_protocol()
    sys.exit(0 if success else 1)
