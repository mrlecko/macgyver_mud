import numpy as np
import pytest

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults, _entropy
from critical_state import CriticalState


def test_entropy_triggers_panic_state():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, stochastic=False)
    agent_state = runtime.monitor  # reuse monitor on synthetic state
    from critical_state import AgentState
    cs = runtime.monitor.evaluate(
        AgentState(
            entropy=_entropy(np.array([0.5, 0.5])),
            history=[],
            steps=10,
            dist=1.0,
            rewards=[],
            error=0.0,
        )
    )
    assert cs == CriticalState.PANIC


def test_low_entropy_stays_flow():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, stochastic=False)
    from critical_state import AgentState
    cs = runtime.monitor.evaluate(
        AgentState(
            entropy=_entropy(np.array([0.99, 0.01])),
            history=[],
            steps=10,
            dist=1.0,
            rewards=[],
            error=0.0,
        )
    )
    assert cs == CriticalState.FLOW
