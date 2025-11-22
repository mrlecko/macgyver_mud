"""
Unit tests for procedural memory functionality
Tests skill statistics tracking, meta-parameter adaptation, and learning metrics
"""
import pytest
from neo4j import GraphDatabase
import config
from graph_model import (
    get_agent,
    get_skill_stats,
    update_skill_stats,
    get_meta_params,
    update_meta_params,
    get_recent_episodes_stats,
    create_episode,
    log_step,
    mark_episode_complete
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
def clean_memory(neo4j_session):
    """Clean up episode data and reset skill stats before each test"""
    # Clean episodes
    neo4j_session.run("MATCH (s:Step) DETACH DELETE s")
    neo4j_session.run("MATCH (e:Episode) DETACH DELETE e")

    # Reset skill stats
    neo4j_session.run("""
        MATCH (sk:Skill)-[:HAS_STATS]->(stats:SkillStats)
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

    # Reset meta params
    neo4j_session.run("""
        MATCH (a:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
        SET meta.alpha = 1.0,
            meta.beta = 6.0,
            meta.gamma = 0.3,
            meta.episodes_completed = 0,
            meta.avg_steps_last_10 = 0.0,
            meta.success_rate_last_10 = 0.0
    """)

    yield

    # Cleanup after test too
    neo4j_session.run("MATCH (s:Step) DETACH DELETE s")
    neo4j_session.run("MATCH (e:Episode) DETACH DELETE e")


class TestSkillStats:
    """Test skill statistics tracking"""

    def test_initial_stats_empty(self, neo4j_session, clean_memory):
        """Newly created stats should have zero counts"""
        stats = get_skill_stats(neo4j_session, "peek_door")

        assert stats["overall"]["uses"] == 0
        assert stats["overall"]["success_rate"] == 0.5  # Prior
        assert stats["overall"]["confidence"] == 0.0

    def test_stats_update_increments_uses(self, neo4j_session, clean_memory):
        """Stats should increment after episode"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Create and run episode
        episode_id = create_episode(neo4j_session, agent["id"], "locked")
        log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)
        mark_episode_complete(neo4j_session, episode_id, True, 2)

        context = {"belief_category": "uncertain"}
        update_skill_stats(neo4j_session, episode_id, True, 2, context)

        stats = get_skill_stats(neo4j_session, "peek_door")
        assert stats["overall"]["uses"] == 1
        assert stats["overall"]["success_rate"] > 0

    def test_context_specific_stats(self, neo4j_session, clean_memory):
        """Should track context-specific performance"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Run multiple episodes with uncertain context
        for i in range(5):
            episode_id = create_episode(neo4j_session, agent["id"], "locked")
            log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)
            mark_episode_complete(neo4j_session, episode_id, True, 2)

            context = {"belief_category": "uncertain"}
            update_skill_stats(neo4j_session, episode_id, True, 2, context)

        stats = get_skill_stats(
            neo4j_session, "peek_door",
            context={"belief_category": "uncertain"}
        )

        assert "belief_context" in stats
        assert stats["belief_context"]["uses"] == 5
        assert stats["belief_context"]["category"] == "uncertain"

    def test_success_rate_calculation(self, neo4j_session, clean_memory):
        """Should correctly calculate success rates"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Run 10 episodes: 7 successful, 3 failed
        for i in range(10):
            episode_id = create_episode(neo4j_session, agent["id"], "locked")
            log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)

            escaped = i < 7  # First 7 succeed
            mark_episode_complete(neo4j_session, episode_id, escaped, 2)

            context = {"belief_category": "uncertain"}
            update_skill_stats(neo4j_session, episode_id, escaped, 2, context)

        stats = get_skill_stats(neo4j_session, "peek_door")
        assert stats["overall"]["uses"] == 10

        # Success rate should be 70% (7 out of 10)
        assert abs(stats["overall"]["success_rate"] - 0.7) < 0.01

    def test_confidence_grows_with_samples(self, neo4j_session, clean_memory):
        """Confidence should grow with number of samples"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Test with different sample sizes
        for n_episodes in [1, 10, 20, 30]:
            # Reset stats
            neo4j_session.run("""
                MATCH (sk:Skill {name: "try_door"})-[:HAS_STATS]->(stats)
                SET stats.total_uses = 0,
                    stats.successful_episodes = 0
            """)

            # Run n episodes
            for i in range(n_episodes):
                episode_id = create_episode(neo4j_session, agent["id"], "unlocked")
                log_step(neo4j_session, episode_id, 0, "try_door", "obs_door_opened", 0.9, 0.99)
                mark_episode_complete(neo4j_session, episode_id, True, 1)

                context = {"belief_category": "confident_unlocked"}
                update_skill_stats(neo4j_session, episode_id, True, 1, context)

            stats = get_skill_stats(neo4j_session, "try_door")

            # Confidence = min(1.0, uses / 20.0)
            expected_confidence = min(1.0, n_episodes / 20.0)
            assert abs(stats["overall"]["confidence"] - expected_confidence) < 0.01


class TestMetaParams:
    """Test meta-parameter tracking and adaptation"""

    def test_get_initial_meta_params(self, neo4j_session, clean_memory):
        """Should return default meta parameters"""
        agent = get_agent(neo4j_session, "MacGyverBot")
        params = get_meta_params(neo4j_session, agent["id"])

        assert params["alpha"] == 1.0
        assert params["beta"] == 6.0
        assert params["gamma"] == 0.3
        assert params["episodes"] == 0

    def test_update_meta_params(self, neo4j_session, clean_memory):
        """Should update and track parameter history"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        new_params = {"alpha": 1.2, "beta": 5.5, "gamma": 0.35}
        update_meta_params(neo4j_session, agent["id"], new_params)

        params = get_meta_params(neo4j_session, agent["id"])
        assert params["alpha"] == 1.2
        assert params["beta"] == 5.5
        assert params["gamma"] == 0.35

    def test_partial_param_update(self, neo4j_session, clean_memory):
        """Should allow updating individual parameters"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Update only beta
        update_meta_params(neo4j_session, agent["id"], {"beta": 7.0})

        params = get_meta_params(neo4j_session, agent["id"])
        assert params["alpha"] == 1.0  # Unchanged
        assert params["beta"] == 7.0   # Changed
        assert params["gamma"] == 0.3  # Unchanged

    def test_episode_count_tracking(self, neo4j_session, clean_memory):
        """Should track episode count correctly"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        for i in range(1, 6):
            update_meta_params(neo4j_session, agent["id"], {"episodes_completed": i})

            params = get_meta_params(neo4j_session, agent["id"])
            assert params["episodes"] == i


class TestRecentEpisodesStats:
    """Test recent episode statistics for meta-learning"""

    def test_calculates_recent_performance(self, neo4j_session, clean_memory):
        """Should calculate avg steps and success rate from recent episodes"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Run 10 episodes with varying performance
        for i in range(10):
            episode_id = create_episode(neo4j_session, agent["id"], "locked")
            log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)

            # Vary steps: 2, 2, 2, 3, 3, 2, 2, 2, 3, 2
            steps = 3 if i in [3, 4, 8] else 2
            escaped = i < 8  # 8 out of 10 succeed

            mark_episode_complete(neo4j_session, episode_id, escaped, steps)

        stats = get_recent_episodes_stats(neo4j_session, agent["id"], limit=10)

        assert stats["count"] == 10
        assert 0 <= stats["success_rate"] <= 1.0
        assert stats["avg_steps"] > 0

        # Should be 80% success rate
        assert abs(stats["success_rate"] - 0.8) < 0.01

    def test_limits_to_recent_episodes(self, neo4j_session, clean_memory):
        """Should only consider most recent N episodes"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Run 20 episodes
        for i in range(20):
            episode_id = create_episode(neo4j_session, agent["id"], "locked")
            log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)
            mark_episode_complete(neo4j_session, episode_id, True, 2)

        stats = get_recent_episodes_stats(neo4j_session, agent["id"], limit=5)
        assert stats["count"] == 5  # Only last 5

    def test_empty_when_no_episodes(self, neo4j_session, clean_memory):
        """Should return zeros when no episodes exist"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        stats = get_recent_episodes_stats(neo4j_session, agent["id"], limit=10)
        assert stats["count"] == 0
        assert stats["avg_steps"] == 0.0
        assert stats["success_rate"] == 0.0


class TestIntegration:
    """Integration tests for full memory system"""

    def test_full_episode_with_memory_update(self, neo4j_session, clean_memory):
        """Should update all memory components after episode"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Run a complete episode
        episode_id = create_episode(neo4j_session, agent["id"], "locked")
        log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)
        log_step(neo4j_session, episode_id, 1, "go_window", "obs_window_escape", 0.15, 0.15)
        mark_episode_complete(neo4j_session, episode_id, True, 2)

        # Update all memory
        context = {"belief_category": "uncertain"}
        update_skill_stats(neo4j_session, episode_id, True, 2, context)
        update_meta_params(neo4j_session, agent["id"], {"episodes_completed": 1})

        # Verify all updates
        peek_stats = get_skill_stats(neo4j_session, "peek_door")
        window_stats = get_skill_stats(neo4j_session, "go_window")
        meta = get_meta_params(neo4j_session, agent["id"])

        assert peek_stats["overall"]["uses"] == 1
        assert window_stats["overall"]["uses"] == 1
        assert meta["episodes"] == 1

    def test_context_sensitive_memory(self, neo4j_session, clean_memory):
        """Memory should distinguish between different contexts"""
        agent = get_agent(neo4j_session, "MacGyverBot")

        # Run episodes in "uncertain" context (p=0.5)
        for i in range(3):
            episode_id = create_episode(neo4j_session, agent["id"], "locked")
            log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.5, 0.15)
            mark_episode_complete(neo4j_session, episode_id, True, 2)

            context = {"belief_category": "uncertain"}
            update_skill_stats(neo4j_session, episode_id, True, 2, context)

        # Run episodes in "confident_locked" context (p=0.1)
        for i in range(2):
            episode_id = create_episode(neo4j_session, agent["id"], "locked")
            log_step(neo4j_session, episode_id, 0, "peek_door", "obs_door_locked", 0.1, 0.15)
            mark_episode_complete(neo4j_session, episode_id, True, 2)

            context = {"belief_category": "confident_locked"}
            update_skill_stats(neo4j_session, episode_id, True, 2, context)

        # Verify context-specific stats
        stats_uncertain = get_skill_stats(
            neo4j_session, "peek_door",
            context={"belief_category": "uncertain"}
        )
        stats_confident = get_skill_stats(
            neo4j_session, "peek_door",
            context={"belief_category": "confident_locked"}
        )

        assert stats_uncertain["belief_context"]["uses"] == 3
        assert stats_confident["belief_context"]["uses"] == 2
        assert stats_uncertain["overall"]["uses"] == 5  # Total across both contexts


