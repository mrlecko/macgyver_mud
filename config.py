"""
Configuration for MacGyver Active Inference Demo
"""
import os

# ============================================================================
# Neo4j Connection Settings
# ============================================================================

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:17687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ============================================================================
# Scenario Configuration
# ============================================================================

# Default door state (can be overridden by CLI)
DEFAULT_DOOR_STATE = "locked"  # or "unlocked"

# Maximum steps before giving up
MAX_STEPS = 5

# ============================================================================
# Scoring Parameters (Active Inference Weights)
# ============================================================================

# These control the balance between exploration and exploitation
ALPHA = 1.0   # Goal value weight
BETA = 6.0    # Information gain weight (increased to make exploration matter)
GAMMA = 0.3   # Cost weight (increased to penalize expensive actions)

# ============================================================================
# Reward/Penalty Constants
# ============================================================================

# Reward Mode: Controls how the agent is incentivized
# - "naive": Simple "minimize steps" approach (demonstrates metric gaming)
# - "strategic": Rewards information-gathering and smart strategies
REWARD_MODE = os.getenv("REWARD_MODE", "strategic")  # Default to strategic

# Rewards for successful outcomes
REWARD_ESCAPE = 10.0  # Successfully escaping the room

# Penalties (vary by reward mode)
PENALTY_FAIL = 3.0    # Trying a locked door (failure)

# SLOW_PENALTY: Using the window (works but is less ideal than using door)
# In NAIVE mode: Lower penalty, agent learns to spam window
# In STRATEGIC mode: Balanced penalty, window is fallback but not forbidden
if REWARD_MODE == "naive":
    SLOW_PENALTY = 4.0   # Original: allows metric gaming
else:  # strategic
    SLOW_PENALTY = 6.0   # Balanced: window is viable fallback when needed

# ============================================================================
# Belief Update Parameters
# ============================================================================

# Conservative belief updates to maintain some uncertainty
# This makes the agent's behavior more adaptive and interesting

# After observing door is locked
BELIEF_DOOR_LOCKED = 0.15

# After observing door is unlocked
BELIEF_DOOR_UNLOCKED = 0.85

# After trying door but it was stuck/locked
BELIEF_DOOR_STUCK = 0.10

# Initial belief (uncertainty)
INITIAL_BELIEF = 0.5

# Belief category thresholds (for procedural memory context matching)
BELIEF_THRESHOLD_CONFIDENT_LOCKED = 0.3  # Below this is "confident_locked"
BELIEF_THRESHOLD_CONFIDENT_UNLOCKED = 0.7  # Above this is "confident_unlocked"
# Between these thresholds is "uncertain"

# ============================================================================
# Agent Configuration
# ============================================================================

AGENT_NAME = "MacGyverBot"
STATE_VAR_NAME = "DoorLockState"

# ============================================================================
# Geometric Meta-Cognition Configuration
# ============================================================================

# Enable the Geometric Controller (Adaptive k-target)
# If False, uses standard Active Inference (Baseline)
# If True, dynamically adjusts skill selection based on entropy/performance
# If True, dynamically adjusts skill selection based on entropy/performance
ENABLE_GEOMETRIC_CONTROLLER = False

# Magnitude of the boost applied to skills matching the target k-value
BOOST_MAGNITUDE = 5.0

# Enable Lyapunov Stability Monitoring
# Monitors system stability via Lyapunov function V(s)
# Escalates if V(s) is diverging (system becoming unstable)
ENABLE_LYAPUNOV_MONITORING = os.getenv("ENABLE_LYAPUNOV", "true").lower() == "true"

# ============================================================================
# Critical State Protocols Configuration
# ============================================================================

# Enable the 5-State Critical Protocol System (Hubris, Deadlock, Novelty, Scarcity, Panic)
# Requires ENABLE_GEOMETRIC_CONTROLLER = True (as it builds on top of it)
ENABLE_CRITICAL_STATE_PROTOCOLS = False

# Thresholds for State Triggers
CRITICAL_THRESHOLDS = {
    "PANIC_ENTROPY": 0.45,      # Entropy > 0.45 triggers Panic
    "SCARCITY_FACTOR": 1.2,     # Steps < Dist * 1.2 triggers Scarcity
    "NOVELTY_ERROR": 0.8,       # Prediction Error > 0.8 triggers Novelty
    "HUBRIS_STREAK": 6,         # Reward Streak >= 6 triggers Hubris
    "HUBRIS_ENTROPY": 0.1,      # Entropy < 0.1 required for Hubris
    "DEADLOCK_WINDOW": 4,       # History window for cycle detection
    "ESCALATION_PANIC_LIMIT": 3, # 3 Panics in window triggers Escalation
    "ESCALATION_DEADLOCK_LIMIT": 2, # 2 Deadlocks in window triggers Escalation
    "ESCALATION_SCARCITY_LIMIT": 2, # Steps < 2 triggers Escalation
    "ESCALATION_STATE_DURATION": 3,  # If in PANIC/DEADLOCK for 3 consecutive steps
    "ESCALATION_COOLDOWN": 5,  # Minimum steps between escalations
}

# ============================================================================
# Episodic Memory & Offline Learning
# ============================================================================

# Enable episodic memory replay (counterfactual reasoning)
ENABLE_EPISODIC_MEMORY = os.getenv("ENABLE_EPISODIC_MEMORY", "false").lower() == "true"

