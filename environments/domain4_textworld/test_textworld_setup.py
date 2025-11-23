"""
TextWorld Domain 4 Integration - Setup Verification Test

This test verifies that TextWorld is installed and working.
Run: python3 environments/domain4_textworld/test_textworld_setup.py
"""
import sys
import os

def test_textworld_installation():
    """Test 1: Verify textworld can be imported."""
    try:
        import textworld
        print("✓ Test 1 PASSED: TextWorld imported successfully")
        print(f"  Version: {textworld.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Test 1 FAILED: Could not import textworld")
        print(f"  Error: {e}")
        print(f"  Fix: pip install textworld")
        return False


def test_game_generation():
    """Test 2: Verify TextWorld can generate a game."""
    try:
        import textworld
        
        # Create game options
        options = textworld.GameOptions()
        options.nb_rooms = 3
        options.nb_objects = 5
        options.quest_length = 3
        options.seed = 42
        
        print("✓ Test 2 PASSED: GameOptions created")
        print(f"  Rooms: {options.nb_rooms}")
        print(f"  Objects: {options.nb_objects}")
        print(f"  Quest length: {options.quest_length}")
        
        # Generate game
        game = textworld.generator.make_game(options)
        print(f"  Game generated: {len(game.world.rooms)} rooms, {len(game.world.objects)} objects")
        return True
        
    except Exception as e:
        print(f"✗ Test 2 FAILED: Could not generate game")
        print(f"  Error: {e}")
        return False


def test_game_compilation():
    """Test 3: Verify game can be compiled to playable format."""
    try:
        import textworld
        
        # Generate simple game
        options = textworld.GameOptions()
        options.nb_rooms = 2
        options.nb_objects = 3
        options.quest_length = 2
        options.seed = 42
        
        game = textworld.generator.make_game(options)
        
        # Compile to file (correct API: returns game file path)
        os.makedirs("./scratch", exist_ok=True)
        game_file = textworld.generator.compile_game(game)
        
        # Move to our scratch directory
        import shutil
        target_path = "./scratch/test_tw_game.ulx"
        if os.path.exists(game_file):
            shutil.move(game_file, target_path)
            game_file = target_path
        
        print("✓ Test 3 PASSED: Game compiled successfully")
        print(f"  Game file: {game_file}")
        print(f"  File exists: {os.path.exists(game_file)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test 3 FAILED: Could not compile game")
        print(f"  Error: {e}")
        return False


def test_game_playability():
    """Test 4: Verify compiled game can be loaded and played."""
    try:
        import textworld
        import shutil
        
        # Use game from previous test
        game_file = "./scratch/test_tw_game.ulx"
        
        if not os.path.exists(game_file):
            # Generate if missing
            options = textworld.GameOptions()
            options.nb_rooms = 2
            options.nb_objects = 3
            options.seed = 42
            game = textworld.generator.make_game(options)
            compiled_file = textworld.generator.compile_game(game)
            shutil.move(compiled_file, game_file)
        
        # Start environment
        env = textworld.start(game_file)
        initial_state = env.reset()
        
        print("✓ Test 4 PASSED: Game is playable")
        print(f"  Initial description length: {len(initial_state.feedback)} chars")
        commands = initial_state.admissible_commands or []
        print(f"  Available commands: {len(commands)}")
        print(f"  Max score: {initial_state.max_score}")
        
        # Try a few actions
        if commands:
            for i, cmd in enumerate(commands[:3]):
                state, reward, done = env.step(cmd)
                print(f"  Action {i+1} ('{cmd}'): reward={reward}, done={done}")
                if done:
                    break
        else:
            print("  No admissible commands available")
        
        env.close()
        return True
        
    except Exception as e:
        print(f"✗ Test 4 FAILED: Could not play game")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_state_structure():
    """Test 5: Verify game state has expected structure."""
    try:
        import textworld
        import shutil
        
        # Generate and start game
        options = textworld.GameOptions()
        options.nb_rooms = 2
        options.seed = 42
        game = textworld.generator.make_game(options)
        game_file = textworld.generator.compile_game(game)
        
        # Move to scratch
        target = "./scratch/test_structure.ulx"
        shutil.move(game_file, target)
        
        env = textworld.start(target)
        state = env.reset()
        
        # Check state components
        assert hasattr(state, 'feedback'), "Missing feedback"
        assert hasattr(state, 'inventory'), "Missing inventory"
        assert hasattr(state, 'admissible_commands'), "Missing admissible_commands"
        assert hasattr(state, 'score'), "Missing score"
        assert hasattr(state, 'max_score'), "Missing max_score"
        
        print("✓ Test 5 PASSED: Game state has expected structure")
        print(f"  State attributes: feedback, inventory, score, commands")
        inv = list(state.inventory) if state.inventory else []
        print(f"  Inventory: {inv}")
        print(f"  Score: {state.score}/{state.max_score}")
        
        env.close()
        return True
        
    except Exception as e:
        print(f"✗ Test 5 FAILED: Game state structure invalid")
        print(f"  Error: {e}")
        return False


def test_quest_structure():
    """Test 6: Verify quest has goals and structure."""
    try:
        import textworld
        
        options = textworld.GameOptions()
        options.nb_rooms = 3
        options.nb_objects = 5
        options.quest_length = 4
        options.seed = 42
        
        game = textworld.generator.make_game(options)
        
        # Check quest
        assert hasattr(game, 'quests'), "Game has no quests"
        assert len(game.quests) > 0, "No quests generated"
        
        quest = game.quests[0]
        
        print("✓ Test 6 PASSED: Quest structure valid")
        print(f"  Number of quests: {len(game.quests)}")
        print(f"  Quest commands: {len(quest.commands) if hasattr(quest, 'commands') else 'N/A'}")
        print(f"  Quest win events: {len(quest.win_events)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test 6 FAILED: Quest structure invalid")
        print(f"  Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("TEXTWORLD DOMAIN 4 - SETUP VERIFICATION")
    print("=" * 70)
    print()
    
    tests = [
        test_textworld_installation,
        test_game_generation,
        test_game_compilation,
        test_game_playability,
        test_game_state_structure,
        test_quest_structure,
    ]
    
    results = []
    for test_func in tests:
        print(f"\nRunning: {test_func.__doc__}")
        result = test_func()
        results.append(result)
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - TextWorld is ready for integration!")
        print("\nWhy TextWorld is PERFECT for this architecture:")
        print("  ✓ Graph-based (rooms, objects, relationships)")
        print("  ✓ Skill-oriented (named actions)")
        print("  ✓ Multi-step planning (quests)")
        print("  ✓ Episodic memory potential (counterfactuals)")
        print("  ✓ Natural language (interpretable)")
        print("\nNext steps:")
        print("  1. Design Neo4j graph schema for TextWorld")
        print("  2. Create TextWorldCriticalStateAdapter")
        print("  3. Map actions to skills")
        print("  4. Integrate with Critical State Protocols")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
