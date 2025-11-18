#!/usr/bin/env python3
"""Quick test of strategic mode only"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from neo4j import GraphDatabase
from agent_runtime import AgentRuntime
import config as base_config
import importlib

# Set strategic mode
os.environ["REWARD_MODE"] = "strategic"
import config
importlib.reload(config)

print(f"SLOW_PENALTY in strategic mode: {config.SLOW_PENALTY}")

driver = GraphDatabase.driver(
    base_config.NEO4J_URI,
    auth=(base_config.NEO4J_USER, base_config.NEO4J_PASSWORD)
)

with driver.session(database="neo4j") as session:
    # Reset
    session.run("""
        MATCH (stats:SkillStats)
        SET stats.total_uses = 0, stats.successful_episodes = 0,
            stats.failed_episodes = 0, stats.uncertain_uses = 0,
            stats.uncertain_successes = 0
    """)

    print("\nRunning 30 episodes with strategic mode (SLOW_PENALTY=6.0)...")

    for i in range(30):
        agent = AgentRuntime(
            session,
            door_state="unlocked" if i % 2 == 0 else "locked",
            initial_belief=0.5,
            use_procedural_memory=True
        )
        agent.run_episode(max_steps=5)

        trace = agent.get_trace()
        skills = [step["skill"] for step in trace]

        if i >= 20:  # Show last 10 episodes
            print(f"  Ep{i+1:2d} ({'unlocked' if i%2==0 else 'locked  '}): {' → '.join(skills):40s} ({agent.step_count} steps, escaped={agent.escaped})")

    # Check skill usage
    print("\nFinal skill stats:")
    from graph_model import get_skill_stats
    for skill in ["peek_door", "try_door", "go_window"]:
        stats = get_skill_stats(session, skill)
        print(f"  {skill:15s}: {stats['overall']['uses']:3d} uses, {stats['overall']['success_rate']:5.1%} success")

driver.close()
