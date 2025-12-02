import pytest

from agent_runtime_active import ActiveInferenceRuntime
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location("scenario_fixtures", pathlib.Path(__file__).parent / "conftest_scenarios.py")
scenario_fixtures = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(scenario_fixtures)  # type: ignore


@pytest.mark.usefixtures("neo4j_session")
def test_robust_scenario_escapes_and_senses_first(robust_room_model):
    model = robust_room_model
    runtime = ActiveInferenceRuntime(model=model, temperature=0.8, stochastic=True)
    runtime.run_episode(
        door_state="locked",
        max_steps=12,
        initial_belief=model.D.copy(),
        policy_depth=3,
        beam_width=10,
    )
    trace = runtime.get_trace()
    assert trace, "Trace should not be empty"
    assert "sense" in [a["action"] for a in trace[:3]], "Should sense early under uncertainty"
    assert runtime.escaped, "Should escape via door/window after key/alarm handling"
