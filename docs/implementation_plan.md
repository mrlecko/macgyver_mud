# Implementation Plan: MacGyver Active Inference Demo

## Overview
Test-driven development approach for implementing the active inference demo.
Each phase includes implementation + tests before moving to next phase.

## Phases

### Phase 0: Setup 
- [x] Neo4j 4.4 running with APOC
- [x] requirements.txt with neo4j, rich
- [x] Makefile for Neo4j management
- [x] Project structure established

### Phase 1: Graph Initialization
**File**: `cypher_init.cypher`

**Tasks**:
1. Clear existing data
2. Create Agent node (MacGyverBot)
3. Create Place node (Room A)
4. Create Object nodes (Door, Window)
5. Create StateVar node (DoorLockState)
6. Create Belief node (initial p_unlocked=0.5)
7. Create Skill nodes (peek_door, try_door, go_window)
8. Create Observation nodes (obs_door_locked, obs_door_unlocked, obs_door_opened, obs_window_escape, obs_door_stuck)
9. Create relationships (LOCATED_IN, HAS_BELIEF, ABOUT, ACTS_ON)

**Validation**:
- Run cypher_init.cypher
- Query to verify all nodes exist
- Query to verify relationships

### Phase 2: Configuration
**File**: `config.py`

**Tasks**:
1. Neo4j connection settings (from env vars)
2. Scenario configuration
3. Scoring parameters (±, ², ³)
4. Reward/penalty constants
5. Belief update parameters

**Tests**: None (configuration only)

**Validation**:
- Import and print config values
- Verify env var reading

### Phase 3: Scoring Logic (TDD)
**File**: `scoring.py`
**Test File**: `test_scoring.py`

**TDD Sequence**:

1. **Test**: `test_entropy_boundary_conditions()`
   - entropy(0) = 0
   - entropy(1) = 0
   - entropy(0.5) > entropy(0.2)
   **Implement**: `entropy(p)`

2. **Test**: `test_expected_goal_value()`
   - peek_door returns 0
   - try_door increases with p_unlocked
   - go_window constant
   **Implement**: `expected_goal_value(skill_name, p_unlocked)`

3. **Test**: `test_expected_info_gain()`
   - peek_door returns entropy(p)
   - try_door returns 0
   - go_window returns 0
   **Implement**: `expected_info_gain(skill_name, p_unlocked)`

4. **Test**: `test_score_skill_behavior()`
   - At p=0.5, peek_door scores highest
   - At p=0.9, try_door scores highest
   - At p=0.1, go_window scores highest
   **Implement**: `score_skill(skill, p_unlocked, alpha, beta, gamma)`

**Validation**:
- Run: `python -m pytest test_scoring.py -v`
- All tests pass

### Phase 4: Graph Model (TDD)
**File**: `graph_model.py`
**Test File**: `test_graph_model.py`

**Prerequisites**:
- Neo4j must be running
- cypher_init.cypher must have been executed

**TDD Sequence**:

1. **Test**: `test_get_agent()`
   - Returns dict with id, name
   - Raises error if agent doesn't exist
   **Implement**: `get_agent(session, name)`

2. **Test**: `test_get_initial_belief()`
   - Returns float p_unlocked
   - Correct value from graph
   **Implement**: `get_initial_belief(session, agent_id, statevar_name)`

3. **Test**: `test_update_belief()`
   - Updates belief value in graph
   - Verify with query
   **Implement**: `update_belief(session, agent_id, statevar_name, new_value)`

4. **Test**: `test_get_skills()`
   - Returns list of skill dicts
   - Contains name, cost, kind
   **Implement**: `get_skills(session, agent_id)`

5. **Test**: `test_create_episode()`
   - Creates Episode node
   - Returns episode_id
   **Implement**: `create_episode(session, agent_id, door_state)`

6. **Test**: `test_log_step()`
   - Creates Step node
   - Links to Episode, Skill, Observation
   - Stores belief snapshots
   **Implement**: `log_step(session, episode_id, step_index, skill_name, obs_name, p_before, p_after)`

**Validation**:
- Run: `python -m pytest test_graph_model.py -v`
- All tests pass
- Inspect Neo4j to verify Episode/Step nodes

### Phase 5: Agent Runtime (TDD)
**File**: `agent_runtime.py`
**Test File**: `test_agent_runtime.py`

**TDD Sequence**:

1. **Test**: `test_select_skill()`
   - Selects highest scoring skill
   - Behavior changes with p_unlocked
   **Implement**: `AgentRuntime.select_skill(skills)`

2. **Test**: `test_simulate_peek_door_locked()`
   - Returns obs_door_locked
   - Updates p_unlocked to ~0.15
   - escaped = False
   **Implement**: Part of `simulate_skill(skill)`

3. **Test**: `test_simulate_peek_door_unlocked()`
   - Returns obs_door_unlocked
   - Updates p_unlocked to ~0.85
   - escaped = False
   **Implement**: Part of `simulate_skill(skill)`

4. **Test**: `test_simulate_try_door_unlocked()`
   - Returns obs_door_opened
   - escaped = True
   **Implement**: Part of `simulate_skill(skill)`

5. **Test**: `test_simulate_try_door_locked()`
   - Returns obs_door_stuck
   - Updates p_unlocked to ~0.10
   - escaped = False
   **Implement**: Part of `simulate_skill(skill)`

