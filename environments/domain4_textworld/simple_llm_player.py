#!/usr/bin/env python3
"""
Simple LLM Player - No Framework, Just Common Sense

The simplest possible TextWorld player to establish if games are winnable.

NO active inference, NO planning, NO memory, NO cognitive architecture.
Just: Show the LLM what's happening, ask what to do, execute.

This is our baseline to validate if our complex architecture is helping or hurting.
"""
import sys
import os
import json
import subprocess

sys.path.insert(0, '/home/juancho/macgyver_mud')

import textworld


def ask_llm(observation: str, quest: str, admissible_commands: list, step: int) -> str:
    """
    Ask LLM what to do given current state.
    
    No fancy prompting, no socratic methods, just: "What should I do?"
    """
    # Defensive check
    if not admissible_commands:
        admissible_commands = ['look', 'inventory']
    
    # Build simple prompt
    prompt = f"""You are playing a text adventure game. Here's your current situation:

QUEST: {quest}

OBSERVATION:
{observation}

AVAILABLE COMMANDS:
{', '.join(admissible_commands[:20])}  # Show first 20

What command should you execute to make progress toward the quest?
Respond with ONLY the command, nothing else. Choose from the available commands.

Command:"""

    try:
        # Call LLM CLI (use default model)
        result = subprocess.run(
            ['llm', prompt],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"⚠️  LLM error: {result.stderr}")
            return "look"  # Fallback
        
        response = result.stdout.strip()
        
        # Clean up response (sometimes LLM adds extra text)
        response = response.split('\n')[0].strip()
        
        # Verify it's in admissible commands
        if response in admissible_commands:
            return response
        
        # Try fuzzy match
        for cmd in admissible_commands:
            if response.lower() in cmd.lower() or cmd.lower() in response.lower():
                return cmd
        
        # Fallback to first command if no match
        print(f"⚠️  LLM suggested '{response}' but not in admissible commands")
        return admissible_commands[0] if admissible_commands else "look"
        
    except Exception as e:
        print(f"⚠️  LLM call failed: {e}")
        return "look"


def play_game(game_file: str, max_steps: int = 50, verbose: bool = True) -> dict:
    """
    Play a TextWorld game using simple LLM reasoning.
    
    Returns:
        dict with success, steps, reward, actions
    """
    if verbose:
        print("\n" + "="*80)
        print("SIMPLE LLM PLAYER")
        print("="*80)
    
    # CRITICAL FIX: Configure environment to provide admissible commands!
    request_infos = textworld.EnvInfos(
        admissible_commands=True,  # Request actual commands, not templates
        objective=True,
        inventory=True,
        max_score=True
    )
    
    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()
    
    obs = game_state.feedback if hasattr(game_state, 'feedback') else str(game_state)
    quest = game_state.objective if hasattr(game_state, 'objective') else "Complete the game"
    
    if verbose:
        print(f"\n🎯 QUEST: {quest}")
        print(f"\n📍 STARTING OBSERVATION:\n{obs[:200]}...\n")
    
    total_reward = 0
    step = 0
    done = False
    actions_taken = []
    
    while not done and step < max_steps:
        step += 1
        
        # Get admissible commands - should work now with request_infos!
        admissible_commands = game_state.admissible_commands
        
        if not admissible_commands:
            admissible_commands = ['look', 'inventory']
            if verbose and step == 1:
                print(f"\n⚠️  WARNING: admissible_commands still None despite EnvInfos!")
        elif verbose and step == 1:
            print(f"\n✅ Got {len(admissible_commands)} admissible commands")
            print(f"   Sample: {admissible_commands[:5]}")
            
        if verbose:
            print(f"\n{'─'*80}")
            print(f"STEP {step}/{max_steps} | Reward: {total_reward:+.1f}")
            print(f"{'─'*80}")
        
        # Ask LLM what to do
        action = ask_llm(obs, quest, admissible_commands, step)
        
        if verbose:
            print(f"🤖 LLM chose: {action}")
        
        actions_taken.append(action)
        
        # Execute
        game_state, reward, done = env.step(action)
        obs = game_state.feedback if hasattr(game_state, 'feedback') else str(game_state)
        total_reward += reward
        
        if reward != 0 and verbose:
            print(f"   💰 Reward: {reward:+.1f}")
        
        if verbose and len(obs) < 300:
            print(f"   📝 {obs}")
    
    env.close()
    
    success = done and total_reward > 0
    
    if verbose:
        print("\n" + "="*80)
        print("EPISODE COMPLETE")
        print("="*80)
        print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Steps: {step}/{max_steps}")
        print(f"Reward: {total_reward:+.1f}")
        print(f"Actions: {len(actions_taken)}")
    
    return {
        'success': success,
        'steps': step,
        'reward': total_reward,
        'actions': actions_taken
    }


def run_baseline_test(n_episodes: int = 3):
    """Run baseline test with simple LLM player."""
    print("\n" + "🎯"*40)
    print("BASELINE TEST: Can We Win With Simple LLM?")
    print("🎯"*40)
    print("\nObjective: Establish if TextWorld games are solvable at all")
    print("Method: No framework, just LLM common sense")
    print(f"Episodes: {n_episodes}\n")
    
    # Create test game
    from environments.domain4_textworld.validate_planning import create_simple_game
    
    print("📦 Creating test game...")
    game_file = create_simple_game()
    print(f"   Game: {game_file}\n")
    
    results = []
    for i in range(1, n_episodes + 1):
        print(f"\n{'='*80}")
        print(f"EPISODE {i}/{n_episodes}")
        print(f"{'='*80}")
        
        result = play_game(game_file, max_steps=50, verbose=True)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("BASELINE SUMMARY")
    print("="*80)
    
    successes = sum(1 for r in results if r['success'])
    avg_steps = sum(r['steps'] for r in results) / len(results)
    avg_reward = sum(r['reward'] for r in results) / len(results)
    
    print(f"\nEpisodes: {n_episodes}")
    print(f"Successes: {successes}/{n_episodes} ({successes/n_episodes:.0%})")
    print(f"Average Steps: {avg_steps:.1f}")
    print(f"Average Reward: {avg_reward:+.2f}")
    
    print("\n" + "─"*80)
    print("INTERPRETATION:")
    print("─"*80)
    
    if successes > 0:
        print("✅ GAMES ARE SOLVABLE!")
        print("   → Simple LLM can win")
        print("   → Our complex architecture should do better")
        print("   → Need to debug why cognitive agent fails")
    else:
        print("❌ GAMES ARE HARD!")
        print("   → Even simple LLM can't win")
        print("   → May need better perception or different approach")
        print("   → Or games inherently difficult for LLM")
    
    print("\n" + "🎯"*40 + "\n")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple LLM baseline player")
    parser.add_argument('--episodes', type=int, default=3, help='Number of episodes')
    parser.add_argument('--game', type=str, help='Path to game file (optional)')
    
    args = parser.parse_args()
    
    if args.game:
        # Play specific game
        result = play_game(args.game, max_steps=50, verbose=True)
    else:
        # Run baseline test
        results = run_baseline_test(n_episodes=args.episodes)
