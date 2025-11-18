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

# ============================================================================
# Agent Configuration
# ============================================================================

AGENT_NAME = "MacGyverBot"
STATE_VAR_NAME = "DoorLockState"

# ============================================================================
# Display Configuration
# ============================================================================

# Rich console styling
SHOW_SCORES = False  # Show scoring details in verbose mode
SHOW_GRAPH_STATS = True  # Show Neo4j stats after run

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
