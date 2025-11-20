# MacGyver MUD: Active Inference Demo

A demonstration of active inference and procedural memory using Neo4j as a knowledge graph backend.

> **⚠️ IMPORTANT**: See [ERRATA.md](ERRATA.md) for critical corrections to original claims about k≈0 clustering and performance benefits. Empirical validation (Nov 2025) found that k≈0 clustering is a design property, not a natural phenomenon.

## Overview

This project implements a "MacGyver in a Knowledge Graph" scenario where an agent:
- Navigates a Neo4j knowledge graph representing a locked room
- Maintains beliefs about hidden states (e.g., "is the door locked?")
- Chooses actions to reduce uncertainty or reach goals
- Logs experiences as procedural memory in the graph

The system demonstrates active inference principles where the agent balances:
- **Information gain** (exploration)
- **Goal achievement** (exploitation)
- **Action costs**

## Procedural Memory & Reward Design

This project demonstrates two key concepts:

### 1. Procedural Memory
The agent can learn from past episodes using the `--use-memory` flag:
- Episodes are logged to the graph (always)
- With `--use-memory`: Agent learns from success patterns to bias future decisions
- Without flag: Episodes are logged but not used for learning

### 2. Reward Mode Impact
The same learning mechanism produces **dramatically different behaviors** based on reward design:

**NAIVE mode** (`--reward-mode=naive`):
- Demonstrates **metric gaming**
- Agent learns to spam `go_window` (lazy but efficient)
- Shows how agents optimize what you measure, not what you intend
- SLOW_PENALTY = 4.0 (window escape is viable)

**STRATEGIC mode** (`--reward-mode=strategic`, default):
- Encourages **information-gathering strategies**
- Agent maintains peek → act pattern
- Shows how better rewards → better learned behavior
- SLOW_PENALTY = 6.0 (encourages checking door first)

### Quick Comparison

```bash
# See metric gaming (agent learns lazy behavior)
python runner.py --door-state locked --use-memory --reward-mode=naive

# See strategic learning (agent learns smart behavior)
python runner.py --door-state locked --use-memory --reward-mode=strategic

# Full statistical comparison
python experiments/reward_mode_comparison.py
```

**Key Lesson:** What you measure determines what you get. A 2-point penalty difference (4.0 vs 6.0) produces completely different learned behaviors.

See [QUICKSTART_BOTH_MODES.md](QUICKSTART_BOTH_MODES.md) for detailed pedagogical guide.

### 3. Skill Modes: Crisp, Balanced, and Hybrid

The agent can operate with different skill sets, each revealing different aspects of decision-making:

**CRISP MODE** (`--skill-mode=crisp`, pure specialists):
- Uses only base skills: peek, try, window
- Each skill is a pure specialist (100% goal OR 100% info)
- k_explore ≈ 0 for all skills (architectural crispness)
- **Use case:** Pedagogical clarity, sharp mode boundaries

**BALANCED MODE** (`--skill-mode=balanced`, multi-objective):
- Uses only balanced skills: probe_and_try, informed_window, exploratory_action, adaptive_peek
- Each skill provides BOTH goal AND information
- k_explore ∈ [0.56, 0.92] (rich geometric structure)
- **Use case:** Demonstrating multi-objective trade-offs, geometric curriculum

**HYBRID MODE** (`--skill-mode=hybrid`, default):
- Uses all 7 skills (3 crisp + 4 balanced)
- Full spectrum from specialists to generalists
- Agent chooses optimal geometric strategy
- **Use case:** Maximum flexibility, research on policy adaptation

```bash
# Pure specialists (crisp)
python runner.py --door-state unlocked --skill-mode crisp

# Multi-objective (balanced)
python runner.py --door-state locked --skill-mode balanced

# All skills (hybrid, default)
python runner.py --door-state unlocked --skill-mode hybrid
```

**Key Insight:** Same active inference scoring, different behavior based on skill design geometry!

### 4. Silver Gauge (Geometric Diagnostic Layer)

The **silver gauge** uses **Pythagorean means** to create geometric fingerprints of decisions:

**What it measures:**
- `k_explore`: Exploration balance (0 = specialist, 1 = perfectly balanced)
- `k_efficiency`: Benefit/cost ratio (0 = inefficient, 1 = excellent)

**Why Pythagorean means?**
- Scale-invariant (dimensionless metrics transfer across domains)
- 100% behavioral fidelity (adds interpretation without changing decisions)
- Theoretically principled (2,500-year-old mathematics, newly applied to AI)

**Auto-enabled by default**, storing compact JSON "stamps" on each Step node.

```bash
# Query recent silver data
make query-silver

# Validate accuracy (100% fidelity)
make validate-silver

# Generate visualizations
make visualize-silver

# Compare crisp vs balanced geometries
make visualize-balanced
```

**Use cases:**
- Quantitative policy comparison
- Geometric curriculum learning
- Transfer learning via dimensionless patterns
- Meta-learning with interpretable signals
- Debugging and anomaly detection

**Deep dive:** See [PYTHAGOREAN_MEANS_EXPLAINED.md](PYTHAGOREAN_MEANS_EXPLAINED.md) for comprehensive ELI5 guide covering:
- WHY use Pythagorean means (interpretability without sacrifice)
- WHAT they are (HM, GM, AM with examples)
- HOW they work (step-by-step walkthrough)
- WHERE else they're used (finance, ML, physics)
- WHAT innovations this enables (10+ expansion opportunities)

## Project Structure

```
macgyver_mud/
├── README.md                          # This file
├── FINAL_REPORT.md                    # 75-page deep analysis (25k words)
├── PYTHAGOREAN_MEANS_EXPLAINED.md     # ELI5 deep dive on geometric means
├── BALANCED_POLICY_GUIDE.md           # Guide to multi-objective skills
├── requirements.txt                   # Python dependencies
├── Makefile                          # Convenient commands (50+ targets)
├── cypher_init.cypher                # Base graph initialization
├── balanced_skills_init.cypher       # Multi-objective skills
├── config.py                         # Configuration
├── scoring.py                        # Active inference scoring
├── scoring_silver.py                 # Silver gauge (Pythagorean means)
├── scoring_balanced.py               # Balanced skill scoring
├── graph_model.py                    # Neo4j I/O + skill filtering
├── agent_runtime.py                  # Agent decision-making
├── runner.py                         # CLI entry point
├── validate_silver_accuracy.py       # 7 validation tests (100% pass)
├── visualize_silver.py               # Phase diagrams, geometries
├── visualize_balanced_comparison.py  # Crisp vs balanced comparisons
├── test_scoring.py                   # 24 tests
├── test_scoring_silver.py            # 22 tests
├── test_graph_model.py               # 14 tests
├── test_agent_runtime.py             # 14 tests
├── test_procedural_memory.py         # 28 tests
├── test_balanced_runner.py           # Integration tests
├── test_skill_mode_integration.py    # 5 skill mode tests
├── docs/
│   └── [Additional documentation]
├── queries/
│   └── demo_queries.cypher           # Neo4j showcase queries
└── scripts/
    └── dev_neo4j_demo.sh             # Neo4j startup script

Total: ~5,300 lines of code, 110+ tests (100% pass rate)
```

## Quick Start

### Prerequisites

- Docker (for Neo4j)
- Python 3.11+
- Make (optional, for convenience)

### Setup

1. **Install Python dependencies:**
   ```bash
   make install
   # or: pip install -r requirements.txt
   ```

2. **Start Neo4j:**
   ```bash
   make neo4j-start
   # or: bash scripts/dev_neo4j_demo.sh
   ```

   This will:
   - Start Neo4j 4.4 with APOC enabled
   - Expose ports 17474 (HTTP) and 17687 (Bolt)
   - Set credentials: `neo4j / password`

3. **Verify connection:**
   ```bash
   make neo4j-query
   # or: make neo4j-shell
   ```

### Access Neo4j

- **Browser UI:** http://localhost:17474
- **Bolt Protocol:** bolt://localhost:17687
- **Credentials:** neo4j / password

## Makefile Commands

