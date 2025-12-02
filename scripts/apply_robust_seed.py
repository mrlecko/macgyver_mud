"""
Apply robust scenario seed to Neo4j if ENABLE_ROBUST_SCENARIO is true.

Adds extended skills/observations/states in parallel to the original seed,
without touching existing nodes.
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # type: ignore
from neo4j import GraphDatabase


ROBUST_CYPHER = """
// Robust skills
MERGE (:Skill {name: 'search_key', kind: 'sense', cost: 1.0, description: 'Search for a key'})
MERGE (:Skill {name: 'disable_alarm', kind: 'act', cost: 1.2, description: 'Disable alarm system'})
MERGE (:Skill {name: 'jam_door', kind: 'act', cost: 1.0, description: 'Jam door mechanism'})
MERGE (:Skill {name: 'try_door_stealth', kind: 'act', cost: 1.0, description: 'Try door quietly'})

// Robust observations
MERGE (:Observation {name: 'obs_alarm_disabled', description: 'Alarm disabled'})
MERGE (:Observation {name: 'obs_alarm_triggered', description: 'Alarm triggered'})
MERGE (:Observation {name: 'obs_key_found', description: 'Key located'})
MERGE (:Observation {name: 'obs_search_failed', description: 'Search did not find a key'})
"""


def apply_robust_seed_to_session(session):
    """
    Apply the robust Cypher seed to an existing Neo4j session.

    Designed for tests/benchmarks to reuse the same seed without
    needing to spawn a new driver.
    """
    session.run(ROBUST_CYPHER)


def main():
    if not config.ENABLE_ROBUST_SCENARIO:
        print("ENABLE_ROBUST_SCENARIO is false; skipping robust seed")
        return
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    with driver.session(database="neo4j") as session:
        apply_robust_seed_to_session(session)
    driver.close()
    print("Robust seed applied.")


if __name__ == "__main__":
    main()
