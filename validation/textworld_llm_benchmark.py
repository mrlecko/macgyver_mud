"""
TextWorld Re-Validation Benchmark

This script validates that the new Perceptual Layer (LLMPerception) enables the agent
to solve a TextWorld-style task by correctly extracting structured state from natural language.

Scenario:
1. Start in Kitchen.
2. Perceive 'apple' and 'closed door'.
3. Action: 'take apple' (Prerequisite for opening door).
4. Action: 'open door'.
5. Action: 'go east'.
6. Goal: Backyard.
"""

import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from perception.llm_parser import LLMPerception

class MockTextWorldEnv:
    """
    Simulates a simple TextWorld game:
    Kitchen (Start) -> East -> Backyard (Goal)
    Constraint: Must take apple and open door first.
    """
    def __init__(self):
        self.state = "kitchen"
        self.inventory = []
        self.door_open = False
        self.steps = 0
        
    def reset(self):
        self.state = "kitchen"
        self.inventory = []
        self.door_open = False
        self.steps = 0
        return self.get_observation()
        
    def get_observation(self):
        if self.state == "kitchen":
            obs = "You are in a kitchen. There is a table here. "
            if "apple" not in self.inventory:
                obs += "On the table you see an apple. "
            obs += "To the east is a wooden door. "
            if self.door_open:
                obs += "The door is open."
            else:
                obs += "The door is closed."
            return obs
        elif self.state == "backyard":
            return "You are in the backyard. You have escaped!"
        return "Unknown state."
        
    def step(self, action):
        self.steps += 1
        action = action.lower().strip()
        feedback = ""
        reward = 0
        done = False
        
        if self.state == "kitchen":
            if action == "take apple":
                if "apple" not in self.inventory:
                    self.inventory.append("apple")
                    feedback = "You take the apple."
                else:
                    feedback = "You already have that."
            elif action == "open door":
                if "apple" in self.inventory:
                    self.door_open = True
                    feedback = "You open the door."
                else:
                    feedback = "The door is stuck. You feel too weak. Maybe eat an apple?"
            elif action == "go east":
                if self.door_open:
                    self.state = "backyard"
                    feedback = "You step into the backyard."
                    reward = 10
                    done = True
                else:
                    feedback = "The door is closed."
            else:
                feedback = "I don't understand that."
        
        # Return feedback + current state description so the agent can "see"
        full_obs = f"{feedback} {self.get_observation()}"
        return full_obs, reward, done

class TextWorldAgent:
    def __init__(self):
        self.perception = LLMPerception(model_name="gpt-4o-mini")
        
    def act(self, observation):
        # 1. Perceive
        print(f"\n[Perception] Reading: '{observation}'")
        state = self.perception.parse(observation)
        print(f"[Perception] Extracted: {state}")
        
        # 2. Heuristic Logic (The "Brain" placeholder)
        items = state.get("items", [])
        
        # Check for apple
        apple = next((i for i in items if i["name"].lower() == "apple"), None)
        if apple and apple.get("location") != "inventory": 
            # Note: Our mock env removes apple from description when taken, 
            # so if we see it, we should take it.
            return "take apple"
            
        # Check for door
        door = next((i for i in items if "door" in i["name"].lower()), None)
        if door:
            if door["state"] == "closed":
                return "open door"
            if door["state"] == "open":
                return "go east"
                
        # Fallback
        return "look"

def run_benchmark():
    print("Starting TextWorld LLM Benchmark...")
    env = MockTextWorldEnv()
    agent = TextWorldAgent()
    
    obs = env.reset()
    done = False
    total_reward = 0
    
    for i in range(10):
        print(f"\n--- Step {i+1} ---")
        action = agent.act(obs)
        print(f"[Action] {action}")
        
        obs, reward, done = env.step(action)
        
        total_reward += reward
        if done:
            print(f"\nSUCCESS! Reached goal in {i+1} steps.")
            break
            
    if total_reward > 0:
        print("TEST PASSED")
    else:
        print("TEST FAILED")

if __name__ == "__main__":
    run_benchmark()
