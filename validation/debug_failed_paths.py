#!/usr/bin/env python3
"""
Debug: Why isn't failed_paths filter working?
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from critical_state import CriticalStateMonitor, CriticalState, AgentState
from validation.shifting_maze_env import ShiftingMazeEnv

class DebugAgent:
    def __init__(self):
        self.lifetime_rewards = []
        self.failed_paths = set()
        self.reset()
        
    def reset(self):
        self.monitor = CriticalStateMonitor()
        self.history = []
        self.state_history = []
        self.reward_history = []
        
    def act(self, state, available_actions):
        print(f"\n  🔍 ACT at {state}:")
        print(f"      Available: {available_actions}")
        print(f"      Failed paths: {self.failed_paths}")
        
        if self.history:
            action_scores = {}
            for action in available_actions:
                path_sig = f"{state}→{action}"
                if path_sig in self.failed_paths:
                    action_scores[action] = -999.0
                    print(f"        {action}: PENALIZED (in failed_paths)")
                else:
                    past_rewards = [h['reward'] for h in self.history if h.get('action') == action]
                    score = sum(past_rewards) / len(past_rewards) if past_rewards else 0.0
                    action_scores[action] = score
                    print(f"        {action}: score={score:.2f}")
            
            best = max(action_scores.items(), key=lambda x: x[1])
            print(f"      → Choosing: {best[0]} (score={best[1]:.2f})")
            return best[0]
        
        return available_actions[0]
        
    def update(self, state, action, reward, done, info):
        self.history.append({'state': state, 'action': action, 'reward': reward})
        self.state_history.append(state)
        self.reward_history.append(reward)
        self.lifetime_rewards.append(reward)
        
        if reward < -5.0:
            lookback = min(3, len(self.state_history) - 1)
            print(f"\n      💥 TRAP! Blaming last {lookback} steps:")
            for i in range(1, lookback + 1):
                state_idx = -(i + 1)
                action_idx = -i
                if abs(state_idx) <= len(self.state_history) and abs(action_idx) <= len(self.history):
                    blamed_state = self.state_history[state_idx]
                    blamed_action = self.history[action_idx]['action']
                    path_sig = f"{blamed_state}→{blamed_action}"
                    self.failed_paths.add(path_sig)
                    print(f"         {path_sig} marked FAILED")

env = ShiftingMazeEnv(phase_shift_step=9)
agent = DebugAgent()

for ep in range(1, 6):
    print(f"\n{'='*60}")
    print(f"Episode {ep}")
    print(f"{'='*60}")
    state = env.reset()
    agent.reset()
    
    for step in range(20):
        available = env.get_available_actions()
        if not available:
            break
        action = agent.act(state, available)
        state, reward, done, info = env.step(action)
        agent.update(state, action, reward, done, info)
        print(f"      Result: {state} | reward={reward:+.1f}")
        if done or state in ['GOAL', 'TRAP']:
            break
