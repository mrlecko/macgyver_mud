# Simple Graph Planner for TextWorld
"""
A lightweight planner that queries the Neo4j graph built by LLMPerception
to find a path from the current room to an exit (door/window) that leads
outside. It returns a list of directions (e.g., ["north", "east"]).
The planner is deliberately simple: it performs a BFS over the room
connectivity stored in Neo4j and stops when it reaches a room that has an
admissible exit to the outside.
"""

from typing import List, Optional, Dict
from neo4j import Session
import collections

class GraphPlanner:
    """Query Neo4j for room graph and compute a shortest path to an exit."""

    def __init__(self, session: Session):
        self.session = session
        # Cache adjacency list to avoid repeated queries within a run
        self._adjacency: Dict[str, List[Dict[str, str]]] = {}
        self._exit_rooms: set = set()
        self._build_graph()

    def _build_graph(self) -> None:
        """Populate adjacency list and identify rooms with an external exit.

        The Neo4j schema created by LLMPerception stores nodes of type
        `Room` with a `name` property and relationships `CONNECTED_TO`
        with a `direction` property (e.g., north, south). Rooms that have an
        exit to the outside are marked with a relationship `HAS_EXIT` where the
        target node has a label `Exit` and a property `type` set to "outside"
        (or "window").
        """
        # Load rooms and connections
        query = """
        MATCH (r:Room)-[c:CONNECTED_TO]->(nbr:Room)
        RETURN r.name AS room, c.direction AS dir, nbr.name AS neighbor
        """
        result = self.session.run(query)
        for record in result:
            room = record["room"]
            neighbor = record["neighbor"]
            direction = record["dir"]
            self._adjacency.setdefault(room, []).append({"neighbor": neighbor, "direction": direction})

        # Identify rooms that have an external exit
        exit_query = """
        MATCH (r:Room)-[:HAS_EXIT]->(e:Exit)
        WHERE e.type IN ["outside", "window"]
        RETURN r.name AS room
        """
        for rec in self.session.run(exit_query):
            self._exit_rooms.add(rec["room"])

    def plan_to_exit(self, start_room: str) -> Optional[List[str]]:
        """Return a list of directions from *start_room* to the nearest exit.

        If no path is found, ``None`` is returned.
        """
        if start_room not in self._adjacency:
            return None
        # BFS queue stores (current_room, path_so_far)
        queue = collections.deque()
        queue.append((start_room, []))
        visited = {start_room}
        while queue:
            room, path = queue.popleft()
            if room in self._exit_rooms:
                return path  # reached a room with an external exit
            for edge in self._adjacency.get(room, []):
                nbr = edge["neighbor"]
                if nbr in visited:
                    continue
                visited.add(nbr)
                queue.append((nbr, path + [edge["direction"]]))
        return None
