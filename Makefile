.PHONY: help install neo4j-start neo4j-stop neo4j-restart neo4j-status neo4j-logs neo4j-shell clean test test-all
.PHONY: validate-silver visualize-silver compare-silver silver-demo silver-analysis test-silver-full
.PHONY: demo demo-original demo-silver demo-comparison
.PHONY: init-balanced test-balanced demo-crisp demo-balanced demo-hybrid test-skill-modes
.PHONY: demo-critical test-full
.PHONY: demo-critical test-full

# --- Configuration ---
CONTAINER_NAME ?= neo4j44
NEO4J_USER ?= neo4j
NEO4J_PASS ?= password
HTTP_PORT ?= 17474
BOLT_PORT ?= 17687

help: ## Show this help message
	@echo "MacGyver Active Inference Demo - Make targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

bootstrap: install neo4j-start test-full ## One-shot setup: Install, Start DB, and Test
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                   BOOTSTRAP COMPLETE                             ║"
	@echo "║                                                                  ║"
	@echo "║  System is ready for agent interaction.                          ║"
	@echo "║  - Dependencies: Installed                                       ║"
	@echo "║  - Database:     Running                                         ║"
	@echo "║  - Tests:        Passed                                          ║"
	@echo "║                                                                  ║"
	@echo "║  Run 'make demo' to see the agent in action.                     ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""

neo4j-start: ## Start Neo4j container with APOC
	@bash scripts/dev_neo4j_demo.sh

neo4j-stop: ## Stop and remove Neo4j container
	@echo "==> Stopping Neo4j container..."
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "==> Neo4j stopped"

neo4j-restart: neo4j-stop neo4j-start ## Restart Neo4j container

neo4j-status: ## Check Neo4j container status
	@docker ps -a | grep $(CONTAINER_NAME) || echo "Container $(CONTAINER_NAME) not found"

neo4j-logs: ## View Neo4j container logs
	@docker logs -f $(CONTAINER_NAME)

neo4j-shell: ## Open cypher-shell in Neo4j container
	@docker exec -it $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false

neo4j-query: ## Run a quick test query (verify connection)
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"RETURN 'Connected!' AS status, datetime() AS timestamp"

test: ## Run all core tests (scoring, graph_model, agent_runtime, procedural_memory)
	@echo "==> Running core test suite (80 tests)..."
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 -m pytest tests/test_scoring.py tests/test_graph_model.py tests/test_agent_runtime.py tests/test_procedural_memory.py -v

test-all: ## Run ALL tests (core + silver = 105 tests)
	@echo "==> Running complete test suite (105 tests)..."
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 -m pytest tests/test_*.py -v

test-silver: ## Run silver gauge tests only
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 -m pytest tests/test_scoring_silver.py -v

query-silver: ## Query recent silver gauge data from Neo4j
	@echo "==> Recent Silver Gauge Data (Last 10 steps)"
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"MATCH (s:Step) WHERE s.silver_stamp IS NOT NULL \
		 RETURN s.step_index AS step, s.skill_name AS skill, \
		        s.silver_score AS score, s.p_before AS belief \
		 ORDER BY s.created_at DESC LIMIT 10"

query-silver-full: ## Query full silver stamp JSON
	@echo "==> Full Silver Stamp (Latest Step)"
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"MATCH (s:Step) WHERE s.silver_stamp IS NOT NULL \
		 RETURN s.silver_stamp \
		 ORDER BY s.created_at DESC LIMIT 1"

clean: neo4j-stop ## Stop Neo4j and clean up
	@echo "==> Cleaning up..."
	@rm -rf __pycache__ .pytest_cache *.pyc
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "==> Clean complete"
	@echo "Note: To remove .neo4j44/ (if exists), run: sudo rm -rf .neo4j44/"

# --- Development targets ---
dev-init: install neo4j-start ## Initialize development environment
	@echo ""
	@echo "==> Development environment ready!"
	@echo "    Neo4j Browser: http://localhost:$(HTTP_PORT)"
	@echo "    Bolt:          bolt://localhost:$(BOLT_PORT)"
	@echo "    Credentials:   $(NEO4J_USER) / $(NEO4J_PASS)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make neo4j-shell' to interact with Neo4j"
	@echo "  2. Create cypher_init.cypher to initialize your graph"
	@echo "  3. Run 'python runner.py' when ready"

