import numpy as np

from agent_runtime_active import (
    ActiveInferenceRuntime,
    build_door_model_defaults,
    save_model_to_graph,
    load_model_from_graph,
)


def test_dirichlet_persistence_roundtrip(neo4j_session):
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=neo4j_session)
    # simulate one update
    runtime.update_likelihoods(action="force", state_idx=0, obs_idx=1, learning_rate=2.0)
    save_model_to_graph(neo4j_session, runtime.model)
    loaded = load_model_from_graph(neo4j_session)
    assert loaded is not None
    # ensure learned slice persisted
    np.testing.assert_allclose(
        loaded.dirichlet_A[:, 0, loaded.actions.index("force")],
        runtime.model.dirichlet_A[:, 0, runtime.model.actions.index("force")],
    )
