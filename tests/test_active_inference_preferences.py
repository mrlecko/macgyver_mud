import json
import numpy as np

from agent_runtime_active import (
    build_model_from_graph,
    save_model_to_graph,
    load_model_from_graph,
    GenerativeModel,
)


def test_preferences_and_states_persist_roundtrip(neo4j_session):
    # Build a custom model with distinct preferences and states
    states = ["locked", "unlocked"]
    observations = ["fail", "success"]
    actions = ["sense"]
    A = np.zeros((2, 2, 1))
    A[0, 0, 0] = 1.0  # fail if locked
    A[1, 1, 0] = 1.0  # success if unlocked
    B = np.zeros((2, 2, 1))
    B[0, 0, 0] = 1.0
    B[1, 1, 0] = 1.0
    C = np.array([0.0, 2.0])
    D = np.array([0.2, 0.8])
    model = GenerativeModel(states, observations, actions, A, B, C, D, action_costs=[0.5])

    save_model_to_graph(neo4j_session, model)
    loaded = load_model_from_graph(neo4j_session)
    assert loaded is not None
    np.testing.assert_allclose(loaded.C, C)
    assert loaded.states == states


def test_domain_fallback_uses_persisted_states(neo4j_session):
    # Remove domain to force fallback
    neo4j_session.run("MATCH (s:StateVar {name: 'DoorLockState'}) REMOVE s.domain")
    # Ensure persisted model exists
    persisted = load_model_from_graph(neo4j_session)
    if not persisted:
        model = build_model_from_graph(neo4j_session)
        save_model_to_graph(neo4j_session, model)
    model2 = build_model_from_graph(neo4j_session)
    assert model2.states == (persisted.states if persisted else ["locked", "unlocked"])
