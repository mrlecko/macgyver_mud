"""
LLM-Based Planner for TextWorld Agent

Uses the llm CLI (https://llm.datasette.io/) for structured planning output.
Replaces the mock planner with real LLM-based task decomposition.
"""
from typing import List, Dict, Optional
import json
import subprocess
import os
from pathlib import Path

# Import Plan data structures (to be created next)
from .plan import Plan, PlanStep, PlanStatus


class LLMPlanner:
    """
    Generates hierarchical plans using LLM reasoning via llm CLI.

    Uses:
    - JSON schema validation (--schema)
    - System fragments for consistent prompting (--sf)
    - Structured output guaranteed by schema enforcement
    """

    def __init__(self, model: str = None, verbose: bool = False):
        """
        Initialize LLM planner.

        Args:
            model: LLM model to use (e.g., 'gpt-4o-mini', 'claude-3-5-sonnet-20241022')
                   If None, uses LLM_MODEL env var or llm default
            verbose: Print debug info
        """
        self.model = model or os.getenv('LLM_MODEL')
        self.verbose = verbose

        # Paths relative to project root
        self.project_root = Path(__file__).parent.parent.parent
        self.schema_path = self.project_root / "schemas" / "textworld_plan.schema.json"
        self.fragment_path = self.project_root / "fragments" / "textworld_planner.md"

        # Validate paths exist
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {self.schema_path}")
        if not self.fragment_path.exists():
            raise FileNotFoundError(f"Fragment not found: {self.fragment_path}")

        if self.verbose:
            print(f"📋 LLM Planner initialized")
            print(f"   Model: {self.model or 'default'}")
            print(f"   Schema: {self.schema_path.name}")
            print(f"   Fragment: {self.fragment_path.name}")

    def generate_plan(self, goal: str, context: str,
                      previous_failures: Optional[List[str]] = None) -> Plan:
        """
        Generate a hierarchical plan for achieving the goal.

        Args:
            goal: High-level objective (e.g., "Find and unlock the chest")
            context: Current world state (observations, beliefs, available actions)
            previous_failures: List of failed attempts to learn from

        Returns:
            Plan object with strategy, steps, and contingencies
        """
        # Build prompt
        prompt = self._build_prompt(goal, context, previous_failures)

        try:
            # Call llm CLI with schema validation
            plan_json = self._call_llm(prompt)

            # Parse and validate
            plan = self._parse_plan_json(plan_json, goal)

            if self.verbose:
                print(f"✅ Plan generated: {len(plan.steps)} steps")
                print(f"   Strategy: {plan.strategy[:60]}...")
                print(f"   Confidence: {plan.confidence:.2f}")

            return plan

        except Exception as e:
            # Fallback to simple plan on error
            if self.verbose:
                print(f"⚠️  LLM planning failed: {e}")
                print(f"   Using fallback plan")

            return self._fallback_plan(goal)

    def _build_prompt(self, goal: str, context: str,
                     previous_failures: Optional[List[str]] = None) -> str:
        """Build the planning prompt."""
        prompt_parts = [
            f"Goal: {goal}",
            "",
            "Current Context:",
            context,
            ""
        ]

        if previous_failures:
            prompt_parts.extend([
                "Previous Failed Attempts:",
                *[f"- {failure}" for failure in previous_failures],
                "",
                "Learn from these failures and adjust the plan.",
                ""
            ])

        prompt_parts.append(
            "Generate a plan as a JSON object. "
            "Return ONLY the JSON, no markdown fences, no explanation."
        )

        return "\n".join(prompt_parts)

    def _call_llm(self, prompt: str) -> Dict:
        """
        Call llm CLI with schema validation.

        Returns:
            Parsed JSON dict
        """
        # Build llm command
        cmd = [
            "llm",
            "--sf", str(self.fragment_path),  # System fragment
            "--schema", str(self.schema_path),  # JSON schema validation
        ]

        if self.model:
            cmd.extend(["-m", self.model])

        # Add prompt as final argument
        cmd.append(prompt)

        if self.verbose:
            print(f"🔧 Running: llm --sf ... --schema ... '{prompt[:50]}...'")

        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                check=True
            )

            # Parse JSON output
            output = result.stdout.strip()

            if self.verbose:
                print(f"📥 LLM output ({len(output)} chars)")

            return json.loads(output)

        except subprocess.TimeoutExpired:
            raise Exception("LLM call timed out (30s)")
        except subprocess.CalledProcessError as e:
            raise Exception(f"LLM command failed: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON from LLM: {e}")

    def _parse_plan_json(self, plan_data: Dict, goal: str) -> Plan:
        """Convert LLM JSON output to Plan object."""
        # Extract steps
        steps = [
            PlanStep(
                description=step['description'],
                action_pattern=step['action_pattern']
            )
            for step in plan_data.get('steps', [])
        ]

        # Extract contingencies
        contingencies = plan_data.get('contingencies', {})

        # Create Plan object
        plan = Plan(
            goal=goal,
            strategy=plan_data.get('strategy', ''),
            steps=steps,
            success_criteria=plan_data.get('success_criteria', ''),
            contingencies=contingencies,
            confidence=plan_data.get('confidence', 0.5),
            status=PlanStatus.ACTIVE
        )

        return plan

    def _fallback_plan(self, goal: str) -> Plan:
        """
        Simple fallback plan when LLM fails.

        Returns a basic exploration plan.
        """
        return Plan(
            goal=goal,
            strategy="Explore the environment and gather information to understand how to achieve the goal.",
            steps=[
                PlanStep(
                    description="Look around to see what's available",
                    action_pattern="look"
                ),
                PlanStep(
                    description="Check current inventory",
                    action_pattern="inventory"
                ),
                PlanStep(
                    description="Examine visible objects to learn about them",
                    action_pattern="examine"
                )
            ],
            success_criteria="Gained information about the environment and available objects",
            contingencies={
                "stuck": "Try examining objects in the current room",
                "failed": "Move to a different room and explore there",
                "unexpected": "Look around again to reassess the situation"
            },
            confidence=0.3,  # Low confidence for fallback
            status=PlanStatus.ACTIVE
        )


