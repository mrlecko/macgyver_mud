import sys
import os
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from critical_state import CriticalStateMonitor, CriticalState, AgentState
import config

# Mock State Factory
def create_mock_state(entropy=0.2, history=[], steps=100):
    return AgentState(
        entropy=entropy,
        history=history,
        steps=steps,
        dist=10,
        rewards=[],
        error=0.0
    )

def test_nervous_breakdown():
    print("\n[SCENARIO] The Nervous Breakdown (Panic Spiral)")
    monitor = CriticalStateMonitor()
    
    # Step 1: Panic
    print("  Step 1: High Entropy (0.5)")
    s1 = create_mock_state(entropy=0.5)
    monitor.evaluate(s1)
    
    # Step 2: Panic
    print("  Step 2: High Entropy (0.5)")
    s2 = create_mock_state(entropy=0.5)
    monitor.evaluate(s2)
    
    # Step 3: Panic (Should Trigger Escalation)
    print("  Step 3: High Entropy (0.5) -> Expect ESCALATION")
    s3 = create_mock_state(entropy=0.5)
    result = monitor.evaluate(s3)
    print(f"  Result: {result}")
    
    if result == CriticalState.ESCALATION:
        print("  [PASS] Circuit Breaker Tripped.")
        return True
    else:
        print(f"  [FAIL] Expected ESCALATION, got {result}")
        return False

def test_sisyphus_failure():
    print("\n[SCENARIO] The Sisyphus Failure (Persistent Deadlock)")
    monitor = CriticalStateMonitor()
    
    # Loop Pattern
    loop_history = ["A", "B", "A", "B"]
    
    # Step 1: Deadlock
    print("  Step 1: Deadlock Detected")
    s1 = create_mock_state(history=loop_history)
    monitor.evaluate(s1)
    
    # Step 2: Deadlock (Should Trigger Escalation)
    # Note: Config says limit is 2
    print("  Step 2: Deadlock Detected -> Expect ESCALATION")
    s2 = create_mock_state(history=loop_history)
    result = monitor.evaluate(s2)
    print(f"  Result: {result}")
    
    if result == CriticalState.ESCALATION:
        print("  [PASS] Circuit Breaker Tripped.")
        return True
    else:
        print(f"  [FAIL] Expected ESCALATION, got {result}")
        return False

if __name__ == "__main__":
    print("=== ESCALATION RED TEAM VALIDATION ===")
    
    # Ensure config is set correctly for test
    config.CRITICAL_THRESHOLDS["ESCALATION_PANIC_LIMIT"] = 3
    config.CRITICAL_THRESHOLDS["ESCALATION_DEADLOCK_LIMIT"] = 2
    
    results = [
        test_nervous_breakdown(),
        test_sisyphus_failure()
    ]
    
    if all(results):
        print("\n=== ALL SYSTEMS GREEN: ESCALATION VERIFIED ===")
        sys.exit(0)
    else:
        print("\n=== CRITICAL FAILURE: ESCALATION COMPROMISED ===")
        sys.exit(1)
