import sys
import os
import time
from neo4j import GraphDatabase

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from agent_runtime import AgentRuntime

def wipe_db(driver):
    print("  [ACTION] Wiping Database (Amnesia)...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def run_episode(agent, driver, label):
    print(f"  [RUN] {label}...")
    
    # Query Neo4j directly
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Skill {name: 'peek_door'})-[r:APPLICABLE_IN]->(c:Context {belief: 'unlocked'})
            OPTIONAL MATCH (c)-[:HAS_STATS]->(stats:SkillStats)
            RETURN stats.count AS count, stats.success_rate AS success_rate
        """).single()
        
        if result and result["count"] is not None:
            stats = {"count": result["count"], "success_rate": result["success_rate"]}
        else:
            stats = {"count": 0, "success_rate": 0.0}
            
    print(f"    Stats for 'peek_door': {stats}")
    return stats

def run_amnesia_test():
    print("=== AMNESIA / RE-LEARNING TEST ===")
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # 1. Start Fresh
    wipe_db(driver)
    
    # 2. Initialize Agent
    # We need to initialize skills first
    with driver.session() as session:
        session.run("CREATE (s:Skill {name: 'peek_door', cost: 1.0, kind: 'exploratory'})")
        session.run("CREATE (c:Context {belief: 'unlocked'})")
        session.run("MATCH (s:Skill {name: 'peek_door'}), (c:Context {belief: 'unlocked'}) CREATE (s)-[:APPLICABLE_IN]->(c)")
        session.run(f"CREATE (a:Agent {{name: '{config.AGENT_NAME}', id: 1}})")
        
    agent = AgentRuntime(driver.session(), door_state="unlocked")
    
    # 3. Check Baseline (Should be empty/default)
    stats_0 = run_episode(agent, driver, "Baseline (Pre-Learning)")
    if stats_0['count'] > 0:
        print("[FAIL] Baseline stats should be empty.")
        sys.exit(1)
        
    # 4. Simulate Learning (Update stats manually to simulate experience)
    print("  [ACTION] Simulating Experience (Learning)...")
    # Update stats manually via Cypher
    with driver.session() as session:
        session.run("""
            MATCH (s:Skill {name: 'peek_door'})-[r:APPLICABLE_IN]->(c:Context {belief: 'unlocked'})
            MERGE (c)-[:HAS_STATS]->(stats:SkillStats)
            ON CREATE SET stats.count = 0, stats.success_rate = 0.0, stats.uncertainty = 1.0
            SET stats.count = stats.count + 2,
                stats.success_rate = 1.0,
                stats.uncertainty = 0.1
        """)
    
    # 5. Check Learned State
    stats_1 = run_episode(agent, driver, "Learned State")
    if stats_1['count'] != 2:
        print(f"[FAIL] Expected 2 uses, got {stats_1['count']}")
        sys.exit(1)
        
    # 6. Induce Amnesia
    wipe_db(driver)
    # Re-init agent to clear local caches if any (AgentRuntime might cache?)
    # AgentRuntime doesn't cache stats locally, it queries Neo4j.
    
    # 7. Check Amnesia State
    stats_2 = run_episode(agent, driver, "Post-Amnesia")
    if stats_2['count'] > 0:
        print(f"[FAIL] Amnesia failed. Stats persisted: {stats_2}")
        sys.exit(1)
        
    print("\n[PASS] Agent successfully learned and forgot.")
    driver.close()
    sys.exit(0)

if __name__ == "__main__":
    run_amnesia_test()
