#!/usr/bin/env python3
"""
Debug Script: Why isn't HUBRIS causing exploration of move_to_D?

Let's trace exactly what happens when cognitive agent encounters state A post-shift.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from critical_state import CriticalStateMonitor, CriticalState, AgentState
from validation.shifting_maze_env import ShiftingMazeEnv

# Simplified cognitive agent with DEBUG output
class DebugCognitiveAgent:
    def __init__(self):
        self.lifetime_rewards = []
        self.expected_rewards = {}
        self.failed_paths = set()
        self.reset()
        
    def reset(self):
        self.monitor = CriticalStateMonitor()
        self.history = []
        self.state_history = []
        self.reward_history = []
        self.steps_remaining = 100
        self.tried_actions_this_episode = set()
        
    def act(self, state, available_actions, last_reward=0.0):
        print(f"\n  🔍 ACT called:")
        print(f"      State: {state}")
        print(f"      Available: {available_actions}")
        print(f"      Lifetime rewards: {self.lifetime_rewards}")
        
        # Check HUBRIS
        agent_state = AgentState(
            entropy=0.05,
            history=self.state_history[-10:],
            steps=self.steps_remaining,
            dist=5,
            rewards=self.lifetime_rewards[-10:],
            error=0.0
        )
        
        critical_state = self.monitor.evaluate(agent_state)
        print(f"      Critical State: {critical_state.name}")
        
        if critical_state == CriticalState.HUBRIS:
            print(f"      ⚡ HUBRIS DETECTED!")
            print(f"      Looking for never-tried actions...")
            
            # Check which actions have been tried
            for action in available_actions:
                tried_this_ep = (state, action) in self.tried_actions_this_episode
                print(f"        {action}: tried_this_episode={tried_this_ep}")
                
                if not tried_this_ep:
                    print(f"        → Choosing {action} (never tried!)")
                    return action
        
        # Default: first action
        print(f"      → Default choice: {available_actions[0]}")
        return available_actions[0]
        
    def update(self, state, action, reward, done, info):
        self.history.append({'state': state, 'action': action, 'reward': reward})
        self.state_history.append(state)
        self.reward_history.append(reward)
        self.tried_actions_this_episode.add((state, action))
        self.lifetime_rewards.append(reward)
        self.steps_remaining -= 1

def main():
    print("="*80)
    print("DEBUG: Why doesn't HUBRIS trigger move_to_D?")
    print("="*80)
    
    env = ShiftingMazeEnv(phase_shift_step=9)
    agent = DebugCognitiveAgent()
    
    # Run 3 episodes
    for ep in range(1, 4):
        print(f"\n{'='*80}")
        print(f"EPISODE {ep} | Global Step: {env.global_step_count}")
        print(f"={'='*80}")
        
        state = env.reset()
        agent.reset()
        
        for step in range(20):
            available_actions = env.get_available_actions()
            if not available_actions:
                break
                
            last_reward = agent.reward_history[-1] if agent.reward_history else 0.0
            
            print(f"\nStep {env.global_step_count + 1}:")
            action = agent.act(state, available_actions, last_reward)
            
            state, reward, done, info = env.step(action)
            agent.update(state, action, reward, done, info)
            
            phase = info.get('phase', '?')
            print(f"  →  Result: {state} | reward={reward:+.1f} | {phase}")
            
            if done or state in ['GOAL', 'TRAP']:
                print(f"\n  Episode ended: {state}")
                break

if __name__ == "__main__":
    main()
