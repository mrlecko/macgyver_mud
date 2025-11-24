# TextWorld Integration: Complete Implementation Plan

**Project:** MacGyver MUD - Domain 4 Addition  
**Domain:** TextWorld (Interactive Fiction / Text-based Adventures)  
**Timeline:** 2-3 weeks  
**Difficulty:** Medium-High  
**Status:** Ready to Implement

---

## Executive Summary

**Goal:** Add TextWorld as the 4th validation domain to showcase Critical State Protocols on graph-based, multi-step planning tasks with natural language.

**Why TextWorld is PERFECT:**
- ✅ **Graph structure** - Rooms, objects, relationships (Neo4j native!)
- ✅ **Named skills** - "take key", "unlock door", "examine painting" (skill system!)
- ✅ **Multi-step planning** - Quests require sequences (planning!)
- ✅ **Episodic memory** - "What if I examined the painting first?" (counterfactuals!)
- ✅ **Interpretability** - Natural language (reviewers understand!)
- ✅ **Symbolic reasoning** - "key unlocks door" (knowledge graphs!)

**Success Criteria:**
- [ ] TextWorld games run successfully
- [ ] Graph schema stores game state in Neo4j
- [ ] All 5 critical states can trigger
- [ ] Baseline vs. Critical comparison shows skill learning
- [ ] Episodic memory generates meaningful counterfactuals
- [ ] Documentation complete

---

## Table of Contents

