import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults


def test_policy_limit_applied():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0)
    scored = runtime.evaluate_policies(prior_belief=model.D, depth=3, max_nodes=10)
    assert len(scored) == len(model.actions) ** 3 or len(scored) == 10
    # Limit policies and ensure truncation respected
    action, limited = runtime.select_action(model.D, depth=3, max_policies=2)
    assert len(limited) == 2
