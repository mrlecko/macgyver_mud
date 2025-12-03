import pytest

from agent_runtime_active import ActiveInferenceRuntime
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location("scenario_fixtures", pathlib.Path(__file__).parent / "conftest_scenarios.py")
scenario_fixtures = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(scenario_fixtures)  # type: ignore


def test_complex_scenario_requires_multi_step():
    model = scenario_fixtures.complex_security_room_model()
    runtime = ActiveInferenceRuntime(model=model, temperature=0.7, stochastic=False)
    runtime.run_episode(
        door_state="locked",
        max_steps=12,
        initial_belief=model.D.copy(),
        policy_depth=4,
        beam_width=12,
    )
    trace = runtime.get_trace()
    assert trace, "Trace should not be empty"
    actions = [a["action"] for a in trace]
    assert "search_key" in actions or "search_code" in actions, "Should explore for key/code first"
    assert runtime.escaped, "Should escape after multi-step planning"
