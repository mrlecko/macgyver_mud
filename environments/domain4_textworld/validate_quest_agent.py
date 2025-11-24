#!/usr/bin/env python3
"""
Validate Quest Agent on generated TextWorld games.

Tests the quest agent against randomly generated games to measure:
- Success rate
- Steps to completion
- Robustness across different quests
"""
import sys
sys.path.insert(0, '/home/juancho/macgyver_mud')

import textworld
from environments.domain4_textworld.quest_agent import QuestAgent
from environments.domain4_textworld.validate_planning import create_simple_game


def run_episode(agent: QuestAgent, game_file: str, max_steps: int = 30, verbose: bool = False) -> dict:
    """
    Run one episode with quest agent.

    Args:
        agent: QuestAgent instance
        game_file: Path to TextWorld game file
        max_steps: Maximum steps allowed
        verbose: Print detailed output

    Returns:
        Dict with episode results
    """
    # Setup environment
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )

    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()

    # Reset agent
    quest = game_state.objective
    agent.reset(quest)

    # Run episode
    step = 0
    total_reward = 0.0
    done = False

    if verbose:
        print(f"\n{'=' * 70}")
        print(f"EPISODE START")
        print(f"{'=' * 70}")
        print(f"🎯 Quest: {quest[:60]}...")
        print()

    while not done and step < max_steps:
        step += 1

        # Get reward (0.0 on first step)
        current_reward = 0.0
        if step > 1 and hasattr(game_state, 'reward') and game_state.reward is not None:
            current_reward = game_state.reward

        # Agent step
        action = agent.step(
            observation=game_state.feedback,
            reward=current_reward,
            admissible_commands=game_state.admissible_commands
        )

        # Environment step
        game_state, reward, done = env.step(action)
        total_reward += reward

        if verbose and reward != 0:
            print(f"   💰 Reward: {reward:+.1f} (total: {total_reward:+.1f})")

    env.close()

    success = done and total_reward > 0

    if verbose:
        print(f"\n{'=' * 70}")
        print(f"EPISODE COMPLETE")
        print(f"{'=' * 70}")
        print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Steps: {step}/{max_steps}")
        print(f"Reward: {total_reward:+.1f}")
        print(f"{'=' * 70}\n")

    return {
        'success': success,
        'steps': step,
        'reward': total_reward,
        'done': done
    }


def validate_on_random_games(n_games: int = 10, verbose: bool = False):
    """
    Validate quest agent on multiple randomly generated games.

    Args:
        n_games: Number of games to test
        verbose: Print detailed output for each game
    """
    print("\n" + "🎯" * 40)
    print("QUEST AGENT VALIDATION")
    print("🎯" * 40)
    print(f"\nTesting on {n_games} randomly generated TextWorld games")
    print(f"Goal: Measure success rate and robustness\n")

    agent = QuestAgent(verbose=verbose)
    results = []

    for i in range(n_games):
        print(f"\n{'─' * 70}")
        print(f"GAME {i + 1}/{n_games}")
        print(f"{'─' * 70}")

        # Generate game
        game_file = create_simple_game()
        print(f"Generated: {game_file}")

        # Run episode
        result = run_episode(agent, game_file, max_steps=30, verbose=verbose)
        results.append(result)

        # Summary
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"{status} - {result['steps']} steps, {result['reward']:+.1f} reward")

    # Calculate statistics
    successes = sum(r['success'] for r in results)
    success_rate = successes / n_games
    avg_steps = sum(r['steps'] for r in results) / n_games
    avg_reward = sum(r['reward'] for r in results) / n_games

    successful_episodes = [r for r in results if r['success']]
    avg_successful_steps = sum(r['steps'] for r in successful_episodes) / len(successful_episodes) if successful_episodes else 0

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\nGames Played: {n_games}")
    print(f"Successes: {successes}/{n_games}")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"\nPerformance:")
    print(f"  Average Steps (all): {avg_steps:.1f}")
    print(f"  Average Steps (successful): {avg_successful_steps:.1f}")
    print(f"  Average Reward: {avg_reward:+.2f}")

    print("\n" + "─" * 70)
    print("INTERPRETATION:")
    print("─" * 70)

    if success_rate >= 0.8:
        print("✅ EXCELLENT: Quest agent performs well!")
        print("   → Success rate ≥ 80%")
        print("   → Ready for comparison with baseline agents")
    elif success_rate >= 0.6:
        print("⚠️  GOOD: Quest agent works, but has room for improvement")
        print(f"   → Success rate: {success_rate:.0%}")
        print("   → May need tuning for edge cases")
    elif success_rate >= 0.4:
        print("⚠️  FAIR: Quest agent needs improvement")
        print(f"   → Success rate: {success_rate:.0%}")
        print("   → Check decomposer and matcher logic")
    else:
        print("❌ POOR: Quest agent not working as expected")
        print(f"   → Success rate: {success_rate:.0%}")
        print("   → Needs debugging")

    print("\n" + "🎯" * 40 + "\n")

    return {
        'n_games': n_games,
        'success_rate': success_rate,
        'avg_steps': avg_steps,
        'avg_reward': avg_reward,
        'results': results
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate Quest Agent")
    parser.add_argument('--games', type=int, default=10, help='Number of games to test')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    validate_on_random_games(n_games=args.games, verbose=args.verbose)
