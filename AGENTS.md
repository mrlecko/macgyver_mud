# Repository Guidelines

## Project Structure & Module Organization
- Core loop: `agent_runtime.py`, `critical_state.py`, `scoring*.py`, and `graph_model.py` drive decisions, stability, and Neo4j I/O.
- Domain modules: `control/` (Lyapunov), `memory/` (episodic/procedural), `perception/`, `planning/`, `cognitive_agent/`, helpers in `macgyver_utils.py`.
- Support: `config.py` (flags/env), `runner.py` (CLI entry), `scripts/` (Neo4j helpers), `validation/` + `experiments/` (stress + demos), `docs/`, and `tests/`.

## Build, Test, and Development Commands
- `make bootstrap` – Install deps, start Neo4j demo container, run full suite.
- `make dev-init` – Start Neo4j and print connection info; `make neo4j-start|stop|status` to manage it.
- `make test` – Fast core tests; `make test-all` runs all unit/integration; `make test-full` adds long validations.
- `python runner.py --door-state locked --skill-mode balanced` – Run an episode with explicit scenario flags.
- Visual/behavior demos: `make demo`, `make demo-critical`, `make visualize-silver`, `make validate-silver`.

## Coding Style & Naming Conventions
- Python 3.11, 4-space indent, type hints where helpful, concise docstrings for public surfaces.
- Use f-strings, deterministic seeds, and pure helpers instead of ad hoc globals; keep DB access in `graph_model.py`.
- Configuration belongs in `config.py` or env (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `REWARD_MODE`, feature flags like `ENABLE_CRITICAL_STATE_PROTOCOLS`); avoid hard-coded creds.
- Naming: snake_case for functions/vars, PascalCase for classes, SCREAMING_SNAKE_CASE for constants, `test_*` files/functions mirroring modules.

## Testing Guidelines
- Requires a running Neo4j (`make neo4j-start`) with demo credentials unless overridden; discovery limited to `tests/` via `pytest.ini`.
- Add tests next to new modules; unit tests can stub Neo4j calls, integration tests may seed via `balanced_skills_init.cypher` or test fixtures.
- Keep coverage near the current bar (~99%). Gate long validations so `make test` stays quick.

## Commit & Pull Request Guidelines
- Match history style: short lowercase scopes with colons (e.g., `fixing: deadlock detection`, `docs: move visuals`), imperative voice.
- PRs should note behavior changes, risks, and toggles touched (`ENABLE_GEOMETRIC_CONTROLLER`, `ENABLE_EPISODIC_MEMORY`, etc.), plus linked issues and visuals when outputs change.
- Run `make test` before pushing; use `make test-all` if touching scoring, memory, or critical-state logic.

## Security & Configuration Tips
- Do not commit real Neo4j credentials; use env vars or local overrides. Validate new knobs with `config.validate_config()` when adding flags.
- Containers run under `scripts/dev_neo4j_demo.sh`; clean with `make neo4j-stop` and avoid manual edits to `.neo4j44/` unless instructed.
