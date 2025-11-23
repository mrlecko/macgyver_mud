# Hubris Protocol Validation: Detailed Test Plan

## Problem Statement

The Hubris protocol currently lacks a dedicated validation scenario that demonstrates it **provably prevents catastrophic failure**. While other critical states have clear test cases:
- PANIC: Turkey Trap (high entropy)
- DEADLOCK: Infinite Hallway (loops)
- SCARCITY: Speed Run (low steps)
- NOVELTY: The Glitch (prediction error)

**HUBRIS has no equivalent adversarial scenario.**

---

## The Hubris Failure Mode: "The Turkey Problem"

### Definition
An agent that has experienced consistent success becomes **overconfident** and:
1. Ignores low-probability risks
2. Assumes the future will resemble the past
3. Fails to verify assumptions that have "always been true"

### Real-World Analogy
A turkey is fed every day for 1000 days. On day 1001 (Thanksgiving), the turkey's confidence in "feeding time = safety" is maximum... right before catastrophic failure.

---

## Test Scenario Design: "The Shifting Maze"

### Scenario Description

**Environment:**
```
Rooms: A → B → C → GOAL
Initial State: Agent starts in Room A

Phase 1 (Steps 1-8): "The Golden Path"
- Path A → B → C → GOAL is open and rewarding
- Each step along this path gives +1.0 reward
- Agent learns: "This path is safe and optimal"

Phase 2 (Step 9+): "The Betrayal"
- At step 9, the environment SHIFTS
- Path A → B → C now leads to TRAP (penalty -10.0)
- A NEW path A → D → GOAL opens (but agent doesn't know this)
- The shift is SILENT (no obvious signal)

Critical Decision Point (Step 9):
- Baseline Agent: Follows learned pattern (A → B), falls into trap
- Hubris-Aware Agent: Detects overconfidence, forces re-exploration, discovers new path
```

### Why This Tests Hubris

**Hubris Trigger Conditions:**
1. High reward streak (8 consecutive +1.0 rewards)
2. Low entropy (agent is confident in path A → B → C)
3. Long success streak (> 5 steps)

**Expected Behavior:**
- **WITHOUT Hubris Protocol:** Agent blindly follows learned path → TRAP
- **WITH Hubris Protocol:** Icarus Protocol triggers → forces skepticism → re-scans environment → finds new path

---

## Implementation Specification

### Environment State Machine

```python
class ShiftingMazeEnv:
    States: ["A", "B", "C", "D", "GOAL", "TRAP"]

    Phase 1 (steps 1-8):
        A → B: +1.0 reward
        B → C: +1.0 reward
        C → GOAL: +10.0 reward (success)

    Phase 2 (steps 9+):
        A → B: +0.5 reward (subtle warning)
        B → C: leads to TRAP (-10.0, episode ends)
        A → D: +1.0 reward (new path)
        D → GOAL: +10.0 reward (success)
```

### Agent Configurations

**Baseline Agent:**
- Standard Active Inference (no critical states)
- Will exploit learned path A → B → C

**Hubris-Aware Agent:**
- Active Inference + Hubris Protocol
- After 6+ high rewards + low entropy:
  - ICARUS PROTOCOL triggers
  - Forces "sanity check" exploration
  - Re-evaluates previously "safe" paths

### Success Metrics

| Agent Type | Expected Outcome | Metric |
|------------|------------------|--------|
| Baseline | Falls into TRAP | Final reward < 0 |
| Hubris-Aware | Discovers new path | Final reward > 0 |

**Validation Criteria:**
1. Baseline agent MUST fail (otherwise scenario is too easy)
2. Hubris agent MUST succeed (otherwise protocol is ineffective)
3. Hubris protocol MUST trigger before the trap (step 8 or 9)

---

## Implementation Steps

### Step 1: Environment Implementation
**File:** `validation/shifting_maze_env.py`

```python
class ShiftingMazeEnv:
    def __init__(self):
        self.state = "A"
        self.step_count = 0
        self.phase_shift_step = 9

    def get_available_actions(self, state):
        # Returns different actions based on phase

    def step(self, action):
        # Returns (next_state, reward, done, info)
```

### Step 2: Test Harness
**File:** `validation/hubris_validation_test.py`

```python
def run_baseline_agent():
    # Should fall into trap

def run_hubris_agent():
    # Should detect overconfidence and explore

def validate_hubris_protocol():
    # Compare outcomes
```

### Step 3: Assertions

```python
assert baseline_reward < 0, "Baseline should fall into trap"
assert hubris_reward > 0, "Hubris agent should find new path"
assert hubris_trigger_step <= 9, "Protocol must trigger before trap"
```

---

## Expected Output

```
=== HUBRIS VALIDATION TEST ===

[BASELINE AGENT]
Step 1: A → B (+1.0) | Reward Streak: 1
Step 2: B → C (+1.0) | Reward Streak: 2
...
Step 8: C → GOAL (+10.0) | Success! Total: +18.0
Step 9: A → B (+0.5) | Reward Streak: 9
Step 10: B → C (TRAP: -10.0) | FAILURE
Final Reward: -10.0

[HUBRIS-AWARE AGENT]
Step 1: A → B (+1.0) | Reward Streak: 1
...
Step 8: C → GOAL (+10.0) | Success! Total: +18.0
Step 9: A → ? | HUBRIS DETECTED | Icarus Protocol: Forced Exploration
Step 9: A → D (+1.0) | New path discovered!
Step 10: D → GOAL (+10.0) | Success!
Final Reward: +29.0

VERDICT: Hubris Protocol PREVENTED catastrophic failure (-10.0 → +29.0)
```

---

## Validation Checklist

- [ ] Environment implemented with phase shift at step 9
- [ ] Baseline agent consistently falls into trap (10/10 runs)
- [ ] Hubris agent consistently avoids trap (10/10 runs)
- [ ] Hubris trigger logged with timestamp
- [ ] Test integrated into `make test-full`
- [ ] Documentation updated with results

---

## Success Definition

This test will be considered **PASSED** if:

1. **Baseline Failure Rate:** 100% (proves the trap is real)
2. **Hubris Success Rate:** ≥ 80% (proves the protocol works)
3. **Hubris Trigger:** Occurs at step 8 or 9 (before the trap)
4. **Reward Delta:** Hubris agent scores ≥ 20 points higher than baseline

If these criteria are met, we can claim: **"The Hubris protocol demonstrably prevents catastrophic failure in environments with silent regime shifts."**
