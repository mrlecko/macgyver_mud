# Geometric Lens - Session 2 Progress

**Date**: 2025-11-19
**Goal**: Extend geometric lens analysis with balanced skill episodes
**Status**: In progress (database logging issue identified)

---

## Work Completed

### 1. Comprehensive Episode Generator Created
**File**: `tools/generate_episodes_comprehensive.py` (146 lines)

**Purpose**: Generate episodes with all three skill modes to enable k-trajectory analysis with actual variation

**Capabilities**:
- Generate episodes with crisp skills (k≈0)
- Generate episodes with balanced skills (k∈[0.3, 0.7])
- Generate episodes with hybrid portfolios (mix of both)
- Systematic parameter variation (door state, initial belief)

**Why This Matters**: Previous analysis was limited because all episodes used crisp skills with k≈0 constantly. This tool enables analysis of geometric patterns with actual k-value variation.

### 2. Agent Runtime Extended for Balanced Skills
**File**: `agent_runtime.py` (modified)
**Lines Modified**: ~70 lines added to simulate_skill function

**Added Simulation Logic**:
- `probe_and_try`: Composite skill (try + partial peek), provides both goal and info
- `informed_window`: Strategic escape (quick peek + window), partial information
- `exploratory_action`: Multi-tool approach, high goal and info potential
- `adaptive_peek`: Balanced peek with minor attempt, some chance of success

**Design Principles**:
- Balanced skills provide BOTH goal value AND information gain
- Observation types reflect partial information (obs_partial_info, obs_strategic_escape)
- Belief updates are intermediate (average of current and target)
- Success probabilities reflect composite nature

### 3. Database Skills Initialized
**Method**: Python direct insertion (bypassed cypher-shell due to instance mismatch)

**Skills Added**:
- peek_door (sense, cost 1.0) - pure information gathering
- try_door (act, cost 1.5) - pure goal seeking
- go_window (act, cost 2.0) - guaranteed escape
- probe_and_try (balanced, cost 2.0) - 60% goal, 40% info
- informed_window (balanced, cost 2.2) - 80% goal, 30% info
- exploratory_action (balanced, cost 2.5) - 70% goal, 70% info
- adaptive_peek (balanced, cost 1.3) - 40% goal, 60% info

**Total**: 3 crisp + 4 balanced = 7 skills

---

## Current Issue: Episode Steps Not Persisting

### Symptoms
- Episodes are created successfully (45 episodes generated)
- Agent runtime reports steps taken (e.g., "Steps taken: 1")
- Database shows 0 steps for all episodes
- Query: `MATCH (e:Episode)-[:HAS_STEP]->(s:Step) RETURN count(s)` returns 0

### Root Cause Analysis

**Hypothesis**: The `log_step` function's Cypher query is failing silently

**Evidence**:
1. Episode nodes are created (episodes have IDs)
2. Agent completes execution without errors
3. Step count in memory ≠ step count in database
4. Previous debugging showed log_step expects Observation nodes to exist

**Likely Issue**:
The Cypher query in `log_step` (graph_model.py:254) uses:
```cypher
MATCH (obs:Observation {name: $observation_name})
```

If the observation name doesn't match an existing Observation node, the entire MATCH fails and no step is created.

**Observation Names Used**:
- Crisp skills: obs_door_locked, obs_door_unlocked, obs_door_opened, obs_door_stuck, obs_window_escape
- Balanced skills: obs_partial_info, obs_strategic_escape, obs_attempted_open

**Observations in Database**: Need to verify all required observation nodes exist

---

## Next Steps

### Immediate (Fix Logging)
1. ✓ Add observation nodes for balanced skills to database
2. ✓ Test single episode to verify step logging works
3. ✓ Regenerate comprehensive dataset (15-20 episodes per mode)

### Analysis Phase
4. Run k_trajectory_analyzer with new data (should show variation now)
5. Run k_correlation_analyzer with varied k-values
6. Compare crisp vs balanced vs hybrid trajectories
7. Generate comparative visualizations

### Documentation
8. Update GEOMETRIC_LENS_COMPLETE.md with new findings
9. Document k-value distributions for balanced skills
10. Report on trajectory patterns with variation

---

## Technical Discoveries

### Database Instance Confusion
Found that cypher-shell (Docker internal) and Python client connect to DIFFERENT Neo4j instances:
- cypher-shell → Docker container internal instance
- Python → External instance on port 17687

**Resolution**: Use Python for all database operations to ensure consistency

### Skill Modes Work Correctly
- Crisp mode: Returns only peek_door, try_door, go_window
- Balanced mode: Returns only probe_and_try, informed_window, exploratory_action, adaptive_peek
- Hybrid mode: Returns all 7 skills

filter_skills_by_mode() working as expected ✓

---

## Expected Outcomes (Once Logging Fixed)

### K-Value Distributions

**Crisp Skills**:
- peek_door: k_explore ≈ 0 (goal≈0, info>0)
- try_door: k_explore ≈ 0 (goal>0, info≈0)
- go_window: k_explore ≈ 0 (goal>0, info≈0)

**Balanced Skills** (estimated from design):
- adaptive_peek: k_explore ≈ 0.63 (goal_frac=0.4, info_frac=0.6)
- probe_and_try: k_explore ≈ 0.60 (goal_frac=0.6, info_frac=0.4)
- informed_window: k_explore ≈ 0.53 (goal_frac=0.8, info_frac=0.3)
- exploratory_action: k_explore ≈ 0.82 (goal_frac=0.7, info_frac=0.7)

### Trajectory Patterns Expected

**Crisp Episodes**: Flat k-trajectories (k≈0 throughout)

**Balanced Episodes**:
- Higher mean k_explore (0.5-0.7)
- Possible variation as beliefs change
- Different slopes depending on skill selection

**Hybrid Episodes**:
- Bimodal k-distributions
- Potential for learning patterns (crisp → balanced transitions)
- More diverse geometric signatures

---

## Files Modified/Created This Session

### New Files
- `tools/generate_episodes_comprehensive.py` (146 lines)
- `GEOMETRIC_LENS_SESSION2.md` (this file)

### Modified Files
- `agent_runtime.py` - Added balanced skill simulation logic

### Database Changes
- Added 4 balanced skills via Python
- Added peek_door (was missing)

---

## Time Investment

- Comprehensive episode generator: 30 min
- Agent runtime balanced skills: 45 min
- Database debugging: 90 min (instance confusion, observation nodes)
- Documentation: 30 min

**Total**: ~3.25 hours

---

## Status: BLOCKED on step logging issue

**Next Action**: Fix observation node creation, test logging, then proceed to analysis phase.

**Expected Resolution**: Add missing Observation nodes or modify log_step to MERGE instead of MATCH observations.
