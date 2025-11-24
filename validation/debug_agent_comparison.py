#!/usr/bin/env python3
"""
Debug Script: Compare Working Demo Agent vs Benchmark Agent

This script runs both agents side-by-side on the SAME episode to see exactly
where they diverge.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from critical_state import CriticalStateMonitor, CriticalState, AgentState


# ============================================================================
# Environment (same as benchmark)
# ============================================================================

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
        reward = 0.0
        
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
            
        return self.state, reward, self.done, {"step": self.steps}


# ============================================================================
# WORKING Agent (from multi_domain_demo.py)
# ============================================================================

class WorkingAgent:
    """Exact copy from multi_domain_demo.py CriticalHoneyPotAgent"""
    def __init__(self):
        self.name = "Working (Original Demo)"
        self.monitor = CriticalStateMonitor()
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        
    def reset(self):
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        
    def act(self, last_reward):
        """Original act method from demo"""
        state = AgentState(
            entropy=0.05,
            history=self.history[-10:],
            steps=self.steps_remaining,
            dist=10,
            rewards=self.reward_history,
            error=0.0
        )
        critical_state = self.monitor.evaluate(state)
        
        print(f"      [Working] History: {self.history[-6:]}, Critical: {critical_state.name}")
        
        if critical_state in [CriticalState.DEADLOCK, CriticalState.HUBRIS]:
            print(f"      [Working] 🚨 DEADLOCK DETECTED! Escaping via C")
            return "C"
        if not self.history:
            return "A"
        if last_reward >= 1.0:
            return "B" if self.history[-1] == "A" else "A"
        return "C"
        
    def update(self, action, reward):
        self.history.append(action)
        self.reward_history.append(reward)
        self.steps_remaining -= 1


# ============================================================================
# BENCHMARK Agent (from shifting_maze_benchmark.py)
# ============================================================================

class BenchmarkAgent:
    """My implementation from benchmark"""
    def __init__(self):
        self.name = "Benchmark (My Version)"
        self.monitor = CriticalStateMonitor()
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        
    def reset(self):
        self.history = []
        self.reward_history = []
        self.steps_remaining = 100
        
    def act(self, state, available_actions, last_reward=0.0):
        """My act method from benchmark"""
        agent_state = AgentState(
            entropy=0.05,
            history=self.history[-10:],
            steps=self.steps_remaining,
            dist=10,
            rewards=self.reward_history,
            error=0.0
        )
        
        critical_state = self.monitor.evaluate(agent_state)
        
        print(f"      [Benchmark] History: {self.history[-6:]}, Critical: {critical_state.name}")
        
        if critical_state in [CriticalState.DEADLOCK, CriticalState.HUBRIS]:
            print(f"      [Benchmark] 🚨 DEADLOCK DETECTED! Escaping via C")
            return "C"
            
        # Greedy strategy
        if not self.history:
            return "A"
        if last_reward >= 1.0:
            return "B" if self.history[-1] == "A" else "A"
        return "C"
        
    def update(self, action, reward, done):
        self.history.append(action)
        self.reward_history.append(reward)
        self.steps_remaining -= 1


# ============================================================================
# Side-by-Side Comparison
# ============================================================================

def run_comparison(max_steps=20):
    """Run both agents on same seed and compare behavior."""
    
    print("="*80)
    print("SIDE-BY-SIDE COMPARISON: Working vs Benchmark Agent".center(80))
    print("="*80)
    print("\nEnvironment: HoneyPot (A↔B loop, C escapes)")
    print("Expected: Both should detect DEADLOCK and escape via C\n")
    
    # Setup
    env_working = HoneyPotEnv()
    env_benchmark = HoneyPotEnv()
    
    agent_working = WorkingAgent()
    agent_benchmark = BenchmarkAgent()
    
    # Run
    last_reward_working = 0.0
    last_reward_benchmark = 0.0
    
    for step in range(1, max_steps + 1):
        print(f"\n{'─'*80}")
        print(f"STEP {step}")
        print(f"{'─'*80}")
        
        # Working agent
        action_working = agent_working.act(last_reward_working)
        state_working, reward_working, done_working, _ = env_working.step(action_working)
        agent_working.update(action_working, reward_working)
        last_reward_working = reward_working
        
        print(f"  Working:   {action_working:10s} → state={state_working:10s} reward={reward_working:+.1f} done={done_working}")
        
        # Benchmark agent  
        action_benchmark = agent_benchmark.act(env_benchmark.state, ["A", "B", "C"], last_reward_benchmark)
        state_benchmark, reward_benchmark, done_benchmark, _ = env_benchmark.step(action_benchmark)
        agent_benchmark.update(action_benchmark, reward_benchmark, done_benchmark)
        last_reward_benchmark = reward_benchmark
        
        print(f"  Benchmark: {action_benchmark:10s} → state={state_benchmark:10s} reward={reward_benchmark:+.1f} done={done_benchmark}")
        
        # Check for divergence
        if action_working != action_benchmark:
            print(f"\n  ⚠️  DIVERGENCE! Working chose {action_working}, Benchmark chose {action_benchmark}")
        
        # Check if done
        if done_working or done_benchmark:
            print(f"\n{'='*80}")
            print("RESULT")
            print(f"{'='*80}")
            print(f"  Working:   {'✅ ESCAPED' if done_working else '❌ STUCK'} in {step} steps")
            print(f"  Benchmark: {'✅ ESCAPED' if done_benchmark else '❌ STUCK'} in {step} steps")
            break
    else:
        print(f"\n{'='*80}")
        print("RESULT")
        print(f"{'='*80}")
        print(f"  Working:   ❌ FAILED to escape in {max_steps} steps")
        print(f"  Benchmark: ❌ FAILED to escape in {max_steps} steps")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    run_comparison(max_steps=20)
