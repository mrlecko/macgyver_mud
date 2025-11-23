"""Quick test to debug path tracking"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from memory.episodic_replay import EpisodicMemory

config.ENABLE_EPISODIC_MEMORY = True

driver = GraphDatabase.driver(
    config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)
session = driver.session(database="neo4j")

try:
    # Clean memory
    mem = EpisodicMemory(session)
    mem.clear_all_episodes()
    
    # Create runtime and run episode
    runtime = AgentRuntime(session, "unlocked", 0.5)
    
    print("Before episode:")
    print(f"  current_episode_path: {runtime.current_episode_path}")
    
    episode_id = runtime.run_episode(max_steps=5)
    
    print(f"\nAfter episode (ID: {episode_id}):")
    print(f"  Steps taken: {runtime.step_count}")
    print(f"  Escaped: {runtime.escaped}")
    print(f"  Path length: {len(runtime.current_episode_path)}")
    print(f"  Path: {runtime.current_episode_path}")
    
    # Check what was stored
    episode = mem.get_episode(episode_id)
    if episode:
        print(f"\nStored in memory:")
        print(f"  Episode found: Yes")
        print(f"  Actual path: {episode.get('actual_path', {})}")
    else:
        print(f"\nStored in memory: Episode NOT found!")
        
finally:
    session.close()
    driver.close()
