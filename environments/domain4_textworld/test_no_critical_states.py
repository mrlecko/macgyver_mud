#!/usr/bin/env python3
"""
Test cognitive agent with critical states DISABLED.

Hypothesis: ESCALATION protocol is causing the agent to fail.
Let's see if it can win without critical state monitoring.
"""
import sys
sys.path.insert(0, '/home/juancho/macgyver_mud')

import os
from neo4j import GraphDatabase
import textworld


def test_without_critical_states(game_file: str, max_steps: int = 20):
    """Run cognitive agent with critical states disabled."""
    
    print("\n" + "="*80)
    print("COGNITIVE AGENT - CRITICAL STATES DISABLED")
    print("="*80)
    
    # Setup
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )
    
    env = textworld.start(game_file, request_infos=request_infos)
    state = env.reset()
    
    # Cognitive agent
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()
    
    from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
    agent = TextWorldCognitiveAgent(session=session, verbose=False)
    agent.last_quest = state.objective
    
    # CRITICAL: Disable critical state monitoring
    agent.critical_monitor = None  # No critical states!
    
    print(f"🎯 QUEST: {state.objective}")
    print(f"⚠️  Critical states: DISABLED\n")
    
    # Run episode
    total_reward = 0
    done = False
    step = 0
    
    while not done and step < max_steps:
        step += 1
        
        obs = state.feedback
        commands = state.admissible_commands
        
        # Agent step (no critical state checking)
        action = agent.select_action(commands, None)
        
        # Update beliefs manually (since we're bypassing step())
        agent.update_beliefs(obs, obs)
        agent.maybe_generate_plan(commands)
        if agent.current_plan:
            agent.check_plan_progress(action)
        
        state, reward, done = env.step(action)
        total_reward += reward
        
        print(f"Step {step:2d}: {action:40s} | Reward: {reward:+.1f} | Done: {done}")
    
    print(f"\n{'='*80}")
    print(f"Result: {'✅ WON' if done and total_reward > 0 else '❌ FAILED'}")
    print(f"Steps: {step}")
    print(f"Reward: {total_reward:+.1f}")
    print(f"{'='*80}")
    
    env.close()
    session.close()
    driver.close()
    
    return done and total_reward > 0


if __name__ == "__main__":
    from environments.domain4_textworld.validate_planning import create_simple_game
    
    print("Creating test game...")
    game_file = create_simple_game()
    
    success = test_without_critical_states(game_file, max_steps=20)
    
    if success:
        print("\n✅ Agent CAN win without critical states!")
        print("   → Critical state monitoring is the problem")
    else:
        print("\n❌ Agent still fails even without critical states")
        print("   → Problem is deeper (EFE scoring, planning, etc.)")
