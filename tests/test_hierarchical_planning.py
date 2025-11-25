
import unittest
from unittest.mock import MagicMock
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.plan import Plan, PlanStep

class TestHierarchicalPlanning(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(self.mock_session, verbose=False)
        
        # Mock the planner
        self.agent.planner = MagicMock()
        
    def test_plan_generation(self):
        """
        Test that the agent can generate a plan for a high-level goal.
        """
        goal = "Open the safe"
        # Mock the planner response - return a Plan object
        expected_steps = [
            PlanStep(description="Find key", action_pattern="find key"),
            PlanStep(description="Take key", action_pattern="take key"),
            PlanStep(description="Unlock safe", action_pattern="unlock safe"),
            PlanStep(description="Open safe", action_pattern="open safe")
        ]
        expected_plan = Plan(
            goal=goal,
            strategy="Multi-step safe opening",
            steps=expected_steps,
            success_criteria="Safe is open",
            contingencies={}
        )
        self.agent.planner.generate_plan.return_value = expected_plan
        
        plan = self.agent.generate_plan(goal)
        
        self.assertEqual(plan, expected_plan)
        self.assertEqual(self.agent.current_plan, expected_plan)

    def test_plan_execution_score(self):
        """
        Test that actions matching the current plan step get a massive score bonus.
        """
        # Set a plan using Plan class
        steps = [
            PlanStep(description="Take key", action_pattern="take key"),
            PlanStep(description="Unlock safe", action_pattern="unlock safe")
        ]
        self.agent.current_plan = Plan(
            goal="Open safe",
            strategy="Take key then unlock",
            steps=steps,
            success_criteria="Safe unlocked",
            contingencies={}
        )
        
        # 'take key' is the next step
        score_plan = self.agent.score_action('take key', self.agent.beliefs)
        score_other = self.agent.score_action('go north', self.agent.beliefs)
        
        print(f"Score Plan: {score_plan}, Score Other: {score_other}")
        
        # The plan bonus should be significant (e.g., +10.0)
        self.assertGreater(score_plan, score_other + 5.0, "Planned action should be heavily prioritized")

if __name__ == '__main__':
    unittest.main()
