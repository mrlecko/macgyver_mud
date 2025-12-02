# Next Steps: From Toy to Mature Active Inference

Goal: replace the current heuristic/utility bandit with a principled, testable active-inference stack while preserving observability (silver stamps) as read-only.

## 1) Formalize the Generative Model (LoE: 2-3 days)
- Define categorical states (locked/unlocked), observations (existing Obs nodes), actions/skills (existing Skill nodes).
- Build A (Obs|State,Skill), B (State'|State,Skill), C (log preferences over observations/states; encode costs/rewards here), D (state priors).
- Source defaults from config + cypher, store matrices in code (and optionally in Neo4j for transparency).
- Add unit tests that A/B rows sum to 1 and C/D are normalized.

## 2) Proper Inference & Policy Evaluation (LoE: 3-5 days)
- Implement belief updates via Bayes/message passing using A/B/D after each observation; remove hand-coded belief clamps.
- Enumerate depth-2/3 policies; compute expected free energy (risk + ambiguity + epistemic value) per policy.
- Action selection via softmax over −EFE; remove ad hoc boosts from critical-state controller.
- Tests: analytic EFE cases, posterior correctness per observation, policy choice invariants.

## 3) Recast Epistemic Value (LoE: 1-2 days)
- Compute expected information gain per policy (expected posterior entropy reduction or expected KL), not current entropy or usage counts.
- Drop usage-based epistemic bonuses unless explicitly modeled as priors; add regression tests on edge beliefs (p≈0,0.5,1).

## 4) Learning A/B/C (LoE: 3-4 days)
- Maintain Dirichlet concentrations over A/B; update with experience.
- Allow preference learning for C when desired; keep costs/rewards as priors, not utilities.
- Tests: convergence on synthetic rollouts; resilience to sparse data.

## 5) Safety & Monitoring (LoE: 2-3 days)
- Redefine “critical states” on principled signals (free-energy gradients, posterior entropy bounds); remove additive boosts.
- Credit assignment becomes soft penalties with recovery via temperature/entropy bonuses; no -999 hard blocks.
- If keeping Lyapunov-style checks, derive from the generative model (e.g., bounds on free-energy change), not heuristic stress proxies.

## 6) Silver/Observability Hardening (LoE: 1 day)
- Lock silver to logging-only; remove/ignore `silver_score` multiplier in control path.
- Add numeric tests for negative/zero inputs, scale invariance, and monotonicity of ratios; keep stamps for dashboards/Neo4j queries.

## 7) Testing & Tooling (LoE: 2-3 days)
- Add fast unit tests for inference/EFE, integration tests over multi-step trajectories, adversarial cases (misleading observations, high-cost/low-info skills).
- Add performance guardrails for policy depth (pruning/temperature); ensure no-action deadlocks even with credit penalties.
- Document runbooks: how to run depth-2/3 planner, how to view silver stamps, how to toggle preference sets.

## 8) Migration Plan (LoE: 1-2 days)
- Maintain the current heuristic path behind a flag during rollout; default new path once tests pass.
- Provide a compatibility layer to load existing Neo4j data (skills/obs) into A/B/C/D, with validation warnings for missing probabilities.

Approximate total LoE: ~15-23 days of focused work (single engineer), depending on depth and test rigor. Critical path: Steps 1→2→3; others can parallelize partially.***
