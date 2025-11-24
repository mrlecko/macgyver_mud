"""
Integration tests for TextWorld planning system.

Tests the full planning loop:
- Goal inference from context
- Plan generation via LLM
- Plan progress tracking
- Plan bonus calculation
- Plan completion detection
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.plan import Plan, PlanStep, PlanStatus


class TestPlanningIntegration:
    """Test planning integration with cognitive agent."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Neo4j session
        mock_session = MagicMock()

        # Create agent with mocked session
        self.agent = TextWorldCognitiveAgent(
            session=mock_session,
            verbose=False
        )

        # Mock memory retrieval to avoid Neo4j calls
        self.agent.memory.retrieve_relevant_memories = Mock(return_value=[])

    def test_goal_inference_from_quest(self):
        """Test that goals are inferred from quest state."""
        # Set up quest state
        self.agent.beliefs['quest_state'] = {
            'description': 'Find the golden key and unlock the treasure chest'
        }

        goal = self.agent._infer_goal_from_context()

        assert goal is not None
        assert 'golden key' in goal
        assert 'treasure chest' in goal

    def test_goal_inference_from_observation(self):
        """Test goal inference from observation heuristics."""
        # Set up observation with locked chest
        self.agent.observation_history = [{
            'observation': 'You see a locked chest and a rusty key on the floor.',
            'step': 1
        }]

        goal = self.agent._infer_goal_from_context()

        assert goal is not None
        assert 'chest' in goal.lower()

    def test_no_goal_when_unclear(self):
        """Test that no goal is inferred when context is unclear."""
        # Empty observation
        self.agent.observation_history = [{
            'observation': 'You are in a room.',
            'step': 1
        }]
        self.agent.beliefs['quest_state'] = None

        goal = self.agent._infer_goal_from_context()

        assert goal is None

    def test_build_planning_context(self):
        """Test that planning context is built correctly."""
        # Set up beliefs
        self.agent.beliefs = {
            'current_room': 'Dark Cellar',
            'rooms': {
                'Dark Cellar': {
                    'objects': ['chest', 'table', 'lamp']
                }
            },
            'inventory': ['rusty key']
        }

        admissible_commands = [
            'examine chest',
            'take lamp',
            'unlock chest with rusty key',
            'open chest',
            'look around'
        ]

        context = self.agent._build_planning_context(admissible_commands)

        assert 'Dark Cellar' in context
        assert 'chest' in context
        assert 'rusty key' in context
        assert 'examine chest' in context

    def test_get_recent_failures(self):
        """Test that recent plan failures are extracted."""
        # Create some failed plans
        failed_plan1 = Plan(
            goal="Find the key",
            strategy="Search everywhere",
            steps=[PlanStep("Look around", "look")],
            success_criteria="Key is in inventory",
            contingencies={},
            confidence=0.5,
            status=PlanStatus.FAILED
        )
        failed_plan1.failure_reason = "Key not in any visible location"

        failed_plan2 = Plan(
            goal="Unlock door",
            strategy="Use rusty key",
            steps=[PlanStep("Unlock door", "unlock door")],
            success_criteria="Door is open",
            contingencies={},
            confidence=0.6,
            status=PlanStatus.FAILED
        )
        failed_plan2.failure_reason = "Rusty key doesn't fit"

        self.agent.plan_history = [failed_plan1, failed_plan2]

        failures = self.agent._get_recent_failures()

        assert len(failures) == 2
        assert "Find the key" in failures[0]
        assert "not in any visible location" in failures[0]
        assert "Unlock door" in failures[1]
        assert "doesn't fit" in failures[1]

    def test_plan_generation_skipped_when_no_goal(self):
        """Test that plan generation is skipped when no goal is clear."""
        # Ensure no clear goal
        self.agent.observation_history = [{
            'observation': 'Empty room',
            'step': 5
        }]
        self.agent.beliefs = {'current_room': 'Empty Room'}
        self.agent.current_step = 5
        self.agent.current_plan = None

        # Should not generate plan
        self.agent.maybe_generate_plan(['look', 'wait'])

        assert self.agent.current_plan is None

    def test_plan_generation_skipped_when_plan_active(self):
        """Test that new plans aren't generated when one is active."""
        # Set up active plan
        active_plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[PlanStep("Test step", "test")],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE
        )
        self.agent.current_plan = active_plan
        self.agent.current_step = 5

        # Set up goal context
        self.agent.beliefs['quest_state'] = {
            'description': 'Find something'
        }

        # Should not generate new plan
        initial_plan = self.agent.current_plan
        self.agent.maybe_generate_plan(['look', 'take'])

        assert self.agent.current_plan is initial_plan

    @patch('environments.domain4_textworld.llm_planner.subprocess.run')
    def test_plan_generation_with_llm(self, mock_subprocess):
        """Test that plan generation calls LLM correctly."""
        # Mock LLM response
        mock_subprocess.return_value = Mock(
            stdout='{"goal":"Find key","strategy":"Search the room","steps":[{"description":"Look around","action_pattern":"look"},{"description":"Take key","action_pattern":"take key"}],"success_criteria":"Key in inventory","contingencies":{"stuck":"Try another room"},"confidence":0.8}',
            stderr='',
            returncode=0
        )

        # Set up context for plan generation
        self.agent.current_step = 5
        self.agent.observation_history = [{
            'observation': 'You see a locked chest.',
            'step': 5
        }]
        self.agent.beliefs = {
            'current_room': 'Cellar',
            'rooms': {'Cellar': {'objects': ['chest']}},
            'inventory': []
        }

        # Generate plan
        self.agent.maybe_generate_plan(['look', 'examine chest'])

        # Verify plan was created
        assert self.agent.current_plan is not None
        assert self.agent.current_plan.goal is not None
        assert len(self.agent.current_plan.steps) > 0
        assert self.agent.current_plan.status == PlanStatus.ACTIVE

    def test_check_plan_progress_no_plan(self):
        """Test plan progress check when no plan exists."""
        self.agent.current_plan = None

        # Should not crash
        self.agent.check_plan_progress("look around")

        assert self.agent.current_plan is None

    def test_check_plan_progress_step_completed(self):
        """Test plan progress tracking when step is completed."""
        # Create plan with steps
        plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[
                PlanStep("First step", "look"),
                PlanStep("Second step", "take key")
            ],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE
        )
        self.agent.current_plan = plan

        # Execute action that matches first step
        self.agent.check_plan_progress("look around")

        # First step should be completed
        assert plan.steps[0].completed
        assert not plan.steps[1].completed
        assert plan.progress_ratio() == 0.5

    def test_check_plan_progress_completion(self):
        """Test plan completion detection."""
        # Create plan with one step
        plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[PlanStep("Only step", "look")],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE,
            created_at_step=1
        )
        self.agent.current_plan = plan
        self.agent.current_step = 10

        # Complete the step
        self.agent.check_plan_progress("look around")

        # Plan should be completed and archived
        assert len(self.agent.plan_history) == 1
        assert self.agent.plan_history[0].status == PlanStatus.COMPLETED
        assert self.agent.plan_history[0].completed_at_step == 10
        assert self.agent.current_plan is None

    def test_calculate_plan_bonus_no_plan(self):
        """Test plan bonus when no plan exists."""
        self.agent.current_plan = None

        bonus = self.agent.calculate_plan_bonus("any action")

        assert bonus == 0.0

    def test_calculate_plan_bonus_matching_action(self):
        """Test plan bonus for action matching current step."""
        # Create plan
        plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[PlanStep("Take the key", "take key")],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE
        )
        self.agent.current_plan = plan

        # Action matches current step
        bonus = self.agent.calculate_plan_bonus("take the golden key")

        assert bonus > 0.0
        assert bonus >= 10.0  # Base bonus

    def test_calculate_plan_bonus_non_matching_action(self):
        """Test plan bonus penalty for action not matching current step."""
        # Create plan
        plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[PlanStep("Take the key", "take key")],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE
        )
        self.agent.current_plan = plan

        # Action doesn't match current step
        bonus = self.agent.calculate_plan_bonus("examine chest")

        assert bonus < 0.0  # Penalty

    def test_calculate_plan_bonus_completed_plan(self):
        """Test plan bonus when plan is complete."""
        # Create plan with all steps completed
        plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[PlanStep("Take the key", "take key", completed=True)],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE
        )
        self.agent.current_plan = plan

        # No current step (all done)
        bonus = self.agent.calculate_plan_bonus("any action")

        assert bonus == 0.0

    def test_plan_bonus_fresh_attempt_extra_bonus(self):
        """Test that first attempt at step gets extra bonus."""
        # Create plan
        plan = Plan(
            goal="Test goal",
            strategy="Test strategy",
            steps=[PlanStep("Take the key", "take key")],
            success_criteria="Success",
            contingencies={},
            confidence=0.7,
            status=PlanStatus.ACTIVE
        )
        self.agent.current_plan = plan

        # First attempt (attempts = 0)
        assert plan.steps[0].attempts == 0
        bonus_first = self.agent.calculate_plan_bonus("take key")

        # Increment attempts
        plan.steps[0].attempts = 1
        bonus_second = self.agent.calculate_plan_bonus("take key")

        # First attempt should have higher bonus
        assert bonus_first > bonus_second
        assert bonus_first >= bonus_second + 2.0


