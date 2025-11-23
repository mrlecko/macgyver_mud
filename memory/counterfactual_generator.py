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
        Generate counterfactual paths by exploring alternate choices at each step.
        
        Args:
            actual_path: Dict with 'rooms_visited' (spatial) or 'path_data' (generalized)
            max_alternates: Maximum number of alternatives to generate
            
        Returns:
            List of counterfactual path dicts
        """
        # Detect path type
        if 'path_data' in actual_path:
            return self._generate_belief_alternatives(actual_path, max_alternates)
        
        # Legacy spatial logic
        # FIX #2: Validate labyrinth is available
        if self.labyrinth is None:
            # Only print warning if we are trying to do spatial generation
            # (If we are here, it means we have spatial data but no labyrinth)
            print("Warning: Spatial counterfactual generation requires graph labyrinth")
            return []
        
        # FIX #2: Validate path has proper structure
        rooms_visited = actual_path.get('rooms_visited', [])
        if not rooms_visited or not isinstance(rooms_visited, list):
            print("Warning: Invalid path structure for counterfactual generation")
            return []
        
        # FIX #2: If rooms_visited contains state dicts, extract room IDs
        if rooms_visited and isinstance(rooms_visited[0], dict):
            # This should be handled by 'path_data' check above, but just in case
            print("Warning: Path contains state dicts but passed as spatial. Spatial counterfactuals not applicable.")
            return []
        
        counterfactuals = []
        
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

    def _generate_belief_alternatives(self, actual_path: Dict[str, Any], max_alternates: int) -> List[Dict[str, Any]]:
        """Generate counterfactuals for belief-space trajectories."""
        import json
        
        # Parse path data
        try:
            if isinstance(actual_path['path_data'], str):
                path = json.loads(actual_path['path_data'])
            else:
                path = actual_path['path_data']
        except:
            return []
            
        if not path:
            return []
            
        counterfactuals = []
        available_skills = ['peek_door', 'try_door', 'go_window'] # Hardcoded for MacGyver for now
        
        # Iterate through steps to diverge
        for i in range(len(path) - 1):
            if len(counterfactuals) >= max_alternates:
                break
                
            step_data = path[i]
            current_belief = step_data.get('belief', 0.5)
            actual_skill = step_data.get('skill')
            
            print(f"DEBUG: Step {i}, skill={actual_skill}, belief={current_belief}")
            
            # Find alternative skills
            alternatives = [s for s in available_skills if s != actual_skill]
            print(f"DEBUG: Alternatives: {alternatives}")
            
            if not alternatives:
                continue
                
            # Pick one alternative
            chosen_alt = random.choice(alternatives)
            
            # Simulate outcome
            cf_path = self._simulate_belief_trajectory(
                start_belief=current_belief,
                chosen_skill=chosen_alt,
                divergence_point=i,
                max_steps=5
            )
            
            if cf_path:
                print(f"DEBUG: Generated CF: {cf_path['path_id']}")
                counterfactuals.append(cf_path)
                
        return counterfactuals
    
    def _simulate_belief_trajectory(self, start_belief, chosen_skill, divergence_point, max_steps):
        """Simulate a belief trajectory from a divergence point."""
        # Simplified simulation logic for MacGyver scenario
        trajectory = []
        belief = start_belief
        
        # Simulate the divergence step
        obs, new_belief, escaped = self._simulate_step(chosen_skill, belief)
        trajectory.append({
            'step': divergence_point,
            'belief': new_belief,
            'skill': chosen_skill,
            'observation': obs
        })
        
        if escaped:
            return {
                'path_id': f'cf_{divergence_point}_{chosen_skill}',
                'path_data': trajectory, # Will be serialized later
                'state_type': 'belief_trajectory',
                'outcome': 'success',
                'steps': len(trajectory) + divergence_point,
                'divergence_point': divergence_point
            }
            
        # Continue simulating greedily
        current_step = 1
        while current_step < max_steps and not escaped:
            # Greedy policy: try_door if belief > 0.8, else peek
            next_skill = 'try_door' if belief > 0.8 else 'peek_door'
            
            obs, new_belief, escaped = self._simulate_step(next_skill, belief)
            trajectory.append({
                'step': divergence_point + current_step,
                'belief': new_belief,
                'skill': next_skill,
                'observation': obs
            })
            
            belief = new_belief
            current_step += 1
            
        return {
            'path_id': f'cf_{divergence_point}_{chosen_skill}',
            'path_data': trajectory,
            'state_type': 'belief_trajectory',
            'outcome': 'success' if escaped else 'failure',
            'steps': len(trajectory) + divergence_point,
            'divergence_point': divergence_point
        }

    def _simulate_step(self, skill, belief):
        """Simulate single step outcome."""
        # Simplified transition model
        escaped = False
        obs = 'unknown'
        new_belief = belief
        
        if skill == 'try_door':
            # Probabilistic success based on belief (which tracks p_unlocked)
            if random.random() < belief:
                escaped = True
                obs = 'success'
                new_belief = 1.0
            else:
                obs = 'locked'
                new_belief = 0.0
        elif skill == 'peek_door':
            # Simulate observation
            is_unlocked = random.random() < belief
            if is_unlocked:
                obs = 'open'
                # Bayesian update: P(U|Open) = 1.0 (assuming perfect sensor)
                new_belief = 0.99 
            else:
                obs = 'closed'
                # Bayesian update: P(U|Closed) -> lower
                new_belief = belief * 0.2 # Rough approximation
        elif skill == 'go_window':
            if random.random() < 0.1: # Low success rate
                escaped = True
                obs = 'success'
            else:
                obs = 'stuck'
                
        return obs, new_belief, escaped
    
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
