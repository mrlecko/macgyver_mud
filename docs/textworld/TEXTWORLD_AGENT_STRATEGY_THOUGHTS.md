# TextWorld Agent Strategy: Deep Thoughts on Cognitive Framework Integration

**Document Purpose:** Strategic analysis of applying the MacGyver MUD bicameral cognitive architecture to TextWorld interactive fiction challenges.

**Audience:** Decision-maker unfamiliar with TextWorld, familiar with the cognitive framework.

**Date:** 2025-11-23

---

## Part 1: Understanding TextWorld

### What is TextWorld?

**TextWorld** is Microsoft Research's sandbox environment for training RL agents on text-based games (interactive fiction).

**Key Characteristics:**
- **Natural language:** All state and actions are text
- **Procedurally generated:** Games created programmatically
- **Quest-based:** Clear objectives (find key, unlock chest, etc.)
- **Partial observability:** Agent only sees textual description
- **Large action space:** Combinatorial (object × verb combinations)

### Example TextWorld Game

```
You are in a kitchen. There is a wooden door to the north.
You can see: a rusty key, a wooden table
Admissible commands: ['go north', 'take key', 'examine table', 'look', ...]

> take key
You pick up the rusty key.

> go north
The door is locked.

> unlock door with key
You unlock the door and step into a bedroom. You win!
```

### The Core Challenges

TextWorld presents 6 fundamental challenges for RL agents:

#### 1. **Natural Language Understanding**
- **Challenge:** Parse human-written text descriptions
- **Example:** "wooden door" vs "mahogany door" vs "locked entrance"
- **Why hard:** Requires semantic understanding, not just pattern matching

#### 2. **Combinatorial Action Space**
- **Challenge:** ~100-1000s of possible commands per state
- **Example:** {"take", "drop", "examine"} × {key, door, table, ...}
- **Why hard:** Can't enumerate all possibilities

#### 3. **Sparse Rewards**
- **Challenge:** Reward only upon quest completion
- **Example:** 0, 0, 0, ... 0, +10 (on win)
- **Why hard:** No gradient for learning during exploration

#### 4. **Partial Observability**
- **Challenge:** True world state hidden, only see text feedback
- **Example:** Don't know if door is locked until you try it
- **Why hard:** Must infer latent state from observations

#### 5. **Long-term Planning**
- **Challenge:** Multi-step quests require sequential reasoning
- **Example:** Find key → take key → go to door → unlock door → enter
- **Why hard:** Credit assignment across 5+ actions

#### 6. **Generalization**
- **Challenge:** Transfer learned skills to new quests/games
- **Example:** "unlock door" strategy should work for any door/key
- **Why hard:** Overfitting to specific game instances

### How Most RL Agents Fail

**Typical approaches:**
1. **DQN/PPO:** Treat as black-box MDP
   - ❌ Struggles with sparse rewards
   - ❌ Can't handle combinatorial actions
   - ❌ No semantic understanding

2. **Language Models (GPT-based):**
   - ❌ No planning capability
   - ❌ Hallucinates invalid commands
   - ❌ Doesn't learn from experience

3. **Symbolic Planners:**
   - ❌ Require perfect world model
   - ❌ Brittle to unexpected states
   - ❌ Don't handle uncertainty

**Success rate on complex quests:** ~10-30% (state of the art)

---

## Part 2: Why the Bicameral Framework is PERFECT for TextWorld

### Architectural Alignment

| TextWorld Challenge | Bicameral Component | Why It Fits |
|:---|:---|:---|
| **Long-term planning** | Cortex (Active Inference) | Goal-directed EFE minimization |
| **Partial observability** | Belief maintenance | Bayesian updates from text feedback |
| **Sparse rewards** | Info-seeking behavior (β) | Explores to reduce uncertainty |
| **Combinatorial actions** | Skill abstraction | Reduce search space via named strategies |
| **Critical failures** | Brainstem (Critical States) | Detect deadlocks, confusion |
| **Learning from mistakes** | Hippocampus (Episodic Memory) | Counterfactual "what if" scenarios |

**The framework naturally addresses 5/6 challenges.**

### The Key Insight: TextWorld IS a Belief Inference Problem

**Standard view:** TextWorld = RL problem (maximize reward)

**Bicameral view:** TextWorld = Active Inference problem (minimize surprise + achieve goals)

