import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_model_from_graph


def test_active_inference_runtime_with_neo4j(neo4j_session):
    model = build_model_from_graph(neo4j_session)
    runtime = ActiveInferenceRuntime(model=model, temperature=2.0, session=neo4j_session)

    episode_id = runtime.run_episode(
        door_state="unlocked",
        max_steps=4,
        initial_belief=model.D.copy(),
        policy_depth=2,
    )

    trace = runtime.get_trace()
    assert trace, "Trace should not be empty"
    first_action = trace[0]["action"]
    assert first_action == "peek_door", f"Expected epistemic first action, got {first_action}"
    assert runtime.escaped, "Agent should escape when door is unlocked"

    # Check belief increases toward unlocked after sensing
    assert trace[0]["p_after"] > trace[0]["p_before"], "Belief should move toward unlocked after observation"

    # Verify logging persisted steps to Neo4j
    result = neo4j_session.run(
        """
        MATCH (e:Episode) WHERE id(e) = $episode_id
        MATCH (e)-[:HAS_STEP]->(s:Step)
        RETURN count(s) AS steps
        """,
        episode_id=episode_id,
    ).single()
    assert result and result["steps"] >= len(trace), "Steps should be logged in Neo4j"
