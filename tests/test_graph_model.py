"""
Unit tests for graph_model.py (Neo4j graph operations)
Requires Neo4j to be running and initialized with cypher_init.cypher
"""
import pytest
from neo4j import GraphDatabase
import config
from graph_model import (
    get_agent,
    get_initial_belief,
    update_belief,
    get_skills,
    create_episode,
    log_step
)


@pytest.fixture(scope="module")
def neo4j_driver():
    """Create Neo4j driver for tests"""
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    yield driver
    driver.close()


@pytest.fixture(scope="module")
def neo4j_session(neo4j_driver):
    """Create Neo4j session for tests"""
    with neo4j_driver.session(database="neo4j") as session:
        yield session


@pytest.fixture(scope="function")
def clean_episodes(neo4j_session):
    """Clean up episode data before each test"""
    neo4j_session.run("MATCH (s:Step) DETACH DELETE s")
    neo4j_session.run("MATCH (e:Episode) DETACH DELETE e")
    yield
    # Cleanup after test too
    neo4j_session.run("MATCH (s:Step) DETACH DELETE s")
    neo4j_session.run("MATCH (e:Episode) DETACH DELETE e")


class TestGetAgent:
    """Test get_agent function"""

    def test_get_agent_exists(self, neo4j_session):
        """Should return agent data when agent exists"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        assert agent is not None
        assert "id" in agent
        assert agent["name"] == "MacGyverBot"

    def test_get_agent_not_exists(self, neo4j_session):
        """Should return None when agent doesn't exist"""
        agent = get_agent(neo4j_session, "NonExistentAgent")
        assert agent is None


class TestGetInitialBelief:
    """Test get_initial_belief function"""

    def test_get_initial_belief(self, neo4j_session):
        """Should return initial belief value"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Reset belief to initial state (may have been modified by other tests)
        update_belief(neo4j_session, agent["id"], "DoorLockState", 0.5)

        belief = get_initial_belief(neo4j_session, agent["id"], "DoorLockState")

        assert belief is not None
        assert isinstance(belief, float)
        assert 0.0 <= belief <= 1.0
        assert belief == pytest.approx(0.5, abs=0.01)  # Initial belief is 0.5

    def test_get_belief_invalid_state_var(self, neo4j_session):
        """Should handle invalid state variable gracefully"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        belief = get_initial_belief(neo4j_session, agent["id"], "NonExistentState")

        # Should return None or raise appropriate error
        assert belief is None or belief == 0.5  # Depending on implementation


class TestUpdateBelief:
    """Test update_belief function"""

    def test_update_belief(self, neo4j_session):
        """Should update belief value in graph"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Get initial value
        initial = get_initial_belief(neo4j_session, agent["id"], "DoorLockState")

        # Update to new value
        new_value = 0.85
        update_belief(neo4j_session, agent["id"], "DoorLockState", new_value)

        # Verify update
        updated = get_initial_belief(neo4j_session, agent["id"], "DoorLockState")
        assert updated == pytest.approx(new_value, abs=0.001)

        # Restore original value for other tests
        update_belief(neo4j_session, agent["id"], "DoorLockState", initial)

    def test_update_belief_multiple_times(self, neo4j_session):
        """Should handle multiple updates correctly"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        values = [0.2, 0.7, 0.3, 0.9]
        for val in values:
            update_belief(neo4j_session, agent["id"], "DoorLockState", val)
            current = get_initial_belief(neo4j_session, agent["id"], "DoorLockState")
            assert current == pytest.approx(val, abs=0.001)

        # Restore
        update_belief(neo4j_session, agent["id"], "DoorLockState", 0.5)