**Why this matters:**
```python
# Standard RL
agent.goal = "maximize expected reward"
agent.method = "try actions, see what works"
Result: Random exploration until lucky

# Active Inference
agent.goal = "minimize free energy = achieve quest + reduce uncertainty"
agent.method = "infer world state, then act strategically"
Result: Systematic information gathering, then goal pursuit
```

**Example:**
```
Situation: Agent in room with locked door, window, and key on floor

Standard RL:
- Try random actions
- Maybe pick up key (random)
- Maybe try door (random)
- Eventually succeed (100+ steps)

Active Inference:
- Step 1: High uncertainty about world → "examine key" (info-seeking)
- Observation: "rusty key, fits door locks"
- Belief update: p(key_unlocks_door) = 0.9
- Step 2: "take key" (prepare for goal)
- Step 3: "unlock door with key" (goal achievement)
- Success in 3 steps
```

---

## Part 3: Strategic Application of Framework Components

### 3.1 Cortex: Active Inference for TextWorld

#### Belief State Representation

**What to track:**
```python
beliefs = {
    'room_connections': {  # Spatial model
        'kitchen': {'north': 'bedroom', 'east': '?'}
    },
    'object_locations': {  # Object tracking
        'key': 'inventory',
        'chest': 'bedroom'
    },
    'object_states': {  # State inference
        'door_north': {'locked': 0.9, 'open': 0.1},
        'chest': {'locked': 0.7, 'unlocked': 0.3}
    },
    'quest_progress': {  # Goal tracking
        'find_key': True,
        'unlock_chest': False
    }
}
```

