"""
Diagnostic test to verify episodic memory storage and retrieval.
"""
import pytest
import config
from agent_runtime import AgentRuntime
from memory.episodic_replay import EpisodicMemory
from neo4j import GraphDatabase

# Enable episodic memory
config.ENABLE_EPISODIC_MEMORY = True
config.EPISODIC_UPDATE_SKILL_PRIORS = True

@pytest.fixture(scope="module")
def neo4j_session():
    """Provide a Neo4j session for testing."""
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    # Clean up
    session.run("MATCH (e:EpisodicMemory) DETACH DELETE e")
    session.run("MATCH (p:EpisodicPath) DELETE p")
    yield session
    session.close()
    driver.close()

def test_counterfactual_storage_retrieval(neo4j_session):
    """
    Diagnostic: Can we store and retrieve a counterfactual?
    """
    memory = EpisodicMemory(neo4j_session)

    # Create a simple episode
    episode_id = "test_episode_001"

    # Store actual path (belief trajectory)
    import json
    actual_path = {
        'path_id': f'actual_{episode_id}',
        'path_data': json.dumps([
            {'belief': 0.5, 'skill': 'peek_door'},
            {'belief': 0.15, 'skill': 'try_door'},
        ]),
        'state_type': 'belief_trajectory',
        'outcome': 'success',
        'steps': 2
    }

    memory.store_actual_path(episode_id, actual_path)

    # Store a counterfactual
    counterfactuals = [{
        'path_id': f'cf_{episode_id}_0',
        'path_data': json.dumps([
            {'belief': 0.5, 'skill': 'go_window'},
        ]),
        'state_type': 'belief_trajectory',
        'outcome': 'failure',
        'steps': 5,
        'divergence_point': 0
    }]

    memory.store_counterfactuals(episode_id, counterfactuals)

    # Retrieve the episode
    episode = memory.get_episode(episode_id)

    print(f"\nDEBUG: Episode retrieved: {episode is not None}")
    if episode:
        print(f"DEBUG: Actual path: {episode.get('actual_path', {}).get('path_id')}")
        print(f"DEBUG: Counterfactuals count: {len(episode.get('counterfactuals', []))}")
        if episode.get('counterfactuals'):
            for cf in episode['counterfactuals']:
                print(f"DEBUG: CF: {cf.get('path_id')}, divergence={cf.get('divergence_point')}")

    assert episode is not None, "Episode should be retrievable"
    assert episode['actual_path'] is not None, "Should have actual path"
    assert len(episode['counterfactuals']) > 0, "Should have at least one counterfactual"
    assert episode['counterfactuals'][0]['divergence_point'] == 0, "Should have divergence point"
