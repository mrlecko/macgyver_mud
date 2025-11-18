"""
Graph model utilities for Neo4j operations
Provides read/write functions for agents, beliefs, skills, episodes, and steps
"""
from typing import Dict, List, Optional, Any
from neo4j import Session
import uuid
from datetime import datetime


def get_agent(session: Session, name: str) -> Optional[Dict[str, Any]]:
    """
    Get agent node by name.

    Args:
        session: Neo4j session
        name: Agent name

    Returns:
        Dict with agent properties including 'id' and 'name', or None if not found
    """
    result = session.run("""
        MATCH (a:Agent {name: $name})
        RETURN id(a) AS id, a.name AS name, a.created_at AS created_at
    """, name=name)

    record = result.single()
    if record:
        return {
            "id": record["id"],
            "name": record["name"],
            "created_at": record.get("created_at")
        }
    return None


def get_initial_belief(session: Session, agent_id: str, statevar_name: str) -> Optional[float]:
    """
    Get agent's current belief about a state variable.

    Args:
        session: Neo4j session
        agent_id: Agent element ID
        statevar_name: Name of state variable

    Returns:
        Belief probability (0 to 1), or None if not found
    """
    result = session.run("""
        MATCH (a:Agent)-[:HAS_BELIEF]->(b:Belief)-[:ABOUT]->(s:StateVar {name: $statevar_name})
        WHERE id(a) = $agent_id
        RETURN b.p_unlocked AS p_unlocked
    """, agent_id=agent_id, statevar_name=statevar_name)

    record = result.single()
    if record and record["p_unlocked"] is not None:
        return float(record["p_unlocked"])
    return None


def update_belief(session: Session, agent_id: str, statevar_name: str, new_value: float) -> None:
    """
    Update agent's belief about a state variable.

    Args:
        session: Neo4j session
        agent_id: Agent element ID
        statevar_name: Name of state variable
        new_value: New belief probability (0 to 1)
    """
    session.run("""
        MATCH (a:Agent)-[:HAS_BELIEF]->(b:Belief)-[:ABOUT]->(s:StateVar {name: $statevar_name})
        WHERE id(a) = $agent_id
        SET b.p_unlocked = $new_value,
            b.last_updated = datetime()
    """, agent_id=agent_id, statevar_name=statevar_name, new_value=new_value)


def get_skills(session: Session, agent_id: str) -> List[Dict[str, Any]]:
    """
    Get all available skills for the agent.

    For v1, we return all skills. In future versions, this could filter
    based on agent location, inventory, etc.

    Args:
        session: Neo4j session
        agent_id: Agent element ID

    Returns:
        List of skill dictionaries with 'name', 'cost', 'kind' properties
    """
    result = session.run("""
        MATCH (s:Skill)
        RETURN s.name AS name, s.cost AS cost, s.kind AS kind, s.description AS description
        ORDER BY s.name
    """)

    skills = []
    for record in result:
        skills.append({
            "name": record["name"],
            "cost": float(record["cost"]),
            "kind": record["kind"],
            "description": record.get("description", "")
        })

    return skills


def create_episode(session: Session, agent_id: str, door_state: str) -> str:
    """
    Create a new episode node representing one simulation run.

    Args:
        session: Neo4j session
        agent_id: Agent element ID
        door_state: Ground truth door state ("locked" or "unlocked")

    Returns:
        Episode element ID
    """
    # Generate unique episode ID
    episode_uuid = str(uuid.uuid4())

    result = session.run("""
        MATCH (a:Agent)
        WHERE id(a) = $agent_id
        CREATE (e:Episode {
            id: $episode_uuid,
            door_state: $door_state,
            created_at: datetime(),
            completed: false
        })
        CREATE (a)-[:PERFORMED_EPISODE]->(e)
        RETURN id(e) AS episode_id
    """, agent_id=agent_id, episode_uuid=episode_uuid, door_state=door_state)

    record = result.single()
    return record["episode_id"]


