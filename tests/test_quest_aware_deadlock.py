"""
Test Quest-Aware DEADLOCK Detection

Tests the enhanced DEADLOCK protocol that distinguishes between:
- TRUE DEADLOCK: Stuck on same subgoal with no progress
- VALID BACKTRACKING: Revisiting locations while making subgoal progress

Following TDD: Write tests FIRST, then implement functionality.
"""

import sys
sys.path.insert(0, '/home/juancho/macgyver_mud')

import pytest
from unittest.mock import Mock, MagicMock
from neo4j import GraphDatabase

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from critical_state import CriticalState, CriticalStateMonitor


def create_test_agent():
    """Create cognitive agent with mock Neo4j session for testing."""
    mock_session = MagicMock()
    mock_session.run = MagicMock(return_value=[])
    
    agent = TextWorldCognitiveAgent(session=mock_session, verbose=False)
    return agent


class TestQuestAwareDeadlockDetection:
    """Test suite for quest-aware DEADLOCK detection."""
    
    def test_no_deadlock_when_making_subgoal_progress(self):
        """
        Scenario: Agent advancing through subgoals (no deadlock).
        
        Quest: "Find key, unlock chest"
        Subgoals: ["find key", "unlock chest"]
        
        Steps:
        1-3: Working on subgoal 0 (find key) - 3 steps
        4-6: Working on subgoal 1 (unlock chest) - 3 steps
        
        Expected: No DEADLOCK (making progress through subgoals)
        """
        agent = create_test_agent()
        agent.reset(quest="Find the key and unlock the chest")
        
        # Simulate advancing through subgoals
        agent.subgoals = ["find key", "unlock chest"]
        agent.current_subgoal_index = 0
        agent.steps_on_current_subgoal = 0
        
        # Spend 3 steps on first subgoal
        for _ in range(3):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0)  # No reward yet
        
        # Check no deadlock at 3 steps (threshold is 5)
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state != CriticalState.DEADLOCK, \
            "Should not detect DEADLOCK at 3 steps on subgoal"
        
        # Advance to next subgoal (progress!)
        agent.current_subgoal_index = 1
        agent.steps_on_current_subgoal = 0  # Reset counter
        
        # Spend 3 more steps on second subgoal
        for _ in range(3):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0)
        
        # Still no deadlock (advancing through plan)
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state != CriticalState.DEADLOCK, \
            "Should not detect DEADLOCK when advancing subgoals"
    
    def test_deadlock_when_stuck_on_same_subgoal(self):
        """
        Scenario: Agent stuck on same subgoal for 6 steps (DEADLOCK).
        
        Quest: "Find the key"
        Subgoals: ["find key"]
        
        Steps 1-6: All on same subgoal, no progress, no reward
        
        Expected: DEADLOCK detected at step 6 (threshold)
        """
        agent = create_test_agent()
        agent.reset(quest="Find the key")
        
        agent.subgoals = ["find key"]
        agent.current_subgoal_index = 0
        agent.steps_on_current_subgoal = 0
        
        # Simulate being stuck (6 steps, no progress)
        for i in range(6):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0)  # No reward
        
        # Check right at threshold
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state == CriticalState.DEADLOCK, \
            f"Should detect DEADLOCK at 6 steps on same subgoal, got {critical_state}"
    
    def test_no_deadlock_if_getting_rewards(self):
        """
        Scenario: Many steps but making progress (rewards).
        
        Even if 6+ steps on same subgoal, if getting rewards → not stuck.
        
        Expected: No DEADLOCK
        """
        agent = create_test_agent()
        agent.reset(quest="Collect 10 items")
        
        agent.subgoals = ["collect items"]
        agent.current_subgoal_index = 0
        agent.steps_on_current_subgoal = 0
        
        # Take 7 steps, but getting rewards
        for i in range(7):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0.1)  # Small rewards (progress!)
        
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state != CriticalState.DEADLOCK, \
            "Should not detect DEADLOCK when making progress (rewards)"
    
    def test_deadlock_resets_when_advancing_subgoal(self):
        """
        Scenario: Steps accumulate per-subgoal, not globally.
        
        3 steps on subgoal 0, advance, 3 steps on subgoal 1
        = No deadlock (max 3 per subgoal)
        
        Expected: Counter resets on subgoal advancement
        """
        agent = create_test_agent()
        agent.reset(quest="First X, then Y")
        
        agent.subgoals = ["do X", "do Y"]
        agent.current_subgoal_index = 0
        agent.steps_on_current_subgoal = 0
        
        # 3 steps on first subgoal
        for _ in range(3):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0)
        
        # Advance subgoal (reset counter!)
        agent.current_subgoal_index = 1
        agent.steps_on_current_subgoal = 0
        
        # 3 steps on second subgoal
        for _ in range(3):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0)
        
        # Should not be deadlock (never more than 3 on same subgoal)
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state != CriticalState.DEADLOCK, \
            "Counter should reset per subgoal"
    
    def test_backward_compatible_without_quest(self):
        """
        Scenario: Agent used without quest (MacGyver mode).
        
        Should fall back to original DEADLOCK detection.
        
        Expected: No crash, uses location-based detection
        """
        agent = create_test_agent()
        agent.reset()  # No quest
        
        # Should work without subgoals
        assert agent.subgoals == []
        
        # Simulate some steps
        for _ in range(6):
            agent.location_history.append("room_A")
            agent.reward_history.append(0)
        
        # Should detect deadlock via location-based method
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        # Will detect via old method (A→A→A→A loop)
        assert critical_state == CriticalState.DEADLOCK, \
            "Should use original detection when no quest"


class TestDeadlockThresholdTuning:
    """Test DEADLOCK threshold is reasonable."""
    
    def test_threshold_allows_reasonable_exploration(self):
        """
        5 steps on same subgoal should be allowed.
        6+ steps with no progress = stuck.
        """
        agent = create_test_agent()
        agent.reset(quest="Test quest")
        
        agent.subgoals = ["test"]
        agent.current_subgoal_index = 0
        agent.steps_on_current_subgoal = 0
        
        # 5 steps = OK
        for _ in range(5):
            agent.steps_on_current_subgoal += 1
            agent.reward_history.append(0)
        
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state != CriticalState.DEADLOCK, \
            "5 steps should be allowed for exploration"
        
        # 6 steps = DEADLOCK
        agent.steps_on_current_subgoal += 1
        agent.reward_history.append(0)
        
        state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(state)
        
        assert critical_state == CriticalState.DEADLOCK, \
            "6+ steps should trigger DEADLOCK"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
