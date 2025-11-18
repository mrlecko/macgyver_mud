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


# ============================================================================
# Procedural Memory Functions (Skill Statistics & Meta-Learning)
# ============================================================================

def get_skill_stats(session: Session, skill_name: str,
                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get skill statistics, optionally filtered by context.

    Context can include:
    - belief_category: "uncertain", "confident_locked", "confident_unlocked"

    Returns context-specific success rates when available.

    Args:
        session: Neo4j session
        skill_name: Name of the skill
        context: Optional context filter

    Returns:
        Dict with overall and context-specific stats
    """
    result = session.run("""
        MATCH (sk:Skill {name: $skill_name})-[:HAS_STATS]->(stats:SkillStats)
        RETURN stats
    """, skill_name=skill_name)

    record = result.single()
    if not record:
        # Return empty stats if not found
        return {
            "overall": {
                "uses": 0,
                "success_rate": 0.5,  # Prior: 50/50
                "confidence": 0.0,
                "avg_steps": 0.0
            }
        }

    stats = dict(record["stats"])

    # Calculate overall statistics
    total = stats["total_uses"]
    overall_success_rate = (
        stats["successful_episodes"] / total if total > 0 else 0.5
    )
    overall_confidence = min(1.0, total / 20.0)  # Full confidence at 20 uses

    result_dict = {
        "overall": {
            "uses": total,
            "success_rate": overall_success_rate,
            "confidence": overall_confidence,
            "avg_steps": stats["avg_steps_when_successful"]
        }
    }

    # Add context-specific statistics if requested
    if context and "belief_category" in context:
        cat = context["belief_category"]

        # Map category to field names
        if cat == "uncertain":
            uses = stats.get("uncertain_uses", 0)
            successes = stats.get("uncertain_successes", 0)
        elif cat == "confident_locked":
            uses = stats.get("confident_locked_uses", 0)
            successes = stats.get("confident_locked_successes", 0)
        elif cat == "confident_unlocked":
            uses = stats.get("confident_unlocked_uses", 0)
            successes = stats.get("confident_unlocked_successes", 0)
        else:
            uses = 0
            successes = 0

        if uses > 0:
            result_dict["belief_context"] = {
                "uses": uses,
                "success_rate": successes / uses,
                "confidence": min(1.0, uses / 10.0),  # Context confidence at 10 uses
                "category": cat
            }

    return result_dict


def update_skill_stats(session: Session, episode_id: str,
                      escaped: bool, total_steps: int,
                      context: Dict[str, Any]) -> None:
    """
    Update skill statistics based on episode outcome.

    Updates both overall and context-specific stats.

    Args:
        session: Neo4j session
        episode_id: Episode element ID
        escaped: Whether agent successfully escaped
        total_steps: Total number of steps taken
        context: Context dict with belief_category
    """
    belief_cat = context.get("belief_category", "uncertain")

    session.run("""
        // Get all skills used in this episode
        MATCH (e:Episode)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
        WHERE id(e) = $episode_id
        MATCH (sk)-[:HAS_STATS]->(stats:SkillStats)

        WITH sk, stats, count(s) AS uses_in_episode

        // Update overall statistics
        SET stats.total_uses = stats.total_uses + uses_in_episode,
            stats.successful_episodes = stats.successful_episodes +
                CASE WHEN $escaped THEN 1 ELSE 0 END,
            stats.failed_episodes = stats.failed_episodes +
                CASE WHEN NOT $escaped THEN 1 ELSE 0 END,

            // Update average steps when successful
            stats.avg_steps_when_successful =
                CASE WHEN $escaped AND stats.successful_episodes > 0 THEN
                    (stats.avg_steps_when_successful * (stats.successful_episodes - 1) + $total_steps)
                    / stats.successful_episodes
                ELSE stats.avg_steps_when_successful END,

            // Update average steps when failed
            stats.avg_steps_when_failed =
                CASE WHEN NOT $escaped AND stats.failed_episodes > 0 THEN
                    (stats.avg_steps_when_failed * (stats.failed_episodes - 1) + $total_steps)
                    / stats.failed_episodes
                ELSE stats.avg_steps_when_failed END,

            // Update context-specific stats (belief category)
            stats.uncertain_uses = stats.uncertain_uses +
                CASE WHEN $belief_cat = 'uncertain' THEN uses_in_episode ELSE 0 END,
            stats.uncertain_successes = stats.uncertain_successes +
                CASE WHEN $belief_cat = 'uncertain' AND $escaped THEN 1 ELSE 0 END,

            stats.confident_locked_uses = stats.confident_locked_uses +
                CASE WHEN $belief_cat = 'confident_locked' THEN uses_in_episode ELSE 0 END,
            stats.confident_locked_successes = stats.confident_locked_successes +
                CASE WHEN $belief_cat = 'confident_locked' AND $escaped THEN 1 ELSE 0 END,

            stats.confident_unlocked_uses = stats.confident_unlocked_uses +
                CASE WHEN $belief_cat = 'confident_unlocked' THEN uses_in_episode ELSE 0 END,
            stats.confident_unlocked_successes = stats.confident_unlocked_successes +
                CASE WHEN $belief_cat = 'confident_unlocked' AND $escaped THEN 1 ELSE 0 END,

            stats.last_updated = datetime()
    """, episode_id=episode_id, escaped=escaped, total_steps=total_steps,
         belief_cat=belief_cat)


def get_meta_params(session: Session, agent_id: str) -> Dict[str, Any]:
    """
    Get current meta-parameters for agent.

    Args:
        session: Neo4j session
        agent_id: Agent element ID

    Returns:
        Dict with alpha, beta, gamma and learning metrics
    """
    result = session.run("""
        MATCH (a:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
        WHERE id(a) = $agent_id
        RETURN meta.alpha AS alpha,
               meta.beta AS beta,
               meta.gamma AS gamma,
               meta.episodes_completed AS episodes,
               meta.adaptation_enabled AS adaptive,
               meta.avg_steps_last_10 AS avg_steps,
               meta.success_rate_last_10 AS success_rate
    """, agent_id=agent_id)

    record = result.single()
    if record:
        return {
            "alpha": record["alpha"],
            "beta": record["beta"],
            "gamma": record["gamma"],
            "episodes": record["episodes"],
            "adaptive": record["adaptive"],
            "avg_steps": record["avg_steps"],
            "success_rate": record["success_rate"]
        }

    # Fallback to config defaults if no MetaParams found
    return {
        "alpha": config.ALPHA,
        "beta": config.BETA,
        "gamma": config.GAMMA,
        "episodes": 0,
        "adaptive": False,
        "avg_steps": 0.0,
        "success_rate": 0.0
    }


def update_meta_params(session: Session, agent_id: str,
                      new_params: Dict[str, Any]) -> None:
    """
    Update agent's meta-parameters and track history.

    Args:
        session: Neo4j session
        agent_id: Agent element ID
        new_params: Dict with alpha, beta, gamma, and/or learning metrics
    """
    # Build SET clause dynamically based on what's provided
    set_clauses = []
    params = {"agent_id": agent_id}

    if "alpha" in new_params:
        set_clauses.append("meta.alpha = $alpha")
        set_clauses.append("meta.alpha_history = meta.alpha_history + $alpha")
        params["alpha"] = new_params["alpha"]

    if "beta" in new_params:
        set_clauses.append("meta.beta = $beta")
        set_clauses.append("meta.beta_history = meta.beta_history + $beta")
        params["beta"] = new_params["beta"]

    if "gamma" in new_params:
        set_clauses.append("meta.gamma = $gamma")
        set_clauses.append("meta.gamma_history = meta.gamma_history + $gamma")
        params["gamma"] = new_params["gamma"]

    if "episodes_completed" in new_params:
        set_clauses.append("meta.episodes_completed = $episodes")
        params["episodes"] = new_params["episodes_completed"]

    if "avg_steps_last_10" in new_params:
        set_clauses.append("meta.avg_steps_last_10 = $avg_steps")
        params["avg_steps"] = new_params["avg_steps_last_10"]

    if "success_rate_last_10" in new_params:
        set_clauses.append("meta.success_rate_last_10 = $success_rate")
        params["success_rate"] = new_params["success_rate_last_10"]

    set_clauses.append("meta.last_adapted = datetime()")

    if set_clauses:
        query = f"""
            MATCH (a:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            WHERE id(a) = $agent_id
            SET {', '.join(set_clauses)}
        """
        session.run(query, **params)


def get_recent_episodes_stats(session: Session, agent_id: str,
                              limit: int = 10) -> Dict[str, Any]:
    """
    Get statistics from recent episodes for meta-learning.

    Args:
        session: Neo4j session
        agent_id: Agent element ID
        limit: Number of recent episodes to analyze

    Returns:
        Dict with avg_steps, success_rate, variance, count
    """
    # Note: In the current implementation, we don't have PARTICIPATED_IN relationship
    # So we'll just get recent episodes by creation time
    result = session.run("""
        MATCH (e:Episode)
        WHERE e.completed = true
        WITH e ORDER BY e.created_at DESC LIMIT $limit
        WITH count(e) AS episode_count,
             avg(e.total_steps) AS avg_steps,
             stDev(e.total_steps) AS steps_variance,
             collect(e) AS episodes
        RETURN episode_count,
               avg_steps,
               steps_variance,
               CASE WHEN episode_count > 0 THEN
                   toFloat(size([ep IN episodes WHERE ep.escaped | 1])) / episode_count
               ELSE 0.0 END AS success_rate
    """, limit=limit)

    record = result.single()
    if record and record["episode_count"] and record["episode_count"] > 0:
        return {
            "avg_steps": float(record["avg_steps"]) if record["avg_steps"] else 0.0,
            "success_rate": float(record["success_rate"]) if record["success_rate"] else 0.0,
            "variance": float(record["steps_variance"]) if record["steps_variance"] else 0.0,
            "count": int(record["episode_count"])
        }

    return {"avg_steps": 0.0, "success_rate": 0.0, "variance": 0.0, "count": 0}


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