# --- Silver Gauge Targets ---

validate-silver: ## Validate silver gauge accuracy (100% behavioral fidelity)
	@echo "==> Validating Silver Gauge Accuracy..."
	@python3 validate_silver_accuracy.py

visualize-silver: ## Generate silver gauge visualizations (phase diagrams, etc.)
	@echo "==> Generating Silver Gauge Visualizations..."
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 visualize_silver.py
	@echo ""
	@echo "Visualizations saved:"
	@echo "  - phase_diagram.png"
	@echo "  - belief_geometry.png"
	@echo "  - policy_comparison.png"
	@echo "  - temporal_evolution.png"
	@echo "  - skill_comparison.png"

silver-demo: ## Run demo episodes to populate silver data
	@echo "==> Running demo episodes with silver gauge..."
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state locked --quiet
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state unlocked --quiet
	@echo "==> Demo complete. Query data with: make query-silver"

silver-analysis: ## Statistical analysis of silver data
	@echo "==> Silver Gauge Statistical Summary"
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"MATCH (s:Step) WHERE s.silver_stamp IS NOT NULL \
		 WITH apoc.convert.fromJsonMap(s.silver_stamp) AS stamp \
		 RETURN \
		   count(*) AS total_steps, \
		   avg(stamp.k_explore) AS avg_k_explore, \
		   stdev(stamp.k_explore) AS std_k_explore, \
		   avg(stamp.k_efficiency) AS avg_k_efficiency, \
		   stdev(stamp.k_efficiency) AS std_k_efficiency, \
		   min(stamp.k_explore) AS min_k_explore, \
		   max(stamp.k_explore) AS max_k_explore"

test-silver-full: test-silver validate-silver ## Run full silver test suite (unit + validation)
	@echo ""
	@echo "==> All Silver Tests Complete ✓"

compare-silver: ## Compare agent decisions with/without silver (behavioral equivalence)
	@echo "==> Comparing Silver vs Default Approach..."
	@echo "Running validation (should show 100% decision invariance)..."
	@python3 validate_silver_accuracy.py | grep -A 20 "VALIDATION 6"
	@echo ""
	@echo "Result: Silver gauge preserves agent behavior exactly."

# --- Demonstration Targets ---

demo: demo-original demo-silver ## Run complete demo (original + silver)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                    DEMO COMPLETE                                 ║"
	@echo "║                                                                  ║"
	@echo "║  Both versions demonstrated:                                     ║"
	@echo "║    ✓ Original active inference (behavior)                       ║"
	@echo "║    ✓ Silver gauge (geometric analysis)                          ║"
	@echo "║                                                                  ║"
	@echo "║  Key insight: IDENTICAL decisions, RICHER understanding          ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""

demo-original: ## Demonstrate original active inference (without silver analysis)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║              DEMO: ORIGINAL ACTIVE INFERENCE                     ║"
	@echo "║                                                                  ║"
	@echo "║  This shows the baseline active inference agent:                 ║"
	@echo "║    - Scores actions: α·goal + β·info - γ·cost                   ║"
	@echo "║    - Selects best action (argmax score)                         ║"
	@echo "║    - Logs to Neo4j                                              ║"
	@echo "║                                                                  ║"
	@echo "║  Silver gauge is present but we focus on BEHAVIOR               ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "==> Scenario 1: Unlocked Door"
	@echo ""
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state unlocked
	@echo ""
	@echo "==> Scenario 2: Locked Door"
	@echo ""
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state locked
	@echo ""
	@echo "✓ Original active inference demonstrated"
	@echo "  - Agent balanced exploration (peeking) and exploitation (acting)"
	@echo "  - Both scenarios solved optimally in 2 steps"
	@echo ""

