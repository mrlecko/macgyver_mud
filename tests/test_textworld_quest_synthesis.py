"""
Test suite for Quest Synthesis (Hierarchical Cognitive Agent).

TDD Approach for Option A: Minimum Viable Synthesis
- Test quest decomposition integration
- Test subgoal tracking and progress
- Test hierarchical goal scoring
- Test that subgoal context flows through EFE

Phase: Write tests FIRST (RED), then implement (GREEN)
"""
import pytest
from neo4j import GraphDatabase
import config


# ============================================================================
# PHASE 1: QUEST DECOMPOSITION INTEGRATION
# ============================================================================

class TestQuestDecompositionIntegration:
    """Test that cognitive agent can decompose and track quests."""

    @pytest.fixture
    def neo4j_session(self):
        """Provide Neo4j session for testing."""
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_agent_has_quest_decomposer(self, neo4j_session):
        """
        Test 1: Cognitive agent has QuestDecomposer component.

        Expected: agent.quest_decomposer exists after initialization.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Should have quest decomposer
        assert hasattr(agent, 'quest_decomposer')
        assert agent.quest_decomposer is not None

    def test_agent_has_subgoal_state(self, neo4j_session):
        """
        Test 2: Agent maintains subgoal tracking state.

        Expected:
        - agent.subgoals (list of subgoal strings)
        - agent.current_subgoal_index (int, starts at 0)
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Should have subgoal tracking
        assert hasattr(agent, 'subgoals')
        assert hasattr(agent, 'current_subgoal_index')
        assert isinstance(agent.subgoals, list)
        assert agent.current_subgoal_index == 0

    def test_reset_decomposes_quest(self, neo4j_session):
        """
        Test 3: reset(quest) method decomposes quest into subgoals.

        Given: "First, move east. Then, take nest. Finally, place nest in dresser."
        Expected: subgoals = ["move east", "take nest", "place nest in dresser"]
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, move east. Then, take nest. Finally, place nest in dresser."
        agent.reset(quest)

        # Should decompose quest
        assert len(agent.subgoals) == 3
        assert "move east" in agent.subgoals[0].lower()
        assert "take" in agent.subgoals[1].lower()
        assert "nest" in agent.subgoals[1].lower()
        assert "place" in agent.subgoals[2].lower() or "insert" in agent.subgoals[2].lower()

        # Should start at first subgoal
        assert agent.current_subgoal_index == 0

        # Should store quest
        assert hasattr(agent, 'last_quest')
        assert agent.last_quest == quest


# ============================================================================
# PHASE 2: PROGRESS TRACKING
# ============================================================================

class TestSubgoalProgressTracking:
    """Test that agent advances through subgoals based on progress."""

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

    def test_progress_advances_on_reward(self, neo4j_session):
        """
        Test 4: Agent advances to next subgoal when reward > 0.

        Scenario:
        1. Reset with 3-step quest
        2. Take action, get reward > 0
        3. Should advance from subgoal 0 → 1
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, go east. Then, take key. Finally, unlock door."
        agent.reset(quest)

        # Start at step 0
        assert agent.current_subgoal_index == 0

        # Simulate step with reward (subgoal completed)
        observation = "You moved east."
        feedback = ""
        reward = 1.0  # Positive reward indicates progress
        done = False
        commands = ["take key", "look", "inventory"]

        action = agent.step(observation, feedback, reward, done, commands, quest={'description': quest})

        # Should advance to step 1
        assert agent.current_subgoal_index == 1

    def test_progress_does_not_advance_without_reward(self, neo4j_session):
        """
        Test 5: Agent stays on current subgoal when reward = 0.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, go east. Then, take key."
        agent.reset(quest)

        assert agent.current_subgoal_index == 0

        # Step with no reward
        observation = "You are in a room."
        feedback = ""
        reward = 0.0
        done = False
        commands = ["go east", "look"]

        agent.step(observation, feedback, reward, done, commands, quest={'description': quest})

        # Should stay at step 0
        assert agent.current_subgoal_index == 0

    def test_progress_stops_at_last_subgoal(self, neo4j_session):
        """
        Test 6: Agent doesn't advance past final subgoal.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "Take the key."
        agent.reset(quest)

        # Only 1 subgoal
        assert len(agent.subgoals) == 1
        assert agent.current_subgoal_index == 0

        # Get reward
        observation = "You took the key."
        feedback = ""
        reward = 1.0
        done = True
        commands = ["inventory"]

        agent.step(observation, feedback, reward, done, commands, quest={'description': quest})

        # Should stay at index 0 (last subgoal)
        # OR advance to 1 but be out of bounds (implementation detail)
        # Either way, should handle gracefully
        assert agent.current_subgoal_index <= len(agent.subgoals)


# ============================================================================
# PHASE 3: HIERARCHICAL GOAL SCORING
# ============================================================================

