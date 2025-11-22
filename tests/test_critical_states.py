import pytest
from unittest.mock import MagicMock
from critical_state import CriticalStateMonitor, CriticalState, AgentState

@pytest.fixture
def monitor():
    return CriticalStateMonitor()

@pytest.fixture
def state():
    # Initialize with default safe values
    return AgentState(
        entropy=0.2,
        history=[],
        steps=100,
        dist=10,
        rewards=[],
        error=0.0
    )

def test_flow_state(monitor, state):
    """Test that normal conditions result in FLOW state."""
    assert monitor.evaluate(state) == CriticalState.FLOW

def test_scarcity_state(monitor, state):
    """Test SCARCITY trigger: Steps < Distance * 1.2"""
    state.distance_to_goal = 10
    state.steps_remaining = 11  # 11 < 12
    assert monitor.evaluate(state) == CriticalState.SCARCITY

def test_panic_state(monitor, state):
    """Test PANIC trigger: Entropy > 0.45"""
    state.entropy = 0.5
    assert monitor.evaluate(state) == CriticalState.PANIC

def test_deadlock_state(monitor, state):
    """Test DEADLOCK trigger: Looping location history"""
    # A -> B -> A -> B pattern
    state.location_history = ["A", "B", "A", "B"]
    assert monitor.evaluate(state) == CriticalState.DEADLOCK

def test_novelty_state(monitor, state):
    """Test NOVELTY trigger: High Prediction Error"""
    state.prediction_error = 0.9
    assert monitor.evaluate(state) == CriticalState.NOVELTY

def test_hubris_state(monitor, state):
    """Test HUBRIS trigger: High Reward Streak + Low Entropy"""
    state.entropy = 0.05
    state.reward_history = [1.0] * 6 # Streak > 5
    assert monitor.evaluate(state) == CriticalState.HUBRIS

def test_priority_resolution(monitor, state):
    """Test that higher priority states override lower ones."""
    
    # Scarcity (1) vs Panic (2) -> Scarcity wins
    state.distance_to_goal = 10
    state.steps_remaining = 11 # Scarcity
    state.entropy = 0.5        # Panic
    assert monitor.evaluate(state) == CriticalState.SCARCITY
    
    # Panic (2) vs Deadlock (3) -> Panic wins
    state.steps_remaining = 100 # Clear Scarcity
    state.entropy = 0.5         # Panic
    state.location_history = ["A", "B", "A", "B"] # Deadlock
    assert monitor.evaluate(state) == CriticalState.PANIC

    # Deadlock (3) vs Novelty (4) -> Deadlock wins
    state.entropy = 0.2         # Clear Panic
    state.location_history = ["A", "B", "A", "B"] # Deadlock
    state.prediction_error = 0.9 # Novelty
    assert monitor.evaluate(state) == CriticalState.DEADLOCK

    # Novelty (4) vs Hubris (5) -> Novelty wins
    state.location_history = ["A", "B", "C", "D"] # Clear Deadlock
    state.prediction_error = 0.9 # Novelty
    state.entropy = 0.05         # Hubris condition
    state.reward_history = [1.0] * 6 # Hubris condition
    assert monitor.evaluate(state) == CriticalState.NOVELTY
