"""
Pytest configuration for MacGyver MUD tests.

Implements proper test isolation with session-scoped schema initialization
and function-scoped selective cleanup for optimal performance.
"""
import os
import pytest
from neo4j import GraphDatabase

# Import scenario fixtures explicitly so they register as fixtures
try:
    from tests.conftest_scenarios import noisy_room_model, two_step_key_model  # type: ignore  # noqa: F401
    from tests.conftest_scenarios import robust_room_model  # type: ignore  # noqa: F401
except ImportError:
    # Fallback for running via python -m pytest from repo root
    import importlib.util
    import pathlib
    _spec = importlib.util.spec_from_file_location("tests.conftest_scenarios", pathlib.Path(__file__).parent / "conftest_scenarios.py")
    module = importlib.util.module_from_spec(_spec)
    assert _spec and _spec.loader
    _spec.loader.exec_module(module)  # type: ignore
    noisy_room_model = module.noisy_room_model  # type: ignore
    two_step_key_model = module.two_step_key_model  # type: ignore
    robust_room_model = module.robust_room_model  # type: ignore


# =============================================================================
# Session-Scoped Setup
# =============================================================================

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
    if os.environ.get("SKIP_NEO4J_TESTS") == "1":
        pytest.skip("Skipping Neo4j availability check for unit-only tests")
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


@pytest.fixture(scope="session")
def neo4j_schema():
    """
    Initialize database schema ONCE per test session.
    
    This runs cypher_init.cypher to create all static data (Agent, Skills, etc.).
    This data persists across all tests in the session.
    """
    if os.environ.get("SKIP_NEO4J_TESTS") == "1":
        # Unit-only runs can bypass the database entirely
        yield
        return
    import config
    
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    
    with driver.session(database="neo4j") as session:
        # First, wipe everything
        session.run("MATCH (n) DETACH DELETE n")
        
        # Then initialize schema from cypher_init.cypher
        init_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cypher_init.cypher")
        with open(init_file, "r") as f:
            cypher_script = f.read()
        
        # Split by semicolon to get individual statements
        statements = cypher_script.split(";")
        
        for statement in statements:
            if statement.strip():
                session.run(statement)
    
    driver.close()
    
    yield
    
    # Session cleanup (optional - could wipe DB here)
    pass


# =============================================================================
# Test-Level Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def neo4j_session(neo4j_schema):
    """
    Provide a Neo4j session for each test.
    
    Depends on neo4j_schema to ensure schema is initialized before tests run.
    """
    import config
    
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    
    yield session
    
    session.close()
    driver.close()


# =============================================================================
# Cleanup Fixtures
# =============================================================================

def reset_dynamic_data(session):
    """
    Clean only dynamic test data, preserving static schema.
    
    Deletes:
    - Episode nodes (both :Episode and :TextWorldEpisode)
    - Step nodes
    - EpisodicMemory nodes
    - Counterfactual nodes
    - ActualPath nodes
    - GeometricAnalysis nodes (created during tests)
    - Robust opt-in skills/observations (to keep base schema clean)
    
    Resets:
    - SkillStats counters to zero
    - Belief.p_unlocked to 0.5
    - MetaParams to default values
    """
    # Delete dynamic nodes in one query
    session.run("""
        MATCH (n)
        WHERE n:Episode OR n:Step OR n:EpisodicMemory OR n:Counterfactual 
           OR n:ActualPath OR n:GeometricAnalysis
        DETACH DELETE n
    """)

    # Remove robust opt-in skills/observations so baseline tests see only core schema
    session.run("""
        MATCH (s:Skill)
        WHERE s.name IN ['search_key','disable_alarm','jam_door','try_door_stealth','sense','open_door']
        DETACH DELETE s
    """)
    session.run("""
        MATCH (o:Observation)
        WHERE o.name IN ['obs_alarm_disabled','obs_alarm_triggered','obs_key_found','obs_search_failed']
        DETACH DELETE o
    """)
    
    # Reset SkillStats counters
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
            stats.confident_unlocked_successes = 0,
            stats.counterfactual_adjusted = false,
            stats.success_rate = null
    """)
    
    # Reset Belief to default
    session.run("""
        MATCH (b:Belief)
        SET b.p_unlocked = 0.5
    """)
    
    # Reset MetaParams to defaults
    session.run("""
        MATCH (meta:MetaParams)
        SET meta.alpha = 1.0,
            meta.beta = 6.0,
            meta.gamma = 0.3,
            meta.alpha_history = [1.0],
            meta.beta_history = [6.0],
            meta.gamma_history = [0.3],
            meta.episodes_completed = 0,
            meta.avg_steps_last_10 = 0.0,
            meta.success_rate_last_10 = 0.0
    """)

    # Ensure all skills have a cost to avoid scoring warnings
    session.run("""
        MATCH (s:Skill)
        WHERE s.cost IS NULL
        SET s.cost = 1.0
    """)


@pytest.fixture(scope="function", autouse=True)
def reset_neo4j_state(neo4j_schema):
    """
    Reset Neo4j state BEFORE each test to ensure isolation.
    
    This is auto-used for all tests. It performs selective cleanup
    instead of full database wipe, making tests much faster.
    """
    if os.environ.get("SKIP_NEO4J_TESTS") == "1":
        yield
        return
    import config
    
    # Cleanup BEFORE test runs
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        with driver.session(database="neo4j") as session:
            reset_dynamic_data(session)
            
        driver.close()
    except Exception as e:
        # Log but don't fail - some tests might not need Neo4j
        print(f"Warning: Neo4j reset failed: {e}")
        pass
    
    # Now run the test with clean state
    yield


# =============================================================================
# Optional: Full Reset Fixture
# =============================================================================

@pytest.fixture(scope="function")
def clean_slate():
    """
    Full database wipe and re-initialization.
    
    Available for tests that explicitly need completely fresh state.
    Most tests should NOT use this - use the auto reset_neo4j_state instead.
    """
    import config
    
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    
    with driver.session(database="neo4j") as session:
        # Wipe everything
        session.run("MATCH (n) DETACH DELETE n")
        
        # Re-run init script
        init_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cypher_init.cypher")
        with open(init_file, "r") as f:
            cypher_script = f.read()
        
        statements = cypher_script.split(";")
        for statement in statements:
            if statement.strip():
                session.run(statement)
    
    driver.close()
    
    yield
