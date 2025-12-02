import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults
from critical_state import CriticalState


def test_efe_triggers_panic():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=None)
    runtime.update_critical_state(entropy_now=0.1, efe=10.0, steps_remaining=5)
    assert runtime.current_critical_state == CriticalState.PANIC


def test_entropy_drives_flow():
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=None)
    runtime.update_critical_state(entropy_now=0.01, efe=0.1, steps_remaining=5)
    assert runtime.current_critical_state in [CriticalState.FLOW, CriticalState.HUBRIS]
