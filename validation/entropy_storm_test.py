import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from critical_state import CriticalStateMonitor, CriticalState, AgentState

def create_mock_state(entropy=0.0):
    return AgentState(
        entropy=entropy,
        history=[],
        steps=100,
        dist=10,
        rewards=[],
        error=0.0
    )

def run_entropy_storm():
    print("=== ENTROPY STORM TEST ===")
    print("Simulating 100% Entropy (Maximum Confusion)...")
    
    monitor = CriticalStateMonitor()
    
    # We expect: PANIC -> PANIC -> PANIC -> ESCALATION (Circuit Breaker)
    # The monitor checks escalation based on history.
    
    states_sequence = []
    
    for i in range(10):
        state = create_mock_state(entropy=1.0)
        result = monitor.evaluate(state)
        states_sequence.append(result)
        print(f"Step {i+1}: Entropy=1.0 -> State={result.name}")
        
        if result == CriticalState.ESCALATION:
            print(f"\n[SUCCESS] Circuit Breaker Tripped at Step {i+1}")
            break
            
    # Verification
    if CriticalState.PANIC in states_sequence and CriticalState.ESCALATION in states_sequence:
        print("\n[PASS] System correctly transitioned from PANIC to ESCALATION.")
        sys.exit(0)
    else:
        print("\n[FAIL] System did not follow expected PANIC -> ESCALATION sequence.")
        print(f"Sequence: {[s.name for s in states_sequence]}")
        sys.exit(1)

if __name__ == "__main__":
    run_entropy_storm()
