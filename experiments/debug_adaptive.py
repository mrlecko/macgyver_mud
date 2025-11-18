#!/usr/bin/env python3
"""
Debug why adaptive parameters don't work
"""
from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from graph_model import get_meta_params, get_recent_episodes_stats, get_agent

# Connect to Neo4j
driver = GraphDatabase.driver(
    config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)

with driver.session(database="neo4j") as session:
    # Reset
    session.run("""
        MATCH (stats:SkillStats)
        SET stats.total_uses = 0,
            stats.successful_episodes = 0,
            stats.failed_episodes = 0
    """)

    session.run("""
        MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
        SET meta.episodes_completed = 0,
            meta.beta = 6.0
    """)

    print("=" * 80)
    print("DEBUGGING ADAPTIVE PARAMETERS")
    print("=" * 80)

    agent_node = get_agent(session, config.AGENT_NAME)
    agent_id = agent_node["id"]

    print(f"\nInitial meta params:")
    meta = get_meta_params(session, agent_id)
    print(f"  Alpha: {meta['alpha']}")
    print(f"  Beta: {meta['beta']}")
    print(f"  Gamma: {meta['gamma']}")
    print(f"  Episodes: {meta['episodes']}")

    print(f"\nRunning 10 episodes with adaptive params enabled...")

    for i in range(10):
        agent = AgentRuntime(
            session,
            door_state="unlocked" if i % 2 == 0 else "locked",
            initial_belief=0.5,
            use_procedural_memory=True,
            adaptive_params=True
        )

        print(f"\n--- Episode {i+1} ---")
        print(f"Door state: {agent.door_state}")
        print(f"Agent episodes_completed (before): {agent.episodes_completed}")
        print(f"Agent beta (before): {agent.beta:.2f}")

        # Run episode
        agent.run_episode(max_steps=5)

        print(f"Steps taken: {agent.step_count}")
        print(f"Escaped: {agent.escaped}")
        print(f"Agent episodes_completed (after): {agent.episodes_completed}")
        print(f"Agent beta (after): {agent.beta:.2f}")

        # Check if adaptation triggered
        if agent.episodes_completed % 5 == 0:
            print(f"  🔄 Adaptation should have triggered!")
            recent = get_recent_episodes_stats(session, agent_id, limit=10)
            print(f"  Recent stats: avg_steps={recent['avg_steps']:.2f}, success_rate={recent['success_rate']:.1%}")

        # Check graph state
        meta = get_meta_params(session, agent_id)
        print(f"Graph beta: {meta['beta']:.2f}")
        print(f"Graph episodes: {meta['episodes']}")

    print(f"\n{'='*80}")
    print("FINAL STATE")
    print(f"{'='*80}\n")

    meta_final = get_meta_params(session, agent_id)
    print(f"Final beta: {meta_final['beta']:.2f}")
    print(f"Final episodes: {meta_final['episodes']}")
    print(f"Expected episodes: 10")

    if meta_final['beta'] != 6.0:
        print(f"\n✅ Beta changed (from 6.0 to {meta_final['beta']:.2f})")
    else:
        print(f"\n❌ Beta never changed (stayed at 6.0)")

driver.close()
