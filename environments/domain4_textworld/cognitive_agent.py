"""
print("DEBUG: Importing cognitive_agent module")
TextWorld Cognitive Agent - Active Inference Implementation.

This agent uses the bicameral architecture:
- Cortex: Active inference decision-making
- Brainstem: Critical state monitoring (added later)
- Hippocampus: Episodic memory (added later)

TDD Iteration 1: Minimal viable agent
- Belief state management
- Basic action selection

Logging Convention:
🧠 Brain/Agent state
📊 Beliefs/Knowledge
🎯 Goals/Quests
🔍 Observations
⚡ Actions
💭 Reasoning/Scoring
✅ Success
❌ Failure
⚠️  Warning
🔄 Updates
"""
from typing import Dict, List, Any, Optional
from neo4j import Session
import logging

# Configure logger
logger = logging.getLogger(__name__)


from environments.domain4_textworld.text_parser import TextWorldParser

class TextWorldCognitiveAgent:
    """
    Cognitive agent for TextWorld using active inference.
    """
    
    def __init__(self, session: Session, verbose: bool = True):
        """
        Initialize cognitive agent.
        """
        self.session = session
        self.verbose = verbose
        
        # Components
        self.parser = TextWorldParser()
        # Import here to avoid circular imports if any
        from .memory_system import MemoryRetriever
        self.memory = MemoryRetriever(session)
        
        # Belief state: Agent's internal model of the world
        self.beliefs = {
            'rooms': {},           # room_name -> {description, objects, connections}
            'objects': {},         # object_name -> {location, properties}
            'inventory': [],       # Objects currently held
            'current_room': None,  # Where agent is now
            'quest_state': {},     # Progress toward goals
            'uncertainty': {}      # Confidence in each belief
        }
        
        if self.verbose:
            print("\n" + "="*70)
            print("🧠 COGNITIVE AGENT INITIALIZATION")
            print("="*70)
        
            print("📊 Belief state initialized:")
            print(f"   - Rooms: {len(self.beliefs['rooms'])}")
            print(f"   - Objects: {len(self.beliefs['objects'])}")
            print(f"   - Inventory: {len(self.beliefs['inventory'])}")
        
        # Episode state
        self.current_step = 0
        self.max_steps = 100
        self.done = False
        
        # History for learning
        self.observation_history = []
        self.action_history = []
        self.reward_history = []
        
        if self.verbose:
            print("✅ Agent ready")
            print("="*70 + "\n")
    
    def reset(self):
        """Reset agent for new episode."""
        if self.verbose:
            print("\n" + "="*70)
            print("🔄 EPISODE RESET")
            print("="*70)
        
        self.beliefs = {
            'rooms': {},
            'objects': {},
            'inventory': [],
            'current_room': None,
            'quest_state': {},
            'uncertainty': {}
        }
        self.current_step = 0
        self.done = False
        self.observation_history = []
        self.action_history = []
        self.reward_history = []
        
        if self.verbose:
            print("📊 State cleared")
            print("✅ Ready for new episode")
            print("="*70 + "\n")
    
    def update_beliefs(self, observation: str, feedback: str = ""):
        """
        Update beliefs from text observation.
        
        Uses TextWorldParser to extract structured data.
        
        Args:
            observation: Text description of current state
            feedback: Response from last action
        """
        # Convert observation to string if it's a dict
        if isinstance(observation, dict):
            observation = observation.get('feedback', '') or str(observation)
        obs_str = str(observation)
        
        if self.verbose:
            print(f"\n🔍 OBSERVATION (Step {self.current_step}):")
            print(f"   {obs_str[:100]}{'...' if len(obs_str) > 100 else ''}")
            if feedback:
                feedback_str = str(feedback)
                print(f"   Feedback: {feedback_str[:80]}{'...' if len(feedback_str) > 80 else ''}")
        
        # Store raw observation
        self.observation_history.append({
            'step': self.current_step,
            'observation': obs_str,
            'feedback': feedback
        })
        
        # 1. Extract Room Name
        room_name = self.parser.extract_room_name(obs_str)
        if room_name:
            self.beliefs['current_room'] = room_name
            if room_name not in self.beliefs['rooms']:
                self.beliefs['rooms'][room_name] = {
                    'description': obs_str,
                    'objects': [],
                    'connections': [],
                    'visited_count': 1
                }
            else:
                # Update description and count
                self.beliefs['rooms'][room_name]['description'] = obs_str
                self.beliefs['rooms'][room_name]['visited_count'] = self.beliefs['rooms'][room_name].get('visited_count', 0) + 1
                
        # 2. Extract Visible Objects
        visible_objects = self.parser.extract_visible_objects(obs_str)
        if visible_objects and self.beliefs['current_room']:
            current_room = self.beliefs['current_room']
            self.beliefs['rooms'][current_room]['objects'] = visible_objects
            
            # Update object registry
            for obj in visible_objects:
                if obj not in self.beliefs['objects']:
                    self.beliefs['objects'][obj] = {'location': current_room, 'examined_count': 0}
                else:
                    self.beliefs['objects'][obj]['location'] = current_room
                
        # 3. Extract Inventory
        # Check both observation and feedback for inventory info
        inventory_items = self.parser.extract_inventory(obs_str)
        if not inventory_items and feedback:
            inventory_items = self.parser.extract_inventory(feedback)
            
        if inventory_items:
            self.beliefs['inventory'] = inventory_items
            for item in inventory_items:
                if item not in self.beliefs['objects']:
                    self.beliefs['objects'][item] = {'location': 'inventory', 'examined_count': 0}
                else:
                    self.beliefs['objects'][item]['location'] = 'inventory'
        elif "You are carrying nothing" in obs_str or (feedback and "You are carrying nothing" in feedback):
            self.beliefs['inventory'] = []

        # Track examined objects based on last action
        if self.action_history:
            last_action = self.action_history[-1]['action']
            if last_action.startswith('examine '):
                target_obj = last_action.replace('examine ', '').strip()
                if target_obj in self.beliefs['objects']:
                    self.beliefs['objects'][target_obj]['examined_count'] = self.beliefs['objects'][target_obj].get('examined_count', 0) + 1

        self.current_step += 1
        
        if self.verbose:
            print(f"📊 Beliefs updated (step → {self.current_step})")
            if room_name:
                count = self.beliefs['rooms'][room_name].get('visited_count', 1)
                print(f"   📍 Room: {room_name} (visited: {count})")
            if visible_objects:
                print(f"   👁️  Objects: {visible_objects}")
            if self.beliefs['inventory']:
                print(f"   🎒 Inventory: {self.beliefs['inventory']}")
    
    def calculate_cost(self, action: str) -> float:
        """
        Calculate cost (habit/repetition penalty).
        Higher cost = bad.
        """
        cost = 1.0  # Base cost
        
        if not self.action_history:
            return cost
            
        # 1. Immediate repetition penalty
        last_action = self.action_history[-1]['action']
        if action == last_action:
            cost += 5.0
            
        # 2. Loop detection (A -> B -> A)
        # If we just moved, and now we're moving back?
        # Hard to know exactly without map, but we can check history
        if len(self.action_history) >= 2:
            prev_action = self.action_history[-2]['action']
            # Simple inverse detection
            opposites = {
                'north': 'south', 'south': 'north',
                'east': 'west', 'west': 'east'
            }
            for d, op in opposites.items():
                if f"go {d}" in prev_action and f"go {op}" in action:
                    cost += 3.0  # Penalty for immediate backtracking
                    
        # 3. Frequency penalty (boredom)
        # Count how many times we've done this recently
        recent_actions = [x['action'] for x in self.action_history[-10:]]
        count = recent_actions.count(action)
        cost += count * 0.5
        
        return cost

    def calculate_entropy(self, action: str) -> float:
        """
        Calculate entropy (information gain potential).
        Higher entropy = good (explore).
        """
        entropy = 0.5  # Base entropy
        
        # 1. Examine unknown objects
        if action.startswith('examine '):
            target = action.replace('examine ', '').strip()
            if target in self.beliefs['objects']:
                count = self.beliefs['objects'][target].get('examined_count', 0)
                if count == 0:
                    entropy += 2.0  # High value for new objects
                else:
                    entropy -= 0.2 * count  # Diminishing returns
        
        # 2. Look is generally good if we haven't just done it
        if action == 'look':
            entropy += 0.5
            
        # 3. Inventory check
        if action == 'inventory':
            entropy += 0.2
            
        return entropy

    def calculate_goal_value(self, action: str) -> float:
        """
        Calculate goal value (pragmatic value).
        Higher value = good.
        """
        value = 0.5  # Base value
        
        # 1. Taking items is usually good
        if action.startswith('take ') or action.startswith('get '):
            value += 2.0
            
        # 2. Opening things
        if action.startswith('open '):
            value += 1.5
            
        # 3. Eating (if food) - simple heuristic
        if action.startswith('eat '):
            value += 1.0
            
        return value

    def calculate_memory_bonus(self, action: str) -> float:
        """
        Calculate score adjustment based on past memories.
        Positive outcome -> Bonus
        Negative outcome -> Penalty
        """
        if not self.beliefs.get('current_room'):
            return 0.0
            
        context = self.beliefs['rooms'][self.beliefs['current_room']].get('description', '')
        memories = self.memory.retrieve_relevant_memories(context, action)
        
        bonus = 0.0
        for mem in memories:
            confidence = mem.get('confidence', 0.5)
            if mem['outcome'] == 'positive':
                bonus += 2.0 * confidence
            elif mem['outcome'] == 'negative':
                bonus -= 5.0 * confidence  # Stronger penalty for bad outcomes
                
        return bonus

    def score_action(self, action: str, beliefs: Dict, quest: Optional[Dict] = None) -> float:
        """
        Score an action using Active Inference EFE.
        
        EFE = α * goal_value + β * entropy - γ * cost + δ * memory
        """
        # Coefficients
        alpha = 2.0  # Goal value weight
        beta = 3.0   # Entropy/Info weight (Encourage exploration)
        gamma = 1.0  # Cost weight
        delta = 1.0  # Memory weight
        
        goal_val = self.calculate_goal_value(action)
        entropy = self.calculate_entropy(action)
        cost = self.calculate_cost(action)
        memory_bonus = self.calculate_memory_bonus(action)
        
        efe = (alpha * goal_val) + (beta * entropy) - (gamma * cost) + (delta * memory_bonus)
        
        return efe
    
    def select_action(self, admissible_commands: List[str], quest: Optional[Dict] = None) -> str:
        """
        Select best action from available commands.
        
        Args:
            admissible_commands: List of valid commands
            quest: Optional quest information
        
        Returns:
            Selected command
        """
        if not admissible_commands:
            if self.verbose:
                print("⚠️  No commands available, using fallback")
            return "look"  # Default fallback
        
        if self.verbose:
            print(f"\n💭 DECISION-MAKING:")
            print(f"   Available actions: {len(admissible_commands)}")
        
        # Score all actions
        scored_actions = []
        for action in admissible_commands:
            score = self.score_action(action, self.beliefs, quest)
            scored_actions.append((score, action))
            
            if self.verbose and len(admissible_commands) <= 10:  # Only show if not too many
                print(f"      {score:6.2f} → {action}")
        
        # Pick highest score
        scored_actions.sort(reverse=True)
        best_score, best_action = scored_actions[0]
        
        if self.verbose:
            print(f"\n   ⚡ SELECTED: '{best_action}' (score: {best_score:.2f})")
        
        # Track decision
        self.action_history.append({
            'step': self.current_step,
            'action': best_action,
            'score': best_score
        })
        
        return best_action
    
    def check_critical_state(self) -> bool:
        """
        Check if agent is in a critical state (stuck, loop, danger).
        """
        # 1. Stuck detection: No reward for N steps
        stuck_threshold = 15
        if len(self.reward_history) >= stuck_threshold:
            recent_rewards = self.reward_history[-stuck_threshold:]
            if sum(recent_rewards) == 0:
                if self.verbose:
                    print("⚠️  CRITICAL STATE: Stuck (no reward recently)")
                return True
                
        # 2. Loop detection (already handled by cost, but could trigger panic here)
        
        return False

    def save_episode(self):
        """
        Save the current episode to Neo4j Episodic Memory.
        """
        if not self.session:
            return
            
        if self.verbose:
            print("💾 Saving episode to memory...")
            
        # Create Episode node
        query = """
        CREATE (e:Episode {
            timestamp: timestamp(),
            steps: $steps,
            total_reward: $total_reward,
            final_room: $final_room,
            success: $success
        })
        RETURN id(e) as episode_id
        """
        
        total_reward = sum(self.reward_history)
        final_room = self.beliefs.get('current_room', 'Unknown')
        success = total_reward > 0  # Simple success metric for now
        
        result = self.session.run(query, {
            'steps': self.current_step,
            'total_reward': total_reward,
            'final_room': final_room,
            'success': success
        })
        episode_id = result.single()['episode_id']
        
        # We could save individual steps here, but for now just the summary
        # is enough to prove the concept.
        
        if self.verbose:
            print(f"   ✅ Episode saved (ID: {episode_id})")

    def step(self, observation: str, feedback: str, reward: float, done: bool, 
             admissible_commands: List[str], quest: Optional[Dict] = None) -> str:
        """
        Execute one step of the agent.
        
        Args:
            observation: Current state description
            feedback: Response from last action
            reward: Reward received
            done: Episode finished?
            admissible_commands: Available actions
            quest: Quest information
        
        Returns:
            Selected action
        """
        if self.verbose:
            print("\n" + "-"*70)
            print(f"🔄 STEP {self.current_step}")
            print("-"*70)
        
        # Update beliefs from observation
        self.update_beliefs(observation, feedback)
        
        # Track reward
        self.reward_history.append(reward)
        if self.verbose and reward != 0:
            print(f"   🎁 Reward: {reward:+.1f}")
        
        # Check critical state
        is_critical = self.check_critical_state()
        if is_critical:
            # TODO: Trigger PANIC protocol or strategy shift
            # For now, just logging it
            pass
            
        # Update done status
        self.done = done
        if self.verbose and done:
            print(f"   ✅ Episode complete!")
            self.save_episode()
        
        # Select next action
        action = self.select_action(admissible_commands, quest)
        
        if self.verbose:
            print("-"*70)
        
        return action
