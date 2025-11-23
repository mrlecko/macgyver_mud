# Phase Space & Attractors: Trajectory Visualization

> **Ancient Wisdom:** Henri Poincaré (1890s), Dynamical Systems Theory  
> **Modern Application:** Visualize agent trajectories to find stable states  
> **Status:** Medium-value visualization framework

---

## I. Foundation

**Origin:** Henri Poincaré (1890s)

**Core Idea:** Plot system state over time in "phase space." Attractors are regions the system tends toward.

---

## II. AI Application

```python
import matplotlib.pyplot as plt

def plot_phase_space(state_history, dims=(0, 1)):
    """Plot 2D phase portrait."""
    x = [s[dims[0]] for s in state_history]
    y = [s[dims[1]] for s in state_history]
    
    plt.plot(x, y, 'b-', alpha=0.5)
    plt.scatter(x[0], y[0], c='g', label='Start')
    plt.scatter(x[-1], y[-1], c='r', label='End')
    plt.xlabel(f'Dimension {dims[0]}')
    plt.ylabel(f'Dimension {dims[1]}')
    plt.legend()
    plt.savefig('phase_space.png')

def find_attractor(trajectory, tolerance=0.1):
    """Find if trajectory converges to an attractor."""
    # Check if final states are clustered
    final_states = trajectory[-20:]
    centroid = np.mean(final_states, axis=0)
    
    distances = [np.linalg.norm(s - centroid) for s in final_states]
    
    if np.mean(distances) < tolerance:
        return centroid  # Converged to attractor
    return None
```

---

## III. Philosophy Connection

**Principle 8 (Loops):** Attractors reveal where agent "wants" to be.

**Estimated Effort:** 2 days  
**Priority:** Medium
