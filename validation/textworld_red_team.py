"""
TextWorld Red Team Comparison: Baseline vs Cognitive Agent

This script runs a head-to-head comparison between:
1. SimpleLLMPlayer (Baseline): Direct LLM prompting, no memory.
2. CognitiveAgent (Challenger): LLM Perception + Heuristic/Planning.

It generates 5 unique games (Seeds 42-46) and runs both agents on each.
"""

import sys
import os
import time
import pandas as pd
from neo4j import GraphDatabase

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from environments.domain4_textworld.textworld_adapter import TextWorldAdapter
from environments.domain4_textworld.simple_llm_player import play_game as play_simple_llm
from validation.textworld_real_benchmark import RealTextWorldAgent

def run_cognitive_episode(adapter, max_steps=20):
    """Run a single episode with the Cognitive Agent."""
    agent = RealTextWorldAgent()
    initial_state = adapter.reset()
    obs = initial_state.feedback
    done = False
    total_reward = 0
    steps = 0
    
    for i in range(max_steps):
        steps += 1
        admissible = adapter.get_admissible_commands()
        if not admissible:
            admissible = ['look']
            
        # Agent Act
        try:
            action = agent.act(obs, admissible)
        except Exception as e:
            print(f"Cognitive Agent Error: {e}")
            action = "look"
            
        # Env Step
        next_state, reward, done = adapter.step(action)
        obs = next_state.feedback
        total_reward += reward
        
        if done:
            break
            
    return {
        'success': done and total_reward > 0,
        'steps': steps,
        'reward': total_reward
    }

def run_red_team():
    print("\n" + "⚔️"*30)
    print("TEXTWORLD RED TEAM BATTLE")
    print("⚔️"*30)
    
    # Setup Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    
    results = []
    seeds = [42, 43, 44, 45, 46]
    
    try:
        adapter = TextWorldAdapter(session)
        
        for seed in seeds:
            print(f"\n\n>>> ROUND {seed} (Seed {seed}) <<<")
            
            # 1. Generate Game
            print(f"Generating Game {seed}...")
            game_file = adapter.generate_game(seed=seed)
            
            # 2. Run Baseline
            print(f"\n--- Baseline (SimpleLLM) ---")
            start_time = time.time()
            res_base = play_simple_llm(game_file, max_steps=20, verbose=False)
            base_time = time.time() - start_time
            print(f"Result: {'✅' if res_base['success'] else '❌'} | Reward: {res_base['reward']} | Steps: {res_base['steps']}")
            
            # 3. Run Challenger
            print(f"\n--- Challenger (Cognitive) ---")
            start_time = time.time()
            res_cog = run_cognitive_episode(adapter, max_steps=20)
            cog_time = time.time() - start_time
            print(f"Result: {'✅' if res_cog['success'] else '❌'} | Reward: {res_cog['reward']} | Steps: {res_cog['steps']}")
            
            results.append({
                'Seed': seed,
                'Baseline_Success': res_base['success'],
                'Baseline_Reward': res_base['reward'],
                'Baseline_Steps': res_base['steps'],
                'Cognitive_Success': res_cog['success'],
                'Cognitive_Reward': res_cog['reward'],
                'Cognitive_Steps': res_cog['steps']
            })
            
    finally:
        if 'adapter' in locals():
            adapter.close()
        session.close()
        driver.close()
        
    # Analysis
    df = pd.DataFrame(results)
    print("\n\n" + "="*60)
    print("FINAL SCOREBOARD")
    print("="*60)
    print(df)
    
    base_wins = df['Baseline_Success'].sum()
    cog_wins = df['Cognitive_Success'].sum()
    
    print(f"\nBaseline Wins: {base_wins}/5")
    print(f"Cognitive Wins: {cog_wins}/5")
    
    # Save results
    with open("TEXTWORLD_RED_TEAM_RESULTS.md", "w") as f:
        f.write("# TextWorld Red Team Results\n\n")
        f.write(df.to_markdown())
        f.write(f"\n\n**Baseline Wins:** {base_wins}/5\n")
        f.write(f"**Cognitive Wins:** {cog_wins}/5\n")

if __name__ == "__main__":
    run_red_team()
