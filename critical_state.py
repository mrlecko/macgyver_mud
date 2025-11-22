from enum import Enum, auto
import config

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
    FLOW = auto()
    PANIC = auto()
    DEADLOCK = auto()
    NOVELTY = auto()
    HUBRIS = auto()
    SCARCITY = auto()

class CriticalStateMonitor:
    def __init__(self):
        pass

    def check_scarcity(self, steps_remaining, distance_to_goal):
        """
        Trigger: Steps < Distance * Factor
        Risk: Death before Glory.
        Protocol: Spartan (Efficiency).
        """
        factor = config.CRITICAL_THRESHOLDS["SCARCITY_FACTOR"]
        if steps_remaining < distance_to_goal * factor:
            return True
        return False

    def check_panic(self, entropy):
        """
        Trigger: Entropy > Threshold
        Risk: Confusion / Error.
        Protocol: Tank (Robustness).
        """
        threshold = config.CRITICAL_THRESHOLDS["PANIC_ENTROPY"]
        if entropy > threshold:
            return True
        return False

    def check_deadlock(self, location_history):
        """
        Trigger: Cycle Detection (A -> B -> A -> B)
        Risk: Infinite Loop.
        Protocol: Sisyphus (Perturbation).
        """
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
        Trigger: High Prediction Error (> Threshold)
        Risk: Epistemic Corruption.
        Protocol: Eureka (Learning).
        """
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
        Priority: SCARCITY > PANIC > DEADLOCK > NOVELTY > HUBRIS > FLOW
        """
        # 1. SCARCITY
        if self.check_scarcity(agent_state.steps_remaining, agent_state.distance_to_goal):
            return CriticalState.SCARCITY
            
        # 2. PANIC
        if self.check_panic(agent_state.entropy):
            return CriticalState.PANIC
            
        # 3. DEADLOCK
        if self.check_deadlock(agent_state.location_history):
            return CriticalState.DEADLOCK
            
        # 4. NOVELTY
        if self.check_novelty(agent_state.prediction_error):
            return CriticalState.NOVELTY
            
        # 5. HUBRIS
        if self.check_hubris(agent_state.reward_history, agent_state.entropy):
            return CriticalState.HUBRIS
            
        # 6. FLOW
        return CriticalState.FLOW
