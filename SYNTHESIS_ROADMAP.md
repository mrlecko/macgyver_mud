# Synthesis Implementation Roadmap

**Goal:** Unify Quest Agent effectiveness with Cognitive Agent sophistication

**Three Approaches:** Minimum Viable → Progressive Enhancement → Complete Rebuild

---

## Option A: Minimum Viable Synthesis (RECOMMENDED)

**Time:** 12-16 hours
**Risk:** Low
**Value:** High (validates concept)

### What It Does
Adds hierarchical scoring to existing Cognitive Agent without major refactoring.

### Changes Required

#### 1. Add Quest Decomposition to Cognitive Agent (4 hours)

**File:** `cognitive_agent.py`

```python
class TextWorldCognitiveAgent:
    def __init__(self, session, verbose=True):
        # ... existing init ...

        # NEW: Add quest decomposer and progress tracker
        from environments.domain4_textworld.quest_decomposer import QuestDecomposer
        self.quest_decomposer = QuestDecomposer()
        self.subgoals = []  # List of subgoal strings
        self.current_subgoal_index = 0

    def reset(self, quest: str):
        """NEW: Decompose quest on reset."""
        self.subgoals = self.quest_decomposer.decompose(quest)
        self.current_subgoal_index = 0
        self.last_quest = quest

        if self.verbose:
            print("📋 Quest decomposed:")
            for i, sg in enumerate(self.subgoals, 1):
                print(f"   {i}. {sg}")

    def step(self, observation, feedback, reward, done, admissible_commands, quest):
        # ... existing belief updates ...

        # NEW: Update progress based on reward
        if reward > 0 and self.current_subgoal_index < len(self.subgoals) - 1:
            self.current_subgoal_index += 1
            if self.verbose:
                print(f"   ✅ Subgoal {self.current_subgoal_index} complete!")

        # Get current subgoal
        current_subgoal = self.subgoals[self.current_subgoal_index] if self.current_subgoal_index < len(self.subgoals) else None

        # ... existing action selection ...
        # PASS current_subgoal to scoring (see next section)
```

#### 2. Make Goal Scoring Subgoal-Aware (3 hours)

**File:** `cognitive_agent.py`, function `calculate_goal_value`

```python
def calculate_goal_value(self, action: str, current_subgoal: str = None) -> float:
    """
    Calculate goal value (pragmatic value).

    NOW HIERARCHICAL:
    1. Current subgoal match (HIGHEST priority)
    2. Overall quest match (MEDIUM priority)
    3. Generic heuristics (LOW priority)
    """
    value = 0.5  # Base

    # PRIORITY 1: Current subgoal match (NEW)
    if current_subgoal:
        subgoal_tokens = set(current_subgoal.lower().split())
        action_tokens = set(action.lower().split())
        stopwords = {'the', 'a', 'an', 'from', 'into', 'on', 'in', 'to', 'of'}

        subgoal_tokens_clean = subgoal_tokens - stopwords
        action_tokens_clean = action_tokens - stopwords

        overlap = len(subgoal_tokens_clean & action_tokens_clean)

        if overlap > 0:
            # HUGE bonus for subgoal match
            value += 15.0 * (overlap / len(subgoal_tokens_clean))

    # PRIORITY 2: Overall quest match (EXISTING CODE, but reduce weight)
    if hasattr(self, 'last_quest') and self.last_quest:
        quest_lower = self.last_quest.lower()
        action_lower = action.lower()

        action_words = set(action_lower.split())
        quest_words = set(quest_lower.split())

        common_words = action_words & quest_words
        stopwords = {'the', 'a', 'an', 'from', 'into', 'on', 'in', 'to', 'of'}
        meaningful_common = common_words - stopwords

        if meaningful_common:
            # MEDIUM bonus (reduced from 10.0)
            value += 5.0 * len(meaningful_common)

    # PRIORITY 3: Generic heuristics (EXISTING CODE)
    if action.startswith('take ') or action.startswith('get '):
        value += 1.0  # Small bonus

    if action.startswith('open '):
        value += 0.8

    if action.startswith('eat '):
        value += 0.5

    return value
```

#### 3. Update Action Selection Call Site (1 hour)

**File:** `cognitive_agent.py`, function `select_action`

