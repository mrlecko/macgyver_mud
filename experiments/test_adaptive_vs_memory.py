#!/usr/bin/env python3
"""
Compare Memory Only vs Memory+Adaptive side-by-side
to understand why adaptive stays at 2 steps
"""
from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from graph_model import get_meta_params, get_agent, get_skill_stats

driver = GraphDatabase.driver(
    config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)

def reset():
    with driver.session(database="neo4j") as session:
        session.run("""
            MATCH (stats:SkillStats)
            SET stats.total_uses = 0,
                stats.successful_episodes = 0,
                stats.failed_episodes = 0,
                stats.uncertain_uses = 0,
                stats.uncertain_successes = 0
        """)
        session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            SET meta.episodes_completed = 0,
                meta.beta = 6.0
        """)

def run_test(use_adaptive, num_episodes=20):
    with driver.session(database="neo4j") as session:
        agent_node = get_agent(session, config.AGENT_NAME)

        print(f"\n{'='*80}")
        print(f"TEST: Memory={'True'}, Adaptive={use_adaptive}")
        print(f"{'='*80}\n")

        steps_history = []

        for i in range(num_episodes):
            agent = AgentRuntime(
                session,
                door_state="unlocked" if i % 2 == 0 else "locked",
                initial_belief=0.5,
                use_procedural_memory=True,
                adaptive_params=use_adaptive,
                verbose_memory=(i % 5 == 0)  # Verbose every 5 episodes
            )

            agent.run_episode(max_steps=5)
            steps_history.append(agent.step_count)

            trace = agent.get_trace()
            skills_used = [step['skill'] for step in trace]

            if i < 5 or i >= num_episodes - 5 or i % 5 == 0:
                print(f"Ep{i+1:2d}: {' → '.join(skills_used):30s} ({agent.step_count} steps)")

                if use_adaptive and i % 5 == 4:  # Every 5th episode
                    meta = get_meta_params(session, agent_node['id'])
                    print(f"      Beta: {meta['beta']:.2f}, Episodes: {meta['episodes']}")

            # Show decision log for first episode
            if i == 0 and agent.decision_log:
                print("\n  Decision log (Episode 1):")
                for decision in agent.decision_log:
                    print(f"    Step {decision['step']}: {decision['selected']} (score={decision['score']:.2f})")
                print()

        early_avg = sum(steps_history[:5]) / 5
        late_avg = sum(steps_history[-5:]) / 5
        overall_avg = sum(steps_history) / len(steps_history)

        print(f"\nRESULTS:")
        print(f"  Early (1-5): {early_avg:.2f} steps")
        print(f"  Late ({num_episodes-4}-{num_episodes}): {late_avg:.2f} steps")
        print(f"  Overall: {overall_avg:.2f} steps")
        print(f"  Improvement: {(early_avg - late_avg) / early_avg * 100:+.1f}%")

        # Show skill preferences
        print(f"\n  Skill stats at end:")
        for skill in ['peek_door', 'try_door', 'go_window']:
            stats = get_skill_stats(session, skill)
            print(f"    {skill:15s}: {stats['overall']['uses']} uses, {stats['overall']['success_rate']:.0%} success")

# Test 1: Memory Only
print("\n" + "="*80)
print("COMPARATIVE TEST: Memory Only vs Memory+Adaptive")
print("="*80)

reset()
run_test(use_adaptive=False, num_episodes=20)

# Test 2: Memory + Adaptive
reset()
run_test(use_adaptive=True, num_episodes=20)

driver.close()
