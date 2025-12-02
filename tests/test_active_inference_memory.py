import numpy as np

from agent_runtime_active import ActiveInferenceRuntime, build_door_model_defaults
from graph_model import get_skill_stats


def test_active_inference_uses_skill_stats_prior(neo4j_session):
    # Seed skill stats to prefer peek_door
    neo4j_session.run(
        """
        MATCH (sk:Skill {name: 'peek_door'})-[:HAS_STATS]->(stats:SkillStats)
        SET stats.total_uses = 10, stats.successful_episodes = 9
        """
    )
    neo4j_session.run(
        """
        MATCH (sk:Skill {name: 'try_door'})-[:HAS_STATS]->(stats:SkillStats)
        SET stats.total_uses = 10, stats.successful_episodes = 1
        """
    )
    model = build_door_model_defaults()
    runtime = ActiveInferenceRuntime(model=model, temperature=1.0, session=neo4j_session)
    runtime.run_episode(
        door_state="locked",
        max_steps=3,
        initial_belief=np.array([0.5, 0.5]),
        policy_depth=1,
    )
    assert runtime.get_trace()[0]["action"] == "sense"