class TestGetSkills:
    """Test get_skills function"""

    def test_get_skills_returns_list(self, neo4j_session):
        """Should return list of skills"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        skills = get_skills(neo4j_session, agent["id"])

        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_get_skills_contains_required_fields(self, neo4j_session):
        """Each skill should have required fields"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        skills = get_skills(neo4j_session, agent["id"])

        for skill in skills:
            assert "name" in skill
            assert "cost" in skill
            assert "kind" in skill
            assert isinstance(skill["cost"], (int, float))
            assert skill["cost"] > 0

    def test_get_skills_contains_expected_skills(self, neo4j_session):
        """Should contain at least the three base skills"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        skills = get_skills(neo4j_session, agent["id"])

        skill_names = {s["name"] for s in skills}
        # Check that base skills are present (may have additional balanced skills)
        base_skills = {"peek_door", "try_door", "go_window"}

        assert base_skills.issubset(skill_names), \
            f"Missing base skills: {base_skills - skill_names}"


class TestCreateEpisode:
    """Test create_episode function"""

    def test_create_episode(self, neo4j_session, clean_episodes):
        """Should create episode and return ID"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        assert episode_id is not None
        assert isinstance(episode_id, str) or isinstance(episode_id, int)

        # Verify episode exists in graph
        result = neo4j_session.run(
            "MATCH (e:Episode) WHERE id(e) = $id OR id(e) = $id "
            "RETURN e.door_state AS door_state",
            id=episode_id
        ).single()

        assert result is not None
        assert result["door_state"] == "locked"

    def test_create_multiple_episodes(self, neo4j_session, clean_episodes):
        """Should create multiple distinct episodes"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        ep1 = create_episode(neo4j_session, agent["id"], "locked")
        ep2 = create_episode(neo4j_session, agent["id"], "unlocked")

        assert ep1 != ep2

        # Verify both exist
        count = neo4j_session.run("MATCH (e:Episode) RETURN count(e) AS count").single()["count"]
        assert count == 2


class TestLogStep:
    """Test log_step function"""

    def test_log_step(self, neo4j_session, clean_episodes):
        """Should create step node with correct properties"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        # Log a step
        log_step(
            neo4j_session,
            episode_id,
            step_index=0,
            skill_name="peek_door",
            observation="obs_door_locked",
            p_before=0.5,
            p_after=0.15
        )

        # Verify step exists and has correct properties
        result = neo4j_session.run("""
            MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
            WHERE id(e) = $ep_id OR id(e) = $ep_id
            RETURN s.step_index AS idx, s.p_before AS p_before, s.p_after AS p_after
        """, ep_id=episode_id).single()

        assert result is not None
        assert result["idx"] == 0
        assert result["p_before"] == pytest.approx(0.5, abs=0.01)
        assert result["p_after"] == pytest.approx(0.15, abs=0.01)

    def test_log_step_relationships(self, neo4j_session, clean_episodes):
        """Should create correct relationships"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        log_step(
            neo4j_session,
            episode_id,
            step_index=0,
            skill_name="peek_door",
            observation="obs_door_locked",
            p_before=0.5,
            p_after=0.15
        )

        # Check relationships exist
        result = neo4j_session.run("""
            MATCH (e:Episode)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
            MATCH (s)-[:OBSERVED]->(o:Observation)
            WHERE id(e) = $ep_id OR id(e) = $ep_id
            RETURN sk.name AS skill, o.name AS obs
        """, ep_id=episode_id).single()

        assert result is not None
        assert result["skill"] == "peek_door"
        assert result["obs"] == "obs_door_locked"

    def test_log_multiple_steps(self, neo4j_session, clean_episodes):
        """Should handle multiple steps in sequence"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        steps = [
            (0, "peek_door", "obs_door_locked", 0.5, 0.15),
            (1, "go_window", "obs_window_escape", 0.15, 0.15)
        ]

        for idx, skill, obs, p_before, p_after in steps:
            log_step(neo4j_session, episode_id, idx, skill, obs, p_before, p_after)

        # Verify both steps exist
        count = neo4j_session.run("""
            MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
            WHERE id(e) = $ep_id OR id(e) = $ep_id
            RETURN count(s) AS count
        """, ep_id=episode_id).single()["count"]

        assert count == 2

    def test_log_step_with_silver_stamp(self, neo4j_session, clean_episodes):
        """Should store silver stamp when provided"""
        from scoring_silver import build_silver_stamp

        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        # Build a silver stamp
        silver_stamp = build_silver_stamp("peek_door", 1.0, 0.5)

        # Log step with silver stamp
        log_step(
            neo4j_session,
            episode_id,
            step_index=0,
            skill_name="peek_door",
            observation="obs_door_locked",
            p_before=0.5,
            p_after=0.15,
            silver_stamp=silver_stamp
        )

        # Verify silver data stored
        result = neo4j_session.run("""
            MATCH (s:Step {step_index: 0})
            RETURN s.silver_stamp AS stamp, s.silver_score AS score
        """).single()

        assert result is not None
        assert result["stamp"] is not None
        assert result["score"] is not None

        # Verify JSON is valid
        import json
        stamp_data = json.loads(result["stamp"])
        assert stamp_data["skill_name"] == "peek_door"
        assert "k_explore" in stamp_data
        assert "k_efficiency" in stamp_data

    def test_log_step_auto_builds_silver(self, neo4j_session, clean_episodes):
        """Should auto-build silver stamp if scoring_silver available"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        # Log step WITHOUT providing silver_stamp
        log_step(
            neo4j_session,
            episode_id,
            step_index=0,
            skill_name="peek_door",
            observation="obs_door_locked",
            p_before=0.5,
            p_after=0.15
        )

        # Should have auto-built silver data
        result = neo4j_session.run("""
            MATCH (s:Step {step_index: 0})
            RETURN s.silver_stamp AS stamp, s.silver_score AS score, s.skill_name AS skill
        """).single()

        assert result is not None
        # Should have convenience field
        assert result["skill"] == "peek_door"
        # Should have silver data (auto-built)
        assert result["stamp"] is not None
        assert result["score"] is not None

    def test_silver_stamp_json_structure(self, neo4j_session, clean_episodes):
        """Silver stamp JSON should have all required fields"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        episode_id = create_episode(neo4j_session, agent["id"], "locked")

        log_step(
            neo4j_session,
            episode_id,
            step_index=0,
            skill_name="try_door",
            observation="obs_door_stuck",
            p_before=0.85,
            p_after=0.10
        )

        result = neo4j_session.run("""
            MATCH (s:Step {step_index: 0})
            RETURN s.silver_stamp AS stamp
        """).single()

        import json
        stamp = json.loads(result["stamp"])

        required_keys = [
            "stamp_version",
            "skill_name",
            "p_unlocked",
            "goal_value",
            "info_gain",
            "cost",
            "base_score",
            "k_explore",
            "k_efficiency",
            "entropy",
            "silver_score"
        ]

        for key in required_keys:
            assert key in stamp, f"Missing required key: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
