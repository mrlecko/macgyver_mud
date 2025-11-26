"""
Integration Tests - Multi-System Interactions

Tests the integration of multiple subsystems working together:
1. Episodic Memory → Procedural Memory → Decision Making
2. Lyapunov Monitor → Escalation Protocol
3. Critical States + Geometric Controller + Memory
"""

import pytest
from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime, AgentEscalationError
from graph_model import get_agent
from critical_state import CriticalState

# Use neo4j_session from conftest.py


class TestEpisodicProceduralDecisionFlow:
    """
    Test that episodic insights actually influence decisions via procedural memory.

    Flow: Episode completes → Episodic memory stores counterfactuals →
          Offline learning analyzes regret → Updates procedural memory (SkillStats) →
          Next episode uses updated stats for decision making
    """

    @pytest.mark.order(1)
    def test_episodic_learning_changes_skill_preferences(self, neo4j_session):
        """
        Verify that episodic memory insights propagate to procedural memory
        and influence subsequent skill selections.
        """
        # Enable episodic memory with skill prior updates
        original_episodic = config.ENABLE_EPISODIC_MEMORY
        original_update_priors = config.EPISODIC_UPDATE_SKILL_PRIORS
        original_labyrinth = config.EPISODIC_USE_LABYRINTH

        try:
            config.ENABLE_EPISODIC_MEMORY = True
            config.EPISODIC_UPDATE_SKILL_PRIORS = True
            config.EPISODIC_USE_LABYRINTH = False  # Use belief-based for simplicity

            # Create agent with procedural memory enabled
            agent = AgentRuntime(
                neo4j_session,
                door_state="locked",
                use_procedural_memory=True
            )

            # Run an episode (will create episodic memory)
            try:
                agent.run_episode()
            except:
                pass  # Episode might fail, that's okay

            # Trigger offline learning manually
            if agent.episodic_memory:
                agent._perform_offline_learning()

                # Verify that episodic memory exists
                from memory.episodic_replay import EpisodicMemory
                em = EpisodicMemory(neo4j_session)

                # Check if we can retrieve episodes
                result = neo4j_session.run("""
                    MATCH (em:EpisodicMemory)
                    RETURN count(em) as count
                """)
                count = result.single()["count"]

                # Should have at least 1 episode stored
                assert count >= 1, "Episodic memory should store episodes"

                # Check if skill stats were updated (procedural memory integration)
                result = neo4j_session.run("""
                    MATCH (sk:Skill)-[:HAS_STATS]->(stats:SkillStats)
                    WHERE stats.total_uses > 0
                    RETURN count(sk) as updated_skills
                """)
                updated = result.single()["updated_skills"]

                # Should have updated at least some skill stats
                assert updated > 0, "Offline learning should update skill statistics"

        finally:
            config.ENABLE_EPISODIC_MEMORY = original_episodic
            config.EPISODIC_UPDATE_SKILL_PRIORS = original_update_priors
            config.EPISODIC_USE_LABYRINTH = original_labyrinth


class TestLyapunovEscalation:
    """
    Test that Lyapunov stability monitoring can trigger escalation.

    Flow: Agent state becomes unstable → Lyapunov V(s) diverges →
          Monitor detects divergence → Raises AgentEscalationError
    """

    def test_lyapunov_monitor_integration(self, neo4j_session):
        """
        Verify Lyapunov monitor is properly integrated and can be enabled/disabled.
        """
        # Test with Lyapunov enabled
        original_lyapunov = config.ENABLE_LYAPUNOV_MONITORING

        try:
            config.ENABLE_LYAPUNOV_MONITORING = True

            agent = AgentRuntime(neo4j_session, door_state="locked")

            # Should have Lyapunov monitor
            assert agent.lyapunov_monitor is not None, "Lyapunov monitor should be enabled"

            # Disable it
            config.ENABLE_LYAPUNOV_MONITORING = False
            agent2 = AgentRuntime(neo4j_session, door_state="locked")

            # Should not have Lyapunov monitor
            assert agent2.lyapunov_monitor is None, "Lyapunov monitor should be disabled"

        finally:
            config.ENABLE_LYAPUNOV_MONITORING = original_lyapunov

    def test_lyapunov_does_not_crash_when_disabled(self, neo4j_session):
        """
        Verify that critical state protocols work even when Lyapunov is disabled.
        """
        original_lyapunov = config.ENABLE_LYAPUNOV_MONITORING
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS

        try:
            config.ENABLE_LYAPUNOV_MONITORING = False
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True

            agent = AgentRuntime(neo4j_session, door_state="locked")

            # Should create without error even with Lyapunov disabled
            assert agent.lyapunov_monitor is None

            # Should still be able to select skills
            from graph_model import get_skills
            skills = get_skills(neo4j_session, agent.agent_id)
            selected = agent.select_skill(skills)

            assert selected is not None, "Should select skill even without Lyapunov"

        finally:
            config.ENABLE_LYAPUNOV_MONITORING = original_lyapunov
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical


class TestCriticalStatesGeometricController:
    """
    Test interaction between critical state protocols and geometric controller.

    Flow: Agent encounters critical situation → CriticalStateMonitor detects state →
          Geometric controller applies appropriate strategy → Skills are boosted
    """

    def test_panic_state_triggers_geometric_response(self, neo4j_session):
        """
        Verify that PANIC state (high entropy) triggers appropriate geometric response.
        """
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS

        try:
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True

            # Create agent with high initial uncertainty (panic-inducing)
            agent = AgentRuntime(
                neo4j_session,
                door_state="locked",
                initial_belief=0.5  # Maximum entropy
            )

            # Verify critical state monitor exists
            assert agent.monitor is not None

            # Manually check if high entropy triggers panic
            from critical_state import AgentState
            from scoring import entropy

            current_entropy = entropy(0.5)  # Maximum entropy
            assert current_entropy > config.CRITICAL_THRESHOLDS["PANIC_ENTROPY"], \
                "Entropy at 0.5 should exceed panic threshold"

            # Create agent state that should trigger panic
            agent_state = AgentState(
                entropy=current_entropy,
                history=[],
                steps=10,
                dist=5,
                rewards=[],
                error=0.0
            )

            critical_state = agent.monitor.evaluate(agent_state)

            # Should detect PANIC state (high entropy, no other critical conditions)
            assert critical_state == CriticalState.PANIC, \
                f"High entropy should trigger PANIC, got {critical_state}"

        finally:
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical

    def test_scarcity_state_triggers_efficiency_mode(self, neo4j_session):
        """
        Verify that SCARCITY state (low steps) triggers efficiency mode.
        """
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS

        try:
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True

            agent = AgentRuntime(neo4j_session, door_state="locked")

            from critical_state import AgentState

            # Create scarcity condition: steps < distance * 1.2
            agent_state = AgentState(
                entropy=0.3,  # Low entropy (not panic)
                history=[],
                steps=5,      # Only 5 steps left
                dist=10,      # But 10 steps away (5 < 10 * 1.2 = 12)
                rewards=[],
                error=0.0
            )

            critical_state = agent.monitor.evaluate(agent_state)

            # Should detect SCARCITY
            assert critical_state == CriticalState.SCARCITY, \
                f"Low steps should trigger SCARCITY, got {critical_state}"

        finally:
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical

    def test_deadlock_detection(self, neo4j_session):
        """
        Verify that deadlock (A→B→A→B loops) is detected.
        """
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS

        try:
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True

            agent = AgentRuntime(neo4j_session, door_state="locked")

            from critical_state import AgentState

            # Create A→B→A→B pattern
            agent_state = AgentState(
                entropy=0.3,
                history=["A", "B", "A", "B"],  # Classic loop
                steps=10,
                dist=5,
                rewards=[],
                error=0.0
            )

            critical_state = agent.monitor.evaluate(agent_state)

            # Should detect DEADLOCK
            assert critical_state == CriticalState.DEADLOCK, \
                f"A→B→A→B pattern should trigger DEADLOCK, got {critical_state}"

        finally:
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical


class TestEscalationProtocol:
    """
    Test that the ESCALATION protocol (circuit breaker) triggers correctly.

    Flow: Agent thrashes between critical states → ESCALATION triggered →
          AgentEscalationError raised → Episode halts
    """

    def test_escalation_on_repeated_panic(self, neo4j_session):
        """
        Verify that repeated PANIC states trigger ESCALATION.
        """
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS

        try:
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True

            agent = AgentRuntime(neo4j_session, door_state="locked")

            from critical_state import AgentState, CriticalState

            # Clear any existing state history
            agent.monitor.state_history = []

            # Simulate 2 PANIC states (build up history)
            for i in range(2):
                agent_state = AgentState(
                    entropy=0.6,  # High entropy (triggers panic)
                    history=[],
                    steps=10,  # Plenty of steps (avoid scarcity/escalation)
                    dist=5,
                    rewards=[],
                    error=0.0
                )

                state = agent.monitor.evaluate(agent_state)
                assert state == CriticalState.PANIC, f"Iteration {i} should be PANIC"

            # Third PANIC should trigger ESCALATION (3 in last 5)
            agent_state = AgentState(
                entropy=0.6,
                history=[],
                steps=10,
                dist=5,
                rewards=[],
                error=0.0
            )

            final_state = agent.monitor.evaluate(agent_state)

            assert final_state == CriticalState.ESCALATION, \
                f"Three PANICs in history should trigger ESCALATION, got {final_state}"

        finally:
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical

    def test_escalation_on_terminal_scarcity(self, neo4j_session):
        """
        Verify that terminal scarcity (steps < 2) triggers ESCALATION.
        """
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS

        try:
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True

            agent = AgentRuntime(neo4j_session, door_state="locked")

            from critical_state import AgentState

            # Terminal scarcity: only 1 step left
            agent_state = AgentState(
                entropy=0.3,
                history=[],
                steps=1,  # Terminal scarcity
                dist=5,
                rewards=[],
                error=0.0
            )

            critical_state = agent.monitor.evaluate(agent_state)

            assert critical_state == CriticalState.ESCALATION, \
                "Terminal scarcity (steps=1) should trigger ESCALATION"

        finally:
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical


class TestFullSystemIntegration:
    """
    End-to-end test with all systems enabled.

    Tests: Episodic Memory + Procedural Memory + Critical States + Lyapunov
    """

    def test_agent_runs_with_all_features_enabled(self, neo4j_session):
        """
        Smoke test: verify agent can run with all advanced features enabled.
        """
        original_episodic = config.ENABLE_EPISODIC_MEMORY
        original_update_priors = config.EPISODIC_UPDATE_SKILL_PRIORS
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS
        original_lyapunov = config.ENABLE_LYAPUNOV_MONITORING

        try:
            # Enable EVERYTHING
            config.ENABLE_EPISODIC_MEMORY = True
            config.EPISODIC_UPDATE_SKILL_PRIORS = True
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True
            config.ENABLE_LYAPUNOV_MONITORING = True

            # Create agent with all features
            agent = AgentRuntime(
                neo4j_session,
                door_state="unlocked",  # Easy scenario for quick test
                use_procedural_memory=True,
                adaptive_params=True
            )

            # Verify all subsystems initialized
            assert agent.episodic_memory is not None, "Episodic memory should be enabled"
            assert agent.monitor is not None, "Critical state monitor should exist"
            assert agent.lyapunov_monitor is not None, "Lyapunov monitor should be enabled"

            # Run episode - should complete without crashing
            agent.run_episode()

            # Should have escaped (door is unlocked)
            assert agent.escaped, "Agent should escape when door is unlocked"

            # Should have logged to Neo4j (check by agent_id)
            result = neo4j_session.run("""
                MATCH (a:Agent)-[:PERFORMED_EPISODE]->(e:Episode)
                WHERE id(a) = $agent_id
                RETURN e.total_steps as steps
                ORDER BY e.created_at DESC
                LIMIT 1
            """, agent_id=agent.agent_id)
            record = result.single()
            assert record is not None, "Episode should be logged to Neo4j"
            assert record["steps"] > 0, "Should have taken at least one step"

        finally:
            config.ENABLE_EPISODIC_MEMORY = original_episodic
            config.EPISODIC_UPDATE_SKILL_PRIORS = original_update_priors
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical
            config.ENABLE_LYAPUNOV_MONITORING = original_lyapunov

    @pytest.mark.order(1)
    def test_agent_handles_failure_gracefully_with_all_features(self, neo4j_session):
        """
        Verify agent handles failure scenarios without crashing when all features enabled.
        """
        original_episodic = config.ENABLE_EPISODIC_MEMORY
        original_geometric = config.ENABLE_GEOMETRIC_CONTROLLER
        original_critical = config.ENABLE_CRITICAL_STATE_PROTOCOLS
        original_lyapunov = config.ENABLE_LYAPUNOV_MONITORING

        try:
            config.ENABLE_EPISODIC_MEMORY = True
            config.ENABLE_GEOMETRIC_CONTROLLER = True
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = True
            config.ENABLE_LYAPUNOV_MONITORING = True

            # Create agent with locked door (harder scenario)
            agent = AgentRuntime(
                neo4j_session,
                door_state="locked",
                use_procedural_memory=True
            )

            # Run episode - might fail or hit max steps, that's okay
            try:
                agent.run_episode()
            except AgentEscalationError:
                # Escalation is a valid outcome
                pass
            except Exception as e:
                pytest.fail(f"Agent crashed with all features enabled: {e}")

            # Should have created episodic memory even if failed
            if agent.episodic_memory:
                result = neo4j_session.run("""
                    MATCH (em:EpisodicMemory)
                    RETURN count(em) as count
                """)
                count = result.single()["count"]
                assert count > 0, "Should store episodic memory even on failure"

        finally:
            config.ENABLE_EPISODIC_MEMORY = original_episodic
            config.ENABLE_GEOMETRIC_CONTROLLER = original_geometric
            config.ENABLE_CRITICAL_STATE_PROTOCOLS = original_critical
            config.ENABLE_LYAPUNOV_MONITORING = original_lyapunov
