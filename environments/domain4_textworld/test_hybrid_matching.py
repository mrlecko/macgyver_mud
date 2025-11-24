#!/usr/bin/env python3
"""
Quick test of Cognitive Agent with Hybrid Matching
Tests only the enhanced cognitive agent to save time.
"""

import sys
import os
sys.path.insert(0, '/home/juancho/macgyver_mud')

import textworld
from neo4j import GraphDatabase

from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from environments.domain4_textworld.benchmark_suite import TextWorldBenchmarkSuite


def test_cognitive_agent():
    """Test enhanced cognitive agent on benchmark."""
    
    # Load benchmark suite
    print("Loading benchmark suite...")
    suite = TextWorldBenchmarkSuite()
    suite.generate_suite(force_regenerate=False)
    
    # Connect to Neo4j
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()
    
    # Test on each game
    results = {'easy': [], 'medium': [], 'hard': []}
    
    for difficulty in ['easy', 'medium', 'hard']:
        games = suite.get_games_by_difficulty(difficulty)[:2]  # Run only 2 games per difficulty for speed
        print(f"\n{'='*70}", flush=True)
        print(f"{difficulty.upper()} Games ({len(games)})", flush=True)
        print('='*70, flush=True)
        
        for i, game_file in enumerate(games, 1):
            # Create fresh agent
            agent = TextWorldCognitiveAgent(session=session, verbose=False)
            
            # Setup environment
            request_infos = textworld.EnvInfos(
                admissible_commands=True,
                objective=True,
                max_score=True
            )
            
            env = textworld.start(game_file, request_infos=request_infos)
            game_state = env.reset()
            
            # Reset agent
            agent.reset(quest=game_state.objective)
            
            # Run episode
            step = 0
            total_reward = 0
            done = False
            
            while not done and step < 50:
                step += 1
                
                action = agent.step(
                    observation=game_state.feedback,
                    feedback=game_state.feedback,
                    reward=total_reward,
                    done=False,
                    admissible_commands=game_state.admissible_commands,
                    quest=None
                )
                
                game_state, reward, done = env.step(action)
                total_reward += reward
            
            env.close()
            
            # Record result
            success = done and total_reward > 0
            results[difficulty].append({
                'game': os.path.basename(game_file),
                'success': success,
                'steps': step,
                'reward': total_reward
            })
            
            status = "✅" if success else "❌"
            print(f"  {i:2d}. {status} {step:2d} steps ({total_reward:+.1f} reward)", flush=True)
    
    # Calculate stats
    all_results = results['easy'] + results['medium'] + results['hard']
    total_games = len(all_results)
    total_success = sum(1 for r in all_results if r['success'])
    
    easy_success = sum(1 for r in results['easy'] if r['success'])
    medium_success = sum(1 for r in results['medium'] if r['success'])
    hard_success = sum(1 for r in results['hard'] if r['success'])
    
    session.close()
    driver.close()
    
    # Print summary
    print(f"\n{'='*70}")
    print("COGNITIVE AGENT WITH HYBRID MATCHING - RESULTS")
    print('='*70)
    print(f"Overall: {total_success}/{total_games} = {total_success/total_games:.1%}")
    print(f"Easy:    {easy_success}/{len(results['easy'])} = {easy_success/len(results['easy']):.1%}")
    print(f"Medium:  {medium_success}/{len(results['medium'])} = {medium_success/len(results['medium']):.1%}")
    print(f"Hard:    {hard_success}/{len(results['hard'])} = {hard_success/len(results['hard']):.1%}")
    print('='*70)
    
    # Compare to baseline
    print("\nCOMPARISON TO BASELINE:")
    print(f"Baseline (token matching):  5% (1/20)")
    print(f"Enhanced (hybrid matching): {total_success/total_games:.1%} ({total_success}/{total_games})")
    
    if total_success > 1:
        improvement = ((total_success/total_games) - 0.05) / 0.05 * 100
        print(f"Improvement: +{improvement:.0f}%")
    
    return results


if __name__ == "__main__":
    test_cognitive_agent()
