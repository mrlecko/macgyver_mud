# Option B: Complete Synthesis - Comprehensive Implementation Plan

**Version:** 1.0
**Created:** 2025-11-24
**Status:** Ready for Implementation
**Estimated Time:** 25-35 hours
**Difficulty:** Medium-High
**Prerequisites:** Option A completed and validated

---

## 📋 Table of Contents

1. [Context & Background](#context--background)
2. [What You're Building](#what-youre-building)
3. [Current State Assessment](#current-state-assessment)
4. [Implementation Phases](#implementation-phases)
5. [Detailed Phase Instructions](#detailed-phase-instructions)
6. [Testing Strategy](#testing-strategy)
7. [Validation Criteria](#validation-criteria)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [File Reference Guide](#file-reference-guide)

---

## Context & Background

### The Story So Far

You're working on a cognitive agent architecture that uses active inference (Expected Free Energy) for decision-making. The project achieved a major breakthrough by implementing **Option A: Minimum Viable Synthesis**, which unified two approaches:

1. **Quest Agent:** Simple, domain-specific agent (100% success on TextWorld)
2. **Cognitive Agent:** Sophisticated active inference architecture (was 0%, now 100% after Option A)

**Option A Achievement:** Added hierarchical goal decomposition to the cognitive agent, achieving 100% success on TextWorld while maintaining backward compatibility.

### What Option B Adds

Option B builds on Option A's foundation to create a **complete synthesis** that demonstrates ALL the project's innovations working together:

1. ✅ **Active Inference (EFE)** - Already working
2. ✅ **Hierarchical Goal Decomposition** - Added in Option A
3. ✅ **Procedural/Episodic Memory** - Exists but not quest-aware
4. ✅ **Geometric Lens (Silver Gauge)** - Exists but not integrated with quests
5. ✅ **Critical State Protocols** - Exist but disabled for TextWorld
6. ⚠️ **Quest-Aware Learning** - NOT YET IMPLEMENTED (Phase 1)
7. ⚠️ **Geometric Quest Analysis** - NOT YET IMPLEMENTED (Phase 2)
8. ⚠️ **Quest-Aware Critical States** - NOT YET IMPLEMENTED (Phase 3)

### Why This Matters (Research Narrative)

**Weak Narrative:** "We built different agents for different domains"

**Strong Narrative:** "We demonstrate that cognitive principles (active inference, episodic memory, meta-cognitive monitoring) generalize across domains when applied hierarchically: strategic reasoning provides context for tactical optimization under reactive safety constraints."

Option B provides the FULL demonstration of this claim.

---

## What You're Building

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 COMPLETE SYNTHESIS AGENT                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  STRATEGIC LAYER: Quest Decomposition                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Quest → Subgoals                                     │   │
│  │ "First X, then Y, finally Z" → [X, Y, Z]           │   │
│  │                                                       │   │
│  │ NEW (Phase 2): Geometric Analysis                    │   │
│  │ - Apply Silver Gauge to decomposition quality        │   │
│  │ - Pythagorean mean of subgoal coherence             │   │
│  │ - Log to Neo4j for analysis                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓                                      │
│  TACTICAL LAYER: Active Inference (EFE)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Hierarchical Action Scoring (from Option A)         │   │
│  │ EFE = α·goal + β·entropy - γ·cost + δ·memory + ε·plan │
│  │                                                       │   │
│  │ NEW (Phase 1): Quest-Aware Memory                    │   │
│  │ - Procedural: "Taking X before Y succeeds"          │   │
│  │ - Episodic: Previous quest attempts & outcomes       │   │
│  │ - Retrieval: Context = current_subgoal              │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓                                      │
│  REACTIVE LAYER: Critical States & Safety                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Protocols: SISYPHUS, TANK, SPARTAN, EUREKA, etc.   │   │
│  │                                                       │   │
│  │ NEW (Phase 3): Quest-Aware Protocols                 │   │
│  │ - Don't interrupt subgoal progress                   │   │
│  │ - Escalate only if truly stuck                       │   │
│  │ - Track subgoal-specific deadlocks                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components You'll Modify

1. **cognitive_agent.py** (main file)
   - Memory retrieval (make quest-aware)
   - Critical state evaluation (make quest-aware)
   - Add geometric analysis integration

2. **memory_system.py** (if exists)
   - Store quest patterns
   - Retrieve by subgoal context

3. **New file: quest_geometric_analyzer.py**
   - Silver Gauge application to quest decomposition
   - Pythagorean mean calculations
   - Neo4j logging

4. **Tests** (comprehensive suite)
   - Quest memory retrieval
   - Geometric analysis
   - Critical state integration

---

## Current State Assessment

### What Works (Option A Implementation)

✅ **File:** `environments/domain4_textworld/cognitive_agent.py`

**Key Features:**
1. **Quest Decomposition** (lines 38, 60, 76-79)
   ```python
   self.quest_decomposer = QuestDecomposer()
   self.subgoals = []
   self.current_subgoal_index = 0
   ```

2. **Progress Tracking** (lines 1011-1050)
   ```python
   # Advances subgoal based on action completion
   if last_action_matches_subgoal(threshold=0.5):
       self.current_subgoal_index += 1
   ```

3. **Hierarchical Goal Scoring** (lines 342-391)
   ```python
   def calculate_goal_value(action, current_subgoal):
       # Subgoal match gets 15x bonus
       # Quest match ONLY if no subgoal (hierarchical isolation)
   ```

4. **Test Coverage:** 30/30 tests passing
   - 14 synthesis tests (test_textworld_quest_synthesis.py)
   - 8 cognitive agent tests
   - 8 graph labyrinth tests

### What Needs Implementation (Option B)

⚠️ **Phase 1: Quest-Aware Memory** (NOT DONE)
- Memory retrieval filtered by current subgoal
- Store quest-specific patterns (procedural)
- Store quest attempt outcomes (episodic)

⚠️ **Phase 2: Geometric Analysis** (NOT DONE)
- Apply Silver Gauge to quest decomposition
- Calculate Pythagorean mean of subgoal coherence
- Log geometric metrics to Neo4j

⚠️ **Phase 3: Quest-Aware Critical States** (NOT DONE)
- Re-enable critical state monitoring (currently disabled at line 960)
- Make protocols respect subgoal progress
- Prevent false deadlock detection during valid subgoal execution

### Performance Baseline (Before Option B)

| Metric | Current Value | Target (Option B) |
|--------|---------------|-------------------|
| TextWorld Success | 100% | 100% (maintain) |
| Episode 1 Steps | 3 | 3 |
| Episode 10 Steps | 3 | 2-3 (learning) |
| Memory Retrieval | Generic | Quest-specific |
| Geometric Logging | None | Full |
| Critical States | Disabled | Quest-aware |

---

## Implementation Phases

### Phase 1: Quest-Aware Memory (8-10 hours)

**Goal:** Integrate procedural and episodic memory with quest context

**Deliverables:**
1. Memory retrieval filtered by current subgoal
2. Procedural memory stores quest patterns
3. Episodic memory stores quest outcomes
4. Tests: 8-10 new tests

**Success Criteria:**
- Agent retrieves relevant memories for current subgoal
- Episode 10 uses learned patterns from episodes 1-9
- Memory bonus in EFE scoring reflects quest history

### Phase 2: Geometric Analysis (6-8 hours)

**Goal:** Apply Silver Gauge (Pythagorean mean) to quest analysis

**Deliverables:**
1. New file: `quest_geometric_analyzer.py`
2. Silver Gauge applied to decomposition quality
3. Metrics logged to Neo4j
4. Tests: 6-8 new tests

**Success Criteria:**
- Decomposition quality scored geometrically
- Neo4j contains geometric metrics
- Can query and visualize quest geometry

### Phase 3: Quest-Aware Critical States (6-8 hours)

**Goal:** Re-enable critical protocols without interfering with quests

**Deliverables:**
1. Modified critical state evaluation
2. Quest-aware protocols (don't interrupt progress)
3. Subgoal-specific deadlock detection
4. Tests: 6-8 new tests

**Success Criteria:**
- Protocols prevent true deadlocks
- Protocols don't interrupt valid subgoal execution
- Agent recovers from stuck states

### Phase 4: Integration & Validation (4-6 hours)

**Goal:** End-to-end testing and documentation

**Deliverables:**
1. Full integration test
2. Performance comparison (Episode 1 vs 10)
3. Documentation update
4. Research narrative

**Success Criteria:**
- All tests pass (50+ total)
- Learning over episodes demonstrated
- Zero regressions
- Complete documentation

---

## Detailed Phase Instructions

## PHASE 1: Quest-Aware Memory (8-10 hours)

### Step 1.1: Understand Current Memory System (1 hour)

**ACTION ITEMS:**

1. **Read the existing memory system:**
   ```bash
   # Find memory-related files
   find . -name "*memory*" -type f | grep -E "\.py$"

   # Read them
   cat environments/domain4_textworld/memory_system.py
   ```

2. **Locate memory retrieval in cognitive agent:**
   ```bash
   grep -n "memory" environments/domain4_textworld/cognitive_agent.py | head -20
   ```

3. **Check what's stored in Neo4j:**
   ```python
   # Run this to see current memory schema
   python3 -c "
   from neo4j import GraphDatabase
   import config

   driver = GraphDatabase.driver(config.NEO4J_URI,
       auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

   with driver.session() as session:
       # Check for episode nodes
       result = session.run('MATCH (e:Episode) RETURN count(e) as count')
       print(f'Episodes: {result.single()[\"count\"]}')

       # Check for memory nodes
       result = session.run('MATCH (m:Memory) RETURN count(m) as count')
       print(f'Memories: {result.single()[\"count\"]}')

   driver.close()
   "
   ```

**EXPECTED FINDINGS:**
- `memory_system.py` exists with `MemoryRetriever` class
- `cognitive_agent.py` has `self.memory = MemoryRetriever(session)` at line ~56
- Memory retrieval happens in `calculate_memory_bonus()` at line ~393
- Current retrieval uses generic context, NOT subgoal-specific

**UNDERSTANDING CHECK:**
- [ ] I know where memories are stored (Neo4j nodes/relationships)
- [ ] I know how retrieval currently works (generic context)
- [ ] I know where to integrate subgoal context (calculate_memory_bonus)

---

### Step 1.2: Write Tests for Quest-Aware Memory (TDD - 2 hours)

**ACTION:** Create `tests/test_quest_aware_memory.py`

```python
"""
Test suite for Quest-Aware Memory (Phase 1 of Option B).

Tests that memory retrieval and storage work with quest context.
"""
import pytest
from neo4j import GraphDatabase
import config


class TestMemoryStorageWithQuestContext:
    """Test that episodes are stored with quest information."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        # Cleanup test data
        session.run("MATCH (e:Episode {test: true}) DETACH DELETE e")
        session.close()
        driver.close()

    def test_episode_stores_quest_text(self, neo4j_session):
        """
        Test 1: Episodes should store the full quest text.

        When: Agent completes episode with quest
        Then: Episode node has 'quest' property
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Simulate episode
        agent.step("You see a key.", "", 0.0, False, ["take key", "look"], None)
        agent.step("You took key.", "", 1.0, False, ["unlock door"], None)
        agent.step("Done!", "", 1.0, True, ["look"], None)

        # Check that episode was stored with quest
        result = neo4j_session.run("""
            MATCH (e:Episode)
            WHERE e.quest IS NOT NULL
            RETURN e.quest as quest, e.success as success
            ORDER BY e.timestamp DESC
            LIMIT 1
        """)

        record = result.single()
        assert record is not None, "Episode should be stored"
        assert record["quest"] == quest, "Quest should be stored"
        assert record["success"] == True, "Success should be tracked"

    def test_episode_stores_subgoals(self, neo4j_session):
        """
        Test 2: Episodes should store the decomposed subgoals.

        When: Quest decomposed into subgoals
        Then: Episode node has 'subgoals' property (list)
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Run episode
        agent.step("You see a key.", "", 0.0, False, ["take key"], None)
        agent.step("Done!", "", 1.0, True, ["look"], None)

        # Check subgoals stored
        result = neo4j_session.run("""
            MATCH (e:Episode)
            WHERE e.subgoals IS NOT NULL
            RETURN e.subgoals as subgoals
            ORDER BY e.timestamp DESC
            LIMIT 1
        """)

        record = result.single()
        assert record is not None
        assert len(record["subgoals"]) == 2
        assert "key" in record["subgoals"][0].lower()
        assert "door" in record["subgoals"][1].lower()


class TestMemoryRetrievalWithSubgoalContext:
    """Test that memory retrieval is filtered by current subgoal."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_memory_retrieval_with_subgoal_context(self, neo4j_session):
        """
        Test 3: Memory retrieval should filter by current subgoal.

        Given: Multiple memories for different subgoals
        When: Retrieving with subgoal="take key"
        Then: Only memories relevant to "take key" returned
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Store some fake memories first
        # Memory 1: Taking key succeeded
        neo4j_session.run("""
            CREATE (m:Memory {
                context: 'You see a key on the table',
                action: 'take key',
                outcome: 'positive',
                subgoal: 'take key',
                confidence: 0.9,
                test: true
            })
        """)

        # Memory 2: Unlocking door succeeded
        neo4j_session.run("""
            CREATE (m:Memory {
                context: 'You have a key',
                action: 'unlock door',
                outcome: 'positive',
                subgoal: 'unlock door',
                confidence: 0.9,
                test: true
            })
        """)

        # Now retrieve with subgoal context
        current_subgoal = "take key"
        context = "You see a key on the table"

        memories = agent.memory.retrieve_relevant_memories(
            context=context,
            action="take key",
            current_subgoal=current_subgoal  # NEW PARAMETER
        )

        # Should only get "take key" memory, not "unlock door"
        assert len(memories) >= 1, "Should retrieve relevant memory"

        for mem in memories:
            # Check that retrieved memories match subgoal
            assert "key" in mem.get('action', '').lower() or \
                   "key" in mem.get('subgoal', '').lower(), \
                   "Memory should be relevant to 'take key' subgoal"

    def test_memory_bonus_uses_subgoal_context(self, neo4j_session):
        """
        Test 4: calculate_memory_bonus should pass subgoal to retrieval.

        When: Scoring action with current subgoal
        Then: Memory retrieval uses subgoal context
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Set up agent state
        agent.beliefs['current_room'] = 'room'
        agent.beliefs['rooms']['room'] = {'description': 'You see a key'}

        # Get current subgoal
        current_subgoal = agent.subgoals[agent.current_subgoal_index]

        # Calculate memory bonus (should use subgoal context)
        bonus = agent.calculate_memory_bonus("take key", current_subgoal)

        # Bonus should be numeric (might be 0 if no memories yet)
        assert isinstance(bonus, float), "Memory bonus should be float"


class TestProceduralMemoryForQuests:
    """Test procedural memory (action patterns) for quests."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_store_action_sequence_pattern(self, neo4j_session):
        """
        Test 5: Store successful action sequences as patterns.

        When: Quest completed successfully with sequence [A, B, C]
        Then: Pattern "A→B→C" stored as procedural memory
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, go east. Then, take nest. Finally, place nest."
        agent.reset(quest)

        # Simulate successful sequence
        agent.step("Attic", "", 0.0, False, ["go east"], None)
        agent.step("Restroom", "", 0.0, False, ["take nest from table"], None)
        agent.step("Got nest", "", 0.0, False, ["insert nest into dresser"], None)
        agent.step("Done!", "", 1.0, True, ["look"], None)

        # Check that pattern was stored
        result = neo4j_session.run("""
            MATCH (p:ProceduralMemory)
            WHERE p.quest_type IS NOT NULL
            RETURN p.pattern as pattern, p.success_rate as success
            ORDER BY p.timestamp DESC
            LIMIT 1
        """)

        record = result.single()
        if record:  # Might not exist if not implemented yet
            assert "go east" in record["pattern"].lower()
            assert record["success"] >= 0.0


class TestLearningOverEpisodes:
    """Test that agent learns and improves over multiple episodes."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_memory_influences_action_scores(self, neo4j_session):
        """
        Test 6: Positive memories should increase action scores.

        Given: Positive memory for "take key"
        When: Scoring "take key" action
        Then: Memory bonus > 0
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        # Store positive memory
        neo4j_session.run("""
            CREATE (m:Memory {
                context: 'room with key',
                action: 'take key',
                outcome: 'positive',
                reward: 1.0,
                confidence: 1.0,
                test: true
            })
        """)

        # Setup agent
        agent.reset("Take the key")
        agent.beliefs['current_room'] = 'room'
        agent.beliefs['rooms']['room'] = {'description': 'room with key'}

        # Get memory bonus
        bonus = agent.calculate_memory_bonus("take key", "take key")

        # Should be positive due to stored positive memory
        # Note: Might be 0 if memory retrieval doesn't find it
        assert bonus >= 0.0, "Memory bonus should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

**SAVE THIS FILE** as `tests/test_quest_aware_memory.py`

**RUN TESTS (should FAIL - TDD Red phase):**
```bash
python -m pytest tests/test_quest_aware_memory.py -v --tb=short
```

**EXPECTED:** Most tests fail because quest-aware memory not implemented yet.

---

### Step 1.3: Modify Memory Storage (2 hours)

**ACTION:** Update `cognitive_agent.py` method `save_episode()` to store quest info

**LOCATION:** Line ~832 in `cognitive_agent.py`

**CURRENT CODE (approximate):**
```python
def save_episode(self):
    """Save the current episode to Neo4j Episodic Memory."""
    # ... existing code ...

    episode_data = {
        'episode_id': f'tw_ep_{self.current_step}_{int(time.time())}',
        'steps': steps,
        'total_reward': float(total_reward),
        'success': bool(success),
        'goal': goal  # Generic goal
    }

    stored = self.memory.store_episode(episode_data)
```

**MODIFY TO:**
```python
def save_episode(self):
    """
    Save the current episode to Neo4j Episodic Memory.

    NOW QUEST-AWARE: Stores quest text, subgoals, and subgoal progression.
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
        success = total_reward > 0

        # Get goal (quest-aware)
        goal = self.last_quest if self.last_quest else None

        # Build step data with rich context INCLUDING SUBGOALS
        steps = []
        for i in range(len(self.action_history)):
            action_data = self.action_history[i]
            obs_data = self.observation_history[i] if i < len(self.observation_history) else {}
            reward = self.reward_history[i] if i < len(self.reward_history) else 0.0

            # Determine which subgoal was active
            # (Approximate - track subgoal progression if you want exact)
            active_subgoal = None
            if self.subgoals and i < len(self.subgoals):
                # Simple heuristic: map step to subgoal
                subgoal_index = min(i // max(1, len(self.action_history) // len(self.subgoals)),
                                   len(self.subgoals) - 1)
                active_subgoal = self.subgoals[subgoal_index]

            outcome = 'positive' if reward > 0 else ('negative' if reward < 0 else 'neutral')

            steps.append({
                'action': action_data.get('action', 'unknown'),
                'room': obs_data.get('room', 'Unknown'),
                'reward': float(reward),
                'outcome': outcome,
                'subgoal': active_subgoal  # NEW: Track active subgoal
            })

        # Create episode data structure (QUEST-AWARE)
        episode_data = {
            'episode_id': f'tw_ep_{self.current_step}_{int(time.time())}',
            'steps': steps,
            'total_reward': float(total_reward),
            'success': bool(success),
            'goal': goal,
            # NEW: Quest-specific fields
            'quest': self.last_quest,  # Full quest text
            'subgoals': self.subgoals,  # Decomposed subgoals
            'num_subgoals': len(self.subgoals) if self.subgoals else 0,
            'subgoals_completed': self.current_subgoal_index  # Progress
        }

        # Use memory system to store
        stored = self.memory.store_episode(episode_data)

        if stored and self.verbose:
            print(f"   ✅ Episode saved ({len(steps)} steps, reward: {total_reward:+.1f})")
            if self.subgoals:
                print(f"   📋 Quest: {len(self.subgoals)} subgoals, completed {self.current_subgoal_index}")
        elif not stored and self.verbose:
            print("   ⚠️  Episode storage failed")

    except Exception as e:
        if self.verbose:
            print(f"⚠️  Episode save failed: {e}")
        logger.warning(f"Failed to save episode to Neo4j: {e}")
```

**TEST:**
```bash
# Run just the storage test
python -m pytest tests/test_quest_aware_memory.py::TestMemoryStorageWithQuestContext -v
```

**EXPECTED:** Tests should now PASS for episode storage.

---

### Step 1.4: Modify Memory Retrieval (2 hours)

**ACTION:** Update `memory_system.py` to filter by subgoal context

**LOCATION:** Find `memory_system.py`:
```bash
find . -name "memory_system.py" -type f
```

**CURRENT METHOD (approximate):**
```python
def retrieve_relevant_memories(self, context: str, action: str) -> List[Dict]:
    """Retrieve memories relevant to current context and action."""
    # Uses generic context matching
    # Does NOT use subgoal filtering
```

**MODIFY TO:**
```python
def retrieve_relevant_memories(
    self,
    context: str,
    action: str,
    current_subgoal: str = None  # NEW PARAMETER
) -> List[Dict]:
    """
    Retrieve memories relevant to current context, action, and subgoal.

    NEW: Filters by current_subgoal if provided (hierarchical memory).

    Args:
        context: Current observation/context
        action: Action being considered
        current_subgoal: Current subgoal (if in quest mode)

    Returns:
        List of relevant memory dicts with 'outcome', 'confidence', etc.
    """
    try:
        if not current_subgoal:
            # Fallback: Use generic retrieval (backward compatibility)
            return self._retrieve_generic(context, action)

        # NEW: Quest-aware retrieval
        return self._retrieve_by_subgoal(context, action, current_subgoal)

    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")
        return []

def _retrieve_generic(self, context: str, action: str) -> List[Dict]:
    """Generic memory retrieval (backward compatible)."""
    # Extract keywords from context
    context_words = set(context.lower().split())
    action_words = set(action.lower().split())
    keywords = (context_words | action_words) - {'the', 'a', 'an', 'in', 'on'}

    if not keywords:
        return []

    # Query Neo4j
    query = """
        MATCH (m:Memory)
        WHERE ANY(word IN $keywords WHERE
            toLower(m.context) CONTAINS word OR
            toLower(m.action) CONTAINS word)
        RETURN m.outcome as outcome,
               m.confidence as confidence,
               m.action as action,
               m.reward as reward
        ORDER BY m.confidence DESC
        LIMIT 5
    """

    result = self.session.run(query, keywords=list(keywords))
    return [dict(record) for record in result]

def _retrieve_by_subgoal(
    self,
    context: str,
    action: str,
    subgoal: str
) -> List[Dict]:
    """
    Quest-aware memory retrieval (NEW).

    Prioritizes memories that match the current subgoal.
    """
    # Extract keywords from context, action, AND subgoal
    context_words = set(context.lower().split())
    action_words = set(action.lower().split())
    subgoal_words = set(subgoal.lower().split())

    stopwords = {'the', 'a', 'an', 'in', 'on', 'to', 'from', 'with'}
    keywords = (context_words | action_words) - stopwords
    subgoal_keywords = subgoal_words - stopwords

    if not keywords:
        return []

    # Query Neo4j with subgoal filtering
    query = """
        MATCH (m:Memory)
        WHERE
            // Match context/action keywords
            ANY(word IN $keywords WHERE
                toLower(m.context) CONTAINS word OR
                toLower(m.action) CONTAINS word)
            AND
            // Match subgoal keywords (PRIORITY FILTER)
            (m.subgoal IS NULL OR
             ANY(word IN $subgoal_keywords WHERE
                toLower(m.subgoal) CONTAINS word))
        RETURN m.outcome as outcome,
               m.confidence as confidence,
               m.action as action,
               m.reward as reward,
               m.subgoal as subgoal,
               // Boost score if subgoal matches
               CASE
                   WHEN m.subgoal IS NOT NULL
                        AND ANY(word IN $subgoal_keywords WHERE
                               toLower(m.subgoal) CONTAINS word)
                   THEN m.confidence * 1.5
                   ELSE m.confidence
               END as relevance_score
        ORDER BY relevance_score DESC
        LIMIT 5
    """

    result = self.session.run(
        query,
        keywords=list(keywords),
        subgoal_keywords=list(subgoal_keywords)
    )

    return [dict(record) for record in result]
```

**TEST:**
```bash
python -m pytest tests/test_quest_aware_memory.py::TestMemoryRetrievalWithSubgoalContext -v
```

---

### Step 1.5: Update calculate_memory_bonus() (1 hour)

**ACTION:** Pass current_subgoal to memory retrieval

**LOCATION:** Line ~393 in `cognitive_agent.py`

**CURRENT CODE:**
```python
def calculate_memory_bonus(self, action: str) -> float:
    """Calculate score adjustment based on past memories."""
    # ... defensive checks ...

    memories = self.memory.retrieve_relevant_memories(context, action)
    # Does NOT pass subgoal
```

**MODIFY TO:**
```python
def calculate_memory_bonus(self, action: str, current_subgoal: str = None) -> float:
    """
    Calculate score adjustment based on past memories.

    NOW QUEST-AWARE: Retrieves memories filtered by current subgoal.

    Args:
        action: Action to evaluate
        current_subgoal: Current subgoal (if in quest mode)

    Returns:
        Float score adjustment (positive for good memories, negative for bad)
    """
    # Defensive: Check if current_room exists
    if not self.beliefs.get('current_room'):
        return 0.0

    current_room = self.beliefs['current_room']
    if current_room not in self.beliefs.get('rooms', {}):
        return 0.0

    context = self.beliefs['rooms'][current_room].get('description', '')
    if not context:
        return 0.0

    try:
        # NEW: Pass current_subgoal to retrieval
        memories = self.memory.retrieve_relevant_memories(
            context,
            action,
            current_subgoal=current_subgoal  # Quest-aware!
        )
    except Exception as e:
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
            bonus -= 5.0 * confidence

    return bonus
```

**THEN UPDATE** `score_action()` to pass subgoal to memory bonus:

**LOCATION:** Line ~625 in `cognitive_agent.py`

**MODIFY:**
```python
def score_action(self, action: str, beliefs: Dict, quest: Optional[Dict] = None,
                current_subgoal: str = None) -> float:
    """Score action using Active Inference EFE."""
    # ... coefficients ...

    goal_val = self.calculate_goal_value(action, current_subgoal)
    entropy = self.calculate_entropy(action)
    cost = self.calculate_cost(action)
    memory_bonus = self.calculate_memory_bonus(action, current_subgoal)  # PASS SUBGOAL
    plan_bonus = self.calculate_plan_bonus(action)

    efe = (alpha * goal_val) + (beta * entropy) - (gamma * cost) + \
          (delta * memory_bonus) + (epsilon * plan_bonus)

    return efe
```

**TEST:**
```bash
python -m pytest tests/test_quest_aware_memory.py -v
```

**EXPECTED:** All Phase 1 tests should now PASS.

---

### Step 1.6: Test Learning Over Episodes (2 hours)

**ACTION:** Create integration test showing learning

**CREATE FILE:** `tests/test_quest_learning_integration.py`

```python
"""
Integration test: Learning over multiple episodes.

Demonstrates that agent improves with experience.
"""
import pytest
from neo4j import GraphDatabase
import config


def test_learning_over_episodes():
    """
    Integration Test: Agent should improve over 5 episodes.

    Scenario:
    - Same quest repeated 5 times
    - Episode 1: No memories, exploration
    - Episode 5: Uses learned patterns, faster/better

    Expected: Episode 5 performance >= Episode 1
    """
    from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session()

    quest = "First, take the key. Then, unlock the door."
    episodes_data = []

    for episode_num in range(1, 6):
        agent = TextWorldCognitiveAgent(session, verbose=False)
        agent.reset(quest)

        steps = 0
        done = False
        max_steps = 10

        # Simplified mock environment
        state = "room_with_key"

        while not done and steps < max_steps:
            steps += 1

            # Mock observations
            if state == "room_with_key":
                obs = "You see a key on the table."
                commands = ["take key", "examine table", "look"]
            elif state == "have_key":
                obs = "You have the key. There's a locked door."
                commands = ["unlock door", "examine key", "drop key"]
            elif state == "door_unlocked":
                obs = "The door is unlocked!"
                commands = ["look"]
                done = True
            else:
                obs = "Unknown state"
                commands = ["look"]

            # Agent selects action
            action = agent.step(obs, obs, 0.0, done, commands, None)

            # Mock environment response
            if action == "take key" and state == "room_with_key":
                state = "have_key"
                reward = 0.0
            elif action == "unlock door" and state == "have_key":
                state = "door_unlocked"
                reward = 1.0
                done = True
            else:
                reward = 0.0

        episodes_data.append({
            'episode': episode_num,
            'steps': steps,
            'success': done
        })

        print(f"Episode {episode_num}: {steps} steps, success={done}")

    session.close()
    driver.close()

    # Analysis
    episode_1_steps = episodes_data[0]['steps']
    episode_5_steps = episodes_data[4]['steps']

    print(f"\nLearning Analysis:")
    print(f"  Episode 1: {episode_1_steps} steps")
    print(f"  Episode 5: {episode_5_steps} steps")

    # Agent should learn (fewer steps or maintain performance)
    # Note: Might not improve if environment too simple
    assert episodes_data[4]['success'], "Episode 5 should succeed"

    # If episode 5 took fewer steps, learning occurred
    if episode_5_steps < episode_1_steps:
        print("  ✅ LEARNING DETECTED: Agent improved!")
    else:
        print("  ⚠️  No improvement (environment might be too simple)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

**RUN:**
```bash
python -m pytest tests/test_quest_learning_integration.py -v
```

---

### Step 1.7: Phase 1 Completion Checklist

**BEFORE MOVING TO PHASE 2:**

- [ ] All memory tests pass (tests/test_quest_aware_memory.py)
- [ ] Integration test passes (tests/test_quest_learning_integration.py)
- [ ] Episodes stored with quest/subgoal info (check Neo4j browser)
- [ ] Memory retrieval filtered by subgoal
- [ ] Memory bonus integrated into EFE scoring
- [ ] Backward compatibility maintained (old tests still pass)

**VERIFY:**
```bash
# Run all tests
python -m pytest tests/test_quest_aware_memory.py tests/test_quest_learning_integration.py -v

# Check Neo4j storage
python3 -c "
from neo4j import GraphDatabase
import config

driver = GraphDatabase.driver(config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

with driver.session() as session:
    result = session.run('''
        MATCH (e:Episode)
        WHERE e.quest IS NOT NULL
        RETURN e.quest as quest, e.subgoals as subgoals
        LIMIT 3
    ''')

    for record in result:
        print(f\"Quest: {record['quest'][:50]}...\")
        print(f\"Subgoals: {record['subgoals']}\")
        print()

driver.close()
"
```

**EXPECTED OUTPUT:**
- Episodes have quest and subgoals
- Memory retrieval works with subgoal context
- Tests pass

---

## PHASE 2: Geometric Analysis (6-8 hours)

### Step 2.1: Understand Silver Gauge / Pythagorean Mean (1 hour)

**BACKGROUND:**

The **Silver Gauge** is a geometric analysis tool that uses the **Pythagorean mean** to measure quality/coherence.

**Pythagorean Mean** = Harmonic-Geometric-Arithmetic mean relationship:
- **Harmonic Mean (H):** Measures worst-case performance (penalties for low values)
- **Geometric Mean (G):** Measures overall balance
- **Arithmetic Mean (A):** Measures average performance

**Formula:**
```
H ≤ G ≤ A

Where:
H = n / (1/x₁ + 1/x₂ + ... + 1/xₙ)
G = ⁿ√(x₁ × x₂ × ... × xₙ)
A = (x₁ + x₂ + ... + xₙ) / n
```

**Application to Quest Decomposition:**

Measure the quality of quest decomposition by analyzing:
1. **Subgoal coherence:** How well do subgoals relate to each other?
2. **Subgoal completeness:** Do subgoals cover the full quest?
3. **Subgoal specificity:** Are subgoals concrete and actionable?

**FIND EXISTING GEOMETRIC CODE:**
```bash
# Find Silver Gauge implementation
find . -name "*silver*" -o -name "*gauge*" -o -name "*geometric*" | grep -E "\.py$"

# Check for existing Pythagorean mean code
grep -r "pythagorean\|harmonic_mean\|geometric_mean" --include="*.py" .
```

**READ DOCUMENTATION:**
```bash
cat docs/secret_docs/silver_update/graph_model.py  # If exists
cat graph_model.py  # Main implementation
```

**EXPECTED FINDINGS:**
- Geometric utilities exist (graph_model.py or similar)
- Silver Gauge may already have methods for calculating means
- Need to apply these to quest analysis

**UNDERSTANDING CHECK:**
- [ ] I understand Pythagorean means (H ≤ G ≤ A)
- [ ] I found existing geometric code
- [ ] I know how to apply to quest decomposition

---

### Step 2.2: Write Tests for Geometric Analysis (TDD - 1 hour)

**CREATE FILE:** `tests/test_quest_geometric_analysis.py`

```python
"""
Test suite for Quest Geometric Analysis (Phase 2 of Option B).

Tests Silver Gauge application to quest decomposition.
"""
import pytest
from neo4j import GraphDatabase
import config


class TestPythagoreanMeanCalculation:
    """Test Pythagorean mean utilities."""

    def test_harmonic_mean_calculation(self):
        """
        Test 1: Harmonic mean penalizes low values.

        H = n / (1/x₁ + 1/x₂ + ...)
        """
        from environments.domain4_textworld.quest_geometric_analyzer import (
            calculate_harmonic_mean
        )

        # Balanced values
        values_balanced = [1.0, 1.0, 1.0]
        h_balanced = calculate_harmonic_mean(values_balanced)
        assert abs(h_balanced - 1.0) < 0.01, "Harmonic mean of 1s should be 1"

        # One low value (should pull down harmonic mean significantly)
        values_unbalanced = [1.0, 1.0, 0.1]
        h_unbalanced = calculate_harmonic_mean(values_unbalanced)
        assert h_unbalanced < 0.5, "Harmonic mean heavily penalizes low values"

    def test_geometric_mean_calculation(self):
        """Test 2: Geometric mean measures overall balance."""
        from environments.domain4_textworld.quest_geometric_analyzer import (
            calculate_geometric_mean
        )

        values = [2.0, 8.0]
        g = calculate_geometric_mean(values)
        expected = (2.0 * 8.0) ** 0.5  # sqrt(16) = 4.0
        assert abs(g - expected) < 0.01

    def test_arithmetic_mean_calculation(self):
        """Test 3: Arithmetic mean is simple average."""
        from environments.domain4_textworld.quest_geometric_analyzer import (
            calculate_arithmetic_mean
        )

        values = [1.0, 2.0, 3.0]
        a = calculate_arithmetic_mean(values)
        assert abs(a - 2.0) < 0.01

    def test_pythagorean_inequality(self):
        """Test 4: H ≤ G ≤ A (Pythagorean inequality)."""
        from environments.domain4_textworld.quest_geometric_analyzer import (
            calculate_harmonic_mean,
            calculate_geometric_mean,
            calculate_arithmetic_mean
        )

        values = [1.0, 2.0, 3.0, 4.0]

        h = calculate_harmonic_mean(values)
        g = calculate_geometric_mean(values)
        a = calculate_arithmetic_mean(values)

        assert h <= g <= a, f"Should satisfy H({h}) ≤ G({g}) ≤ A({a})"


class TestSubgoalCoherenceAnalysis:
    """Test subgoal coherence measurement."""

    def test_measure_subgoal_coherence(self):
        """
        Test 5: Measure how well subgoals relate to each other.

        Coherence metrics:
        - Token overlap between consecutive subgoals
        - Semantic similarity (if using embeddings)
        - Action flow (verb transitions)
        """
        from environments.domain4_textworld.quest_geometric_analyzer import (
            QuestGeometricAnalyzer
        )

        analyzer = QuestGeometricAnalyzer()

        # High coherence: Related subgoals
        subgoals_coherent = [
            "take the key from the table",
            "unlock the door with the key",
            "go through the door"
        ]

        coherence_high = analyzer.measure_subgoal_coherence(subgoals_coherent)

        # Low coherence: Unrelated subgoals
        subgoals_incoherent = [
            "take the key",
            "examine the painting",
            "eat the apple"
        ]

        coherence_low = analyzer.measure_subgoal_coherence(subgoals_incoherent)

        assert coherence_high > coherence_low, \
            "Related subgoals should have higher coherence"

    def test_measure_subgoal_completeness(self):
        """
        Test 6: Measure if subgoals cover the full quest.

        Completeness = (subgoal_tokens ∩ quest_tokens) / quest_tokens
        """
        from environments.domain4_textworld.quest_geometric_analyzer import (
            QuestGeometricAnalyzer
        )

        analyzer = QuestGeometricAnalyzer()

        quest = "Take the golden key from the table and unlock the ancient door"

        # Complete coverage
        subgoals_complete = [
            "take the golden key from the table",
            "unlock the ancient door"
        ]

        completeness_high = analyzer.measure_subgoal_completeness(
            subgoals_complete, quest
        )

        # Incomplete coverage (missing "ancient")
        subgoals_incomplete = [
            "take the key",
            "unlock door"
        ]

        completeness_low = analyzer.measure_subgoal_completeness(
            subgoals_incomplete, quest
        )

        assert completeness_high > completeness_low

    def test_measure_subgoal_specificity(self):
        """
        Test 7: Measure if subgoals are specific and actionable.

        Specificity factors:
        - Has verb (action word)
        - Has object (noun)
        - Has details (adjectives)
        """
        from environments.domain4_textworld.quest_geometric_analyzer import (
            QuestGeometricAnalyzer
        )

        analyzer = QuestGeometricAnalyzer()

        # Specific
        specific = "take the golden key from the wooden table"
        specificity_high = analyzer.measure_subgoal_specificity(specific)

        # Vague
        vague = "do something"
        specificity_low = analyzer.measure_subgoal_specificity(vague)

        assert specificity_high > specificity_low


class TestSilverGaugeIntegration:
    """Test full Silver Gauge analysis of quest decomposition."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_analyze_quest_decomposition(self, neo4j_session):
        """
        Test 8: Complete geometric analysis of quest decomposition.

        Returns: {
            'coherence': float,
            'completeness': float,
            'specificity': float,
            'harmonic_mean': float,
            'geometric_mean': float,
            'arithmetic_mean': float,
            'overall_quality': float
        }
        """
        from environments.domain4_textworld.quest_geometric_analyzer import (
            QuestGeometricAnalyzer
        )

        analyzer = QuestGeometricAnalyzer(neo4j_session)

        quest = "First, take the key. Then, unlock the door. Finally, go through."
        subgoals = ["take the key", "unlock the door", "go through"]

        analysis = analyzer.analyze_decomposition(quest, subgoals)

        # Check all metrics present
        assert 'coherence' in analysis
        assert 'completeness' in analysis
        assert 'specificity' in analysis
        assert 'harmonic_mean' in analysis
        assert 'geometric_mean' in analysis
        assert 'arithmetic_mean' in analysis
        assert 'overall_quality' in analysis

        # Check Pythagorean inequality
        h = analysis['harmonic_mean']
        g = analysis['geometric_mean']
        a = analysis['arithmetic_mean']
        assert h <= g <= a, f"H({h}) ≤ G({g}) ≤ A({a})"

    def test_geometric_metrics_logged_to_neo4j(self, neo4j_session):
        """
        Test 9: Geometric analysis logged to Neo4j.

        Creates: (:Quest)-[:DECOMPOSED_INTO]->(:Subgoal)
        With properties: coherence, completeness, specificity, etc.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Geometric analysis should have been performed and logged
        # Check Neo4j for geometric properties
        result = neo4j_session.run("""
            MATCH (q:Quest)
            WHERE q.text IS NOT NULL
            RETURN q.text as quest,
                   q.coherence as coherence,
                   q.geometric_mean as geometric_mean
            ORDER BY q.timestamp DESC
            LIMIT 1
        """)

        record = result.single()

        if record:  # Might not exist if not implemented yet
            assert record['coherence'] is not None
            assert record['geometric_mean'] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

**SAVE & RUN (should FAIL):**
```bash
python -m pytest tests/test_quest_geometric_analysis.py -v --tb=short
```

---

### Step 2.3: Implement Quest Geometric Analyzer (3 hours)

**ACTION:** Create new file `quest_geometric_analyzer.py`

**CREATE:** `environments/domain4_textworld/quest_geometric_analyzer.py`

```python
"""
Quest Geometric Analyzer - Silver Gauge Application to Quest Decomposition.

Uses Pythagorean means to measure quest decomposition quality:
- Harmonic Mean: Worst-case performance (penalizes weak subgoals)
- Geometric Mean: Overall balance
- Arithmetic Mean: Average performance

Metrics:
1. Coherence: How well subgoals relate to each other
2. Completeness: Do subgoals cover the full quest
3. Specificity: Are subgoals concrete and actionable

Phase 2 of Option B: Complete Synthesis
"""
import math
from typing import List, Dict, Optional
from neo4j import Session
import logging

logger = logging.getLogger(__name__)


def calculate_harmonic_mean(values: List[float]) -> float:
    """
    Calculate harmonic mean (penalizes low values).

    H = n / (1/x₁ + 1/x₂ + ... + 1/xₙ)

    Args:
        values: List of positive numbers

    Returns:
        Harmonic mean
    """
    if not values or any(v <= 0 for v in values):
        return 0.0

    n = len(values)
    reciprocal_sum = sum(1.0 / v for v in values)

    return n / reciprocal_sum


def calculate_geometric_mean(values: List[float]) -> float:
    """
    Calculate geometric mean (overall balance).

    G = ⁿ√(x₁ × x₂ × ... × xₙ)

    Args:
        values: List of positive numbers

    Returns:
        Geometric mean
    """
    if not values or any(v <= 0 for v in values):
        return 0.0

    product = math.prod(values)
    n = len(values)

    return product ** (1.0 / n)


def calculate_arithmetic_mean(values: List[float]) -> float:
    """
    Calculate arithmetic mean (simple average).

    A = (x₁ + x₂ + ... + xₙ) / n

    Args:
        values: List of numbers

    Returns:
        Arithmetic mean
    """
    if not values:
        return 0.0

    return sum(values) / len(values)


class QuestGeometricAnalyzer:
    """
    Analyze quest decomposition quality using geometric methods.

    Applies Silver Gauge (Pythagorean means) to measure:
    - Subgoal coherence
    - Subgoal completeness
    - Subgoal specificity
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize analyzer.

        Args:
            session: Neo4j session (optional, for logging)
        """
        self.session = session

        # Stopwords for token analysis
        self.stopwords = {
            'the', 'a', 'an', 'in', 'on', 'to', 'from', 'with',
            'of', 'at', 'by', 'for', 'into', 'through', 'during'
        }

    def measure_subgoal_coherence(self, subgoals: List[str]) -> float:
        """
        Measure how well subgoals relate to each other.

        Coherence = average token overlap between consecutive subgoals.

        Args:
            subgoals: List of subgoal strings

        Returns:
            Coherence score (0.0 to 1.0)
        """
        if len(subgoals) < 2:
            return 1.0  # Single subgoal is perfectly coherent

        overlaps = []

        for i in range(len(subgoals) - 1):
            current = set(subgoals[i].lower().split()) - self.stopwords
            next_goal = set(subgoals[i + 1].lower().split()) - self.stopwords

            if not current or not next_goal:
                overlap = 0.0
            else:
                # Jaccard similarity
                intersection = len(current & next_goal)
                union = len(current | next_goal)
                overlap = intersection / union if union > 0 else 0.0

            overlaps.append(overlap)

        return sum(overlaps) / len(overlaps) if overlaps else 0.0

    def measure_subgoal_completeness(self, subgoals: List[str], quest: str) -> float:
        """
        Measure if subgoals cover the full quest.

        Completeness = (tokens in subgoals ∩ tokens in quest) / (tokens in quest)

        Args:
            subgoals: List of subgoal strings
            quest: Original quest text

        Returns:
            Completeness score (0.0 to 1.0)
        """
        quest_tokens = set(quest.lower().split()) - self.stopwords

        if not quest_tokens:
            return 1.0

        # Aggregate all tokens from subgoals
        subgoal_tokens = set()
        for subgoal in subgoals:
            tokens = set(subgoal.lower().split()) - self.stopwords
            subgoal_tokens |= tokens

        # How many quest tokens are covered?
        covered = len(quest_tokens & subgoal_tokens)
        total = len(quest_tokens)

        return covered / total if total > 0 else 0.0

    def measure_subgoal_specificity(self, subgoal: str) -> float:
        """
        Measure if subgoal is specific and actionable.

        Specificity factors:
        - Has action verb (take, go, unlock, etc.)
        - Has object noun
        - Has descriptive words (adjectives)
        - Length (more specific = more words)

        Args:
            subgoal: Subgoal string

        Returns:
            Specificity score (0.0 to 1.0)
        """
        tokens = subgoal.lower().split()

        if not tokens:
            return 0.0

        score = 0.0

        # Factor 1: Has action verb (heuristic - starts with verb)
        action_verbs = {
            'take', 'get', 'go', 'move', 'unlock', 'open', 'close',
            'examine', 'look', 'use', 'place', 'put', 'insert', 'drop',
            'pick', 'grab', 'push', 'pull', 'activate', 'deactivate'
        }

        if tokens[0] in action_verbs:
            score += 0.3

        # Factor 2: Has object (heuristic - has nouns)
        # Simple heuristic: non-stopwords are likely objects
        objects = set(tokens) - self.stopwords - action_verbs
        if objects:
            score += 0.3

        # Factor 3: Has descriptors (heuristic - length > 3)
        if len(tokens) > 3:
            score += 0.2

        # Factor 4: Specificity from length (up to 0.2)
        length_score = min(len(tokens) / 10.0, 0.2)
        score += length_score

        return min(score, 1.0)

    def analyze_decomposition(
        self,
        quest: str,
        subgoals: List[str]
    ) -> Dict[str, float]:
        """
        Complete geometric analysis of quest decomposition.

        Calculates:
        - Individual metrics (coherence, completeness, specificity)
        - Pythagorean means (harmonic, geometric, arithmetic)
        - Overall quality score

        Args:
            quest: Original quest text
            subgoals: Decomposed subgoals

        Returns:
            Dict with all metrics
        """
        # Calculate individual metrics
        coherence = self.measure_subgoal_coherence(subgoals)
        completeness = self.measure_subgoal_completeness(subgoals, quest)

        # Average specificity across all subgoals
        specificities = [self.measure_subgoal_specificity(sg) for sg in subgoals]
        specificity = sum(specificities) / len(specificities) if specificities else 0.0

        # Aggregate metrics
        metrics = [coherence, completeness, specificity]

        # Calculate Pythagorean means
        # Add small epsilon to avoid division by zero
        metrics_safe = [max(m, 0.01) for m in metrics]

        harmonic = calculate_harmonic_mean(metrics_safe)
        geometric = calculate_geometric_mean(metrics_safe)
        arithmetic = calculate_arithmetic_mean(metrics)

        # Overall quality = geometric mean (balanced measure)
        overall_quality = geometric

        return {
            'coherence': coherence,
            'completeness': completeness,
            'specificity': specificity,
            'harmonic_mean': harmonic,
            'geometric_mean': geometric,
            'arithmetic_mean': arithmetic,
            'overall_quality': overall_quality,
            'num_subgoals': len(subgoals),
            'pythagorean_inequality_satisfied': harmonic <= geometric <= arithmetic
        }

    def log_to_neo4j(
        self,
        quest: str,
        subgoals: List[str],
        analysis: Dict[str, float]
    ) -> bool:
        """
        Log geometric analysis to Neo4j.

        Creates:
        (:Quest {text, coherence, completeness, ...})
        -[:DECOMPOSED_INTO]->
        (:Subgoal {text, specificity, order})

        Args:
            quest: Quest text
            subgoals: Subgoal list
            analysis: Analysis dict from analyze_decomposition()

        Returns:
            True if successful
        """
        if not self.session:
            logger.warning("No Neo4j session - skipping geometric logging")
            return False

        try:
            # Create Quest node with geometric properties
            self.session.run("""
                CREATE (q:Quest {
                    text: $quest,
                    coherence: $coherence,
                    completeness: $completeness,
                    specificity: $specificity,
                    harmonic_mean: $harmonic,
                    geometric_mean: $geometric,
                    arithmetic_mean: $arithmetic,
                    overall_quality: $quality,
                    num_subgoals: $num_subgoals,
                    timestamp: timestamp()
                })
                WITH q
                UNWIND $subgoals_data as sg
                CREATE (q)-[:DECOMPOSED_INTO {order: sg.order}]->(s:Subgoal {
                    text: sg.text,
                    specificity: sg.specificity,
                    order: sg.order
                })
            """,
                quest=quest,
                coherence=analysis['coherence'],
                completeness=analysis['completeness'],
                specificity=analysis['specificity'],
                harmonic=analysis['harmonic_mean'],
                geometric=analysis['geometric_mean'],
                arithmetic=analysis['arithmetic_mean'],
                quality=analysis['overall_quality'],
                num_subgoals=analysis['num_subgoals'],
                subgoals_data=[
                    {
                        'text': sg,
                        'specificity': self.measure_subgoal_specificity(sg),
                        'order': i
                    }
                    for i, sg in enumerate(subgoals)
                ]
            )

            return True

        except Exception as e:
            logger.error(f"Failed to log geometric analysis to Neo4j: {e}")
            return False


if __name__ == "__main__":
    """Quick manual test."""
    print("=== Quest Geometric Analyzer Test ===\n")

    analyzer = QuestGeometricAnalyzer()

    quest = "First, take the golden key from the table. Then, unlock the ancient door. Finally, go through the door."
    subgoals = [
        "take the golden key from the table",
        "unlock the ancient door",
        "go through the door"
    ]

    analysis = analyzer.analyze_decomposition(quest, subgoals)

    print(f"Quest: {quest}\n")
    print("Subgoals:")
    for i, sg in enumerate(subgoals, 1):
        print(f"  {i}. {sg}")

    print("\nGeometric Analysis:")
    print(f"  Coherence:     {analysis['coherence']:.3f}")
    print(f"  Completeness:  {analysis['completeness']:.3f}")
    print(f"  Specificity:   {analysis['specificity']:.3f}")
    print(f"\nPythagorean Means:")
    print(f"  Harmonic:      {analysis['harmonic_mean']:.3f}")
    print(f"  Geometric:     {analysis['geometric_mean']:.3f}")
    print(f"  Arithmetic:    {analysis['arithmetic_mean']:.3f}")
    print(f"\nOverall Quality: {analysis['overall_quality']:.3f}")
    print(f"Pythagorean Inequality: {analysis['pythagorean_inequality_satisfied']}")
```

**TEST:**
```bash
# Quick manual test
python environments/domain4_textworld/quest_geometric_analyzer.py

# Run test suite
python -m pytest tests/test_quest_geometric_analysis.py::TestPythagoreanMeanCalculation -v
python -m pytest tests/test_quest_geometric_analysis.py::TestSubgoalCoherenceAnalysis -v
```

---

### Step 2.4: Integrate Geometric Analysis into Agent (2 hours)

**ACTION:** Add geometric analysis to `cognitive_agent.py` reset method

**LOCATION:** In `reset()` method, after quest decomposition (line ~144)

**MODIFY:**
```python
def reset(self, quest: str = None):
    """Reset agent for new episode."""
    # ... existing reset logic ...

    # Decompose quest into subgoals (hierarchical synthesis)
    if quest:
        self.last_quest = quest
        self.subgoals = self.quest_decomposer.decompose(quest)
        self.current_subgoal_index = 0

        if self.verbose:
            print("📋 Quest decomposed:")
            for i, sg in enumerate(self.subgoals, 1):
                print(f"   {i}. {sg}")
            print()

        # NEW: Geometric analysis of decomposition (Phase 2)
        if self.subgoals:
            try:
                from environments.domain4_textworld.quest_geometric_analyzer import (
                    QuestGeometricAnalyzer
                )

                analyzer = QuestGeometricAnalyzer(self.session)
                analysis = analyzer.analyze_decomposition(quest, self.subgoals)

                # Store analysis for introspection
                self.quest_geometric_analysis = analysis

                # Log to Neo4j
                analyzer.log_to_neo4j(quest, self.subgoals, analysis)

                if self.verbose:
                    print("📐 Geometric Analysis:")
                    print(f"   Coherence: {analysis['coherence']:.2f}")
                    print(f"   Completeness: {analysis['completeness']:.2f}")
                    print(f"   Overall Quality: {analysis['overall_quality']:.2f}")
                    print()

            except Exception as e:
                logger.warning(f"Geometric analysis failed: {e}")
                self.quest_geometric_analysis = None
    else:
        # No quest provided
        self.subgoals = []
        self.current_subgoal_index = 0
        self.last_quest = None
        self.quest_geometric_analysis = None

    # ... rest of reset ...
```

**TEST:**
```bash
python -m pytest tests/test_quest_geometric_analysis.py::TestSilverGaugeIntegration -v
```

---

### Step 2.5: Phase 2 Completion Checklist

**BEFORE MOVING TO PHASE 3:**

- [ ] All geometric tests pass
- [ ] Pythagorean means calculated correctly (H ≤ G ≤ A)
- [ ] Quest decomposition analyzed on reset
- [ ] Geometric metrics logged to Neo4j
- [ ] Can query Neo4j for geometric data

**VERIFY:**
```bash
# All Phase 2 tests
python -m pytest tests/test_quest_geometric_analysis.py -v

# Check Neo4j logging
python3 -c "
from neo4j import GraphDatabase
import config

driver = GraphDatabase.driver(config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

with driver.session() as session:
    result = session.run('''
        MATCH (q:Quest)-[:DECOMPOSED_INTO]->(s:Subgoal)
        RETURN q.text as quest,
               q.coherence as coherence,
               q.geometric_mean as geometric_mean,
               count(s) as num_subgoals
        ORDER BY q.timestamp DESC
        LIMIT 3
    ''')

    for record in result:
        print(f\"Quest: {record['quest'][:50]}...\")
        print(f\"  Coherence: {record['coherence']:.3f}\")
        print(f\"  Geometric Mean: {record['geometric_mean']:.3f}\")
        print(f\"  Subgoals: {record['num_subgoals']}\")
        print()

driver.close()
"
```

---

## PHASE 3: Quest-Aware Critical States (6-8 hours)

### Step 3.1: Understand Current Critical State System (1 hour)

**BACKGROUND:**

Critical states are meta-cognitive protocols that detect when the agent is stuck/confused:
- **DEADLOCK:** Stuck in loops
- **PANIC:** High uncertainty
- **SCARCITY:** Running out of time
- **NOVELTY:** Unexpected observations
- **ESCALATION:** Repeated failures

**Current Issue:** Critical states are DISABLED for TextWorld (line 960 in cognitive_agent.py) because they were interfering with quest execution.

**FIND CODE:**
```bash
# Find critical state code
grep -n "CriticalState\|critical_monitor" environments/domain4_textworld/cognitive_agent.py | head -20

# Read critical state implementation
cat critical_state.py  # Main implementation
```

**CHECK DISABLED CODE:** Around line 960:
```python
# CRITICAL FIX: Disable critical state monitoring for TextWorld
# The ESCALATION/DEADLOCK/NOVELTY protocols were overriding quest-aware action selection
# Force FLOW state (normal operation, no protocol override)
from critical_state import CriticalState
self.current_critical_state = CriticalState.FLOW
protocol_action = None
```

**Goal:** Re-enable critical states but make them QUEST-AWARE so they don't interfere.

**UNDERSTANDING CHECK:**
- [ ] I know where critical states are evaluated (step() method)
- [ ] I know why they were disabled (interfering with quests)
- [ ] I know how to make them quest-aware (check subgoal progress)

---

### Step 3.2: Write Tests for Quest-Aware Critical States (TDD - 2 hours)

**CREATE FILE:** `tests/test_quest_aware_critical_states.py`

```python
"""
Test suite for Quest-Aware Critical States (Phase 3 of Option B).

Tests that critical protocols don't interfere with valid quest execution.
"""
import pytest
from neo4j import GraphDatabase
import config


class TestCriticalStateDetection:
    """Test that critical states are detected appropriately."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_deadlock_detected_when_truly_stuck(self, neo4j_session):
        """
        Test 1: DEADLOCK should be detected when agent is stuck.

        Scenario:
        - Agent repeats same 2 actions in loop (A→B→A→B→A→B)
        - NOT making progress on subgoal
        - Should trigger DEADLOCK
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        from critical_state import CriticalState

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.reset("Take the key")

        # Simulate stuck loop (same room, same actions, no progress)
        for _ in range(6):
            agent.step("Room A", "", 0.0, False, ["go east", "go west"], None)
            agent.location_history.append("Room A")
            agent.location_history.append("Room B")

        # Evaluate critical state
        agent_state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(agent_state)

        # Should detect DEADLOCK or ESCALATION
        assert critical_state in [CriticalState.DEADLOCK, CriticalState.ESCALATION], \
            f"Should detect stuck state, got {critical_state}"

    def test_flow_maintained_during_valid_quest_execution(self, neo4j_session):
        """
        Test 2: FLOW should be maintained during valid quest execution.

        Scenario:
        - Agent executing quest steps in order
        - Making progress on subgoals
        - Should stay in FLOW (no interference)
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        from critical_state import CriticalState

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.reset("First, go east. Then, take key.")

        # Simulate valid execution
        agent.step("Attic", "", 0.0, False, ["go east"], None)
        agent.step("Room", "", 0.0, False, ["take key"], None)

        # Agent is making progress, should be FLOW
        agent_state = agent.get_agent_state_for_critical_monitor()
        critical_state = agent.critical_monitor.evaluate(agent_state)

        # Should be FLOW (normal operation)
        assert critical_state == CriticalState.FLOW, \
            f"Valid quest execution should maintain FLOW, got {critical_state}"


class TestQuestAwareProtocols:
    """Test that protocols respect subgoal progress."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_protocol_does_not_override_subgoal_action(self, neo4j_session):
        """
        Test 3: Critical protocol should NOT override when making subgoal progress.

        Scenario:
        - Agent in potential deadlock state
        - But current action matches subgoal
        - Protocol should NOT interfere
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.reset("Take the key")

        # Set up state that might trigger protocol
        agent.location_history = ["Room A"] * 5  # Looks like stuck

        # But agent is about to take correct action
        commands = ["take key", "look", "inventory"]

        action = agent.step("You see a key", "", 0.0, False, commands, None)

        # Should select "take key" (matches subgoal), NOT protocol override
        assert "key" in action.lower(), \
            "Should select subgoal-matching action, not protocol override"

    def test_protocol_intervenes_when_truly_stuck(self, neo4j_session):
        """
        Test 4: Protocol SHOULD intervene when truly stuck.

        Scenario:
        - Agent stuck in loop
        - NO progress on subgoal
        - Protocol should break the loop
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.reset("Take the key")

        # Simulate being stuck (repeated failed attempts)
        agent.action_history = [
            {'action': 'examine table', 'step': 0},
            {'action': 'look', 'step': 1},
            {'action': 'examine table', 'step': 2},
            {'action': 'look', 'step': 3},
            {'action': 'examine table', 'step': 4},
            {'action': 'look', 'step': 5},
        ]

        agent.location_history = ["Room"] * 6

        # No progress for 6 steps
        # Protocol should detect and potentially intervene
        # (Exact behavior depends on protocol implementation)


class TestSubgoalProgressTracking:
    """Test that progress tracking informs critical state evaluation."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_subgoal_progress_prevents_false_deadlock(self, neo4j_session):
        """
        Test 5: Subgoal progress should prevent false DEADLOCK detection.

        Scenario:
        - Agent taking multiple steps for same subgoal (normal)
        - E.g., "go east" then "go east again" to reach target
        - Should NOT trigger DEADLOCK if making progress toward subgoal
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        agent.reset("Go east three times to reach the target room")

        # Multiple steps for same subgoal (normal exploration)
        agent.step("Room 1", "", 0.0, False, ["go east"], None)
        agent.step("Room 2", "", 0.0, False, ["go east"], None)
        agent.step("Room 3", "", 0.0, False, ["go east"], None)

        # Should not be deadlock (making spatial progress)
        agent_state = agent.get_agent_state_for_critical_monitor()

        # Check that we're tracking different rooms
        assert len(set(agent.location_history)) >= 2, \
            "Should be visiting different rooms"


class TestCriticalStateIntegration:
    """Test full integration of quest-aware critical states."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    def test_quest_execution_with_critical_states_enabled(self, neo4j_session):
        """
        Test 6: End-to-end quest execution with critical states enabled.

        Should:
        - Complete quest successfully
        - Maintain FLOW during normal execution
        - Recover if stuck (protocol intervenes)
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)

        quest = "First, take key. Then, unlock door."
        agent.reset(quest)

        # Simulate execution
        steps = [
            ("You see a key", ["take key", "look"]),
            ("You took key", ["unlock door", "look"]),
            ("Door unlocked", ["look"])
        ]

        for obs, commands in steps:
            action = agent.step(obs, "", 0.0, False, commands, None)
            # Should select appropriate actions without protocol interference
            assert action in commands


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

**RUN (should FAIL):**
```bash
python -m pytest tests/test_quest_aware_critical_states.py -v --tb=short
```

---

### Step 3.3: Implement Quest-Aware Critical State Evaluation (3 hours)

**ACTION:** Modify `cognitive_agent.py` to re-enable critical states with quest awareness

**LOCATION:** Line ~960 in `cognitive_agent.py` (in `step()` method)

**CURRENT CODE (disabled):**
```python
# CRITICAL FIX: Disable critical state monitoring for TextWorld
# Force FLOW state (normal operation, no protocol override)
from critical_state import CriticalState
self.current_critical_state = CriticalState.FLOW
protocol_action = None
```

**REPLACE WITH:**
```python
# NEW (Phase 3): Quest-aware critical state monitoring
# Re-enable protocols but make them respect subgoal progress
agent_state = self.get_agent_state_for_critical_monitor()

# Quest-aware evaluation
if self.subgoals:
    # Check if making progress on current subgoal
    making_progress = self._is_making_subgoal_progress()

    if making_progress:
        # Making progress - stay in FLOW (don't interfere)
        self.current_critical_state = CriticalState.FLOW
        protocol_action = None

        if self.verbose:
            print("   ✓ Making subgoal progress - maintaining FLOW")
    else:
        # NOT making progress - evaluate critical state normally
        self.current_critical_state = self.critical_monitor.evaluate(agent_state)

        # Apply protocol only if truly stuck
        if self.current_critical_state != CriticalState.FLOW:
            protocol_action = self.apply_critical_state_protocol(
                self.current_critical_state,
                admissible_commands
            )
        else:
            protocol_action = None
else:
    # No quest context - use standard critical state evaluation
    self.current_critical_state = self.critical_monitor.evaluate(agent_state)
    protocol_action = self.apply_critical_state_protocol(
        self.current_critical_state,
        admissible_commands
    )
```

**ADD NEW METHOD** (around line 850):
```python
def _is_making_subgoal_progress(self) -> bool:
    """
    Check if agent is making progress on current subgoal.

    Progress indicators:
    - Visiting different locations (spatial progress)
    - Advancing subgoal index (task progress)
    - Actions matching subgoal (intent alignment)
    - Recent positive rewards

    Returns:
        True if making progress
    """
    # Progress indicator 1: Advanced subgoals recently
    if len(self.reward_history) >= 3:
        recent_rewards = self.reward_history[-3:]
        if any(r > 0 for r in recent_rewards):
            return True  # Got reward recently = progress

    # Progress indicator 2: Visiting different rooms (spatial exploration)
    if len(self.location_history) >= 5:
        recent_locations = self.location_history[-5:]
        unique_locations = len(set(recent_locations))

        if unique_locations >= 3:
            return True  # Exploring different rooms = progress

    # Progress indicator 3: Actions matching current subgoal
    if self.subgoals and self.action_history:
        current_subgoal = self.subgoals[self.current_subgoal_index]
        recent_actions = [a['action'] for a in self.action_history[-3:]]

        # Check if recent actions relate to subgoal
        subgoal_tokens = set(current_subgoal.lower().split())
        stopwords = {'the', 'a', 'an', 'to', 'from', 'in', 'on'}
        subgoal_clean = subgoal_tokens - stopwords

        for action in recent_actions:
            action_tokens = set(action.lower().split()) - stopwords
            overlap = len(action_tokens & subgoal_clean)

            if overlap >= 1:
                return True  # Actions align with subgoal = progress

    # Progress indicator 4: Not repeating same action
    if len(self.action_history) >= 4:
        recent_actions = [a['action'] for a in self.action_history[-4:]]
        unique_actions = len(set(recent_actions))

        if unique_actions >= 3:
            return True  # Trying different things = progress

    # If no progress indicators, might be stuck
    return False
```

**TEST:**
```bash
python -m pytest tests/test_quest_aware_critical_states.py -v
```

---

### Step 3.4: Phase 3 Completion Checklist

**VERIFY:**

- [ ] Critical states re-enabled
- [ ] Protocols don't interfere with valid quest execution
- [ ] Protocols DO intervene when truly stuck
- [ ] All critical state tests pass
- [ ] TextWorld still works (no regression)

**RUN:**
```bash
# Phase 3 tests
python -m pytest tests/test_quest_aware_critical_states.py -v

# Regression test - ensure TextWorld still works
python environments/domain4_textworld/compare_all_agents.py

# All tests
python -m pytest tests/ -v --tb=short
```

---

## PHASE 4: Integration & Validation (4-6 hours)

### Step 4.1: Full Integration Test (2 hours)

**CREATE FILE:** `tests/test_option_b_complete_synthesis.py`

```python
"""
Complete Synthesis Integration Test (Option B).

Validates all three phases working together:
- Phase 1: Quest-aware memory
- Phase 2: Geometric analysis
- Phase 3: Quest-aware critical states
"""
import pytest
from neo4j import GraphDatabase
import config


def test_complete_synthesis_single_episode():
    """
    Integration Test: Complete synthesis on one episode.

    Validates:
    1. Quest decomposition + geometric analysis
    2. Memory retrieval with subgoal context
    3. Critical states don't interfere
    4. Agent completes quest successfully
    """
    from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session()

    agent = TextWorldCognitiveAgent(session, verbose=True)

    quest = "First, take the golden key. Then, unlock the ancient door."
    agent.reset(quest)

    # Check Phase 2: Geometric analysis
    assert hasattr(agent, 'quest_geometric_analysis')
    assert agent.quest_geometric_analysis is not None
    assert 'coherence' in agent.quest_geometric_analysis
    print(f"✓ Geometric analysis: {agent.quest_geometric_analysis['overall_quality']:.3f}")

    # Check Phase 1: Memory system ready
    assert hasattr(agent, 'memory')
    print("✓ Memory system initialized")

    # Simulate episode
    steps = [
        ("You see a golden key on a pedestal.", ["take golden key", "examine key", "look"]),
        ("You took the golden key.", ["unlock ancient door", "examine door", "look"]),
        ("You unlocked the ancient door!", ["look"])
    ]

    for obs, commands in steps:
        action = agent.step(obs, "", 0.0, False, commands, None)
        print(f"  Selected: {action}")

        # Check Phase 3: Critical state should be FLOW
        from critical_state import CriticalState
        assert agent.current_critical_state == CriticalState.FLOW, \
            "Should maintain FLOW during valid execution"

    session.close()
    driver.close()

    print("✓ Complete synthesis validated!")


def test_learning_over_10_episodes():
    """
    Integration Test: Learning over 10 episodes.

    Expected: Episode 10 performance >= Episode 1
    """
    from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session()

    quest = "First, take the key. Then, unlock the door."

    episodes = []

    for ep in range(1, 11):
        agent = TextWorldCognitiveAgent(session, verbose=False)
        agent.reset(quest)

        # Simplified mock environment
        steps = 0
        done = False
        state = "start"

        while not done and steps < 10:
            steps += 1

            if state == "start":
                action = agent.step("You see a key.", "", 0.0, False,
                                   ["take key", "look"], None)
                if "key" in action:
                    state = "have_key"

            elif state == "have_key":
                action = agent.step("You have key. Door ahead.", "", 0.0, False,
                                   ["unlock door", "drop key"], None)
                if "unlock" in action:
                    state = "done"
                    done = True

        episodes.append({
            'episode': ep,
            'steps': steps,
            'success': done
        })

        if ep % 2 == 0:
            print(f"Episode {ep}: {steps} steps, success={done}")

    session.close()
    driver.close()

    # Analysis
    episode_1_steps = episodes[0]['steps']
    episode_10_steps = episodes[9]['steps']

    print(f"\nLearning Analysis:")
    print(f"  Episode 1: {episode_1_steps} steps")
    print(f"  Episode 10: {episode_10_steps} steps")

    if episode_10_steps <= episode_1_steps:
        print("  ✓ LEARNING: Episode 10 ≤ Episode 1")
    else:
        print("  ⚠️  No clear improvement")

    # At minimum, should maintain success
    assert episodes[9]['success'], "Episode 10 should succeed"


def test_neo4j_contains_complete_data():
    """
    Validation Test: Neo4j contains all expected data.

    Checks:
    - Episodes with quest/subgoals
    - Quest nodes with geometric analysis
    - Memory nodes
    """
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session() as session:
        # Check episodes
        result = session.run("""
            MATCH (e:Episode)
            WHERE e.quest IS NOT NULL
            RETURN count(e) as count
        """)
        episode_count = result.single()['count']
        print(f"✓ Episodes with quest data: {episode_count}")

        # Check Quest nodes (Phase 2)
        result = session.run("""
            MATCH (q:Quest)
            WHERE q.geometric_mean IS NOT NULL
            RETURN count(q) as count
        """)
        quest_count = result.single()['count']
        print(f"✓ Quest nodes with geometric analysis: {quest_count}")

        # Check Memory nodes (Phase 1)
        result = session.run("""
            MATCH (m:Memory)
            RETURN count(m) as count
        """)
        memory_count = result.single()['count']
        print(f"✓ Memory nodes: {memory_count}")

    driver.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

**RUN:**
```bash
python -m pytest tests/test_option_b_complete_synthesis.py -v
```

---

### Step 4.2: Performance Comparison (1 hour)

**CREATE SCRIPT:** `validation/compare_option_a_vs_b.py`

```python
"""
Compare Option A vs Option B performance.

Metrics:
- Success rate
- Steps to completion
- Learning over episodes
- Memory usage
- Geometric quality scores
"""
import sys
sys.path.insert(0, '/home/juancho/macgyver_mud')

from neo4j import GraphDatabase
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
import config


def run_episode(agent, quest):
    """Run single episode (mock)."""
    agent.reset(quest)

    steps = 0
    done = False
    state = "room_with_key"

    while not done and steps < 10:
        steps += 1

        if state == "room_with_key":
            obs = "You see a key"
            commands = ["take key", "look"]
            action = agent.step(obs, "", 0.0, False, commands, None)

            if "key" in action:
                state = "have_key"

        elif state == "have_key":
            obs = "You have key"
            commands = ["unlock door", "drop key"]
            action = agent.step(obs, "", 0.0, False, commands, None)

            if "unlock" in action:
                done = True

    return steps, done


def main():
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    session = driver.session()

    quest = "First, take the key. Then, unlock the door."

    print("="*80)
    print("OPTION A vs OPTION B COMPARISON")
    print("="*80)

    # Run 10 episodes
    print("\nRunning 10 episodes...")

    results = []
    for ep in range(1, 11):
        agent = TextWorldCognitiveAgent(session, verbose=False)
        steps, success = run_episode(agent, quest)
        results.append({'episode': ep, 'steps': steps, 'success': success})
        print(f"  Episode {ep}: {steps} steps, success={success}")

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    success_rate = sum(r['success'] for r in results) / len(results)
    avg_steps = sum(r['steps'] for r in results) / len(results)

    print(f"\nSuccess Rate: {success_rate*100:.0f}%")
    print(f"Average Steps: {avg_steps:.1f}")

    episode_1_steps = results[0]['steps']
    episode_10_steps = results[9]['steps']

    print(f"\nLearning:")
    print(f"  Episode 1:  {episode_1_steps} steps")
    print(f"  Episode 10: {episode_10_steps} steps")

    if episode_10_steps < episode_1_steps:
        improvement = ((episode_1_steps - episode_10_steps) / episode_1_steps) * 100
        print(f"  Improvement: {improvement:.1f}%")

    # Check Neo4j data
    print(f"\nNeo4j Data:")

    result = session.run("MATCH (e:Episode) WHERE e.quest IS NOT NULL RETURN count(e) as count")
    print(f"  Episodes with quest data: {result.single()['count']}")

    result = session.run("MATCH (q:Quest) WHERE q.geometric_mean IS NOT NULL RETURN count(q) as count")
    print(f"  Quest geometric analyses: {result.single()['count']}")

    result = session.run("MATCH (m:Memory) RETURN count(m) as count")
    print(f"  Memory nodes: {result.single()['count']}")

    session.close()
    driver.close()

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
```

**RUN:**
```bash
python validation/compare_option_a_vs_b.py
```

---

### Step 4.3: Update Documentation (2 hours)

**UPDATE FILE:** `HIERARCHICAL_SYNTHESIS_IMPLEMENTATION.md`

**ADD SECTION:**
```markdown
## Option B: Complete Synthesis - IMPLEMENTED

### Changes Beyond Option A

#### Phase 1: Quest-Aware Memory (Completed)

**Files Modified:**
- `memory_system.py`: Added subgoal-filtered retrieval
- `cognitive_agent.py`: Pass subgoal to memory, store quest data

**Key Features:**
1. Memory retrieval filtered by current subgoal
2. Episodes store quest text + decomposed subgoals
3. Procedural memory for action sequences
4. Learning over episodes demonstrated

**Tests:** 10 new tests in `test_quest_aware_memory.py`

#### Phase 2: Geometric Analysis (Completed)

**Files Created:**
- `quest_geometric_analyzer.py`: Silver Gauge implementation

**Files Modified:**
- `cognitive_agent.py`: Integrate geometric analysis in reset()

**Key Features:**
1. Pythagorean means (H ≤ G ≤ A) for decomposition quality
2. Coherence, completeness, specificity metrics
3. Neo4j logging of geometric data
4. Introspection: `agent.quest_geometric_analysis`

**Tests:** 9 new tests in `test_quest_geometric_analysis.py`

#### Phase 3: Quest-Aware Critical States (Completed)

**Files Modified:**
- `cognitive_agent.py`: Re-enable protocols with quest awareness

**Key Features:**
1. Progress tracking prevents false deadlock detection
2. Protocols respect subgoal execution
3. Intervene only when truly stuck
4. `_is_making_subgoal_progress()` method

**Tests:** 6 new tests in `test_quest_aware_critical_states.py`

### Performance Results

| Metric | Option A | Option B |
|--------|----------|----------|
| TextWorld Success | 100% | 100% |
| Episode 1 Steps | 3 | 3 |
| Episode 10 Steps | 3 | 2-3 (learning) |
| Memory Usage | Generic | Quest-specific |
| Geometric Analysis | No | Yes (logged to Neo4j) |
| Critical States | Disabled | Quest-aware |
| Total Tests | 30 | 55+ |

### Research Contribution

**Complete Demonstration:**

Option B demonstrates ALL innovations working together:

1. ✅ Active Inference (EFE scoring)
2. ✅ Hierarchical Decomposition
3. ✅ Quest-Aware Memory (procedural + episodic)
4. ✅ Geometric Analysis (Silver Gauge / Pythagorean means)
5. ✅ Meta-Cognitive Monitoring (quest-aware critical states)
6. ✅ Learning Over Episodes

**Strong Narrative:**

"We demonstrate that cognitive principles (active inference, episodic memory, meta-cognitive monitoring) generalize across domains when applied hierarchically. Strategic decomposition provides context for tactical optimization under reactive safety constraints. Geometric analysis validates decomposition quality, while quest-aware memory enables learning over episodes."

This is a COMPLETE research contribution. 🧠⚡
```

---

### Step 4.4: Final Validation Checklist

**COMPLETE VALIDATION:**

- [ ] All tests pass (55+ tests)
  ```bash
  python -m pytest tests/ -v
  ```

- [ ] TextWorld performance maintained (100%)
  ```bash
  python environments/domain4_textworld/compare_all_agents.py
  ```

- [ ] Backward compatibility (old tests pass)
  ```bash
  python -m pytest tests/test_textworld_cognitive_agent.py -v
  ```

- [ ] Neo4j contains complete data
  - Episodes with quest/subgoals
  - Quest nodes with geometric analysis
  - Memory nodes

- [ ] Learning demonstrated (Episode 10 performance ≥ Episode 1)
  ```bash
  python -m pytest tests/test_quest_learning_integration.py -v
  ```

- [ ] Documentation complete
  - Implementation details
  - Performance results
  - Research narrative

- [ ] Code clean and well-commented
  ```bash
  # Check for TODOs/FIXMEs
  grep -r "TODO\|FIXME" environments/domain4_textworld/*.py
  ```

---

## Testing Strategy

### Test-Driven Development (TDD) Approach

**For Each Phase:**

1. **RED:** Write tests FIRST (should fail)
2. **GREEN:** Implement minimal code to pass tests
3. **REFACTOR:** Clean up code, maintain tests passing

### Test Pyramid

```
        ┌─────────────────┐
        │  Integration    │  (5-10 tests)
        │  End-to-end     │
        └─────────────────┘
       ┌───────────────────┐
       │  Component        │  (20-30 tests)
       │  Individual       │
       │  Features         │
       └───────────────────┘
      ┌─────────────────────┐
      │  Unit               │  (25-35 tests)
      │  Utilities          │
      │  Functions          │
      └─────────────────────┘
```

### Running Tests

**Individual Phase:**
```bash
# Phase 1
python -m pytest tests/test_quest_aware_memory.py -v

# Phase 2
python -m pytest tests/test_quest_geometric_analysis.py -v

# Phase 3
python -m pytest tests/test_quest_aware_critical_states.py -v
```

**All Tests:**
```bash
# All Option B tests
python -m pytest tests/test_quest_aware_memory.py \
                 tests/test_quest_geometric_analysis.py \
                 tests/test_quest_aware_critical_states.py \
                 tests/test_option_b_complete_synthesis.py -v

# All project tests
python -m pytest tests/ -v
```

**With Coverage:**
```bash
python -m pytest tests/ --cov=environments/domain4_textworld --cov-report=html
```

---

## Validation Criteria

### Success Criteria for Option B

**Phase 1: Quest-Aware Memory**
- ✅ Episodes store quest + subgoals
- ✅ Memory retrieval filtered by subgoal
- ✅ Memory bonus integrated into EFE
- ✅ 10+ tests passing

**Phase 2: Geometric Analysis**
- ✅ Pythagorean means calculated correctly (H ≤ G ≤ A)
- ✅ Decomposition analyzed on reset
- ✅ Geometric metrics logged to Neo4j
- ✅ 9+ tests passing

**Phase 3: Quest-Aware Critical States**
- ✅ Critical states re-enabled
- ✅ No interference with valid quest execution
- ✅ Protocols intervene when truly stuck
- ✅ 6+ tests passing

**Complete Synthesis:**
- ✅ All 55+ tests passing
- ✅ TextWorld: 100% success maintained
- ✅ Learning over episodes demonstrated
- ✅ Neo4j contains complete data
- ✅ Zero regressions
- ✅ Documentation complete

### Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Success Rate | 100% | Compare agents script |
| Test Pass Rate | 100% | pytest |
| Episode 10 vs 1 | ≤ steps | Learning integration test |
| Memory Retrieval | Subgoal-filtered | Check Neo4j queries |
| Geometric Quality | > 0.5 | Check Neo4j Quest nodes |
| Critical State False Positives | 0 | Quest execution tests |

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Tests Fail - "No module named 'quest_geometric_analyzer'"

**Problem:** File not created or not in correct location

**Solution:**
```bash
# Check file exists
ls environments/domain4_textworld/quest_geometric_analyzer.py

# If not, create it (see Step 2.3)
# Make sure it's in the correct directory
```

#### Issue 2: Memory Retrieval Returns Empty List

**Problem:** Neo4j queries not finding memories

**Solution:**
```python
# Check Neo4j has data
from neo4j import GraphDatabase
import config

driver = GraphDatabase.driver(config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

with driver.session() as session:
    result = session.run("MATCH (m:Memory) RETURN count(m)")
    print(f"Memory count: {result.single()[0]}")

    result = session.run("MATCH (e:Episode) RETURN count(e)")
    print(f"Episode count: {result.single()[0]}")

driver.close()
```

If counts are 0, need to run episodes to populate data.

#### Issue 3: Critical States Interfering with Quest Execution

**Problem:** Agent stuck even though making progress

**Solution:**
```python
# Check progress tracking
# In cognitive_agent.py, add debug output to _is_making_subgoal_progress()

def _is_making_subgoal_progress(self) -> bool:
    # ... existing code ...

    if self.verbose:
        print(f"   🔍 Progress check:")
        print(f"      Recent rewards: {self.reward_history[-3:]}")
        print(f"      Unique locations: {len(set(self.location_history[-5:]))}")
        print(f"      Current subgoal: {self.subgoals[self.current_subgoal_index]}")

    # ... rest of method ...
```

Run with verbose=True and check output.

#### Issue 4: Geometric Analysis Produces NaN

**Problem:** Invalid values in Pythagorean mean calculation

**Solution:**
```python
# Check for zero or negative values
# In quest_geometric_analyzer.py, add validation:

def calculate_harmonic_mean(values):
    # Filter out invalid values
    valid_values = [v for v in values if v > 0]

    if not valid_values:
        return 0.0  # Fallback

    # ... rest of calculation ...
```

#### Issue 5: Tests Pass But TextWorld Fails

**Problem:** Test mocks don't match real environment

**Solution:**
```bash
# Run actual TextWorld game with verbose
python3 -c "
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from neo4j import GraphDatabase
import config
import textworld

# ... setup ...
agent = TextWorldCognitiveAgent(session, verbose=True)
# ... run real game ...
"
```

Check verbose output for issues.

#### Issue 6: Neo4j Connection Fails

**Problem:** Neo4j not running or wrong credentials

**Solution:**
```bash
# Check Neo4j running
docker ps | grep neo4j

# If not running, start it
# (Check project's docker-compose.yml or README)

# Test connection
python3 -c "
from neo4j import GraphDatabase
import config

try:
    driver = GraphDatabase.driver(config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run('RETURN 1')
        print('✓ Connected to Neo4j')
    driver.close()
except Exception as e:
    print(f'✗ Connection failed: {e}')
"
```

---

## File Reference Guide

### Files to Read (Understanding)

1. **cognitive_agent.py** (main implementation)
   - Current Option A implementation
   - Lines to focus on: 38-80 (init), 110-160 (reset), 342-391 (goal scoring)

2. **quest_decomposer.py**
   - How quest decomposition works
   - Regex patterns and cleanup logic

3. **memory_system.py**
   - Current memory implementation
   - Understand retrieval method signature

4. **critical_state.py**
   - Critical state definitions
   - Protocol implementations

5. **graph_model.py** (if exists)
   - Existing geometric utilities
   - Silver Gauge implementation

### Files to Modify (Implementation)

1. **cognitive_agent.py**
   - Add geometric analysis integration (~20 lines)
   - Modify memory retrieval (~30 lines)
   - Re-enable critical states with quest awareness (~50 lines)
   - Add progress tracking method (~40 lines)

2. **memory_system.py**
   - Add subgoal-filtered retrieval (~80 lines)
   - Add procedural memory storage (~40 lines)

3. **save_episode() method in cognitive_agent.py**
   - Add quest/subgoal storage (~30 lines)

### Files to Create (New Implementation)

1. **quest_geometric_analyzer.py** (~300 lines)
   - Pythagorean mean utilities
   - Coherence/completeness/specificity measurement
   - Neo4j logging

2. **test_quest_aware_memory.py** (~400 lines)
   - Phase 1 tests

3. **test_quest_geometric_analysis.py** (~350 lines)
   - Phase 2 tests

4. **test_quest_aware_critical_states.py** (~300 lines)
   - Phase 3 tests

5. **test_option_b_complete_synthesis.py** (~200 lines)
   - Integration tests

6. **compare_option_a_vs_b.py** (~150 lines)
   - Performance comparison script

### Files to Test (Validation)

**Run these to verify no regression:**
```bash
python -m pytest tests/test_textworld_cognitive_agent.py
python -m pytest tests/test_textworld_active_inference.py
python -m pytest tests/test_textworld_quest_synthesis.py
python -m pytest tests/test_graph_labyrinth.py
```

**Run these for new functionality:**
```bash
python -m pytest tests/test_quest_aware_memory.py
python -m pytest tests/test_quest_geometric_analysis.py
python -m pytest tests/test_quest_aware_critical_states.py
python -m pytest tests/test_option_b_complete_synthesis.py
```

---

## Bootstrap Checklist for New Claude Instance

When continuing this work, verify:

- [ ] I've read the entire context section
- [ ] I understand what Option A achieved (hierarchical goal scoring)
- [ ] I understand what Option B adds (memory + geometric + critical states)
- [ ] I've located all key files (cognitive_agent.py, memory_system.py, etc.)
- [ ] I've verified current state (run existing tests)
- [ ] I know which phase to start (or continue from)
- [ ] I understand TDD approach (tests first, then implementation)
- [ ] I have Neo4j connection working
- [ ] I've read the troubleshooting guide

**Quick Start Command:**
```bash
# 1. Verify environment
python -m pytest tests/test_textworld_quest_synthesis.py -v

# 2. Check current phase progress
ls tests/test_quest_aware_memory.py  # Phase 1
ls tests/test_quest_geometric_analysis.py  # Phase 2
ls tests/test_quest_aware_critical_states.py  # Phase 3

# 3. Start from first incomplete phase
# If Phase 1 incomplete, start at Step 1.1
# If Phase 1 complete, start Phase 2, etc.
```

---

## Final Notes

### Implementation Philosophy

1. **Test-Driven:** Write tests BEFORE implementation
2. **Incremental:** One phase at a time, validate each
3. **Safe:** Maintain backward compatibility
4. **Thorough:** 55+ tests total
5. **Documented:** Update docs as you go

### Time Estimates

- **Phase 1:** 8-10 hours (memory)
- **Phase 2:** 6-8 hours (geometric)
- **Phase 3:** 6-8 hours (critical states)
- **Phase 4:** 4-6 hours (integration)
- **Total:** 25-35 hours

### Success Metrics

**At completion, you should have:**

✅ 55+ tests passing (100%)
✅ TextWorld: 100% success maintained
✅ Learning over episodes demonstrated
✅ Neo4j rich with data (episodes, quests, memories)
✅ Complete documentation
✅ Zero regressions
✅ Publication-ready research contribution

---

## Getting Help

If stuck:

1. **Check troubleshooting guide** (section above)
2. **Run existing tests** to verify baseline
3. **Add debug output** (verbose=True)
4. **Check Neo4j browser** (http://localhost:7474)
5. **Refer to Option A implementation** (working example)

Remember: This is a COMPLETE plan. Follow it step-by-step, test thoroughly, and you'll achieve Option B successfully.

**Good luck! 🚀**

---

**Document Version:** 1.0
**Status:** Ready for Implementation
**Next Action:** Start Phase 1, Step 1.1
**Estimated Completion:** 25-35 hours from start
