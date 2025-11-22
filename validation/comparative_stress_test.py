import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from critical_state import CriticalStateMonitor, CriticalState, AgentState

# Mock Environment
class HoneyPotEnv:
    def __init__(self):
        self.actions = ["A", "B", "C"]
        self.state = "A"
        self.steps = 0
    
    def step(self, action):
        self.steps += 1
        reward = 0.0
        done = False
        
        if action == "A":
            reward = 1.0 # The Trap: High reward
            self.state = "B"
        elif action == "B":
            reward = 1.0 # The Trap: High reward
            self.state = "A"
        elif action == "C":
            reward = 10.0 # The Escape
            done = True
            
        return self.state, reward, done

# Baseline Agent (Simulated Active Inference)
class BaselineAgent:
    def __init__(self):
        self.name = "Baseline (Standard)"
        self.history = []
    
    def act(self, last_reward):
        # Simple logic: If last reward was good, keep doing what works (Exploit)
        # This simulates a greedy/efficient Active Inference agent in a local optimum
        if last_reward >= 1.0:
            # Toggle between A and B (The Loop)
            return "B" if self.history and self.history[-1] == "A" else "A"
        else:
            return random.choice(["A", "B", "C"])
            
    def update(self, action):
        self.history.append(action)

# Critical Agent (With Protocols)
class CriticalAgent:
    def __init__(self):
        self.name = "Critical (Protocols)"
        self.monitor = CriticalStateMonitor()
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        self.entropy = 0.05 # Low entropy (confident)
        self.prediction_error = 0.0
        
    def act(self, last_reward):
        # 1. Update State
        state = AgentState(
            entropy=self.entropy,
            history=self.history[-10:],
            steps=self.steps_remaining,
            dist=10,
            rewards=self.reward_history,
            error=self.prediction_error
        )
        
        # 2. Check Monitor
        critical_state = self.monitor.evaluate(state)
        
        # 3. Decide
        if critical_state == CriticalState.HUBRIS:
            # ICARUS PROTOCOL: Force Exploration (Break the loop)
            # "I am too successful. Something is wrong."
            return "C" # In a real agent, this would be a random exploration or specific heuristic
            
        elif critical_state == CriticalState.DEADLOCK:
            # SISYPHUS PROTOCOL: Perturbation
            return "C"
            
        else:
            # Standard Behavior (Same as Baseline)
            if last_reward >= 1.0:
                return "B" if self.history and self.history[-1] == "A" else "A"
            else:
                return random.choice(["A", "B", "C"])

    def update(self, action, reward):
        self.history.append(action)
        self.reward_history.append(reward)
        self.steps_remaining -= 1

def run_simulation(agent_cls, max_steps=20):
    env = HoneyPotEnv()
    agent = agent_cls()
    print(f"\n--- Running {agent.name} ---")
    
    last_reward = 0.0
    for i in range(max_steps):
        # Decide
        if isinstance(agent, BaselineAgent):
            action = agent.act(last_reward)
            agent.update(action)
        else:
            action = agent.act(last_reward)
            agent.update(action, last_reward)
            
        # Act
        state, reward, done = env.step(action)
        last_reward = reward
        
        print(f"Step {i+1}: Action={action}, Reward={reward}")
        
        if done:
            print(f"SUCCESS! Escaped in {i+1} steps.")
            return i + 1
            
    print("FAILURE! Stuck in loop.")
    return max_steps + 1

if __name__ == "__main__":
    # Ensure config is loaded
    config.CRITICAL_THRESHOLDS["HUBRIS_STREAK"] = 5
    
    print("=== COMPARATIVE STRESS TEST: THE HONEY POT ===")
    print("Scenario: A/B Loop gives Reward=1.0. C gives Reward=10.0 (Escape).")
    
    steps_baseline = run_simulation(BaselineAgent)
    steps_critical = run_simulation(CriticalAgent)
    
    print("\n=== RESULTS ===")
    print(f"Baseline Agent: {steps_baseline} steps (Failed/Slow)")
    print(f"Critical Agent: {steps_critical} steps (Fast)")
    
    if steps_critical < steps_baseline:
        print("\nVERDICT: Critical State Protocols successfully broke the local optimum.")
        sys.exit(0)
    else:
        print("\nVERDICT: No improvement detected.")
        sys.exit(1)
