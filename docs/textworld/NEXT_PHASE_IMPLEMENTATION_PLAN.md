# Next Phase Implementation Plan: "Close the Loop"

**Date:** 2025-11-23 23:50 UTC
**Strategic Goal:** Validate planning works, then complete memory system for full cognitive loop
**Mission:** Make an effective agent, not just build infrastructure

---

## Deep Analysis: What "Closing the Loop" Actually Means

### The Current State (Honest Assessment)

We have **three cognitive loops**, each at different stages of completion:

```
Loop 1: Planning → Action Selection
├─ Planning generates plans ✅ (just implemented)
├─ Plans influence EFE via bonus (+10-12) ✅
├─ Actions are selected based on EFE ✅
├─ Plan progress is tracked ✅
└─ STATUS: BUILT but UNVALIDATED
    └─ We don't know if this actually improves performance

Loop 2: Memory → Action Selection
├─ Memory retrieval is called ❌ (returns empty lists)
├─ Memory bonus influences EFE ✅ (gets 0.0 from empty data)
├─ Episode history is stored ⚠️ (partially - to Neo4j)
└─ STATUS: INTERFACE EXISTS, IMPLEMENTATION MISSING
    └─ This is the critical blocker for learning

Loop 3: Critical State → Action Override
├─ Critical monitor evaluates state ✅
├─ Protocols trigger on thresholds ✅
├─ Actions are overridden when needed ✅
└─ STATUS: COMPLETE and TESTED
    └─ This works and is validated
```

### What "Effective Agent" Actually Requires

For the agent to be **demonstrably effective**, we need:

1. **Empirical Validation** - Proof that our systems improve performance
2. **Learning Across Episodes** - Agent gets better over time
3. **Adaptive Behavior** - Agent responds intelligently to context
4. **Measurable Improvement** - Quantifiable metrics (win rate, efficiency)

**Current Status:**
- ✅ Adaptive behavior (critical states work)
- ⚠️ Empirical validation (incomplete)
- ❌ Learning across episodes (memory is mocked)
- ❌ Measurable improvement (no benchmarks yet)

---

## Critical Next Steps Analysis

### The Fork in the Road

We have **two valid strategies**, each with different value propositions:

**Strategy A: Validate First (Risk Mitigation)**
```
1. Run 2-3 episodes with planning (verbose) → 30 min
2. Observe if plans are generated and followed → immediate feedback
3. Identify bugs or failures in plan execution → fix before building more
4. THEN implement memory system → 2-3 hours
5. THEN comprehensive benchmarking → 1-2 hours
```

**Pro:** Early validation prevents building on broken foundations
**Con:** Delays completing the "planning + memory" vertical slice

**Strategy B: Complete Vertical Slice (Commitment Fulfillment)**
```
1. Implement memory system immediately → 2-3 hours
2. Complete the "planning + memory" commitment → closure
3. THEN validate both together → 1-2 hours
4. Fix issues holistically → TBD
```

**Pro:** Completes the promised work, enables learning
**Con:** Risk of discovering planning issues after memory is built

### My Deep Recommendation: **Strategy A with Immediate Memory After**

**Rationale:**

1. **Risk Management:** We just integrated planning (893 lines changed). We should validate it works before building the next layer.

2. **Fast Feedback:** Running 2-3 episodes takes 30 minutes but could reveal critical issues (e.g., goal inference fails, plans are ignored, LLM timeouts).

3. **Motivation:** Seeing plans work (or fail) in real episodes provides crucial context for memory implementation.

4. **Incremental Progress:** Quick win (validation) → bigger win (memory) → comprehensive win (benchmarks).

5. **User Expectation:** You asked to "close the loop" - this means validating the loop actually closes, not just assuming it does.

---

## Implementation Plan: Phase 2 Complete

### **Step 1: Quick Validation Run (30 minutes)**

**Objective:** See planning in action, identify obvious issues

**Action Items:**

1. **Create validation script** - Run agent with planning enabled, verbose output
```python
# environments/domain4_textworld/validate_planning.py
# - Run 3 simple TextWorld games
# - Log plan generation, step tracking, completion
# - Output: Success/failure patterns
```

