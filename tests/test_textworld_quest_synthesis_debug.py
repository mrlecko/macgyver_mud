"""
Debug tests for Quest Synthesis - Reproduce actual TextWorld failures.

These tests capture the specific issues we're seeing in the real game.
"""
import pytest
from neo4j import GraphDatabase
import config


class TestProgressTrackingTiming:
    """Test that progress tracking works correctly across multiple steps."""

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

    def test_step1_no_advancement_expected(self, neo4j_session):
        """
        Test: Step 1 should stay on subgoal 0 (first action, no history).

        Scenario:
        - Quest: "First, move east. Then, take nest."
        - Step 1: No prior actions, should stay on subgoal 0
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        quest = "First, move east. Then, take nest."
        agent.reset(quest)

        # Step 1 - no prior actions
        assert agent.current_subgoal_index == 0

        commands = ["go east", "look", "inventory"]
        action = agent.step(
            observation="You are in a room.",
            feedback="You are in a room.",
            reward=0.0,
            done=False,
            admissible_commands=commands,
            quest={'description': quest}
        )

        # After step 1, should still be on subgoal 0
        # (Progress tracking runs at START of next step)
        assert agent.current_subgoal_index == 0

    def test_step2_should_advance_after_movement(self, neo4j_session):
        """
        Test: Step 2 should advance from subgoal 0 to 1 after completing movement.

        This is the KEY test that's currently failing!

        Scenario:
        - Quest: "First, move east. Then, take nest."
        - Step 1: Selected "go east"
        - Step 2: Should see "go east" completed subgoal 0, advance to subgoal 1
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        quest = "First, move east. Then, take nest."
        agent.reset(quest)

        assert agent.current_subgoal_index == 0

        # Step 1: Agent should select and execute "go east"
        commands = ["go east", "look", "inventory"]
        action1 = agent.step(
            observation="You are in a room.",
            feedback="You are in a room.",
            reward=0.0,
            done=False,
            admissible_commands=commands,
            quest={'description': quest}
        )

        # Agent should have selected "go east" (movement matches subgoal 0)
        assert "east" in action1.lower()

        # Step 2: Should advance to subgoal 1 when it sees "go east" completed
        commands2 = ["take nest from table", "examine nest", "look"]
        action2 = agent.step(
            observation="You moved east. You see a nest on a table.",
            feedback="You moved east. You see a nest on a table.",
            reward=0.0,  # No reward yet
            done=False,
            admissible_commands=commands2,
            quest={'description': quest}
        )

        # CRITICAL: Should have advanced to subgoal 1
        assert agent.current_subgoal_index == 1, \
            f"Expected subgoal_index=1 after movement, got {agent.current_subgoal_index}"

        # Should now be selecting actions for "take nest"
        assert "nest" in action2.lower()
        assert "take" in action2.lower()

    def test_three_step_quest_full_sequence(self, neo4j_session):
        """
        Test: Complete 3-step quest with proper advancement.

        This tests the EXACT scenario from TextWorld game.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        quest = "First, move east. Then, take nest from table. Finally, place nest in dresser."
        agent.reset(quest)

        assert len(agent.subgoals) == 3
        assert agent.current_subgoal_index == 0

        # === STEP 1: Movement ===
        commands1 = ["go east", "examine table", "look"]
        action1 = agent.step("You are in attic.", "", 0.0, False, commands1, {'description': quest})

        assert "east" in action1.lower(), f"Step 1 should select movement, got: {action1}"
        assert agent.current_subgoal_index == 0  # No advancement yet (happens at start of next step)

        # === STEP 2: Take nest ===
        commands2 = ["take nest of spiders from table", "examine nest", "go west"]
        action2 = agent.step("You moved east. You see nest on table.", "", 0.0, False, commands2, {'description': quest})

        # Should have advanced to subgoal 1 (take nest)
        assert agent.current_subgoal_index == 1, \
            f"After movement, should be on subgoal 1, got {agent.current_subgoal_index}"

        assert "nest" in action2.lower() and "take" in action2.lower(), \
            f"Step 2 should take nest, got: {action2}"

        # === STEP 3: Place nest ===
        commands3 = ["insert nest of spiders into dresser", "put nest of spiders on table", "drop nest"]
        action3 = agent.step("You took the nest.", "", 0.0, False, commands3, {'description': quest})

        # Should have advanced to subgoal 2 (place nest)
        assert agent.current_subgoal_index == 2, \
            f"After taking nest, should be on subgoal 2, got {agent.current_subgoal_index}"

        # CRITICAL: Should select "insert...into dresser" NOT "put...on table"
        assert "insert" in action3.lower() or "place" in action3.lower(), \
            f"Step 3 should insert/place nest in dresser, got: {action3}"
        assert "dresser" in action3.lower(), \
            f"Step 3 should target dresser, got: {action3}"


class TestPlanInterference:
    """Test that plan generation doesn't override subgoal-based decisions."""

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

    def test_subgoal_scoring_dominates_plan(self, neo4j_session):
        """
        Test: Subgoal match should score higher than plan match.

        Scenario:
        - Current subgoal: "place nest in dresser"
        - Available: ["insert nest into dresser", "put nest on table"]
        - Even if plan suggests "put on table", subgoal match should win
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.reset("First, take nest. Then, place nest in dresser.")

        # Advance to subgoal 1 (place nest)
        agent.current_subgoal_index = 1

        commands = [
            "insert nest of spiders into dresser",  # Perfect subgoal match
            "put nest of spiders on table",          # Partial match (nest, but wrong target)
            "examine dresser"
        ]

        # Manually check scores
        current_subgoal = agent.subgoals[agent.current_subgoal_index]

        scores = {}
        for action in commands:
            score = agent.score_action(action, agent.beliefs, None, current_subgoal)
            scores[action] = score

        # "insert...into dresser" should score HIGHEST
        best_action = max(scores, key=scores.get)

        assert "insert" in best_action.lower() and "dresser" in best_action.lower(), \
            f"Should prefer 'insert...into dresser', but scored: {scores}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_step2_should_advance"])