### Core Commands
```bash
make help           # Show all available commands (50+)
make install        # Install Python dependencies
make neo4j-start    # Start Neo4j container
make neo4j-stop     # Stop Neo4j container
make neo4j-restart  # Restart Neo4j
make neo4j-status   # Check container status
make neo4j-logs     # View Neo4j logs
make neo4j-shell    # Open cypher-shell
make neo4j-query    # Run a test query
make clean          # Clean up
make dev-init       # Full setup (install + start)
```

### Testing Commands
```bash
make test              # Core tests (80 tests)
make test-all          # All tests (110+ tests)
make test-silver       # Silver gauge tests only
make test-balanced     # Balanced skill tests
make test-skill-modes  # Skill mode integration tests
```

### Skill Mode Demos
```bash
make demo-crisp     # Demo crisp skills (pure specialists, k≈0)
make demo-balanced  # Demo balanced skills (multi-objective, k∈[0.5,0.9])
make demo-hybrid    # Demo all skills (full spectrum)
make init-balanced  # Initialize balanced skills in Neo4j
```

### Silver Gauge Commands
```bash
make validate-silver     # Validate 100% behavioral fidelity
make visualize-silver    # Generate phase diagrams
make visualize-balanced  # Compare crisp vs balanced geometries
make query-silver        # Query recent silver data
make silver-analysis     # Statistical summary
```

### Demo Commands
```bash
make demo            # Full demo (original + silver)
make demo-original   # Original active inference demo
make demo-silver     # Silver gauge demo
make demo-comparison # Side-by-side comparison
```

## Configuration

Environment variables can override defaults:

```bash
export CONTAINER_NAME=neo4j44
export NEO4J_USER=neo4j
export NEO4J_PASS=password
export HTTP_PORT=17474
export BOLT_PORT=17687
```

## Running the Demo

### Basic Usage

Run the agent in both scenarios:

```bash
# Unlocked door scenario
python runner.py --door-state unlocked

# Locked door scenario
python runner.py --door-state locked
```

### Expected Behavior

**Unlocked Scenario** (optimal: 2 steps)
1. Agent peeks at door (p=0.5 → 0.85)
2. Agent tries door and escapes

**Locked Scenario** (optimal: 2 steps)
1. Agent peeks at door (p=0.5 → 0.15)
2. Agent uses window to escape

### Advanced Options

```bash
# Custom initial belief
python runner.py --door-state unlocked --initial-belief 0.9

# Increase max steps
python runner.py --door-state locked --max-steps 10

# Verbose mode (show scoring details)
python runner.py --door-state unlocked --verbose

# Quiet mode (just result)
python runner.py --door-state locked --quiet

# Enable procedural memory learning
python runner.py --door-state locked --use-memory

# Choose reward mode (naive shows metric gaming, strategic shows smart learning)
python runner.py --door-state locked --use-memory --reward-mode=naive
python runner.py --door-state locked --use-memory --reward-mode=strategic

# Enable adaptive meta-learning (adjusts exploration over time)
python runner.py --door-state locked --use-memory --adaptive

# Show memory reasoning details
python runner.py --door-state locked --use-memory --verbose-memory

# Use different skill modes
python runner.py --door-state locked --skill-mode crisp      # Pure specialists
python runner.py --door-state locked --skill-mode balanced   # Multi-objective
python runner.py --door-state locked --skill-mode hybrid     # All skills (default)
```

**Key Flags:**
- `--use-memory`: Enable learning from past episodes
- `--reward-mode`: Choose `naive` (metric gaming) or `strategic` (smart play)
- `--adaptive`: Enable meta-learning (adjusts parameters every 5 episodes)
- `--verbose-memory`: Show detailed memory-based reasoning
- `--skill-mode`: Choose skill set: `crisp`, `balanced`, or `hybrid` (default)

## Graph Model

The knowledge graph consists of three subgraphs:

### 1. World Graph
- **Agent**: MacGyverBot
- **Place**: Room A
- **Objects**: Door (can peek), Window (always escape)
- **StateVar**: DoorLockState {locked, unlocked}
- **Belief**: Agent's p(unlocked)

