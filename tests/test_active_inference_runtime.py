import os

# These unit tests don't need Neo4j; disable DB fixtures for fast local runs.
os.environ["SKIP_NEO4J_TESTS"] = "1"

import numpy as np
import pytest

from agent_runtime_active import (
    ActiveInferenceRuntime,
    GenerativeModel,
    build_door_model_defaults,
)


def test_generative_model_normalization():
    model = build_door_model_defaults()
    # Rows of A (obs given state, action) should sum to 1 for every state/action
    for action_idx in range(len(model.actions)):
        for state_idx in range(len(model.states)):
            probs = model.A[:, state_idx, action_idx]
            assert np.isclose(probs.sum(), 1.0)
    # Columns of B (state' given state, action) should sum to 1 for every action/state
    for action_idx in range(len(model.actions)):
        for state_idx in range(len(model.states)):
            probs = model.B[:, state_idx, action_idx]
            assert np.isclose(probs.sum(), 1.0)
    # Preferences should form a proper distribution
    assert np.isclose(model.preference_dist.sum(), 1.0)


def test_belief_update_reweights_toward_unlocked():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0)

    prior = np.array([0.5, 0.5])
    posterior = runtime.update_belief(
        prior_belief=prior,
        action="sense",
        observation="open_success",
    )

    unlocked_idx = model.states.index("unlocked")
    assert posterior[unlocked_idx] > 0.95


def test_policy_selection_prefers_information_gathering():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=4.0)

    prior = np.array([0.5, 0.5])
    policy_scores = runtime.evaluate_policies(prior_belief=prior, depth=1)
    best_policy, _ = policy_scores[0]

    assert best_policy[0] == "sense", "Epistemic policy should win from uniform prior"


def test_run_episode_reaches_escape_and_logs_trace():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=2.0, session=None)

    prior = np.array([0.5, 0.5])
    runtime.run_episode(door_state="unlocked", max_steps=3, initial_belief=prior, policy_depth=2)

    trace = runtime.get_trace()
    assert trace, "Trace should contain steps"
    assert trace[0]["action"] == "sense", "Agent should sense first from uniform prior"
    assert runtime.escaped, "Agent should escape within allotted steps"
