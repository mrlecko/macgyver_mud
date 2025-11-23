"""
Episodic Memory System with Counterfactual Reasoning

Stores not just what happened, but what could have happened.
Enables offline learning by replaying episodes with alternate choices.
"""

from typing import Dict, List, Optional, Any
from neo4j import Session

class EpisodicMemory:
    """
    Manages episodic memory storage and retrieval in Neo4j.
    
    Each episode contains:
    - Actual path taken
    - Counterfactual paths (what could have happened)
    - Regret calculations (actual vs. counterfactual outcomes)
    """
    
    def __init__(self, session: Session):
        """
        Initialize episodic memory system.
        
        Args:
            session: Active Neo4j session
        """
        self.session = session
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create Neo4j constraints and indexes for episodic memory."""
        # Constraint on episode ID
        self.session.run("""
            CREATE CONSTRAINT episodic_memory_id IF NOT EXISTS
            FOR (e:EpisodicMemory) REQUIRE e.episode_id IS UNIQUE
        """)
        
        # Index on path type for faster queries
        self.session.run("""
            CREATE INDEX episodic_path_type IF NOT EXISTS
           FOR (p:EpisodicPath) ON (p.path_type)
        """)
    
    def store_actual_path(self, episode_id: str, path_data: Dict[str, Any]):
        """
        Store the actual path taken during an episode.
        
        Args:
            episode_id: Unique identifier for episode
            path_data: Dict containing:
                - path_id: Unique path identifier
                - rooms_visited: List of room IDs
                - actions_taken: List of actions
                - outcome: 'success' or 'failure'
                - steps: Number of steps taken
                - final_distance: Distance from goal at end
        """
        self.session.run("""
            MERGE (e:EpisodicMemory {episode_id: $episode_id})
            CREATE (p:EpisodicPath {
                path_id: $path_id,
                path_type: 'actual',
                rooms_visited: $rooms_visited,
                actions_taken: $actions_taken,
                outcome: $outcome,
                steps: $steps,
                final_distance: $final_distance
            })
            CREATE (e)-[:HAD_ACTUAL_PATH]->(p)
        """, episode_id=episode_id, **path_data)
    
    def store_counterfactuals(self, episode_id: str, counterfactuals: List[Dict[str, Any]]):
        """
        Store counterfactual paths for an episode.
        
        Args:
            episode_id: Episode to attach counterfactuals to
            counterfactuals: List of path dicts, each with same structure as actual
                             plus 'divergence_point' (step where it diverged)
        """
        for cf in counterfactuals:
            self.session.run("""
                MATCH (e:EpisodicMemory {episode_id: $episode_id})
                CREATE (p:EpisodicPath {
                    path_id: $path_id,
                    path_type: 'counterfactual',
                    rooms_visited: $rooms_visited,
                    actions_taken: $actions_taken,
                    outcome: $outcome,
                    steps: $steps,
                    final_distance: $final_distance,
                    divergence_point: $divergence_point
                })
                CREATE (e)-[:HAD_COUNTERFACTUAL]->(p)
            """, episode_id=episode_id, **cf)
    
    def get_episode(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an episode with all its paths.
        
        Args:
            episode_id: Episode to retrieve
            
        Returns:
            Dict with 'actual_path' and 'counterfactuals' list, or None if not found
        """
        # Get actual path
        result = self.session.run("""
            MATCH (e:EpisodicMemory {episode_id: $episode_id})-[:HAD_ACTUAL_PATH]->(p:EpisodicPath)
            RETURN p.path_id AS path_id,
                   p.rooms_visited AS rooms_visited,
                   p.actions_taken AS actions_taken,
                   p.outcome AS outcome,
                   p.steps AS steps,
                   p.final_distance AS final_distance
        """, episode_id=episode_id)
        
        actual_record = result.single()
        if not actual_record:
            return None
        
        actual_path = dict(actual_record)
        
        # Get counterfactuals
        result = self.session.run("""
            MATCH (e:EpisodicMemory {episode_id: $episode_id})-[:HAD_COUNTERFACTUAL]->(p:EpisodicPath)
            RETURN p.path_id AS path_id,
                   p.rooms_visited AS rooms_visited,
                   p.actions_taken AS actions_taken,
                   p.outcome AS outcome,
                   p.steps AS steps,
                   p.final_distance AS final_distance,
                   p.divergence_point AS divergence_point
            ORDER BY p.divergence_point
        """, episode_id=episode_id)
        
        counterfactuals = [dict(record) for record in result]
        
        return {
            'actual_path': actual_path,
            'counterfactuals': counterfactuals
        }
    
    def calculate_regret(self, actual_outcome: Dict, counterfactual_outcome: Dict) -> float:
        """
        Calculate regret: how much better the counterfactual was.
        
        Args:
            actual_outcome: Dict with 'steps' and 'outcome'
            counterfactual_outcome: Dict with 'steps' and 'outcome'
            
        Returns:
            Regret score (positive = counterfactual was better)
        """
        # Simple regret: difference in steps
        # More sophisticated version would consider outcome and distance
        actual_steps = actual_outcome.get('steps', 0)
        cf_steps = counterfactual_outcome.get('steps', 0)
        
        # If counterfactual succeeded and actual failed, huge regret
        if actual_outcome.get('outcome') == 'failure' and counterfactual_outcome.get('outcome') == 'success':
            return 100 + (actual_steps - cf_steps)
        
        # If both succeeded or both failed, regret is just step difference
        return actual_steps - cf_steps
    
    def clear_all_episodes(self):
        """Delete all episodic memory (for testing)."""
        self.session.run("""
            MATCH (e:EpisodicMemory)
            DETACH DELETE e
        """)
        
        self.session.run("""
            MATCH (p:EpisodicPath)
            DELETE p
        """)
