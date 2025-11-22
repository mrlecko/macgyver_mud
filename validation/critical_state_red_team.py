import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from critical_state import CriticalStateMonitor, CriticalState, AgentState

def create_mock_state():
    return AgentState(
        entropy=0.2,
        history=[],
        steps=100,
        dist=10,
        rewards=[],
        error=0.0
    )

def test_turkey_trap():
    print("\n[SCENARIO] The Turkey Trap (Hubris Test)")
    monitor = CriticalStateMonitor()
    state = create_mock_state()
    
    # Simulate success streak
    state.entropy = 0.05
    state.reward_history = [1.0] * 10
    print(f"  Context: Reward Streak={len(state.reward_history)}, Entropy={state.entropy}")
    
    result = monitor.evaluate(state)
    print(f"  Result: {result}")
    
    if result == CriticalState.HUBRIS:
        print("  [PASS] Hubris Detected. Icarus Protocol Activated.")
        return True
    else:
        print(f"  [FAIL] Expected HUBRIS, got {result}")
        return False

def test_infinite_hallway():
    print("\n[SCENARIO] The Infinite Hallway (Deadlock Test)")
    monitor = CriticalStateMonitor()
    state = create_mock_state()
    
    # Simulate loop
    state.location_history = ["Room A", "Room B", "Room A", "Room B"]
    print(f"  Context: History={state.location_history}")
    
    result = monitor.evaluate(state)
    print(f"  Result: {result}")
    
    if result == CriticalState.DEADLOCK:
        print("  [PASS] Deadlock Detected. Sisyphus Protocol Activated.")
        return True
    else:
        print(f"  [FAIL] Expected DEADLOCK, got {result}")
        return False

def test_the_glitch():
    print("\n[SCENARIO] The Glitch (Novelty Test)")
    monitor = CriticalStateMonitor()
    state = create_mock_state()
    
    # Simulate surprise
    state.prediction_error = 0.95
    print(f"  Context: Prediction Error={state.prediction_error}")
    
    result = monitor.evaluate(state)
    print(f"  Result: {result}")
    
    if result == CriticalState.NOVELTY:
        print("  [PASS] Novelty Detected. Eureka Protocol Activated.")
        return True
    else:
        print(f"  [FAIL] Expected NOVELTY, got {result}")
        return False

def test_speed_run():
    print("\n[SCENARIO] The Speed Run (Scarcity Test)")
    monitor = CriticalStateMonitor()
    state = create_mock_state()
    
    # Simulate scarcity
    state.distance_to_goal = 10
    state.steps_remaining = 11
    print(f"  Context: Steps={state.steps_remaining}, Dist={state.distance_to_goal}")
    
    result = monitor.evaluate(state)
    print(f"  Result: {result}")
    
    if result == CriticalState.SCARCITY:
        print("  [PASS] Scarcity Detected. Spartan Protocol Activated.")
        return True
    else:
        print(f"  [FAIL] Expected SCARCITY, got {result}")
        return False

if __name__ == "__main__":
    print("=== CRITICAL STATE RED TEAM VALIDATION ===")
    results = [
        test_turkey_trap(),
        test_infinite_hallway(),
        test_the_glitch(),
        test_speed_run()
    ]
    
    if all(results):
        print("\n=== ALL SYSTEMS GREEN: CRITICAL PROTOCOLS VERIFIED ===")
        sys.exit(0)
    else:
        print("\n=== CRITICAL FAILURE: PROTOCOLS COMPROMISED ===")
        sys.exit(1)