1. [Why TextWorld Over CartPole](#why-textworld-over-cartpole)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Environment Setup](#phase-1-environment-setup)
4. [Phase 2: Graph Schema Design](#phase-2-graph-schema-design)
5. [Phase 3: TextWorld Adapter](#phase-3-textworld-adapter)
6. [Phase 4: Skill Mapping](#phase-4-skill-mapping)
7. [Phase 5: Critical State Mapping](#phase-5-critical-state-mapping)
8. [Phase 6: Agent Integration](#phase-6-agent-integration)
9. [Phase 7: Episodic Memory Integration](#phase-7-episodic-memory-integration)
10. [Phase 8: Testing](#phase-8-testing)
11. [Phase 9: Validation](#phase-9-validation)
12. [Phase 10: Documentation](#phase-10-documentation)
13. [Troubleshooting](#troubleshooting)

---

## Why TextWorld Over CartPole

### Architectural Fit Comparison

| Feature | MacGyver MUD | TextWorld | CartPole |
|:---|:---:|:---:|:---:|
| **Graph reasoning** | ✓✓✓ | ✓✓✓ | ✗ |
| **Skill composition** | ✓✓✓ | ✓✓✓ | ✗ |
| **Multi-step planning** | ✓✓✓ | ✓✓✓ | ✗ |
| **Episodic memory** | ✓✓✓ | ✓✓✓ | ✗ |
| **Counterfactuals** | ✓✓✓ | ✓✓✓ | ✗ |
| **Named actions** | ✓✓✓ | ✓✓✓ | ✗ |
| **Belief tracking** | ✓✓✓ | ✓✓ | ✗ |
| **Neo4j integration** | ✓✓✓ | ✓✓✓ | ✗ |
| **Natural language** | ✓ | ✓✓✓ | ✗ |
| **Interpretable** | ✓✓✓ | ✓✓✓ | ✗ |

**Verdict:** TextWorld showcases **10/10** architecture features vs. CartPole's **0/10**

### What TextWorld Proves That CartPole Doesn't

**TextWorld demonstrates:**
1. Graph-based knowledge representation
2. Symbolic reasoning ("key unlocks door")
3. Skill composition ("go to room → take key → go to door → unlock")
4. Meaningful counterfactuals ("what if I examined the painting?")
5. Multi-step planning under uncertainty
6. Transfer learning across different quests

**CartPole only demonstrates:**
1. Critical states trigger on continuous dynamics (already proven by Labyrinth)

---

## Prerequisites

### Required Knowledge

- [ ] Familiar with MacGyver MUD architecture
- [ ] Understanding of Critical State Protocols
- [ ] Basic graph theory (nodes, edges, relationships)
- [ ] Interactive fiction concepts (rooms, objects, actions)

### Required Tools

- [ ] Python 3.11+
- [ ] Neo4j running
- [ ] Git

### Time Commitment

- **Minimum:** 40 hours over 2 weeks
- **Recommended:** 60-80 hours over 3 weeks
- **Maximum:** 100 hours if learning + experimenting

---

## Phase 1: Environment Setup

**Duration:** 2-4 hours  
**Difficulty:** Easy

### Step 1.1: Install TextWorld

TextWorld is developed by Microsoft Research.

**Installation:**

```bash
cd /path/to/macgyver_mud

# Install TextWorld
pip install textworld

# Verify installation
python3 -c "import textworld; print(textworld.__version__)"
```

**Note:** TextWorld has dependencies on `tatsu`, `networkx`, `numpy`, etc. These should install automatically.

### Step 1.2: Test TextWorld Game Generation

**Create test script:** `scratch/test_textworld.py`

```python
"""
Test TextWorld installation and game generation.
"""
import textworld

# Generate a simple game
options = textworld.GameOptions()
options.nb_rooms = 3
options.nb_objects = 5
options.quest_length = 3
options.seed = 42

game = textworld.generator.make_game(options)

# Save game
game_file = textworld.generator.compile_game(game, path="./scratch/test_game.z8")
print(f"Game created: {game_file}")

# Load and play
env = textworld.start(game_file)
game_state = env.reset()

print("\nGame State:")
print(game_state)
print("\nInitial observation:")
print(game_state.description)
print(f"\nAvailable commands: {game_state.admissible_commands}")

# Try an action
game_state, reward, done = env.step("inventory")
print(f"\nAfter 'inventory': {game_state.feedback}")

env.close()
```

### Step 1.3: Understand TextWorld Structure

**Game Components:**

```python
# TextWorld game structure
game = {
    'rooms': [
        {'name': 'Kitchen', 'description': '...'},
        {'name': 'Bedroom', 'description': '...'},
    ],
    'objects': [
        {'name': 'key', 'location': 'Kitchen'},
        {'name': 'door', 'state': 'locked'},
    ],
    'connections': [
        {'from': 'Kitchen', 'to': 'Bedroom', 'direction': 'north'},
    ],
    'quest': {
        'goal': 'Unlock the door and take the treasure',
        'steps': ['take key', 'unlock door', 'go to bedroom', 'take treasure']
    }
}
```

**State Representation:**

```python
game_state = {
    'description': "You are in a kitchen...",  # Natural language
    'feedback': "You take the key.",           # Action result
    'inventory': ['key'],                      # Agent's items
    'score': 0,                                # Current score
    'max_score': 1,                            # Maximum possible
    'done': False,                             # Episode complete?
    'admissible_commands': ['go north', 'take knife', ...]  # Valid actions
}
```

✅ **Checkpoint:** TextWorld installation verified

---

## Phase 2: Graph Schema Design

**Duration:** 4-8 hours  
**Difficulty:** Medium

### Step 2.1: Design Neo4j Schema for TextWorld

**Node Types:**

```cypher
// Rooms
(r:TextWorldRoom {
    id: string,
    name: string,
    description: string,
    visited: boolean
})

// Objects
(o:TextWorldObject {
    id: string,
    name: string,
    type: string,  // container, door, item, etc.
    state: string,  // open, closed, locked, etc.
    takeable: boolean,
    portable: boolean
})

// Actions (for episodic memory)
(a:TextWorldAction {
    action_text: string,
    timestamp: int,
    success: boolean,
    reward: float
})
```

**Relationship Types:**

```cypher
// Spatial connections
(r1:TextWorldRoom)-[:CONNECTS_TO {direction: 'north'}]->(r2:TextWorldRoom)

// Object locations
(o:TextWorldObject)-[:LOCATED_IN]->(r:TextWorldRoom)
(o:TextWorldObject)-[:IN_INVENTORY]->(agent)

// Object states
(key:TextWorldObject)-[:UNLOCKS]->(door:TextWorldObject)
(container:TextWorldObject)-[:CONTAINS]->(item:TextWorldObject)

// Episodic memory
(episode)-[:PERFORMED]->(action)
(action)-[:IN_ROOM]->(room)
(action)-[:WITH_OBJECT]->(object)
```

### Step 2.2: Create Schema Initialization

**File:** `environments/domain4_textworld/graph_schema.py`

```python
"""
Neo4j schema for TextWorld integration.
"""
from neo4j import Session

class TextWorldGraphSchema:
    """Manages Neo4j schema for TextWorld."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def initialize_schema(self):
        """Create constraints and indexes."""
        # Room constraints
        self.session.run("""
            CREATE CONSTRAINT textworld_room_id IF NOT EXISTS
            FOR (r:TextWorldRoom) REQUIRE r.id IS UNIQUE
        """)
        
        # Object constraints
        self.session.run("""
            CREATE CONSTRAINT textworld_object_id IF NOT EXISTS
            FOR (o:TextWorldObject) REQUIRE o.id IS UNIQUE
        """)
        
        # Indexes for fast lookup
        self.session.run("""
            CREATE INDEX textworld_room_name IF NOT EXISTS
            FOR (r:TextWorldRoom) ON (r.name)
        """)
    
    def clear_game_state(self):
        """Remove all TextWorld nodes (for fresh game)."""
        self.session.run("""
            MATCH (n:TextWorldRoom) DETACH DELETE n
        """)
        self.session.run("""
            MATCH (n:TextWorldObject) DETACH DELETE n
        """)
    
    def store_game_world(self, game):
        """
        Store TextWorld game structure in Neo4j.
        
        Converts TextWorld's internal representation to graph.
        """
        self.clear_game_state()
        
        # Store rooms
        for room in game.world.rooms:
            self.session.run("""
                CREATE (r:TextWorldRoom {
                    id: $id,
                    name: $name,
                    description: $desc,
                    visited: false
                })
            """, id=room.id, name=room.name, desc=str(room))
        
        # Store connections
        for room in game.world.rooms:
            for direction, exit in room.exits.items():
                self.session.run("""
                    MATCH (r1:TextWorldRoom {id: $from_id})
                    MATCH (r2:TextWorldRoom {id: $to_id})
                    CREATE (r1)-[:CONNECTS_TO {direction: $dir}]->(r2)
                """, from_id=room.id, to_id=exit.dest.id, dir=direction)
        
        # Store objects
        for obj in game.world.objects:
            self.session.run("""
                CREATE (o:TextWorldObject {
                    id: $id,
                    name: $name,
                    type: $type
                })
            """, id=obj.id, name=obj.name, type=obj.type)
```

✅ **Checkpoint:** Graph schema designed

---

## Phase 3: TextWorld Adapter

**Duration:** 8-12 hours  
**Difficulty:** Medium-High

### Step 3.1: Create Adapter Class

**File:** `environments/domain4_textworld/textworld_adapter.py`

```python
"""
TextWorld adapter for Critical State Protocol integration.
"""
import textworld
import numpy as np
from neo4j import Session
from critical_state import AgentState
from environments.domain4_textworld.graph_schema import TextWorldGraphSchema

class TextWorldCriticalStateAdapter:
    """
    Adapter for TextWorld to work with Critical State Protocols.
    
    Key responsibilities:
    1. Generate/load TextWorld games
    2. Manage game state
    3. Convert state to AgentState for critical monitoring
    4. Store world structure in Neo4j graph
    5. Track history for DEADLOCK/HUBRIS detection
    """
    
    def __init__(self, session: Session, game_options=None):
        self.session = session
        self.schema = TextWorldGraphSchema(session)
        self.schema.initialize_schema()
        
        # Game configuration
        if game_options is None:
            game_options = textworld.GameOptions()
            game_options.nb_rooms = 5
            game_options.nb_objects = 8
            game_options.quest_length = 5
            game_options.seed = 42
        
        self.game_options = game_options
        self.env = None
        self.game = None
        self.current_state = None
        
        # State tracking
        self.action_history = []
        self.observation_history = []
        self.reward_history = []
        self.inventory_history = []
        self.current_room_history = []
        
        # Maximum steps (prevent infinite episodes)
        self.max_steps = 100
        self.current_step = 0
    
    def generate_game(self, seed=None):
        """Generate a new TextWorld game."""
        if seed:
            self.game_options.seed = seed
        
        self.game = textworld.generator.make_game(self.game_options)
        game_file = textworld.generator.compile_game(
            self.game, 
            path=f"./scratch/tw_game_{seed or 42}.z8"
        )
        
        # Store in Neo4j
        self.schema.store_game_world(self.game)
        
        return game_file
    
    def reset(self, seed=None):
        """Reset environment with new or existing game."""
        # Generate game if needed
        if self.game is None or seed is not None:
            game_file = self.generate_game(seed)
        else:
            game_file = self.game.metadata.get('game_file')
        
        # Start environment
        if self.env:
            self.env.close()
        
        self.env = textworld.start(game_file)
        self.current_state = self.env.reset()
        
        # Reset tracking
        self.action_history = []
        self.observation_history = [self.current_state.description]
        self.reward_history = []
        self.inventory_history = [list(self.current_state.inventory)]
        self.current_step = 0
        
        return self.current_state
    
    def step(self, action):
        """Execute action and update state."""
        prev_state = self.current_state
        self.current_state, reward, done = self.env.step(action)
        
        # Track history
        self.action_history.append(action)
        self.observation_history.append(self.current_state.description)
        self.reward_history.append(reward)
        self.inventory_history.append(list(self.current_state.inventory))
        self.current_step += 1
        
        # Auto-terminate if too long
        if self.current_step >= self.max_steps:
            done = True
        
        return self.current_state, reward, done
    
    def calculate_entropy(self):
        """
        Calculate uncertainty based on game state.
        
        Higher entropy = more confusion/uncertainty
        """
        # Number of available actions (more actions = more uncertainty)
        num_actions = len(self.current_state.admissible_commands)
        action_entropy = min(1.0, num_actions / 20.0)  # Normalize
        
        # Progress (closer to goal = lower entropy)
        progress = self.current_state.score / max(self.current_state.max_score, 1)
        progress_entropy = 1.0 - progress
        
        # Inventory changes (learning about world)
        inv_size = len(self.current_state.inventory)
        inv_entropy = max(0.0, 1.0 - inv_size / 5.0)  # Assume ~5 items
        
        # Weighted combination
        entropy = (
            0.4 * action_entropy +
            0.4 * progress_entropy +
            0.2 * inv_entropy
        )
        
        return entropy
    
    def calculate_distance_to_goal(self):
        """
        Estimate distance to goal.
        
        Lower score = further from goal
        """
        max_score = max(self.current_state.max_score, 1)
        current_score = self.current_state.score
        
        # Distance = (max - current) scaled
        distance = (max_score - current_score) / max_score * 20
        return distance
    
    def calculate_prediction_error(self):
        """
        How unexpected was the last state transition?
        """
        if len(self.observation_history) < 2:
            return 0.0
        
        # Simple heuristic: did description change significantly?
        prev_desc = self.observation_history[-2]
        curr_desc = self.observation_history[-1]
        
        # Similarity check (simple)
        common_words = set(prev_desc.split()) & set(curr_desc.split())
        total_words = set(prev_desc.split()) | set(curr_desc.split())
        
        similarity = len(common_words) / max(len(total_words), 1)
        prediction_error = 1.0 - similarity
        
        return prediction_error
    
    def get_agent_state(self):
        """
        Convert TextWorld state to AgentState for critical monitoring.
        """
        entropy = self.calculate_entropy()
        distance = self.calculate_distance_to_goal()
        prediction_error = self.calculate_prediction_error()
        
        agent_state = AgentState(
            entropy=entropy,
            history=self.action_history[-10:],  # Last 10 actions
            steps=self.max_steps - self.current_step,
            dist=distance,
            rewards=self.reward_history[-10:],
            error=prediction_error
        )
        
        return agent_state
    
    def get_admissible_commands(self):
        """Get valid actions in current state."""
        return self.current_state.admissible_commands
    
    def close(self):
        """Clean up."""
        if self.env:
            self.env.close()
```

✅ **Checkpoint:** Adapter created

---

## Phase 4: Skill Mapping

**Duration:** 4-6 hours  
**Difficulty:** Medium

### TextWorld Actions as Skills

**Map TextWorld commands to skill abstraction:**

```python
SKILL_TEMPLATES = {
    # Navigation skills
    "navigate": ["go {direction}", "enter {room}"],
    
    # Object manipulation
    "take_item": ["take {object}", "pick up {object}"],
    "drop_item": ["drop {object}", "put down {object}"],
    "examine": ["examine {object}", "look at {object}"],
    
    # Containers
    "open_container": ["open {container}"],
    "close_container": ["close {container}"],
    "put_in": ["put {item} in {container}"],
    
    # Doors
    "unlock": ["unlock {door} with {key}"],
    "lock": ["lock {door} with {key}"],
    
    # Food
    "eat": ["eat {food}"],
    "cook": ["cook {food} with {appliance}"],
    
    # Light
    "turn_on": ["turn on {light}"],
    "turn_off": ["turn off {light}"],
}
```

**Skills integrate with existing MacGyver skill system!**

---

## Phase 5: Critical State Mapping

**Duration:** 4-6 hours  
**Difficulty:** Medium

### Critical State Triggers for TextWorld

| Critical State | Trigger Condition | TextWorld Interpretation |
|:---|:---|:---|
| **PANIC** | High uncertainty | Many commands, no progress |
| **SCARCITY** | steps < distance × 1.2 | Running out of moves before goal |
| **DEADLOCK** | Repeated actions | Trying same thing repeatedly (stuck) |
| **NOVELTY** | High prediction error | Unexpected room/object |
| **HUBRIS** | Success streak | Same solution works repeatedly |

**Example Implementations:**

```python
# PANIC: Too many options, no idea what to do
if len(admissible_commands) > 15 and score == 0:
    # Agent is confused
    critical_state = PANIC

# DEADLOCK: Repeating "go north, go south, go north"
if actions[-4:] == ['go north', 'go south', 'go north', 'go south']:
    critical_state = DEADLOCK

# NOVELTY: New room type seen
if "never seen before" in observation:
    critical_state = NOVELTY
```

---

## Phase 6-10: [Continued in next section due to length...]

**Remaining phases:**
- Agent Implementation
- Episodic Memory Integration
- Testing
- Validation
- Documentation

**See Section 2 of implementation plan for details.**

---

## Key Benefits Over CartPole

**Scientific:**
1. ✅ Tests graph reasoning (core feature)
2. ✅ Tests skill composition (unique capability)
3. ✅ Tests episodic memory meaningfully
4. ✅ Tests counterfactual generation
5. ✅ Tests natural language understanding

**Practical:**
1. ✅ More impressive demos (reviewers can understand)
2. ✅ Natural fit for Neo4j (showcase integration)
3. ✅ Enables future robot applications (symbolic planning)
4. ✅ Shows transfer learning (different quests)

**vs. CartPole:**
- CartPole: "Can balance a pole" (trivial, architectural overkill)
- TextWorld: "Can reason about quests in graph-based worlds" (showcases architecture)

---

## Timeline

### Week 1: Setup & Adapter
- Days 1-2: Install, test, understand TextWorld
- Days 3-4: Graph schema + adapter
- Day 5: Initial testing

### Week 2: Agent & Testing
- Days 6-7: Baseline and critical agents
- Days 8-9: Unit tests, integration
- Day 10: Episodic memory integration

### Week 3: Validation & Documentation
- Days 11-13: Run validation, analyze results
- Days 14-15: Documentation, polish

---

## Success Metrics

**Must Have:**
- [ ] TextWorld games run in Neo4j
- [ ] Critical states trigger appropriately
- [ ] Episodic memory generates counterfactuals
- [ ] Agent can solve simple quests
- [ ] Tests pass

**Should Have:**
- [ ] Better than baseline on complex quests
- [ ] Counterfactuals show learning
- [ ] Graph visualization of game world

**Nice to Have:**
- [ ] Transfer learning across quest types
- [ ] Natural language action suggestions

---

**Document Version:** 1.0  
**Created:** 2025-11-23  
**Status:** Ready to Execute

**This is the RIGHT domain for this architecture.**