### 2. Procedural Graph
- **Crisp Skills** (pure specialists):
  - `peek_door` (cost: 1.0, kind: sense) - 100% info, 0% goal
  - `try_door` (cost: 1.5, kind: act) - 0% info, 100% goal
  - `go_window` (cost: 2.0, kind: act) - 0% info, 100% goal
- **Balanced Skills** (multi-objective):
  - `adaptive_peek` (cost: 1.3, kind: balanced) - 60% info + 40% goal
  - `probe_and_try` (cost: 2.0, kind: balanced) - 40% info + 60% goal
  - `informed_window` (cost: 2.2, kind: balanced) - 30% info + 80% goal
  - `exploratory_action` (cost: 2.5, kind: balanced) - 70% info + 70% goal
- **Observations**:
  - obs_door_locked, obs_door_unlocked
  - obs_door_opened, obs_door_stuck
  - obs_window_escape
  - obs_partial_info, obs_attempted_open, obs_strategic_escape

### 3. Episode Graph
- **Episode**: One simulation run
- **Step**: Action + observation + belief update
- Links: HAS_STEP, USED_SKILL, OBSERVED

## Exploring in Neo4j Browser

Open http://localhost:17474 and try these queries:

```cypher
// View latest episode trace
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH (e)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
MATCH (s)-[:OBSERVED]->(o:Observation)
RETURN s.step_index AS step, sk.name AS skill,
       o.name AS observation, s.p_before, s.p_after
ORDER BY s.step_index;

// Visualize episode flow
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH path = (e)-[:HAS_STEP]->(s)-[:USED_SKILL]->(sk)
MATCH (s)-[:OBSERVED]->(o)
RETURN path, o;
```

See `queries/demo_queries.cypher` for more showcase queries.

## Development

### Running Tests

All tests use pytest with TDD approach:

```bash
# Run all tests (110+ tests)
make test-all

# Run specific test suites
make test            # Core tests (80 tests)
make test-silver     # Silver gauge tests (22 tests)
make test-balanced   # Balanced skill tests
make test-skill-modes # Skill mode integration tests

# Or use pytest directly
pytest test_*.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

**Test Coverage:**
- `test_scoring.py`: 24 tests (entropy, goal value, info gain, scoring)
- `test_scoring_silver.py`: 22 tests (Pythagorean means, silver gauge)
- `test_graph_model.py`: 14 tests (Neo4j I/O operations)
- `test_agent_runtime.py`: 14 tests (agent behavior, episodes)
- `test_procedural_memory.py`: 28 tests (memory integration, learning)
- `test_balanced_runner.py`: Integration tests (skill mode filtering)
- `test_skill_mode_integration.py`: 5 tests (CLI integration)
- `validate_silver_accuracy.py`: 7 validation tests (100% pass)

### Configuration

Edit `config.py` to tune parameters:

```python
# Active inference weights
ALPHA = 1.0   # Goal value weight
BETA = 6.0    # Information gain weight
GAMMA = 0.3   # Cost weight

# Rewards/Penalties
REWARD_ESCAPE = 10.0
PENALTY_FAIL = 3.0
SLOW_PENALTY = 4.0  # (naive mode) or 6.0 (strategic mode)

# Belief updates
BELIEF_DOOR_LOCKED = 0.15
BELIEF_DOOR_UNLOCKED = 0.85
BELIEF_DOOR_STUCK = 0.10

