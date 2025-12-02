import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults


def test_update_from_episode_updates_dirichlet():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=None)
    transitions = [
        (0, "force", 1, 0),  # locked, force, success obs, remains locked
        (0, "force", 1, 0),
    ]
    before = runtime.model.dirichlet_A[1, 0, runtime._action_idx("force")]
    runtime.update_from_episode(transitions, learning_rate=1.0)
    after = runtime.model.dirichlet_A[1, 0, runtime._action_idx("force")]
    assert after > before
