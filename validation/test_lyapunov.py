import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.lyapunov import LyapunovMetric, StabilityMonitor
from environments.labyrinth import LabyrinthEnvironment
from agent_runtime import AgentEscalationError
from collections import namedtuple

# Mock AgentState for testing
AgentState = namedtuple('AgentState', ['entropy', 'dist', 'steps'])

class MockAgentRuntime:
    """Minimal runtime to test Lyapunov integration without Neo4j."""
    def __init__(self):
        self.lyapunov_monitor = StabilityMonitor(window_size=10, divergence_threshold=0.02)
        
    def step(self, state):
        # Calculate metrics
        entropy = state['entropy']
        distance = state['distance_estimate']
        stress = state['stress']
        
        # Update monitor
        v = self.lyapunov_monitor.update(entropy, distance, stress)
        
        # Check divergence
        if self.lyapunov_monitor.is_diverging():
            raise AgentEscalationError(f"LYAPUNOV DIVERGENCE DETECTED (V={v:.2f})")
            
        return v

def test_lyapunov_metric():
    """Test that V increases with bad metrics."""
    metric = LyapunovMetric()
    
    v_good = metric.calculate_v(entropy=0.1, distance_estimate=5, stress=0.1)
    v_bad = metric.calculate_v(entropy=0.9, distance_estimate=20, stress=0.8)
    
    assert v_bad > v_good

def test_monitor_divergence():
    """Test that monitor detects positive trend."""
    monitor = StabilityMonitor(window_size=5, divergence_threshold=0.1)
    
    # Feed increasing values
    for i in range(10):
        monitor.update(entropy=0.5, distance_estimate=i, stress=0.0)
        
    assert monitor.is_diverging()
    assert not monitor.is_converging()

def test_monitor_convergence():
    """Test that monitor detects negative trend."""
    monitor = StabilityMonitor(window_size=5, divergence_threshold=0.1)
    
    # Feed decreasing values
    for i in range(10, 0, -1):
        monitor.update(entropy=0.5, distance_estimate=i, stress=0.0)
        
    assert not monitor.is_diverging()
    assert monitor.is_converging()

def test_infinite_labyrinth_divergence():
    """
    The Divergence Test:
    Agent in Infinite Labyrinth should eventually trigger Lyapunov Alarm.
    """
    env = LabyrinthEnvironment(mode='infinite', max_steps=100)
    agent = MockAgentRuntime()
    # Adjust for noisy environment - Re-initialize monitor to resize deque
    agent.lyapunov_monitor = StabilityMonitor(window_size=20, divergence_threshold=0.01)
    
    divergence_detected = False
    
    try:
        state = env.reset()
        for i in range(50):
            # Naive agent just moves
            next_state, _, done, _ = env.step('move')
            v = agent.step(next_state)
            slope = agent.lyapunov_monitor.get_trend()
            print(f"Step {i}: V={v:.2f}, Slope={slope:.4f}, Diverging={agent.lyapunov_monitor.is_diverging()}")
            if done: break
            
    except AgentEscalationError as e:
        print(f"\nCaught expected error: {e}")
        divergence_detected = True
        
    assert divergence_detected, "Agent failed to detect divergence in Infinite Labyrinth!"

def test_goal_labyrinth_convergence():
    """
    The Convergence Test:
    Agent in Goal Labyrinth should NOT trigger alarm (if it makes progress).
    """
    env = LabyrinthEnvironment(mode='goal', goal_distance=10, max_steps=50)
    agent = MockAgentRuntime()
    # Increase window size to smooth out stochastic noise
    agent.lyapunov_monitor.window_size = 20
    
    # Smart agent that follows gradient (simulated by environment probability)
    # We need to ensure the environment actually yields progress for this test to pass
    # In 'goal' mode, 'move' has high success prob if entropy is low.
    # We'll force low entropy to simulate a smart agent.
    
    try:
        state = env.reset()
        env.entropy = 0.1 # Simulate smart agent
        
        for _ in range(20):
            next_state, _, done, _ = env.step('move')
            agent.step(next_state)
            if done: break
            
    except AgentEscalationError:
        pytest.fail("Agent triggered False Positive in Goal Labyrinth!")

if __name__ == "__main__":
    # Manual run
    try:
        test_lyapunov_metric()
        print("Metric Test: PASS")
        test_monitor_divergence()
        print("Monitor Divergence: PASS")
        test_monitor_convergence()
        print("Monitor Convergence: PASS")
        test_infinite_labyrinth_divergence()
        print("Infinite Labyrinth Test: PASS")
        test_goal_labyrinth_convergence()
        print("Goal Labyrinth Test: PASS")
        print("\nALL TESTS PASSED")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
