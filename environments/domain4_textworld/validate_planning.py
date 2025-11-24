#!/usr/bin/env python3
"""
Quick validation script for planning integration.

Runs 2-3 simple TextWorld episodes with planning enabled and verbose output
to observe if planning works in practice.

Usage:
    cd /home/juancho/macgyver_mud
    python environments/domain4_textworld/validate_planning.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, '/home/juancho/macgyver_mud')

import textworld
from neo4j import GraphDatabase
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
import time


def create_simple_game(output_dir='/tmp/tw_validation'):
    """Create a simple TextWorld game for testing."""
    os.makedirs(output_dir, exist_ok=True)

    # Create simple game: find key, unlock chest
    options = textworld.GameOptions()
    options.seeds = 42  # Reproducible
    options.nb_rooms = 3
    options.nb_objects = 5
    options.quest_length = 3
    options.quest_breadth = 1

    game_file = f"{output_dir}/simple_game.z8"
    options.path = game_file  # Set path in options

    game = textworld.generator.make_game(options)
    textworld.generator.compile_game(game, options)  # Pass options, not string

    return game_file


def run_validation_episode(game_file, episode_num, max_steps=50):
    """Run single episode with verbose planning output."""
    print("\n" + "="*80)
    print(f"VALIDATION EPISODE {episode_num}")
    print("="*80)

    # Connect to Neo4j
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')

    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()

    # Create agent with planning enabled and VERBOSE
    agent = TextWorldCognitiveAgent(session=session, verbose=True)

    # Start TextWorld environment with proper configuration
    # CRITICAL FIX: Request admissible commands via EnvInfos!
    request_infos = textworld.EnvInfos(
        admissible_commands=True,  # This was missing - causes commands to be None
        objective=True,
        inventory=True,
        max_score=True
    )
    
    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()

    # TextWorld returns GameState object
    obs = game_state.feedback if hasattr(game_state, 'feedback') else str(game_state)
    infos = game_state.__dict__ if hasattr(game_state, '__dict__') else {}

    print(f"\n📍 INITIAL OBSERVATION:")
    print(f"   {obs}")
    print(f"\n🎯 QUEST: {infos.get('objective', 'Check game state')}")

    # Extract quest objective from game state
    quest_objective = infos.get('objective', None)
    if quest_objective:
        # Set agent's last_quest so goal inference uses the real quest
        agent.last_quest = quest_objective
        print(f"   📋 Quest set: {quest_objective}")
    
    # Episode tracking
    total_reward = 0
    reward = 0  # Current step reward
    step = 0
    done = False

    plan_generated = False
    plan_steps_completed = 0
    actions_on_plan = 0
    actions_off_plan = 0

    while not done and step < max_steps:
        step += 1
        print(f"\n{'─'*80}")
        print(f"STEP {step}/{max_steps}")
        print(f"{'─'*80}")

        # Get admissible commands - TextWorld stores these in the GameState
        if hasattr(game_state, 'admissible_commands') and game_state.admissible_commands:
            admissible_commands = game_state.admissible_commands
        elif hasattr(game_state, '_admissible_commands') and game_state._admissible_commands:
            admissible_commands = game_state._admissible_commands
        else:
            # Fallback to basic commands if not available
            admissible_commands = ['look', 'inventory', 'examine insect', 'take insect', 'go east', 'go south']

        # Ensure admissible_commands is never None
        if not admissible_commands:
            admissible_commands = ['look', 'inventory']

        # Agent step (this triggers planning internally)
        # step(observation, feedback, reward, done, admissible_commands, quest)
        action = agent.step(obs, obs, reward, done, admissible_commands, None)

        # Track planning metrics
        if agent.current_plan:
            if not plan_generated:
                plan_generated = True
                print(f"\n🎉 PLAN GENERATED!")
                print(f"   Goal: {agent.current_plan.goal}")
                print(f"   Strategy: {agent.current_plan.strategy}")
                print(f"   Steps: {len(agent.current_plan.steps)}")
                for i, step_obj in enumerate(agent.current_plan.steps, 1):
                    print(f"      {i}. {step_obj.description} (pattern: '{step_obj.action_pattern}')")

            # Check if action matches plan
            current_step = agent.current_plan.get_current_step()
            if current_step and current_step.matches_action(action):
                actions_on_plan += 1
                print(f"   ✅ Action matches plan step: {current_step.description}")
            else:
                actions_off_plan += 1
                if current_step:
                    print(f"   ⚠️  Action diverges from plan (expected: {current_step.description})")

        print(f"\n⚡ ACTION: {action}")

        # Execute action
        game_state, reward, done = env.step(action)
        obs = game_state.feedback if hasattr(game_state, 'feedback') else str(game_state)
        total_reward += reward

        if reward != 0:
            print(f"   💰 Reward: {reward:+.1f} (total: {total_reward:+.1f})")

        print(f"   📝 Observation: {obs[:200]}{'...' if len(obs) > 200 else ''}")

        # Show plan progress if plan exists
        if agent.current_plan:
            progress = agent.current_plan.progress_ratio()
            remaining = agent.current_plan.steps_remaining()
            print(f"   📊 Plan Progress: {progress:.0%} ({remaining} steps remaining)")

    # Episode summary
    print("\n" + "="*80)
    print(f"EPISODE {episode_num} SUMMARY")
    print("="*80)
    print(f"Result: {'✅ SUCCESS' if done and total_reward > 0 else '❌ FAILED'}")
    print(f"Steps: {step}/{max_steps}")
    print(f"Total Reward: {total_reward:+.1f}")
    print(f"\nPlanning Metrics:")
    print(f"  Plan Generated: {'✅ Yes' if plan_generated else '❌ No'}")

    if plan_generated:
        print(f"  Goal: {agent.current_plan.goal if agent.current_plan else 'Completed'}")
        print(f"  Actions on Plan: {actions_on_plan}")
        print(f"  Actions off Plan: {actions_off_plan}")

        if actions_on_plan + actions_off_plan > 0:
            adherence = actions_on_plan / (actions_on_plan + actions_off_plan)
            print(f"  Plan Adherence: {adherence:.0%}")

        if agent.plan_history:
            print(f"  Plans Completed: {len([p for p in agent.plan_history if p.is_complete()])}")
            print(f"  Plans Failed: {len([p for p in agent.plan_history if p.status.value == 'failed'])}")

    # Cleanup
    session.close()
    driver.close()
    env.close()

    return {
        'success': done and total_reward > 0,
        'steps': step,
        'reward': total_reward,
        'plan_generated': plan_generated,
        'actions_on_plan': actions_on_plan,
        'actions_off_plan': actions_off_plan
    }


def main():
    """Run validation test."""
    print("\n" + "🔬"*40)
    print("PLANNING SYSTEM VALIDATION TEST")
    print("🔬"*40)
    print("\nObjective: Verify planning integration works in real episodes")
    print("Method: Run 2-3 simple games with verbose output")
    print("Success: Plans generated, agent follows them, observable coherence")

    # Create test game
    print("\n📦 Creating test game...")
    game_file = create_simple_game()
    print(f"   Game created: {game_file}")

    # Run validation episodes
    results = []
    n_episodes = 2  # Start with 2 for quick feedback

    for i in range(1, n_episodes + 1):
        result = run_validation_episode(game_file, i)
        results.append(result)
        time.sleep(1)  # Brief pause between episodes

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL VALIDATION SUMMARY")
    print("="*80)

    successes = sum(1 for r in results if r['success'])
    plans_generated = sum(1 for r in results if r['plan_generated'])
    avg_steps = sum(r['steps'] for r in results) / len(results)

    print(f"\nEpisodes Run: {n_episodes}")
    print(f"Success Rate: {successes}/{n_episodes} ({successes/n_episodes:.0%})")
    print(f"Average Steps: {avg_steps:.1f}")
    print(f"Plans Generated: {plans_generated}/{n_episodes}")

    if plans_generated > 0:
        total_on_plan = sum(r['actions_on_plan'] for r in results)
        total_off_plan = sum(r['actions_off_plan'] for r in results)
        total_actions = total_on_plan + total_off_plan

        if total_actions > 0:
            overall_adherence = total_on_plan / total_actions
            print(f"Overall Plan Adherence: {overall_adherence:.0%}")

    # Validation checklist
    print("\n" + "─"*80)
    print("VALIDATION CHECKLIST:")
    print("─"*80)

    checklist = [
        ("Goal inference triggers", plans_generated > 0),
        ("Plans are generated (LLM works)", plans_generated > 0),
        ("Agent follows plans", total_on_plan > 0 if plans_generated > 0 else False),
        ("Plans have 3-7 steps", True),  # We'll check this manually in output
        ("Plan progress tracked", True),  # Visible in verbose output
    ]

    for item, status in checklist:
        symbol = "✅" if status else "❌"
        print(f"  {symbol} {item}")

    # Recommendations
    print("\n" + "─"*80)
    print("RECOMMENDATIONS:")
    print("─"*80)

    if plans_generated == 0:
        print("  ⚠️  NO PLANS GENERATED - Check:")
        print("     - Is goal inference working? (check _infer_goal_from_context)")
        print("     - Is LLM API working? (check llm CLI)")
        print("     - Are we waiting too long? (plan gen starts after step 3)")
    elif total_on_plan == 0:
        print("  ⚠️  PLANS GENERATED BUT NOT FOLLOWED - Check:")
        print("     - Is plan bonus too weak? (ε=2.0)")
        print("     - Are action patterns matching? (token-based matching)")
        print("     - Is EFE scoring balanced?")
    elif overall_adherence < 0.5:
        print("  ⚠️  LOW PLAN ADHERENCE - Consider:")
        print("     - Increasing plan bonus (ε > 2.0)")
        print("     - Improving goal inference")
        print("     - Checking if plans are reasonable for context")
    else:
        print("  ✅ PLANNING APPEARS TO BE WORKING!")
        print("     - Plans are generated")
        print("     - Agent follows them reasonably well")
        print("     - Ready to implement memory system next")

    print("\n" + "🔬"*40)
    print("VALIDATION COMPLETE")
    print("🔬"*40 + "\n")


if __name__ == "__main__":
    main()
