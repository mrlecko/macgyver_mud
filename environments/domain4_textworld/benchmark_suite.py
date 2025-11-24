"""
TextWorld Benchmark Suite

Manages a collection of TextWorld games for systematic agent evaluation.

Generates and maintains a benchmark suite with:
- 5 easy games (3-5 steps, linear)
- 10 medium games (6-8 steps, dependencies)
- 5 hard games (9-12 steps, complex)

Usage:
    from benchmark_suite import TextWorldBenchmarkSuite
    
    suite = TextWorldBenchmarkSuite()
    suite.generate_suite()
    
    all_games = suite.get_all_games()
    # Run your agent on all_games
"""

import os
import json
from typing import Dict, List
from complex_game_generator import create_complex_game, inspect_game


class TextWorldBenchmarkSuite:
    """
    Manages TextWorld benchmark game collection.
    """
    
    def __init__(self, output_dir: str = '/tmp/tw_benchmark'):
        """
        Initialize benchmark suite.
        
        Args:
            output_dir: Where to store generated games and metadata
        """
        self.output_dir = output_dir
        self.metadata_file = f"{output_dir}/benchmark_metadata.json"
        
        self.games = {
            'easy': [],
            'medium': [],
            'hard': []
        }
        
        self.metadata = {
            'easy': [],
            'medium': [],
            'hard': []
        }
    
    def generate_suite(self, force_regenerate: bool = False):
        """
        Generate full benchmark suite.
        
        Args:
            force_regenerate: If True, regenerate even if games exist
        """
        # Check if already generated
        if not force_regenerate and os.path.exists(self.metadata_file):
            print(f"   Loading existing benchmark from {self.metadata_file}")
            self.load_existing()
            return
        
        print(f"   Generating new benchmark suite...")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Easy: 5 games, seeds 100-104
        print(f"   Generating 5 easy games...")
        for seed in range(100, 105):
            game_file = create_complex_game(seed, 'easy', self.output_dir)
            meta = inspect_game(game_file)
            meta['seed'] = seed
            meta['difficulty'] = 'easy'
            meta['file'] = game_file
            
            self.games['easy'].append(game_file)
            self.metadata['easy'].append(meta)
        
        # Medium: 10 games, seeds 200-209
        print(f"   Generating 10 medium games...")
        for seed in range(200, 210):
            game_file = create_complex_game(seed, 'medium', self.output_dir)
            meta = inspect_game(game_file)
            meta['seed'] = seed
            meta['difficulty'] = 'medium'
            meta['file'] = game_file
            
            self.games['medium'].append(game_file)
            self.metadata['medium'].append(meta)
        
        # Hard: 5 games, seeds 300-304
        print(f"   Generating 5 hard games...")
        for seed in range(300, 305):
            game_file = create_complex_game(seed, 'hard', self.output_dir)
            meta = inspect_game(game_file)
            meta['seed'] = seed
            meta['difficulty'] = 'hard'
            meta['file'] = game_file
            
            self.games['hard'].append(game_file)
            self.metadata['hard'].append(meta)
        
        # Save metadata
        self.save_metadata()
        
        print(f"   ✓ Benchmark suite generated:")
        print(f"      Easy: {len(self.games['easy'])} games")
        print(f"      Medium: {len(self.games['medium'])} games")
        print(f"      Hard: {len(self.games['hard'])} games")
    
    def save_metadata(self):
        """Save benchmark metadata to JSON."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def load_existing(self):
        """Load existing benchmark metadata."""
        with open(self.metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        # Reconstruct game lists
        for difficulty in ['easy', 'medium', 'hard']:
            self.games[difficulty] = [
                meta['file'] for meta in self.metadata[difficulty]
            ]
    
    def get_all_games(self) -> List[str]:
        """
        Get flat list of all benchmark games.
        
        Returns:
            List of game file paths
        """
        return (self.games['easy'] + 
                self.games['medium'] + 
                self.games['hard'])
    
    def get_games_by_difficulty(self, difficulty: str) -> List[str]:
        """Get games for specific difficulty level."""
        return self.games.get(difficulty, [])
    
    def print_summary(self):
        """Print benchmark suite summary."""
        print("\n" + "=" * 70)
        print("BENCHMARK SUITE SUMMARY")
        print("=" * 70)
        
        for difficulty in ['easy', 'medium', 'hard']:
            print(f"\n{difficulty.upper()} ({len(self.games[difficulty])} games):")
            for meta in self.metadata[difficulty][:2]:  # Show first 2
                quest_preview = meta['quest'][:50] + "..." if len(meta['quest']) > 50 else meta['quest']
                print(f"  Seed {meta['seed']}: {quest_preview}")
            if len(self.metadata[difficulty]) > 2:
                print(f"  ... and {len(self.metadata[difficulty]) - 2} more")
        
        print("\n" + "=" * 70)
        print(f"Total: {len(self.get_all_games())} games")
        print("=" * 70 + "\n")


# Quick test
if __name__ == "__main__":
    print("Testing Benchmark Suite")
    print("=" * 70)
    
    suite = TextWorldBenchmarkSuite()
    suite.generate_suite()
    suite.print_summary()
    
    print(f"\nAll games ({len(suite.get_all_games())}):")
    for game_file in suite.get_all_games():
        print(f"  - {os.path.basename(game_file)}")
