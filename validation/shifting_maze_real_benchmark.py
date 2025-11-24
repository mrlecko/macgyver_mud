#!/usr/bin/env python3
"""
Shifting Maze (Real) Comprehensive Benchmark

Tests cognitive architecture on ACTUAL shifting maze environment:
- Multi-step navigation (A→B→C→GOAL)
- Environment shift at step 9 (betrayal!)
- Old path becomes trap, new path opens
- Tests: HUBRIS detection, adaptation, memory

This is a REAL-WORLD test of:
1. Multi-episode learning
2. Adaptation to changing environments
3. Balance between exploitation and exploration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from typing import List, Dict
from critical_state import CriticalStateMonitor, CriticalState, AgentState
from validation.shifting_maze_env import ShiftingMazeEnv


# ============================================================================
# Agent Types
# ============================================================================

class GreedyAgent:
    """Baseline: Always follows highest reward path (no adaptation)."""
    def __init__(self):
        self.name = "Greedy (No Adaptation)"
        self.reset()
        
    def reset(self):
        """Reset for new episode."""
        self.history = []
        self.learned_path = None  # Will learn A→B→C→GOAL
        
    def act(self, state, available_actions, last_reward=0.0):
        """
        Greedy strategy:
        - Learn successful path
        - Repeat it forever (even when it becomes trap!)
        """
        if not available_actions:
            return None
            
        # If we learned a successful path, follow it
        if self.learned_path:
            if state in self.learned_path:
                next_state = self.learned_path[self.learned_path.index(state) + 1]
                for action in available_actions:
                    if action == f"move_to_{next_state}":
                        return action
        
        # Otherwise, prefer actions that gave highest reward before
        if self.history:
            # Try to continue successful pattern
            best_action = available_actions[0]  # Default
            for action in available_actions:
                # Prefer actions we've seen work
                if any(h['action'] == action and h['reward'] > 0 for h in self.history):
                    best_action = action
                    break
            return best_action
        
        return available_actions[0]  # First action by default
        
    def update(self, state, action, reward, done, info):
        """Track history."""
        self.history.append({
            'state': state,
            'action': action,
            'reward': reward,
            'done': done
        })
        
        # If we reached GOAL, remember the path
        if state == "GOAL" and done:
            path = [h['state'] for h in self.history]
            self.learned_path = path


class CognitiveAgent:
    """
    Enhanced cognitive architecture with:
    - Persistent reward tracking (HUBRIS detection)
    - Prediction error calculation (NOVELTY detection)
    - Exploration when stuck (escape loops)
    """
    def __init__(self):
        self.name = "Cognitive (Enhanced)"
        
        # PERSISTENT STATE (survives across episodes)
        self.lifetime_rewards = []  # All rewards ever received
        self.expected_rewards = {}  # state → expected reward learned
        self.failed_paths = set()   # Remember which paths failed
        self.episode_count = 0
        
        self.reset()
        
    def reset(self):
        """Reset for new episode (but keep lifetime state!)."""
        self.episode_count += 1
        
        # Create fresh monitor for this episode
        self.monitor = CriticalStateMonitor()
        
        # Episode-specific state
        self.history = []
        self.state_history = []
        self.reward_history = []
        self.steps_remaining = 100
        self.tried_actions_this_episode = set()
        
        # Critical state tracking
        self.hubris_count = 0
        self.novelty_count = 0
        self.last_state = None
        self.last_reward = 0.0
        
    def calculate_prediction_error(self, state, actual_reward):
        """
        Calculate how much actual reward differs from expected.
        
        High error = NOVELTY (something unexpected happened)
        """
        if state not in self.expected_rewards:
            # First time seeing this state, no expectation
            return 0.0
            
        expected = self.expected_rewards[state]
        error = abs(actual_reward - expected)
        
        # Normalize to 0-1 range (assume rewards in -10 to +10)
        normalized_error = min(error / 20.0, 1.0)
        
        return normalized_error
        
    def update_expectations(self, state, reward):
        """
        Update expected reward for state using running average.
        """
        if state not in self.expected_rewards:
            self.expected_rewards[state] = reward
        else:
            # Running average: 80% old + 20% new
            old = self.expected_rewards[state]
            self.expected_rewards[state] = 0.8 * old + 0.2 * reward
        
    def is_stuck(self, state):
        """
        Detect if we're stuck in a loop (same state multiple times with negative rewards).
        """
        if len(self.state_history) < 3:
            return False
            
        # Count how many times we've been in this state recently
        recent_states = self.state_history[-5:]
        times_in_state = recent_states.count(state)
        
        if times_in_state >= 3:
            # And if recent rewards are negative
            recent_rewards = self.reward_history[-3:]
            if all(r < 0 for r in recent_rewards):
                return True
        
        return False
        
    def act(self, state, available_actions, last_reward=0.0):
        """
        Enhanced action selection with critical state awareness.
        """
        # Capture current state for history tracking
        self.current_state_for_history = state
        
        if not available_actions:
            return None
            
        # Calculate prediction error BEFORE updating monitor
        prediction_error = self.calculate_prediction_error(state, last_reward)
        
        # Build agent state for monitor
        # Use LIFETIME rewards for HUBRIS detection!
        agent_state = AgentState(
            entropy=0.1 if len(self.lifetime_rewards) < 3 else 0.05,
            history=self.state_history[-10:],
            steps=self.steps_remaining,
            dist=5,
            rewards=self.lifetime_rewards[-10:],  # Use lifetime, not episode!
            error=prediction_error  # ACTUAL prediction error!
        )
        
        # Check for critical states
        critical_state = self.monitor.evaluate(agent_state)
        
        # Track detections
        if critical_state == CriticalState.HUBRIS:
            self.hubris_count += 1
        elif critical_state == CriticalState.NOVELTY:
            self.novelty_count += 1
            
        # STRATEGY 1: If stuck in loop → EXPLORE randomly
        if self.is_stuck(state):
            # Try actions we haven't tried this episode
            untried = [a for a in available_actions 
                      if (state, a) not in self.tried_actions_this_episode]
            if untried:
                action = untried[0]  # Could also be random.choice(untried)
                return action
        
        # STRATEGY 2: If HUBRIS or NOVELTY → explore genuinely NEW paths
        if critical_state in [CriticalState.HUBRIS, CriticalState.NOVELTY]:
            # First, try actions we've NEVER tried in ANY episode
            never_tried = []
            for action in available_actions:
                # Check if this action has ever been tried from this state
                action_sig = (state, action)
                if action_sig not in self.tried_actions_this_episode:
                    # Also check if it's in our episode history
                    if not any(h['action'] == action and prev_state == state 
                              for i, h in enumerate(self.history) 
                              for prev_state in ([self.state_history[i-1]] if i > 0 else [])):
                        never_tried.append(action)
            
            if never_tried:
                # Prefer genuinely novel actions when HUBRIS detected!
                return never_tried[0]
            
            # If no never-tried actions, avoid known failures
            for action in available_actions:
                path_sig = f"{state}→{action}"
                if path_sig not in self.failed_paths:
                    return action
        
        # STRATEGY 3: Default greedy (prefer actions that gave rewards before)
        # BUT AVOID KNOWN FAILED PATHS!
        if self.history:
            # Score each action by historical reward
            action_scores = {}
            
            for action in available_actions:
                # CRITICAL: Skip actions that are known to lead to failure
                path_sig = f"{state}→{action}"
                if path_sig in self.failed_paths:
                    action_scores[action] = -999.0  # Heavily penalize failed paths
                    continue
                
                # Did this action work in the past?
                past_rewards = [h['reward'] for h in self.history 
                               if h.get('action') == action]
                if past_rewards:
                    action_scores[action] = sum(past_rewards) / len(past_rewards)
                else:
                    action_scores[action] = 0.0
            
            # Choose best action (avoiding failed paths)
            best_action = max(action_scores.items(), key=lambda x: x[1])[0]
            
            return best_action
        
        # STRATEGY 4: No history yet, try first action
        # BUT CHECK FAILED PATHS FIRST!
        for action in available_actions:
            path_sig = f"{state}→{action}"
            if path_sig not in self.failed_paths:
                return action
                
        # If all actions failed, try the first one anyway (desperation)
        return available_actions[0]
        
    def update(self, state, action, reward, done, info):
        """Update agent state after action."""
        # Track episode-specific state
        self.history.append({
            'state': self.current_state_for_history, # Use the state where action was taken!
            'action': action,
            'reward': reward,
            'done': done
        })
        self.state_history.append(self.current_state_for_history) # Append visited state
        self.reward_history.append(reward)
        self.steps_remaining -= 1
        
        # Track which actions we've tried
        self.tried_actions_this_episode.add((self.current_state_for_history, action))
        
        # CRITICAL: Track lifetime rewards for HUBRIS detection
        self.lifetime_rewards.append(reward)
        
        # Update expectations for prediction error
        if self.last_state is not None:
            self.update_expectations(self.last_state, self.last_reward)
        
        # ============================================================
        # MULTI-STEP CREDIT ASSIGNMENT
        # ============================================================
        # When we hit a catastrophic failure (trap), blame the ENTIRE path
        # that led to it, not just the immediate action!
        if reward < -5.0:  # Catastrophic failure (trap)
            # Blame last N steps (trace back the path that led here)
            lookback = min(3, len(self.state_history))
            
            for i in range(1, lookback + 1):
                # We need to match: state at step -i with action at step -i
                # state_history now contains [A, B] for path A->B->TRAP
                # history contains actions taken at A, B
                
                idx = -i
                if abs(idx) <= len(self.state_history):
                    blamed_state = self.state_history[idx]
                    blamed_action = self.history[idx]['action']
                    
                    path_sig = f"{blamed_state}→{blamed_action}"
                    self.failed_paths.add(path_sig)
                    
        self.last_state = state
        self.last_reward = reward
        
    def get_stats(self):
        """Get agent statistics."""
        return {
            'hubris_detections': self.hubris_count,
            'novelty_detections': self.novelty_count,
            'episode': self.episode_count,
            'failed_paths_learned': len(self.failed_paths)
        }


# ============================================================================
# Benchmark Runner
# ============================================================================

def run_episode(agent, env, episode_num, verbose=False):
    """
    Run one episode of Shifting Maze.
    
    Returns:
        dict with episode metrics
    """
    state = env.reset()
    agent.reset()
    
    total_reward = 0.0
    last_reward = 0.0
    actions_taken = []
    states_visited = [state]
    
    step = 0
    max_steps = 20
    
    while step < max_steps:
        step += 1
        
        available_actions = env.get_available_actions()
        if not available_actions:
            break
            
        action = agent.act(state, available_actions, last_reward)
        if action is None:
            break
            
        actions_taken.append(action)
        
        prev_state = state
        state, reward, done, info = env.step(action)
        total_reward += reward
        last_reward = reward
        states_visited.append(state)
        
        agent.update(state, action, reward, done, info)
        
        if verbose:
            phase = info.get('phase', '?')
            print(f"  Step {info['global_step']:3d} ({phase}): {prev_state} --{action[-1]}--> {state} | reward={reward:+.1f}")
            if 'trap' in info:
                print(f"       ⚠️  {info['trap']}")
            if 'warning' in info:
                print(f"       ⚡ {info['warning']}")
        
        if done or state in ['GOAL', 'TRAP']:
            break
    
    # Collect metrics
    success = (state == "GOAL")
    hit_trap = (state == "TRAP")
    
    result = {
        'success': success,
        'hit_trap': hit_trap,
        'steps': step,
        'total_reward': total_reward,
        'states': states_visited,
        'actions': actions_taken
    }
    
    # Add agent-specific stats
    if hasattr(agent, 'get_stats'):
        result.update(agent.get_stats())
    
    return result


def run_benchmark(agent_class, n_episodes=5, phase_shift=9, verbose=False):
    """
    Run N episodes with given agent type.
    Environment shifts at global step 'phase_shift'.
    
    Returns:
        List of episode results
    """
    agent = agent_class()
    env = ShiftingMazeEnv(phase_shift_step=phase_shift)
    
    results = []
    for episode in range(1, n_episodes + 1):
        if verbose:
            print(f"\n{'='*80}")
            print(f"Episode {episode}/{n_episodes} | Global Step: {env.global_step_count}")
            print(f"{'='*80}")
        
        result = run_episode(agent, env, episode, verbose=verbose)
        result['episode'] = episode
        result['global_step_start'] = env.global_step_count - result['steps']
        results.append(result)
        
        if verbose:
            status = "✅ SUCCESS" if result['success'] else ("💥 TRAP" if result['hit_trap'] else "❌ FAILED")
            print(f"\n  {status} | Steps: {result['steps']} | Reward: {result['total_reward']:+.1f}")
    
    return results


def print_results(agent_name, results):
    """Print summary statistics."""
    n = len(results)
    success_count = sum(1 for r in results if r['success'])
    trap_count = sum(1 for r in results if r['hit_trap'])
    
    avg_steps = sum(r['steps'] for r in results) / n
    avg_reward = sum(r['total_reward'] for r in results) / n
    
    # Count pre-shift vs post-shift
    pre_shift_success = sum(1 for r in results if r['success'] and r['global_step_start'] < 9)
    post_shift_success = sum(1 for r in results if r['success'] and r['global_step_start'] >= 9)
    
    print(f"\n{'='*70}")
    print(f"{agent_name} Results (N={n})")
    print(f"{'='*70}")
    print(f"Success Rate: {success_count}/{n} ({success_count/n*100:.1f}%)")
    print(f"Trap Rate: {trap_count}/{n} ({trap_count/n*100:.1f}%)")
    print(f"Average Steps: {avg_steps:.1f}")
    print(f"Average Reward: {avg_reward:+.1f}")
    print(f"\nPre-Shift Success: {pre_shift_success} episodes")
    print(f"Post-Shift Success: {post_shift_success} episodes")
    
    # Agent-specific stats
    if 'hubris_detections' in results[0]:
        total_hubris = sum(r.get('hubris_detections', 0) for r in results)
        total_novelty = sum(r.get('novelty_detections', 0) for r in results)
        print(f"\nCritical State Detections:")
        print(f"  HUBRIS: {total_hubris}")
        print(f"  NOVELTY: {total_novelty}")
    
    print(f"{'='*70}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Shifting Maze Real Benchmark")
    parser.add_argument('--episodes', type=int, default=5, help='Episodes to run')
    parser.add_argument('--shift', type=int, default=9, help='Global step for environment shift')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("SHIFTING MAZE REAL BENCHMARK".center(80))
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Episodes: {args.episodes}")
    print(f"  Phase shift at global step: {args.shift}")
    print(f"\nEnvironment:")
    print(f"  Phase 1 (steps 1-{args.shift-1}): A→B→C→GOAL (safe path)")
    print(f"  Phase 2 (step {args.shift}+): B→C→TRAP! New path: A→D→GOAL")
    print(f"\nAgent Types:")
    print(f"  1. Greedy - Learns successful path, repeats forever (no adaptation)")
    print(f"  2. Cognitive - Detects HUBRIS/NOVELTY, explores new paths")
    
    # Run benchmarks
    print("\n" + "-"*80)
    print("Running Greedy Agent...")
    print("-"*80)
    greedy_results = run_benchmark(GreedyAgent, args.episodes, args.shift, args.verbose)
    print_results("Greedy Agent", greedy_results)
    
    print("\n" + "-"*80)
    print("Running Cognitive Agent...")
    print("-"*80)
    cognitive_results = run_benchmark(CognitiveAgent, args.episodes, args.shift, args.verbose)
    print_results("Cognitive Agent", cognitive_results)
    
    # Summary comparison
    print("\n" + "="*80)
    print("COMPARISON SUMMARY".center(80))
    print("="*80)
    
    greedy_success = sum(1 for r in greedy_results if r['success']) / len(greedy_results) * 100
    cognitive_success = sum(1 for r in cognitive_results if r['success']) / len(cognitive_results) * 100
    
    greedy_traps = sum(1 for r in greedy_results if r['hit_trap'])
    cognitive_traps = sum(1 for r in cognitive_results if r['hit_trap'])
    
    print(f"\nSuccess Rates:")
    print(f"  Greedy:    {greedy_success:5.1f}%  (Traps: {greedy_traps})")
    print(f"  Cognitive: {cognitive_success:5.1f}%  (Traps: {cognitive_traps})")
    
    print(f"\nKey Question: Does cognitive agent ADAPT when environment shifts?")
    
    if cognitive_traps < greedy_traps:
        print(f"  ✅ YES! Cognitive avoided {greedy_traps - cognitive_traps} more traps")
        print(f"  ✅ HUBRIS/NOVELTY detection working!")
    else:
        print(f"  ❌ NO - Both agents hit same number of traps")
        print(f"  ❌ Adaptation not working as expected")
        
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
