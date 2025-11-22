#!/usr/bin/env python3
"""
Episode Generator - Create dataset for geometric analysis.

Runs multiple episodes to populate Neo4j with k-trajectory data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import os
import numpy as np
from agent_runtime import AgentRuntime


def generate_episodes(n_episodes=50, vary_initial_belief=True, vary_door_state=True):
    """Generate multiple episodes with varied parameters."""

    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')

    driver = GraphDatabase.driver(uri, auth=(user, password))

    print(f"Generating {n_episodes} episodes...")
    print("="*60)

    results = []

    try:
        with driver.session(database="neo4j") as session:
            for i in range(n_episodes):
                # Vary parameters
                if vary_initial_belief:
                    initial_belief = np.random.uniform(0.1, 0.9)
                else:
                    initial_belief = 0.5

                if vary_door_state:
                    door_state = np.random.choice(['locked', 'unlocked'])
                else:
                    door_state = 'locked'

                # Run episode
                runtime = AgentRuntime(
                    session=session,
                    door_state=door_state,
                    initial_belief=initial_belief,
                    skill_mode='crisp',  # Use crisp for consistent analysis
                    use_procedural_memory=False,
                    adaptive_params=False
                )

                try:
                    episode_id = runtime.run_episode(max_steps=5)

                    # Get episode outcome
                    query = """
                    MATCH (e:Episode {id: $episode_id})-[:HAS_STEP]->(s:Step)
                    RETURN count(s) AS steps, max(s.step_index) AS final_step
                    """
                    result = session.run(query, episode_id=episode_id).single()

                    results.append({
                        'episode_id': episode_id,
                        'door_state': door_state,
                        'initial_belief': initial_belief,
                        'steps': result['steps'] if result else 0
                    })

                    if (i + 1) % 10 == 0:
                        print(f"  Generated {i+1}/{n_episodes} episodes...")

                except Exception as e:
                    print(f"  ⚠ Episode {i+1} failed: {e}")

    finally:
        driver.close()

    print("="*60)
    print(f"✓ Generated {len(results)} episodes successfully")

    # Summary statistics
    steps = [r['steps'] for r in results]
    print(f"\nEpisode statistics:")
    print(f"  Mean steps: {np.mean(steps):.2f}")
    print(f"  Median steps: {np.median(steps):.0f}")
    print(f"  Min steps: {min(steps)}")
    print(f"  Max steps: {max(steps)}")

    door_states = [r['door_state'] for r in results]
    print(f"\nDoor state distribution:")
    print(f"  Locked: {door_states.count('locked')}")
    print(f"  Unlocked: {door_states.count('unlocked')}")

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate episodes for geometric analysis')
    parser.add_argument('-n', '--num-episodes', type=int, default=50,
                       help='Number of episodes to generate')
    parser.add_argument('--fixed-belief', action='store_true',
                       help='Use fixed initial belief (0.5) instead of random')
    parser.add_argument('--fixed-door', action='store_true',
                       help='Always use locked door instead of random')

    args = parser.parse_args()

    generate_episodes(
        n_episodes=args.num_episodes,
        vary_initial_belief=not args.fixed_belief,
        vary_door_state=not args.fixed_door
    )
