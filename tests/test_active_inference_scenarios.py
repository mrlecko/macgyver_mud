from agent_runtime_active import ActiveInferenceRuntime
import pytest
# Import fixtures from tests package
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location("scenario_fixtures", pathlib.Path(__file__).parent / "conftest_scenarios.py")
scenario_fixtures = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(scenario_fixtures)  # type: ignore


@pytest.mark.usefixtures("neo4j_session", "noisy_room_model")
def test_noisy_scenario_prefers_sense_then_escape(noisy_room_model):
    model = noisy_room_model
    runtime = ActiveInferenceRuntime(model=model, temperature=0.5, stochastic=True)
    runtime.run_episode(
        door_state="locked",
        max_steps=8,
        initial_belief=model.D.copy(),
        policy_depth=3,
        beam_width=5,
    )
    trace = runtime.get_trace()
    assert trace, "Trace should not be empty"
    assert trace[0]["action"] == "sense"
    assert runtime.escaped, "Should escape via window or jam/try sequence"


@pytest.mark.usefixtures("neo4j_session", "two_step_key_model")
def test_two_step_key_requires_depth(two_step_key_model):
    model = two_step_key_model
    runtime = ActiveInferenceRuntime(model=model, temperature=0.5, stochastic=True)
    runtime.run_episode(
        door_state="locked",
        max_steps=10,
        initial_belief=model.D.copy(),
        policy_depth=4,
        beam_width=8,
    )
    trace = runtime.get_trace()
    assert trace, "Trace should not be empty"
    actions = [step["action"] for step in trace]
    assert "search_key" in actions
    assert runtime.escaped, "Should escape via key or window"