class TestPlanningEndToEnd:
    """End-to-end integration tests."""

    @patch('environments.domain4_textworld.llm_planner.subprocess.run')
    def test_full_planning_cycle(self, mock_subprocess):
        """Test complete planning cycle from generation to completion."""
        # Mock LLM response
        mock_subprocess.return_value = Mock(
            stdout='{"goal":"Find and take the key","strategy":"Search the room systematically","steps":[{"description":"Look around the room","action_pattern":"look"},{"description":"Take the key","action_pattern":"take key"}],"success_criteria":"Key is in inventory","contingencies":{"stuck":"Examine objects"},"confidence":0.8}',
            stderr='',
            returncode=0
        )

        # Create agent with mock session
        mock_session = MagicMock()
        agent = TextWorldCognitiveAgent(
            session=mock_session,
            verbose=True
        )
        agent.memory.retrieve_relevant_memories = Mock(return_value=[])

        # Set up scenario: locked chest visible
        agent.current_step = 5
        agent.observation_history = [{
            'observation': 'You see a locked chest and a golden key on the table.',
            'step': 5
        }]
        agent.beliefs = {
            'current_room': 'Treasure Room',
            'rooms': {
                'Treasure Room': {
                    'objects': ['chest', 'key', 'table']
                }
            },
            'inventory': []
        }

        # 1. Generate plan
        agent.maybe_generate_plan(['look', 'take key', 'examine chest'])

        assert agent.current_plan is not None
        assert agent.current_plan.status == PlanStatus.ACTIVE
        assert len(agent.current_plan.steps) == 2
        initial_plan = agent.current_plan

        # 2. Execute first step
        agent.check_plan_progress("look around")

        assert agent.current_plan.steps[0].completed
        assert agent.current_plan.progress_ratio() == 0.5

        # 3. Plan bonus should favor next step
        bonus_matching = agent.calculate_plan_bonus("take the golden key")
        bonus_wrong = agent.calculate_plan_bonus("examine chest")

        assert bonus_matching > bonus_wrong
        assert bonus_matching > 0.0
        assert bonus_wrong < 0.0

        # 4. Execute second step
        agent.check_plan_progress("take the golden key")

        assert agent.current_plan is None  # Plan completed and archived
        assert len(agent.plan_history) == 1
        assert agent.plan_history[0] is initial_plan
        assert agent.plan_history[0].status == PlanStatus.COMPLETED
        assert agent.plan_history[0].is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
