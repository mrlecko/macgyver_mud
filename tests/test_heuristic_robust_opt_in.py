import importlib
import os

import pytest

import config
import scoring
import agent_runtime_robust
from experiments.benchmark_robust import run_robust_benchmark
from scripts.apply_robust_seed import apply_robust_seed_to_session


@pytest.fixture
def enable_robust(monkeypatch):
    """
    Temporarily enable the robust scenario flag and reload config-dependent modules.
    Ensures we don't leak the flag to other tests.
    """
    original = os.environ.get("ENABLE_ROBUST_SCENARIO")
    monkeypatch.setenv("ENABLE_ROBUST_SCENARIO", "true")

    importlib.reload(config)
    importlib.reload(scoring)
    importlib.reload(agent_runtime_robust)

    yield

    if original is None:
        monkeypatch.delenv("ENABLE_ROBUST_SCENARIO", raising=False)
    else:
        monkeypatch.setenv("ENABLE_ROBUST_SCENARIO", original)

    importlib.reload(config)
    importlib.reload(scoring)
    importlib.reload(agent_runtime_robust)


@pytest.mark.usefixtures("neo4j_session")
def test_heuristic_runtime_uses_robust_skills(monkeypatch, neo4j_session, enable_robust):
    """Heuristic runtime should pick up robust skills when opt-in flag is true."""
    apply_robust_seed_to_session(neo4j_session)

    runtime = agent_runtime_robust.AgentRuntimeRobust(
        neo4j_session, door_state="locked", initial_belief=0.5
    )
    runtime.run_episode(max_steps=8)

    assert runtime.escaped, "Heuristic runtime should still find an escape path"
    skills_used = [step["selected"] for step in runtime.decision_log]
    assert any(
        s in {"search_key", "disable_alarm", "jam_door", "try_door_stealth"}
        for s in skills_used
    ), f"Expected robust skills to appear in decision log, saw {skills_used}"


def test_benchmark_reports_both_runtimes(monkeypatch, neo4j_session, robust_room_model, enable_robust):
    """Benchmark helper should return metrics for heuristic and Active Inference on robust scenario."""
    apply_robust_seed_to_session(neo4j_session)

    results = run_robust_benchmark(
        session=neo4j_session,
        robust_model=robust_room_model,
        episodes=4,
        max_steps=10,
    )

    assert set(results.keys()) == {"heuristic", "active"}
    assert results["heuristic"]["episodes"] == 4
    assert results["active"]["episodes"] == 4
    assert "escape_rate" in results["heuristic"]
    assert "escape_rate" in results["active"]
