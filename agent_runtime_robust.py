"""
Heuristic Agent Runtime (Robust scenario opt-in)

Wraps the original AgentRuntime but adds support for extended skills/observations
when ENABLE_ROBUST_SCENARIO is true. Preserves original behavior otherwise.
"""

from agent_runtime import AgentRuntime as BaseAgentRuntime
import config


class AgentRuntimeRobust(BaseAgentRuntime):
    """Heuristic runtime with optional robust-scenario skills."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track robust scenario state without changing the original runtime fields
        self._robust_state = {"key_found": False, "alarm_disabled": False}

    def run_episode(self, max_steps: int = None):  # type: ignore[override]
        # Reset robust state each episode so we don't leak across runs
        self._robust_state = {"key_found": False, "alarm_disabled": False}
        return super().run_episode(max_steps=max_steps)

    def select_skill(self, skills, *args, **kwargs):  # type: ignore[override]
        if config.ENABLE_ROBUST_SCENARIO and not self._robust_state["key_found"]:
            for skill in skills:
                if skill.get("name") == "search_key":
                    return skill
        return super().select_skill(skills, *args, **kwargs)

    def simulate_skill(self, skill, *args, **kwargs):  # type: ignore[override]
        if not config.ENABLE_ROBUST_SCENARIO:
            return super().simulate_skill(skill)

        name = skill["name"]
        # Map robust skills to existing behaviors or simple heuristics
        if name == "search_key":
            # Deterministic success to keep tests stable; bumps belief toward unlocked
            if not self._robust_state["key_found"]:
                self._robust_state["key_found"] = True
                self.p_unlocked = min(self.p_unlocked + 0.25, 0.95)
                return "obs_key_found", self.p_unlocked, False
            return "obs_search_failed", self.p_unlocked, False
        if name == "disable_alarm":
            self._robust_state["alarm_disabled"] = True
            return "obs_alarm_disabled", self.p_unlocked, False
        if name == "jam_door":
            # Small random perturbation of belief
            self.p_unlocked = min(max(self.p_unlocked + 0.1, 0.0), 1.0)
            return "obs_door_locked", self.p_unlocked, False
        if name == "try_door" and self._robust_state.get("key_found"):
            # Key found: treat as unlocked even if original ground truth was locked
            self.escaped = True
            self.p_unlocked = 0.99
            return "obs_door_opened", self.p_unlocked, True
        if name == "try_door_stealth":
            if self._robust_state.get("key_found"):
                self.escaped = True
                self.p_unlocked = 0.99
                return "obs_door_opened", self.p_unlocked, True
            return super().simulate_skill({"name": "try_door"})

        # Fallback to base behavior for known skills
        return super().simulate_skill(skill)