6. **Test**: `test_simulate_go_window()`
   - Returns obs_window_escape
   - escaped = True
   - p_unlocked unchanged
   **Implement**: Part of `simulate_skill(skill)`

7. **Test**: `test_run_episode_unlocked()`
   - Integration test
   - Escapes within max_steps
   - Creates Episode in graph
   **Implement**: `run_episode(max_steps)`

8. **Test**: `test_run_episode_locked()`
   - Integration test
   - Different behavior than unlocked
   - Creates Episode in graph
   **Implement**: Complete `run_episode(max_steps)`

**Validation**:
- Run: `python -m pytest test_agent_runtime.py -v`
- All tests pass
- Manual inspection of episodes in Neo4j

### Phase 6: Runner CLI
**File**: `runner.py`

**Tasks**:
1. Argument parsing (--door-state, --max-steps, --verbose)
2. Neo4j connection setup
3. Initialize AgentRuntime
4. Run episode
5. Print rich formatted trace
6. Summary statistics

**Tests**: `test_runner.py` (integration tests)

**Validation**:
- Run: `python runner.py --door-state unlocked`
- Run: `python runner.py --door-state locked`
- Verify different behaviors
- Check Neo4j for episodes

### Phase 7: Integration & Tuning
**Tasks**:
1. Run both scenarios multiple times
2. Verify expected behaviors:
   - Unlocked: peek ’ try_door (2 steps)
   - Locked: peek ’ go_window (2 steps)
3. Tune ±, ², ³ if needed
4. Tune belief update values if needed
5. Ensure info gain visibly influences decisions

**Validation**:
- Consistent, explainable behavior
- Clear demonstration of active inference
- Episodes logged correctly

### Phase 8: Demo Queries & Documentation
**Files**:
- `queries/demo_queries.cypher`
- Update `README.md`

**Tasks**:
1. Create showcase Cypher queries:
   - View all episodes
   - View episode traces
   - Skill usage statistics
   - Belief evolution over steps
2. Update README with:
   - Usage examples
   - Expected outputs
   - Neo4j browser instructions
3. Create DEMO.md with presentation notes

**Validation**:
- Run queries in Neo4j browser
- Beautiful visualizations
- Clear narrative

## Parameter Decisions (Based on Analysis)

### Belief Updates
```python
# Conservative updates to maintain uncertainty
obs_door_locked ’ p_unlocked = 0.15  (not 0.05)
obs_door_unlocked ’ p_unlocked = 0.85  (not 0.95)
obs_door_stuck ’ p_unlocked = 0.10  (new)
```

### Scoring Weights
```python
ALPHA = 1.0   # Goal value weight
BETA = 2.0    # Info gain weight (increased to make it matter)
GAMMA = 0.1   # Cost weight
```

### Rewards/Penalties
```python
REWARD_ESCAPE = 10.0
PENALTY_FAIL = 3.0   # Trying locked door
SLOW_PENALTY = 2.0   # Using window
```

### Skill Costs
```python
peek_door: 1.0
try_door: 1.5
go_window: 2.0
```

## Success Criteria

### Behavioral
- [ ] Scenario A (unlocked): Agent peeks, then tries door (d3 steps)
- [ ] Scenario B (locked): Agent peeks, then goes to window (d3 steps)
- [ ] Clear difference in behavior based on belief
- [ ] No hard-coded decision paths

### Technical
- [ ] All unit tests pass
- [ ] Episodes logged to Neo4j with correct structure
- [ ] Graph visualizable in Neo4j Browser
- [ ] Clean, readable code
- [ ] Rich formatted output

### Demo Quality
- [ ] 5-minute demo feasible
- [ ] Clear narrative ("peek when uncertain, exploit when confident")
- [ ] Obvious extension points
- [ ] Impressive Neo4j visualizations

## Testing Strategy

### Unit Tests
- `test_scoring.py`: Pure functions, no Neo4j needed
- `test_graph_model.py`: Requires running Neo4j, uses test fixtures
- `test_agent_runtime.py`: Requires Neo4j, may use mocks for some tests

### Integration Tests
- `test_runner.py`: End-to-end scenario tests
- Verify both scenarios produce expected traces

### Test Fixtures
- Use pytest fixtures for Neo4j sessions
- Reset graph state between tests (or use transactions)
- Mock time/randomness if needed

### Test Coverage Goal
- Aim for >80% coverage on scoring, graph_model, agent_runtime
- runner.py can have lower coverage (mostly integration)

## Implementation Order (TDD Workflow)

For each component:
1. Write failing test
2. Implement minimal code to pass
3. Refactor if needed
4. Write next test
5. Repeat

Between phases:
1. Validate with manual testing
2. Check Neo4j state
3. Review code quality
4. Document any decisions

## Timeline Estimate

- Phase 1: 15 min (Graph init)
- Phase 2: 10 min (Config)
- Phase 3: 30 min (Scoring + tests)
- Phase 4: 45 min (Graph model + tests)
- Phase 5: 60 min (Agent runtime + tests)
- Phase 6: 30 min (Runner CLI)
- Phase 7: 30 min (Tuning)
- Phase 8: 20 min (Docs)

**Total**: ~3.5-4 hours

## Notes

- Use `rich` for pretty output (tables, colors)
- Use pytest for all tests
- Keep functions small and focused
- Document key decisions inline
- Add TODO comments for future extensions
- Commit after each phase (if using git)
