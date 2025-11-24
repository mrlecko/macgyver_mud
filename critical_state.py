from enum import Enum, auto
import config
from control.autotuner import AutoTuner

class AgentState:
    """
    Data Transfer Object for Agent State metrics.
    Used by CriticalStateMonitor to evaluate protocols.
    """
    def __init__(self, entropy, history, steps, dist, rewards, error):
        self.entropy = entropy
        self.location_history = history
        self.steps_remaining = steps
        self.distance_to_goal = dist
        self.reward_history = rewards
        self.prediction_error = error

class CriticalState(Enum):
    ESCALATION = auto() # Highest Priority (Stop)
    FLOW = auto()
    PANIC = auto()
    DEADLOCK = auto()
    NOVELTY = auto()
    HUBRIS = auto()
    SCARCITY = auto()

class CriticalStateMonitor:
    def __init__(self):
        self.state_history = [] # Track past critical states for meta-meta-cognition
        self.tuner = AutoTuner() # Online statistical tracking

    def check_escalation(self, steps_remaining):
        """
        Trigger: Meta-Cognitive Failure (Thrashing) or Terminal Scarcity.
        Risk: System Collapse.
        Protocol: STOP_AND_ESCALATE.
        """
        # 1. Terminal Scarcity
        scarcity_limit = config.CRITICAL_THRESHOLDS["ESCALATION_SCARCITY_LIMIT"]
        if steps_remaining < scarcity_limit:
            return True
            
        # 2. Panic Spiral (3 Panics in last 5 states)
        panic_limit = config.CRITICAL_THRESHOLDS["ESCALATION_PANIC_LIMIT"]
        recent_states = self.state_history[-5:]
        if recent_states.count(CriticalState.PANIC) >= panic_limit:
            return True
            
        # 3. Sisyphus Failure (2 Deadlocks in last 10 states)
        deadlock_limit = config.CRITICAL_THRESHOLDS["ESCALATION_DEADLOCK_LIMIT"]
        recent_states_long = self.state_history[-10:]
        if recent_states_long.count(CriticalState.DEADLOCK) >= deadlock_limit:
            return True
            
        return False

    def check_scarcity(self, steps_remaining, distance_to_goal, agent_state=None):
        """
        Trigger: Steps < Distance * Factor (OR Quest-Aware: Steps < Subgoals * Factor)
        Risk: Death before Glory.
        Protocol: Spartan (Efficiency).
        
        QUEST-AWARE (NEW):
        If agent has quest context, use remaining subgoals to estimate needed steps.
        """
        # QUEST-AWARE MODE: Use remaining subgoals for better estimation
        if (agent_state and 
            hasattr(agent_state, 'has_quest') and 
            agent_state.has_quest and
            hasattr(agent_state, 'current_subgoal_index')):
            
            # Calculate remaining subgoals
            # Heuristic: Each subgoal needs ~2-3 steps on average
            if hasattr(agent_state, 'total_subgoals'):
                remaining_subgoals = agent_state.total_subgoals - agent_state.current_subgoal_index
            else:
                # Fallback if we don't track total
                remaining_subgoals = max(1, 5 - agent_state.current_subgoal_index)
            
            steps_per_subgoal = 2.5  # Average steps needed per subgoal
            estimated_steps_needed = remaining_subgoals * steps_per_subgoal
            
            # Add 20% buffer
            threshold = estimated_steps_needed * 1.2
            
            return steps_remaining < threshold
        
        # ORIGINAL MODE: Distance-based estimation (for non-quest scenarios)
        factor = config.CRITICAL_THRESHOLDS["SCARCITY_FACTOR"]
        if steps_remaining < distance_to_goal * factor:
            return True
        return False

    def check_panic(self, entropy):
        """
        Trigger: Entropy > Threshold OR Statistical Anomaly
        Risk: Confusion / Error.
        Protocol: Tank (Robustness).
        """
        # Update tuner
        self.tuner.update("entropy", entropy)
        
        # Check 1: Statistical Anomaly (Dynamic)
        if self.tuner.is_anomaly("entropy", entropy, threshold_sigma=3.0):
            return True
            
        # Check 2: Hard Safety Limit (Static)
        threshold = config.CRITICAL_THRESHOLDS["PANIC_ENTROPY"]
        if entropy > threshold:
            return True
            
        return False

    def check_deadlock(self, location_history, agent_state=None):
        """
        Trigger: Cycle Detection (A -> B -> A -> B) OR Quest-Aware Stuck Detection
        Risk: Infinite Loop.
        Protocol: Sisyphus (Perturbation).
        
        QUEST-AWARE (NEW):
        If agent has quest context, detect stuck-on-subgoal instead of location loops.
        - TRUE DEADLOCK: 6+ steps on same subgoal with no progress
        - NOT DEADLOCK: Advancing through subgoals (even if revisiting locations)
        """
        # QUEST-AWARE MODE: If agent_state has quest context, use subgoal-based detection
        if (agent_state and 
            hasattr(agent_state, 'has_quest') and 
            agent_state.has_quest and
            hasattr(agent_state, 'steps_on_current_subgoal')):
            
            # Check if stuck on same subgoal
            steps_on_subgoal = agent_state.steps_on_current_subgoal
            deadlock_threshold = 6  # Allow 5 steps for exploration, 6+ = stuck
            
            if steps_on_subgoal < deadlock_threshold:
                return False  # Still exploring
            
            # 6+ steps on subgoal - check if making progress via rewards
            if len(agent_state.reward_history) >= 5:
                recent_rewards = agent_state.reward_history[-5:]
                total_recent_reward = sum(recent_rewards)
                
                if total_recent_reward > 0:
                    return False  # Making progress (getting rewards)
            
            # 6+ steps on subgoal, no rewards = STUCK
            return True
        
        # ORIGINAL MODE: Location-based cycle detection (for non-quest scenarios)
        window = config.CRITICAL_THRESHOLDS["DEADLOCK_WINDOW"]
        if len(location_history) < window:
            return False
        # Check for A -> B -> A -> B pattern
        # t (last) == t-2 AND t-1 == t-3
        if (location_history[-1] == location_history[-3] and 
            location_history[-2] == location_history[-4]):
            return True
        return False

    def check_novelty(self, prediction_error):
        """
        Trigger: High Prediction Error (> Threshold) OR Statistical Anomaly
        Risk: Epistemic Corruption.
        Protocol: Eureka (Learning).
        """
        # Update tuner
        self.tuner.update("prediction_error", prediction_error)
        
        # Check 1: Statistical Anomaly (Dynamic)
        if self.tuner.is_anomaly("prediction_error", prediction_error, threshold_sigma=3.0):
            return True
            
        # Check 2: Hard Safety Limit (Static)
        threshold = config.CRITICAL_THRESHOLDS["NOVELTY_ERROR"]
        if prediction_error > threshold:
            return True
        return False

    def check_hubris(self, reward_history, entropy):
        """
        Trigger: High Reward Streak (> Streak) AND Low Entropy (< Threshold)
        Risk: Complacency.
        Protocol: Icarus (Skepticism).
        """
        entropy_threshold = config.CRITICAL_THRESHOLDS["HUBRIS_ENTROPY"]
        streak_threshold = config.CRITICAL_THRESHOLDS["HUBRIS_STREAK"]
        
        if entropy >= entropy_threshold:
            return False
        
        if len(reward_history) < streak_threshold:
            return False
            
        # Check if last N rewards are all high (>= 1.0)
        recent_rewards = reward_history[-streak_threshold:]
        if all(r >= 1.0 for r in recent_rewards):
            return True
            
        return False

    def evaluate(self, agent_state) -> CriticalState:
        """
        Evaluate the agent's state and return the highest priority CriticalState.
        Priority: ESCALATION > SCARCITY > PANIC > DEADLOCK > NOVELTY > HUBRIS > FLOW
        """
        # 1. Determine Raw State (The "Reptilian Reflex")
        raw_state = CriticalState.FLOW
        
        if self.check_scarcity(agent_state.steps_remaining, agent_state.distance_to_goal, agent_state):  # PASS agent_state
            raw_state = CriticalState.SCARCITY
        elif self.check_panic(agent_state.entropy):
            raw_state = CriticalState.PANIC
        elif self.check_deadlock(agent_state.location_history, agent_state):  # PASS agent_state for quest-aware
            raw_state = CriticalState.DEADLOCK
        elif self.check_novelty(agent_state.prediction_error):
            raw_state = CriticalState.NOVELTY
        elif self.check_hubris(agent_state.reward_history, agent_state.entropy):
            raw_state = CriticalState.HUBRIS
            
        # 2. Update History (The "Memory")
        self.state_history.append(raw_state)
        
        # 3. Check Escalation (The "Circuit Breaker")
        # We check this AFTER updating history so the current state counts towards the limit
        if self.check_escalation(agent_state.steps_remaining):
            return CriticalState.ESCALATION
            
        return raw_state