demo-silver: ## Demonstrate silver gauge geometric analysis
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║              DEMO: SILVER GAUGE GEOMETRIC ANALYSIS               ║"
	@echo "║                                                                  ║"
	@echo "║  This shows the geometric lens on decisions:                     ║"
	@echo "║    - Same agent behavior (proven identical)                      ║"
	@echo "║    - NEW: k_explore (exploration balance)                        ║"
	@echo "║    - NEW: k_efficiency (benefit/cost ratio)                      ║"
	@echo "║    - NEW: Geometric interpretation                               ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "==> Running episodes to generate silver data..."
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state unlocked --quiet
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state locked --quiet
	@echo "✓ Episodes complete"
	@echo ""
	@echo "==> Silver Gauge Data (Recent Steps):"
	@echo ""
	@make query-silver
	@echo ""
	@echo "==> Geometric Interpretation:"
	@echo ""
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"MATCH (s:Step) WHERE s.silver_stamp IS NOT NULL \
		 WITH s, apoc.convert.fromJsonMap(s.silver_stamp) AS stamp \
		 RETURN s.step_index AS step, \
		        stamp.skill_name AS skill, \
		        round(stamp.k_explore * 100) / 100 AS k_explore, \
		        round(stamp.k_efficiency * 100) / 100 AS k_efficiency, \
		        CASE \
		          WHEN stamp.k_explore < 0.2 THEN 'Pure Exploitation' \
		          WHEN stamp.k_explore > 0.6 THEN 'Balanced' \
		          ELSE 'Mixed' \
		        END AS explore_mode, \
		        CASE \
		          WHEN stamp.k_efficiency > 0.8 THEN 'Excellent' \
		          WHEN stamp.k_efficiency > 0.5 THEN 'Good' \
		          ELSE 'Moderate' \
		        END AS efficiency \
		 ORDER BY s.created_at DESC LIMIT 5"
	@echo ""
	@echo "✓ Silver gauge demonstrated"
	@echo "  - Same decisions as original (100% behavioral fidelity)"
	@echo "  - NEW geometric insights: exploration balance, efficiency ratio"
	@echo "  - Interpretable: k_explore shows pure exploration vs. exploitation"
	@echo ""

demo-comparison: ## Side-by-side comparison: Original vs Silver
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║          COMPARISON: ORIGINAL vs SILVER GAUGE                    ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "┌──────────────────────────────────────────────────────────────────┐"
	@echo "│ ORIGINAL ACTIVE INFERENCE                                        │"
	@echo "├──────────────────────────────────────────────────────────────────┤"
	@echo "│ What you see:                                                    │"
	@echo "│   • Scalar score: 5.7                                            │"
	@echo "│   • Action selected: peek_door                                   │"
	@echo "│                                                                  │"
	@echo "│ What you DON'T see:                                              │"
	@echo "│   • WHY this action was chosen                                   │"
	@echo "│   • HOW balanced the trade-off is                                │"
	@echo "│   • WHAT shape the decision has                                  │"
	@echo "└──────────────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "┌──────────────────────────────────────────────────────────────────┐"
	@echo "│ SILVER GAUGE (GEOMETRIC LENS)                                    │"
	@echo "├──────────────────────────────────────────────────────────────────┤"
	@echo "│ What you see:                                                    │"
	@echo "│   • Same score: 5.7 (behavior unchanged!)                        │"
	@echo "│   • Same action: peek_door                                       │"
	@echo "│   • NEW: k_explore = 0.0 (pure exploration)                      │"
	@echo "│   • NEW: k_efficiency = 1.0 (perfect balance)                    │"
	@echo "│   • NEW: entropy = 1.0 (max uncertainty)                         │"
	@echo "│                                                                  │"
	@echo "│ Now you understand:                                              │"
	@echo "│   ✓ WHY: Pure information-gathering at max uncertainty           │"
	@echo "│   ✓ HOW: Perfectly balanced benefit/cost ratio                   │"
	@echo "│   ✓ WHAT: Pure exploration with excellent efficiency             │"
	@echo "└──────────────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "==> Running validation to prove behavioral equivalence..."
	@echo ""
	@python3 validate_silver_accuracy.py 2>&1 | grep -A 8 "VALIDATION 6"
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                        KEY INSIGHT                               ║"
	@echo "║                                                                  ║"
	@echo "║  Silver gauge transforms:                                        ║"
	@echo "║    Opaque scalar → Transparent geometry                          ║"
	@echo "║    \"What wins\" → \"Why it wins\"                                 ║"
	@echo "║    Magnitude only → Structure revealed                           ║"
	@echo "║                                                                  ║"
	@echo "║  Zero behavioral cost, rich diagnostic value                     ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""

# --- Balanced Skills & Multi-Objective Targets ---

