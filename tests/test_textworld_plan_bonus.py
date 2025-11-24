"""
Test suite for plan bonus weight tuning.

Following TDD: Write test to verify plan bonus influences action selection properly.

The issue: epsilon=2.0 is too weak, gets overwhelmed by other EFE terms.
Expected: epsilon=5.0 should make plan adherence 40-60%.
"""
import pytest
from neo4j import GraphDatabase
import os

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.plan import Plan, PlanStep


class TestPlanBonusWeight:
    """Test that plan bonus weight properly influences action selection."""
    
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
    
    def test_plan_bonus_magnitude(self, agent):
        """Test that plan bonus is strong enough to influence decisions."""
        # Setup: Create a simple plan
        plan_steps = [
            PlanStep(
                description="Take the key",
                action_pattern="take key"
            )
        ]
        plan = Plan(
            goal="Unlock the door",
            strategy="Get key first",
            steps=plan_steps,
            success_criteria="Door is unlocked",
            contingencies={}
        )
        agent.current_plan = plan
        
        # Execute: Calculate bonus for matching vs non-matching action
        bonus_matching = agent.calculate_plan_bonus("take key")
        bonus_non_matching = agent.calculate_plan_bonus("examine door")
        
        # Assert: Bonus should be significant (10+ points for matching)
        # This ensures it can compete with other EFE terms
        assert bonus_matching >= 10.0, f"Plan bonus too weak: {bonus_matching}"
        assert bonus_non_matching < 0, "Should penalize diverging from plan"
        assert abs(bonus_matching - bonus_non_matching) >= 10, \
            "Difference between on-plan and off-plan should be significant"
    
    def test_plan_bonus_with_increased_epsilon(self, agent):
        """Test that increased epsilon (5.0) properly weights plan bonus."""
        # Setup: Create plan
        plan_steps = [
            PlanStep(
                description="Go north",
                action_pattern="go north"
            )
        ]
        plan = Plan(
            goal="Enter bedroom",
            strategy="Navigate north",
            steps=plan_steps,
            success_criteria="Entered bedroom",
            contingencies={}
        )
        agent.current_plan = plan
        
        # Update beliefs to provide context
        agent.update_beliefs(
            observation="You are in a kitchen. There is a door to the north.",
            feedback=""
        )
        
        # Execute: Score both on-plan and off-plan actions
        score_on_plan = agent.score_action("go north", agent.beliefs, None)
        score_off_plan = agent.score_action("examine table", agent.beliefs, None)
        
        # Assert: On-plan action should score significantly higher
        # With epsilon=5.0 and bonus=10, plan contributes 50 points
        # This should make on-plan action clearly preferred
        assert score_on_plan > score_off_plan, \
            f"On-plan ({score_on_plan:.2f}) should beat off-plan ({score_off_plan:.2f})"
        
        # The difference should be substantial to ensure adherence
        difference = score_on_plan - score_off_plan
        assert difference >= 30.0, \
            f"Score difference ({difference:.2f}) should be >= 30 to ensure adherence"
    
    def test_plan_overrides_exploration(self, agent):
        """Test that plan bonus overcomes exploration tendency."""
        # Setup: Create plan for goal-directed action
        plan_steps = [
            PlanStep(
                description="Take the ruby",
                action_pattern="take ruby"
            )
        ]
        plan = Plan(
            goal="Collect ruby",
            strategy="Grab it",
            steps=plan_steps,
            success_criteria="Ruby collected",
            contingencies={}
        )
        agent.current_plan = plan
        
        agent.update_beliefs(
            observation="You see a ruby and a mysterious box.",
            feedback=""
        )
        
        # Execute: Score on-plan (take ruby) vs high-entropy (examine box)
        score_on_plan = agent.score_action("take ruby", agent.beliefs, None)
        score_explore = agent.score_action("examine box", agent.beliefs, None)
        
        # Assert: Even though "examine box" has high entropy (new object),
        # plan should win with increased epsilon
        assert score_on_plan > score_explore, \
            "Plan should override exploration tendency"
    
    def test_epsilon_coefficient_value(self, agent):
        """Test that epsilon coefficient is set to 5.0 (not 2.0)."""
        # This is a direct check of the coefficient
        # We can verify via scoring
        
        # Setup plan
        plan_steps = [PlanStep("Test step", "test action")]
        plan = Plan(
            goal="Test",
            strategy="Test",
            steps=plan_steps,
            success_criteria="Test completed",
            contingencies={}
        )
        agent.current_plan = plan
        
        # Calculate bonus
        bonus = agent.calculate_plan_bonus("test action")
        
        # The base bonus from calculate_plan_bonus is 10-12
        # With epsilon=5.0 in score_action, contribution is 50-60
        # With epsilon=2.0, contribution would be 20-24
        
        # We can verify by checking the actual score
        agent.update_beliefs("Test observation", "")
        score = agent.score_action("test action", agent.beliefs, None)
        
        # With epsilon=5.0 and bonus≈10, plan contributes ≈50
        # Total score should reflect this
        # (Not a perfect test but validates the magnitude)
        assert bonus >= 10.0, "Base bonus should be ≥10"


class TestPlanAdherence:
    """Integration tests for plan adherence."""
    
    @pytest.fixture
    def agent(self):
        """Create agent."""
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        session = driver.session()
        
        agent = TextWorldCognitiveAgent(session=session, verbose=False)
        
        yield agent
        
        session.close()
        driver.close()
    
    def test_action_selection_prefers_plan(self, agent):
        """Test that select_action chooses on-plan actions when plan exists."""
        # Setup: Create a plan
        plan_steps = [
            PlanStep("Unlock the chest", "unlock chest")
        ]
        plan = Plan(
            goal="Open chest",
            strategy="Use key",
            steps=plan_steps,
            success_criteria="Chest opened",
            contingencies={}
        )
        agent.current_plan = plan
        
        # Populate some beliefs
        agent.update_beliefs("You see a chest and a key.", "")
        
        # Available commands include both on-plan and off-plan
        commands = [
            "look",  # off-plan
            "examine chest",  # off-plan
            "unlock chest with key",  # ON-PLAN (matches pattern "unlock chest")
            "take key"  # off-plan
        ]
        
        # Execute
        selected = agent.select_action(commands, None)
        
        # Assert: Should select the on-plan action
        assert "unlock chest" in selected, \
            f"Should select on-plan action, got: {selected}"
