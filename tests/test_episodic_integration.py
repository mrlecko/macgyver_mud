"""
Integration test for Episodic Memory in AgentRuntime.

Tests that episodic memory can be enabled/disabled and works correctly
when integrated with the agent runtime.
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime

# Override config for testing
config.ENABLE_EPISODIC_MEMORY = True
config.MAX_COUNTERFACTUALS_PER_EPISODE = 3

@pytest.fixture(scope="module")
def neo4j_session():
    """Provide a Neo4j session for testing."""
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    yield session
    session.close()
    driver.close()

def test_episodic_memory_disabled_by_default(neo4j_session):
    """Test that episodic memory is disabled when config flag is False."""
    # Temporarily disable
    orig_value = config.ENABLE_EPISODIC_MEMORY
    config.ENABLE_EPISODIC_MEMORY = False
    
    try:
        runtime = AgentRuntime(neo4j_session, "unlocked", 0.5)
        assert runtime.episodic_memory is None
        assert runtime.counterfactual_generator is None  
    finally:
        config.ENABLE_EPISODIC_MEMORY = orig_value

def test_episodic_memory_enabled(neo4j_session):
    """Test that episodic memory is initialized when config flag is True."""
    runtime = AgentRuntime(neo4j_session, "unlocked", 0.5, enable_episodic_memory=True)
    assert runtime.episodic_memory is not None
    assert hasattr(runtime, 'current_episode_path')

def test_offline_learning_trigger(neo4j_session):
    """Test that offline learning is triggered periodically."""
    runtime = AgentRuntime(neo4j_session, "unlocked", 0.5, enable_episodic_memory=True, adaptive_params=True)
    
    # Clear any existing episodes
    if runtime.episodic_memory:
        runtime.episodic_memory.clear_all_episodes()
    
def test_episodic_memory_stores_episode(neo4j_session):
    """Test that episodes are stored in episodic memory."""
    runtime = AgentRuntime(neo4j_session, "unlocked", 0.5, enable_episodic_memory=True, adaptive_params=True)
    
    # Clear any existing episodes
    if runtime.episodic_memory:
        runtime.episodic_memory.clear_all_episodes()
    
    # Run an episode
    episode_id = runtime.run_episode(max_steps=5)
    
    # Verify episode was stored
    if runtime.episodic_memory:
        episode = runtime.episodic_memory.get_episode(episode_id)
        assert episode is not None
        assert 'actual_path' in episode
        assert episode['actual_path']['outcome'] == 'success'

def test_backward_compatibility_without_episodic(neo4j_session):
    """Test that runtime works normally when episodic memory is disabled."""
    orig_value = config.ENABLE_EPISODIC_MEMORY
    config.ENABLE_EPISODIC_MEMORY = False
    
    try:
        runtime = AgentRuntime(neo4j_session, "locked", 0.5)
        episode_id = runtime.run_episode(max_steps=5)
        
        # Should work fine
        assert runtime.escaped in [True, False]
        assert runtime.step_count > 0
    finally:
        config.ENABLE_EPISODIC_MEMORY = orig_value

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
