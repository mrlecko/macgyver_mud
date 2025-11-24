import unittest
from memory.credit_assignment import CreditAssignment

class TestCreditAssignment(unittest.TestCase):
    def setUp(self):
        self.ca = CreditAssignment(lookback_steps=3, failure_threshold=-5.0)
        
    def test_history_tracking(self):
        """Verify steps are recorded correctly."""
        self.ca.record_step("state_A", "action_1")
        self.ca.record_step("state_B", "action_2")
        
        self.assertEqual(len(self.ca.history), 2)
        self.assertEqual(self.ca.history[0], ("state_A", "action_1"))
        self.assertEqual(self.ca.history[1], ("state_B", "action_2"))
        
    def test_reset(self):
        """Verify reset clears history but keeps failed paths."""
        self.ca.record_step("state_A", "action_1")
        self.ca.failed_paths.add("some_failure")
        
        self.ca.reset()
        
        self.assertEqual(len(self.ca.history), 0)
        self.assertIn("some_failure", self.ca.failed_paths)
        
    def test_blame_assignment(self):
        """Verify blame is assigned to recent steps upon failure."""
        # Scenario: A -> B -> C -> TRAP
        self.ca.record_step("state_A", "move_to_B") # Step -3
        self.ca.record_step("state_B", "move_to_C") # Step -2
        self.ca.record_step("state_C", "move_to_TRAP") # Step -1
        
        # Trigger failure
        self.ca.process_outcome(-10.0)
        
        # Check failed paths
        failed = self.ca.get_failed_paths()
        
        # Should blame all 3 steps (lookback=3)
        self.assertIn("state_A→move_to_B", failed)
        self.assertIn("state_B→move_to_C", failed)
        self.assertIn("state_C→move_to_TRAP", failed)
        
    def test_blame_assignment_short_history(self):
        """Verify blame works with history shorter than lookback."""
        self.ca.record_step("state_C", "move_to_TRAP")
        
        self.ca.process_outcome(-10.0)
        
        failed = self.ca.get_failed_paths()
        self.assertIn("state_C→move_to_TRAP", failed)
        self.assertEqual(len(failed), 1)
        
    def test_is_safe(self):
        """Verify safety check works."""
        self.ca.failed_paths.add("state_A→bad_action")
        
        self.assertFalse(self.ca.is_safe("state_A", "bad_action"))
        self.assertTrue(self.ca.is_safe("state_A", "good_action"))
        self.assertTrue(self.ca.is_safe("state_B", "bad_action"))

if __name__ == '__main__':
    unittest.main()
