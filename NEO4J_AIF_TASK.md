# Task: Neo4j-Backed Active Inference Runtime

Goal: Extend the new `agent_runtime_active.py` to load/run against Neo4j (skills/observations/state) and add DB-backed tests. This keeps the heuristic path intact and selectable via config/CLI.

## Scope
- Wire the Active Inference runtime to consume Neo4j data (skills, observations, state priors) instead of defaults.
- Persist episodes/steps using the existing graph schema (Episode, Step).
- Add a minimal integration test that runs a short Active Inference trajectory using Neo4j data (can reuse `cypher_init.cypher`).

## Implementation Steps
1) **Model loading from Neo4j (production code)**
   - In `agent_runtime_active.build_model_from_graph(session)`, replace the heuristic likelihood scaffolding with reads from Neo4j:
     - Actions: `MATCH (s:Skill) RETURN s.name, s.kind, s.cost`.
     - Observations: `MATCH (o:Observation) RETURN o.name`.
     - State domain: `MATCH (s:StateVar {name: $STATE_VAR_NAME}) RETURN s.domain AS domain`.
   - Define likelihoods (A) and transitions (B):
     - For each action/observation/state, either read stored params (if present) or derive from the existing semantics:
       - `peek_door` → deterministic observation of lock state.
       - `try_door` → success conditioned on unlocked state; failure on locked.
       - `go_window` → deterministic escape observation.
     - Keep state static for now (B = identity per action).
   - Preferences (C):
     - Prefer escape/opened observations highest; window escape next; neutral/negative for locked/stuck.
     - Store as log-preferences; normalize with softmax.
   - Prior (D):
     - Read from Belief node if present (`Belief.p_unlocked`); fallback to uniform.
   - Keep a safe fallback to `build_door_model_defaults()` if required entities are missing.

2) **Runtime execution against Neo4j**
   - Use the existing `start_episode/log_decision/complete_episode` hooks with the agent id fetched from graph (`get_agent`).
   - Ensure `log_decision` maps fields to the current Step schema (skill_name, observation, p_before, p_after, efe).
   - Keep MAP observation sampling for test determinism; optionally make sampling stochastic via a flag.

3) **Integration test (DB-backed)**
   - Add `tests/test_active_inference_runtime_integration.py`:
     - Mark it to require Neo4j (no `SKIP_NEO4J_TESTS`).
     - Use `neo4j_session` fixture to ensure `cypher_init.cypher` is loaded.
     - Build model via `build_model_from_graph(session)`.
     - Run `ActiveInferenceRuntime.run_episode` with `door_state="unlocked"` and assert:
       - First action is `peek_door` (epistemic from uniform prior).
       - `escaped` is True within `max_steps`.
       - Steps are logged in Neo4j (Episode + Step count > 0).
   - Optional: add a locked-case to verify window fallback or stuck observation handling.

4) **Config/CLI toggle (already present)**
   - `config.AGENT_RUNTIME_MODE` and `--runtime` flag are in place; ensure docs mention Neo4j requirement for active runtime when using graph-backed model.

5) **Docs**
   - Add a short README note pointing to this task file and indicating: “Active runtime requires Neo4j running on `NEO4J_URI` with `cypher_init.cypher` loaded.”

## Permissions / How to enable Neo4j access in Codex CLI
If the sandbox blocks sockets, restart the Codex session with:
- Filesystem: `workspace-write` or `danger-full-access` (preferred for DB work).
- Network: allow outbound localhost sockets (remove `restricted`/`no network`).
- Approval policy: allow escalated commands for `docker` and local sockets.
Then:
1) Start Neo4j: `make neo4j-start` (requires Docker).
2) Verify: `make neo4j-status` and `docker logs neo4j44 | tail`.
3) Run tests: `python -m pytest tests/test_active_inference_runtime.py tests/test_active_inference_runtime_integration.py` or `make test`/`make test-all`.

If Docker remains blocked, run Neo4j externally and set env:
```
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
```
and rerun the tests.
