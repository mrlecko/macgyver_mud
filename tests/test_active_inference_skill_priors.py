import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, GenerativeModel


def test_skill_priors_bias_action_selection():
    states = ["locked", "unlocked"]
    observations = ["opened", "stuck"]
    actions = ["sense", "try"]
    A = np.zeros((len(observations), len(states), len(actions)))
    A[observations.index("opened"), states.index("unlocked"), actions.index("try")] = 1.0
    A[observations.index("stuck"), states.index("locked"), actions.index("try")] = 1.0
    A[observations.index("stuck"), :, actions.index("sense")] = 1.0
    B = np.zeros((len(states), len(states), len(actions)))
    for a in actions:
        a_idx = actions.index(a)
        B[:, :, a_idx] = np.eye(len(states))
    C = np.array([2.0, -0.5])
    D = np.array([0.5, 0.5])
    costs = [0.5, 1.0]
    kinds = ["sense", "act"]
    model = GenerativeModel(states, observations, actions, A, B, C, D, action_costs=costs, action_kinds=kinds)

    skill_priors = {"try": {"success_rate": 0.9, "confidence": 0.9}}
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, stochastic=False, skill_priors=skill_priors)
    action, ranked = runtime.select_action(prior_belief=D, depth=1)
    assert action == "try", f"Expected priors to bias toward 'try', got '{action}'"
    assert ranked[0][0][0] == "try"
