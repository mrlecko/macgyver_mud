import pytest
import numpy as np

from agent_runtime_active import GenerativeModel


@pytest.fixture
def noisy_room_model():
    """
    Parallel room-escape model with noisy sensing and a jam action.
    States: locked, unlocked
    Observations: locked_signal, unlocked_signal, opened, stuck
    Actions:
      - sense (noisy)
      - try_door (state-dependent)
      - go_window (deterministic escape)
      - jam_door (probabilistic toggle)
    """
    states = ["locked", "unlocked"]
    observations = ["locked_signal", "unlocked_signal", "opened", "stuck"]
    actions = ["sense", "try_door", "go_window", "jam_door"]
    A = np.zeros((len(observations), len(states), len(actions)))

    # sense: noisy
    A[observations.index("locked_signal"), states.index("locked"), actions.index("sense")] = 0.8
    A[observations.index("unlocked_signal"), states.index("locked"), actions.index("sense")] = 0.2
    A[observations.index("locked_signal"), states.index("unlocked"), actions.index("sense")] = 0.2
    A[observations.index("unlocked_signal"), states.index("unlocked"), actions.index("sense")] = 0.8

    # try_door: success if unlocked, fail if locked
    A[observations.index("opened"), states.index("unlocked"), actions.index("try_door")] = 0.9
    A[observations.index("stuck"), states.index("unlocked"), actions.index("try_door")] = 0.1
    A[observations.index("opened"), states.index("locked"), actions.index("try_door")] = 0.05
    A[observations.index("stuck"), states.index("locked"), actions.index("try_door")] = 0.95

    # go_window: always escape
    A[observations.index("opened"), :, actions.index("go_window")] = 1.0

    # jam_door: no observation, but we model as "stuck"
    A[observations.index("stuck"), :, actions.index("jam_door")] = 1.0

    B = np.zeros((len(states), len(states), len(actions)))
    # sense/try/window: static state
    for act in ("sense", "try_door", "go_window"):
        a_idx = actions.index(act)
        B[states.index("locked"), states.index("locked"), a_idx] = 1.0
        B[states.index("unlocked"), states.index("unlocked"), a_idx] = 1.0
    # jam_door: toggle with probability
    j_idx = actions.index("jam_door")
    B[states.index("locked"), states.index("locked"), j_idx] = 0.6
    B[states.index("unlocked"), states.index("locked"), j_idx] = 0.4
    B[states.index("locked"), states.index("unlocked"), j_idx] = 0.4
    B[states.index("unlocked"), states.index("unlocked"), j_idx] = 0.6

    C = np.array([0.0, 0.0, 2.5, -0.5])  # prefer opened more strongly
    D = np.array([0.5, 0.5])
    costs = [0.5, 1.0, 1.0, 1.0]  # make window/jam affordable
    kinds = ["sense", "act", "act", "act"]

    return GenerativeModel(states, observations, actions, A, B, C, D, action_costs=costs, action_kinds=kinds)


@pytest.fixture
def two_step_key_model():
    """
    Two-step unlock scenario.
    States: locked, key_found, unlocked
    Observations: key_found_obs, opened, fail
    Actions:
      - search_key (noisy success)
      - try_door (fails unless unlocked)
      - go_window (escape)
    """
    states = ["locked", "key_found", "unlocked"]
    observations = ["key_found_obs", "opened", "fail"]
    actions = ["search_key", "try_door", "go_window"]
    A = np.zeros((len(observations), len(states), len(actions)))

    # search_key: succeed if locked, move to key_found (via B)
    A[observations.index("key_found_obs"), states.index("locked"), actions.index("search_key")] = 0.7
    A[observations.index("fail"), states.index("locked"), actions.index("search_key")] = 0.3
    A[observations.index("key_found_obs"), states.index("key_found"), actions.index("search_key")] = 0.9
    A[observations.index("fail"), states.index("key_found"), actions.index("search_key")] = 0.1
    A[observations.index("fail"), states.index("unlocked"), actions.index("search_key")] = 1.0

    # try_door: only unlocked succeeds
    A[observations.index("opened"), states.index("unlocked"), actions.index("try_door")] = 0.9
    A[observations.index("fail"), states.index("unlocked"), actions.index("try_door")] = 0.1
    A[observations.index("fail"), states.index("locked"), actions.index("try_door")] = 1.0
    A[observations.index("fail"), states.index("key_found"), actions.index("try_door")] = 1.0

    # go_window: always escape
    A[observations.index("opened"), :, actions.index("go_window")] = 1.0

    B = np.zeros((len(states), len(states), len(actions)))
    # search_key transitions
    B[states.index("key_found"), states.index("locked"), actions.index("search_key")] = 0.7
    B[states.index("locked"), states.index("locked"), actions.index("search_key")] = 0.3
    B[states.index("unlocked"), states.index("key_found"), actions.index("search_key")] = 0.5
    B[states.index("key_found"), states.index("key_found"), actions.index("search_key")] = 0.5
    # try_door can unlock if key found
    B[states.index("unlocked"), states.index("key_found"), actions.index("try_door")] = 0.8
    B[states.index("key_found"), states.index("key_found"), actions.index("try_door")] = 0.2
    # Default static transitions for all remaining zero columns
    for a_idx in range(len(actions)):
        for s_idx in range(len(states)):
            if np.isclose(B[:, s_idx, a_idx].sum(), 0.0):
                B[s_idx, s_idx, a_idx] = 1.0

    C = np.array([0.5, 3.0, -0.5])  # prefer key_found, strongly prefer opened
    D = np.array([0.8, 0.1, 0.1])
    costs = [0.8, 1.0, 1.5]
    kinds = ["sense", "act", "act"]
    return GenerativeModel(states, observations, actions, A, B, C, D, action_costs=costs, action_kinds=kinds)
