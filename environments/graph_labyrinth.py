"""
Graph Labyrinth - Multi-room dungeon for testing advanced AI concepts.

This is a stand-alone extension to the MacGyver scenario that enables:
- Long-running episodes (for Lyapunov stability testing)
- Multi-agent coordination (for Schelling points)
- Complex decision trees (for Minimax regret)

The labyrinth uses Neo4j to store a room graph, enabling:
- Spatial traversal via graph queries
- Persistent state across episodes
- Visual debugging via Neo4j Browser
"""

from typing import Dict, List, Optional, Tuple
from neo4j import Session
import random

class GraphLabyrinth:
    """
    Neo4j-backed dungeon crawler environment.
    
    Rooms are nodes, connections are edges.
    Agents traverse the graph to reach objectives.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the labyrinth.
        
        Args:
            session: Active Neo4j session
        """
        self.session = session
        
    def initialize_schema(self):
        """
        Create Neo4j constraints and indexes for labyrinth.
        
        Note: This does NOT modify existing Agent/Episode/Skill schema.
        """
        self.session.run("""
            CREATE CONSTRAINT labyrinth_room_id IF NOT EXISTS
            FOR (r:LabyrinthRoom) REQUIRE r.id IS UNIQUE
        """)
        
        self.session.run("""
            CREATE INDEX labyrinth_room_type IF NOT EXISTS
            FOR (r:LabyrinthRoom) ON (r.room_type)
        """)
        
    def clear_labyrinth(self):
        """Remove all labyrinth nodes (for testing/reset)."""
        self.session.run("""
            MATCH (r:LabyrinthRoom)
            DETACH DELETE r
        """)
        
    def generate_linear_dungeon(self, num_rooms: int = 10, 
                                seed: Optional[int] = None) -> str:
        """
        Generate a simple linear dungeon: Start → Room1 → ... → Exit
        
        Args:
            num_rooms: Number of rooms in the dungeon
            seed: Random seed for procedural generation
            
        Returns:
            ID of the start room
        """
        if seed is not None:
            random.seed(seed)
            
        self.clear_labyrinth()
        
        room_ids = []
        
        # Create start room
        result = self.session.run("""
            CREATE (r:LabyrinthRoom {
                id: 'start',
                room_type: 'start',
                description: 'The entrance to the labyrinth',
                danger_level: 0.0,
                visited: false
            })
            RETURN r.id AS room_id
        """)
        room_ids.append(result.single()['room_id'])
        
        # Create intermediate rooms
        for i in range(1, num_rooms - 1):
            danger = random.uniform(0.1, 0.5)
            result = self.session.run("""
                CREATE (r:LabyrinthRoom {
                    id: $room_id,
                    room_type: 'corridor',
                    description: $description,
                    danger_level: $danger,
                    visited: false
                })
                RETURN r.id AS room_id
            """, room_id=f"room_{i}",
                description=self._generate_description(),
                danger=danger)
            room_ids.append(result.single()['room_id'])
        
        # Create exit room
        result = self.session.run("""
            CREATE (r:LabyrinthRoom {
                id: 'exit',
                room_type: 'exit',
                description: 'A bright doorway leading out',
                danger_level: 0.0,
                visited: false
            })
            RETURN r.id AS room_id
        """)
        room_ids.append(result.single()['room_id'])
        
        # Connect rooms linearly
        for i in range(len(room_ids) - 1):
            self.session.run("""
                MATCH (r1:LabyrinthRoom {id: $from_id})
                MATCH (r2:LabyrinthRoom {id: $to_id})
                CREATE (r1)-[:CONNECTS_TO {
                    direction: 'forward',
                    locked: false,
                    cost: 1
                }]->(r2)
                CREATE (r2)-[:CONNECTS_TO {
                    direction: 'backward',
                    locked: false,
                    cost: 1
                }]->(r1)
            """, from_id=room_ids[i], to_id=room_ids[i+1])
        
        return 'start'
    
    def _generate_description(self) -> str:
        """Generate a random room description."""
        adjectives = ['dark', 'winding', 'damp', 'cold', 'echoing', 'narrow']
        nouns = ['corridor', 'chamber', 'passage', 'tunnel', 'hall']
        features = ['with ancient markings', 'lit by torches', 'covered in moss', 
                   'with crumbling walls', 'silent and still']
        
        return f"A {random.choice(adjectives)} {random.choice(nouns)} {random.choice(features)}"
    
    def get_room_info(self, room_id: str) -> Optional[Dict]:
        """
        Get information about a room.
        
        Args:
            room_id: ID of the room
            
        Returns:
            Dict with room properties or None if not found
        """
        result = self.session.run("""
            MATCH (r:LabyrinthRoom {id: $room_id})
            RETURN r.id AS id, r.description AS description, 
                   r.danger_level AS danger_level, r.room_type AS room_type,
                   r.visited AS visited
        """, room_id=room_id)
        
        record = result.single()
        if record:
            return dict(record)
        return None
    
    def get_adjacent_rooms(self, room_id: str) -> List[Dict]:
        """
        Get rooms connected to the current room.
        
        Args:
            room_id: ID of the current room
            
        Returns:
            List of dicts with room info and connection properties
        """
        result = self.session.run("""
            MATCH (r:LabyrinthRoom {id: $room_id})-[c:CONNECTS_TO]->(adj:LabyrinthRoom)
            RETURN adj.id AS id, adj.description AS description,
                   adj.room_type AS room_type, adj.visited AS visited,
                   c.direction AS direction, c.locked AS locked, c.cost AS cost
        """, room_id=room_id)
        
        return [dict(record) for record in result]
    
    def mark_visited(self, room_id: str):
        """Mark a room as visited."""
        self.session.run("""
            MATCH (r:LabyrinthRoom {id: $room_id})
            SET r.visited = true
        """, room_id=room_id)
    
    def get_distance_to_exit(self, room_id: str) -> int:
        """
        Calculate shortest path distance to exit using Dijkstra.
        
        Args:
            room_id: ID of the current room
            
        Returns:
            Number of rooms to traverse to reach exit
        """
        # Check if we're already at exit
        room_info = self.get_room_info(room_id)
        if room_info and room_info.get('room_type') == 'exit':
            return 0
            
        result = self.session.run("""
            MATCH path = shortestPath((start:LabyrinthRoom {id: $room_id})-[:CONNECTS_TO*]-(exit:LabyrinthRoom {room_type: 'exit'}))
            RETURN length(path) AS distance
        """, room_id=room_id)
        
        record = result.single()
        if record:
            return record['distance']
        return 999  # Unreachable
    
    def get_labyrinth_stats(self) -> Dict:
        """Get statistics about the current labyrinth."""
        result = self.session.run("""
            MATCH (r:LabyrinthRoom)
            OPTIONAL MATCH (visited:LabyrinthRoom WHERE visited.visited = true)
            RETURN count(DISTINCT r) AS total, count(DISTINCT visited) AS visited_count
        """)
        
        record = result.single()
        if record:
            total = record['total']
            visited = record['visited_count']
            return {
                'total_rooms': total,
                'visited_rooms': visited,
                'completion': visited / total if total > 0 else 0.0
            }
        return {'total_rooms': 0, 'visited_rooms': 0, 'completion': 0.0}
