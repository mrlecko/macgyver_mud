# Generalized Credit Assignment ("Blame the Path")

**Feature:** Generalized Credit Assignment
**Module:** `memory/credit_assignment.py`
**Introduced:** November 2025
**Status:** Core Component

---

## 1. Overview

Generalized Credit Assignment is a safety and adaptation mechanism designed to prevent the agent from repeating catastrophic failures (traps). Unlike standard Reinforcement Learning which often struggles with sparse negative rewards or delayed punishment, this system explicitly "blames" the sequence of actions that led to a failure.

**Key Insight:** A trap is rarely the result of a single bad decision at the end; it is the culmination of a path. To avoid the trap, the agent must avoid the *path* that leads to it.

## 2. How It Works

### The "Blame" Logic
When the agent encounters a reward below a critical threshold (e.g., `-5.0`), the system triggers a **Blame Assignment** event.
1.  **Lookback:** It looks back at the last `N` steps (default: 3).
2.  **Signature:** It generates a unique signature for each state-action pair in that window (e.g., `confident_locked→move_to_trap`).
3.  **Persistence:** It adds these signatures to a persistent `failed_paths` set.

### The "Safety Veto"
Before taking any action, the `AgentRuntime` consults the `CreditAssignment` module:
-   **Check:** "Is `current_state→proposed_action` in `failed_paths`?"
-   **Veto:** If yes, the action is assigned a massive penalty (`-999.0`), effectively blocking it unless no other options exist.

## 3. Architecture

### `CreditAssignment` Class
Located in `memory/credit_assignment.py`.

```python
class CreditAssignment:
    def __init__(self, lookback_steps=3, failure_threshold=-5.0):
        self.failed_paths = set()  # Persists across episodes
        self.history = []          # Resets per episode
```

### Integration
Integrated into `AgentRuntime` (`agent_runtime.py`).
-   **Initialization:** Created in `__init__`.
-   **Reset:** `reset()` called at start of `run_episode`.
-   **Recording:** `record_step()` called before `simulate_skill`.
-   **Processing:** `process_outcome()` called after `simulate_skill`.
-   **Selection:** `is_safe()` checked in `select_skill`.

## 4. Configuration

Currently hardcoded in `memory/credit_assignment.py` defaults, but designed to be configurable:
-   `lookback_steps`: Number of steps to blame (Default: 3).
-   `failure_threshold`: Reward value that triggers blame (Default: -5.0).

## 5. Usage Example

The system works automatically. No manual intervention is needed.
To inspect what the agent has learned to avoid:

```python
# Access the set of failed paths
failed = agent.credit_assignment.get_failed_paths()
print(failed)
# Output: {'confident_locked→kick_door', 'uncertain→jump_window'}
```

## 6. Benefits

1.  **One-Shot Safety:** Learns to avoid a trap after hitting it once.
2.  **Temporal Extension:** Blames the *cause* (early step), not just the *effect* (final step).
3.  **Domain Agnostic:** Works in any domain where states and actions can be stringified.
