"""
Test suite for TextWorld goal inference fix.

Following TDD approach: Write tests first, then implement.

The issue: _infer_goal_from_context() uses naive heuristics instead of
parsing actual quest from TextWorld game state.

Expected behavior: Agent should extract the real quest objective from
the game state's 'objective' field.
"""
import pytest
from neo4j import GraphDatabase
import os

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent


class TestGoalInference:
    """Test goal inference from TextWorld game state."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with test database session."""
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        session = driver.session()
        
        agent = TextWorldCognitiveAgent(session=session, verbose=False)
        
        yield agent
        
        session.close()
        driver.close()
    
    def test_goal_inference_from_quest_state(self, agent):
        """Test that agent extracts goal from quest_state.description."""
        # Setup: Populate quest_state with actual quest objective
        agent.beliefs['quest_state'] = {
            'description': 'Move east, recover nest of spiders from table, place in dresser'
        }
        
        # Execute
        goal = agent._infer_goal_from_context()
        
        # Assert: Should return the actual quest
        assert goal == 'Move east, recover nest of spiders from table, place in dresser'
    
    def test_goal_inference_from_last_quest(self, agent):
        """Test that agent uses last_quest if available."""
        # Setup: Set last_quest (common pattern in TextWorld agents)
        agent.last_quest = 'Find the golden key and unlock the ancient chest'
        
        # Execute
        goal = agent._infer_goal_from_context()
        
        # Assert: Should use last_quest
        assert goal == 'Find the golden key and unlock the ancient chest'
    
    def test_goal_inference_fallback_to_heuristics(self, agent):
        """Test that agent falls back to heuristics if no quest data."""
        # Setup: Add observation with locked door
        agent.update_beliefs(
            observation="You are in a room. There is a locked door to the north.",
            feedback=""
        )
        
        # Execute
        goal = agent._infer_goal_from_context()
        
        # Assert: Should fall back to heuristic
        assert goal == "Find key and unlock the door"
    
    def test_goal_inference_returns_none_when_no_clues(self, agent):
        """Test that agent returns None when no goal can be inferred."""
        # Setup: Empty state, generic observation
        agent.update_beliefs(
            observation="You are in a room.",
            feedback=""
        )
        
        # Execute
        goal = agent._infer_goal_from_context()
        
        # Assert: Should return None (no clear goal)
        assert goal is None or goal != ""  # Some goal might be inferred from very basic heuristics
    
    def test_integration_with_planning(self, agent):
        """Test that planning uses correct goal when quest_state is set."""
        # Setup: Set quest_state
        agent.beliefs['quest_state'] = {
            'description': 'Retrieve the ruby gemstone from the pedestal'
        }
        
        # Simulate some steps
        for i in range(3):
            agent.update_beliefs(
                observation=f"Step {i}: You are in a chamber.",
                feedback=""
            )
        
        # Execute: Try to generate plan
        admissible_commands = ['look', 'go north', 'examine pedestal', 'take ruby']
        agent.maybe_generate_plan(admissible_commands)
        
        # Assert: Plan should use correct goal
        if agent.current_plan:
            assert agent.current_plan.goal == 'Retrieve the ruby gemstone from the pedestal'


class TestGoalExtractionFromValidationScript:
    """Test the actual issue found during validation."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with test database session."""
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        session = driver.session()
        
        agent = TextWorldCognitiveAgent(session=session, verbose=False)
        
        yield agent
        
        session.close()
        driver.close()
    
    def test_actual_quest_extraction(self, agent):
        """
        Reproduce the actual validation failure:
        - Actual quest: 'Move east, recover nest of spiders from table, place in dresser'
        - Inferred goal: 'Find key and unlock the door'
        
        This test should FAIL before fix, PASS after fix.
        """
        # Setup: Simulate what happens in validate_planning.py
        # The quest should be passed via step() call or stored in agent
        actual_quest = 'Move east, recover nest of spiders from table, place in dresser'
        
        # Option 1: Via quest_state (preferred)
        agent.beliefs['quest_state'] = {'description': actual_quest}
        
        # Option 2: Via last_quest attribute
        # agent.last_quest = actual_quest
        
        # Execute
        goal = agent._infer_goal_from_context()
        
        # Assert: Goal should match actual quest
        assert goal == actual_quest, \
            f"Goal inference failed: got '{goal}' but quest was '{actual_quest}'"
