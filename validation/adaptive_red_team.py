#!/usr/bin/env python3
"""
Adaptive Red Team: Battle-Testing the Geometric Controller
==========================================================

Stress tests for the new "Geometric Meta-Cognition" feature.

Test 1: "The Jitterbug"
    - Checks for stability/oscillation when entropy hovers near the threshold.
    - Does the agent flip-flop strategies?

Test 2: "The Mimic"
    - Checks for vulnerability to "False Confidence".
    - If the agent is WRONG but CERTAIN, does the controller save it?
    - Spoiler: It shouldn't.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from agent_runtime import AgentRuntime

# Enable the feature for testing
config.ENABLE_GEOMETRIC_CONTROLLER = True

def run_jitterbug_test():
    print("\n" + "="*60)
    print("TEST 1: THE JITTERBUG (Oscillation Stress Test)")
    print("="*60)
    
    # Mock Runtime
    session = MagicMock()
    with patch('agent_runtime.get_agent', return_value={"id": 1}):
        with patch('agent_runtime.get_initial_belief', return_value=0.5):
            agent = AgentRuntime(session, "locked")
            
    # Mock Skills
    skills = [
        {"name": "Specialist", "cost": 1.0, "expected_goal": 10.0, "expected_info": 0.0},
        {"name": "Balanced", "cost": 1.0, "expected_goal": 5.0, "expected_info": 5.0}
    ]
    
    # Mock Scoring (Base)
    # Specialist always wins on base score
    def mock_score(skill, p, **kwargs):
        return 10.0 if skill["name"] == "Specialist" else 8.0
        
    # Mock Silver (Shape)
    def mock_silver(name, cost, p):
        if name == "Specialist": return {"k_explore": 0.0}
        return {"k_explore": 0.8}
        
    print("Simulating Entropy Fluctuation around Threshold (0.4)...")
    print("-" * 40)
    
    # Entropy sequence: 0.39 -> 0.41 -> 0.39 -> 0.41 ...
    entropies = [0.39, 0.41, 0.39, 0.41, 0.39, 0.41]
    
    switches = 0
    last_mode = None
    
    with patch('agent_runtime.score_skill', side_effect=mock_score):
        with patch('scoring_silver.build_silver_stamp', side_effect=mock_silver):
            with patch('scoring_silver.entropy') as mock_entropy:
                
                for i, e in enumerate(entropies):
                    mock_entropy.return_value = e
                    agent.p_unlocked = 0.5 # Dummy value, entropy is mocked
                    
                    selected = agent.select_skill(skills)
                    
                    # Infer mode from selection
                    # Specialist -> Flow (k=0)
                    # Balanced -> Panic (k=0.8)
                    mode = "FLOW" if selected["name"] == "Specialist" else "PANIC"
                    
                    print(f"Step {i}: Entropy={e:.2f} -> Mode={mode} (Selected: {selected['name']})")
                    
                    if last_mode and mode != last_mode:
                        switches += 1
                    last_mode = mode
                    
    print("-" * 40)
    print(f"Total Switches: {switches} / {len(entropies)-1}")
    
    if switches > 2:
        print("❌ FAILED: High Oscillation Detected. The agent is 'Jitterbugging'.")
    else:
        print("✅ PASSED: Stable. (Hysteresis/Meta-Monitor working)")

def run_mimic_test():
    print("\n" + "="*60)
    print("TEST 2: THE MIMIC (False Confidence Test)")
    print("="*60)
    
    # Scenario: Agent is CONFIDENT (Low Entropy) that door is safe.
    # Reality: Door is a Mimic (Trap).
    
    # Mock Runtime
    session = MagicMock()
    with patch('agent_runtime.get_agent', return_value={"id": 1}):
        with patch('agent_runtime.get_initial_belief', return_value=0.5):
            agent = AgentRuntime(session, "mimic")
            agent.use_procedural_memory = True # Enable memory for Veto
            
    # Skills
    skills = [
        {"name": "Smash", "cost": 1.0, "expected_goal": 10.0, "expected_info": 0.0}, # Triggers Mimic
        {"name": "Inspect", "cost": 1.0, "expected_goal": 5.0, "expected_info": 5.0} # Reveals Mimic
    ]
    
    # Mock Scoring
    def mock_score(skill, p, **kwargs):
        return 10.0 if skill["name"] == "Smash" else 8.0
        
    def mock_silver(name, cost, p):
        if name == "Smash": return {"k_explore": 0.0}
        return {"k_explore": 0.8}
        
    # Mock Memory Stats (Bad History)
    # This simulates that the agent has tried this before and failed
    mock_stats = {
        "success_rate": 0.1, 
        "count": 10,
        "overall": {"uses": 10}
    }
        
    # High Confidence (Low Entropy)
    entropy_val = 0.1 
    
    print(f"Agent State: Confident (Entropy={entropy_val})")
    print("Memory: Historical Success Rate = 10% (BAD)")
    print("Reality: IT'S A TRAP!")
    print("-" * 40)
    
    with patch('agent_runtime.score_skill', side_effect=mock_score):
        with patch('scoring_silver.build_silver_stamp', side_effect=mock_silver):
            with patch('scoring_silver.entropy', return_value=entropy_val):
                with patch('agent_runtime.get_skill_stats', return_value=mock_stats):
                    # Mock score_skill_with_memory (needed because use_procedural_memory=True)
                    with patch('agent_runtime.score_skill_with_memory', return_value=(10.0, "explanation")):
                
                        selected = agent.select_skill(skills)
                        
                        # Check Mode
                        mode = agent.geo_mode
                        print(f"Controller Mode: {mode}")
                        print(f"Selected Action: {selected['name']}")
                        
                        if "PANIC" in mode and selected["name"] == "Inspect":
                            print("Outcome: SURVIVED. (Memory Veto triggered)")
                            print("✅ PASSED: The controller saved the agent from Delusion.")
                        elif selected["name"] == "Smash":
                            print("Outcome: 💀 DIED. (Triggered Mimic)")
                            print("❌ FAILED: The controller did not save the agent.")
                        else:
                            print(f"Outcome: Unknown ({selected['name']})")

if __name__ == "__main__":
    run_jitterbug_test()
    run_mimic_test()
