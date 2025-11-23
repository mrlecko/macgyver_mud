# Schelling Points: Coordination Without Communication

> **Ancient Wisdom:** Thomas Schelling (1960)  
> **Modern Application:** Enable agent coordination via focal points  
> **Status:** HIGH-value coordination framework

---

## I. Foundation

**Origin:** Thomas Schelling, "The Strategy of Conflict" (1960)

**Core Idea:** When agents need to coordinate without communication, they converge on "obvious" solutions (Schelling Points).

**Example:** "Meet in New York" → Most people go to Grand Central (focal point).

---

## II. AI Application

```python
class SchellingCoordinator:
    """Identify and exploit focal points for coordination."""
    
    def __init__(self, salience_fn):
        self.salience = salience_fn  # How "obvious" is an option?
    
    def coordinate(self, options):
        """Pick most salient (obvious) option."""
        return max(options, key=self.salience)

# Example salience function
def salience(location):
    """How "obvious" is this location as a meeting point?"""
    if location == "Train Station":
        return 10  # Very obvious
    elif location == "City Hall":
        return 7  # Somewhat obvious
    elif location == "Random street corner":
        return 1  # Not obvious
    return 0
```

---

## III. Implementation

```python
class MultiAgentCoordination:
    """Use Schelling Points for distributed coordination."""
    
    def __init__(self):
        self.schelling = SchellingCoordinator(salience_fn=self.compute_salience)
    
    def compute_salience(self, option):
        """Calculate salience based on:
        - Symmetry (is this option special/central?)
        - Simplicity (is this option easy to describe?)
        - Convention (is there a cultural default?)
        """
        score = 0
        if self.is_symmetric(option):
            score += 5
        if self.is_simple(option):
            score += 3
        if self.is_conventional(option):
            score += 2
        return score
    
    def coordinate_without_communication(self, agents, options):
        """All agents pick same Schelling Point."""
        focal_point = self.schelling.coordinate(options)
        for agent in agents:
            agent.choose(focal_point)
```

---

## IV. Tests

```python
def test_schelling_convergence():
    """Verify agents converge on Schelling Point."""
    options = ["Train Station", "Park", "Street Corner"]
    
    agent1 = SchellingAgent(salience_fn)
    agent2 = SchellingAgent(salience_fn)
    
    choice1 = agent1.coordinate(options)
    choice2 = agent2.coordinate(options)
    
    # Both should pick "Train Station" (highest salience)
    assert choice1 == choice2 == "Train Station"
```

---

## V. Philosophy Connection

**Principle 24 (Trust):** Schelling Points enable coordination without trust or communication.

---

## VI. Success Metrics

- Coordination Rate: % of times agents successfully coordinate
- Time to Converge: Steps until all agents choose same option

**Estimated Effort:** 3 days  
**Priority:** HIGH (critical for multi-agent systems)
