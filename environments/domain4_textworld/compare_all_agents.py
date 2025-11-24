#!/usr/bin/env python3
"""
Compare All TextWorld Agents Side-by-Side

Tests three approaches on the same game:
1. Quest Agent (new minimal implementation)
2. Simple LLM (baseline)
3. Cognitive Agent (original cognitive architecture)

Goal: Demonstrate that Quest Agent fixes the TextWorld integration.
"""
import sys
sys.path.insert(0, '/home/juancho/macgyver_mud')

import os
import textworld
from neo4j import GraphDatabase

# Import agents
from environments.domain4_textworld.quest_agent import QuestAgent
from environments.domain4_textworld.simple_llm_player import ask_llm
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent


def run_quest_agent(game_file: str, max_steps: int = 20) -> dict:
    """Run Quest Agent on game."""
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )

    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()

    agent = QuestAgent(verbose=False)
    agent.reset(game_state.objective)

    step = 0
    total_reward = 0.0
    done = False
    actions = []

    while not done and step < max_steps:
        step += 1

        current_reward = 0.0
        if step > 1:
            current_reward = total_reward

        action = agent.step(
            observation=game_state.feedback,
            reward=current_reward,
            admissible_commands=game_state.admissible_commands
        )

        actions.append(action)
        game_state, reward, done = env.step(action)
        total_reward += reward

    env.close()

    return {
        'name': 'Quest Agent',
        'success': done and total_reward > 0,
        'steps': step,
        'reward': total_reward,
        'actions': actions
    }


def run_simple_llm(game_file: str, max_steps: int = 20) -> dict:
    """Run Simple LLM baseline on game."""
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )

    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()

    quest = game_state.objective
    step = 0
    total_reward = 0.0
    done = False
    actions = []

    while not done and step < max_steps:
        step += 1

        obs = game_state.feedback
        commands = game_state.admissible_commands

        action = ask_llm(obs, quest, commands, step)
        actions.append(action)

        game_state, reward, done = env.step(action)
        total_reward += reward

    env.close()

    return {
        'name': 'Simple LLM',
        'success': done and total_reward > 0,
        'steps': step,
        'reward': total_reward,
        'actions': actions
    }


def run_cognitive_agent(game_file: str, max_steps: int = 20) -> dict:
    """Run Cognitive Agent on game."""
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )

    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()

    # Setup Neo4j connection
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')

    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()

    agent = TextWorldCognitiveAgent(session=session, verbose=False)
    agent.last_quest = game_state.objective

    step = 0
    total_reward = 0.0
    done = False
    actions = []

    while not done and step < max_steps:
        step += 1

        obs = game_state.feedback
        commands = game_state.admissible_commands

        action = agent.step(
            observation=obs,
            feedback=obs,
            reward=total_reward,
            done=False,
            admissible_commands=commands,
            quest=None
        )

        actions.append(action)
        game_state, reward, done = env.step(action)
        total_reward += reward

    env.close()
    session.close()
    driver.close()

    return {
        'name': 'Cognitive Agent',
        'success': done and total_reward > 0,
        'steps': step,
        'reward': total_reward,
        'actions': actions
    }


def compare_agents(game_file: str, max_steps: int = 20):
    """Compare all three agents on the same game."""
    print("\n" + "=" * 80)
    print("THREE-WAY COMPARISON: Quest Agent vs Simple LLM vs Cognitive Agent")
    print("=" * 80)
    print(f"Game: {game_file}")
    print(f"Max steps: {max_steps}\n")

    # Run each agent
    print("Running agents...")
    quest_result = run_quest_agent(game_file, max_steps)
    print(f"  ✓ Quest Agent complete")

    llm_result = run_simple_llm(game_file, max_steps)
    print(f"  ✓ Simple LLM complete")

    cognitive_result = run_cognitive_agent(game_file, max_steps)
    print(f"  ✓ Cognitive Agent complete")

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    results = [quest_result, llm_result, cognitive_result]

    for result in results:
        status = "✅ WON" if result['success'] else "❌ FAILED"
        print(f"\n{result['name']:20s} {status:10s} "
              f"({result['steps']:2d} steps, {result['reward']:+.1f} reward)")

        # Show first few actions
        if len(result['actions']) <= 5:
            for i, action in enumerate(result['actions'], 1):
                print(f"  {i}. {action}")
        else:
            for i in range(3):
                print(f"  {i+1}. {result['actions'][i]}")
            print(f"  ... ({len(result['actions']) - 3} more actions)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    quest_status = "✅" if quest_result['success'] else "❌"
    llm_status = "✅" if llm_result['success'] else "❌"
    cog_status = "✅" if cognitive_result['success'] else "❌"

    print(f"\n{quest_status} Quest Agent:     {quest_result['steps']:2d} steps")
    print(f"{llm_status} Simple LLM:      {llm_result['steps']:2d} steps")
    print(f"{cog_status} Cognitive Agent: {cognitive_result['steps']:2d} steps")

    print("\n" + "─" * 80)
    print("INTERPRETATION:")
    print("─" * 80)

    if quest_result['success'] and llm_result['success'] and not cognitive_result['success']:
        print("✅ VALIDATION SUCCESSFUL!")
        print("   Quest Agent performs similarly to Simple LLM baseline")
        print("   Both outperform the Cognitive Agent (which was stuck in loops)")
        print("   → Quest Agent successfully fixes the TextWorld integration")
    elif quest_result['success'] and not llm_result['success']:
        print("🎉 EXCELLENT!")
        print("   Quest Agent actually BEATS the Simple LLM baseline!")
        print("   This shows the structured approach adds value")
    elif not quest_result['success']:
        print("⚠️  Quest Agent failed - needs debugging")
    else:
        print(f"   Quest Agent: {quest_result['steps']} steps")
        print(f"   LLM Baseline: {llm_result['steps']} steps")
        print(f"   Cognitive: {cognitive_result['steps']} steps")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    from environments.domain4_textworld.validate_planning import create_simple_game

    print("Creating test game...")
    game_file = create_simple_game()

    compare_agents(game_file, max_steps=20)
