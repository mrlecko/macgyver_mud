import numpy as np
from collections import deque

class LyapunovMetric:
    """
    Calculates the Lyapunov Function V(s) for the agent's state.
    V(s) represents the 'potential energy' or 'distance from stability'.
    
    V(s) = w_E * Entropy + w_D * Distance + w_S * Stress
    """
    def __init__(self, w_entropy=1.0, w_distance=1.0, w_stress=1.0):
        self.w_entropy = w_entropy
        self.w_distance = w_distance
        self.w_stress = w_stress
    
    def calculate_v(self, entropy, distance_estimate, stress):
        """
        Calculate scalar V(s).
        
        Args:
            entropy (float): 0.0 to 1.0 (Cognitive Entropy)
            distance_estimate (float): Estimated steps to goal (0 to inf)
            stress (float): 0.0 to 1.0 (Resource Stress / Fatigue)
            
        Returns:
            float: Lyapunov value V(s)
        """
        # Ensure inputs are non-negative
        entropy = max(0.0, entropy)
        distance = max(0.0, distance_estimate)
        stress = max(0.0, stress)
        
        v = (self.w_entropy * entropy + 
             self.w_distance * distance + 
             self.w_stress * stress)
        return v

class StabilityMonitor:
    """
    Monitors the stability of the agent by tracking V(s) over time.
    Checks if the system is converging (dV/dt < 0) or diverging (dV/dt >= 0).
    """
    def __init__(self, metric=None, window_size=20, divergence_threshold=0.05):
        self.metric = metric if metric else LyapunovMetric()
        self.history = deque(maxlen=window_size)
        self.window_size = window_size
        self.divergence_threshold = divergence_threshold # Positive slope allowed before flagging
        
    def update(self, entropy, distance_estimate, stress):
        """
        Update monitor with new state metrics.
        Returns current V(s).
        """
        v = self.metric.calculate_v(entropy, distance_estimate, stress)
        self.history.append(v)
        return v
    
    def get_trend(self):
        """
        Calculate the linear trend (slope) of V(s) over the current window.
        Returns:
            float: Slope of V(s). Negative = Stable, Positive = Unstable.
        """
        if len(self.history) < 5:
            return 0.0 # Not enough data
            
        # Linear regression to find slope
        y = np.array(self.history)
        x = np.arange(len(y))
        
        # Slope = Cov(x, y) / Var(x)
        slope = np.polyfit(x, y, 1)[0]
        return slope
        
    def is_diverging(self):
        """
        Check if the system is diverging (unstable).
        Returns True if trend is significantly positive.
        """
        if len(self.history) < self.window_size:
            return False
            
        trend = self.get_trend()
        return trend > self.divergence_threshold

    def is_converging(self):
        """
        Check if the system is converging (stable).
        Returns True if trend is negative.
        """
        if len(self.history) < self.window_size:
            return False
            
        trend = self.get_trend()
        return trend < -self.divergence_threshold
