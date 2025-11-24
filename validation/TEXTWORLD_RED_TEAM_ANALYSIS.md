# TextWorld Integration Red Team Analysis

**Date:** 2025-11-24
**Status:** 🔴 CRITICAL ISSUES IDENTIFIED
**Success Rate:** 0% (Cognitive Agent) vs ~100% (Simple LLM)

---

## Executive Summary

The TextWorld integration has **catastrophically failed** despite significant implementation effort. The Simple LLM baseline consistently wins in 3 steps, while the Cognitive Agent gets stuck in action loops and never completes quests. This represents a fundamental architecture mismatch rather than minor tuning issues.

**Critical Finding:** The cognitive architecture that excels at graph-based spatial navigation (MacGyver MUD, Graph Labyrinth) is **actively harmful** for sequential task completion in TextWorld.

---

## Test Results: The Stark Reality

### Simple LLM Baseline
- **Success Rate:** ~100%
- **Steps to Completion:** 3 steps
- **Approach:** Direct quest interpretation → Execute sequence
- **Example:**
  ```
  Quest: "move east, recover nest from table, place nest in dresser"
  Actions:
  1. go east
  2. take nest of spiders from table
  3. insert nest of spiders into dresser
  ✅ WON
  ```

### Cognitive Agent (Current)
- **Success Rate:** 0%
- **Steps to Completion:** Never (hits max_steps)
- **Failure Mode:** Action loops (take nest → put nest → take nest...)
- **Example:**
  ```
  Steps 4-20:
  - take nest of spiders from table
  - put nest of spiders on table
  - take nest of spiders from table
  - put nest of spiders on table
  [... repeats until timeout]
  ❌ FAILED
  ```

**Verdict:** The cognitive agent is ~100x worse than a zero-shot LLM prompt.

---

## Root Cause Analysis

### 1. **The Quest Blindness Problem**

**Issue:** The agent doesn't properly use quest information for action selection.

**Evidence from `cognitive_agent.py:299-335`:**
```python
def calculate_goal_value(self, action: str) -> float:
    value = 0.5  # Base value

    # Quest keyword matching (lines 302-320)
    if hasattr(self, 'last_quest') and self.last_quest:
        # Extract overlapping words
        # Bonus: 10.0 * len(meaningful_common)
```

**Problem:**
- Word overlap is crude: "take nest" overlaps with "take insect" equally
- No understanding of **sequence**: Quest says "FIRST move east, THEN take nest"
- Agent doesn't track quest progress (step 1 of 3 complete)

**Result:** Agent picks high-scoring actions randomly instead of following quest sequence.

---

### 2. **The Loop Trap**

**Issue:** Cost penalties don't prevent action oscillations.

**Evidence from `cognitive_agent.py:229-264`:**
```python
def calculate_cost(self, action: str) -> float:
    cost = 1.0

    # Immediate repetition penalty
    if action == last_action:
        cost += 5.0

    # Frequency penalty (last 10 actions)
    count = recent_actions.count(action)
    cost += count * 0.5
```

**Problem:**
- Penalty for `take nest → take nest` (same action)
- NO penalty for `take nest → put nest → take nest` (alternating actions)
- Agent sees "put nest" as *different* from "take nest" (technically correct, pragmatically disastrous)

**Result:** Agent oscillates between complementary actions indefinitely.

---

### 3. **Critical State Protocols Are Disabled**

**Issue:** The safety mechanisms that make this architecture robust were intentionally turned off.

**Evidence from `cognitive_agent.py:947-962`:**
```python
# CRITICAL FIX: Disable critical state monitoring for TextWorld
# The ESCALATION/DEADLOCK/NOVELTY protocols were overriding quest-aware action selection

# Force FLOW state (normal operation, no protocol override)
self.current_critical_state = CriticalState.FLOW
protocol_action = None
```

**Comment says:** "For TextWorld quests, we want to follow the EFE scores directly"

**Problem:**
- DEADLOCK protocol would have detected `take → put → take` loop by step 8
- Sisyphus Protocol would have forced perturbation (try different action)
- **Protocols were disabled because they conflicted with quest completion**

**Implication:** The architecture's meta-cognitive safety features **cannot coexist** with task-driven behavior in TextWorld.

---

### 4. **Planning Layer Is Disconnected**

**Issue:** LLM-based planning exists but doesn't drive behavior effectively.

**Evidence from `cognitive_agent.py:459-507`:**
```python
def maybe_generate_plan(self, admissible_commands: List[str]):
    # Only generates if:
    # - No active plan
    # - Goal can be inferred
    # - current_step >= 3 (waits 3 steps before planning!)

    # Calls LLMPlanner.generate_plan()
    # Creates Plan object with steps
```

