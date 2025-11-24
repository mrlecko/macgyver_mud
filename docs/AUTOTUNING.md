# Auto-Tuning ("The Self-Calibrating Agent")

**Feature:** Auto-Tuning
**Module:** `control/autotuner.py`
**Introduced:** November 2025
**Status:** Core Component

---

## 1. Overview

Auto-Tuning allows the agent to learn "what is normal" for its internal metrics (Entropy, Stress, Prediction Error) and detect anomalies based on statistical deviation rather than hardcoded thresholds.

**Problem:** A hard threshold like `entropy > 2.0` might be too sensitive in a chaotic environment (false positives) or too dull in a stable one (false negatives).
**Solution:** Define "Panic" as `entropy > mean + 3 * std_dev`.

## 2. How It Works

### Online Statistics (Welford's Algorithm)
We use **Welford's Online Algorithm** to track the mean and variance of streaming data in a single pass (O(1) complexity). This avoids storing the entire history of values.

### Drift Handling (Exponential Decay)
The world changes. What was normal yesterday might be anomalous today.
We use an **Exponential Decay** factor (default `0.995`) to weight recent samples more heavily. This allows the "normal" baseline to shift over time, adapting to non-stationary environments.

### Anomaly Detection (Z-Score)
The `CriticalStateMonitor` queries the `AutoTuner`:
1.  **Update:** `tuner.update("entropy", current_entropy)`
2.  **Check:** `tuner.is_anomaly("entropy", current_entropy, sigma=3.0)`
3.  **Trigger:** If `True`, trigger `PANIC` protocol.

## 3. Architecture

### `AutoTuner` Class
Located in `control/autotuner.py`.

```python
class AutoTuner:
    def __init__(self, decay=0.995, min_samples=20):
        self.stats = {} 
        
    def update(self, metric, value): ...
    def is_anomaly(self, metric, value, sigma=3.0): ...
```

### Integration
Integrated into `CriticalStateMonitor` (`critical_state.py`).
It acts as a **Dynamic Trigger** that works in parallel with **Static Safety Bounds**.
-   **Dynamic:** "This entropy is unusually high *for this context*."
-   **Static:** "This entropy is objectively dangerous (> 5.0)."

## 4. Benefits

1.  **Zero-Shot Calibration:** The agent calibrates itself to the environment's natural noise level.
2.  **Robustness:** Reduces false positives in noisy domains.
3.  **Adaptability:** Handles domain shifts (e.g., moving from a simple maze to a complex one) without manual retuning.

## 5. Usage

The system works automatically.
To inspect the learned statistics:

```python
stats = agent.monitor.tuner.get_stats("entropy")
print(f"Mean Entropy: {stats['mean']:.2f}, Std Dev: {stats['std_dev']:.2f}")
```
