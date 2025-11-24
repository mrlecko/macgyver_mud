#!/usr/bin/env python3
"""
Debug Script 2: Test Full Episode Loop

Test if the problem is in the episode reset logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from critical_state import CriticalStateMonitor, CriticalState, AgentState


class HoneyPotEnv:
    def __init__(self):
        self.state = "A"
        self.steps = 0
        self.done = False
        
    def reset(self):
        self.state = "A"
        self.steps = 0
        self.done = False
        return self.state
        
    def step(self, action):
        if self.done:
            return self.state, 0.0, True, {}
            
        self.steps += 1
        if action == "A":
            self.state = "B"
            reward = 1.0
        elif action == "B":
            self.state = "A"
            reward = 1.0
        elif action == "C":
            self.state = "ESCAPE"
            reward = 10.0
            self.done = True
        else:
            reward = -1.0
            
        return self.state, reward, self.done, {}


class CognitiveAgent:
    def __init__(self):
        self.monitor = CriticalStateMonitor()
        self.reset()
        
    def reset(self):
        """Reset for new episode"""
        print("    [Agent] RESET called")
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        self.deadlock_count = 0
        
    def act(self, state, available_actions, last_reward=0.0):
        agent_state = AgentState(
            entropy=0.05,
            history=self.history[-10:],
            steps=self.steps_remaining,
            dist=10,
            rewards=self.reward_history,
            error=0.0
        )
        
        critical_state = self.monitor.evaluate(agent_state)
        
        # Debug output
        print(f"      History: {self.history}, Critical: {critical_state.name}")
        
        if critical_state in [CriticalState.DEADLOCK, CriticalState.HUBRIS]:
            print(f"      🚨 DEADLOCK DETECTED!")
            self.deadlock_count += 1
            return "C"
            
        if not self.history:
            return "A"
        if last_reward >= 1.0:
            return "B" if self.history[-1] == "A" else "A"
        return "C"
        
    def update(self, action, reward, done):
        self.history.append(action)
        self.reward_history.append(reward)
        self.steps_remaining -= 1


def run_episode(agent, env, episode_num, max_steps=20):
    """Run ONE episode"""
    print(f"\n{'='*60}")
    print(f"Episode {episode_num}")
    print(f"{'='*60}")
    
    state = env.reset()
    agent.reset()  # CRITICAL: Reset agent
    
    last_reward = 0.0
    
    for step in range(1, max_steps + 1):
        print(f"  Step {step}:")
        
        action = agent.act(state, ["A", "B", "C"], last_reward)
        state, reward, done, _ = env.step(action)
        agent.update(action, reward, done)
        last_reward = reward
        
        print(f"    → Action: {action}, State: {state}, Reward: {reward:+.1f}, Done: {done}")
        
        if done:
            print(f"  ✅ ESCAPED in {step} steps")
            return True
    
    print(f"  ❌ FAILED to escape")
    return False


def main():
    print("="*80)
    print("TESTING MULTIPLE EPISODES WITH SAME AGENT".center(80))
    print("="*80)
    print("\nQuestion: Does agent.reset() properly clear history between episodes?")
    
    agent = CognitiveAgent()
    env = HoneyPotEnv()
    
    escapes = 0
    for ep in range(1, 6):
        escaped = run_episode(agent, env, ep, max_steps=20)
        if escaped:
            escapes += 1
    
    print(f"\n{'='*80}")
    print(f"RESULT: {escapes}/5 episodes escaped")
    print(f"{'='*80}\n")
    
    if escapes == 5:
        print("✅ Agent works correctly across multiple episodes!")
    else:
        print("❌ Agent performance degrades across episodes - reset issue?")


if __name__ == "__main__":
    main()
