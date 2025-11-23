import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from memory.episodic_replay import EpisodicMemory
from memory.counterfactual_generator import CounterfactualGenerator
from environments.graph_labyrinth import GraphLabyrinth

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

@pytest.fixture
def episodic_memory(neo4j_session):
    """Provide an EpisodicMemory instance."""
    mem = EpisodicMemory(neo4j_session)
    # Clean up before each test
    mem.clear_all_episodes()
    return mem

@pytest.fixture
def labyrinth(neo4j_session):
    """Provide a simple labyrinth for testing."""
    lab = GraphLabyrinth(neo4j_session)
    lab.initialize_schema()
    lab.clear_labyrinth()
    lab.generate_linear_dungeon(num_rooms=5, seed=42)
    return lab

def test_store_and_retrieve_episode(episodic_memory, neo4j_session):
    """Test storing and retrieving an episodic path."""
    episode_id = "test_episode_001"
    actual_path = {
        'path_id': 'actual_001',
        'rooms_visited': ['start', 'room_1', 'room_2', 'exit'],
        'actions_taken': ['move', 'move', 'move'],
        'outcome': 'success',
        'steps': 3,
        'final_distance': 0
    }
    
    # Store
    episodic_memory.store_actual_path(episode_id, actual_path)
    
    # Retrieve
    retrieved = episodic_memory.get_episode(episode_id)
    
    assert retrieved is not None
    assert retrieved['actual_path']['outcome'] == 'success'
    assert len(retrieved['actual_path']['rooms_visited']) == 4

def test_store_counterfactuals(episodic_memory):
    """Test storing multiple counterfactual paths."""
    episode_id = "test_episode_002"
    
    actual = {
        'path_id': 'actual_002',
        'rooms_visited': ['start', 'room_1', 'exit'],
        'actions_taken': ['move', 'move'],
        'outcome': 'success',
        'steps': 2,
        'final_distance': 0
    }
    
    counterfactuals = [
        {
            'path_id': 'cf_002_1',
            'rooms_visited': ['start', 'room_2', 'dead_end'],
            'actions_taken': ['move', 'move'],
            'outcome': 'failure',
            'steps': 2,
            'final_distance': 10,
            'divergence_point': 0
        },
        {
            'path_id': 'cf_002_2',
            'rooms_visited': ['start', 'room_1', 'room_3', 'exit'],
            'actions_taken': ['move', 'move', 'move'],
            'outcome': 'success',
            'steps': 3,
            'final_distance': 0,
            'divergence_point': 1
        }
    ]
    
    episodic_memory.store_actual_path(episode_id, actual)
    episodic_memory.store_counterfactuals(episode_id, counterfactuals)
    
    retrieved = episodic_memory.get_episode(episode_id)
    
    assert len(retrieved['counterfactuals']) == 2
    assert retrieved['counterfactuals'][0]['divergence_point'] == 0

def test_regret_calculation(episodic_memory):
    """Test regret calculation between actual and counterfactual."""
    actual_outcome = {'steps': 5, 'outcome': 'success'}
    cf_outcome = {'steps': 3, 'outcome': 'success'}
    
    regret = episodic_memory.calculate_regret(actual_outcome, cf_outcome)
    
    # Regret = (actual_steps - cf_steps) = 5 - 3 = 2
    assert regret == 2

def test_counterfactual_generation(labyrinth, neo4j_session):
    """Test generating counterfactual paths from actual path."""
    generator = CounterfactualGenerator(neo4j_session, labyrinth)
    
    actual_path = {
        'rooms_visited': ['start', 'room_1', 'exit'],
        'actions_taken': ['move', 'move']
    }
    
    counterfactuals = generator.generate_alternatives(actual_path, max_alternates=3)
    
    assert len(counterfactuals) <= 3
    assert all('divergence_point' in cf for cf in counterfactuals)
    
def test_offline_learning_improves_performance(episodic_memory, labyrinth):
    """
    Test that replaying episodes leads to improved performance.
    
    This is a mock test - in reality, we'd run actual episodes and measure improvement.
    """
    # Store a "bad" episode
    bad_episode = {
        'path_id': 'bad_001',
        'rooms_visited': ['start', 'room_1', 'room_2', 'room_3', 'exit'],
        'actions_taken': ['move'] * 4,
        'outcome': 'success',
        'steps': 4,
        'final_distance': 0
    }
    
    # Store a "good" counterfactual
    good_cf = {
        'path_id': 'good_001',
        'rooms_visited': ['start', 'room_1', 'exit'],
        'actions_taken': ['move'] * 2,
        'outcome': 'success',
        'steps': 2,
        'final_distance': 0,
        'divergence_point': 1
    }
    
    episodic_memory.store_actual_path('learn_episode', bad_episode)
    episodic_memory.store_counterfactuals('learn_episode', [good_cf])
    
    # Calculate insight
    regret = episodic_memory.calculate_regret(
        {'steps': bad_episode['steps']},
        {'steps': good_cf['steps']}
    )
    
    # Agent should learn that shorter path exists
    assert regret > 0  # There was a better option

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
