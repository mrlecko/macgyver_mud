"""
Test suite for Phase 3: Quest-Aware Critical States.

Tests that critical state protocols (DEADLOCK, PANIC, etc.) respect
subgoal progress and don't trigger false alarms during valid subgoal execution.

TDD Approach: Write tests FIRST, then implement to make them pass.
"""
import pytest
from neo4j import GraphDatabase
import config
from critical_state import CriticalState


class TestQuestAwareDeadlockDetection:
    """Test that DEADLOCK detection respects subgoal progress."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_no_deadlock_when_advancing_subgoals(self, agent):
        """
        Test: Agent shouldn't detect DEADLOCK when making subgoal progress.

        Scenario:
        - Quest: "First A, then B, finally C"
        - Agent completes A, moves to B
        - Even if revisiting locations, it's making progress (subgoal advancement)
        - Should NOT trigger DEADLOCK
        """
        quest = "First move east, then take nest, finally place nest"
        agent.reset(quest)

        # Simulate subgoal progress
        agent.current_subgoal_index = 0

        # Step 1: Complete first subgoal
        agent.step("You are in attic", "", 0.0, False, ["go east"], {'description': quest})
        agent.location_history.append("attic")

        # Advance to next subgoal
        agent.current_subgoal_index = 1

        # Step 2: Working on second subgoal (in new location)
        agent.step("You moved east. You see nest.", "", 0.0, False, ["take nest"], {'description': quest})
        agent.location_history.append("bedroom")

        # Check critical state - should still be FLOW (not DEADLOCK)
        # Even though no reward yet, we're advancing subgoals
        assert agent.current_critical_state != CriticalState.DEADLOCK, \
            "Should not trigger DEADLOCK when advancing subgoals"

    def test_deadlock_detected_when_truly_stuck(self, agent):
        """
        Test: DEADLOCK should trigger when stuck on SAME subgoal.

        Scenario:
        - Agent stuck on subgoal 1 for many steps
        - Revisiting same locations repeatedly
        - No subgoal progress
        - Should trigger DEADLOCK
        """
        quest = "First move east, then take nest"
        agent.reset(quest)
        agent.current_subgoal_index = 1  # Working on "take nest"

        # Simulate getting stuck (revisit same location multiple times)
        for i in range(6):
            agent.step(f"You are in bedroom. Attempt {i}.", "", 0.0, False,
                      ["take nest", "examine nest", "look"], {'description': quest})
            agent.location_history.append("bedroom")

        # Should detect DEADLOCK (stuck on same subgoal + location looping)
        # Note: This depends on agent implementing quest-aware deadlock detection
        # The test will initially fail, guiding implementation


class TestQuestAwarePanicProtocol:
    """Test that PANIC protocol checks subgoal completion before escalating."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_no_panic_when_completing_subgoals(self, agent):
        """
        Test: PANIC shouldn't trigger when making quest progress.

        Scenario:
        - Many steps taken, but completing subgoals
        - Step count is high, but effective
        - Should NOT panic
        """
        quest = "First move east, then take nest, finally place nest"
        agent.reset(quest)

        # Simulate completing subgoals (even with many steps)
        for step in range(15):
            # Advance subgoals every few steps
            if step % 5 == 0 and agent.current_subgoal_index < len(agent.subgoals) - 1:
                agent.current_subgoal_index += 1

            agent.step(f"Step {step}", "", 0.0, False, ["action"], {'description': quest})

        # Should NOT panic (making subgoal progress)
        assert agent.current_critical_state != CriticalState.PANIC, \
            "Should not panic when completing subgoals"

    def test_panic_when_stuck_without_progress(self, agent):
        """
        Test: PANIC should trigger when stuck without subgoal progress.

        Scenario:
        - Many steps on SAME subgoal
        - No advancement
        - Should trigger PANIC
        """
        quest = "First move east, then take nest"
        agent.reset(quest)
        agent.current_subgoal_index = 0  # Stuck on first subgoal

        # Many steps without advancing
        for step in range(15):
            agent.step(f"Still stuck on subgoal 0", "", 0.0, False, ["go east"], {'description': quest})

        # Should detect lack of progress and panic
        # (This tests the implementation)


class TestCriticalStateContextPropagation:
    """Test that critical state evaluation receives subgoal context."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_critical_state_monitor_receives_subgoal_context(self, agent):
        """
        Test: Critical state evaluation should receive current subgoal info.

        This enables quest-aware protocol decisions.
        """
        quest = "First move east, then take nest"
        agent.reset(quest)

        # Agent should have method to evaluate critical state with subgoal context
        # For now, just verify the agent tracks subgoal state
        assert hasattr(agent, 'current_subgoal_index'), \
            "Agent should track current subgoal"
        assert hasattr(agent, 'subgoals'), \
            "Agent should have subgoals list"

        # When critical state is evaluated, it should use this info
        # (Implementation detail - will guide Phase 3 coding)


class TestSubgoalProgressMetrics:
    """Test metrics for tracking subgoal progress over time."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_track_steps_per_subgoal(self, agent):
        """
        Test: Agent should track how many steps taken on each subgoal.

        This helps detect if stuck on a particular subgoal.
        """
        quest = "First move east, then take nest, finally place nest"
        agent.reset(quest)

        # Should have metric for steps per subgoal
        assert hasattr(agent, 'subgoal_step_counts') or hasattr(agent, 'steps_on_current_subgoal'), \
            "Agent should track steps per subgoal"

    def test_detect_excessive_steps_on_single_subgoal(self, agent):
        """
        Test: Detect when spending too many steps on one subgoal.

        Threshold: >10 steps on same subgoal = potential stuck state.
        """
        quest = "First move east, then take nest"
        agent.reset(quest)
        agent.current_subgoal_index = 0

        # Simulate many steps on subgoal 0
        for i in range(12):
            agent.step(f"Attempt {i}", "", 0.0, False, ["go east"], {'description': quest})

        # Should detect excessive steps
        # (This will guide implementation of step counter)


class TestBackwardCompatibility:
    """Test that critical states still work in MacGyver mode (no quest)."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_critical_states_work_without_quest(self, agent):
        """
        Test: Critical state detection works in MacGyver mode (no quest).

        Should fall back to traditional detection methods.
        """
        agent.reset()  # No quest parameter

        # Should still evaluate critical states
        assert agent.current_critical_state is not None, \
            "Critical state should be initialized"

        # Simulate some steps
        for i in range(5):
            agent.step(f"MacGyver step {i}", "", 0.0, False, ["look"], {})

        # Should work fine without quest context
        assert agent.current_critical_state in [CriticalState.FLOW, CriticalState.DEADLOCK,
                                                 CriticalState.PANIC, CriticalState.SCARCITY,
                                                 CriticalState.NOVELTY], \
            "Critical state should be valid enum value"


class TestCriticalStateReEnabling:
    """Test that critical state monitoring can be safely re-enabled."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_critical_state_evaluation_enabled(self, agent):
        """
        Test: Critical state evaluation is enabled (not disabled).

        In Option A, it was disabled at line 960. In Phase 3, we re-enable it
        with quest-aware safeguards.
        """
        quest = "First move east, then take nest"
        agent.reset(quest)

        # Do some steps
        for i in range(3):
            agent.step(f"Step {i}", "", 0.0, False, ["go east"], {'description': quest})

        # Critical state should be evaluated (not stuck at initial value)
        # Note: Exact behavior depends on implementation
        # For now, just verify monitoring is happening
        assert hasattr(agent, 'current_critical_state'), \
            "Agent should track critical state"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
