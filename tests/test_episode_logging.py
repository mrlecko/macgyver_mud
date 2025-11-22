#!/usr/bin/env python3
"""
Test episode logging to verify steps persist correctly.
"""
from neo4j import GraphDatabase
from agent_runtime import AgentRuntime
import config

def test_episode_logging():
    """Test single episode with each skill mode."""

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    try:
        with driver.session(database="neo4j") as session:
            print("=" * 70)
            print("TESTING EPISODE LOGGING")
            print("=" * 70)

            modes = ['crisp', 'balanced', 'hybrid']

            for mode in modes:
                print(f"\n{mode.upper()} MODE TEST:")
                print("-" * 60)

                runtime = AgentRuntime(
                    session=session,
                    door_state='locked',
                    initial_belief=0.5,
                    skill_mode=mode
                )

                episode_id = runtime.run_episode(max_steps=8)

                # Check episode in database
                result = session.run('''
                    MATCH (e:Episode {id: $episode_id})-[:HAS_STEP]->(s:Step)
                    RETURN count(s) AS step_count,
                           collect(s.skill_name) AS skills_used
                ''', episode_id=episode_id).single()

                steps_in_db = result['step_count']
                skills_used = result['skills_used']

                print(f"  Episode ID: {episode_id}")
                print(f"  Steps taken (runtime): {runtime.step_count}")
                print(f"  Steps in database: {steps_in_db}")
                print(f"  Skills used: {', '.join(skills_used) if skills_used else 'none'}")
                print(f"  Escaped: {runtime.escaped}")

                if steps_in_db == runtime.step_count:
                    print(f"  ✓ Logging working correctly")
                else:
                    print(f"  ✗ Mismatch: {runtime.step_count} runtime vs {steps_in_db} database")

            print("\n" + "=" * 70)
            print("EPISODE LOGGING TEST COMPLETE")
            print("=" * 70)

    finally:
        driver.close()

if __name__ == '__main__':
    test_episode_logging()