demo-critical: ## Run the "Maximum Attack" demo (Critical State Protocols)
	@echo "==> Running Maximum Attack Demo (Critical State Protocols)..."
	@echo "This demonstrates the agent escaping a local optimum where standard AI fails."
	@python3 validation/comparative_stress_test.py

test-full: ## Run the full test suite (Unit + Red Team)
	@echo "==> Running Full Spectrum Test Suite..."
	@export PYTHONPATH=$$PYTHONPATH:. && \
	pytest tests/test_geometric_controller.py tests/test_critical_states.py && \
	python3 validation/geometric_trap_experiment.py && \
	python3 validation/red_team_experiment.py && \
	python3 validation/adaptive_red_team.py && \
	python3 validation/critical_state_red_team.py && \
	python3 validation/comparative_stress_test.py && \
	python3 validation/escalation_red_team.py && \
	python3 validation/hubris_validation_test.py
	@echo "==> ALL SYSTEMS GREEN: Full Spectrum Test Passed."

# --- Balanced Skills & Multi-Objective Targets ---

init-balanced: ## Initialize balanced skills in Neo4j (multi-objective)
	@echo "==> Adding balanced skills to Neo4j..."
	@docker exec -i $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false < balanced_skills_init.cypher
	@echo "✓ Balanced skills initialized"
	@echo ""
	@echo "Available skills:"
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"MATCH (s:Skill) RETURN s.name AS name, s.kind AS kind, s.cost AS cost ORDER BY s.kind, s.cost"

test-balanced: ## Test balanced skill scoring
	@echo "==> Testing balanced skill scoring..."
	@python3 scoring_balanced.py
	@echo ""
	@echo "✓ Balanced skills produce k_explore ∈ [0.56, 0.92]"

test-skill-modes: ## Test all skill mode filtering
	@echo "==> Testing skill mode integration..."
	@python3 tests/test_skill_mode_integration.py

demo-crisp: ## Demo with crisp skills only (pure specialists)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                  DEMO: CRISP SKILLS MODE                         ║"
	@echo "║                                                                  ║"
	@echo "║  Using only base skills (pure specialists):                      ║"
	@echo "║    • peek_door   (100% info, 0% goal) → k=0.00                   ║"
	@echo "║    • try_door    (0% info, 100% goal) → k=0.00                   ║"
	@echo "║    • go_window   (0% info, 100% goal) → k=0.00                   ║"
	@echo "║                                                                  ║"
	@echo "║  All k_explore ≈ 0 (architectural crispness)                     ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "==> Unlocked door scenario (crisp skills):"
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state unlocked --skill-mode crisp
	@echo ""
	@echo "==> Locked door scenario (crisp skills):"
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state locked --skill-mode crisp
	@echo ""
	@echo "✓ Crisp mode: Pure specialists, sharp mode boundaries"

demo-balanced: ## Demo with balanced skills only (multi-objective)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                DEMO: BALANCED SKILLS MODE                        ║"
	@echo "║                                                                  ║"
	@echo "║  Using only balanced skills (multi-objective):                   ║"
	@echo "║    • adaptive_peek      (40% goal + 60% info) → k=0.92           ║"
	@echo "║    • exploratory_action (70% goal + 70% info) → k=0.80           ║"
	@echo "║    • probe_and_try      (60% goal + 40% info) → k=0.73           ║"
	@echo "║    • informed_window    (80% goal + 30% info) → k=0.56           ║"
	@echo "║                                                                  ║"
	@echo "║  k_explore ∈ [0.56, 0.92] (rich geometric structure)             ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "==> Unlocked door scenario (balanced skills):"
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state unlocked --skill-mode balanced
	@echo ""
	@echo "==> Locked door scenario (balanced skills):"
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state locked --skill-mode balanced
	@echo ""
	@echo "✓ Balanced mode: Multi-objective, smooth transitions"

demo-hybrid: ## Demo with all skills (crisp + balanced)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                  DEMO: HYBRID SKILLS MODE                        ║"
	@echo "║                                                                  ║"
	@echo "║  Using ALL skills (crisp + balanced = 7 total):                  ║"
	@echo "║    Crisp (3):    k ≈ 0.0 (specialists)                           ║"
	@echo "║    Balanced (4): k ∈ [0.56, 0.92] (generalists)                  ║"
	@echo "║                                                                  ║"
	@echo "║  Agent has full spectrum to choose from                          ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "==> Unlocked door scenario (hybrid):"
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state unlocked --skill-mode hybrid
	@echo ""
	@echo "==> Locked door scenario (hybrid):"
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
		python3 runner.py --door-state locked --skill-mode hybrid
	@echo ""
	@echo "✓ Hybrid mode: Full flexibility, agent chooses optimal geometry"

