import time, random
from neo4j import GraphDatabase
import config
from cognitive_agent.textworld_cognitive_agent import CognitiveTextWorldAgent

SEEDS = [42, 43, 44, 45, 46]
MAX_STEPS = 30


def run_red_team():
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    results = []
    try:
        for seed in SEEDS:
            print(f"\n=== Seed {seed} ===")
            agent = CognitiveTextWorldAgent(session, seed=seed)
            reward, steps, visited = agent.run_episode(max_steps=MAX_STEPS)
            success = reward > 0
            results.append({
                "seed": seed,
                "reward": reward,
                "steps": steps,
                "success": success,
                "visited_rooms": visited,
            })
            print(f"Result: {'✅' if success else '❌'} | Reward: {reward} | Steps: {steps}")
    finally:
        session.close()
        driver.close()
    # Summarize
    success_rate = sum(r["success"] for r in results) / len(results)
    avg_reward = sum(r["reward"] for r in results) / len(results)
    avg_steps = sum(r["steps"] for r in results) / len(results)
    summary = (
        f"\n=== RED‑TEAM SUMMARY ===\n"
        f"Seeds evaluated: {SEEDS}\n"
        f"Success rate: {success_rate:.2%}\n"
        f"Average reward: {avg_reward:.2f}\n"
        f"Average steps: {avg_steps:.1f}\n"
    )
    print(summary)
    # Write detailed results to a markdown file for documentation
    with open("validation/COGNITIVE_RED_TEAM_RESULTS.md", "w", encoding="utf-8") as f:
        f.write("# Cognitive Agent Red‑Team Results\n\n")
        f.write(summary)
        f.write("\n## Per‑seed details\n")
        for r in results:
            f.write(f"* Seed {r['seed']}: {'✅' if r['success'] else '❌'} – Reward {r['reward']}, Steps {r['steps']}, Visited rooms: {', '.join(r['visited_rooms'])}\n")
    return results

if __name__ == "__main__":
    run_red_team()