# Reward Mode
REWARD_MODE = "strategic"  # or "naive"
```

### Implementation Status

✅ **Fully Implemented:**
- [x] Neo4j 4.4 with APOC
- [x] Graph initialization (crisp + balanced skills)
- [x] Configuration system
- [x] Scoring logic (active inference + silver gauge + balanced)
- [x] Graph model operations + skill filtering
- [x] Agent runtime (decision loop + skill modes)
- [x] Procedural memory & learning
- [x] Reward modes (naive vs strategic)
- [x] Skill modes (crisp, balanced, hybrid)
- [x] Silver gauge (Pythagorean means diagnostic layer)
- [x] Balanced skills (multi-objective trade-offs)
- [x] CLI runner with rich output + skill mode support
- [x] Test suite (110+ tests, 100% pass rate)
- [x] Validation suite (7 tests, 100% fidelity proven)
- [x] Visualization suite (phase diagrams, comparisons)
- [x] Comprehensive documentation (FINAL_REPORT, ELI5 guides)
- [x] Makefile with 50+ convenient targets

## Architecture Decisions

- **Neo4j 4.4**: Chosen for stability and APOC 4.4 compatibility
- **Alternate Ports** (17474/17687): Avoid conflicts with system services
- **No local plugin mount**: Using `NEO4JLABS_PLUGINS` for cleaner setup
- **Rich library**: For better demo output formatting

## Troubleshooting

**Container won't start:**
```bash
make neo4j-logs  # Check logs
make neo4j-stop && make neo4j-start  # Force restart
```

**Port conflicts:**
```bash
# Change ports in Makefile or export:
export HTTP_PORT=18474 BOLT_PORT=18687
make neo4j-start
```

**Permission issues with .neo4j44/:**
```bash
sudo rm -rf .neo4j44/  # If needed
```

## Next Steps

**Beginners:**
- Read [ELI5.md](ELI5.md) for concept explanations
- Run both door scenarios (unlocked/locked)
- Explore the memory graph in Neo4j Browser

**Compare Reward Modes:**
- See [QUICKSTART_BOTH_MODES.md](QUICKSTART_BOTH_MODES.md) for pedagogical guide
- Run `python experiments/reward_mode_comparison.py` for statistical comparison
- Understand how metric gaming emerges from reward design

**Deep Dive:**
- Read [FINAL_REPORT.md](FINAL_REPORT.md) for comprehensive 75-page analysis
- Study [PYTHAGOREAN_MEANS_EXPLAINED.md](PYTHAGOREAN_MEANS_EXPLAINED.md) for mathematical foundations
- Review [BALANCED_POLICY_GUIDE.md](BALANCED_POLICY_GUIDE.md) for multi-objective skills
- Explore the graph structure with custom Cypher queries
- Experiment with different parameter values in `config.py`

**Research Directions:**
- Geometric curriculum learning (k_explore-based progression)
- Transfer learning via dimensionless patterns
- Meta-learning with shape coefficients
- Multi-agent coordination via geometric diversity
- Continuous skill spaces with target k values
- Deep RL integration with geometric constraints

**Extend The Project:**
- Add new balanced skills with different k_explore targets
- Implement multi-room scenarios
- Try geometric meta-learning controllers
- Integrate with deep RL frameworks
- Build cross-domain pattern libraries
- Develop hierarchical shape coefficients

## Key Documents

**⚠️ READ FIRST:**
- [ERRATA.md](ERRATA.md) - **Critical corrections** to original claims (empirical validation results)
- [validation/EMPIRICAL_RED_TEAM_RESULTS.md](validation/EMPIRICAL_RED_TEAM_RESULTS.md) - Full experimental results

**Framework Documentation:**
- [FINAL_REPORT.md](FINAL_REPORT.md) - Comprehensive analysis of Silver Gauge framework *(see ERRATA for corrections)*
- [PYTHAGOREAN_MEANS_EXPLAINED.md](PYTHAGOREAN_MEANS_EXPLAINED.md) - ELI5 deep dive on geometric means
- [BALANCED_POLICY_GUIDE.md](BALANCED_POLICY_GUIDE.md) - Guide to multi-objective skills *(see ERRATA for corrections)*
- [DEMO_GUIDE.md](DEMO_GUIDE.md) - Interactive demonstration walkthrough
- [TEST_COMMANDS.md](TEST_COMMANDS.md) - Testing and validation guide

## References

- [Neo4j 4.4 Documentation](https://neo4j.com/docs/cypher-manual/4.4/)
- [APOC Documentation](https://neo4j.com/labs/apoc/4.4/)
- Active Inference Framework (Friston et al.)
- Pythagorean Means (Classical Mathematics, 500 BCE)

## License

MIT

## Author

mrlecko@gmail.com