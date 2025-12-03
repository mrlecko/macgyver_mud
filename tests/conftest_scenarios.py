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


@pytest.fixture
def robust_room_model():
    """
    Robust room escape with alarm, key search, and noisy sensing.
    States: locked, key_found, unlocked, alarmed
    Observations: locked_signal, unlocked_signal, key_found_obs, opened, stuck, alarm_triggered
    Actions: sense, search_key, disable_alarm, try_door, go_window, jam_door
    """
    states = ["locked", "key_found", "unlocked", "alarmed"]
    observations = ["locked_signal", "unlocked_signal", "key_found_obs", "opened", "stuck", "alarm_triggered"]
    actions = ["sense", "search_key", "disable_alarm", "try_door", "go_window", "jam_door"]
    A = np.zeros((len(observations), len(states), len(actions)))

    # sense: noisy on lock state
    A[observations.index("locked_signal"), states.index("locked"), actions.index("sense")] = 0.7
    A[observations.index("unlocked_signal"), states.index("locked"), actions.index("sense")] = 0.3
    A[observations.index("locked_signal"), states.index("unlocked"), actions.index("sense")] = 0.2
    A[observations.index("unlocked_signal"), states.index("unlocked"), actions.index("sense")] = 0.8
    A[observations.index("alarm_triggered"), states.index("alarmed"), actions.index("sense")] = 1.0
    A[observations.index("locked_signal"), states.index("key_found"), actions.index("sense")] = 0.5
    A[observations.index("unlocked_signal"), states.index("key_found"), actions.index("sense")] = 0.5

    # search_key
    A[observations.index("key_found_obs"), states.index("locked"), actions.index("search_key")] = 0.6
    A[observations.index("stuck"), states.index("locked"), actions.index("search_key")] = 0.4
    A[observations.index("key_found_obs"), states.index("key_found"), actions.index("search_key")] = 0.7
    A[observations.index("stuck"), states.index("key_found"), actions.index("search_key")] = 0.3
    A[observations.index("stuck"), states.index("unlocked"), actions.index("search_key")] = 1.0
    A[observations.index("alarm_triggered"), states.index("alarmed"), actions.index("search_key")] = 1.0

    # disable_alarm
    A[observations.index("alarm_triggered"), states.index("alarmed"), actions.index("disable_alarm")] = 0.6
    A[observations.index("stuck"), states.index("alarmed"), actions.index("disable_alarm")] = 0.4
    A[observations.index("stuck"), :, actions.index("disable_alarm")] += 0.1  # mild noise

    # try_door
    A[observations.index("opened"), states.index("unlocked"), actions.index("try_door")] = 0.9
    A[observations.index("stuck"), states.index("unlocked"), actions.index("try_door")] = 0.1
    A[observations.index("opened"), states.index("locked"), actions.index("try_door")] = 0.05
    A[observations.index("stuck"), states.index("locked"), actions.index("try_door")] = 0.95
    A[observations.index("alarm_triggered"), states.index("alarmed"), actions.index("try_door")] = 0.8
    A[observations.index("stuck"), states.index("alarmed"), actions.index("try_door")] = 0.2

    # go_window
    A[observations.index("opened"), :, actions.index("go_window")] = 1.0

    # jam_door
    A[observations.index("locked_signal"), :, actions.index("jam_door")] = 0.5
    A[observations.index("stuck"), :, actions.index("jam_door")] = 0.5

    B = np.zeros((len(states), len(states), len(actions)))
    # sense/try/go_window static except alarmed remains alarmed
    for act in ("sense", "try_door", "go_window"):
        a_idx = actions.index(act)
        for s_idx in range(len(states)):
            B[s_idx, s_idx, a_idx] = 1.0
    # search_key transitions
    B[states.index("key_found"), states.index("locked"), actions.index("search_key")] = 0.6
    B[states.index("locked"), states.index("locked"), actions.index("search_key")] = 0.4
    B[states.index("unlocked"), states.index("key_found"), actions.index("search_key")] = 0.5
    B[states.index("key_found"), states.index("key_found"), actions.index("search_key")] = 0.5
    for s in ("unlocked", "alarmed"):
        B[states.index(s), states.index(s), actions.index("search_key")] = 1.0
    # disable_alarm transitions
    B[states.index("locked"), states.index("alarmed"), actions.index("disable_alarm")] = 0.7
    B[states.index("alarmed"), states.index("alarmed"), actions.index("disable_alarm")] = 0.3
    for s in ("locked", "key_found", "unlocked"):
        B[states.index(s), states.index(s), actions.index("disable_alarm")] = 1.0 if s != "alarmed" else 0.0
    # jam_door transitions (toggle-ish)
    j_idx = actions.index("jam_door")
    B[states.index("locked"), states.index("locked"), j_idx] = 0.6
    B[states.index("unlocked"), states.index("locked"), j_idx] = 0.4
    B[states.index("locked"), states.index("unlocked"), j_idx] = 0.4
    B[states.index("unlocked"), states.index("unlocked"), j_idx] = 0.6
    B[states.index("alarmed"), states.index("alarmed"), j_idx] = 1.0
    B[states.index("key_found"), states.index("key_found"), j_idx] = 1.0

    C = np.array([0.1, 0.1, 0.5, 3.0, -0.5, -1.0])  # prefer opened most, dislike alarm/stuck
    D = np.array([0.6, 0.1, 0.1, 0.2])
    costs = [0.5, 1.0, 1.2, 1.0, 2.0, 1.0]
    kinds = ["sense", "sense", "act", "act", "act", "act"]
    # Ensure no zero slices in A/B
    for a_idx in range(len(actions)):
        for s_idx in range(len(states)):
            if np.isclose(A[:, s_idx, a_idx].sum(), 0.0):
                A[0, s_idx, a_idx] = 1.0
            if np.isclose(B[:, s_idx, a_idx].sum(), 0.0):
                B[s_idx, s_idx, a_idx] = 1.0

    return GenerativeModel(states, observations, actions, A, B, C, D, action_costs=costs, action_kinds=kinds)


