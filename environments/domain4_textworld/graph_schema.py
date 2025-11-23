"""
Neo4j graph schema for TextWorld integration.

This module defines how TextWorld game worlds are represented in Neo4j,
enabling graph-based knowledge representation and spatial reasoning.

Schema:
- Nodes: TextWorldRoom, TextWorldObject
- Relationships: CONNECTS_TO, LOCATED_IN, UNLOCKS, CONTAINS
"""
from neo4j import Session


class TextWorldGraphSchema:
    """
    Manages Neo4j schema for TextWorld game worlds.
    
    This class creates and manages the graph structure that represents
    TextWorld games in Neo4j, enabling the cognitive architecture to
    reason about spatial relationships and object interactions.
    """
    
    def __init__(self, session: Session):
        """
        Initialize schema manager.
        
        Args:
            session: Active Neo4j session
        """
        self.session = session
    
    def initialize_schema(self):
        """
        Create Neo4j constraints and indexes for TextWorld.
        
        This ensures data integrity and query performance.
        """
        # Room constraints (unique IDs)
        self.session.run("""
            CREATE CONSTRAINT textworld_room_id IF NOT EXISTS
            FOR (r:TextWorldRoom) REQUIRE r.id IS UNIQUE
        """)
        
        # Object constraints (unique IDs)
        self.session.run("""
            CREATE CONSTRAINT textworld_object_id IF NOT EXISTS
            FOR (o:TextWorldObject) REQUIRE o.id IS UNIQUE
        """)
        
        # Indexes for performance
        self.session.run("""
            CREATE INDEX textworld_room_name IF NOT EXISTS
            FOR (r:TextWorldRoom) ON (r.name)
        """)
    
    def clear_game_state(self):
        """
        Remove all TextWorld nodes (for fresh game).
        
        This cleans up the graph before storing a new game world.
        """
        # Delete rooms
        self.session.run("""
            MATCH (n:TextWorldRoom)
            DETACH DELETE n
        """)
        
        # Delete objects
        self.session.run("""
            MATCH (n:TextWorldObject)
            DETACH DELETE n
        """)
    
    def store_game_world(self, game):
        """
        Store TextWorld game structure in Neo4j.
        
        This converts the TextWorld game object into a Neo4j graph,
        creating nodes for rooms and objects, and relationships for
        connections and containment.
        
        Args:
            game: TextWorld game object
        """
        # Clear any existing game state
        self.clear_game_state()
        
        # Store rooms
        for room in game.world.rooms:
            self.session.run("""
                CREATE (r:TextWorldRoom {
                    id: $id,
                    name: $name,
                    description: $desc,
                    visited: false
                })
            """, id=room.id, name=room.name, desc=str(room))
        
        # Store room connections
        for room in game.world.rooms:
            for direction, dest_room in room.exits.items():
                if dest_room:  # Check destination exists
                    self.session.run("""
                        MATCH (r1:TextWorldRoom {id: $from_id})
                        MATCH (r2:TextWorldRoom {id: $to_id})
                        CREATE (r1)-[:CONNECTS_TO {direction: $dir}]->(r2)
                    """, from_id=room.id, to_id=dest_room.id, dir=direction)
        
        # Store objects
        for obj in game.world.objects:
            self.session.run("""
                CREATE (o:TextWorldObject {
                    id: $id,
                    name: $name,
                    type: $type
                })
            """, id=obj.id, name=obj.name, type=obj.type)
    
    def get_room_count(self):
        """
        Get number of rooms in current game.
        
        Returns:
            Number of TextWorldRoom nodes
        """
        result = self.session.run("""
            MATCH (r:TextWorldRoom)
            RETURN count(r) as count
        """)
        return result.single()['count']
    
    def get_object_count(self):
        """
        Get number of objects in current game.
        
        Returns:
            Number of TextWorldObject nodes
        """
        result = self.session.run("""
            MATCH (o:TextWorldObject)
            RETURN count(o) as count
        """)
        return result.single()['count']
