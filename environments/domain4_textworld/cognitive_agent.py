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
import time

# Configure logger
logger = logging.getLogger(__name__)


from environments.domain4_textworld.text_parser import TextWorldParser
from critical_state import CriticalStateMonitor, CriticalState, AgentState
from environments.domain4_textworld.plan import Plan, PlanStep, PlanStatus
from environments.domain4_textworld.quest_decomposer import QuestDecomposer

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
        from .llm_planner import LLMPlanner
        self.memory = MemoryRetriever(session)
        self.planner = LLMPlanner(verbose=verbose)  # Now uses real LLM
        self.critical_monitor = CriticalStateMonitor()  # Critical state protocol system
        self.quest_decomposer = QuestDecomposer()  # NEW: Quest decomposition for hierarchical synthesis
        
        # Belief state: Agent's internal model of the world
        self.beliefs = {
            'rooms': {},           # room_name -> {description, objects, connections}
            'objects': {},         # object_name -> {location, properties}
            'inventory': [],       # Objects currently held
            'current_room': None,  # Where agent is now
            'quest_state': {},     # Progress toward goals
            'uncertainty': {}      # Confidence in each belief
        }

        # Planning state
        self.current_plan: Optional[Plan] = None  # Active hierarchical plan
        self.plan_history = []  # Completed/failed plans for learning

        # Quest decomposition state (NEW: for hierarchical synthesis)
        self.subgoals = []  # List of subgoal strings (ordered)
        self.current_subgoal_index = 0  # Which subgoal we're working on (0-indexed)
        self.last_quest = None  # Full quest text for reference
        
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
        self.location_history = []  # Track room transitions for deadlock detection

        # Critical state tracking
        self.current_critical_state = CriticalState.FLOW
        self.distance_to_goal = 20.0  # Estimated distance (updated dynamically)
        
        if self.verbose:
            print("✅ Agent ready")
            print("="*70 + "\n")
    
    def reset(self, quest: str = None):
        """
        Reset agent for new episode.

        Args:
            quest: Optional quest description to decompose into subgoals.
                   If provided, enables hierarchical goal-directed behavior.
        """
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
        self.location_history = []
        self.current_critical_state = CriticalState.FLOW
        self.distance_to_goal = 20.0

        # NEW: Decompose quest into subgoals (hierarchical synthesis)
        if quest:
            self.last_quest = quest
            self.subgoals = self.quest_decomposer.decompose(quest)
            self.current_subgoal_index = 0

            if self.verbose:
                print("📋 Quest decomposed:")
                for i, sg in enumerate(self.subgoals, 1):
                    print(f"   {i}. {sg}")
                print()
        else:
            # No quest provided, use reactive behavior
            self.subgoals = []
            self.current_subgoal_index = 0
            self.last_quest = None

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
            # Track location for deadlock detection
            self.location_history.append(room_name)

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

    def calculate_goal_value(self, action: str, current_subgoal: str = None) -> float:
        """
        Calculate goal value (pragmatic value).
        Higher value = good.

        NOW HIERARCHICAL (Option A - Synthesis):
        1. Current subgoal match (HIGHEST priority) - NEW
        2. Overall quest match (MEDIUM priority)
        3. Generic heuristics (LOW priority)

        Args:
            action: Action to evaluate
            current_subgoal: Current subgoal string (if available)

        Returns:
            Goal value score
        """
        value = 0.5  # Base value

        # PRIORITY 1: Current subgoal match (NEW - HIERARCHICAL SYNTHESIS)
        # CRITICAL FIX: When we have a subgoal, use ONLY subgoal matching, not quest matching
        # Otherwise quest-level tokens interfere with hierarchical decisions
        has_subgoal_match = False
        if current_subgoal:
            subgoal_tokens = set(current_subgoal.lower().split())
            action_tokens = set(action.lower().split())
            stopwords = {'the', 'a', 'an', 'from', 'into', 'on', 'in', 'to', 'of'}

            subgoal_tokens_clean = subgoal_tokens - stopwords
            action_tokens_clean = action_tokens - stopwords

            overlap = len(subgoal_tokens_clean & action_tokens_clean)

            if overlap > 0:
                # HUGE bonus for subgoal match (15.0 per overlapping token)
                # This is the KEY to hierarchical synthesis!
                value += 15.0 * (overlap / max(len(subgoal_tokens_clean), 1))
                has_subgoal_match = True  # Mark that we used subgoal matching

        # PRIORITY 2: Overall quest match (ONLY if no subgoal context)
        # When we have a subgoal, we should focus on it exclusively
        if not has_subgoal_match and hasattr(self, 'last_quest') and self.last_quest:
            quest_lower = self.last_quest.lower()
            action_lower = action.lower()

            # Extract action words (verbs and objects)
            action_words = set(action_lower.split())
            quest_words = set(quest_lower.split())

            # Calculate overlap
            common_words = action_words & quest_words

            # Remove common words like 'the', 'a', 'from', 'into'
            stopwords = {'the', 'a', 'an', 'from', 'into', 'on', 'in', 'to', 'of'}
            meaningful_common = common_words - stopwords

            if meaningful_common:
                # MEDIUM bonus (reduced from 10.0 to avoid conflict with subgoal)
                value += 5.0 * len(meaningful_common)

        # PRIORITY 3: Generic action bonuses (much weaker now)
        # Taking items is usually good (but quest-relevance is better)
        if action.startswith('take ') or action.startswith('get '):
            value += 1.0  # Small bonus

        # Opening things
        if action.startswith('open '):
            value += 0.8

        # Eating (if food) - simple heuristic
        if action.startswith('eat '):
            value += 0.5

        return value

    def calculate_memory_bonus(self, action: str) -> float:
        """
        Calculate score adjustment based on past memories.
        Positive outcome -> Bonus
        Negative outcome -> Penalty

        Returns:
            Float score adjustment (can be positive or negative)
        """
        # Defensive: Check if current_room exists and is in rooms dict
        if not self.beliefs.get('current_room'):
            return 0.0

        current_room = self.beliefs['current_room']
        if current_room not in self.beliefs.get('rooms', {}):
            # Room reference exists but room data not yet populated
            return 0.0

        context = self.beliefs['rooms'][current_room].get('description', '')
        if not context:
            # No context available for memory retrieval
            return 0.0

        try:
            memories = self.memory.retrieve_relevant_memories(context, action)
        except Exception as e:
            # Memory retrieval failed - log but don't crash
            if self.verbose:
                print(f"⚠️  Memory retrieval error: {e}")
            return 0.0

        bonus = 0.0
        for mem in memories:
            confidence = mem.get('confidence', 0.5)
            outcome = mem.get('outcome', 'neutral')

            if outcome == 'positive':
                bonus += 2.0 * confidence
            elif outcome == 'negative':
                bonus -= 5.0 * confidence  # Stronger penalty for bad outcomes

        return bonus

    def _infer_goal_from_context(self) -> Optional[str]:
        """
        Infer high-level goal from current context.

        Uses quest state or observation heuristics.
        
        Priority order:
        1. quest_state.description (if set via step() call)
        2. last_quest attribute (if set from TextWorld game state)
        3. Heuristics from observations (fallback)
        """
        # Strategy 1: Check quest state (if populated)
        if self.beliefs.get('quest_state') and self.beliefs['quest_state'].get('description'):
            return self.beliefs['quest_state']['description']
        
        # Strategy 2: Check last_quest attribute (TextWorld game state objective)
        if hasattr(self, 'last_quest') and self.last_quest:
            return self.last_quest

        # Strategy 3: Simple heuristics based on recent observations (fallback)
        if not self.observation_history:
            return None

        recent_obs = self.observation_history[-1]
        obs_text = recent_obs.get('observation', '').lower()

        # Look for common goal patterns
        if 'locked' in obs_text and 'chest' in obs_text:
            return "Find key and unlock the chest"
        elif 'locked' in obs_text and 'door' in obs_text:
            return "Find key and unlock the door"
        elif 'hungry' in obs_text or 'need' in obs_text:
            return "Find and consume food"
        elif 'escape' in obs_text:
            return "Escape the room"

        # No clear goal detected
        return None

    def _build_planning_context(self, admissible_commands: List[str]) -> str:
        """Build context summary for planning."""
        parts = []

        # Current location
        if self.beliefs.get('current_room'):
            parts.append(f"Current Room: {self.beliefs['current_room']}")

        # Visible objects
        current_room = self.beliefs.get('current_room')
        if current_room and current_room in self.beliefs.get('rooms', {}):
            objects = self.beliefs['rooms'][current_room].get('objects', [])
            if objects:
                parts.append(f"Visible Objects: {', '.join(objects[:10])}")  # Max 10

        # Inventory
        inventory = self.beliefs.get('inventory', [])
        if inventory:
            parts.append(f"Inventory: {', '.join(inventory)}")
        else:
            parts.append("Inventory: empty")

        # Available actions (sample)
        if admissible_commands:
            sample = admissible_commands[:8]  # First 8 actions
            parts.append(f"Available Actions: {', '.join(sample)}")
            if len(admissible_commands) > 8:
                parts.append(f"... and {len(admissible_commands) - 8} more")

        return "\n".join(parts)

    def _get_recent_failures(self) -> List[str]:
        """Get recent failed plans for learning."""
        failures = []
        for plan in self.plan_history[-3:]:  # Last 3 plans
            if plan.status == PlanStatus.FAILED:
                reason = plan.failure_reason or "unknown reason"
                failures.append(f"Tried '{plan.goal}' - {reason}")
        return failures

    def maybe_generate_plan(self, admissible_commands: List[str]):
        """
        Generate a new plan if we don't have one and a goal is clear.

        Only generates when:
        - No active plan exists
        - A goal can be inferred from context
        - We have enough steps accumulated to make planning worthwhile
        """
        # Only generate if no active plan
        if self.current_plan and self.current_plan.status == PlanStatus.ACTIVE:
            return

        # Don't plan too early (need some observations first)
        if self.current_step < 3:
            return

        # Infer goal from context
        goal = self._infer_goal_from_context()
        if not goal:
            return  # No clear goal, use reactive EFE only

        # Build context summary
        context = self._build_planning_context(admissible_commands)

        # Get previous failures if any
        failures = self._get_recent_failures()

        # Generate plan
        if self.verbose:
            print(f"\n📋 Generating plan for: {goal}")

        try:
            self.current_plan = self.planner.generate_plan(
                goal=goal,
                context=context,
                previous_failures=failures
            )
            self.current_plan.created_at_step = self.current_step

            if self.verbose:
                print(f"   Strategy: {self.current_plan.strategy[:80]}...")
                print(f"   Steps: {len(self.current_plan.steps)}")
                for i, step in enumerate(self.current_plan.steps, 1):
                    print(f"     {i}. {step.description}")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Plan generation failed: {e}")
            # Continue without plan (use reactive EFE)

    def check_plan_progress(self, last_action: str):
        """
        Check if last action completed a plan step.

        Tracks progress through the current plan and handles completion.
        """
        if not self.current_plan:
            return

        # Try to advance the plan
        if self.current_plan.advance_step(last_action):
            if self.verbose:
                print(f"   ✅ Plan step completed!")
                print(f"   Progress: {self.current_plan.progress_ratio():.0%}")

            next_step = self.current_plan.get_current_step()
            if next_step:
                if self.verbose:
                    print(f"   Next: {next_step.description}")
            else:
                if self.verbose:
                    print(f"   🎉 Plan complete!")

        # Check if plan is complete
        if self.current_plan.is_complete():
            self.current_plan.status = PlanStatus.COMPLETED
            self.current_plan.completed_at_step = self.current_step
            self.plan_history.append(self.current_plan)
            if self.verbose:
                print(f"   🎯 Goal '{self.current_plan.goal}' achieved!")
            self.current_plan = None

    def calculate_plan_bonus(self, action: str) -> float:
        """
        Calculate score adjustment based on the current plan.

        Big bonus if action matches current step.
        Uses new Plan API with step matching.
        """
        if not self.current_plan:
            return 0.0

        current_step = self.current_plan.get_current_step()
        if not current_step:
            return 0.0  # Plan complete

        # Check if action matches current step
        if current_step.matches_action(action):
            # Big bonus for following the plan
            bonus = 10.0

            # Extra bonus if this is a fresh step (no retries)
            if current_step.attempts == 0:
                bonus += 2.0

            return bonus

        # Small penalty for diverging from plan
        return -1.0

    def score_action(self, action: str, beliefs: Dict, quest: Optional[Dict] = None,
                    current_subgoal: str = None) -> float:
        """
        Score an action using Active Inference EFE (Expected Free Energy).

        EFE = α * goal_value + β * entropy - γ * cost + δ * memory + ε * plan

        NOW HIERARCHICAL: current_subgoal provides context for goal_value.

        Coefficients tuned to balance exploration vs exploitation:
        - Higher α = more goal-directed (exploitation)
        - Higher β = more exploratory (information seeking)
        - Higher γ = more penalty for repetitive actions

        Args:
            action: Action to score
            beliefs: Agent's belief state
            quest: Quest information (optional)
            current_subgoal: Current subgoal string (for hierarchical scoring)

        Returns:
            EFE score
        """
        # Tuned coefficients (v4 - hierarchical synthesis)
        # CRITICAL: Plan weight reduced to prioritize subgoal matching!
        alpha = 3.0  # Goal value weight (includes hierarchical subgoal bonus)
        beta = 2.0   # Entropy/Info weight
        gamma = 1.5  # Cost weight (loop penalty)
        delta = 1.5  # Memory weight (learn from experience)
        epsilon = 1.0 # Plan weight (REDUCED from 5.0 - subgoal match should dominate)

        goal_val = self.calculate_goal_value(action, current_subgoal)  # PASS subgoal
        entropy = self.calculate_entropy(action)
        cost = self.calculate_cost(action)
        memory_bonus = self.calculate_memory_bonus(action)
        plan_bonus = self.calculate_plan_bonus(action)

        efe = (alpha * goal_val) + (beta * entropy) - (gamma * cost) + (delta * memory_bonus) + (epsilon * plan_bonus)

        return efe
    
    def select_action(self, admissible_commands: List[str], quest: Optional[Dict] = None) -> str:
        """
        Select best action from available commands.

        NOW HIERARCHICAL: Uses current subgoal for contextual scoring.

        Args:
            admissible_commands: List of valid commands (strings)
            quest: Optional quest information

        Returns:
            Selected command string
        """
        # Input validation
        if admissible_commands is None or not isinstance(admissible_commands, list):
            if self.verbose:
                print("⚠️  Invalid commands input, using fallback")
            return "look"

        # Filter out invalid commands (non-strings or empty)
        valid_commands = [
            cmd for cmd in admissible_commands
            if isinstance(cmd, str) and cmd.strip()
        ]

        if not valid_commands:
            if self.verbose:
                print("⚠️  No valid commands available, using fallback")
            return "look"  # Default fallback

        # NEW: Get current subgoal for hierarchical scoring
        current_subgoal = None
        if self.subgoals and self.current_subgoal_index < len(self.subgoals):
            current_subgoal = self.subgoals[self.current_subgoal_index]

        if self.verbose:
            print(f"\n💭 DECISION-MAKING:")
            print(f"   Available actions: {len(valid_commands)}")
            if current_subgoal:
                print(f"   🎯 Current subgoal: {current_subgoal}")

        # Score all actions (NOW WITH SUBGOAL CONTEXT)
        scored_actions = []
        for action in valid_commands:
            try:
                score = self.score_action(action, self.beliefs, quest, current_subgoal)  # PASS subgoal
                scored_actions.append((score, action))

                if self.verbose and len(valid_commands) <= 20:  # Only show if not too many (increased for debugging)
                    print(f"      {score:6.2f} → {action}")
            except Exception as e:
                # If scoring fails for an action, skip it but don't crash
                if self.verbose:
                    print(f"⚠️  Scoring error for '{action}': {e}")
                continue

        # Safety: If all actions failed to score, fallback
        if not scored_actions:
            if self.verbose:
                print("⚠️  All actions failed to score, using fallback")
            return "look"

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
    
    def calculate_entropy_metric(self) -> float:
        """
        Calculate current entropy for critical state monitoring.
        Higher entropy = more uncertainty/confusion.
        """
        # Base entropy from number of unknown objects
        unknown_objects = sum(
            1 for obj, data in self.beliefs.get('objects', {}).items()
            if data.get('examined_count', 0) == 0
        )
        object_entropy = min(1.0, unknown_objects / 10.0)

        # Entropy from unexplored rooms (if we have room data)
        unvisited_rooms = sum(
            1 for room, data in self.beliefs.get('rooms', {}).items()
            if data.get('visited_count', 0) == 0
        )
        room_entropy = min(1.0, unvisited_rooms / 5.0)

        # Recent action diversity (low diversity = high certainty)
        if len(self.action_history) >= 5:
            recent_actions = [a['action'] for a in self.action_history[-5:]]
            unique_actions = len(set(recent_actions))
            action_entropy = 1.0 - (unique_actions / 5.0)
        else:
            action_entropy = 0.5

        return (0.4 * object_entropy + 0.3 * room_entropy + 0.3 * action_entropy)

    def calculate_prediction_error_metric(self) -> float:
        """Calculate prediction error for novelty detection."""
        if len(self.observation_history) < 2:
            return 0.0

        # Simple: Compare last two observations
        recent_obs = self.observation_history[-2:]
        obs_prev = str(recent_obs[0].get('observation', ''))
        obs_curr = str(recent_obs[1].get('observation', ''))

        # Text similarity
        prev_words = set(obs_prev.lower().split())
        curr_words = set(obs_curr.lower().split())

        if not prev_words and not curr_words:
            return 0.0

        common = prev_words & curr_words
        total = prev_words | curr_words

        similarity = len(common) / max(len(total), 1)
        return 1.0 - similarity

    def get_agent_state_for_critical_monitor(self) -> AgentState:
        """
        Build AgentState object for CriticalStateMonitor.
        """
        entropy = self.calculate_entropy_metric()
        prediction_error = self.calculate_prediction_error_metric()
        steps_remaining = self.max_steps - self.current_step

        return AgentState(
            entropy=entropy,
            history=self.location_history,
            steps=steps_remaining,
            dist=self.distance_to_goal,
            rewards=self.reward_history,
            error=prediction_error
        )

    def apply_critical_state_protocol(self, critical_state: CriticalState, admissible_commands: List[str]) -> Optional[str]:
        """
        Apply protocol-specific action override when in critical state.

        Returns:
            Action to take (if protocol overrides), or None (use normal EFE)
        """
        # Defensive: ensure admissible_commands is a list
        if not admissible_commands:
            admissible_commands = ['look', 'inventory']

        if critical_state == CriticalState.FLOW:
            return None  # Normal operation

        if self.verbose:
            print(f"\n🚨 CRITICAL STATE: {critical_state.name}")

        # PANIC Protocol: Choose safer, simpler actions
        if critical_state == CriticalState.PANIC:
            if self.verbose:
                print("   Protocol: TANK (Robustness over efficiency)")
            safe_commands = [
                c for c in admissible_commands
                if any(kw in c.lower() for kw in ['look', 'inventory', 'examine'])
            ]
            if safe_commands:
                import random
                action = random.choice(safe_commands)
                if self.verbose:
                    print(f"   Override: {action}")
                return action

        # DEADLOCK Protocol: Break the loop
        elif critical_state == CriticalState.DEADLOCK:
            if self.verbose:
                print("   Protocol: SISYPHUS (Perturbation)")
            # Filter out recently used actions
            recent_actions = [a['action'] for a in self.action_history[-5:]]
            new_commands = [c for c in admissible_commands if c not in recent_actions]
            if new_commands:
                import random
                action = random.choice(new_commands)
                if self.verbose:
                    print(f"   Override: {action} (breaking loop)")
                return action

        # SCARCITY Protocol: Focus on efficiency
        elif critical_state == CriticalState.SCARCITY:
            if self.verbose:
                print("   Protocol: SPARTAN (Efficiency)")
            # Prioritize goal-directed actions
            goal_commands = [
                c for c in admissible_commands
                if any(kw in c.lower() for kw in ['take', 'open', 'unlock', 'use', 'eat'])
            ]
            if goal_commands:
                # Use EFE scoring but only on goal commands
                scored = [(self.score_action(c, self.beliefs, None), c) for c in goal_commands]
                scored.sort(reverse=True)
                action = scored[0][1]
                if self.verbose:
                    print(f"   Override: {action} (goal-directed)")
                return action

        # NOVELTY Protocol: Explore to learn
        elif critical_state == CriticalState.NOVELTY:
            if self.verbose:
                print("   Protocol: EUREKA (Learning mode)")
            # Prioritize examine/look actions
            explore_commands = [
                c for c in admissible_commands
                if any(kw in c.lower() for kw in ['examine', 'look'])
            ]
            if explore_commands:
                import random
                action = random.choice(explore_commands)
                if self.verbose:
                    print(f"   Override: {action} (learning)")
                return action

        # ESCALATION Protocol: Emergency stop (shouldn't happen in normal flow)
        elif critical_state == CriticalState.ESCALATION:
            if self.verbose:
                print("   Protocol: ESCALATION (Emergency)")
                print("   ⛔ Agent is thrashing - requesting external help")
            # Return safe fallback
            return "look"

        # HUBRIS Protocol: Stay vigilant
        elif critical_state == CriticalState.HUBRIS:
            if self.verbose:
                print("   Protocol: ICARUS (Skepticism - stay alert)")
            # Let normal EFE handle it, but logged the state
            return None

        return None  # Fallback to normal EFE

    def save_episode(self):
        """
        Save the current episode to Neo4j Episodic Memory.

        Uses memory system to store episode with rich context for future retrieval.
        Includes error handling to prevent crashes on DB failures.
        """
        if not self.session:
            if self.verbose:
                print("⚠️  No database session - skipping episode save")
            return

        try:
            if self.verbose:
                print("💾 Saving episode to memory...")

            # Calculate episode metrics
            total_reward = sum(self.reward_history) if self.reward_history else 0.0
            success = total_reward > 0  # Simple success metric

            # Get goal from plan if available
            goal = None
            if self.plan_history:
                # Use most recent plan's goal
                goal = self.plan_history[-1].goal
            elif self.current_plan:
                goal = self.current_plan.goal

            # Build step data with rich context
            steps = []
            for i in range(len(self.action_history)):
                action_data = self.action_history[i]
                obs_data = self.observation_history[i] if i < len(self.observation_history) else {}
                reward = self.reward_history[i] if i < len(self.reward_history) else 0.0

                # Determine outcome
                if reward > 0:
                    outcome = 'positive'
                elif reward < 0:
                    outcome = 'negative'
                else:
                    outcome = 'neutral'

                steps.append({
                    'action': action_data.get('action', 'unknown'),
                    'room': obs_data.get('room', 'Unknown'),
                    'reward': float(reward),
                    'outcome': outcome
                })

            # Create episode data structure
            episode_data = {
                'episode_id': f'tw_ep_{self.current_step}_{int(time.time())}',
                'steps': steps,
                'total_reward': float(total_reward),
                'success': bool(success),
                'goal': goal
            }

            # Use memory system to store
            stored = self.memory.store_episode(episode_data)

            if stored and self.verbose:
                print(f"   ✅ Episode saved ({len(steps)} steps, reward: {total_reward:+.1f})")
            elif not stored and self.verbose:
                print("   ⚠️  Episode storage failed")

        except Exception as e:
            # Don't crash on database errors
            if self.verbose:
                print(f"⚠️  Episode save failed: {e}")
            logger.warning(f"Failed to save episode to Neo4j: {e}")

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

        # NEW: Update subgoal progress (hierarchical synthesis)
        # Advance when: (1) positive reward, OR (2) last action likely completed subgoal
        should_advance = False

        if reward > 0 and self.subgoals and self.current_subgoal_index < len(self.subgoals) - 1:
            should_advance = True
            if self.verbose:
                print(f"   ✨ Advancing due to positive reward")
        elif self.action_history and self.subgoals and self.current_subgoal_index < len(self.subgoals) - 1:
            # Check if last action likely completed current subgoal
            last_action = self.action_history[-1]['action']
            current_subgoal = self.subgoals[self.current_subgoal_index]

            # Extract key tokens from subgoal and action
            subgoal_tokens = set(current_subgoal.lower().split())
            action_tokens = set(last_action.lower().split())
            stopwords = {'the', 'a', 'an', 'from', 'into', 'on', 'in', 'to', 'of', 'with'}

            subgoal_clean = subgoal_tokens - stopwords
            action_clean = action_tokens - stopwords

            # If action matches subgoal closely, likely completed
            overlap = len(subgoal_clean & action_clean)
            match_ratio = overlap / max(len(subgoal_clean), 1)

            if self.verbose:
                print(f"   🔍 Progress check: '{last_action}' vs subgoal '{current_subgoal}'")
                print(f"       Overlap: {overlap}/{len(subgoal_clean)} tokens ({match_ratio:.0%})")

            if overlap >= len(subgoal_clean) * 0.5:  # At least 50% match
                should_advance = True
                if self.verbose:
                    print(f"   ✨ Advancing due to action match")

        if should_advance:
            self.current_subgoal_index += 1
            if self.verbose:
                print(f"   ✅ Subgoal {self.current_subgoal_index} complete!")
                if self.current_subgoal_index < len(self.subgoals):
                    print(f"   🎯 Next subgoal: {self.subgoals[self.current_subgoal_index]}")

        # Update distance estimate (simple heuristic based on progress)
        # Could be improved with actual graph distance if we build connectivity map
        if reward > 0:
            self.distance_to_goal = max(0, self.distance_to_goal - 5)

        # Check plan progress (if we have a plan and took an action)
        if self.action_history:
            last_action = self.action_history[-1]['action']
            self.check_plan_progress(last_action)

        # Maybe generate a new plan (if we don't have one and goal is clear)
        self.maybe_generate_plan(admissible_commands)

        # CRITICAL FIX: Disable critical state monitoring for TextWorld
        # The ESCALATION/DEADLOCK/NOVELTY protocols were overriding quest-aware action selection
        # For TextWorld quests, we want to follow the EFE scores directly
        
        # Original code (now disabled):
        # agent_state = self.get_agent_state_for_critical_monitor()
        # self.current_critical_state = self.critical_monitor.evaluate(agent_state)
        # protocol_action = self.apply_critical_state_protocol(
        #     self.current_critical_state,
        #     admissible_commands
        # )
        
        # Force FLOW state (normal operation, no protocol override)
        from critical_state import CriticalState
        self.current_critical_state = CriticalState.FLOW
        protocol_action = None

        # Update done status
        self.done = done
        if self.verbose and done:
            print("   ✅ Episode complete!")
            self.save_episode()

        # Select next action (either protocol override or normal EFE)
        if protocol_action is not None:
            action = protocol_action
            if self.verbose:
                print(f"⚡ ACTION: {action}")
        else:
            # Normal EFE-based selection (now quest-aware!)
            action = self.select_action(admissible_commands, quest)
        
        if self.verbose:
            print("-"*70)
        
        return action
