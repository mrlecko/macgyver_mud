"""
TextWorld Baseline Benchmark Runner

Tests all three agents on the benchmark suite to establish baseline performance:
1. Quest Agent (minimal, quest-focused)
2. Simple LLM (baseline)
3. Cognitive Agent (current state, protocols disabled)

Generates comparative results to identify where cognitive agent needs improvement.

Usage:
    python environments/domain4_textworld/baseline_benchmark.py
"""

import sys
import os
import json
import time
from typing import Dict, List, Type

sys.path.insert(0, '/home/juancho/macgyver_mud')

import textworld
from neo4j import GraphDatabase

from environments.domain4_textworld.quest_agent import QuestAgent
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.benchmark_suite import TextWorldBenchmarkSuite


def create_simple_llm_agent():
    """
    Create a simple LLM agent for baseline comparison.
    
    Note: Using quest agent as LLM baseline since they're similar performance.
    """
    return QuestAgent(verbose=False)


def run_agent_on_game(
    agent,
    agent_name: str,
    game_file: str,
    max_steps: int = 50
) -> Dict:
    """
    Run single agent on single game.
    
    Returns:
        Result dictionary with success, steps, actions, etc.
    """
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )
    
    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()
    
    # Reset agent with quest
    if hasattr(agent, 'reset'):
        agent.reset(quest=game_state.objective)
    
    step = 0
    total_reward = 0
    last_reward = 0
    done = False
    actions = []
    
    while not done and step < max_steps:
        step += 1
        
        # Get action from agent
        try:
            if agent_name == "Cognitive Agent":
                # Cognitive agent needs more parameters
                action = agent.step(
                    observation=game_state.feedback,
                    feedback=game_state.feedback,
                    reward=last_reward,
                    done=False,
                    admissible_commands=game_state.admissible_commands,
                    quest=None
                )
            else:
                # Quest agent
                action = agent.step(
                    observation=game_state.feedback,
                    reward=last_reward,
                    admissible_commands=game_state.admissible_commands
                )
        except Exception as e:
            print(f"   ⚠️  Agent error: {e}")
            break
        
        actions.append(action)
        
        # Execute in environment
        game_state, reward, done = env.step(action)
        last_reward = reward
        total_reward += reward
    
    env.close()
    
    return {
        'success': done and total_reward > 0,
        'steps': step,
        'reward': total_reward,
        'actions': actions[:10],  # Save first 10 for debugging
    }


def run_benchmark_for_agent(
    agent_class_or_creator,
    agent_name: str,
    suite: TextWorldBenchmarkSuite
) -> Dict:
    """
    Run full benchmark for one agent.
    
    Returns:
        Aggregate results with per-difficulty breakdowns
    """
    print(f"\n{'='*70}")
    print(f"Testing: {agent_name}")
    print(f"{'='*70}")
    
    all_results = []
    
    # Need Neo4j for cognitive agent
    if agent_name == "Cognitive Agent":
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
        
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            session = driver.session()
        except Exception as e:
            print(f"⚠️  Neo4j connection failed: {e}")
            print("   Skipping Cognitive Agent")
            return None
    
    # Test each game
    for difficulty in ['easy', 'medium', 'hard']:
        games = suite.get_games_by_difficulty(difficulty)
        
        print(f"\n{difficulty.upper()} Games ({len(games)}):")
        
        for i, game_file in enumerate(games, 1):
            # Create fresh agent instance
            if agent_name == "Cognitive Agent":
                agent = agent_class_or_creator(session=session, verbose=False)
            else:
                agent = agent_class_or_creator()
            
            # Run game
            result = run_agent_on_game(agent, agent_name, game_file)
            result['difficulty'] = difficulty
            result['game_file'] = os.path.basename(game_file)
            
            all_results.append(result)
            
            # Print progress
            status = "✅" if result['success'] else "❌"
            print(f"  {i:2d}. {status} {result['steps']:2d} steps ({result['reward']:+.1f} reward)")
    
    # Cleanup
    if agent_name == "Cognitive Agent":
        session.close()
        driver.close()
    
    # Calculate stats
    total = len(all_results)
    successes = sum(1 for r in all_results if r['success'])
    
    easy_results = [r for r in all_results if r['difficulty'] == 'easy']
    medium_results = [r for r in all_results if r['difficulty'] == 'medium']
    hard_results = [r for r in all_results if r['difficulty'] == 'hard']
    
    stats = {
        'agent_name': agent_name,
        'overall_success_rate': successes / total if total > 0 else 0,
        'overall_success_count': f"{successes}/{total}",
        'avg_steps': sum(r['steps'] for r in all_results) / total if total > 0 else 0,
        'easy_success_rate': sum(1 for r in easy_results if r['success']) / len(easy_results) if easy_results else 0,
        'medium_success_rate': sum(1 for r in medium_results if r['success']) / len(medium_results) if medium_results else 0,
        'hard_success_rate': sum(1 for r in hard_results if r['success']) / len(hard_results) if hard_results else 0,
        'results_by_game': all_results,
    }
    
    # Print summary
    print(f"\n{agent_name} Summary:")
    print(f"  Overall: {stats['overall_success_rate']:.1%} ({stats['overall_success_count']})")
    print(f"  Easy:    {stats['easy_success_rate']:.1%}")
    print(f"  Medium:  {stats['medium_success_rate']:.1%}")
    print(f"  Hard:    {stats['hard_success_rate']:.1%}")
    print(f"  Avg Steps: {stats['avg_steps']:.1f}")
    
    return stats


