#!/usr/bin/env python3
"""
Comprehensive Episode Generator - Geometric Lens Analysis

Generates episodes with crisp, balanced, and hybrid skill modes to
enable trajectory analysis with actual k-value variation.

Previous limitation: All episodes used crisp skills (k≈0 constantly).
This tool addresses that gap.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import os
import numpy as np
from agent_runtime import AgentRuntime


def generate_episodes_by_mode(session, n_episodes_per_mode=20, max_steps=10):
    """
    Generate episodes for each skill mode.

    Args:
        session: Neo4j session
        n_episodes_per_mode: Number of episodes per mode
        max_steps: Max steps per episode

    Returns:
        Dictionary with episode counts by mode
    """
    modes = ['crisp', 'balanced', 'hybrid']
    results = {mode: [] for mode in modes}

    for mode in modes:
        print(f"\nGenerating {n_episodes_per_mode} episodes with {mode} skills...")
        print("-" * 60)

        for i in range(n_episodes_per_mode):
            # Vary parameters for diversity
            initial_belief = np.random.uniform(0.1, 0.9)
            door_state = np.random.choice(['locked', 'unlocked'])

            try:
                runtime = AgentRuntime(
                    session=session,
                    door_state=door_state,
                    initial_belief=initial_belief,
                    skill_mode=mode,
                    use_procedural_memory=False,
                    adaptive_params=False
                )

                episode_id = runtime.run_episode(max_steps=max_steps)

                # Get outcome
                query = """
                MATCH (e:Episode {id: $episode_id})-[:HAS_STEP]->(s:Step)
                RETURN count(s) AS steps,
                       any(s IN collect(s) WHERE s.observation = 'escaped') AS success
                """
                result = session.run(query, episode_id=episode_id).single()

                results[mode].append({
                    'episode_id': episode_id,
                    'door_state': door_state,
                    'initial_belief': initial_belief,
                    'steps': result['steps'] if result else 0,
                    'success': result['success'] if result else False
                })

                if (i + 1) % 5 == 0:
                    print(f"  {mode}: {i+1}/{n_episodes_per_mode} episodes")

            except Exception as e:
                print(f"  ⚠ Episode {i+1} ({mode}) failed: {e}")

    return results


def print_summary(results):
    """Print comprehensive summary of generated episodes."""
    print("\n" + "=" * 70)
    print("EPISODE GENERATION SUMMARY")
    print("=" * 70)

    total_episodes = sum(len(episodes) for episodes in results.values())
    print(f"\nTotal episodes generated: {total_episodes}")

    for mode in ['crisp', 'balanced', 'hybrid']:
        episodes = results[mode]
        if not episodes:
            continue

        print(f"\n{mode.upper()} MODE ({len(episodes)} episodes):")
        print("-" * 60)

        steps = [e['steps'] for e in episodes]
        successes = [e for e in episodes if e['success']]

        print(f"  Steps: mean={np.mean(steps):.2f}, median={np.median(steps):.0f}, "
              f"min={min(steps)}, max={max(steps)}")
        print(f"  Success rate: {len(successes)}/{len(episodes)} ({100*len(successes)/len(episodes):.1f}%)")

        door_locked = sum(1 for e in episodes if e['door_state'] == 'locked')
        print(f"  Door states: locked={door_locked}, unlocked={len(episodes)-door_locked}")

    print("\n" + "=" * 70)
    print("✓ Comprehensive dataset ready for geometric analysis")
    print("  - Run k_trajectory_analyzer.py to see temporal patterns")
    print("  - Run k_correlation_analyzer.py to test relationships")
    print("  - Compare crisp vs balanced vs hybrid episodes")
    print("=" * 70)


def main():
    """Generate comprehensive episode dataset."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate episodes across all skill modes for geometric analysis'
    )
    parser.add_argument('-n', '--episodes-per-mode', type=int, default=20,
                       help='Episodes per mode (default: 20)')
    parser.add_argument('--max-steps', type=int, default=10,
                       help='Max steps per episode (default: 10)')

    args = parser.parse_args()

    # Connect to Neo4j
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session(database="neo4j") as session:
            print("=" * 70)
            print("COMPREHENSIVE EPISODE GENERATOR - GEOMETRIC LENS")
            print("=" * 70)
            print("\nGenerating episodes with crisp, balanced, and hybrid skills")
            print("This enables trajectory analysis with actual k-value variation.")

            results = generate_episodes_by_mode(
                session,
                n_episodes_per_mode=args.episodes_per_mode,
                max_steps=args.max_steps
            )

            print_summary(results)

    finally:
        driver.close()


if __name__ == '__main__':
    main()
