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


def cleanup_neo4j(session):
    """Wipe the entire database."""
    session.run("MATCH (n) DETACH DELETE n")

def init_neo4j(session):
    """Initialize database with schema and default data."""
    # Read cypher_init.cypher
    init_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cypher_init.cypher")
    with open(init_file, "r") as f:
        cypher_script = f.read()
    
    # Split by semicolon to get individual statements
    # (Simple split, assumes no semicolons in strings/comments which is true for this file)
    statements = cypher_script.split(";")
    
    for statement in statements:
        if statement.strip():
            session.run(statement)

@pytest.fixture(scope="function", autouse=True)
def reset_neo4j_state():
    """
    Reset Neo4j state BEFORE each test to ensure isolation.
    
    CRITICAL: Cleanup runs BEFORE the test (not after) to prevent
    test pollution where previous test's data affects current test.
    """
    import config
    
    # Cleanup BEFORE test runs
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        with driver.session(database="neo4j") as session:
            cleanup_neo4j(session)
            init_neo4j(session)
            
        driver.close()
    except Exception as e:
        # Silently ignore cleanup errors (Neo4j might not be ready yet)
        print(f"Warning: Neo4j reset failed: {e}")
        pass
    
    # Now run the test with clean state
    yield
