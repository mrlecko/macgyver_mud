"""
Pytest configuration for MacGyver MUD tests.

Ensures all tests use the correct Neo4j connection settings (port 17687)
to match the Docker configuration and avoid conflicts with default Neo4j installations.
"""
import os
import pytest
from neo4j import GraphDatabase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up test environment variables before any tests run.
    
    This ensures all tests use port 17687 for Neo4j, matching the
    Docker setup and avoiding conflicts with default installations.
    """
    os.environ["NEO4J_URI"] = "bolt://localhost:17687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    
    # Reload config module to pick up environment variables
    import config
    import importlib
    importlib.reload(config)
    
    yield
    
    # Cleanup after all tests
    pass


@pytest.fixture(scope="session")
def verify_neo4j_connection():
    """Verify Neo4j is accessible before running tests."""
    import config
    
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        with driver.session(database="neo4j") as session:
            result = session.run("RETURN 1 AS test")
            assert result.single()["test"] == 1
        driver.close()
    except Exception as e:
        pytest.fail(f"Neo4j connection failed: {e}. Make sure Neo4j is running on port 17687 (run 'make neo4j-start')")


@pytest.fixture(scope="function", autouse=True)
def reset_neo4j_state():
    """
    Reset Neo4j state BEFORE each test to ensure isolation.
    
    CRITICAL: Cleanup runs BEFORE the test (not after) to prevent
    test pollution where previous test's data affects current test.
    """
    import config
    
    # Cleanup BEFORE test runs (this is the key fix!)
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        with driver.session(database="neo4j") as session:
            # Delete episode/step data created by previous tests
            session.run("MATCH (s:Step) DETACH DELETE s")
            session.run("MATCH (e:Episode) DETACH DELETE e")
            session.run("MATCH (c:Counterfactual) DETACH DELETE c")
            
            # Reset skill stats to zero
            session.run("""
                MATCH (stats:SkillStats)
                SET stats.total_uses = 0,
                    stats.successful_episodes = 0,
                    stats.failed_episodes = 0,
                    stats.avg_steps_when_successful = 0.0,
                    stats.avg_steps_when_failed = 0.0,
                    stats.uncertain_uses = 0,
                    stats.uncertain_successes = 0,
                    stats.confident_locked_uses = 0,
                    stats.confident_locked_successes = 0,
                    stats.confident_unlocked_uses = 0,
                    stats.confident_unlocked_successes = 0
            """)
            
            # Reset belief to default
            session.run("""
                MATCH (b:Belief)
                SET b.p_unlocked = 0.5
            """)
            
            # Reset meta params to defaults
            session.run("""
                MATCH (meta:MetaParams)
                SET meta.alpha = 1.0,
                    meta.beta = 6.0,
                    meta.gamma = 0.3,
                    meta.episodes_completed = 0,
                    meta.avg_steps_last_10 = 0.0,
                    meta.success_rate_last_10 = 0.0
            """)
        driver.close()
    except Exception:
        # Silently ignore cleanup errors (Neo4j might not be ready yet)
        pass
    
    # Now run the test with clean state
    yield
    
    # Optionally cleanup after test too (but main cleanup is above)
    # This helps keep Neo4j clean but isn't critical for test isolation
