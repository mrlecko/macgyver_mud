"""
TextWorld adapter for Critical State Protocol integration.

This adapter bridges TextWorld (interactive fiction) with the MacGyver MUD
cognitive architecture, enabling:
1. Graph-based knowledge representation (Neo4j)
2. Skill-based action mapping
3. Critical state detection
4. Episodic memory integration

Iteration 1: Basic adapter with game generation and reset.
Iteration 2: Neo4j graph integration for world representation.
Iteration 3: AgentState conversion for critical monitoring.
"""
import textworld
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass
from neo4j import Session
from environments.domain4_textworld.graph_schema import TextWorldGraphSchema


@dataclass
class TextWorldState:
    """State representation for TextWorld environment."""
    step: int
    feedback: str
    score: float
    max_score: Optional[float]
    won: bool
    lost: bool


class TextWorldAdapter:
    """
    Adapter for TextWorld environment.
    
    This class manages TextWorld games and provides an interface compatible
    with the MacGyver MUD agent framework.
    
    Attributes:
        session: Neo4j session for graph storage
        game: Current TextWorld game object
        env: TextWorld environment handle
        current_state: Current game state
    """
    
    def __init__(self, session: Session, game_options=None):
        """
        Initialize adapter with Neo4j session.
        
        Args:
            session: Active Neo4j session
            game_options: Optional TextWorld GameOptions for customization
        """
        self.session = session
        self.game = None
        self.env = None
        self.current_state = None
        self.game_file = None
        
        # Initialize graph schema
        self.schema = TextWorldGraphSchema(session)
        self.schema.initialize_schema()
        
        # Default game options if not provided
        if game_options is None:
            game_options = textworld.GameOptions()
            game_options.nb_rooms = 5        # 5 rooms
            game_options.nb_objects = 8       # 8 objects
            game_options.quest_length = 5     # 5-step quest
        
        self.game_options = game_options
        
        # Create scratch directory for game files
        os.makedirs("./scratch/textworld_games", exist_ok=True)
    
    def generate_game(self, seed=None):
        """
        Generate a new TextWorld game.
        
        Args:
            seed: Random seed for reproducibility
        
        Returns:
            Path to compiled game file
        """
        if seed is not None:
            self.game_options.seeds = seed
        
        # Generate game
        self.game = textworld.generator.make_game(self.game_options)
        
        # Store game world in Neo4j
        self.schema.store_game_world(self.game)
        
        # Compile to playable file
        compiled_path = textworld.generator.compile_game(self.game)
        
        # Move to our scratch directory
        import shutil
        target_path = f"./scratch/textworld_games/game_{seed or 'default'}.ulx"
        if os.path.exists(compiled_path):
            shutil.move(compiled_path, target_path)
            
            # Also move the corresponding .json file if it exists
            # This is CRITICAL for admissible_commands to work!
            json_path = compiled_path.replace('.ulx', '.json')
            target_json_path = target_path.replace('.ulx', '.json')
            if os.path.exists(json_path):
                shutil.move(json_path, target_json_path)
                
            self.game_file = target_path
        else:
            self.game_file = compiled_path
        
        # Start new environment after game generation
        # Request admissible commands from TextWorld
        if self.env is not None:
            self.env.close()
        
        # Configure what info we want from TextWorld
        request_infos = textworld.EnvInfos(
            admissible_commands=True,  # Get valid commands
            description=True,           # Get room descriptions
            inventory=True,             # Get inventory
            max_score=True,             # Get quest score info
            won=True,                   # Check if won
            lost=True                   # Check if lost
        )
        
        self.env = textworld.start(self.game_file, request_infos=request_infos)
        
        return self.game_file
    
    def reset(self) -> TextWorldState:
        """
        Reset the environment to initial state.
        
        Returns:
            Initial AgentState
        """
        if not self.env:
            # If env is not initialized, try to generate a game first
            if self.game_file is None or not os.path.exists(self.game_file):
                self.generate_game()
            else:
                # If game_file exists but env is not started, start it
                request_infos = textworld.EnvInfos(
                    admissible_commands=True,
                    description=True,
                    inventory=True,
                    max_score=True,
                    won=True,
                    lost=True
                )
                self.env = textworld.start(self.game_file, request_infos=request_infos)
        
        # Reset environment and get initial state  
        # TextWorld returns a GameState object (dict-like)
        game_state = self.env.reset()
        
        # Store the full game state for command access
        self._current_infos = game_state
        
        # Create state
        self.current_state = TextWorldState(
            step=0,
            feedback=game_state.get('feedback', '') or '',
            score=game_state.get('score', 0),
            max_score=game_state.get('max_score', None),
            won=game_state.get('won', False),
            lost=game_state.get('lost', False)
        )
        
        # Initialize state tracking for Iteration 3+
        self.action_history = []
        self.observation_history = [self.current_state.feedback if self.current_state.feedback else ""]
        self.reward_history = []
        self.current_step = 0
        self.max_steps = 100  # Default episode limit
        
        return self.current_state
    
    def step(self, action: str) -> Tuple[TextWorldState, float, bool]:
        """
        Execute action in environment.
        
        Args:
            action: Command to execute
            
        Returns:
            Tuple of (new_state, reward, done)
        """
        if not self.env:
            raise ValueError("Must generate game and reset first")
        
        # Execute action - TextWorld returns (game_state, reward, done)
        # where game_state is a GameState dict
        game_state, reward, done = self.env.step(action)
        
        # Store the full game state for command access
        self._current_infos = game_state
        
        # Track action
        self.action_history.append(action)
        self.observation_history.append(game_state.get('feedback', '') or '')
        self.reward_history.append(reward)
        
        # Create new state
        prev_score = self.current_state.score if self.current_state else 0
        self.current_state = TextWorldState(
            step=self.current_state.step + 1 if self.current_state else 0,
            feedback=game_state.get('feedback', '') or '',
            score=game_state.get('score', prev_score),
            max_score=game_state.get('max_score', None),
            won=game_state.get('won', False),
            lost=game_state.get('lost', False)
        )
        
        return self.current_state, reward, done
    
    def get_admissible_commands(self) -> Optional[List[str]]:
        """
        Get list of valid commands in current state.
        
        Returns:
            List of admissible command strings, or None if not available
        """
        if not hasattr(self, '_current_infos') or not self._current_infos:
            return None
        
        # Get commands from GameState dict
        commands = self._current_infos.get('admissible_commands', [])
        
        return list(commands) if commands else None
    
    def calculate_entropy(self):
        """
        Calculate uncertainty/entropy from game state.
        
        Higher entropy indicates:
        - More available actions (confusion)
        - Less progress toward goal
        - More uncertainty
        
        Returns:
            Float in [0, 1] representing entropy
        """
        if self.current_state is None:
            return 0.0
        
        # Number of available actions (more = higher entropy)
        commands = self.get_admissible_commands()
        num_actions = len(commands)
        action_entropy = min(1.0, num_actions / 20.0)  # Normalize (assume max ~20 actions)
        
        # Progress toward goal (less progress = higher entropy)
        max_score = self.current_state.max_score if self.current_state.max_score else 1
        current_score = self.current_state.score if self.current_state.score else 0
        progress = current_score / max(max_score, 1)
        progress_entropy = 1.0 - progress
        
        # Inventory size (fewer items = higher entropy, haven't learned about world)
        if hasattr(self.current_state, 'inventory') and self.current_state.inventory:
            inv_size = len(list(self.current_state.inventory))
        else:
            inv_size = 0
        inv_entropy = max(0.0, 1.0 - inv_size / 5.0)  # Assume ~5 items max
        
        # Weighted combination
        entropy = (
            0.4 * action_entropy +
            0.4 * progress_entropy +
            0.2 * inv_entropy
        )
        
        return min(1.0, max(0.0, entropy))
    
    def calculate_distance_to_goal(self):
        """
        Estimate distance to goal based on score progress.
        
        Lower score = further from goal.
        
        Returns:
            Float representing estimated distance
        """
        if self.current_state is None:
            return 20.0  # Default high distance
        
        max_score = self.current_state.max_score if self.current_state.max_score else 1
        current_score = self.current_state.score if self.current_state.score else 0
        
        # Distance = (max - current) scaled to reasonable range
        remaining_score = max_score - current_score
        distance = (remaining_score / max(max_score, 1)) * 20
        
        return distance
    
    def calculate_prediction_error(self):
        """
        Calculate how unexpected the last state transition was.
        
        Higher error = more surprising transition.
        
        Returns:
            Float in [0, 1] representing prediction error
        """
        if len(self.observation_history) < 2:
            return 0.0
        
        prev_obs = self.observation_history[-2]
        curr_obs = self.observation_history[-1]
        
        # Simple text similarity check
        prev_words = set(prev_obs.split())
        curr_words = set(curr_obs.split())
        
        if not prev_words and not curr_words:
            return 0.0
        
        common_words = prev_words & curr_words
        total_words = prev_words | curr_words
        
        similarity = len(common_words) / max(len(total_words), 1)
        prediction_error = 1.0 - similarity
        
        return min(1.0, max(0.0, prediction_error))
    
    def get_agent_state(self):
        """
        Convert TextWorld state to AgentState for critical monitoring.
        
        This is the key integration point with Critical State Protocols.
        
        Returns:
            AgentState object with all required metrics
        """
        from critical_state import AgentState
        
        entropy = self.calculate_entropy()
        distance = self.calculate_distance_to_goal()
        prediction_error = self.calculate_prediction_error()
        
        agent_state = AgentState(
            entropy=entropy,
            history=self.action_history[-10:],  # Last 10 actions
            steps=self.max_steps - self.current_step,  # Steps remaining
            dist=distance,
            rewards=self.reward_history[-10:],  # Last 10 rewards
            error=prediction_error
        )
        
        return agent_state
    
    def close(self):
        """Clean up resources."""
        if self.env is not None:
            self.env.close()
            self.env = None