**Problem:**
- Plan is created at step 3+ (agent already diverging by then)
- Plan bonus weight (`epsilon = 5.0`) competes with other scores instead of dominating
- Plan matching is fuzzy: `step.action_pattern = "take key"` matches any action with "take" and "key"

**Result:** Plans are suggestive, not prescriptive. Agent still follows EFE scores.

---

### 5. **The Perception Layer Doesn't Help**

**Issue:** LLM-based parsing was added to extract entities, but quest understanding wasn't addressed.

**Evidence:**
- `llm_parser.py`: Parses objects from text (fallback to LLM if regex fails)
- `text_parser.py`: Regex for room names, objects, inventory

**Problem:**
- Perception extracts *what's in the world*
- Quest requires understanding *what to do and when*
- No temporal reasoning: "First A, then B, then C"

**Result:** Agent sees the world clearly but doesn't know what to do with it.

---

## Architectural Mismatch: Why This Failed

### The MacGyver MUD Architecture Is Designed For:

✅ **Spatial Navigation**
- Graph exploration (rooms, connections)
- Bayesian belief updates (p_unlocked)
- Multi-objective optimization (goal + info + cost)
- Loop detection (visiting same room repeatedly)

✅ **Uncertainty Management**
- High entropy → PANIC (choose safe actions)
- Low steps → SCARCITY (force efficiency)
- Deadlocks → SISYPHUS (perturbation)

✅ **Learning From Experience**
- Episodic memory (counterfactuals)
- Procedural memory (skill success rates)
- Credit assignment (blame dangerous paths)

### TextWorld Requires:

❌ **Sequential Task Execution**
- Linear quest decomposition: [A, B, C]
- Strong temporal ordering: "First... then... finally..."
- Progress tracking: "I've done A and B, now do C"

❌ **Goal-Directed Behavior**
- Quest is the *only* objective
- Exploration is *bad* (wastes steps)
- High goal weight should dominate all other factors

❌ **Hierarchical Planning**
- Commit to a plan upfront
- Execute plan steps sequentially
- Override reactive scoring with plan adherence

**Conclusion:** The architecture is fundamentally misaligned with TextWorld's task structure.

---

## Why Simple LLM Wins

The simple baseline (`simple_llm_player.py`) works because:

1. **Direct Quest Interpretation:** LLM reads quest, understands sequence
2. **No Competing Objectives:** Only goal = complete quest (no exploration, no info gain)
3. **No Loops:** LLM doesn't oscillate between complementary actions
4. **No Over-Engineering:** No EFE, no beliefs, no protocols—just "what should I do next?"

**Key Insight:** For sequential tasks with clear instructions, **simpler is better**.

---

## Red Team Findings

### Finding 1: Quest-Awareness Is Surface-Level

**Severity:** 🔴 Critical

**Details:**
- `calculate_goal_value()` uses keyword overlap (lines 302-320)
- Quest: "First move east, then take nest, then place in dresser"
- Agent scores "take insect" highly (overlaps with "take")
- Agent scores "go east" highly (overlaps with "east")
- **No sequential understanding**

**Impact:** Agent cannot distinguish quest-relevant actions from similar-sounding irrelevant actions.

---

### Finding 2: Critical States Disabled Out of Necessity

**Severity:** 🔴 Critical

**Details:**
- DEADLOCK detection would have saved the agent (lines 947-962)
- But it was disabled because it "overrode quest-aware action selection"
- **This reveals a design conflict:** Safety protocols vs Task completion

**Impact:** Agent has no circuit breaker for loops in TextWorld context.

---

### Finding 3: Planning Is Weak

**Severity:** 🟡 High

**Details:**
- LLM generates plans at step 3+ (lines 472-474)
- Plan bonus weight (`epsilon = 5.0`) competes with other factors
- Plan step matching is fuzzy (token-based, not exact)
- Agent can ignore plan if other actions score higher

**Impact:** Plans don't enforce execution discipline.

---

### Finding 4: Loop Detection Logic Is Inadequate

**Severity:** 🟡 High

**Details:**
- `calculate_cost()` penalizes immediate repetition: A → A
- Does NOT penalize alternating actions: A → B → A → B
- TextWorld actions are often complementary: `take X` ↔ `put X`

**Impact:** Agent oscillates indefinitely between complementary actions.

---

### Finding 5: No Progress Tracking

**Severity:** 🟠 Medium