class TestMemoryScoring:
    """Test memory-influenced scoring functions"""

    def test_no_memory_returns_theoretical(self):
        """Without memory, should return pure theory"""
        from scoring import score_skill_with_memory, score_skill

        skill = {"name": "peek_door", "cost": 1.0}
        theoretical = score_skill(skill, 0.5)

        score, explanation = score_skill_with_memory(skill, 0.5, skill_stats=None)

        assert score == theoretical
        assert explanation["memory_bonus"] == 0.0
        assert explanation["theoretical_score"] == theoretical

    def test_memory_bonus_positive_for_success(self):
        """High success rate should increase score"""
        from scoring import score_skill_with_memory

        skill = {"name": "peek_door", "cost": 1.0}
        stats = {
            "overall": {
                "uses": 10,
                "success_rate": 0.9,  # 90% success
                "confidence": 1.0     # Full confidence (10/20 = 0.5, but capped)
            }
        }

        score, explanation = score_skill_with_memory(skill, 0.5, skill_stats=stats, memory_weight=0.5)

        assert explanation["memory_bonus"] > 0
        assert score > explanation["theoretical_score"]

    def test_memory_penalty_for_failure(self):
        """Low success rate should decrease score"""
        from scoring import score_skill_with_memory

        skill = {"name": "try_door", "cost": 1.5}
        stats = {
            "overall": {
                "uses": 10,
                "success_rate": 0.2,  # 20% success
                "confidence": 0.5
            }
        }

        score, explanation = score_skill_with_memory(skill, 0.5, skill_stats=stats, memory_weight=0.5)

        assert explanation["memory_bonus"] < 0
        assert score < explanation["theoretical_score"]

    def test_prefers_context_specific_stats(self):
        """Should use context-specific stats when available and confident"""
        from scoring import score_skill_with_memory

        skill = {"name": "peek_door", "cost": 1.0}
        stats = {
            "overall": {"uses": 100, "success_rate": 0.5, "confidence": 1.0},
            "belief_context": {
                "uses": 10,
                "success_rate": 0.9,
                "confidence": 0.5,  # > 0.3 threshold
                "category": "uncertain"
            }
        }
        context = {"belief_category": "uncertain"}

        score, explanation = score_skill_with_memory(skill, 0.5, skill_stats=stats, context=context)

        assert explanation["context_type"] == "context-specific"
        assert explanation["success_rate"] == 0.9  # Used context-specific

    def test_epistemic_bonus_for_underexplored(self):
        """Should add exploration bonus for skills with few samples"""
        from scoring import compute_epistemic_value

        stats_underexplored = {"overall": {"uses": 2}}
        stats_explored = {"overall": {"uses": 15}}

        # Early in learning (episode 5)
        bonus_under = compute_epistemic_value(0.5, stats_underexplored, episodes_completed=5)
        bonus_explored = compute_epistemic_value(0.5, stats_explored, episodes_completed=5)

        assert bonus_under > bonus_explored
        assert bonus_under > 0

    def test_epistemic_decays_with_experience(self):
        """Exploration bonus should decay as agent gains experience"""
        from scoring import compute_epistemic_value

        stats = {"overall": {"uses": 3}}

        # Same skill, different episode counts
        bonus_early = compute_epistemic_value(0.5, stats, episodes_completed=2)
        bonus_mid = compute_epistemic_value(0.5, stats, episodes_completed=10)
        bonus_late = compute_epistemic_value(0.5, stats, episodes_completed=25)

        assert bonus_early > bonus_mid > bonus_late
        assert bonus_late == 0  # After 20 episodes, no more epistemic bonus

    def test_score_all_skills_with_memory(self):
        """Should score and sort all skills correctly"""
        from scoring import score_all_skills_with_memory

        skills = [
            {"name": "peek_door", "cost": 1.0},
            {"name": "try_door", "cost": 1.5},
            {"name": "go_window", "cost": 2.0}
        ]

        stats_dict = {
            "peek_door": {"overall": {"uses": 10, "success_rate": 0.95, "confidence": 0.5}},
            "try_door": {"overall": {"uses": 5, "success_rate": 0.6, "confidence": 0.25}},
            "go_window": {"overall": {"uses": 8, "success_rate": 0.8, "confidence": 0.4}}
        }

        results = score_all_skills_with_memory(
            skills, p_unlocked=0.5,
            skill_stats_dict=stats_dict,
            memory_weight=0.5
        )

        # Should return list of (score, skill, explanation) tuples
        assert len(results) == 3

        # Should be sorted by score descending
        scores = [r[0] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_explanation_contains_reasoning(self):
        """Explanation should contain human-readable reasoning"""
        from scoring import score_skill_with_memory

        skill = {"name": "peek_door", "cost": 1.0}
        stats = {
            "overall": {
                "uses": 15,
                "success_rate": 0.8,
                "confidence": 0.75
            }
        }

        score, explanation = score_skill_with_memory(skill, 0.5, skill_stats=stats)

        assert "reasoning" in explanation
        assert "Theory" in explanation["reasoning"]
        assert "Memory" in explanation["reasoning"]
        assert "Final" in explanation["reasoning"]


# ============================================================================
# Agent Runtime Integration Tests
# ============================================================================

class TestAgentRuntimeMemory:
    """Test agent runtime with procedural memory enabled"""

    def test_agent_with_memory_updates_skill_stats(self, neo4j_session):
        """Agent with memory enabled should update skill stats after episode"""
        from agent_runtime import AgentRuntime

        # Create agent with memory enabled
        agent = AgentRuntime(
            neo4j_session,
            door_state="unlocked",
            initial_belief=0.5,
            use_procedural_memory=True
        )

        # Run one episode
        episode_id = agent.run_episode(max_steps=5)

        # Verify skill stats were updated
        result = neo4j_session.run("""
            MATCH (sk:Skill)-[:HAS_STATS]->(stats:SkillStats)
            WHERE stats.total_uses > 0
            RETURN count(stats) as updated_count
        """)
        record = result.single()
        assert record["updated_count"] > 0, "At least one skill should have updated stats"

    def test_agent_without_memory_does_not_update_stats(self, neo4j_session):
        """Agent without memory should not update skill stats"""
        from agent_runtime import AgentRuntime

        # Reset stats to zero
        neo4j_session.run("""
            MATCH (stats:SkillStats)
            SET stats.total_uses = 0,
                stats.successful_episodes = 0,
                stats.failed_episodes = 0
        """)

        # Create agent WITHOUT memory
        agent = AgentRuntime(
            neo4j_session,
            door_state="unlocked",
            initial_belief=0.5,
            use_procedural_memory=False
        )

        # Run one episode
        episode_id = agent.run_episode(max_steps=5)

        # Verify skill stats were NOT updated
        result = neo4j_session.run("""
            MATCH (sk:Skill)-[:HAS_STATS]->(stats:SkillStats)
            WHERE stats.total_uses > 0
            RETURN count(stats) as updated_count
        """)
        record = result.single()
        assert record["updated_count"] == 0, "Stats should not be updated without memory enabled"

    def test_agent_with_adaptive_params_increments_episodes(self, neo4j_session):
        """Agent with adaptive params should increment episode counter"""
        from agent_runtime import AgentRuntime

        # Reset meta params
        neo4j_session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            SET meta.episodes_completed = 0
        """)

        # Create agent with adaptive params
        agent = AgentRuntime(
            neo4j_session,
            door_state="unlocked",
            initial_belief=0.5,
            adaptive_params=True
        )

        initial_episodes = agent.episodes_completed

        # Run one episode
        agent.run_episode(max_steps=5)

        # Verify counter incremented
        assert agent.episodes_completed == initial_episodes + 1

        # Verify it's persisted in graph
        result = neo4j_session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            RETURN meta.episodes_completed as episodes
        """)
        record = result.single()
        assert record["episodes"] == initial_episodes + 1

    def test_agent_adapts_meta_params_after_5_episodes(self, neo4j_session):
        """Agent should adapt meta-parameters every 5 episodes"""
        from agent_runtime import AgentRuntime

        # Reset and set initial state
        neo4j_session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            SET meta.episodes_completed = 0,
                meta.beta = 6.0
        """)

        # Create agent with adaptive params
        agent = AgentRuntime(
            neo4j_session,
            door_state="unlocked",
            initial_belief=0.5,
            adaptive_params=True,
            use_procedural_memory=True
        )

        # Run 5 episodes (should trigger adaptation on 5th)
        for i in range(5):
            agent.run_episode(max_steps=5)

        # Check that episodes_completed is 5
        assert agent.episodes_completed == 5

        # Adaptation should have been called (beta might have changed)
        # We can't predict exact beta value, but episodes should be recorded
        result = neo4j_session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            RETURN meta.episodes_completed as episodes
        """)
        record = result.single()
        assert record["episodes"] == 5

    def test_memory_influences_skill_selection(self, neo4j_session):
        """Memory should influence which skill is selected"""
        from agent_runtime import AgentRuntime
        from graph_model import get_skill_stats, update_skill_stats

        # Artificially boost peek_door success rate
        neo4j_session.run("""
            MATCH (sk:Skill {name: "peek_door"})-[:HAS_STATS]->(stats:SkillStats)
            SET stats.total_uses = 20,
                stats.successful_episodes = 18,
                stats.failed_episodes = 2,
                stats.uncertain_uses = 10,
                stats.uncertain_successes = 9
        """)

        # Create agent with memory at uncertain belief
        agent = AgentRuntime(
            neo4j_session,
            door_state="unlocked",
            initial_belief=0.5,  # uncertain
            use_procedural_memory=True,
            verbose_memory=True
        )

        # Select skill - should favor peek_door due to high success rate
        from graph_model import get_skills
        skills = get_skills(neo4j_session, agent.agent_id)
        selected = agent.select_skill(skills)

        # Check decision log
        assert len(agent.decision_log) > 0
        last_decision = agent.decision_log[-1]

        # Memory should have influenced the decision
        assert last_decision["explanation"] is not None
        assert "memory_bonus" in last_decision["explanation"]

    def test_verbose_memory_includes_explanations(self, neo4j_session):
        """Verbose memory mode should include decision explanations"""
        from agent_runtime import AgentRuntime

        agent = AgentRuntime(
            neo4j_session,
            door_state="unlocked",
            initial_belief=0.5,
            use_procedural_memory=True,
            verbose_memory=True
        )

        # Run one step
        from graph_model import get_skills
        skills = get_skills(neo4j_session, agent.agent_id)
        selected = agent.select_skill(skills)

        # Check that explanation is present
        assert len(agent.decision_log) > 0
        last_decision = agent.decision_log[-1]
        assert last_decision["explanation"] is not None
        assert "reasoning" in last_decision["explanation"]
