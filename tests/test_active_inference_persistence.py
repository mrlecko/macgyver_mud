import numpy as np

from agent_runtime_active import (
    ActiveInferenceRuntime,
    build_door_model_defaults,
    save_model_to_graph,
    load_model_from_graph,
)
from neo4j import GraphDatabase
import config


def test_save_and_load_roundtrip(neo4j_session):
    model = build_door_model_defaults()
    save_model_to_graph(neo4j_session, model)
    loaded = load_model_from_graph(neo4j_session)
    assert loaded is not None
    np.testing.assert_allclose(loaded.A, model.A)
    np.testing.assert_allclose(loaded.B, model.B)
    np.testing.assert_allclose(loaded.C, model.C)
    np.testing.assert_allclose(loaded.D, model.D)
    assert loaded.actions == model.actions


def test_active_inference_vs_heuristic_steps(neo4j_session):
    from agent_runtime import AgentRuntime

    # Active Inference
    model = build_door_model_defaults()
    runtime_ai = ActiveInferenceRuntime(model=model, temperature=1.5, session=neo4j_session)
    runtime_ai.run_episode(
        door_state="unlocked",
        max_steps=4,
        initial_belief=model.D.copy(),
        policy_depth=2,
    )

    # Heuristic agent
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    with driver.session(database="neo4j") as session2:
        heur = AgentRuntime(
            session2,
            door_state="unlocked",
            initial_belief=config.INITIAL_BELIEF,
            use_procedural_memory=False,
            adaptive_params=False,
            verbose_memory=False,
            skill_mode="hybrid",
        )
        heur.run_episode(max_steps=4)

    assert runtime_ai.escaped
    assert heur.escaped
    assert len(runtime_ai.get_trace()) <= heur.step_count