**Details:**
- Quest: "Move east [25%], take nest [50%], place in dresser [75%], done [100%]"
- Agent doesn't track which parts of quest are complete
- Each step re-evaluates all actions independently
- No memory of "I already moved east"

**Impact:** Agent may repeat completed sub-tasks.

---

## Comparison with Successful Domains

### MacGyver MUD (Original) ✅
- **Task:** Navigate graph, find key, unlock door
- **Architecture Fit:** Perfect
  - Graph exploration (Neo4j)
  - Belief updates (Bayesian)
  - Critical states (DEADLOCK for loops)
- **Result:** 96% success rate

### Graph Labyrinth ✅
- **Task:** Navigate multi-room spatial graph
- **Architecture Fit:** Excellent
  - Spatial reasoning
  - Shortest path algorithms (Dijkstra)
  - SCARCITY (time pressure)
- **Result:** All tests pass

### TextWorld ❌
- **Task:** Execute linear instruction sequence
- **Architecture Fit:** Terrible
  - No temporal reasoning
  - No quest decomposition
  - Exploration conflicts with task completion
- **Result:** 0% success rate

**Pattern:** Architecture excels at **graph problems**, fails at **plan execution problems**.

---

## Why "Adding Perception" Didn't Help

### The Hypothesis (Previous Attempt)
"If we parse TextWorld observations into structured data (rooms, objects, connections), the cognitive agent will understand the world better."

### What Was Added
- `llm_parser.py`: LLM-based entity extraction
- `text_parser.py`: Regex parsing for observations
- Structured beliefs: `{'rooms': {}, 'objects': {}, 'inventory': []}`

### Why It Failed
**Perception ≠ Planning**
- Agent can now see "nest of spiders is on table in restroom"
- Agent still doesn't know "I should go east FIRST"
- Quest understanding is not a perception problem—it's a **reasoning problem**

**Analogy:** Giving the agent glasses (perception) when it needs a map (planning).

---

## Recommendations: Two Paths Forward

### Option A: Radical Simplification (Recommended)

**Approach:** Embrace that TextWorld is a **different problem domain**.

**Implementation:**
1. **Separate TextWorld Agent Class**
   - Don't force fit into `AgentRuntime`
   - Create `TextWorldQuestAgent` that uses simple LLM reasoning
   - Keep it under 200 lines

2. **Quest-First Architecture**
   ```python
   class TextWorldQuestAgent:
       def step(self, observation, quest, admissible_commands):
           # 1. Parse quest into sequence: [step1, step2, step3]
           # 2. Track progress: which steps are complete
           # 3. Execute current step
           # 4. Don't explore, don't optimize, just follow the plan
   ```

3. **Use LLM for Planning Only**
   - LLM decomposes quest → action sequence
   - Agent executes sequence mechanically
   - No EFE, no beliefs, no protocols

**Pros:**
- ✅ Will actually work (simple LLM already proves this)
- ✅ Honest about domain differences
- ✅ Can still showcase episodic memory (learning quest patterns)

**Cons:**
- ❌ Doesn't use full MacGyver MUD architecture
- ❌ Can't claim "universal" cognitive architecture

---

### Option B: Deep Integration (High Risk)

**Approach:** Make the architecture actually work for sequential tasks.

**Changes Required:**

1. **Add Quest Decomposition Module**
   ```python
   class QuestDecomposer:
       def decompose(self, quest: str) -> List[SubGoal]:
           # Parse "First A, then B, then C"
           # Return ordered list with completion tracking
   ```

2. **Hierarchical Control**
   - Top level: Quest decomposer (strategic)
   - Middle level: Plan executor (tactical)
   - Bottom level: EFE scoring (reactive)
   - **Strategic layer dominates tactical layer**

3. **Fix Loop Detection**
   ```python
   def calculate_cost(self, action: str) -> float:
       # Detect A → B → A patterns (not just A → A)
       if len(history) >= 3:
           if history[-3] == action and history[-2] != action:
               cost += 10.0  # Oscillation penalty
   ```

4. **Re-enable Critical States with Quest Context**
   ```python
   def apply_protocol(self, state: CriticalState, quest_progress: float):
       if state == DEADLOCK and quest_progress < 0.5:
           # Agent is stuck before completing quest
           return force_quest_action()
   ```

5. **Progress Tracking**
   - Track which sub-goals are complete
   - Boost scores for "next" sub-goal actions
   - Penalize scores for "already done" sub-goal actions

**Pros:**
- ✅ Demonstrates cognitive architecture can handle diverse domains
- ✅ Uses full feature set (planning, protocols, memory)
- ✅ More impressive research contribution

