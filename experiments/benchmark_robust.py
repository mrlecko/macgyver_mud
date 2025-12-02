"""
Benchmark helper for comparing heuristic vs Active Inference runtimes
on the robust room-escape scenario. Intended for quick opt-in runs
without affecting the default (toy) setup.
"""
from __future__ import annotations

import importlib
import os
from typing import Dict, Any

import numpy as np

import config
from agent_runtime_active import ActiveInferenceRuntime
from agent_runtime_robust import AgentRuntimeRobust
from scripts.apply_robust_seed import apply_robust_seed_to_session


def _toggle_robust_flag(enable: bool):
    """Enable/disable robust scenario flag on the config module."""
    os.environ["ENABLE_ROBUST_SCENARIO"] = "true" if enable else "false"
    importlib.reload(config)


def _run_heuristic_batch(session, episodes: int, max_steps: int):
    """Run a batch of heuristic episodes on the robust scenario."""
    results = {"episodes": episodes, "escapes": 0, "steps": []}
    door_states = ["locked", "unlocked"] * ((episodes // 2) + 1)

    for i in range(episodes):
        door_state = door_states[i]
        runtime = AgentRuntimeRobust(session, door_state=door_state, initial_belief=0.5)
        runtime.run_episode(max_steps=max_steps)
        results["escapes"] += 1 if runtime.escaped else 0
        results["steps"].append(runtime.step_count)

    results["escape_rate"] = results["escapes"] / episodes if episodes else 0.0
    results["avg_steps"] = float(np.mean(results["steps"])) if results["steps"] else 0.0
    return results


def _run_active_batch(model, episodes: int, max_steps: int):
    """Run a batch of Active Inference episodes on the robust model."""
    results = {"episodes": episodes, "escapes": 0, "steps": []}
    door_states = ["locked", "unlocked"] * ((episodes // 2) + 1)

    for i in range(episodes):
        door_state = door_states[i]
        runtime = ActiveInferenceRuntime(model=model, temperature=0.8, stochastic=True)
        runtime.run_episode(
            door_state=door_state,
            max_steps=max_steps,
            initial_belief=model.D.copy(),
            policy_depth=3,
            beam_width=10,
        )
        results["escapes"] += 1 if runtime.escaped else 0
        results["steps"].append(len(runtime.trace))

    results["escape_rate"] = results["escapes"] / episodes if episodes else 0.0
    results["avg_steps"] = float(np.mean(results["steps"])) if results["steps"] else 0.0
    return results


def run_robust_benchmark(
    session,
    robust_model,
    episodes: int = 10,
    max_steps: int = 10,
) -> Dict[str, Dict[str, Any]]:
    """
    Run a side-by-side comparison on the robust scenario.

    Returns:
        Dict with keys 'heuristic' and 'active', each containing
        escape_rate/avg_steps/episodes.
    """
    original_flag = config.ENABLE_ROBUST_SCENARIO
    try:
        _toggle_robust_flag(True)
        apply_robust_seed_to_session(session)

        heuristic = _run_heuristic_batch(session, episodes=episodes, max_steps=max_steps)
        active = _run_active_batch(robust_model, episodes=episodes, max_steps=max_steps)
        return {"heuristic": heuristic, "active": active}
    finally:
        _toggle_robust_flag(original_flag)