**Why this works:**
- Matches partial observability (we build knowledge from text)
- Enables planning (we know what's where)
- Supports counterfactuals (what if door was unlocked?)

#### Expected Free Energy (EFE) Scoring

**Adapt existing EFE formula:**
```python
def score_textworld_action(action, beliefs, quest):
    # α: Goal achievement (pragmatic value)
    goal_value = estimate_progress_toward_quest(action, quest, beliefs)
    
    # β: Information gain (epistemic value)
    info_gain = estimate_uncertainty_reduction(action, beliefs)
    
    # γ: Cost (efficiency)
    cost = estimate_action_cost(action)  # Steps, risk
    
    EFE = α * goal_value + β * info_gain - γ * cost
    return EFE
```

**Example scoring:**
```
Current state: In kitchen, key on table, door locked
Quest: Escape through door

Actions:
1. "take key"
   - goal_value = 0.5 (prepares for unlock)
   - info_gain = 0.1 (minor, we can see key)
   - cost = 1
   - EFE = 0.5*10 + 0.1*5 - 1 = 4.5

2. "examine key"
   - goal_value = 0.0 (doesn't progress quest)
   - info_gain = 0.8 (confirms key type)
   - cost = 1
   - EFE = 0 + 0.8*5 - 1 = 3.0

3. "try door"
   - goal_value = 0.9 (might succeed!)
   - info_gain = 0.6 (confirms lock state)
   - cost = 1
   - EFE = 0.9*10 + 0.6*5 - 1 = 12.0  ← Best!
```

**Key insight:** EFE naturally balances "try the goal" vs "gather info first"

### 3.2 Brainstem: Critical State Protocols for TextWorld

#### Mapping Critical States to TextWorld

**1. PANIC (High Entropy / Confusion)**

**Trigger:**
- Too many admissible commands (>50)
- No clear parse of room description
- Multiple viable actions, no clear best

**TextWorld example:**
```
You are in a vast library. There are hundreds of books, dozens of shelves,
multiple doors, windows, tables, chairs...
Admissible commands: [... 200 commands ...]

Agent entropy: H(beliefs) = 0.9 → PANIC
```

**Protocol: TANK (Robustness)**
```python
if state == PANIC:
    # Simplify: Use safe, information-gathering actions
    preferred_actions = [
        'look',           # Re-examine room
        'inventory',      # Check what I have
        'examine quest',  # Remind goal
    ]
    # Avoid complex multi-step actions
```

**2. DEADLOCK (Repeated Pattern)**

**Trigger:**
- Agent tries same action 3+ times
- No progress toward quest for 10+ steps
- Stuck in loop (e.g., "go north" → "go south" → "go north" ...)

**TextWorld example:**
```
> go north
You can't go that way.
> go east
You can't go that way.
> go north  # Repeating!
```

**Protocol: SISYPHUS (Force Perturbation)**
```python
if state == DEADLOCK:
    # Break pattern: Try unexplored action
    recent_actions = history[-5:]
    forbidden = set(recent_actions)
    valid_actions = [a for a in admissible if a not in forbidden]
    select_random_from(valid_actions)  # Force novelty
```

**3. SCARCITY (Running Out of Steps)**

**Trigger:**
- Steps remaining < estimated distance to goal
- Max episode length approaching (e.g., 95/100 steps)

**TextWorld example:**
```
Steps: 97/100
Quest: Still need to find key, unlock chest, take treasure
Estimated steps needed: 5+

SCARCITY triggered!
```

**Protocol: SPARTAN (Ruthless Efficiency)**
```python
if state == SCARCITY:
    # Only goal-directed actions, no exploration
    α = 10.0  # Massive goal weight
    β = 0.0   # Zero exploration
    γ = 0.1   # Ignore cost
    # Forces: "take shortcut even if risky"
```

**4. NOVELTY (High Prediction Error)**

**Trigger:**
- Unexpected observation (hallucinated object appears)
- Action fails when expected to succeed
- Observation contradicts belief

**TextWorld example:**
```
Agent belief: "key unlocks door" (p=0.9)
Action: "unlock door with key"
Observation: "The rusty key breaks in the lock!"

Prediction error: HIGH → NOVELTY
```

**Protocol: EUREKA (Learning Mode)**
```python
if state == NOVELTY:
    # Update world model, then re-plan
    update_beliefs_from_surprise(observation)
    recompute_quest_plan()
    # Might discover: "need different key"
```

**5. HUBRIS (Overconfidence)**

**Trigger:**
- Recent success streak (5+ wins in a row)
- Agent using same strategy repeatedly
- Low entropy + high confidence

**TextWorld example:**
```
Agent: "I always win by trying door first"
Belief: p(door_unlocked) = 0.95 (too confident!)

New game: Door is actually locked
Agent tries door → FAILS → confused
```

**Protocol: ICARUS (Enforce Skepticism)**
```python
if state == HUBRIS:
    # Force some exploration even when confident
    β = max(β, 3.0)  # Minimum info-seeking
    # "Check your assumptions"
```

**6. ESCALATION (System Failure)**

**Trigger:**
- 3+ PANIC states in last 5 steps
- 2+ DEADLOCK states in last 10 steps
- Lyapunov divergence (belief updates oscillating)

**Protocol: STOP_AND_ESCALATE**
```python
if state == ESCALATION:
    raise AgentEscalationError("Cannot solve, requesting help")
    # In production: Call human supervisor
    # In research: Log failure mode for analysis
```

### 3.3 Hippocampus: Episodic Memory for TextWorld

#### Why Episodic Memory is CRITICAL for TextWorld

**The problem:**
- TextWorld has sparse rewards → slow learning
- Need 100s of episodes to learn "take key before trying door"
- Expensive in episode count

**The solution: Counterfactual Replay**

#### How It Works

**1. Store Episode Path:**
```python
episode = {
    'actual_path': [
        ('kitchen', 'examine door'),
        ('kitchen', 'go north'),  # FAILED - door locked
        ('kitchen', 'take key'),
        ('kitchen', 'unlock door with key'),
        ('bedroom', 'WON')
    ],
    'outcome': 'success',
    'steps': 5
}
```

**2. Generate Counterfactuals (Offline):**
```python
counterfactuals = [
    {
        'path': [
            ('kitchen', 'take key'),  # ← Do this FIRST
            ('kitchen', 'unlock door with key'),
            ('bedroom', 'WON')
        ],
        'outcome': 'success',
        'steps': 3  # ← Better!
    },
    {
        'path': [
            ('kitchen', 'go north'),  # ← Try without key
            ('kitchen', 'FAILED - locked')
        ],
        'outcome': 'failure',
        'steps': 2
    }
]
```

**3. Learn from Comparison:**
```python
# Update skill priors:
# - "take key first" → better than "try door first"
# - Success rate: take_key_then_unlock = 90%
# - Success rate: try_without_key = 10%

# Next episode: Prefer "take key" early
```

**Key insight:** Learn from 1 episode as if you played 5+ episodes!

#### TextWorld-Specific Counterfactuals

**Quest: Find treasure in chest**

**Actual path (failed):**
```
1. examine chest → "locked"
2. try chest → "need key"
3. look → "you see a desk"
4. examine desk → "drawer is closed"
5. open drawer → "you find a small key"
6. take key → "taken"
7. unlock chest with key → "wrong key"
8. MAX_STEPS → FAILED
```

**Counterfactual 1 (explore first):**
```
1. look → "desk, chest, window"
2. examine desk → "drawer"
3. open drawer → "small key"
4. examine window → "ledge outside"
5. examine ledge → "rusty key!"  ← FOUND RIGHT KEY
6. take rusty key
7. unlock chest with rusty key → WON (7 steps)
```

**Learning:** "Examine everything before committing to an action path"

**Counterfactual 2 (wrong first):**
```
1. try chest → "locked"
2. examine desk → "drawer"
... same path ...
7. unlock chest with small key → "wrong key"
8. examine window → "too late, out of steps"
```

**Learning:** "Don't try chest first - gather info first"

#### Memory Integration

**Update procedural memory:**
```python
skills = {
    'examine_first': {
        'context': 'uncertain_about_objects',
        'success_rate': 0.85,  # High!
        'uses': 12
    },
    'try_directly': {
        'context': 'uncertain_about_objects',
        'success_rate': 0.30,  # Low!
        'uses': 8
    }
}

# Next episode: Strongly prefer 'examine_first'
```

### 3.4 Procedural Memory: Skill Learning

#### TextWorld Skill Taxonomy

**Information-Gathering Skills:**
```python
skills_exploration = [
    'look',                  # General room scan
    'inventory',             # Check possessions
    'examine <object>',      # Inspect details
    'search <container>',    # Check contents
]

# Cost: 1 step
# Goal value: 0
# Info gain: HIGH
```

**Goal-Directed Skills:**
```python
skills_pragmatic = [
    'take <object>',         # Acquire item
    'unlock <door> with <key>',  # Access new area
    'open <container>',      # Access contents
    'go <direction>',        # Navigate
]

# Cost: 1 step
# Goal value: HIGH
# Info gain: MEDIUM
```

**Balanced Skills:**
```python
skills_balanced = [
    'take <object> then examine',  # Pragmatic + epistemic
    'try <door> then examine',     # Test + learn
]

# Cost: 1-2 steps
# Goal value: MEDIUM
# Info gain: MEDIUM
```

#### Context-Specific Learning

**The key innovation: Context matters!**

```python
# WRONG: Global statistics
skill_stats = {
    'try_door': {
        'global_success_rate': 0.5  # Meaningless!
    }
}

# RIGHT: Context-specific statistics
skill_stats = {
    'try_door': {
        'when_confident_unlocked': {
            'success_rate': 0.95,  # Usually works!
            'uses': 20
        },
        'when_uncertain': {
            'success_rate': 0.48,  # Coin flip
            'uses': 25
        },
        'when_confident_locked': {
            'success_rate': 0.05,  # Almost never
            'uses': 15
        }
    }
}
```

**Usage in decision-making:**
```python
# Current situation: Uncertain about door
context = 'when_uncertain'
stats = skill_stats['try_door'][context]

if stats['success_rate'] < 0.5:
    # Memory suggests: Don't try directly
    # Prefer: 'examine door first'
    override_to_examination()
```

---

## Part 4: Complete Agent Architecture for TextWorld

### The Full Stack

```
┌─────────────────────────────────────────────────────┐
│  ESCALATION CIRCUIT BREAKER                         │
│  (Halts if meta-cognition fails)                    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  BRAINSTEM (Critical State Monitor)                 │
│  ┌────────────┬──────────┬──────────┬────────────┐  │
│  │ PANIC      │ DEADLOCK │ SCARCITY │ NOVELTY    │  │
│  │ (Tank)     │ (Sisyphus)│(Spartan)│ (Eureka)   │  │
│  └────────────┴──────────┴──────────┴────────────┘  │
│         ▲                                            │
│         │ Monitors: entropy, loops, steps, errors   │
│         │                                            │
└─────────┼────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────┐
│  CORTEX (Active Inference Decision Loop)             │
│                                                       │
│  1. Observe: Parse text → Update beliefs             │
│  2. Score: EFE(action) = α*goal + β*info - γ*cost    │
│  3. Modulate: Apply procedural memory bonus          │
│  4. Act: Execute highest-EFE action                  │
│  5. Learn: Update beliefs from observation           │
└───────────────────────┬───────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
┌────────▼─────┐ ┌──────▼──────┐ ┌────▼──────────┐
│ EPISODIC     │ │ PROCEDURAL  │ │ BELIEF        │
│ MEMORY       │ │ MEMORY      │ │ STATE         │
│              │ │             │ │               │
│ Stores:      │ │ Stores:     │ │ Tracks:       │
│ - Episodes   │ │ - Skill     │ │ - Room map    │
│ - Counter-   │ │   stats     │ │ - Object locs │
│   factuals   │ │ - Context   │ │ - Quest state │
│ - Patterns   │ │   priors    │ │ - Uncertainty │
└──────────────┘ └─────────────┘ └───────────────┘
```

### Decision Flow (Single Step)

```python
def textworld_decision_step(agent, observation, admissible_commands):
    # 1. HIPPOCAMPUS: Update beliefs from observation
    beliefs = agent.update_beliefs(observation)
    
    # 2. CORTEX: Score all actions
    scored_actions = []
    for action in admissible_commands:
        # Base EFE score
        efe = score_efe(action, beliefs, quest)
        
        # 3. PROCEDURAL MEMORY: Add empirical bonus
        context = infer_context(beliefs)
        stats = get_skill_stats(action, context)
        memory_bonus = stats['success_rate'] * 2.0
        
        total_score = efe + memory_bonus
        scored_actions.append((total_score, action))
    
    # 4. BRAINSTEM: Check critical states
    agent_state = AgentState(
        entropy=calculate_entropy(beliefs),
        history=agent.recent_actions,
        steps=agent.steps_remaining,
        dist=estimate_distance_to_goal(beliefs, quest),
        rewards=agent.reward_history,
        error=agent.prediction_error
    )
    
    critical = monitor.evaluate(agent_state)
    
    # 5. Apply protocol override if needed
    if critical == PANIC:
        # Filter to safe actions only
        scored_actions = [(s, a) for s, a in scored_actions 
                          if is_safe_action(a)]
    
    elif critical == DEADLOCK:
        # Remove recently tried actions
        forbidden = set(agent.recent_actions[-5:])
        scored_actions = [(s, a) for s, a in scored_actions 
                          if a not in forbidden]
    
    elif critical == ESCALATION:
        # Halt and request help
        raise AgentEscalationError("Cannot proceed")
    
    # 6. Select best action
    scored_actions.sort(reverse=True)
    best_score, best_action = scored_actions[0]
    
    return best_action
```

---

## Part 5: Competitive Advantages Over Standard Approaches

### vs. Pure RL (DQN/PPO)

**Standard RL approach:**
```python
# Black-box policy
action = policy_network(text_embedding)

# Problems:
# - No interpretability (why this action?)
# - No explicit planning (reactive only)
# - Slow learning (needs 1000s of episodes)
# - Brittle (fails on new scenarios)
```

**Our approach:**
```python
# Interpretable active inference
action, reasoning = agent.select_with_explanation(beliefs)

# Advantages:
# ✓ Explainable (can show EFE breakdown)
# ✓ Plans ahead (estimates goal distance)
# ✓ Fast learning (counterfactual replay)
# ✓ Robust (critical state protocols)
```

**Example output:**
```
Selected: "examine key"
Reasoning:
  - EFE breakdown:
    • Goal value: 0.3 (helps with quest indirectly)
    • Info gain: 0.8 (HIGH - uncertain about key type)
    • Cost: -0.1 (low cost action)
    • Total EFE: 0.3*10 + 0.8*5 - 0.1 = 6.9
  - Memory bonus: +1.5 (examine_first succeeded 85% historically)
  - Critical state: FLOW (normal operation)
  - Final score: 8.4
```

### vs. Language Models (GPT-based)

**LLM approach:**
```python
prompt = f"You are playing a text game. {observation}. What do you do?"
action = gpt4(prompt)

# Problems:
# - Hallucinates invalid commands
# - No learning (stateless)
# - No planning (one-step greedy)
# - Expensive (API costs)
```

**Our approach:**
```python
# Bayesian belief maintenance
beliefs = agent.infer_state(observation)
action = agent.plan_with_beliefs(beliefs, quest)

# Advantages:
# ✓ Only valid actions (constrained by admissible set)
# ✓ Learns from experience (episodic memory)
# ✓ Multi-step planning (estimates goal distance)
# ✓ Efficient (local inference, no API)
```

### vs. Symbolic Planners (PDDL-based)

**Planner approach:**
```python
# Requires perfect world model
world_model = {
    'door': {'locked': True},
    'key': {'location': 'table'},
    'unlock': {'precondition': has_key, 'effect': door_unlocked}
}
plan = planner.solve(world_model, goal)

# Problems:
# - Needs perfect knowledge (unrealistic)
# - Brittle (any error breaks plan)
# - No uncertainty handling
# - No adaptation
```

**Our approach:**
```python
# Probabilistic beliefs
beliefs = {
    'door': {'locked': 0.9, 'unlocked': 0.1},  # Uncertain!
    'key': {'location_table': 0.7, 'location_drawer': 0.3}
}
action = agent.act_under_uncertainty(beliefs, quest)

# Advantages:
# ✓ Handles partial observability
# ✓ Robust to errors (updates beliefs)
# ✓ Quantifies uncertainty
# ✓ Adapts dynamically
```

---

## Part 6: Research Contributions & Publication Potential

### What Makes This Novel?

**1. First Bicameral Architecture for Interactive Fiction**
- No prior work applies cortex/brainstem split to text games
- Novel: Meta-cognitive oversight for language environments

**2. Active Inference with Natural Language**
- Most active inference work: robotics, grid worlds
- This: Symbolic/linguistic action spaces (new domain)

**3. Counterfactual Learning Without Re-simulation**
- Standard episodic memory: Replay actual trajectories
- This: Generate alternatives offline (sample-efficient)

**4. Context-Aware Skill Learning**
- Standard: Global skill statistics
- This: Belief-context conditional statistics (e.g., "when_uncertain")

**5. Critical State Protocols for Planning**
- Standard: Binary safe/unsafe
- This: 5 distinct metacognitive states with named responses

### Expected Performance Gains

**Hypothesis:**

| Metric | Standard RL | LLM-based | Our Framework | Improvement |
|:---|---:|---:|---:|---:|
| **Sample Efficiency** | 1000 episodes | N/A | 100 episodes | **10×** |
| **Success Rate** | 30% | 45% | 75% | **2.5×** |
| **Average Steps** | 25 | 15 | 8 | **3×** |
| **Zero-shot Transfer** | 10% | 60% | 80% | **8×** |
| **Interpretability** | 0% | 20% | 95% | **∞** |

**Why these gains?**
- Sample efficiency: Counterfactual replay (learn from 1 episode as if 10)
- Success rate: Critical state protocols (avoid deadlocks)
- Steps: Active inference (systematic info-gathering, not random)
- Transfer: Belief-based reasoning (not scenario-memorization)
- Interpretability: Explicit EFE scoring + protocol logging

### Publication Venues

**Top-tier:**
1. **NeurIPS** - Active Inference + Meta-Cognition angle
2. **ICML** - Sample-efficient RL angle
3. **ICLR** - Cognitive architecture angle
4. **AAAI** - Symbolic+sub-symbolic integration

**Domain-specific:**
5. **ACL/EMNLP** - Language grounding angle
6. **CoRL** - Cognitive robotics (if extended to embodiment)

**Title suggestion:**
"Bicameral Active Inference for Interactive Fiction: Meta-Cognitive Protocols for Sample-Efficient Text Game Solving"

---

## Part 7: Implementation Roadmap

### Phase 1: Core Integration (Week 1)

**Goal:** Get agent playing TextWorld games

**Tasks:**
1. ✅ TextWorld adapter (DONE)
2. ✅ Graph schema (DONE)
3. ⏭️ Belief state representation
   - Implement: Room map tracking
   - Implement: Object location beliefs
   - Implement: Quest progress tracking

4. ⏭️ EFE scoring for commands
   - Adapt existing `score_skill()` function
   - Add: Text-based goal value estimation
   - Add: Text-based info gain estimation

**Deliverable:** Agent completes simple 3-room quests (>50% success)

### Phase 2: Critical State Integration (Week 2)

**Goal:** Add meta-cognitive oversight

**Tasks:**
1. ⏭️ Map TextWorld metrics to AgentState
   - Entropy: From belief uncertainty
   - Distance: Estimated steps to quest completion
   - Prediction error: Text parse surprises

2. ⏭️ Implement TextWorld-specific protocols
   - PANIC: Too many commands → simplify
   - DEADLOCK: Repeated actions → force novelty
   - SCARCITY: Low steps → goal-only mode

3. ⏭️ Test protocol triggers
   - Create adversarial quests (force each protocol)
   - Verify: Baseline fails, Critical succeeds

**Deliverable:** Agent handles complex scenarios (loops, confusion)

### Phase 3: Episodic Memory (Week 3)

**Goal:** Enable counterfactual learning

**Tasks:**
1. ⏭️ Adapt counterfactual generator for TextWorld
   - Input: Episode path (room sequence + actions)
   - Output: Alternative paths (swap action order, try different objects)

2. ⏭️ Implement offline learning
   - After each episode: Generate 5 counterfactuals
   - Compare: Actual vs alternatives
   - Update: Skill priors ("examine_first" better than "try_directly")

3. ⏭️ Test sample efficiency
   - Baseline: 100 episodes to learn
   - With memory: 10 episodes to learn (10× gain)

**Deliverable:** Agent learns from 1 episode as if played 10

### Phase 4: Validation & Comparison (Week 4)

**Goal:** Prove superiority over baselines

**Tasks:**
1. ⏭️ Implement baselines
   - Random policy
   - Standard DQN
   - GPT-4 prompted
   - Symbolic planner

2. ⏭️ Generate test suite
   - Simple quests (3 rooms, 1 key)
   - Medium quests (5 rooms, 3 objects, 2 keys)
   - Hard quests (10 rooms, chains of unlocks)

3. ⏭️ Run statistical comparison
   - 100 trials per agent per quest type
   - Metrics: Success rate, steps, episodes to learn

**Deliverable:** Data for publication (our framework wins)

---

## Part 8: Strategic Recommendations

### Recommendation 1: Start Simple, Scale Up

**Approach:**
1. **Week 1:** Single-room quests ("take key, unlock chest")
2. **Week 2:** Multi-room quests (navigation required)
3. **Week 3:** Chain quests ("key1 unlocks door1 → room2 has key2 → key2 unlocks chest")
4. **Week 4:** Full TextWorld complexity

**Why:** Build confidence incrementally, debug early

### Recommendation 2: Prioritize Interpretability

**Every decision should be explainable:**
```python
log = {
    'step': 5,
    'observation': "You see a rusty key",
    'beliefs': {'key_type': 'rusty', 'p_unlocks_door': 0.8},
    'scored_actions': [
        {'action': 'take key', 'EFE': 8.5, 'reason': 'high goal value'},
        {'action': 'examine key', 'EFE': 6.0, 'reason': 'moderate info gain'},
    ],
    'critical_state': 'FLOW',
    'selected': 'take key',
    'reason': 'Highest EFE + memory suggests this works 90% of time'
}
```

**Why:** Makes debugging trivial, reviewers love it

### Recommendation 3: Embrace Failure Modes

**Don't hide failures - analyze them:**

**Example failure log:**
```
Episode 47: ESCALATION triggered
Reason: Agent tried 'go north' 8 times (DEADLOCK → PANIC → ESCALATION)
Root cause: No "try different direction" skill in action set
Fix: Add exploration skills
Result: Episode 48 succeeds
```

**Why:** Failures are learning opportunities for both agent AND researchers

### Recommendation 4: Compare to GPT-4 Directly

**This is the killer demo:**

**Setup:**
- Same quest given to both agents
- Show side-by-side execution
- Our agent: Systematic, explains reasoning
- GPT-4: Random, hallucinates, no learning

**Expected result:**
```
Our Agent:
  Step 1: "examine room" [Info-seeking, entropy=0.9]
  Step 2: "take key" [Pragmatic, key spotted]
  Step 3: "unlock door with key" [Goal, WIN]
  Result: 3 steps, explained every choice

GPT-4:
  Step 1: "unlock door with magic wand" [Hallucinated item!]
  Step 2: "cast fireball" [Invalid command]
  Step 3: "take key" [Finally valid]
  Step 4: "examine key" [Why? Goal is right there]
  Step 5: "unlock door with key" [WIN after confusion]
  Result: 5 steps, no learning for next game
```

**Why:** Shows cognitive architecture beats pure language models

---

## Part 9: Success Criteria

### How to Know If This Works

**Tier 1: Basic Competence**
- [ ] Agent completes simple quests (3 rooms) >70% of time
- [ ] Agent learns from experience (episode 100 better than episode 1)
- [ ] Agent explains decisions (interpretable logs)

**Tier 2: Protocol Validation**
- [ ] PANIC triggers in high-complexity scenarios and simplifies successfully
- [ ] DEADLOCK breaks loops within 3 steps
- [ ] SCARCITY mode achieves goals faster (vs baseline)
- [ ] No ESCALATION on solvable quests (stable)

**Tier 3: Memory Validation**
- [ ] Counterfactuals improve learning (10 episodes w/ memory = 100 w/out)
- [ ] Procedural memory adapts to context (skill preferences change correctly)
- [ ] Transfer learning works (skills from quest A help on quest B)

**Tier 4: Competitive Performance**
- [ ] Beats random baseline by 5× success rate
- [ ] Beats DQN by 2× sample efficiency
- [ ] Beats GPT-4 by 1.5× success rate + 100% interpretability
- [ ] Matches/beats state-of-the-art TextWorld agents

**Tier 5: Research Contribution**
- [ ] Novel architecture (no prior bicameral IF agents)
- [ ] Publishable results (NeurIPS/ICML caliber)
- [ ] Reproducible (code + data released)
- [ ] Influential (citations in 2 years)

---

## Part 10: Final Strategic Thoughts

### Why This Matters Beyond TextWorld

**TextWorld is a stepping stone to:**

1. **Real-world dialogue systems**
   - Customer service bots with meta-cognition
   - Tutorial systems that detect student confusion (PANIC)
   - Negotiation agents that avoid deadlocks (SISYPHUS)

2. **Embodied AI**
   - Robots navigating via language instructions
   - "Go to the kitchen" → belief updates + planning
   - Critical states prevent physical damage (ESCALATION)

3. **Game AI**
   - NPCs in RPGs with believable reasoning
   - Adaptive difficulty (detect player PANIC, simplify)
   - Storytelling agents that learn player preferences

4. **AI Safety**
   - Interpretable decision-making (EFE transparency)
   - Safe exploration (critical state protocols)
   - Graceful degradation (ESCALATION circuit breaker)

**The architecture is general. TextWorld proves it.**

### The Killer Insight

**Most AI research:** "How do we make agents smarter?"

**This project:** "How do we make agents AWARE of when they're confused?"

**TextWorld demonstrates:** An agent that knows when it's stuck is more valuable than an agent that's occasionally brilliant but usually lost.

**The bicameral divide:**
- **Cortex:** Be as smart as possible (active inference, planning)
- **Brainstem:** Know when smartness isn't enough (meta-cognition)

**This is the future of robust AI.**

---

## Conclusion

### To Summarize

**TextWorld challenges:**
1. Natural language ✓ (Handled by text parsing + belief updates)
2. Combinatorial actions ✓ (Handled by skill abstraction)
3. Sparse rewards ✓ (Handled by info-seeking + counterfactuals)
4. Partial observability ✓ (Handled by Bayesian beliefs)
5. Long-term planning ✓ (Handled by active inference EFE)
6. Generalization ✓ (Handled by context-aware memory)

**Framework strengths:**
- Active Inference: Natural fit for partial observability + planning
- Critical States: Robustness against confusion/loops/failure
- Episodic Memory: Sample-efficient learning via counterfactuals
- Procedural Memory: Context-specific skill refinement
- Interpretability: Explainable every decision

**Expected outcomes:**
- 10× sample efficiency vs standard RL
- 2-3× success rate vs baselines
- 100% interpretability vs black boxes
- Publication-quality results

**Strategic approach:**
1. Start simple (single-room quests)
2. Add complexity incrementally
3. Validate each protocol independently
4. Compare to strong baselines (GPT-4, DQN)
5. Publish results (NeurIPS/ICML)

**This is not just another TextWorld agent.**

**This is:**
- A proof that bicameral architectures generalize beyond toy MDPs
- A demonstration that meta-cognition beats pure optimization
- A foundation for robust, interpretable AI in language domains
- A research contribution worthy of top-tier publication

**The architecture is ready. The domain is perfect. The time is now.**

---

**Document Status:** Strategic foundation complete  
**Confidence:** Very high (architecture-domain fit is exceptional)  
**Next Action:** Implement Phase 1 (core integration)  
**Expected Timeline:** 4 weeks to publication-ready results

**Let's build the future of cognitive agents.**
