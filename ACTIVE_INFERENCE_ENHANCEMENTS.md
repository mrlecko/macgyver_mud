# Active Inference Enhancements (Session Log)

This document summarizes the Active Inference additions, behavior changes, and tests introduced during this session.

## What was added
- **Graph-backed generative model**: `build_model_from_graph` now filters skills/observations from Neo4j, derives likelihoods/transitions, carries action costs/kinds, and handles missing state domains with safe fallbacks. Action costs feed into EFE.
- **Stochastic sampling + learning hooks**: Active Inference runtime supports stochastic observation sampling and simple Dirichlet updates for A/B (`update_likelihoods`, `update_transitions`) with normalization.
- **EFE scoring improvements**: Epistemic value scaling (`info_weight`), entropy-scaled action cost, and a sense bonus under uncertainty; extra penalty for costly/act actions to preserve epistemic-first behavior.
- **Persistence**: `save_model_to_graph` / `load_model_from_graph` store/load the generative model as a single `GenerativeModel` node (arrays serialized as JSON).
- **Policy search control**: `select_action` supports `max_policies` to cap brute-force search at higher depths.
- **Beam search**: Optional beam search (`evaluate_policies_beam`) to prune policy enumeration; avoids full combinatorial blow-up.
- **Schema versioning & domain fallback**: Persisted models carry a schema version; builder falls back to persisted states when `StateVar.domain` is missing.
- **Runner integration**: `runner.py` now attempts to load a persisted model before building from graph, and saves the model after an Active Inference run.
- **Escape handling**: Window/door escape detection; locked-case can attempt window fallback.
- **Parallel richer scenarios**: Added noisy sensing + jam action and a two-step key path as parallel fixtures to exercise deeper planning and stochastic handling without breaking the original room-escape tests.
- **Critical-state monitoring**: Active Inference runtime now updates `CriticalStateMonitor` each step (entropy-based) and exposes `current_critical_state`; unit tests cover panic/flow evaluation.
- **Learning persistence**: Dirichlet concentrations for A/B and preference counts are persisted (schema version 1.1); updates occur per step.
- **Memory influence**: SkillStats can bias prior action selection in the Active Inference path (procedural memory hook).
- **Automatic episodic replay**: Episode traces are replayed into A/B updates post-run; `update_from_episode` supports bulk transition updates.

## Tests added
- `tests/test_active_inference_runtime_learning.py`: Dirichlet update on A and locked/unlocked runs with stochastic sampling.
- `tests/test_active_inference_runtime_integration.py`: DB-backed unlocked run, epistemic-first action, escape, and Neo4j logging.
- `tests/test_active_inference_persistence.py`: Save/load roundtrip for the generative model; sanity comparison vs heuristic agent (both escape unlocked; Active Inference uses no more steps).
- `tests/test_active_inference_policy.py`: Confirms policy limiting works at higher depths.
- `tests/test_active_inference_policy_beam.py`: Validates beam search pruning reduces policy count.
- `tests/test_active_inference_preferences.py`: Confirms preferences/states persist round-trip and domain fallback uses persisted states.
- `tests/test_active_inference_scenarios.py`: Covers noisy sensing + jam/window path and a two-step key scenario (requires deeper planning/beam).
- `tests/test_active_inference_critical_states.py`: Validates panic vs flow evaluation using entropy signals.
- `tests/test_active_inference_persistence_dirichlet.py`: Ensures Dirichlet concentrations persist.
- `tests/test_active_inference_memory.py`: Confirms SkillStats bias action selection in Active Inference.
- `tests/test_active_inference_episode_learning.py`: Verifies episodic transitions update Dirichlet counts.
- `tests/test_active_inference_multi_episode.py`: Checks multi-episode likelihood improvements.
- `tests/test_active_inference_critical_protocols.py`: Validates free-energy-driven panic and entropy-driven flow.

## Current behavior vs heuristic baseline
- Active Inference now escapes in both unlocked and locked cases (window fallback), selects an epistemic action first in the unlocked integration test, and can persist learned parameters.
- The heuristic runtime remains richer (procedural/episodic memory, silver scoring, critical-state hooks); Active Inference is now functional but still lean: fixed-depth policy search, hand-shaped preferences, no long-horizon planning or memory integration.

## Known limitations / next steps
- Preferences/cost weights remain hand-tuned; persisted preferences help, but validating against graph changes would strengthen robustness.
- Policy search still relies on brute force or simple beam; more advanced pruning/batching would help for larger spaces.
- Persistence is JSON-with-version; no checkpointing/history yet.
- Critical-state is entropy/FE-only; Lyapunov and richer protocols are not integrated. Procedural/episodic memory influence is minimal (SkillStats bias; replay uses heuristic state inference).

## Red Team Assessment (current)
- Learning is rudimentary: per-step Dirichlet/preference count updates, but no multi-episode convergence or checkpoints; preferences still mostly hand-shaped.
- Policy search is basic (cap/beam), no advanced pruning or performance guards beyond caps.
- Critical-state signals are entropy-only; no Lyapunov or action-bias protocols under panic/scarcity.
- Memory integration is minimal (SkillStats bias); episodic memory is not wired into A/B/C.
- Behavior is still tuned to toy scenarios; robustness to graph changes or larger action/state spaces is unproven.