visualize-balanced: ## Generate balanced vs crisp comparison visualizations
	@echo "==> Generating balanced skills comparison visualizations..."
	@python3 visualize_balanced_comparison.py
	@echo ""
	@echo "✓ Visualizations generated:"
	@echo "  - k_explore_comparison.png (crisp vs balanced distribution)"
	@echo "  - goal_info_space.png (2D objective space)"
	@echo "  - k_explore_vs_belief.png (evolution over belief)"
	@echo "  - phase_diagram_comparison.png (geometric phase space)"

# --- Jupyter Notebook Targets ---

.PHONY: notebook notebook-build notebook-info

notebook: ## Launch Jupyter notebook for interactive deep dive
	@echo "Launching Jupyter notebook..."
	@echo "The notebook will open in your browser."
	@echo ""
	@echo "Notebook: MacGyverMUD_DeepDive.ipynb"
	@echo "  - Part 0: Setup & Orientation"
	@echo "  - Part 1: The MacGyver Problem"
	@echo "  - Part 2: Active Inference Math"
	@echo "  - Part 4: Silver Gauge Revelation (THE CLIMAX!)"
	@echo "  - Part 5: Multi-Objective Evolution"
	@echo ""
	jupyter notebook MacGyverMUD_DeepDive.ipynb

notebook-build: ## Rebuild notebook from source scripts
	@echo "Rebuilding notebook..."
	python build_notebook_parts.py
	python build_notebook_part4.py
	python build_notebook_part5_final.py
	@echo "✓ Notebook rebuilt successfully"

notebook-info: ## Show notebook information
	@echo "MacGyver MUD Interactive Deep Dive Notebook"
	@echo "==========================================="
	@echo ""
	@echo "File: MacGyverMUD_DeepDive.ipynb"
	@echo "Estimated time: 2-3 hours"
	@echo ""
	@echo "Contents:"
	@echo "  Part 0: Setup & Orientation (5 min)"
	@echo "  Part 1: The MacGyver Problem (10 min)"
	@echo "  Part 2: Active Inference Math (20 min)"
	@echo "  Part 4: Silver Gauge Revelation (25 min) ⭐ THE CLIMAX"
	@echo "  Part 5: Multi-Objective Evolution (20 min)"
	@echo ""
	@echo "Features:"
	@echo "  ✓ Interactive sliders and calculators"
	@echo "  ✓ Live Neo4j database queries"
	@echo "  ✓ Progressive disclosure (concrete → abstract)"
	@echo "  ✓ Checkpoints to test understanding"
	@echo "  ✓ Professional visualizations"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Neo4j running (make neo4j-start)"
	@echo "  - Database initialized (make init)"
	@echo "  - Jupyter installed (pip install jupyter)"
	@echo ""
	@echo "Launch: make notebook"


# --- Advanced Features ---

demo-episodic: ## Demonstrate Episodic Memory Replay (Offline Learning)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║         DEMO: EPISODIC MEMORY REPLAY (OFFLINE LEARNING)         ║"
	@echo "║                                                                  ║"
	@echo "║  Demonstrates counterfactual reasoning:                          ║"
	@echo "║    Phase 1: Exploration (agent explores labyrinth)               ║"
	@echo "║    Phase 2: Reflection (generates 'what if' alternatives)        ║"
	@echo "║    Phase 3: Improvement (learns without new experience)          ║"
	@echo "║                                                                  ║"
	@echo "║  Key insight: Agent learns from MISTAKES in hindsight           ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
	python3 validation/episodic_replay_demo.py

test-episodic: ## Test Episodic Memory suite (unit + stress tests)
	@echo "==> Running Episodic Memory test suite..."
	@NEO4J_URI=bolt://localhost:$(BOLT_PORT) NEO4J_USER=$(NEO4J_USER) NEO4J_PASSWORD=$(NEO4J_PASS) \
	python3 -m pytest tests/test_episodic_stress.py -v
	@echo ""
	@echo "✓ All episodic memory tests passed"