**Cons:**
- ❌ High complexity (requires major refactoring)
- ❌ May still underperform simple LLM
- ❌ Risk of over-engineering for one domain

**Estimated Effort:** 40-60 hours of development

---

## Detailed Recommendations

### Immediate Actions (Option A - Recommended)

1. **Accept Domain Mismatch**
   - Update documentation: "TextWorld is a planning domain, not a navigation domain"
   - Explain why architecture is NOT universal
   - Position as "honest limitations" (research integrity)

2. **Create Minimal TextWorld Agent**
   ```python
   # New file: environments/domain4_textworld/quest_agent.py
   class QuestAgent:
       def __init__(self):
           self.planner = LLMPlanner()
           self.quest_steps = []
           self.current_step = 0

       def step(self, obs, quest, commands):
           if not self.quest_steps:
               # First time: decompose quest
               self.quest_steps = self.planner.decompose_quest(quest)

           # Execute current step
           current_goal = self.quest_steps[self.current_step]
           action = self._match_command(current_goal, commands)

           # Advance if step succeeded
           if self._step_complete(action, obs):
               self.current_step += 1

           return action
   ```

3. **Validate It Works**
   - Run against same games as simple LLM
   - Target: 80%+ success rate
   - Prove quest decomposition + execution works

4. **Document Learnings**
   - "Why spatial cognitive architectures struggle with sequential tasks"
   - "When to use simple LLM vs cognitive architecture"
   - Honest assessment: MacGyver excels at navigation, fails at planning

### If Pursuing Option B (Deep Integration)

1. **Start with Quest Decomposer**
   - Temporal logic: "first X, then Y, finally Z"
   - Dependency tracking: "X must complete before Y"
   - Progress monitoring: "X done (✅), Y in progress (⏳), Z pending (⬜)"

2. **Hierarchical Scoring Override**
   ```python
   def select_action(self, commands, quest):
       # Layer 1: Quest decomposer (HIGHEST PRIORITY)
       if self.quest_progress.has_active_subgoal():
           quest_action = self.quest_progress.get_next_action(commands)
           if quest_action:
               return quest_action  # Override everything

       # Layer 2: Plan executor (MEDIUM PRIORITY)
       if self.current_plan:
           plan_action = self.current_plan.get_next_step()
           if plan_action in commands:
               return plan_action

       # Layer 3: Reactive EFE (FALLBACK)
       return self.score_and_select(commands)
   ```

3. **Fix Loop Detection**
   - Extend history window to 10+ steps
   - Detect A → B → A → B patterns (not just A → A)
   - Critical state: DEADLOCK triggers at 3 oscillations

4. **Test Incrementally**
   - Week 1: Quest decomposer + progress tracking
   - Week 2: Hierarchical control override
   - Week 3: Loop detection fixes
   - Week 4: Critical state re-integration

5. **Acceptance Criteria**
   - Success rate: 70%+ (comparable to simple LLM)
   - No loops: Max 2 oscillations before breaking
   - Quest adherence: 80%+ actions match quest steps

---

## What This Reveals About the Architecture

### Strengths (Validated)
✅ **Graph Navigation:** MacGyver MUD, Graph Labyrinth
✅ **Spatial Reasoning:** Shortest paths, room connectivity
✅ **Loop Breaking:** DEADLOCK protocol works when enabled
✅ **Uncertainty:** Bayesian belief updates, entropy monitoring

### Weaknesses (Newly Discovered)
❌ **Sequential Planning:** Cannot execute linear instruction sequences
❌ **Temporal Reasoning:** No "first, then, finally" logic
❌ **Goal Decomposition:** Cannot break quests into sub-tasks
❌ **Progress Tracking:** Doesn't remember completed sub-goals

### Design Conflicts (Critical Finding)
⚠️ **Exploration vs Exploitation:**
- MacGyver MUD rewards exploration (find key, discover rooms)
- TextWorld punishes exploration (every non-quest action wastes steps)

