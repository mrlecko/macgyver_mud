# Heraclitus Flux: Non-Stationarity Detector for AI

> **Ancient Wisdom:** "You cannot step in the same river twice"  
> **Modern Application:** Detect when environment dynamics have changed  
> **Status:** Medium-value drift detection framework

---

## I. Historical Foundation

**Origin:** Heraclitus of Ephesus (~500 BCE)

**Core Teaching:** Panta rhei - "Everything flows." The world is in constant flux. What appears stable is actually changing.

**The River:** The river looks the same, but the water is constantly new.

---

## II. AI Application

**Problem:** Environment appears stationary, but underlying dynamics have shifted.

```python
class HeraclitusFluxDetector:
    """Detect non-stationarity via prediction error tracking."""
    
    def __init__(self, window=100):
        self.prediction_errors = []
        self.window = window
    
    def detect_flux(self, error):
        """Detect if environment has changed."""
        self.prediction_errors.append(error)
        
        if len(self.prediction_errors) < self.window:
            return False
        
        # Compare recent vs. historical error
        recent = np.mean(self.prediction_errors[-self.window//2:])
        historical = np.mean(self.prediction_errors[:-self.window//2])
        
        # If recent error >> historical, "river has changed"
        return recent > historical * 1.5
    
    def flux_magnitude(self):
        """How much has the environment changed?"""
        if len(self.prediction_errors) < self.window:
            return 0.0
        
        recent = np.mean(self.prediction_errors[-self.window//2:])
        historical = np.mean(self.prediction_errors[:-self.window//2])
        
        return (recent - historical) / (historical + 1e-10)
```

---

## III. Implementation

```python
class AgentRuntime:
    def __init__(self):
        self.flux_detector = HeraclitusFluxDetector(window=100)
        # ... existing init ...
    
    def update(self, state, action, reward, next_state):
        # Calculate prediction error
        predicted_reward = self.model.predict(state, action)
        error = abs(predicted_reward - reward)
        
        # Check for flux
        if self.flux_detector.detect_flux(error):
            self.logger.warning("FLUX DETECTED: Environment has changed!")
            self.relearn_model()  # Reset or adapt model
```

---

## IV. Tests

```python
def test_flux_detection():
    """Inject non-stationarity and verify detection."""
    detector = HeraclitusFluxDetector(window=100)
    
    # Stable period
    for _ in range(50):
        detector.detect_flux(error=0.1)
    
    assert not detector.detect_flux(0.1)
    
    # Inject change
    for _ in range(50):
        detector.detect_flux(error=0.5)  # Error jumps
    
    assert detector.detect_flux(0.5)  # Should detect flux
```

---

## V. Philosophy Connection

**Principle 13 (Surprise):** Prediction error signals the world has changed.

---

## VI. Success Metrics

- Detection Latency: Steps to detect flux after change
- False Positive Rate: Flux detections in stationary environment

**Estimated Effort:** 1-2 days  
**Priority:** Medium