```python
def select_action(self, admissible_commands: List[str], quest: Optional[Dict] = None) -> str:
    # ... existing validation ...

    # Get current subgoal
    current_subgoal = self.subgoals[self.current_subgoal_index] if self.current_subgoal_index < len(self.subgoals) else None

    # Score all actions
    scored_actions = []
    for action in valid_commands:
        try:
            score = self.score_action(action, self.beliefs, quest, current_subgoal)  # NEW parameter
            scored_actions.append((score, action))

            if self.verbose and len(valid_commands) <= 10:
                print(f"      {score:6.2f} → {action}")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Scoring error for '{action}': {e}")
            continue

    # ... rest of existing code ...
```

#### 4. Update `score_action` Signature (1 hour)

**File:** `cognitive_agent.py`, function `score_action`

```python
def score_action(self, action: str, beliefs: Dict, quest: Optional[Dict] = None,
                current_subgoal: str = None) -> float:  # NEW parameter
    """
    Score an action using Active Inference EFE.

    NOW HIERARCHICAL: current_subgoal provides context for goal_value.
    """
    # ... existing coefficients ...

    goal_val = self.calculate_goal_value(action, current_subgoal)  # PASS subgoal
    entropy = self.calculate_entropy(action)
    cost = self.calculate_cost(action)
    memory_bonus = self.calculate_memory_bonus(action)
    plan_bonus = self.calculate_plan_bonus(action)

    efe = (alpha * goal_val) + (beta * entropy) - (gamma * cost) + (delta * memory_bonus) + (epsilon * plan_bonus)

    return efe
```

### Testing Plan

```bash
# 1. Test on TextWorld (should improve from 0% to 80%+)
python3 environments/domain4_textworld/compare_all_agents.py

# 2. Test on MacGyver MUD (should maintain 96%)
python3 validation/comparative_stress_test.py

# 3. Test on Graph Labyrinth (should maintain excellent)
pytest tests/test_graph_labyrinth.py -v
```

### Expected Results

| Test | Before | After (Option A) |
|------|--------|------------------|
| TextWorld | 0% | 80-90% |
| MacGyver MUD | 96% | 96% (maintained) |
| Graph Labyrinth | Excellent | Excellent (maintained) |

### Why This Works

- **Small change:** Only modifies goal scoring (5 functions)
- **Low risk:** Doesn't touch memory, geometric lens, critical states
- **Validates concept:** Proves hierarchical scoring is the key
- **Maintains existing:** MacGyver/Labyrinth should work unchanged

---

## Option B: Progressive Enhancement

**Time:** 30-42 hours (in phases)
**Risk:** Medium
**Value:** Very High (full research demonstration)

### Phase 1: Core Synthesis (12 hours)
Implement full hierarchical agent with all three layers

### Phase 2: Add Learning (8 hours)
Integrate procedural + episodic memory for quest contexts

### Phase 3: Add Geometric Analysis (6 hours)
Apply Silver Gauge to quest decisions, log to Neo4j