⚠️ **Reactive vs Planned:**
- Active Inference is reactive (score all actions, pick best)
- TextWorld needs commitment (execute plan, don't deviate)

⚠️ **Safety vs Progress:**
- Critical states enforce safety (break loops, prevent thrashing)
- But they conflict with quest execution (protocols override task-relevant actions)

**Conclusion:** The architecture embodies trade-offs that work for navigation, fail for planning.

---

## Comparison: What Cognitive Architecture Adds (or Doesn't)

### Simple LLM
```python
# 50 lines
action = ask_llm(observation, quest, commands)
```
- ✅ Works (100% success)
- ✅ Simple (50 lines)
- ❌ No learning
- ❌ No safety

### Cognitive Agent (Current)
```python
# 983 lines (cognitive_agent.py)
# + 1112 lines (agent_runtime.py)
# + 260 lines (scoring.py)
# + 154 lines (critical_state.py)
# = ~2500 lines total
action = agent.step(obs, feedback, reward, done, commands, quest)
```
- ❌ Doesn't work (0% success)
- ❌ Complex (2500 lines)
- ✅ Has learning (episodic memory, procedural memory)
- ✅ Has safety (critical states, circuit breakers)

**Current Value Proposition:** Negative. Adding 2500 lines breaks functionality.

**Desired Value Proposition:**
- Same or better success rate than simple LLM
- Plus learning (improve over episodes)
- Plus safety (handle edge cases)
- Plus introspection (explain decisions)

**Path Forward:** Either achieve desired value or admit domain mismatch.

---

## Test Plan for Validation

### Phase 1: Reproduce Failure (Complete)
- ✅ Run `compare_players.py`
- ✅ Confirm 0% cognitive success vs 100% LLM success
- ✅ Document loop behavior

### Phase 2: Implement Fix (Choose Option A or B)

**Option A Track:**
1. Create `quest_agent.py` (minimal implementation)
2. Test on 10 random games
3. Validate 80%+ success rate
4. Document "different tools for different jobs" philosophy

**Option B Track:**
1. Implement quest decomposer
2. Add hierarchical control layer
3. Fix loop detection (oscillation patterns)
4. Re-enable critical states with quest context
5. Test on 10 random games
6. Validate 70%+ success rate

### Phase 3: Red Team New Implementation
- Generate adversarial quests (long sequences, ambiguous wording)
- Test loop resistance (complementary actions)
- Verify learning (does performance improve over episodes?)
- Compare against simple LLM baseline

### Phase 4: Documentation
- Update README: Honest limitations
- Write "Domain-Specific Architecture Considerations" doc
- Publish findings: "When Cognitive Architectures Fail"

---

## Lessons Learned

### 1. **Perception ≠ Understanding**
Adding LLM-based parsing made the agent "see" the world better but didn't help it "think" about what to do. Quest execution requires reasoning, not just perception.

### 2. **Architecture Assumptions Matter**
The MacGyver MUD architecture assumes:
- Exploration is valuable (info gain is good)
- Multiple objectives compete (goal vs info vs cost)
- Safety matters more than efficiency (protocols can override)

TextWorld violates all three assumptions.

### 3. **Simple Often Wins**
For well-defined sequential tasks, a 50-line LLM prompt outperforms a 2500-line cognitive architecture. This is not a failure of engineering—it's a lesson in matching tools to problems.

### 4. **Disabling Safety Features Is a Red Flag**
When critical state protocols had to be disabled (line 947), that was a signal that the architecture was misaligned. We should have pivoted then instead of continuing.

### 5. **Honest Limitations Are Research Contributions**
Showing what a cognitive architecture CAN'T do is as valuable as showing what it CAN do. This project can contribute "A Case Study in Architecture-Domain Mismatch."

---

## Conclusion

The TextWorld integration has **conclusively failed**, but in an instructive way. The cognitive architecture that excels at spatial navigation, uncertainty management, and loop breaking is **fundamentally mismatched** with sequential task execution domains.

### Two Viable Paths:

1. **Accept Limitations (Option A):** Create separate minimal TextWorld agent, document why different domains need different architectures, position as research honesty.

2. **Deep Integration (Option B):** Invest 40-60 hours refactoring to add quest decomposition, hierarchical control, and progress tracking. Risk: May still underperform simple LLM.

### Recommendation: Option A

**Rationale:**
- Simple LLM already proves TextWorld is solvable simply
- Cognitive architecture adds value for **uncertain, exploratory** domains
- TextWorld is **certain, goal-directed** (different problem class)
- Honest limitations strengthen research credibility

### Next Steps:

1. **Immediate:** Create `quest_agent.py` (minimal implementation)
2. **Short-term:** Validate 80%+ success rate on test games
3. **Documentation:** Write "Architecture-Domain Fit" analysis
4. **Long-term:** Position project as "Cognitive Architecture for Graph Navigation" (honest scope)

---

**End of Red Team Analysis**

*"The best laid plans of mice and men often go awry." - Robert Burns*

*In this case, the plans went awry because we tried to use a navigation system to execute a recipe.*
