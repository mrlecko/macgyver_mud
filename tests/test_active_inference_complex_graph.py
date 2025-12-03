import numpy as np
import pytest

from agent_runtime_active import ActiveInferenceRuntime, build_model_from_graph
from scripts.apply_robust_seed import apply_robust_seed_to_session
from conftest import reset_dynamic_data


@pytest.mark.usefixtures("neo4j_session")
def test_complex_graph_model_escapes_with_dependencies(neo4j_session):
    """
    Ensure the Neo4j-built complex model can escape when strict dependencies are present.

    Uses deterministic transitions (stochastic=False) for stability.
    """
    apply_robust_seed_to_session(neo4j_session)
    model = build_model_from_graph(neo4j_session)

    runtime = ActiveInferenceRuntime(
        model=model,
        temperature=0.8,
        stochastic=False,
        session=neo4j_session,
    )

    try:
        runtime.run_episode(
            door_state="locked",
            max_steps=12,
            initial_belief=model.D.copy(),
            policy_depth=5,
            beam_width=12,
        )
    finally:
        reset_dynamic_data(neo4j_session)

    trace = runtime.get_trace()
    actions = [step["action"] for step in trace]

    assert trace, "Trace should not be empty"
    assert {"search_key", "search_code"}.intersection(actions), "Should explore for key/code first"
    assert "pick_lock" in actions or "go_window" in actions, "Should attempt an escape action"
    assert runtime.escaped, f"Expected escape within 12 steps, got actions={actions}"
