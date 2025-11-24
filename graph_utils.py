from neo4j import Session

def update_graph_from_state(session: Session, state: dict) -> None:
    """Create or merge Room nodes and CONNECTED_TO relationships based on parsed perception state.

    Expected ``state`` keys:
        - ``room_name``: name of the current room (string)
        - ``exits``: list of direction strings (e.g., ["north", "east"])
        - ``items``: list of item dicts (ignored for graph connectivity)
    """
    room = state.get("room_name")
    exits = state.get("exits", [])
    if not room:
        return
    # Ensure the current room node exists
    session.run("MERGE (r:Room {name: $name})", name=room)
    # For each exit, create a placeholder neighbor and a CONNECTED_TO relationship
    for direction in exits:
        # Simple placeholder neighbor name – can be refined later when that room is observed
        neighbor = f"{room}_{direction}"
        session.run("MERGE (n:Room {name: $n})", n=neighbor)
        session.run(
            """
            MATCH (r:Room {name: $room}), (n:Room {name: $neighbor})
            MERGE (r)-[c:CONNECTED_TO {direction: $dir}]->(n)
            """,
            room=room,
            neighbor=neighbor,
            dir=direction,
        )
    # Mark rooms that have an external exit (e.g., "outside" or "window")
    if any(e.lower() in ("outside", "window") for e in exits):
        session.run("MERGE (r:Room {name: $name}) SET r.is_exit = true", name=room)
