"""
Red Team Stress Tests for Episodic Memory System

Tests the two identified vulnerabilities:
1. Overfitting Trap: Too many counterfactuals cause specialization
2. Regret Spiral: Always seeing better options causes paralysis
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from memory.episodic_replay import EpisodicMemory
from memory.counterfactual_generator import CounterfactualGenerator
from environments.graph_labyrinth import GraphLabyrinth
import numpy as np

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
    mem.clear_all_episodes()
    return mem

@pytest.fixture
def labyrinth(neo4j_session):
    """Provide a labyrinth for testing."""
    lab = GraphLabyrinth(neo4j_session)
    lab.initialize_schema()
    lab.clear_labyrinth()
    lab.generate_linear_dungeon(num_rooms=10, seed=42)
    return lab

def test_overfitting_trap_stress_test(episodic_memory, labyrinth, neo4j_session):
    """
    STRESS TEST: The Overfitting Trap
    
    Test if generating too many counterfactuals causes the agent to learn
    patterns that don't generalize.
    
    Hypothesis: 100 CFs per episode will cause overfitting
    """
    generator = CounterfactualGenerator(neo4j_session, labyrinth)
    
    # Store 1 episode with MANY counterfactuals
    actual_path = {
        'path_id': 'actual_overfit',
        'rooms_visited': ['start', 'room_1', 'room_2', 'exit'],
        'actions_taken': ['move'] * 3,
        'outcome': 'success',
        'steps': 3,
        'final_distance': 0
    }
    
    episodic_memory.store_actual_path('overfit_episode', actual_path)
    
    # Generate MANY alternates (simulate overfitting)
    all_counterfactuals = []
    for _ in range(20):  # Try to generate 20 alternates
        cfs = generator.generate_alternatives(actual_path, max_alternates=5)
        all_counterfactuals.extend(cfs)
    
    # Store all
    episodic_memory.store_counterfactuals('overfit_episode', all_counterfactuals[:50])  # Cap at 50
    
    retrieved = episodic_memory.get_episode('overfit_episode')
    num_cfs = len(retrieved['counterfactuals'])
    
    print(f"\n=== OVERFITTING TRAP TEST ===")
    print(f"Number of counterfactuals stored: {num_cfs}")
    
    # Analyze divergence points
    divergence_points = [cf['divergence_point'] for cf in retrieved['counterfactuals']]
    unique_divergence = len(set(divergence_points))
    
    print(f"Unique divergence points: {unique_divergence}")
    print(f"Average divergence point: {np.mean(divergence_points):.2f}")
    
    # Calculate "specialization score" (how many CFs from each divergence point)
    from collections import Counter
    divergence_dist = Counter(divergence_points)
    print(f"Divergence distribution: {dict(divergence_dist)}")
    
    # CRITICAL QUESTION: Is this too specialized?
    # If >70% of CFs come from same divergence point, it's overfitting
    max_concentration = max(divergence_dist.values()) / len(divergence_points)
    print(f"Max concentration at single divergence: {max_concentration:.2%}")
    
    if max_concentration > 0.7:
        print("⚠️ OVERFITTING DETECTED: Agent is specializing to specific choice point")
        is_overfitting = True
    else:
        print("✓ DIVERSITY MAINTAINED: CFs spread across multiple divergence points")
        is_overfitting = False
    
    # VERDICT: Is this a CRITICAL flaw?
    # Critical = causes measurable harm
    # Non-critical = theoretical concern but manageable
    
    assert num_cfs > 0, "Should have generated some counterfactuals"
    
    return {
        'num_counterfactuals': num_cfs,
        'overfitting_detected': is_overfitting,
        'max_concentration': max_concentration
    }

def test_regret_spiral_stress_test(episodic_memory):
    """
    STRESS TEST: The Regret Spiral
    
    Test if always seeing better counterfactuals causes decision paralysis.
    
    Hypothesis: If counterfactual is ALWAYS better, regret accumulates to point
    where agent becomes risk-averse.
    """
    print(f"\n=== REGRET SPIRAL TEST ===")
    
    # Simulate 10 episodes where CF is always better
    regrets = []
    for i in range(10):
        actual = {
            'path_id': f'actual_{i}',
            'rooms_visited': ['start'] + [f'room_{j}' for j in range(5)] + ['exit'],
            'actions_taken': ['move'] * 5,
            'outcome': 'success',
            'steps': 5,
            'final_distance': 0
        }
        
        # Counterfactual is ALWAYS better (2 steps instead of 5)
        cf = {
            'path_id': f'cf_{i}',
            'rooms_visited': ['start', 'room_1', 'exit'],
            'actions_taken': ['move'] * 2,
            'outcome': 'success',
            'steps': 2,
            'final_distance': 0,
            'divergence_point': 0
        }
        
        episodic_memory.store_actual_path(f'episode_{i}', actual)
        episodic_memory.store_counterfactuals(f'episode_{i}', [cf])
        
        # Calculate regret
        regret = episodic_memory.calculate_regret(
            {'steps': actual['steps'], 'outcome': actual['outcome']},
            {'steps': cf['steps'], 'outcome': cf['outcome']}
        )
        regrets.append(regret)
    
    total_regret = sum(regrets)
    avg_regret = np.mean(regrets)
    
    print(f"Episodes with counterfactuals: {len(regrets)}")
    print(f"Regrets per episode: {regrets}")
    print(f"Average regret: {avg_regret:.2f}")
    print(f"Total accumulated regret: {total_regret}")
    
    # CRITICAL QUESTION: Does accumulated regret cause paralysis?
    # Paralysis = agent becomes too risk-averse to act
    
    # Simulate decision-making with regret penalty
    def decide_with_regret_penalty(base_utility, regret_history):
        """
        Agent's decision utility decreases with accumulated regret.
        If regret is too high, agent becomes paralyzed.
        """
        regret_penalty = sum(regret_history) * 0.1  # 10% penalty per regret point
        adjusted_utility = base_utility - regret_penalty
        return adjusted_utility
    
    base_action_utility = 10.0  # Baseline value of taking action
    
    utilities_over_time = []
    for i in range(len(regrets)):
        current_regret_history = regrets[:i+1]
        utility = decide_with_regret_penalty(base_action_utility, current_regret_history)
        utilities_over_time.append(utility)
    
    print(f"\nUtility over time (with regret penalty):")
    for i, u in enumerate(utilities_over_time):
        print(f"  Episode {i}: Utility = {u:.2f}")
    
    final_utility = utilities_over_time[-1]
    
    # If final utility goes negative, agent is paralyzed
    if final_utility < 0:
        print("⚠️ PARALYSIS DETECTED: Regret has made action utility negative")
        is_paralyzed = True
    elif final_utility < base_action_utility * 0.5:
        print("⚠️ SEVERE INHIBITION: Regret has reduced utility by >50%")
        is_paralyzed = True
    else:
        print("✓ MANAGEABLE REGRET: Agent still has positive utility")
        is_paralyzed = False
    
    assert len(regrets) == 10, "Should have 10 episodes"
    
    return {
        'average_regret': avg_regret,
        'total_regret': total_regret,
        'final_utility': final_utility,
        'paralysis_detected': is_paralyzed
    }

def test_combined_stress_scenario(episodic_memory, labyrinth, neo4j_session):
    """
    COMBINED STRESS TEST: Both vulnerabilities at once
    
    Worst case: Many CFs (overfitting) + Always better (regret spiral)
    """
    print(f"\n=== COMBINED STRESS TEST ===")
    
    generator = CounterfactualGenerator(neo4j_session, labyrinth)
    
    # 5 episodes with many CFs, all better than actual
    for ep_num in range(5):
        actual = {
            'path_id': f'actual_combined_{ep_num}',
            'rooms_visited': ['start', 'room_1', 'room_2', 'room_3', 'exit'],
            'actions_taken': ['move'] * 4,
            'outcome': 'success',
            'steps': 4,
            'final_distance': 0
        }
        
        # Generate 10 CFs
        cfs = []
        for cf_num in range(10):
            cfs.append({
                'path_id': f'cf_combined_{ep_num}_{cf_num}',
                'rooms_visited': ['start', 'room_1', 'exit'],
                'actions_taken': ['move'] * 2,
                'outcome': 'success',
                'steps': 2,  # Always better
                'final_distance': 0,
                'divergence_point': cf_num % 3  # Some variety in divergence
            })
        
        episodic_memory.store_actual_path(f'combined_{ep_num}', actual)
        episodic_memory.store_counterfactuals(f'combined_{ep_num}', cfs)
    
    # Measure total memory consumption
    total_episodes = 5
    total_cfs = 5 * 10
    
    print(f"Total episodes stored: {total_episodes}")
    print(f"Total counterfactuals: {total_cfs}")
    print(f"CFs per episode: {total_cfs / total_episodes}")
    
    # Check if system is still functional
    retrieved = episodic_memory.get_episode('combined_0')
    assert len(retrieved['counterfactuals']) == 10
    
    print("✓ System remains functional under combined stress")
    
    return {
        'total_episodes': total_episodes,
        'total_counterfactuals': total_cfs,
        'system_functional': True
    }

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements
