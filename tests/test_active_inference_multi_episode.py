import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults


def test_multi_episode_likelihood_converges():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=None)
    force_idx = runtime._action_idx("force")
    before = runtime.model.A[1, 0, force_idx]
    for _ in range(5):
        runtime.update_from_episode([(0, "force", 1, 0)], learning_rate=1.0)
    after = runtime.model.A[1, 0, force_idx]
    assert after > before
