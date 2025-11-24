
import textworld
import os

def test_textworld_api():
    print("1. Generating game with complex options...")
    options = textworld.GameOptions()
    options.seeds = 42
    options.nb_rooms = 5
    options.nb_objects = 8
    options.quest_length = 5
    
    game = textworld.generator.make_game(options)
    game_file = textworld.generator.compile_game(game)
    print(f"   Game file: {game_file}")

    print("\n2. Starting environment with request_infos...")
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        description=True,
        inventory=True,
        max_score=True,
        won=True,
        lost=True
    )
    env = textworld.start(game_file, request_infos=request_infos)

    print("\n3. Resetting environment...")
    game_state = env.reset()
    print(f"   State type: {type(game_state)}")
    print(f"   Has admissible_commands: {'admissible_commands' in game_state}")
    print(f"   Commands: {game_state.get('admissible_commands')}")

    print("\n4. Stepping 'look'...")
    game_state, reward, done = env.step("look")
    print(f"   State type: {type(game_state)}")
    print(f"   Has admissible_commands: {'admissible_commands' in game_state}")
    print(f"   Commands: {game_state.get('admissible_commands')}")

    print("\n5. Stepping 'inventory'...")
    game_state, reward, done = env.step("inventory")
    print(f"   State type: {type(game_state)}")
    print(f"   Has admissible_commands: {'admissible_commands' in game_state}")
    print(f"   Commands: {game_state.get('admissible_commands')}")

    env.close()
    if os.path.exists(game_file):
        os.remove(game_file)
        os.remove(game_file.replace('.ulx', '.json'))

if __name__ == "__main__":
    test_textworld_api()
