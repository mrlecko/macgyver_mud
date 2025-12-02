import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults


def test_run_episode_updates_likelihoods_via_replay():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=None)
    sense_idx = runtime._action_idx("sense")
    before = runtime.model.A[1, 1, sense_idx]
    runtime.run_episode(
        door_state="unlocked",
        max_steps=2,
        initial_belief=np.array([0.5, 0.5]),
        policy_depth=1,
    )
    after = runtime.model.A[1, 1, sense_idx]
    assert after > before
