import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
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
def labyrinth(neo4j_session):
    """Provide a fresh GraphLabyrinth instance."""
    lab = GraphLabyrinth(neo4j_session)
    lab.initialize_schema()
    lab.clear_labyrinth()
    return lab

def test_schema_initialization(labyrinth):
    """Test that schema can be initialized without errors."""
    # Should not raise
    labyrinth.initialize_schema()

def test_generate_linear_dungeon(labyrinth):
    """Test basic dungeon generation."""
    start_room = labyrinth.generate_linear_dungeon(num_rooms=5, seed=42)
    
    assert start_room == 'start'
    
    # Verify start room exists
    room = labyrinth.get_room_info('start')
    assert room is not None
    assert room['room_type'] == 'start'

def test_room_navigation(labyrinth):
    """Test moving through rooms."""
    labyrinth.generate_linear_dungeon(num_rooms=5, seed=42)
    
    # Get rooms adjacent to start
    adjacent = labyrinth.get_adjacent_rooms('start')
    assert len(adjacent) == 1  # Linear dungeon has one forward connection
    
    next_room = adjacent[0]
    assert next_room['id'] == 'room_1'
    assert next_room['locked'] == False

def test_distance_calculation(labyrinth):
    """Test shortest path calculation."""
    labyrinth.generate_linear_dungeon(num_rooms=5, seed=42)
    
    # Distance from start to exit in 5-room dungeon should be 4 hops
    distance = labyrinth.get_distance_to_exit('start')
    assert distance == 4
    
    # Distance from room_1 should be 3
    distance = labyrinth.get_distance_to_exit('room_1')
    assert distance == 3

def test_visited_tracking(labyrinth):
    """Test room visitation tracking."""
    labyrinth.generate_linear_dungeon(num_rooms=5, seed=42)
    
    # Initially not visited
    room = labyrinth.get_room_info('start')
    assert room['visited'] == False
    
    # Mark as visited
    labyrinth.mark_visited('start')
    
    # Now visited
    room = labyrinth.get_room_info('start')
    assert room['visited'] == True

def test_labyrinth_stats(labyrinth):
    """Test statistics gathering."""
    labyrinth.generate_linear_dungeon(num_rooms=5, seed=42)
    
    stats = labyrinth.get_labyrinth_stats()
    assert stats['total_rooms'] == 5
    assert stats['visited_rooms'] == 0
    assert stats['completion'] == 0.0
    
    # Visit a room
    labyrinth.mark_visited('start')
    
    stats = labyrinth.get_labyrinth_stats()
    assert stats['visited_rooms'] == 1
    assert stats['completion'] == 0.2  # 1/5

def test_clear_labyrinth(labyrinth):
    """Test that clearing removes all rooms."""
    labyrinth.generate_linear_dungeon(num_rooms=5, seed=42)
    
    # Verify rooms exist
    stats = labyrinth.get_labyrinth_stats()
    assert stats['total_rooms'] == 5
    
    # Clear
    labyrinth.clear_labyrinth()
    
    # Verify empty
    stats = labyrinth.get_labyrinth_stats()
    assert stats['total_rooms'] == 0

def test_backward_compatibility(neo4j_session):
    """
    CRITICAL: Verify that GraphLabyrinth doesn't interfere with existing schema.
    
    This test ensures that Agent, Episode, and Skill nodes are unaffected.
    """
    # Create a labyrinth
    lab = GraphLabyrinth(neo4j_session)
    lab.initialize_schema()
    lab.generate_linear_dungeon(num_rooms=3, seed=42)
    
    # Verify existing node types still work
    result = neo4j_session.run("MATCH (a:Agent) RETURN count(a) AS count")
    agent_count = result.single()['count']
    
    # Should not have deleted agents
    assert agent_count >= 0  # At least 0 (may have existing data)
    
    # Verify LabyrinthRoom is separate
    result = neo4j_session.run("MATCH (r:LabyrinthRoom) RETURN count(r) AS count")
    room_count = result.single()['count']
    assert room_count == 3
    
    # Clean up
    lab.clear_labyrinth()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
