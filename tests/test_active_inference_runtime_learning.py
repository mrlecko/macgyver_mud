import numpy as np
import pytest

from agent_runtime_active import (
    ActiveInferenceRuntime,
    GenerativeModel,
)


def make_simple_model():
    # Two states, two observations, two actions
    states = ["locked", "unlocked"]
    observations = ["fail", "success"]
    actions = ["sense", "force"]
    A = np.array([
        # obs=fail/success for each state/action
        [[1.0, 0.2],  # locked
         [0.0, 0.1]],  # unlocked
        [[0.0, 0.8],
         [1.0, 0.9]],
    ])
    B = np.zeros((2, 2, 2))
    for a in range(2):
        B[0, 0, a] = 1.0
        B[1, 1, a] = 1.0
    C = np.array([0.0, 1.0])
    D = np.array([0.5, 0.5])
    return GenerativeModel(states, observations, actions, A, B, C, D, action_costs=[0.5, 1.0])


def test_dirichlet_learning_updates_A():
    model = make_simple_model()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=None)
    # Before update, likelihood for force on locked -> success is 0.2
    prior = np.array([1.0, 0.0])  # certainly locked
    runtime.update_likelihoods(action="force", state_idx=0, obs_idx=1, learning_rate=1.0)
    # After one success observation, likelihood should move upward
    assert runtime.model.A[1, 0, runtime._action_idx("force")] > 0.2


@pytest.mark.parametrize("door_state,expected_escape", [("unlocked", True), ("locked", True)])
def test_locked_and_unlocked_runs_escape(neo4j_session, door_state, expected_escape):
    from agent_runtime_active import build_model_from_graph

    model = build_model_from_graph(neo4j_session)
    runtime = ActiveInferenceRuntime(model=model, temperature=1.5, session=neo4j_session, stochastic=True)

    runtime.run_episode(
        door_state=door_state,
        max_steps=5,
        initial_belief=model.D.copy(),
        policy_depth=2,
    )
    # Should escape in both cases (door via try, window fallback when locked)
    assert runtime.escaped == expected_escape