2. **Manual observation checklist:**
   - [ ] Does goal inference trigger correctly?
   - [ ] Are plans generated (or does LLM fail)?
   - [ ] Do plans have reasonable steps (3-7)?
   - [ ] Does agent follow plans or ignore them?
   - [ ] Does plan bonus influence action selection?
   - [ ] Are plans completed or abandoned?

3. **Expected outcomes:**
   - **Best case:** Plans work, agent follows them, we see coherent behavior
   - **Likely case:** Plans work but reveal tuning needs (goal inference, bonus weight)
   - **Worst case:** LLM fails, plans are gibberish, or agent ignores them

**Deliverable:** Short report (5-10 lines) on what works and what doesn't

**Time:** 30-45 minutes (implementation + run + observation)

---

### **Step 2: Implement Memory System (2-3 hours)**

**Objective:** Enable cross-episode learning via semantic memory retrieval

**Why This Is Critical:**

Memory is the **other half** of the cognitive loop. Without it:
- Plans can't learn from past failures (we have the API but no data)
- Agent repeats mistakes across episodes
- Neo4j graph is underutilized (we store but don't retrieve)

**Architecture Decision:**

We have **two approaches** for memory retrieval:

#### **Option A: LLM-Based Semantic Retrieval (Recommended)**

Use `llm` CLI to query Neo4j and retrieve relevant memories:

```python
def retrieve_relevant_memories(self, context: str, action: str) -> List[Dict]:
    """Retrieve using LLM to query Neo4j."""
    # Build query prompt
    prompt = f"""
    Context: {context}
    Proposed Action: {action}

    Query the Neo4j database for relevant past experiences.
    Return episodes where similar actions were taken in similar contexts.
    """

    # Call LLM with Neo4j schema knowledge
    result = subprocess.run([
        'llm',
        '--sf', str(self.memory_fragment_path),
        '--schema', str(self.memory_schema_path),
        prompt
    ], capture_output=True, text=True)

    # Parse and return memories
    memories = json.loads(result.stdout)
    return self._rank_by_relevance(memories, context, action)
```

**Pros:**
- No embedding infrastructure needed
- Leverages existing `llm` integration pattern
- LLM can reason about semantic similarity
- Consistent with planning approach

**Cons:**
- Slower than vector search
- More LLM API calls (cost)
- Requires Neo4j schema knowledge in fragment

#### **Option B: Simple Cypher Query Retrieval (Faster, Limited)**

Use pattern matching in Neo4j:

```python
def retrieve_relevant_memories(self, context: str, action: str) -> List[Dict]:
    """Retrieve using Cypher pattern matching."""
    # Extract key entities from context/action
    room = self._extract_room(context)
    action_verb = action.split()[0].lower()

    # Query Neo4j for similar episodes
    query = """
    MATCH (e:Episode)-[:CONTAINS]->(s:Step)
    WHERE s.room = $room
      AND s.action CONTAINS $action_verb
      AND e.reward IS NOT NULL
    RETURN e.id, e.reward, s.action, s.outcome
    ORDER BY e.timestamp DESC
    LIMIT 5
    """

    results = self.session.run(query, room=room, action_verb=action_verb)
    return self._format_memories(results)
```

**Pros:**
- Fast (milliseconds)
- No LLM calls
- Uses existing Neo4j infrastructure
- Simple to implement

**Cons:**
- Limited semantic understanding (keyword matching)
- May miss relevant but differently-phrased memories
- Requires good entity extraction

#### **Recommended Hybrid Approach:**

```python
def retrieve_relevant_memories(self, context: str, action: str) -> List[Dict]:
    """Hybrid: Cypher first, LLM refinement if needed."""
    # 1. Fast retrieval via Cypher (top-10)
    candidates = self._cypher_retrieve(context, action, limit=10)

    if not candidates:
        return []  # No memories found

    # 2. If we have multiple candidates, use LLM to rank
    if len(candidates) > 3:
        candidates = self._llm_rerank(candidates, context, action, top_k=3)

    return candidates
```

**Implementation Details:**

**A. Create Memory Schema**
```json
{
  "type": "object",
  "required": ["memories"],
  "properties": {
    "memories": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["action", "outcome", "confidence", "summary"],
        "properties": {
          "action": {"type": "string"},
          "outcome": {"type": "string", "enum": ["positive", "negative", "neutral"]},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "summary": {"type": "string"},
          "context": {"type": "string"}
        }
      }
    }
  }
}
```

**B. Create Memory Fragment**
```markdown
STATEMENT: You retrieve relevant episodic memories from past TextWorld experiences.

ASSUMPTIONS:
- Memories are stored in Neo4j as Episode and Step nodes
- Relevance is based on context similarity and action similarity
- Recent memories are more reliable than old ones

SOCRATIC (answer briefly):
1) What makes a memory relevant to this context and action?
2) How do you weigh recency vs. similarity?
3) What outcome information is most useful?

APHORISMS:
- Recent failures teach more than ancient successes
- Similar context + similar action = relevant memory
- Return empty rather than irrelevant

ACCEPTANCE:
- Return 0-5 memories (not more)
- Each memory must have: action, outcome, confidence, summary
- Confidence reflects both match quality and recency
```

**C. Implement Episode Storage**

Currently we store episodes but need to enhance structure:

```python
def save_episode_to_graph(self):
    """Save episode with proper structure for retrieval."""
    if not self.session:
        return

    # Create episode node
    episode_id = f"tw_ep_{self.current_step}_{hash(time.time())}"

    self.session.run("""
        CREATE (e:Episode:TextWorldEpisode {
            id: $id,
            timestamp: timestamp(),
            total_steps: $steps,
            total_reward: $reward,
            success: $success,
            goal: $goal,
            plan_count: $plan_count
        })
    """,
        id=episode_id,
        steps=self.current_step,
        reward=sum(self.reward_history),
        success=self.done and sum(self.reward_history) > 0,
        goal=self.current_plan.goal if self.current_plan else None,
        plan_count=len(self.plan_history)
    )

    # Create step nodes with rich context
    for i, (action, obs, reward) in enumerate(zip(
        self.action_history,
        self.observation_history,
        self.reward_history
    )):
        self.session.run("""
            MATCH (e:Episode {id: $ep_id})
            CREATE (e)-[:CONTAINS]->(s:Step {
                step_number: $step,
                action: $action,
                room: $room,
                reward: $reward,
                outcome: $outcome
            })
        """,
            ep_id=episode_id,
            step=i,
            action=action['action'],
            room=obs.get('room', 'Unknown'),
            reward=reward,
            outcome='positive' if reward > 0 else ('negative' if reward < 0 else 'neutral')
        )
```

**D. Implement Retrieval**

```python
def retrieve_relevant_memories(self, context: str, action: str) -> List[Dict]:
    """Retrieve relevant memories using hybrid approach."""
    if not self.session:
        return []

    # Extract entities for query
    room = self._extract_room_from_context(context)
    action_verb = action.split()[0].lower() if action else ""

    # Cypher query for candidates
    query = """
    MATCH (e:Episode)-[:CONTAINS]->(s:Step)
    WHERE (s.room = $room OR s.action CONTAINS $action_verb)
      AND e.timestamp > timestamp() - (7 * 24 * 60 * 60 * 1000)  // Last 7 days
    WITH e, s,
         CASE WHEN s.room = $room THEN 2 ELSE 0 END +
         CASE WHEN s.action CONTAINS $action_verb THEN 2 ELSE 0 END AS relevance_score
    WHERE relevance_score > 0
    RETURN e.id, e.success, s.action, s.outcome, s.reward, s.room,
           relevance_score,
           (timestamp() - e.timestamp) / (24.0 * 60 * 60 * 1000) AS days_ago
    ORDER BY relevance_score DESC, days_ago ASC
    LIMIT 5
    """

    try:
        result = self.session.run(query, room=room, action_verb=action_verb)
        memories = []

        for record in result:
            # Calculate confidence based on relevance and recency
            relevance = record['relevance_score'] / 4.0  # Normalize to 0-1
            recency = max(0, 1.0 - (record['days_ago'] / 7.0))  # Decay over week
            confidence = (relevance * 0.7) + (recency * 0.3)

            memories.append({
                'action': record['s.action'],
                'outcome': record['s.outcome'],
                'confidence': confidence,
                'summary': f"In {record['s.room']}, {record['s.action']} → {record['s.outcome']} (reward: {record['s.reward']})"
            })

        return memories

    except Exception as e:
        if self.verbose:
            print(f"⚠️ Memory retrieval error: {e}")
        return []

def _extract_room_from_context(self, context: str) -> str:
    """Extract room name from context string."""
    # Simple extraction - context format: "Current Room: XYZ\n..."
    if "Current Room:" in context:
        lines = context.split('\n')
        for line in lines:
            if "Current Room:" in line:
                return line.split("Current Room:")[1].strip()
    return "Unknown"
```

**Testing:**

```python
# tests/test_textworld_memory_integration.py
def test_memory_retrieval_with_neo4j():
    """Test real memory retrieval from Neo4j."""
    # Store fake episode
    # Retrieve memories for similar context/action
    # Assert relevant memories are returned

def test_memory_bonus_with_real_data():
    """Test that memory bonus uses retrieved data."""
    # Store positive outcome for action
    # Calculate bonus for same action
    # Assert bonus is positive

def test_empty_memory_graceful():
    """Test graceful handling when no memories exist."""
    # Query with no stored episodes
    # Assert returns empty list
    # Assert no errors
```

**Time Estimate:** 2-3 hours
- Schema/fragment creation: 30 min
- Cypher implementation: 1 hour
- Episode storage enhancement: 45 min
- Testing: 45 min

---

### **Step 3: Integration Validation (30 minutes)**

**Objective:** Verify memory system works with agent

**Action Items:**

1. Run agent with memory enabled
2. Store episode after first game
3. Run second game, verify memories are retrieved
4. Check memory bonus influences action selection

**Success Criteria:**
- [ ] Memories are stored with proper structure
- [ ] Retrieval returns relevant memories (not empty)
- [ ] Memory bonus is non-zero when memories exist
- [ ] Agent learns from past episodes (observable behavior change)

---

### **Step 4: Comprehensive Benchmarking (1-2 hours)**

**Objective:** Quantify agent effectiveness with full system

**Benchmark Design:**

```python
# benchmarks/textworld_planning_memory_benchmark.py

def run_benchmark(n_episodes=20):
    """Run comparative benchmark."""
    conditions = [
        {'name': 'Baseline', 'planning': False, 'memory': False},
        {'name': 'Planning Only', 'planning': True, 'memory': False},
        {'name': 'Memory Only', 'planning': False, 'memory': True},
        {'name': 'Full System', 'planning': True, 'memory': True}
    ]

    results = {}
    for condition in conditions:
        wins = 0
        total_steps = []
        total_rewards = []

        for episode in range(n_episodes):
            agent = create_agent(**condition)
            outcome = run_episode(agent)

            if outcome['success']:
                wins += 1
            total_steps.append(outcome['steps'])
            total_rewards.append(outcome['reward'])

        results[condition['name']] = {
            'win_rate': wins / n_episodes,
            'avg_steps': np.mean(total_steps),
            'avg_reward': np.mean(total_rewards),
            'efficiency': wins / np.mean(total_steps)
        }

    return results
```

**Metrics:**
- Win rate (primary)
- Average steps to completion
- Average reward
- Efficiency (wins per step)
- Plan completion rate (new)
- Memory retrieval rate (new)

**Statistical Validation:**
- Run N=20 episodes per condition
- Calculate confidence intervals
- Run t-tests for significance

**Time:** 1-2 hours (depending on game complexity)

---

### **Step 5: Failure Analysis & Tuning (1 hour)**

**Objective:** Identify and fix issues revealed by benchmarks

**Analysis Questions:**

1. **Planning Issues:**
   - Are goals being inferred correctly?
   - Are plans reasonable for the context?
   - Why are plans abandoned (if they are)?
   - Does plan bonus need tuning (ε=2.0)?

2. **Memory Issues:**
   - Are memories being retrieved?
   - Are retrieved memories actually relevant?
   - Does memory bonus need tuning (δ=1.5)?
   - Is episode storage capturing enough context?

3. **Integration Issues:**
   - Do planning and memory conflict?
   - Is EFE scoring balanced across all terms?
   - Are critical states overriding too aggressively?

**Tuning Levers:**
- EFE coefficients (α, β, γ, δ, ε)
- Goal inference patterns
- Memory relevance scoring
- Plan bonus weights
- Critical state thresholds

---

## Success Criteria

### Phase 2 Complete When:

✅ **Planning Validation:**
- [ ] Plans are generated in real episodes
- [ ] Agent follows plans (observable behavior)
- [ ] Plan bonus influences decisions
- [ ] Plan completion tracked and logged

✅ **Memory Implementation:**
- [ ] Memory retrieval returns non-empty results
- [ ] Retrieved memories are contextually relevant
- [ ] Memory bonus influences action selection
- [ ] Episodes are stored with rich context

✅ **Performance Validation:**
- [ ] Benchmarks show quantifiable improvement
- [ ] Planning improves win rate OR efficiency
- [ ] Memory enables cross-episode learning
- [ ] Statistical significance demonstrated

✅ **Integration Quality:**
- [ ] All TextWorld tests passing
- [ ] No regressions in critical state handling
- [ ] Clean error handling throughout
- [ ] Comprehensive test coverage

---

## Timeline

**Total Estimated Time: 5-7 hours**

| Step | Task | Time | Priority |
|------|------|------|----------|
| 1 | Quick planning validation | 30-45 min | CRITICAL |
| 2 | Implement memory system | 2-3 hours | CRITICAL |
| 3 | Integration validation | 30 min | HIGH |
| 4 | Comprehensive benchmarks | 1-2 hours | HIGH |
| 5 | Failure analysis & tuning | 1 hour | MEDIUM |

**Recommended Session Plan:**
- **Tonight:** Steps 1-2 (validate planning, implement memory) → 3-4 hours
- **Next session:** Steps 3-5 (integrate, benchmark, tune) → 2-3 hours

---

## Risk Mitigation

### Potential Blockers:

1. **LLM API failures** - Fallback to simple Cypher queries
2. **Neo4j schema issues** - Clear and reinitialize if needed
3. **Planning doesn't work** - Debug before building memory
4. **Memory retrieval too slow** - Cache recent queries
5. **Benchmarks take too long** - Reduce N, use simpler games

### Contingency Plans:

- If planning is broken → Fix before memory
- If memory is too complex → Start with simple Cypher, iterate
- If benchmarks show no improvement → Analyze why, don't abandon
- If integration breaks tests → Revert, fix incrementally

---

## Expected Outcomes

### Best Case:
- Planning works well, improves win rate by 10-20%
- Memory enables learning, improves performance over episodes
- Full system shows emergent intelligent behavior
- Clear path to further improvements

### Realistic Case:
- Planning works but needs tuning (goal inference, bonus weight)
- Memory retrieval works but relevance needs improvement
- Modest performance improvement (5-10%)
- Clear areas for optimization identified

### Worst Case:
- Planning generates poor plans (fix LLM prompt/fragment)
- Memory retrieval is too slow or irrelevant (simplify)
- No performance improvement (deeper analysis needed)
- But: We learn what doesn't work and why

**Key Insight:** Even "worst case" is progress because we'll have empirical data on what needs fixing.

---

## Bottom Line

**Next Best Actions:**

1. **Immediate (30 min):** Validate planning with real episodes
   - Creates: `environments/domain4_textworld/validate_planning.py`
   - Runs: 3 episodes with verbose output
   - Delivers: Quick assessment of planning effectiveness

2. **Core Work (2-3 hours):** Implement memory system
   - Creates: Enhanced `memory_system.py` with Cypher retrieval
   - Creates: Memory schema and fragment
   - Creates: Episode storage with rich context
   - Delivers: Functional cross-episode learning

3. **Validation (30 min):** Integration test
   - Runs: Agent with planning + memory
   - Verifies: Data flows through full cognitive loop
   - Delivers: Confidence in integration

4. **Proof (1-2 hours):** Benchmark and measure
   - Runs: Comparative benchmarks (baseline vs. full)
   - Analyzes: Statistical significance
   - Delivers: Quantified effectiveness

**This closes the loop because:**
- Planning → validated it works
- Memory → implemented for learning
- Integration → tested end-to-end
- Benchmarks → proven effectiveness
- **Result:** Effective agent, not just infrastructure

**Philosophy:** Validate early, build incrementally, measure ruthlessly.
