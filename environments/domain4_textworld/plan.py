"""
Plan data structures for TextWorld cognitive agent.

Hierarchical planning with step tracking and execution monitoring.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class PlanStatus(Enum):
    """Status of a plan's execution."""
    ACTIVE = "active"          # Currently being executed
    COMPLETED = "completed"    # All steps done successfully
    FAILED = "failed"         # Plan failed, cannot proceed
    SUSPENDED = "suspended"    # Temporarily paused


@dataclass
class PlanStep:
    """
    A single step in a plan.

    Tracks completion status and attempts.
    """
    description: str          # What this step accomplishes
    action_pattern: str       # Keyword to match in actions (e.g., "take key")
    completed: bool = False   # Has this step been completed?
    attempts: int = 0        # How many times we've tried this step
    max_attempts: int = 3    # Give up after this many failures

    def matches_action(self, action: str) -> bool:
        """
        Check if an action completes this step.

        Uses both substring and token-based matching (case-insensitive).
        This allows "take key" to match "take the golden key".

        Args:
            action: The action string to check

        Returns:
            True if action matches this step's pattern
        """
        # Normalize both strings
        pattern_lower = self.action_pattern.lower()
        action_lower = action.lower()

        # Simple substring match
        if pattern_lower in action_lower:
            return True

        # Token-based match: all pattern tokens must be in action
        # This handles "take key" matching "take the golden key"
        pattern_tokens = set(pattern_lower.split())
        action_tokens = set(action_lower.split())

        # Match if all pattern tokens are in action
        return pattern_tokens.issubset(action_tokens)

    def mark_completed(self):
        """Mark this step as successfully completed."""
        self.completed = True

    def increment_attempts(self) -> Optional[str]:
        """
        Increment attempt counter.

        Returns:
            "retry_limit_exceeded" if max attempts reached, None otherwise
        """
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            return "retry_limit_exceeded"
        return None


@dataclass
class Plan:
    """
    A hierarchical plan for achieving a goal.

    Combines strategic reasoning with executable steps.
    """
    goal: str                           # High-level objective
    strategy: str                       # WHY this approach works
    steps: List[PlanStep]              # Sequence of actions
    success_criteria: str               # HOW to know if succeeded
    contingencies: Dict[str, str]       # failure_type -> backup_plan
    confidence: float = 0.5            # Planner's confidence (0.0-1.0)
    status: PlanStatus = PlanStatus.ACTIVE
    created_at_step: int = 0           # When was this plan created
    completed_at_step: Optional[int] = None
    failure_reason: Optional[str] = None

    def get_current_step(self) -> Optional[PlanStep]:
        """
        Get the next incomplete step.

        Returns:
            Next step to execute, or None if plan is complete
        """
        for step in self.steps:
            if not step.completed:
                return step
        return None

    def advance_step(self, action: str) -> bool:
        """
        Mark current step as complete if action matches.

        Args:
            action: The action that was just executed

        Returns:
            True if a step was completed, False otherwise
        """
        current = self.get_current_step()
        if current and current.matches_action(action):
            current.mark_completed()
            return True
        return False

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(step.completed for step in self.steps)

    def progress_ratio(self) -> float:
        """
        Return completion percentage.

        Returns:
            Float in [0.0, 1.0] representing progress
        """
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.completed)
        return completed / len(self.steps)

    def steps_remaining(self) -> int:
        """Return number of incomplete steps."""
        return sum(1 for s in self.steps if not s.completed)

    def get_next_step_description(self) -> str:
        """
        Get description of next step.

        Returns:
            Description string, or "Plan complete" if done
        """
        next_step = self.get_current_step()
        if next_step:
            return next_step.description
        return "Plan complete"

    def to_dict(self) -> Dict:
        """
        Convert to dictionary for serialization.

        Useful for saving to Neo4j or logging.
        """
        return {
            'goal': self.goal,
            'strategy': self.strategy,
            'steps': [
                {
                    'description': s.description,
                    'action_pattern': s.action_pattern,
                    'completed': s.completed,
                    'attempts': s.attempts
                }
                for s in self.steps
            ],
            'success_criteria': self.success_criteria,
            'contingencies': self.contingencies,
            'confidence': self.confidence,
            'status': self.status.value,
            'progress': self.progress_ratio(),
            'steps_remaining': self.steps_remaining()
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        progress = self.progress_ratio()
        return (
            f"Plan(goal='{self.goal}', "
            f"steps={len(self.steps)}, "
            f"progress={progress:.0%}, "
            f"status={self.status.value})"
        )


# Test code
if __name__ == "__main__":
    """Quick test of Plan data structures."""
    print("=" * 70)
    print("PLAN DATA STRUCTURE TEST")
    print("=" * 70)

    # Create a test plan
    plan = Plan(
        goal="Find and unlock the treasure chest",
        strategy="Locate the key first, then use it to unlock the chest",
        steps=[
            PlanStep("Look around the room", "look"),
            PlanStep("Find the key", "take key"),
            PlanStep("Unlock the chest", "unlock chest"),
            PlanStep("Open the chest", "open chest")
        ],
        success_criteria="Chest is open and contents are visible",
        contingencies={
            "stuck": "Examine all objects to find hidden compartments",
            "failed": "Try a different room"
        },
        confidence=0.8
    )

    print(f"\n{plan}")
    print(f"\nStrategy: {plan.strategy}")
    print(f"Steps:")
    for i, step in enumerate(plan.steps, 1):
        status = "✅" if step.completed else "⬜"
        print(f"  {status} {i}. {step.description}")

    # Simulate execution
    print("\n--- Simulating Execution ---")

    actions = [
        "look around",
        "take the golden key",
        "unlock chest with key",
        "open the treasure chest"
    ]

    for action in actions:
        print(f"\nAction: {action}")
        if plan.advance_step(action):
            print(f"  ✅ Step completed!")
            print(f"  Progress: {plan.progress_ratio():.0%}")
            next_step = plan.get_current_step()
            if next_step:
                print(f"  Next: {next_step.description}")
            else:
                print(f"  🎉 Plan complete!")
        else:
            print(f"  ⬜ No step matched")

    print(f"\n--- Final Status ---")
    print(f"Complete: {plan.is_complete()}")
    print(f"Progress: {plan.progress_ratio():.0%}")
    print(f"\nSerialized:")
    import json
    print(json.dumps(plan.to_dict(), indent=2))
