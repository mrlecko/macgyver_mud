"""
Episodic Memory Replay Demonstration

Demonstrates offline learning through counterfactual reasoning:
1. Agent explores labyrinth (Phase 1: Experience)
2. Agent replays episodes and generates counterfactuals (Phase 2: Reflection)
3. Agent re-attempts labyrinth with insights (Phase 3: Improvement)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import config
from memory.episodic_replay import EpisodicMemory
from memory.counterfactual_generator import CounterfactualGenerator
from environments.graph_labyrinth import GraphLabyrinth
import random

def run_episodic_replay_demo():
    """Run the complete episodic memory demonstration."""
    
    print("=" * 70)
    print("EPISODIC MEMORY REPLAY DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how an agent learns from past mistakes")
    print("WITHOUT new experience, using counterfactual reasoning.\n")
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    
    try:
        # Initialize systems
        episodic_memory = EpisodicMemory(session)
        labyrinth = GraphLabyrinth(session)
        
        # Clean up
        episodic_memory.clear_all_episodes()
        labyrinth.clear_labyrinth()
        
        # Create a 10-room labyrinth
        print("Setting up 10-room labyrinth...")
        labyrinth.generate_linear_dungeon(num_rooms=10, seed=42)
        print("✓ Labyrinth created\n")
        
        # PHASE 1: EXPLORATION (Naive)
        print("-" * 70)
        print("PHASE 1: EXPLORATION (No prior knowledge)")
        print("-" * 70)
        
        exploration_paths = simulate_naive_exploration(labyrinth, num_episodes=5)
        
        print(f"\nExplored {len(exploration_paths)} episodes")
        avg_steps_phase1 = sum(p['steps'] for p in exploration_paths) / len(exploration_paths)
        print(f"Average steps to exit: {avg_steps_phase1:.1f}")
        
        # Store episodes
        for i, path in enumerate(exploration_paths):
            episode_id = f"exploration_{i}"
            episodic_memory.store_actual_path(episode_id, path)
        
        # PHASE 2: REFLECTION (Offline Learning)
        print("\n" + "-" * 70)
        print("PHASE 2: REFLECTION (Generating counterfactuals)")
        print("-" * 70)
        
        generator = CounterfactualGenerator(session, labyrinth)
        total_counterfactuals = 0
        total_regret = 0
        
        for i, path in enumerate(exploration_paths):
            episode_id = f"exploration_{i}"
            
            # Generate counterfactuals
            counterfactuals = generator.generate_alternatives(path, max_alternates=3)
            episodic_memory.store_counterfactuals(episode_id, counterfactuals)
            
            # Calculate regret
            for cf in counterfactuals:
                if cf['outcome'] == 'success':
                    regret = episodic_memory.calculate_regret(
                        {'steps': path['steps'], 'outcome': path['outcome']},
                        {'steps': cf['steps'], 'outcome': cf['outcome']}
                    )
                    total_regret += regret
            
            total_counterfactuals += len(counterfactuals)
            print(f"  Episode {i}: Generated {len(counterfactuals)} counterfactuals")
        
        print(f"\nTotal counterfactuals generated: {total_counterfactuals}")
        if total_counterfactuals > 0:
            avg_regret = total_regret / total_counterfactuals
            print(f"Average regret per counterfactual: {avg_regret:.2f} steps")
            print(f"Total learning opportunities: {total_regret:.1f} steps saved if optimal")
        
        # PHASE 3: IMPROVED PERFORMANCE (With Insights)
        print("\n" + "-" * 70)
        print("PHASE 3: RE-ATTEMPT (Using insights from reflection)")
        print("-" * 70)
        print("Note: This is a mock improvement - full integration would use")
        print("      counterfactual insights to update skill priors.\n")
        
        # For demo purposes, show what the agent learned
        print("Key insights from counterfactuals:")
        for i in range(min(3, len(exploration_paths))):
            episode = episodic_memory.get_episode(f"exploration_{i}")
            actual_steps = episode['actual_path']['steps']
            
            if episode['counterfactuals']:
                best_cf = min(episode['counterfactuals'], key=lambda x: x['steps'])
                best_steps = best_cf['steps']
                divergence = best_cf['divergence_point']
                
                print(f"  Episode {i}: Actual={actual_steps} steps, " 
                      f"Best CF={best_steps} steps (diverged at step {divergence})")
        
        # Simulate improved performance (mock)
        improvement_factor = 0.7  # 30% improvement from learning
        avg_steps_phase3 = avg_steps_phase1 * improvement_factor
        
        print(f"\nProjected improvement with counterfactual insights:")
        print(f"  Before: {avg_steps_phase1:.1f} steps average")
        print(f"  After:  {avg_steps_phase3:.1f} steps average")
        print(f"  Improvement: {(1 - improvement_factor) * 100:.0f}%")
        
        # SUMMARY
        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
        print(f"\n✓ Stored {len(exploration_paths)} episodes")
        print(f"✓ Generated {total_counterfactuals} counterfactuals")
        print(f"✓ Identified {total_regret:.0f} steps of improvement potential")
        print(f"✓ Offline learning enabled WITHOUT new experience")
        
        print("\n" + "=" * 70)
        print("KEY TAKEAWAY: Counterfactual reasoning allows the agent to")
        print("learn 'what could have been' and improve without exploration.")
        print("=" * 70 + "\n")
        
    finally:
        session.close()
        driver.close()

def simulate_naive_exploration(labyrinth, num_episodes=5):
    """
    Simulate naive agent exploring the labyrinth.
    
    Uses random walk to find exit (no learning between episodes).
    """
    paths = []
    
    for ep in range(num_episodes):
        current_room = 'start'
        rooms_visited = [current_room]
        actions_taken = []
        max_steps = 20
        
        for step in range(max_steps):
            # Check if at exit
            room_info = labyrinth.get_room_info(current_room)
            if room_info and room_info['room_type'] == 'exit':
                # Success!
                paths.append({
                    'path_id': f'naive_{ep}',
                    'rooms_visited': rooms_visited,
                    'actions_taken': actions_taken,
                    'outcome': 'success',
                    'steps': len(actions_taken),
                    'final_distance': 0
                })
                break
            
            # Get adjacent rooms
            adjacent = labyrinth.get_adjacent_rooms(current_room)
            if not adjacent:
                # Dead end (shouldn't happen in linear dungeon)
                paths.append({
                    'path_id': f'naive_{ep}',
                    'rooms_visited': rooms_visited,
                    'actions_taken': actions_taken,
                    'outcome': 'failure',
                    'steps': len(actions_taken),
                    'final_distance': labyrinth.get_distance_to_exit(current_room)
                })
                break
            
            # Random choice (naive exploration)
            next_room = random.choice(adjacent)
            current_room = next_room['id']
            rooms_visited.append(current_room)
            actions_taken.append('move')
        else:
            # Ran out of steps
            paths.append({
                'path_id': f'naive_{ep}',
                'rooms_visited': rooms_visited,
                'actions_taken': actions_taken,
                'outcome': 'failure',
                'steps': len(actions_taken),
                'final_distance': labyrinth.get_distance_to_exit(current_room)
            })
    
    return paths

if __name__ == "__main__":
    run_episodic_replay_demo()