class TestHierarchicalGoalScoring:
    """Test that goal scoring is subgoal-aware."""

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

    def test_calculate_goal_value_accepts_subgoal(self, neo4j_session):
        """
        Test 7: calculate_goal_value() accepts current_subgoal parameter.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Should accept subgoal parameter
        value = agent.calculate_goal_value("take key", current_subgoal="take key")

        assert isinstance(value, float)
        assert value > 0  # Should give positive value for matching action

    def test_subgoal_match_gives_high_bonus(self, neo4j_session):
        """
        Test 8: Actions matching current subgoal get HUGE bonus.

        Given subgoal: "take nest"
        - "take nest of spiders from table" should score HIGH (matches)
        - "examine painting" should score LOW (doesn't match)
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        subgoal = "take nest"

        # Action that matches subgoal
        matching_action = "take nest of spiders from table"
        matching_value = agent.calculate_goal_value(matching_action, current_subgoal=subgoal)

        # Action that doesn't match
        non_matching_action = "examine painting"
        non_matching_value = agent.calculate_goal_value(non_matching_action, current_subgoal=subgoal)

        # Matching should score MUCH higher
        assert matching_value > non_matching_value + 10.0  # At least 10 point difference

    def test_score_action_passes_subgoal(self, neo4j_session):
        """
        Test 9: score_action() accepts and passes current_subgoal to calculate_goal_value().
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Set up quest context
        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Current subgoal is "take key"
        current_subgoal = agent.subgoals[agent.current_subgoal_index]

        # Score with subgoal
        score = agent.score_action("take key", agent.beliefs, quest={'description': quest}, current_subgoal=current_subgoal)

        assert isinstance(score, float)
        # Should incorporate subgoal bonus
        assert score > 5.0  # Should be high due to subgoal match

    def test_select_action_uses_hierarchical_scoring(self, neo4j_session):
        """
        Test 10: select_action() passes current subgoal through to scoring.

        Integration test: Full pipeline from quest → subgoal → scoring → selection.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Set up quest
        quest = "First, take the nest. Then, place it in the dresser."
        agent.reset(quest)

        # Current subgoal: "take the nest"
        assert agent.current_subgoal_index == 0

        # Commands available
        commands = [
            "examine painting",       # Irrelevant
            "take nest from table",   # Matches current subgoal!
            "open dresser",           # Relevant to future subgoal
            "look"                    # Generic
        ]

        # Select action
        selected = agent.select_action(commands, quest={'description': quest})

        # Should prefer the subgoal-matching action
        assert "nest" in selected.lower()
        assert "take" in selected.lower()


# ============================================================================
# PHASE 4: END-TO-END INTEGRATION
# ============================================================================

class TestEndToEndQuestSynthesis:
    """Test complete quest execution with hierarchical synthesis."""

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

    def test_simple_quest_execution(self, neo4j_session):
        """
        Test 11: Execute simple 2-step quest end-to-end.

        Quest: "First, take key. Then, unlock door."

        Expected behavior:
        1. Decompose quest into 2 subgoals
        2. Start at subgoal 0 (take key)
        3. Select "take key" action (high score due to subgoal match)
        4. Get reward, advance to subgoal 1
        5. Select "unlock door" action
        6. Complete
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Should have 2 subgoals
        assert len(agent.subgoals) == 2

        # === STEP 1: Take key ===
        observation = "You see a key and a door."
        commands = ["take key", "examine door", "look"]

        action = agent.step(observation, "", 0.0, False, commands, quest={'description': quest})

        # Should select "take key" (matches subgoal 0)
        assert "key" in action.lower()
        assert "take" in action.lower()

        # === STEP 2: Got key, reward ===
        observation = "You took the key."
        commands = ["unlock door", "examine key", "look"]
        reward = 1.0  # Progress!

        action = agent.step(observation, "", reward, False, commands, quest={'description': quest})

        # Should have advanced to subgoal 1
        assert agent.current_subgoal_index == 1

        # Should select "unlock door" (matches subgoal 1)
        assert "door" in action.lower()
        assert "unlock" in action.lower()

    def test_complex_quest_with_three_steps(self, neo4j_session):
        """
        Test 12: Execute TextWorld-style 3-step quest.

        Quest: "First, move east. Then, take nest from table. Finally, place nest in dresser."
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, move east. Then, take nest from table. Finally, place nest in dresser."
        agent.reset(quest)

        # Should decompose into 3 steps
        assert len(agent.subgoals) >= 2  # At least 2 (might be 3 depending on decomposer)

        # Step 1: Should prefer movement
        commands = ["go east", "examine table", "look"]
        action = agent.step("You are in a room.", "", 0.0, False, commands, quest={'description': quest})

        # Should select movement action
        assert "east" in action.lower()

        # Step 2: After reward, should prefer taking nest
        commands = ["take nest of spiders from table", "examine nest", "go west"]
        action = agent.step("You moved east.", "", 1.0, False, commands, quest={'description': quest})

        # Should be at next subgoal now
        assert agent.current_subgoal_index >= 1


# ============================================================================
# PHASE 5: BACKWARD COMPATIBILITY
# ============================================================================

class TestBackwardCompatibility:
    """Ensure changes don't break existing functionality."""

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

    def test_old_reset_without_quest_still_works(self, neo4j_session):
        """
        Test 13: Calling reset() without quest parameter still works.

        Backward compatibility: Some tests/code might call reset() without args.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Old API: reset() with no args
        agent.reset()

        # Should work (just won't have subgoals)
        assert agent.subgoals == [] or agent.subgoals is not None

    def test_calculate_goal_value_without_subgoal_still_works(self, neo4j_session):
        """
        Test 14: calculate_goal_value() works without current_subgoal parameter.

        Backward compatibility: Should default to quest-level matching.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.last_quest = "Take the key and unlock the door."

        # Old API: no subgoal parameter
        value = agent.calculate_goal_value("take key")

        # Should still score based on quest match
        assert isinstance(value, float)
        assert value > 0.0  # Should give bonus for quest relevance


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