# Maximum counterfactuals to generate per episode
MAX_COUNTERFACTUALS_PER_EPISODE = int(os.getenv("MAX_COUNTERFACTUALS", "3"))

# Replay frequency (every N episodes, perform offline learning)
EPISODIC_REPLAY_FREQUENCY = int(os.getenv("REPLAY_FREQUENCY", "10"))

# Number of episodes to replay during offline learning
NUM_EPISODES_TO_REPLAY = int(os.getenv("NUM_REPLAY_EPISODES", "5"))

# ============================================================================
# Advanced Episodic Memory Features
# ============================================================================

# Update skill priors based on counterfactual insights
EPISODIC_UPDATE_SKILL_PRIORS = os.getenv("EPISODIC_UPDATE_PRIORS", "false").lower() == "true"

# Weight for skill prior updates (0.0 = no learning, 1.0 = full trust in counterfactuals)
# FIX #4: Increased from 0.1 to 0.5 for meaningful adaptation
EPISODIC_LEARNING_RATE = float(os.getenv("EPISODIC_LEARNING_RATE", "0.5"))

# Scaling factor for regret-based adjustments (larger = more conservative updates)
EPISODIC_REGRET_SCALE_FACTOR = 10.0

# Enable graph labyrinth integration for spatial counterfactuals
EPISODIC_USE_LABYRINTH = os.getenv("EPISODIC_USE_LABYRINTH", "false").lower() == "true"

# Forgetting mechanism: decay episodes older than N episodes
EPISODIC_FORGETTING_ENABLED = os.getenv("EPISODIC_FORGETTING", "false").lower() == "true"

# Maximum episodes to keep (oldest are deleted)
EPISODIC_MAX_EPISODES = int(os.getenv("EPISODIC_MAX_EPISODES", "100"))

# Decay factor for regret from old episodes (0.0-1.0, lower = faster decay)
EPISODIC_DECAY_FACTOR = float(os.getenv("EPISODIC_DECAY_FACTOR", "0.95"))


# ============================================================================
# Display Configuration
# ============================================================================

# Rich console styling
SHOW_SCORES = False  # Show scoring details in verbose mode
SHOW_GRAPH_STATS = True  # Show Neo4j stats after run

# ============================================================================
# Runtime Selection
# ============================================================================

# Agent runtime mode: "heuristic" (current bandit) or "active" (new Active Inference runtime)
AGENT_RUNTIME_MODE = os.getenv("AGENT_RUNTIME_MODE", "heuristic")

# Robust scenario flag: if true, include extended skills/observations (alarm/key/jam)
ENABLE_ROBUST_SCENARIO = os.getenv("ENABLE_ROBUST_SCENARIO", "false").lower() == "true"

# Allow hard-stop escalation (tests may override)
ALLOW_ESCALATION_HARD_STOP = os.getenv("ALLOW_ESCALATION_HARD_STOP", "true").lower() == "true"

# ============================================================================
# Validation
# ============================================================================

def validate_config():
    """Validate configuration parameters"""
    assert 0 <= INITIAL_BELIEF <= 1, "INITIAL_BELIEF must be in [0, 1]"
    assert 0 <= BELIEF_DOOR_LOCKED <= 1, "BELIEF_DOOR_LOCKED must be in [0, 1]"
    assert 0 <= BELIEF_DOOR_UNLOCKED <= 1, "BELIEF_DOOR_UNLOCKED must be in [0, 1]"
    assert 0 <= BELIEF_DOOR_STUCK <= 1, "BELIEF_DOOR_STUCK must be in [0, 1]"
    assert ALPHA >= 0, "ALPHA must be non-negative"
    assert BETA >= 0, "BETA must be non-negative"
    assert GAMMA >= 0, "GAMMA must be non-negative"
    assert MAX_STEPS > 0, "MAX_STEPS must be positive"

    # Feature flag dependency validation
    if ENABLE_CRITICAL_STATE_PROTOCOLS and not ENABLE_GEOMETRIC_CONTROLLER:
        print("⚠️  WARNING: ENABLE_CRITICAL_STATE_PROTOCOLS=True requires ENABLE_GEOMETRIC_CONTROLLER=True")
        print("   Critical state protocols will NOT execute unless both flags are enabled.")
        print("   Set ENABLE_GEOMETRIC_CONTROLLER=True to activate protocols.")

    print("✓ Configuration validated")

if __name__ == "__main__":
    # Test configuration by printing values
    print("=== MacGyver Demo Configuration ===")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Neo4j User: {NEO4J_USER}")
    print(f"\nReward Mode: {REWARD_MODE}")
    print(f"\nScoring Weights:")
    print(f"  α (goal): {ALPHA}")
    print(f"  β (info): {BETA}")
    print(f"  γ (cost): {GAMMA}")
    print(f"\nRewards/Penalties:")
    print(f"  Escape reward: {REWARD_ESCAPE}")
    print(f"  Fail penalty: {PENALTY_FAIL}")
    print(f"  Slow penalty: {SLOW_PENALTY} ({'naive: allows gaming' if REWARD_MODE == 'naive' else 'strategic: encourages info-gathering'})")
    print(f"\nBelief Updates:")
    print(f"  Initial: {INITIAL_BELIEF}")
    print(f"  Door locked: {BELIEF_DOOR_LOCKED}")
    print(f"  Door unlocked: {BELIEF_DOOR_UNLOCKED}")
    print(f"  Door stuck: {BELIEF_DOOR_STUCK}")
    print()
    validate_config()
