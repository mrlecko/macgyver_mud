"""
Auto-Tuning Module

This module implements online statistical tracking for self-calibrating thresholds.
It uses Welford's Online Algorithm to compute mean and variance in a single pass,
allowing the agent to learn "what is normal" for any metric (Entropy, Stress, etc.)
and detect anomalies based on statistical deviation (Z-score) rather than hardcoded values.
"""

import math
from typing import Dict, Optional

class AutoTuner:
    """
    Tracks statistics (mean, variance) for multiple metrics using Welford's Online Algorithm.
    Supports exponential decay to adapt to non-stationary environments (drift).
    """
    
    def __init__(self, decay: float = 0.995, min_samples: int = 20):
        """
        Initialize the AutoTuner.
        
        Args:
            decay: Exponential decay factor (0 < decay <= 1). 
                   1.0 = Infinite memory (standard average).
                   < 1.0 = Moving average (adapts to drift).
                   0.995 implies a "memory" of roughly 200 steps.
            min_samples: Minimum samples required before reporting anomalies.
        """
        self.decay = decay
        self.min_samples = min_samples
        
        # Structure: {metric_name: {'mean': float, 'm2': float, 'count': int}}
        # m2 is the sum of squares of differences from the current mean
        self.stats: Dict[str, Dict] = {}
        
    def update(self, metric_name: str, value: float):
        """
        Update statistics for a given metric with a new value.
        Uses Welford's algorithm for numerical stability.
        """
        if metric_name not in self.stats:
            self.stats[metric_name] = {'mean': 0.0, 'm2': 0.0, 'count': 0}
            
        stat = self.stats[metric_name]
        
        # Standard Welford's Algorithm
        stat['count'] += 1
        delta = value - stat['mean']
        stat['mean'] += delta / stat['count']
        delta2 = value - stat['mean']
        stat['m2'] += delta * delta2
        
        # Apply exponential decay to 'count' and 'm2' to handle drift
        # This effectively limits the "window size" of the statistics
        if self.decay < 1.0:
            stat['m2'] *= self.decay
            # We don't decay mean directly, but we decay the weight of past samples
            # by capping the count. This is a heuristic for "windowed Welford".
            # A more rigorous approach is EMA for mean and EMSD for variance,
            # but this hybrid approach works well for "stable then drifting" data.
            effective_window = 1.0 / (1.0 - self.decay)
            if stat['count'] > effective_window:
                stat['count'] = effective_window
                
    def get_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Return current mean and std_dev for a metric."""
        if metric_name not in self.stats:
            return None
            
        stat = self.stats[metric_name]
        if stat['count'] < 2:
            return {'mean': stat['mean'], 'std_dev': 0.0, 'count': stat['count']}
            
        variance = stat['m2'] / (stat['count'] - 1)
        return {
            'mean': stat['mean'],
            'std_dev': math.sqrt(variance),
            'count': stat['count']
        }
        
    def get_z_score(self, metric_name: str, value: float) -> float:
        """
        Calculate how many standard deviations the value is from the mean.
        Returns 0.0 if insufficient data.
        """
        stats = self.get_stats(metric_name)
        if not stats or stats['count'] < self.min_samples or stats['std_dev'] == 0:
            return 0.0
            
        return (value - stats['mean']) / stats['std_dev']
        
    def is_anomaly(self, metric_name: str, value: float, threshold_sigma: float = 3.0) -> bool:
        """
        Check if the value is a statistical anomaly (critical state).
        
        Args:
            metric_name: Name of the metric (e.g., 'entropy')
            value: Current value
            threshold_sigma: Z-score threshold (default 3.0 = 99.7% confidence)
            
        Returns:
            True if anomaly, False otherwise (or if insufficient data).
        """
        z_score = self.get_z_score(metric_name, value)
        return abs(z_score) > threshold_sigma
