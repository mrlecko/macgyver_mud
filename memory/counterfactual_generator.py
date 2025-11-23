"""
Counterfactual Generator - Generates alternative paths for episodic memory.

Given an actual path taken, this generates plausible alternative paths
that the agent could have taken instead.
"""

from typing import Dict, List, Any
from neo4j import Session
from environments.graph_labyrinth import GraphLabyrinth
import random

class CounterfactualGenerator:
    """
    Generates counterfactual paths for episodic replay.
    
    Uses the labyrinth structure to simulate "what if" scenarios.
    """
    
    def __init__(self, session: Session, labyrinth: GraphLabyrinth):
        """
        Initialize counterfactual generator.
        
        Args:
            session: Neo4j session
            labyrinth: Graph labyrinth environment
        """
        self.session = session
        self.labyrinth = labyrinth
    
    def generate_alternatives(self, actual_path: Dict[str, Any], 
                             max_alternates: int = 5) -> List[Dict[str, Any]]:
        """
        Generate counter factual paths by exploring alternate choices at each step.
        
        Args:
            actual_path: Dict with 'rooms_visited' and 'actions_taken'
            max_alternates: Maximum number of alternatives to generate
            
        Returns:
            List of counterfactual path dicts
        """
        counterfactuals = []
        rooms_visited = actual_path['rooms_visited']
        
        # Generate alternatives by diverging at different points
        for divergence_point in range(len(rooms_visited) - 1):
            if len(counterfactuals) >= max_alternates:
                break
                
            current_room = rooms_visited[divergence_point]
            
            # Get all adjacent rooms
            adjacent = self.labyrinth.get_adjacent_rooms(current_room)
            
            # Filter out the room actually chosen
            actual_next = rooms_visited[divergence_point + 1] if divergence_point + 1 < len(rooms_visited) else None
            alternate_rooms = [r for r in adjacent if r['id'] != actual_next]
            
            if not alternate_rooms:
                continue
            
            # Pick a random alternate
            chosen_alternate = random.choice(alternate_rooms)
            
            # Simulate path from this alternate choice
            cf_path = self._simulate_path(
                start_room=chosen_alternate['id'],
                max_steps=20,
                divergence_point=divergence_point
            )
            
            if cf_path:
                counterfactuals.append(cf_path)
        
        return counterfactuals
    
    def _simulate_path(self, start_room: str, max_steps: int, 
                      divergence_point: int) -> Dict[str, Any]:
        """
        Simulate a path from a starting room using simple greedy strategy.
        
        Args:
            start_room: Room to start from
            max_steps: Maximum steps to simulate
            divergence_point: Step where this diverged from actual
            
        Returns:
            Counterfactual path dict or None if couldn't complete
        """
        rooms_visited = [start_room]
        actions_taken = []
        current = start_room
        
        for step in range(max_steps):
            # Get room info
            room_info = self.labyrinth.get_room_info(current)
            if not room_info:
                break
            
            # Check if at exit
            if room_info['room_type'] == 'exit':
                return {
                    'path_id': f'cf_{divergence_point}_{start_room}',
                    'rooms_visited': rooms_visited,
                    'actions_taken': actions_taken,
                    'outcome': 'success',
                    'steps': len(actions_taken),
                    'final_distance': 0,
                    'divergence_point': divergence_point
                }
            
            # Get adjacent rooms
            adjacent = self.labyrinth.get_adjacent_rooms(current)
            if not adjacent:
                # Dead end
                return {
                    'path_id': f'cf_{divergence_point}_{start_room}',
                    'rooms_visited': rooms_visited,
                    'actions_taken': actions_taken,
                    'outcome': 'failure',
                    'steps': len(actions_taken),
                    'final_distance': self.labyrinth.get_distance_to_exit(current),
                    'divergence_point': divergence_point
                }
            
            # Choose room (greedy: pick closest to exit)
            next_room = min(adjacent, key=lambda r: self.labyrinth.get_distance_to_exit(r['id']))
            
            current = next_room['id']
            rooms_visited.append(current)
            actions_taken.append('move')
        
        # Ran out of steps
        return {
            'path_id': f'cf_{divergence_point}_{start_room}',
            'rooms_visited': rooms_visited,
            'actions_taken': actions_taken,
            'outcome': 'failure',
            'steps': len(actions_taken),
            'final_distance': self.labyrinth.get_distance_to_exit(current),
            'divergence_point': divergence_point
        }