def create_comparison_report(all_results: Dict[str, Dict], suite: TextWorldBenchmarkSuite):
    """
    Create markdown report comparing all agents.
    """
    report = []
    report.append("# TextWorld Baseline Benchmark Results")
    report.append(f"\n**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**Games:** {len(suite.get_all_games())} (5 easy, 10 medium, 5 hard)")
    report.append("\n---\n")
    
    report.append("## Overall Performance\n")
    report.append("| Agent | Easy | Medium | Hard | Overall | Avg Steps |")
    report.append("|-------|------|--------|------|---------|-----------|")
    
    for agent_name, stats in all_results.items():
        if stats is None:
            continue
        report.append(
            f"| {agent_name} | "
            f"{stats['easy_success_rate']:.0%} | "
            f"{stats['medium_success_rate']:.0%} | "
            f"{stats['hard_success_rate']:.0%} | "
            f"{stats['overall_success_rate']:.0%} ({stats['overall_success_count']}) | "
            f"{stats['avg_steps']:.1f} |"
        )
    
    report.append("\n---\n")
    report.append("## Analysis\n")
    report.append("**Key Findings:**\n")
    report.append("- [To be filled after reviewing results]\n")
    report.append("- Which agent performs best on complex games?\n")
    report.append("- Where does cognitive agent struggle?\n")
    report.append("- What protocols would help?\n")
    
    report_text = "\n".join(report)
    
    # Save report
    report_file = "TEXTWORLD_BASELINE_RESULTS.md"
    with open(report_file, 'w') as f:
        f.write(report_text)
    
    print(f"\n📝 Report saved to: {report_file}")
    
    return report_text


def main():
    """Run baseline benchmark."""
    print("\n" + "="*70)
    print("TEXTWORLD BASELINE BENCHMARK")
    print("="*70)
    print("\nEstablishing baseline performance before cognitive enhancements")
    
    # Load or generate benchmark suite
    print("\n1. Loading benchmark suite...")
    suite = TextWorldBenchmarkSuite()
    suite.generate_suite(force_regenerate=False)
    
    # Test agents
    agents_to_test = [
        (QuestAgent, "Quest Agent"),
        # (create_simple_llm_agent, "Simple LLM"),  # Skip for now, similar to Quest
        (TextWorldCognitiveAgent, "Cognitive Agent"),
    ]
    
    all_results = {}
    
    for agent_class, agent_name in agents_to_test:
        stats = run_benchmark_for_agent(agent_class, agent_name, suite)
        if stats:
            all_results[agent_name] = stats
    
    # Save detailed results
    print(f"\n2. Saving detailed results...")
    with open('baseline_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"   ✓ Saved to: baseline_results.json")
    
    # Create comparison report
    print(f"\n3. Creating comparison report...")
    create_comparison_report(all_results, suite)
    
    print("\n" + "="*70)
    print("BASELINE BENCHMARK COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Review TEXTWORLD_BASELINE_RESULTS.md")
    print("2. Identify where cognitive agent struggles")
    print("3. Implement quest-aware critical states")
    print("4. Re-run benchmark to measure improvement")


if __name__ == "__main__":
    main()
