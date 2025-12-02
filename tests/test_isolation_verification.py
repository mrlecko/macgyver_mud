"""
Test to verify proper test isolation.

This test checks that each test starts with a clean, predictable state.
"""
import pytest
from neo4j import GraphDatabase
import config


def test_clean_state_no_episodes(neo4j_session):
    """
    Verify that no Episode or Step nodes exist at test start.

    This catches state pollution from previous tests.
    """
    import conftest as test_conftest  # ensure cleanup runs here
    test_conftest.reset_dynamic_data(neo4j_session)

    # Check for Episodes
    result = neo4j_session.run("""
        MATCH (e:Episode)
        RETURN count(e) AS episode_count
    """)
    episode_count = result.single()["episode_count"]
    assert episode_count == 0, f"Found {episode_count} Episode nodes - state not clean!"
    
    # Check for Steps
    result = neo4j_session.run("""
        MATCH (s:Step)
        RETURN count(s) AS step_count
    """)
    step_count = result.single()["step_count"]
    assert step_count == 0, f"Found {step_count} Step nodes - state not clean!"
    
    # Check for EpisodicMemory
    result = neo4j_session.run("""
        MATCH (em:EpisodicMemory)
        RETURN count(em) AS em_count
    """)
    em_count = result.single()["em_count"]
    assert em_count == 0, f"Found {em_count} EpisodicMemory nodes - state not clean!"


def test_skill_stats_reset(neo4j_session):
    """
    Verify that SkillStats counters are reset to zero.
    """
    import conftest as test_conftest
    test_conftest.reset_dynamic_data(neo4j_session)

    result = neo4j_session.run("""
        MATCH (stats:SkillStats)
        RETURN stats.skill_name AS name,
               stats.total_uses AS uses,
               stats.successful_episodes AS successes
    """)
    
    for record in result:
        name = record["name"]
        uses = record["uses"]
        successes = record["successes"]
        assert uses == 0, f"SkillStats for {name} has {uses} uses (should be 0)"
        assert successes == 0, f"SkillStats for {name} has {successes} successes (should be 0)"


def test_belief_reset(neo4j_session):
    """
    Verify that Belief is reset to default (p_unlocked = 0.5).
    """
    import conftest as test_conftest
    test_conftest.reset_dynamic_data(neo4j_session)

    result = neo4j_session.run("""
        MATCH (b:Belief)
        RETURN b.p_unlocked AS p_unlocked
    """)
    
    record = result.single()
    assert record is not None, "Belief node missing!"
    p_unlocked = record["p_unlocked"]
    assert p_unlocked == 0.5, f"Belief p_unlocked = {p_unlocked} (should be 0.5)"



@pytest.mark.order(1)
def test_static_data_present(neo4j_session):

    """
    Verify that static schema data is present (Agent, Skills, etc.).

        This ensures we didn't accidentally delete the schema.
        """
    import conftest as test_conftest
    test_conftest.reset_dynamic_data(neo4j_session)

    # Check Agent
    result = neo4j_session.run("""
        MATCH (a:Agent {name: "MacGyverBot"})
        RETURN count(a) AS agent_count
    """)
    assert result.single()["agent_count"] == 1, "Agent node missing!"
    
    # Check Skills
    result = neo4j_session.run("""
        MATCH (s:Skill)
        RETURN count(s) AS skill_count
    """)
    skill_count = result.single()["skill_count"]
    assert skill_count == 3, f"Expected 3 Skills, found {skill_count}"
    
    # Check SkillStats exist (even if reset)
    result = neo4j_session.run("""
        MATCH (stats:SkillStats)
        RETURN count(stats) AS stats_count
    """)
    stats_count = result.single()["stats_count"]
    assert stats_count == 3, f"Expected 3 SkillStats, found {stats_count}"
