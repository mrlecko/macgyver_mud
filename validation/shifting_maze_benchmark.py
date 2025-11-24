#!/usr/bin/env python3
"""
Shifting Maze Comprehensive Benchmark

Statistical validation showing cognitive architecture's strengths:
- N=20 episodes per agent type
- 3 agent types: Random, Greedy (baseline), Cognitive
- Detailed metrics: escape rate, steps, DEADLOCK detection
- Reproducible with seed

Run: python validation/shifting_maze_benchmark.py --episodes 20 --seed 42
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import argparse
from typing import List, Dict
from critical_state import CriticalStateMonitor, CriticalState, AgentState


# ============================================================================
# Environment (using HoneyPot pattern from multi_domain_demo.py)
# ============================================================================

class HoneyPotEnv:
    """
    Reward loop environment that tests DEADLOCK detection.
    
    States: A, B, C, ESCAPE
    - A ↔ B: Reward loop (+1.0 each)
    - C: Escape action (+10.0, ends episode)
    """
    def __init__(self):
        self.state = "A"
        self.steps = 0
        self.done = False
        
    def reset(self):
        """Reset to initial state."""
        self.state = "A"
        self.steps = 0
        self.done = False
        return self.state
        
    def get_available_actions(self):
        """Get available actions from current state."""
        if self.done:
            return []
        # From any state, can loop (A/B) or escape (C)
        return ["A", "B", "C"]
        
    def step(self, action):
        """Execute action and return (state, reward, done, info)."""
        if self.done:
            return self.state, 0.0, True, {"error": "Episode finished"}
            
        self.steps += 1
        reward = 0.0
        info = {"step": self.steps}
        
        if action == "A":
            self.state = "B"
            reward = 1.0
            info["action_type"] = "loop"
        elif action == "B":
            self.state = "A"
            reward = 1.0
            info["action_type"] = "loop"
        elif action == "C":
            self.state = "ESCAPE"
            reward = 10.0
            self.done = True
            info["action_type"] = "escape"
            info["success"] = True
        else:
            reward = -1.0
            info["error"] = f"Invalid action: {action}"
            
        return self.state, reward, self.done, info


# ============================================================================
# Agent Types
# ============================================================================

class RandomAgent:
    """Baseline: Random action selection."""
    def __init__(self, seed=None):
        self.name = "Random"
        if seed is not None:
            random.seed(seed)
        self.reset()
        
    def reset(self):
        """Reset agent for new episode."""
        pass
        
    def act(self, state, available_actions, last_reward=0.0):
        """Choose random action."""
        return random.choice(available_actions)
        
    def update(self, action, reward, done):
        """No learning."""
        pass


class GreedyAgent:
    """Baseline: Follow rewards greedily (no critical state detection)."""
    def __init__(self):
        self.name = "Greedy"
        self.reset()
        
    def reset(self):
        """Reset for new episode."""
        self.history = []
        self.reward_history = []
        
    def act(self, state, available_actions, last_reward=0.0):
        """
        Greedy strategy:
        - If no history, try A
        - If getting rewards, alternate A↔B
        - Otherwise try C
        """
        if not self.history:
            return "A"
        if last_reward >= 1.0:
            # Keep looping (gets stuck!)
            return "B" if self.history[-1] == "A" else "A"
        return "C"
        
    def update(self, action, reward, done):
        """Track history."""
        self.history.append(action)
        self.reward_history.append(reward)


class CognitiveAgent:
    """Full cognitive architecture with DEADLOCK detection."""
    def __init__(self):
        self.name = "Cognitive"
        self.reset()
        
    def reset(self):
        """Reset for new episode."""
        # CRITICAL FIX: Create NEW monitor each episode!
        # The monitor's state_history persists across episodes, causing
        # ESCALATION after first DEADLOCK detection
        self.monitor = CriticalStateMonitor()
        
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        self.deadlock_count = 0
        
    def act(self, state, available_actions, last_reward=0.0):
        """
        Active Inference with critical state monitoring.
        
        - Monitors for DEADLOCK (A↔B loop)
        - If DEADLOCK detected → escape via C
        - Otherwise greedy
        """
        # Create agent state for monitor
        agent_state = AgentState(
            entropy=0.05,
            history=self.history[-10:],
            steps=self.steps_remaining,
            dist=10,
            rewards=self.reward_history,
            error=0.0
        )
        
        # Check critical state
        critical_state = self.monitor.evaluate(agent_state)
        
        # If DEADLOCK or HUBRIS detected → escape!
        if critical_state in [CriticalState.DEADLOCK, CriticalState.HUBRIS]:
            self.deadlock_count += 1
            return "C"  # Escape!
            
        # Otherwise use greedy strategy (same as GreedyAgent)
        if not self.history:
            return "A"
        if last_reward >= 1.0:
            return "B" if self.history[-1] == "A" else "A"
        return "C"
        
    def update(self, action, reward, done):
        """Update state."""
        self.history.append(action)
        self.reward_history.append(reward)
        self.steps_remaining -= 1
        
    def get_deadlock_count(self):
        """Get number of times DEADLOCK was detected."""
        return self.deadlock_count


# ============================================================================
# Benchmark Runner
# ============================================================================

def run_episode(agent, env, max_steps=50, verbose=False):
    """
    Run one episode with given agent.
    
    Returns:
        dict with episode metrics
    """
    state = env.reset()
    agent.reset()
    
    total_reward = 0.0
    last_reward = 0.0
    actions_taken = []
    
    for step in range(max_steps):
        available_actions = env.get_available_actions()
        if not available_actions:
            break
            
        action = agent.act(state, available_actions, last_reward)
        actions_taken.append(action)
        
        state, reward, done, info = env.step(action)
        total_reward += reward
        last_reward = reward
        
        agent.update(action, reward, done)
        
        if verbose:
            print(f"  Step {step+1}: {action} → reward={reward:+.1f}")
            
        if done:
            break
    
    # Collect metrics
    escaped = (state == "ESCAPE")
    steps_to_escape = len(actions_taken) if escaped else max_steps
    deadlock_detections = agent.get_deadlock_count() if hasattr(agent, 'get_deadlock_count') else 0
    
    return {
        'escaped': escaped,
        'steps': steps_to_escape,
        'total_reward': total_reward,
        'actions': actions_taken,
        'deadlock_detections': deadlock_detections
    }


def run_benchmark(agent_class, n_episodes=20, seed=None, verbose=False):
    """
    Run N episodes with given agent type.
    
    Returns:
        List of episode results
    """
    if seed is not None:
        random.seed(seed)
        
    agent = agent_class() if agent_class != RandomAgent else agent_class(seed=seed)
    env = HoneyPotEnv()
    
    results = []
    for episode in range(n_episodes):
        if verbose:
            print(f"\nEpisode {episode+1}/{n_episodes}")
        result = run_episode(agent, env, max_steps=50, verbose=verbose)
        results.append(result)
        
    return results


def print_results(agent_name, results):
    """Print summary statistics."""
    n = len(results)
    escape_count = sum(1 for r in results if r['escaped'])
    escape_rate = escape_count / n * 100
    
    avg_steps = sum(r['steps'] for r in results) / n
    avg_reward = sum(r['total_reward'] for r in results) / n
    total_deadlocks = sum(r['deadlock_detections'] for r in results)
    
    print(f"\n{'='*60}")
    print(f"{agent_name} Agent Results (N={n})")
    print(f"{'='*60}")
    print(f"Escape Rate: {escape_count}/{n} ({escape_rate:.1f}%)")
    print(f"Average Steps: {avg_steps:.1f}")
    print(f"Average Reward: {avg_reward:+.1f}")
    if total_deadlocks > 0:
        print(f"DEADLOCK Detections: {total_deadlocks}")
    print(f"{'='*60}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Shifting Maze Benchmark")
    parser.add_argument('--episodes', type=int, default=20, help='Episodes per agent')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("SHIFTING MAZE COMPREHENSIVE BENCHMARK".center(80))
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Episodes per agent: {args.episodes}")
    print(f"  Random seed: {args.seed}")
    print(f"  Environment: Honey Pot (A↔B reward loop)")
    print("\nAgent Types:")
    print("  1. Random - Chooses actions randomly")
    print("  2. Greedy - Follows rewards (no critical states)")
    print("  3. Cognitive - Full architecture with DEADLOCK detection")
    
    # Run benchmarks
    print("\n" + "-"*80)
    print("Running Random Agent...")
    print("-"*80)
    random_results = run_benchmark(RandomAgent, args.episodes, args.seed, args.verbose)
    print_results("Random", random_results)
    
    print("\n" + "-"*80)
    print("Running Greedy Agent (Baseline)...")
    print("-"*80)
    greedy_results = run_benchmark(GreedyAgent, args.episodes, args.seed, args.verbose)
    print_results("Greedy", greedy_results)
    
    print("\n" + "-"*80)
    print("Running Cognitive Agent...")
    print("-"*80)
    cognitive_results = run_benchmark(CognitiveAgent, args.episodes, args.seed, args.verbose)
    print_results("Cognitive", cognitive_results)
    
    # Summary comparison
    print("\n" + "="*80)
    print("COMPARISON SUMMARY".center(80))
    print("="*80)
    
    random_escape = sum(1 for r in random_results if r['escaped']) / len(random_results) * 100
    greedy_escape = sum(1 for r in greedy_results if r['escaped']) / len(greedy_results) * 100
    cognitive_escape = sum(1 for r in cognitive_results if r['escaped']) / len(cognitive_results) * 100
    
    print(f"\nEscape Rates:")
    print(f"  Random:    {random_escape:5.1f}%")
    print(f"  Greedy:    {greedy_escape:5.1f}%")
    print(f"  Cognitive: {cognitive_escape:5.1f}% ✅")
    
    print(f"\nConclusion:")
    if cognitive_escape > greedy_escape:
        improvement = cognitive_escape - greedy_escape
        print(f"  ✅ Cognitive agent outperforms baseline by {improvement:.1f}%")
        print(f"  ✅ DEADLOCK detection successfully breaks reward loops")
    else:
        print(f"  ❌ Cognitive agent did not outperform baseline")
        
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
