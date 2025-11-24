"""
Generalized Credit Assignment Module

This module implements the "blame the path" logic derived from the Shifting Maze benchmark.
It allows the agent to learn from catastrophic failures (traps) by assigning negative credit
to the sequence of actions that led to the failure, not just the final step.

Key Features:
- Persistent memory of failed paths (across episodes)
- Multi-step credit assignment (lookback)
- Safety checking for proposed actions
"""

from typing import List, Set, Tuple, Any, Optional

class CreditAssignment:
    """
    Manages credit assignment for agent actions, specifically focusing on
    identifying and avoiding paths that lead to catastrophic failure.
    """
    
    def __init__(self, lookback_steps: int = 3, failure_threshold: float = -5.0):
        """
        Initialize the credit assignment system.
        
        Args:
            lookback_steps: How many steps back to blame for a failure.
            failure_threshold: Reward value below which a result is considered a "trap".
        """
        self.lookback_steps = lookback_steps
        self.failure_threshold = failure_threshold
        
        # Persistent memory of failed paths
        # Format: "state_repr→action_name"
        self.failed_paths: Set[str] = set()
        
        # Episode-specific history
        # List of (state_repr, action_name) tuples
        self.history: List[Tuple[str, str]] = []
        
    def reset(self):
        """Reset history for a new episode. Failed paths are preserved."""
        self.history = []
        
    def record_step(self, state_repr: str, action_name: str):
        """
        Record a step taken by the agent.
        
        Args:
            state_repr: String representation of the state (e.g., "confident_locked")
            action_name: Name of the action taken
        """
        self.history.append((state_repr, action_name))
        
    def process_outcome(self, reward: float):
        """
        Process the reward from the last action.
        If the reward indicates a catastrophic failure, blame recent steps.
        
        Args:
            reward: The reward received
        """
        if reward <= self.failure_threshold:
            self._assign_blame()
            
    def _assign_blame(self):
        """
        Assign blame to the recent history for a catastrophic failure.
        Adds the blamed state-action pairs to failed_paths.
        """
        if not self.history:
            return
            
        # Determine how far back to look
        # We blame the last N steps
        steps_to_blame = min(self.lookback_steps, len(self.history))
        
        print(f"      💥 CATASTROPHIC FAILURE! Blaming last {steps_to_blame} steps:")
        
        # Iterate backwards
        for i in range(1, steps_to_blame + 1):
            # Get the step at index -i
            # history is [(s1, a1), (s2, a2), (s3, a3)]
            # i=1 -> (s3, a3)
            # i=2 -> (s2, a2)
            state_repr, action_name = self.history[-i]
            
            path_sig = self._get_path_signature(state_repr, action_name)
            
            if path_sig not in self.failed_paths:
                self.failed_paths.add(path_sig)
                print(f"         Step -{i}: {path_sig} marked as FAILED")
            else:
                print(f"         Step -{i}: {path_sig} already known as FAILED")

    def is_safe(self, state_repr: str, action_name: str) -> bool:
        """
        Check if an action is safe to take from the given state.
        
        Args:
            state_repr: String representation of the state
            action_name: Name of the action
            
        Returns:
            True if the action is safe (not in failed_paths), False otherwise.
        """
        path_sig = self._get_path_signature(state_repr, action_name)
        return path_sig not in self.failed_paths
        
    def _get_path_signature(self, state_repr: str, action_name: str) -> str:
        """Create a unique signature for a state-action pair."""
        return f"{state_repr}→{action_name}"
        
    def get_failed_paths(self) -> Set[str]:
        """Return the set of known failed paths."""
        return self.failed_paths
