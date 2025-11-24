#!/usr/bin/env python3
"""
Side-by-side comparison: Simple LLM vs Cognitive Agent

Run the same game with both approaches and see EXACTLY where they diverge.
"""
import sys
sys.path.insert(0, '/home/juancho/macgyver_mud')

import os
from neo4j import GraphDatabase
import textworld
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.simple_llm_player import ask_llm


def play_side_by_side(game_file: str, max_steps: int = 20):
    """Run same game with both players, compare actions."""
    
    print("\n" + "="*80)
    print("SIDE-BY-SIDE COMPARISON")
    print("="*80)
    print(f"Game: {game_file}")
    print(f"Max steps: {max_steps}\n")
    
    # Setup environments
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )
    
    # Simple LLM environment
    env_simple = textworld.start(game_file, request_infos=request_infos)
    state_simple = env_simple.reset()
    
    # Cognitive agent environment  
    env_cognitive = textworld.start(game_file, request_infos=request_infos)
    state_cognitive = env_cognitive.reset()
    
    # Setup cognitive agent
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()
    agent = TextWorldCognitiveAgent(session=session, verbose=False)
    agent.last_quest = state_cognitive.objective
    
    quest = state_simple.objective
    print(f"🎯 QUEST: {quest}")
    print(f"\n{'='*80}\n")
    
    # Run side-by-side
    done_simple = False
    done_cognitive = False
    step = 0
    
    while (not done_simple or not done_cognitive) and step < max_steps:
        step += 1
        print(f"{'─'*80}")
        print(f"STEP {step}")
        print(f"{'─'*80}")
        
        # Simple LLM
        if not done_simple:
            obs_simple = state_simple.feedback
            commands_simple = state_simple.admissible_commands
            action_simple = ask_llm(obs_simple, quest, commands_simple, step)
            
            state_simple, reward_simple, done_simple = env_simple.step(action_simple)
            
            print(f"🤖 Simple LLM:  {action_simple:40s} | Reward: {reward_simple:+.1f} | Done: {done_simple}")
        else:
            print(f"🤖 Simple LLM:  {'[FINISHED]':40s}")
        
        # Cognitive Agent
        if not done_cognitive:
            obs_cognitive = state_cognitive.feedback
            commands_cognitive = state_cognitive.admissible_commands
            
            # Call agent's step method
            action_cognitive = agent.step(
                observation=obs_cognitive,
                feedback=obs_cognitive,
                reward=0.0,
                done=False,
                admissible_commands=commands_cognitive,
                quest=None
            )
            
            state_cognitive, reward_cognitive, done_cognitive = env_cognitive.step(action_cognitive)
            
            # Check critical state
            critical_state = agent.current_critical_state.name if hasattr(agent, 'current_critical_state') else "FLOW"
            
            print(f"🧠 Cognitive:    {action_cognitive:40s} | Reward: {reward_cognitive:+.1f} | Done: {done_cognitive} | State: {critical_state}")
        else:
            print(f"🧠 Cognitive:    {'[FINISHED]':40s}")
        
        # Check for divergence
        if not done_simple and not done_cognitive:
            if action_simple != action_cognitive:
                print(f"   ⚠️  DIVERGENCE!")
        
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Simple LLM:  {'✅ WON' if done_simple else '❌ FAILED'} in {step} steps")
    print(f"Cognitive:   {'✅ WON' if done_cognitive else '❌ FAILED'} in {step} steps")
    
    # Cleanup
    env_simple.close()
    env_cognitive.close()
    session.close()
    driver.close()


if __name__ == "__main__":
    from environments.domain4_textworld.validate_planning import create_simple_game
    
    print("Creating test game...")
    game_file = create_simple_game()
    
    play_side_by_side(game_file, max_steps=20)
