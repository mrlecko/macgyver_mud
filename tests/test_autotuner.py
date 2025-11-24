import unittest
import math
import random
from control.autotuner import AutoTuner

class TestAutoTuner(unittest.TestCase):
    def setUp(self):
        # Use decay=1.0 for stationary tests (standard average)
        self.tuner = AutoTuner(decay=1.0, min_samples=10)
        
    def test_welford_accuracy(self):
        """Verify Welford's algorithm matches standard mean/std calculation."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for x in data:
            self.tuner.update("test", x)
            
        stats = self.tuner.get_stats("test")
        
        # Expected: Mean=3.0, Std=1.5811
        self.assertAlmostEqual(stats['mean'], 3.0)
        self.assertAlmostEqual(stats['std_dev'], 1.58113883, places=5)
        self.assertEqual(stats['count'], 5)
        
    def test_anomaly_detection(self):
        """Verify anomaly detection works with Z-scores."""
        # Feed normal data (Mean=0, Std=1)
        for _ in range(50):
            self.tuner.update("metric", random.gauss(0, 1))
            
        # Check normal value (0.0) - Should NOT be anomaly
        self.assertFalse(self.tuner.is_anomaly("metric", 0.0))
        
        # Check extreme value (5.0) - Should be anomaly (5 sigma)
        self.assertTrue(self.tuner.is_anomaly("metric", 5.0))
        
    def test_cold_start(self):
        """Verify no anomalies reported during warm-up."""
        tuner = AutoTuner(min_samples=20)
        
        # Feed 5 samples (insufficient)
        for _ in range(5):
            tuner.update("metric", 100.0) # Extreme value
            
        # Should return False because count < min_samples
        self.assertFalse(tuner.is_anomaly("metric", 100.0))
        
    def test_drift_handling(self):
        """Verify tuner adapts to shifting mean using decay."""
        # Use fast decay for test
        tuner = AutoTuner(decay=0.9, min_samples=5)
        
        # Phase 1: Mean = 0
        for _ in range(50):
            tuner.update("metric", 0.0)
            
        stats1 = tuner.get_stats("metric")
        self.assertAlmostEqual(stats1['mean'], 0.0, delta=0.1)
        
        # Phase 2: Mean shifts to 10
        for _ in range(50):
            tuner.update("metric", 10.0)
            
        stats2 = tuner.get_stats("metric")
        print(f"Stats after drift: {stats2}")
        z_score = tuner.get_z_score("metric", 0.0)
        print(f"Z-score for 0.0: {z_score}")
        
        # Mean should have shifted close to 10
        self.assertAlmostEqual(stats2['mean'], 10.0, delta=0.5)
        
        # 10.0 should now be normal, 0.0 should be anomaly
        self.assertFalse(tuner.is_anomaly("metric", 10.0))
        self.assertTrue(tuner.is_anomaly("metric", 0.0))

if __name__ == '__main__':
    unittest.main()