def log_step(session: Session, episode_id: str, step_index: int,
             skill_name: str, obs_name: str,
             p_before: float, p_after: float) -> None:
    """
    Log a single step in an episode.

    Creates a Step node and links it to:
    - Episode (via HAS_STEP)
    - Skill used (via USED_SKILL)
    - Observation received (via OBSERVED)

    Args:
        session: Neo4j session
        episode_id: Episode element ID
        step_index: Step number (0-indexed)
        skill_name: Name of skill used
        obs_name: Name of observation received
        p_before: Belief before action
        p_after: Belief after observation
    """
    session.run("""
        MATCH (e:Episode)
        WHERE id(e) = $episode_id
        MATCH (sk:Skill {name: $skill_name})
        MATCH (o:Observation {name: $obs_name})
        CREATE (s:Step {
            step_index: $step_index,
            p_before: $p_before,
            p_after: $p_after,
            timestamp: datetime()
        })
        CREATE (e)-[:HAS_STEP]->(s)
        CREATE (s)-[:USED_SKILL]->(sk)
        CREATE (s)-[:OBSERVED]->(o)
    """, episode_id=episode_id, step_index=step_index,
        skill_name=skill_name, obs_name=obs_name,
        p_before=p_before, p_after=p_after)


def mark_episode_complete(session: Session, episode_id: str,
                          escaped: bool, total_steps: int) -> None:
    """
    Mark an episode as complete.

    Args:
        session: Neo4j session
        episode_id: Episode element ID
        escaped: Whether agent successfully escaped
        total_steps: Total number of steps taken
    """
    session.run("""
        MATCH (e:Episode)
        WHERE id(e) = $episode_id
        SET e.completed = true,
            e.escaped = $escaped,
            e.total_steps = $total_steps,
            e.completed_at = datetime()
    """, episode_id=episode_id, escaped=escaped, total_steps=total_steps)


def get_episode_stats(session: Session, episode_id: str) -> Dict[str, Any]:
    """
    Get statistics for an episode.

    Args:
        session: Neo4j session
        episode_id: Episode element ID

    Returns:
        Dict with episode stats
    """
    result = session.run("""
        MATCH (e:Episode)
        WHERE id(e) = $episode_id
        OPTIONAL MATCH (e)-[:HAS_STEP]->(s:Step)
        RETURN e.id AS id,
               e.door_state AS door_state,
               e.escaped AS escaped,
               e.total_steps AS total_steps,
               count(s) AS step_count
    """, episode_id=episode_id)

    record = result.single()
    if record:
        return {
            "id": record["id"],
            "door_state": record["door_state"],
            "escaped": record.get("escaped"),
            "total_steps": record.get("total_steps"),
            "step_count": record["step_count"]
        }
    return {}


# Utility function for debugging
def get_episode_trace(session: Session, episode_id: str) -> List[Dict[str, Any]]:
    """
    Get full trace of an episode (all steps in order).

    Args:
        session: Neo4j session
        episode_id: Episode element ID

    Returns:
        List of step dictionaries in order
    """
    result = session.run("""
        MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
        MATCH (s)-[:USED_SKILL]->(sk:Skill)
        MATCH (s)-[:OBSERVED]->(o:Observation)
        WHERE id(e) = $episode_id
        RETURN s.step_index AS step_index,
               sk.name AS skill,
               o.name AS observation,
               s.p_before AS p_before,
               s.p_after AS p_after,
               s.timestamp AS timestamp
        ORDER BY s.step_index
    """, episode_id=episode_id)

    trace = []
    for record in result:
        trace.append({
            "step_index": record["step_index"],
            "skill": record["skill"],
            "observation": record["observation"],
            "p_before": record["p_before"],
            "p_after": record["p_after"],
            "timestamp": record["timestamp"]
        })

    return trace


if __name__ == "__main__":
    # Quick manual test
    from neo4j import GraphDatabase
    import config

    print("=== Graph Model Test ===\n")

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Test get_agent
        agent = get_agent(session, "MacGyverBot")
        print(f"Agent: {agent}")

        # Test get_initial_belief
        belief = get_initial_belief(session, agent["id"], "DoorLockState")
        print(f"Initial belief: {belief}")

        # Test get_skills
        skills = get_skills(session, agent["id"])
        print(f"\nSkills ({len(skills)}):")
        for skill in skills:
            print(f"  {skill['name']:12s} - cost={skill['cost']}, kind={skill['kind']}")

    driver.close()
    print("\n✓ Graph model functions work!")