def complex_security_room_model():
    """
    Complex security scenario to stress Active Inference.
    States:
      - locked
      - key_found
      - code_found
      - jammed
      - unlocked
      - alarmed
      - guard_distracted
    Observations:
      - key_found_obs, code_found_obs
      - alarm_triggered, guard_distracted_obs
      - opened, stuck, jam_feedback, noise_signal, quiet_signal
    Actions:
      - search_key (sense)
      - search_code (sense, better after key)
      - distract_guard (sense)
      - disable_alarm (act)
      - jam_door (act)
      - pick_lock (act, better after code/tool)
      - try_door (act)
      - go_window (act)
    """
    states = ["locked", "key_found", "code_found", "jammed", "unlocked", "alarmed", "guard_distracted"]
    observations = [
        "key_found_obs",
        "code_found_obs",
        "alarm_triggered",
        "guard_distracted_obs",
        "opened",
        "stuck",
        "jam_feedback",
        "noise_signal",
        "quiet_signal",
    ]
    actions = ["search_key", "search_code", "distract_guard", "disable_alarm", "jam_door", "pick_lock", "try_door", "go_window"]
    A = np.zeros((len(observations), len(states), len(actions)))

    # search_key: good in locked, worse elsewhere
    A[observations.index("key_found_obs"), states.index("locked"), actions.index("search_key")] = 0.6
    A[observations.index("noise_signal"), states.index("locked"), actions.index("search_key")] = 0.4
    A[observations.index("key_found_obs"), states.index("key_found"), actions.index("search_key")] = 0.5
    A[observations.index("noise_signal"), states.index("key_found"), actions.index("search_key")] = 0.5
    A[observations.index("noise_signal"), :, actions.index("search_key")] += 0.1

    # search_code: better after key_found
    A[observations.index("code_found_obs"), states.index("key_found"), actions.index("search_code")] = 0.6
    A[observations.index("code_found_obs"), states.index("code_found"), actions.index("search_code")] = 0.5
    A[observations.index("noise_signal"), :, actions.index("search_code")] += 0.1

    # distract_guard
    A[observations.index("guard_distracted_obs"), states.index("guard_distracted"), actions.index("distract_guard")] = 0.8
    A[observations.index("noise_signal"), :, actions.index("distract_guard")] += 0.2

    # disable_alarm
    A[observations.index("alarm_triggered"), states.index("alarmed"), actions.index("disable_alarm")] = 0.5
    A[observations.index("quiet_signal"), states.index("alarmed"), actions.index("disable_alarm")] = 0.5
    A[observations.index("quiet_signal"), :, actions.index("disable_alarm")] += 0.1

    # jam_door
    A[observations.index("jam_feedback"), :, actions.index("jam_door")] = 1.0

    # pick_lock (only viable after code_found)
    A[:, :, actions.index("pick_lock")] = 0.0
    A[observations.index("opened"), states.index("code_found"), actions.index("pick_lock")] = 0.6
    A[observations.index("stuck"), states.index("code_found"), actions.index("pick_lock")] = 0.4
    A[observations.index("alarm_triggered"), states.index("locked"), actions.index("pick_lock")] = 0.5
    A[observations.index("stuck"), states.index("locked"), actions.index("pick_lock")] = 0.5

    # try_door (strict dependency: only works if unlocked)
    A[:, :, actions.index("try_door")] = 0.0
    A[observations.index("opened"), states.index("unlocked"), actions.index("try_door")] = 0.8
    A[observations.index("stuck"), states.index("unlocked"), actions.index("try_door")] = 0.2
    A[observations.index("alarm_triggered"), states.index("locked"), actions.index("try_door")] = 0.6
    A[observations.index("stuck"), states.index("locked"), actions.index("try_door")] = 0.4

    # go_window (much less reliable)
    A[:, :, actions.index("go_window")] = 0.0
    A[observations.index("opened"), :, actions.index("go_window")] = 0.5
    A[observations.index("stuck"), :, actions.index("go_window")] = 0.5

    # Default noise to avoid zero slices
    for a_idx in range(len(actions)):
        for s_idx in range(len(states)):
            if np.isclose(A[:, s_idx, a_idx].sum(), 0.0):
                A[observations.index("noise_signal"), s_idx, a_idx] = 1.0

    B = np.zeros((len(states), len(states), len(actions)))
    # Default self transitions
    for a_idx in range(len(actions)):
        for s_idx in range(len(states)):
            B[s_idx, s_idx, a_idx] = 1.0

    # search_key transitions
    B[states.index("key_found"), states.index("locked"), actions.index("search_key")] = 0.6
    B[states.index("locked"), states.index("locked"), actions.index("search_key")] = 0.4

    # search_code transitions
    B[states.index("code_found"), states.index("key_found"), actions.index("search_code")] = 0.6
    B[states.index("key_found"), states.index("key_found"), actions.index("search_code")] = 0.4

    # distract_guard transitions
    B[states.index("guard_distracted"), states.index("locked"), actions.index("distract_guard")] = 0.5
    B[states.index("guard_distracted"), states.index("alarmed"), actions.index("distract_guard")] = 0.3

    # disable_alarm transitions
    B[states.index("locked"), states.index("alarmed"), actions.index("disable_alarm")] = 0.7
    B[states.index("alarmed"), states.index("alarmed"), actions.index("disable_alarm")] = 0.3

    # jam_door transitions (reduce lock quality)
    B[states.index("jammed"), states.index("locked"), actions.index("jam_door")] = 0.5
    B[states.index("locked"), states.index("locked"), actions.index("jam_door")] = 0.5

    # pick_lock transitions
    B[states.index("unlocked"), states.index("code_found"), actions.index("pick_lock")] = 0.6
    B[states.index("jammed"), states.index("jammed"), actions.index("pick_lock")] = 0.2

    # try_door: unlocked stays unlocked; locked triggers alarm mostly
    B[:, :, actions.index("try_door")] = 0.0
    B[states.index("unlocked"), states.index("unlocked"), actions.index("try_door")] = 1.0
    B[states.index("alarmed"), states.index("locked"), actions.index("try_door")] = 0.7
    B[states.index("locked"), states.index("locked"), actions.index("try_door")] = 0.3

    # costs and kinds (raise cost of brute acts / window)
    costs = [1.0, 1.0, 1.2, 1.5, 1.0, 1.8, 2.0, 3.0]
    kinds = ["sense", "sense", "sense", "act", "act", "act", "act", "act"]

    # Preferences: opened high, alarm/noise negative
    C = np.array([1.0, 1.0, -3.0, 0.5, 3.0, -2.0, -1.0, -1.0, 0.2])
    D = np.ones(len(states)) / len(states)

    # Ensure normalization
    for a_idx in range(len(actions)):
        for s_idx in range(len(states)):
            if np.isclose(B[:, s_idx, a_idx].sum(), 0.0):
                B[s_idx, s_idx, a_idx] = 1.0

    return GenerativeModel(states, observations, actions, A, B, C, D, action_costs=costs, action_kinds=kinds)
