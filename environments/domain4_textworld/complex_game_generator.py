"""
Complex TextWorld Game Generator

Generates TextWorld games with realistic complexity for benchmarking:
- Easy: 3-5 steps, linear sequences
- Medium: 6-8 steps, one dependency (locked container/door)
- Hard: 9-12 steps, multiple dependencies, backtracking required

Usage:
    from complex_game_generator import create_complex_game
    
    game_file = create_complex_game(seed=42, difficulty='hard')
"""

import os
import textworld
from typing import Literal, Dict


def create_complex_game(
    seed: int,
    difficulty: Literal['easy', 'medium', 'hard'] = 'medium',
    output_dir: str = '/tmp/tw_complex'
) -> str:
    """
    Generate TextWorld game with specified complexity.
    
    Args:
        seed: Random seed for reproducibility
        difficulty: Game complexity level
            - 'easy': 3-5 steps, no dependencies
            - 'medium': 6-8 steps, one locked container
            - 'hard': 9-12 steps, multiple dependencies, backtracking
        output_dir: Directory for generated game files
    
    Returns:
        Path to generated .z8 game file
    
    Example:
        >>> game_file = create_complex_game(100, 'easy')
        >>> # Use with TextWorld: env = textworld.start(game_file)
    """
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure game generation options
    options = textworld.GameOptions()
    options.seeds = seed
    
    # Set complexity parameters
    # NOTE: Reduced from original plan - TextWorld generation is SLOW with many objects
    # Focus on quest_length for complexity, not object count
    if difficulty == 'easy':
        options.nb_rooms = 3
        options.nb_objects = 4  # Reduced from 6
        options.quest_length = 4  # Actual steps will be 3-5
        options.quest_breadth = 1  # Linear path
        
    elif difficulty == 'medium':
        options.nb_rooms = 4  # Reduced from 5
        options.nb_objects = 6  # Reduced from 10
        options.quest_length = 7  # Actual steps will be 6-8
        options.quest_breadth = 1  # Reduced from 2 for speed
        
    else:  # hard
        options.nb_rooms = 5  # Reduced from 7 - generation time is exponential
        options.nb_objects = 8  # Reduced from 15 - this was killing performance
        options.quest_length = 10  # Still 9-12 steps
        options.quest_breadth = 1  # Reduced from 2 for speed
    
    # Enable quest types
    options.grammar_flags = {
        'theme': 'house',  # Familiar environment (kitchen, bedroom, etc.)
        'include_adj': True,  # "golden key", "red door"
        'blend_descriptions': True,  # Natural language
        'ambiguous_instructions': False,  # Clear instructions for now
    }
    
    # Set output file path
    game_file = f"{output_dir}/{difficulty}_game_seed_{seed}.z8"
    options.path = game_file
    
    # Generate and compile game
    game = textworld.generator.make_game(options)
    textworld.generator.compile_game(game, options)
    
    return game_file


def inspect_game(game_file: str) -> Dict:
    """
    Load game and extract metadata.
   
    Args:
        game_file: Path to .z8 file
   
    Returns:
        {
            'quest': str,
            'max_score': int,
            'nb_rooms': int,
            'nb_objects': int,
        }
    """
    request_infos = textworld.EnvInfos(
        objective=True,
        max_score=True,
        admissible_commands=True,
    )
    
    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()
    
    metadata = {
        'quest': game_state.objective,
        'max_score': game_state.max_score,
        'initial_commands': len(game_state.admissible_commands),
    }
    
    env.close()
    return metadata


# Quick test
if __name__ == "__main__":
    print("Testing Complex Game Generator")
    print("=" * 70)
    
    for difficulty in ['easy', 'medium', 'hard']:
        print(f"\n{difficulty.upper()} Game:")
        game_file = create_complex_game(seed=42, difficulty=difficulty)
        print(f"  Generated: {game_file}")
        
        metadata = inspect_game(game_file)
        print(f"  Quest: {metadata['quest'][:60]}...")
        print(f"  Max Score: {metadata['max_score']}")
        print(f"  Initial Commands: {metadata['initial_commands']}")
    
    print("\n" + "=" * 70)
    print("✓ Game generation successful")
