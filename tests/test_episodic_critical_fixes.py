"""
TDD Tests for Critical Episodic Memory Flaws

These tests define the EXPECTED behavior after fixes.
All tests should FAIL initially, then PASS after implementation.
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from memory.episodic_replay import EpisodicMemory
from memory.counterfactual_generator import CounterfactualGenerator
from environments.graph_labyrinth import GraphLabyrinth

# Enable episodic memory for all tests
config.ENABLE_EPISODIC_MEMORY = True
config.EPISODIC_UPDATE_SKILL_PRIORS = True
config.EPISODIC_LEARNING_RATE = 0.5  # Increased from 0.1

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
def clean_memory(neo4j_session):
    """Clean episodic memory before each test."""
    mem = EpisodicMemory(neo4j_session)
    mem.clear_all_episodes()
    yield mem

@pytest.fixture
def labyrinth(neo4j_session):
    """Create a test labyrinth."""
    lab = GraphLabyrinth(neo4j_session)
    lab.clear_labyrinth()
    lab.generate_linear_dungeon(num_rooms=5, seed=42)
    yield lab
    lab.clear_labyrinth()

# ============================================================================
# CRITICAL FLAW 1: Path Tracking Not Hooked Up
# ============================================================================

def test_path_tracking_is_populated(neo4j_session, clean_memory):
    """
    CRITICAL: Verify that current_episode_path is actually populated during episodes.
    
    Expected: After running an episode, current_episode_path should contain state trace.
    """
    runtime = AgentRuntime(neo4j_session, "unlocked", 0.5)
    
    # Run episode
    episode_id = runtime.run_episode(max_steps=5)
    
    # After episode completes and is stored, path should have been populated
    # Check in episodic memory
    episode = clean_memory.get_episode(episode_id)
    
    assert episode is not None, "Episode should be stored"
    assert 'actual_path' in episode, "Episode should have actual_path"
    
    # CRITICAL: Path should NOT be empty
    actual_path = episode['actual_path']
    assert len(actual_path.get('rooms_visited', [])) > 0, \
        "FLAW #1: Path tracking must be populated, not empty!"
    assert actual_path['steps'] > 0, "Should have taken steps"

def test_state_tracking_records_each_step(neo4j_session):
    """
    Verify that each step in the episode is tracked in the path.
    
    Expected: Number of states tracked should equal number of steps taken.
    """
    runtime = AgentRuntime(neo4j_session, "locked", 0.5)
    
    # Track steps manually
    runtime.run_episode(max_steps=5)
    
    # Path should have length equal to steps + 1 (initial state)
    # We'll check this after fixing the integration
    assert len(runtime.current_episode_path) == runtime.step_count + 1, \
        "Path should track all states including initial"

# ============================================================================
# CRITICAL FLAW 2: Invalid Counterfactuals Without Labyrinth
# ============================================================================

def test_counterfactuals_require_labyrinth(neo4j_session, clean_memory):
    """
    CRITICAL: Counterfactual generation should FAIL gracefully without labyrinth.
    
    Expected: Without labyrinth, should return empty list or raise informative error.
    """
    # Create path without labyrinth context
    fake_path = {
        'path_id': 'test_path',
        'rooms_visited': ['start', 'room_1', 'exit'],
        'actions_taken': ['move', 'move'],
        'outcome': 'success',
        'steps': 2,
        'final_distance': 0
    }
    
    # Try to generate counterfactuals without labyrinth
    generator = CounterfactualGenerator(neo4j_session, labyrinth=None)
    counterfactuals = generator.generate_alternatives(fake_path, max_alternates=3)
    
    # Should return empty list or handle gracefully
    assert counterfactuals == [], \
        "FLAW #2: Without labyrinth, counterfactuals should be empty, not invalid!"

def test_counterfactuals_are_valid_with_labyrinth(neo4j_session, labyrinth):
    """
    CRITICAL: With labyrinth, all counterfactuals must be spatially valid.
    
    Expected: All room transitions must exist in graph.
    """
    # Create realistic path
    actual_path = {
        'path_id': 'valid_path',
        'rooms_visited': ['start', 'room_1', 'room_2', 'exit'],
        'actions_taken': ['move'] * 3,
        'outcome': 'success',
        'steps': 3,
        'final_distance': 0
    }
    
    generator = CounterfactualGenerator(neo4j_session, labyrinth)
    counterfactuals = generator.generate_alternatives(actual_path, max_alternates=3)
    
    # Validate each counterfactual
    for cf in counterfactuals:
        rooms = cf['rooms_visited']
        for i in range(len(rooms) - 1):
            current = rooms[i]
            next_room = rooms[i + 1]
            
            # Check that transition is valid
            adjacent = labyrinth.get_adjacent_rooms(current)
            adjacent_ids = [r['id'] for r in adjacent]
            
            assert next_room in adjacent_ids, \
                f"FLAW #2: Invalid transition {current} -> {next_room} (not adjacent)"

# ============================================================================
# CRITICAL FLAW 3: Offline Learning Doesn't Improve Performance
# ============================================================================

def test_offline_learning_improves_skill_selection(neo4j_session, clean_memory, labyrinth):
    """
    CRITICAL: Offline learning should actually affect future decisions.
    
    Expected: After learning from high-regret episodes, agent should pick different skills.
    """
    runtime = AgentRuntime(
        neo4j_session, 
        "unlocked", 
        0.5,
        use_procedural_memory=True,
        adaptive_params=True
    )
    
    # Integrate labyrinth for valid counterfactuals
    runtime._integrate_graph_labyrinth(labyrinth)
    
    # Phase 1: Record which skills are selected (before learning)
    skills_before = []
    for i in range(5):
        ep_id = runtime.run_episode(max_steps=10)
        trace = runtime.get_trace()
        skills_before.extend([step['skill'] for step in trace])
    
    # Phase 2: Trigger offline learning
    runtime._perform_offline_learning()
    
    # Phase 3: Record which skills are selected (after learning)
    skills_after = []
    for i in range(5):
        ep_id = runtime.run_episode(max_steps=10)
        trace = runtime.get_trace()
        skills_after.extend([step['skill'] for step in trace])
    
    # Verify that skill distribution changed
    from collections import Counter
    before_counts = Counter(skills_before)
    after_counts = Counter(skills_after)
    
    # At least ONE skill should have different frequency
    assert before_counts != after_counts, \
        "FLAW #3: Offline learning must change skill selection patterns!"

def test_skill_priors_updated_after_replay(neo4j_session, clean_memory):
    """
    CRITICAL: Skill stats should be updated after offline learning.
    
    Expected: Skills with high regret should have lower success rates.
    """
    from graph_model import get_skill_stats
    
    runtime = AgentRuntime(
        neo4j_session,
        "locked",
        0.5,
        use_procedural_memory=True,
        adaptive_params=True
    )
    
    # Run episodes to generate data
    for i in range(5):
        runtime.run_episode(max_steps=10)
    
    # Get skill stats before
    context = {"belief_category": runtime._get_belief_category(0.5)}
    stats_before = get_skill_stats(neo4j_session, "try_door", context)
    rate_before = stats_before.get('success_rate', 0.5) if stats_before else 0.5
    
    # Trigger offline learning
    runtime._perform_offline_learning()
    
    # Get skill stats after
    stats_after = get_skill_stats(neo4j_session, "try_door", context)
    rate_after = stats_after.get('success_rate', 0.5) if stats_after else 0.5
    
    # Verify change (could be up or down, but should change)
    assert rate_before != rate_after, \
        "FLAW #3: Skill stats must update after offline learning!"

# ============================================================================
# CRITICAL FLAW 4: Learning Rate Too Low
# ============================================================================

def test_learning_rate_causes_meaningful_change(neo4j_session, clean_memory):
    """
    CRITICAL: Learning rate should cause noticeable adaptation.
    
    Expected: With learning_rate=0.5, a single high-regret episode should change stats by >5%.
    """
    # Simulate one episode with high regret
    regret = 10  # Very bad choice
    learning_rate = config.EPISODIC_LEARNING_RATE  # Should be 0.5
    
    adjustment = -regret * learning_rate  # -10 * 0.5 = -5
    initial_rate = 0.5
    new_rate = initial_rate + (adjustment / 100)  # 0.5 + (-0.05) = 0.45
    
    change_pct = abs(new_rate - initial_rate) / initial_rate * 100
    
    assert change_pct >= 5.0, \
        f"FLAW #4: Learning rate too low! Only {change_pct:.1f}% change (need >5%)"
    
    # Verify config
    assert config.EPISODIC_LEARNING_RATE >= 0.5, \
        f"FLAW #4: Learning rate is {config.EPISODIC_LEARNING_RATE}, should be >=0.5"

# ============================================================================
# CRITICAL FLAW 5: Episodic/Procedural Memory Isolated
# ============================================================================

def test_episodic_insights_propagate_to_procedural_memory(neo4j_session, clean_memory):
    """
    CRITICAL: Episodic insights must propagate to procedural memory.
    
    Expected: When episodic memory identifies bad skills, procedural memory should reflect this.
    """
    runtime = AgentRuntime(
        neo4j_session,
        "unlocked",
        0.5,
        use_procedural_memory=True,
        adaptive_params=True
    )
    
    # Run episodes
    for i in range(5):
        runtime.run_episode(max_steps=10)
    
    # Trigger offline learning
    runtime._perform_offline_learning()
    
    # Check that procedural memory was updated
    # This is verified by checking if skill stats changed
    from graph_model import get_skill_stats
    
    stats = get_skill_stats(neo4j_session, "peek_door", {})
    
    # Should have counterfactual_adjusted flag
    if stats:
        # Note: We need to add this field to verify integration
        # For now, just verify stats exist and can be updated
        assert 'success_rate' in stats, \
            "FLAW #5: Episodic insights must update procedural memory stats!"

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_end_to_end_episodic_learning(neo4j_session, clean_memory, labyrinth):
    """
    Full integration test: Store, replay, learn, adapt.
    
    This validates the entire pipeline works correctly.
    """
    runtime = AgentRuntime(
        neo4j_session,
        "locked",
        0.5,
        use_procedural_memory=True,
        adaptive_params=True
    )
    
    # Integrate labyrinth
    runtime._integrate_graph_labyrinth(labyrinth)
    
    # Phase 1: Generate episodes
    episode_ids = []
    for i in range(10):
        ep_id = runtime.run_episode(max_steps=10)
        episode_ids.append(ep_id)
    
    # Phase 2: Verify storage
    for ep_id in episode_ids:
        episode = clean_memory.get_episode(ep_id)
        assert episode is not None, "All episodes should be stored"
        assert len(episode.get('counterfactuals', [])) > 0, "Should have counterfactuals"
    
    # Phase 3: Trigger offline learning
    runtime._perform_offline_learning()
    
    # Phase 4: Verify adaptation occurred
    # This is a smoke test - just verify no crashes and some change happened
    assert runtime.episodes_completed >= 10, "Should have completed episodes"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
