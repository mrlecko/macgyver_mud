# Limit Cycles: Oscillation Detector for AI

> **Ancient Wisdom:** Poincaré-Bendixson Theorem  
> **Modern Application:** Detect when agent is oscillating  
> **Status:** Medium-value oscillation detection

---

## I. Foundation

**Origin:** Henri Poincaré (1892)

**Core Idea:** A limit cycle is a closed trajectory in phase space—the system oscillates forever.

---

## II. AI Application

```python
def detect_limit_cycle(trajectory, tolerance=0.1):
    """Detect if trajectory forms a closed loop."""
    for i in range(len(trajectory) // 2):
        for j in range(i + 10, len(trajectory)):
            # Check if state returns to earlier state
            if np.linalg.norm(trajectory[i] - trajectory[j]) < tolerance:
                return True, (i, j)  # Limit cycle detected
    return False, None

class OscillationDetector:
    """Detect oscillating behavior."""
    
    def __init__(self):
        self.state_history = []
    
    def update(self, state):
        self.state_history.append(state)
    
    def is_oscillating(self):
        """Check if agent is in limit cycle."""
        if len(self.state_history) < 20:
            return False
        
        is_cycle, _ = detect_limit_cycle(self.state_history[-50:])
        return is_cycle
```

---

## III. Philosophy Connection

**Principle 8 (Loops):** Limit cycles are geometric loops.

**Estimated Effort:** 1-2 days  
**Priority:** Medium