# Test function for development
if __name__ == "__main__":
    """Quick test of LLM planner."""
    print("=" * 70)
    print("LLM PLANNER TEST")
    print("=" * 70)

    planner = LLMPlanner(verbose=True)

    # Test 1: Simple goal
    print("\n--- Test 1: Simple Goal ---")
    plan = planner.generate_plan(
        goal="Find the key",
        context="""
        Current Room: Dark Basement
        Visible Objects: chest, table, old lamp
        Inventory: empty
        Available Actions: look, examine <object>, take <object>, go <direction>
        """
    )

    print(f"\nGenerated Plan:")
    print(f"  Goal: {plan.goal}")
    print(f"  Strategy: {plan.strategy}")
    print(f"  Steps: {len(plan.steps)}")
    for i, step in enumerate(plan.steps, 1):
        print(f"    {i}. {step.description} (match: '{step.action_pattern}')")
    print(f"  Success Criteria: {plan.success_criteria}")
    print(f"  Confidence: {plan.confidence}")

    # Test 2: With failures
    print("\n--- Test 2: Learning from Failures ---")
    plan2 = planner.generate_plan(
        goal="Open the locked door",
        context="""
        Current Room: Hallway
        Visible Objects: locked door, painting
        Inventory: rusty key
        Available Actions: examine <object>, unlock <object> with <key>, open <object>
        """,
        previous_failures=[
            "Tried 'unlock door with rusty key' - key doesn't fit",
            "Tried 'open door' - it's locked"
        ]
    )

    print(f"\nGenerated Plan (with failure context):")
    print(f"  Strategy: {plan2.strategy}")
    print(f"  Contingencies:")
    for situation, response in plan2.contingencies.items():
        print(f"    {situation}: {response}")
