import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults


def test_beam_search_reduces_policy_count():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0)
    full = runtime.evaluate_policies(prior_belief=model.D, depth=3)
    beam = runtime.evaluate_policies_beam(prior_belief=model.D, depth=3, beam_width=2)
    assert len(full) > len(beam)
    assert len(beam) == 2