### Phase 4: Critical States (6 hours)
Make protocols quest-aware (don't interfere with subgoal progress)

### Phase 5: Validation (8 hours)
Test across all domains, compare to baselines, document results

**See `COGNITIVE_SYNTHESIS_ANALYSIS.md` for detailed implementation.**

---

## Option C: Document & Defer

**Time:** 2-4 hours
**Risk:** None
**Value:** Medium (research documentation without implementation)

### Deliverables

1. **Paper/Report:** "Hierarchical Application of Cognitive Principles"
   - Problem: Flat architecture fails on sequential tasks
   - Solution: Strategic/Tactical/Reactive layers
   - Evidence: Quest Agent success shows hierarchical reasoning works
   - Future Work: Full synthesis implementation

2. **README Update:**
   - Honest about domain boundaries
   - Explain Quest Agent as proof-of-concept for hierarchy
   - Position as "research in progress"

3. **Code Comments:**
   - Annotate cognitive_agent.py with "TODO: Add hierarchical scoring"
   - Reference synthesis documents

**Why This Might Be Appropriate:**
- If time-constrained
- If want to publish current work first
- If want external validation before major refactoring

---

## Recommendation Matrix

| Your Priority | Recommended Option | Why |
|---------------|-------------------|-----|
| **Quick fix for TextWorld** | Option A | Minimal changes, proves concept |
| **Complete research demo** | Option B | Shows all innovations working together |
| **Publish current state** | Option C | Document lessons, defer implementation |
| **Uncertain** | Option A → assess → Option B or C | Low-risk start, decision point after |

---

## Implementation Steps (Option A - Detailed)

### Day 1: Decomposition (4 hours)

**Morning (2 hours):**
```bash
# 1. Copy QuestDecomposer into cognitive_agent.py imports
# 2. Add decomposer to __init__
# 3. Add reset() method that calls decomposer
# 4. Test decomposition works

python3 -c "
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:17687', auth=('neo4j', 'macgyver_pass'))
session = driver.session()
agent = TextWorldCognitiveAgent(session, verbose=True)

quest = 'First, move east. Then, take nest. Finally, place nest in dresser.'
agent.reset(quest)

print('Subgoals:', agent.subgoals)
print('Current index:', agent.current_subgoal_index)
"
```

**Afternoon (2 hours):**
```bash
# 5. Add progress tracking (advance on reward)
# 6. Test progress updates correctly
# 7. Handle edge cases (empty quest, single step, etc.)
```

### Day 2: Goal Scoring (4 hours)

**Morning (2 hours):**
```bash
# 1. Modify calculate_goal_value to accept current_subgoal
# 2. Add hierarchical matching logic
# 3. Test goal value increases for subgoal-matching actions
```

**Afternoon (2 hours):**
```bash
# 4. Update score_action signature
# 5. Update select_action call site
# 6. Test full scoring pipeline
```

### Day 3: Integration & Testing (4 hours)

**Morning (2 hours):**
```bash
# 1. Create updated compare_all_agents.py that uses reset()
# 2. Run on TextWorld game
# 3. Debug any issues
```

**Afternoon (2 hours):**
```bash
# 4. Test on MacGyver MUD (validate no regression)
# 5. Test on Graph Labyrinth (validate no regression)
# 6. Document results
```

### Day 4: Validation & Documentation (4 hours)

**Morning (2 hours):**
```bash
# 1. Run 10 TextWorld games
# 2. Calculate success rate
# 3. Compare to Quest Agent and Simple LLM
```

**Afternoon (2 hours):**
```bash
# 4. Write results document
# 5. Update README
# 6. Create synthesis demo script
```

---

## Success Criteria

### Option A Success
- ✅ TextWorld success rate: 70%+ (vs 0% before)
- ✅ MacGyver MUD: Maintains 95%+ success
- ✅ Graph Labyrinth: All tests passing
- ✅ Code changes: < 200 lines modified
- ✅ No breaking changes to existing tests

### Option B Success
- ✅ All Option A criteria
- ✅ Demonstrates all 6 innovations (EFE, memory, geometric lens, critical states, decomposition, progress)
- ✅ Learning over episodes (episode 10 > episode 1)
- ✅ Rich introspection (can explain decisions)
- ✅ Works across all 3 domains

### Option C Success
- ✅ Clear documentation of synthesis approach
- ✅ Honest assessment of limitations
- ✅ Roadmap for future implementation
- ✅ Research narrative explains lessons learned

---

## Risk Mitigation

### Risk: Option A Breaks MacGyver Performance
**Mitigation:**
- Test on MacGyver after each change
- Keep subgoal scoring conditional: `if current_subgoal: ... else: old_logic`
- Have rollback plan (git branch)

### Risk: Option A Doesn't Improve TextWorld Enough
**Mitigation:**
- Start with simplified decomposer (regex only)
- Increase subgoal matching bonus incrementally (test 10.0, 15.0, 20.0)
- Add progress tracking heuristics if needed

### Risk: Option B Takes Too Long
**Mitigation:**
- Break into weekly sprints
- Validate each phase before continuing
- Have "good enough" stopping points

---

## Next Steps

**Immediate:**
1. Choose option (A, B, or C)
2. Create git branch for changes
3. Set aside implementation time

**If Option A:**
1. Start with Day 1 (decomposition)
2. Validate at each step
3. Assess after 16 hours: continue to Option B or document with Option C?

**If Option B:**
1. Read `COGNITIVE_SYNTHESIS_ANALYSIS.md` in detail
2. Create implementation plan
3. Start with Phase 1 (core synthesis)

**If Option C:**
1. Write research document
2. Update README with honest assessment
3. Reference synthesis documents for future work

---

## Closing Thoughts

The Quest Agent vs Cognitive Agent comparison revealed something valuable: **your cognitive architecture is sound, it just needs hierarchical application**.

This isn't a failure—it's a research insight worth documenting and implementing.

**Option A proves the concept in 12-16 hours.**
**Option B demonstrates the complete vision in 30-42 hours.**
**Option C documents the lessons for future work.**

All three are valid. Choose based on your priorities. 🧠⚡
