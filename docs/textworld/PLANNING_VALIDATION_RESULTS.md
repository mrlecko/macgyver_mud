# Planning Validation Results

**Date:** 2025-11-23
**Test:** Step 1 validation - Planning system in real episodes
**Episodes Run:** 1 complete, 1 partial

---

## Key Findings

### ✅ **PLANNING WORKS!**

**Evidence:**
- Plan was successfully generated at step 3
- LLM integration functional (`llm` CLI with schema validation)
- Goal: "Find key and unlock the door"
- Strategy: "systematically examining the attic for the key..."
- 3 steps generated with action patterns

### ❌ **PLAN ADHERENCE IS VERY LOW**

**Critical Issue:**
- **Plan Adherence: 6%** (3 actions on plan, 45 off plan)
- Agent generated plan but mostly ignored it
- Actions diverged from plan immediately after generation

### 🔍 **Root Cause Analysis**

**Why low adherence?**

1. **Plan bonus too weak:**
   - ε = 2.0 (plan weight coefficient)
   - Bonus: +10-12 for matching actions
   - Other EFE terms likely overwhelming plan bonus

2. **Goal inference mismatched actual quest:**
   - Inferred goal: "Find key and unlock the door"
   - Actual quest: "Move east, recover nest of spiders from table, place in dresser"
   - Plan was for the wrong goal!

3. **Admissible commands issue:**
   - "Invalid commands input, using fallback" warnings
   - Fallback commands may not match plan patterns well

4. **Critical state override:**
   - DEADLOCK triggered at step 4
   - ESCALATION at step 50
   - Protocols may be overriding plan-directed actions

---

## Detailed Metrics

### Episode 1:
- **Result:** Failed (timeout at 50 steps)
- **Total Reward:** +0.0
- **Plan Generated:** ✅ Yes
- **Plan Adherence:** 6% (3/48 actions)
- **Critical States:**
  - DEADLOCK (step 4)
  - ESCALATION (step 50)
- **Behavior:** Agent mostly did "look" repeatedly

### Plan Quality:
```
Goal: Find key and unlock the door

Strategy: This approach works because the agent will first search the room
         for any objects that might contain the key, then take the key, and
         finally attempt to unlock the door with it.

Steps:
1. Examine the attic for any potential hiding spots (pattern: 'examine')
2. Take the key if found (pattern: 'take key')
3. Unlock the door with the key (pattern: 'unlock door')

Confidence: 0.80
```

**Assessment:** Plan structure is good, but goal is wrong for this quest.

---

## Validation Checklist

| Criterion | Status | Notes |
|-----------|--------|-------|
| Goal inference triggers | ✅ Yes | Triggered at step 3 |
| Plans are generated | ✅ Yes | LLM worked, schema validated |
| Plans have 3-7 steps | ✅ Yes | Had 3 steps |
| Agent follows plans | ❌ NO | Only 6% adherence |
| Plan bonus influences EFE | ⚠️ Weak | Present but insufficient |
| Plan progress tracked | ✅ Yes | "67% complete" visible |
| Critical states handled | ✅ Yes | DEADLOCK, ESCALATION triggered |

---

## Issues Identified

### 1. Goal Inference (HIGH PRIORITY)

**Problem:** Goal inference uses naive heuristics:
```python
if 'locked' in obs_text and 'chest' in obs_text:
    return "Find key and unlock the chest"
```

**Issue:** Quest was "recover nest of spiders" but inferred "find key"

**Fix Options:**
- A. Extract goal from quest text properly
- B. Parse actual objective from game state
- C. Use LLM to infer goal from observation + quest

**Recommended:** Option B - parse quest from TextWorld game state

### 2. Plan Bonus Weight (MEDIUM PRIORITY)

**Problem:** ε = 2.0 is too weak vs. other EFE terms

**Evidence:** 6% adherence means plan bonus is being overwhelmed

**Fix:** Increase ε from 2.0 to 5.0 or higher

**Test:** Run episode with ε=5.0, measure adherence

### 3. Admissible Commands (LOW PRIORITY)

**Problem:** "Invalid commands input, using fallback" warnings

**Issue:** Fallback commands may not have the actions plan expects

**Fix:** Properly extract admissible_commands from TextWorld game state

**Status:** Partially fixed (defensive checks added)

###4. Critical State Interference (LOW PRIORITY)

**Problem:** DEADLOCK triggered at step 4, may be too aggressive

**Evidence:** Agent got stuck in "look" loop, DEADLOCK fired

**Consider:** Tuning DEADLOCK threshold (currently triggers on visit_count)

---

## Recommendations

### Immediate Fixes (Before implementing memory):

1. **Fix goal inference** (30 min)
   - Extract actual quest objective from game state
   - Test that inferred goal matches quest

2. **Increase plan bonus** (5 min)
   - Change ε from 2.0 to 5.0
   - Re-run validation, measure adherence

3. **Fix admissible commands** (15 min)
   - Properly extract from TextWorld API
   - Remove fallback warnings

### Expected Improvement:

With fixes:
- Plan adherence: 6% → 40-60%
- Agent follows plans more consistently
- Better goal-directed behavior

### Then Proceed To:

Step 2: Implement memory system (as planned)

---

## Positive Takeaways

✅ **Planning infrastructure works:**
- LLM integration functional
- Schema validation working
- Plan generation successful
- Progress tracking operational

✅ **Agent is robust:**
- Critical states trigger appropriately
- Defensive error handling prevents crashes
- Exploration/exploitation balance functional

✅ **We have data:**
- Know exactly what's broken (goal inference, weak bonus)
- Clear path to fixes
- Validation approach works well

---

## Bottom Line

**Planning system is BUILT and FUNCTIONAL but needs TUNING:**

1. Goal inference is broken (infers wrong goal)
2. Plan bonus is too weak (6% adherence)
3. With fixes, should see 40-60% adherence

**This is GOOD progress:** We validated the system works but identified tuning needs before building more.

**Next Action:** Quick fixes (1 hour) then proceed to memory implementation.
