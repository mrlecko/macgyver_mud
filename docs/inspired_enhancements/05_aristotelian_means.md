# Aristotelian Means: Virtue Detection Between Extremes

> **Ancient Wisdom:** Aristotle - "Virtue is the mean between two vices"  
> **Modern Application:** Balance detector for behavioral parameters  
> **Status:** Medium-value behavioral framework

---

## I. Historical Foundation

**Origin:** Nicomachean Ethics, ~350 BCE

**Core Teaching:** Virtue exists at the mean between deficiency and excess:
- Courage = mean between cowardice (deficiency) and recklessness (excess)
- Generosity = mean between stinginess and wastefulness
- Confidence = mean between humility and arrogance

---

## II. AI Application

**Use Case:** Detect if agent's exploration rate, confidence, or other parameters are "virtuous" (balanced).

```python
class AristotelianMean:
    def virtue_score(self, value, vice_low, vice_high):
        """Score how close value is to virtuous mean."""
        mean = (vice_low + vice_high) / 2
        span = vice_high - vice_low
        distance = abs(value - mean)
        return 1 - (distance / (span / 2))
    
    def is_virtuous(self, value, vice_low, vice_high, tolerance=0.2):
        """Check if value is in virtuous range."""
        score = self.virtue_score(value, vice_low, vice_high)
        return score > (1 - tolerance)

# Example: Exploration rate
explore_rate = 0.3
virtue = AristotelianMean().virtue_score(
    explore_rate,
    vice_low=0.0,  # Cowardice (never explore)
    vice_high=1.0  # Recklessness (always explore)
)
# Returns ~0.4 (somewhat virtuous, leaning toward caution)
```

---

## III. Implementation

```python
class VirtuousBehaviorMonitor:
    def __init__(self):
        self.virtues = {
            'exploration': (0.1, 0.9),  # Too little vs. too much
            'confidence': (0.7, 0.95),  # Humble vs. arrogant
            'risk_taking': (0.2, 0.8),
        }
    
    def check_virtue(self, behavior, value):
        if behavior not in self.virtues:
            return None
        
        low, high = self.virtues[behavior]
        mean = AristotelianMean()
        return mean.virtue_score(value, low, high)
```

---

## IV. Connection to Philosophy

**Principle 16 (Complementarity):** Virtue is not choosing one extreme, but balancing both.

---

## V. Success Metrics

- Virtue Score: % of time agent's parameters are in virtuous range
- Behavioral Stability: Variance in parameters over time

**Estimated Effort:** 1-2 days  
**Priority:** Medium
