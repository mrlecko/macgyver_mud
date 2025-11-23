# Minimax Regret: Decision Criterion Under Uncertainty

> **Ancient Wisdom:** Savage's Criterion (1951)  
> **Modern Application:** Robust decision-making when probabilities unknown  
> **Status:** Medium-value decision framework

---

## I. Foundation

**Origin:** Leonard Savage (1951)

**Core Idea:** When you don't know the probabilities, minimize your maximum regret.

**Regret:** Best possible outcome - Actual outcome

---

## II. AI Application

```python
def minimax_regret(actions, possible_worlds):
    """Choose action that minimizes worst-case regret."""
    regrets = {}
    
    for action in actions:
        max_regret = 0
        for world in possible_worlds:
            outcome = simulate(action, world)
            best_possible = max(simulate(a, world) for a in actions)
            regret = best_possible - outcome
            max_regret = max(max_regret, regret)
        
        regrets[action] = max_regret
    
    # Pick action with minimum max regret
    return min(regrets, key=regrets.get)
```

---

## III. Implementation

```python
class ConfusedAgent:
    """Use minimax regret when confused (high entropy)."""
    
    def select_skill(self, skills, entropy):
        if entropy > CONFUSION_THRESHOLD:
            # Don't know probabilities - use minimax regret
            return self.minimax_regret_decision(skills)
        else:
            # Know probabilities - use expected value
            return self.max_expected_value(skills)
```

---

## IV. Philosophy Connection

**Principle 12 (Confusion):** When confused, minimize regret, not expected value.

---

## V. Success Metrics

- Regret Reduction: Actual regret vs. baseline
- Robustness: Performance in worst-case scenarios

**Estimated Effort:** 2 days  
**Priority:** Medium
