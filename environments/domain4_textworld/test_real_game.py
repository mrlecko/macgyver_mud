"""
Test cognitive agent on real TextWorld game.

This validates the agent chassis works with actual TextWorld environment.
"""
import sys
from neo4j import GraphDatabase
import config
from environments.domain4_textworld.textworld_adapter import TextWorldAdapter
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent


def main():
    """Run cognitive agent on a real TextWorld game."""
    print("\n" + "="*70)
    print("🎮 TEXTWORLD COGNITIVE AGENT - REAL GAME TEST")
    print("="*70)
    
    # Setup Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    
    try:
        # Create TextWorld environment
        print("\n🏗️  Setting up TextWorld environment...")
        adapter = TextWorldAdapter(session)
        
        # Generate simple game
        print("🎲 Generating game (seed=42, 3 rooms, 5 objects)...")
        adapter.generate_game(seed=42)
        
        # Reset environment
        print("🔄 Resetting environment...")
        initial_state = adapter.reset()
        
        print(f"\n📊 Initial state:")
        feedback_str = str(initial_state.feedback)[:200]
        print(f"   Feedback: {feedback_str}...")
        print(f"   Max score: {initial_state.max_score}")
        
        # Create cognitive agent
        print("\n🧠 Creating cognitive agent...")
        agent = TextWorldCognitiveAgent(session, verbose=True)
        
        # Run episode
        print("\n" + "="*70)
        print("🚀 STARTING EPISODE")
        print("="*70)
        
        done = False
        current_state = initial_state
        total_reward = 0
        max_steps = 20  # Limit for testing
        
        for step_num in range(max_steps):
            # Get admissible commands
            commands = adapter.get_admissible_commands()
            
            # Agent decides action
            action = agent.step(
                observation=str(current_state.feedback) if current_state.feedback else "",
                feedback="",
                reward=total_reward,
                done=done,
                admissible_commands=commands or ['look']
            )
            
            print(f"\n💬 Executing: '{action}'")
            
            # Execute in environment
            if commands and action in commands:
                current_state, reward, done = adapter.step(action)
                total_reward += reward
            else:
                print(f"⚠️  Action not in admissible commands, trying anyway...")
                try:
                    current_state, reward, done = adapter.step(action)
                    total_reward += reward
                except:
                    print(f"❌ Action failed, using 'look' instead")
                    current_state, reward, done = adapter.step('look')
            
            if done:
                print(f"\n🏆 EPISODE COMPLETE!")
                print(f"   Total reward: {total_reward}")
                print(f"   Steps taken: {step_num + 1}")
                break
        
        if not done:
            print(f"\n⏱️  Episode timeout after {max_steps} steps")
            print(f"   Total reward: {total_reward}")
        
        # Summary
        print("\n" + "="*70)
        print("📈 EPISODE SUMMARY")
        print("="*70)
        print(f"   Steps: {len(agent.action_history)}")
        print(f"   Observations: {len(agent.observation_history)}")
        print(f"   Total reward: {total_reward}")
        print(f"   Completed: {'✅ Yes' if done else '❌ No'}")
        
        print("\n🔍 Action history:")
        for i, action_entry in enumerate(agent.action_history[:10], 1):
            print(f"   {i}. {action_entry['action']} (score: {action_entry['score']:.2f})")
        
        if len(agent.action_history) > 10:
            print(f"   ... and {len(agent.action_history) - 10} more")
        
        print("\n✅ Test complete!")
        
    finally:
        adapter.close()
        session.close()
        driver.close()


if __name__ == "__main__":
    main()
