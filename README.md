# MacGyver MUD: Hybrid Meta-Cognitive Agent Architecture

> **Status:** Research Prototype (Seeking External Validation)
> **Test Coverage:** Unit Tests + Red Team Scenarios (Discrete Environments)
> **Architecture:** Hybrid (Active Inference + Critical State Protocols)

A research demonstration exploring **meta-cognitive robustness** in discrete decision-making environments. This project combines:
1.  **Active Inference:** Probabilistic optimization for goal-seeking and exploration.
2.  **Geometric Meta-Cognition:** Real-time monitoring of the agent's belief state (entropy-based).
3.  **Critical State Protocols:** Rule-based overrides triggered during specific failure modes (Panic, Deadlock, Scarcity).

**Scope:** Tested in discrete, low-dimensional state spaces (5-step MUD scenarios). Generalization to continuous or high-dimensional environments remains unvalidated.

---

## 🚀 Quick Start

### Prerequisites
*   Docker (for Neo4j)
*   Python 3.11+

### 1. Initialize Environment
```bash
make dev-init
```

### 2. Run the Adversarial Robustness Demo
Watch the agent escape a local optimum (Honey Pot scenario) using critical state detection.
```bash
make demo-critical
```

### 3. Run the Full Test Suite
Verify the system integrity (Unit Tests + Red Team Scenarios).
```bash
make test-full
```

---

## 📋 Features & Capabilities

### Core Features

| Feature | Status | Demo Command | Documentation |
|:---|:---:|:---|:---|
| **Active Inference Decision Making** | ✅ Stable | `make demo-original` | Baseline agent optimization |
| **Geometric Meta-Cognition** | ✅ Stable | `make demo-silver` | Entropy-based belief monitoring |
| **Critical State Protocols** | ✅ Stable | `make demo-critical` | [Critical States](docs/design/CRITICAL_STATE_PROTOCOLS.md) |
| **Escalation (Circuit Breaker)** | ✅ Stable | `make demo-critical` | Hard stop for thrashing states |
| **Lyapunov Stability Monitor** | ✅ Stable | `pytest validation/test_lyapunov.py` | [Assessment](docs/brain/LYAPUNOV_ASSESSMENT_AND_RED_TEAM.md) |
| **Procedural Memory** | ✅ Stable | `python3 runner.py --memory` | Learn from past episodes |
| **Adaptive Meta-Parameters** | ✅ Stable | `python3 runner.py --adaptive` | α, β, γ self-tuning |

### Extended Environment

| Feature | Status | Demo Command | Documentation |
|:---|:---:|:---|:---|
| **Graph Labyrinth** | ✅ Stable | `pytest tests/test_graph_labyrinth.py` | [Walkthrough](docs/brain/GRAPH_LABYRINTH_WALKTHROUGH.md) |
| **Multi-Room Navigation** | ✅ Stable | N/A | Neo4j-backed spatial graphs |
| **Shortest Path Algorithms** | ✅ Stable | N/A | Dijkstra via Neo4j |

### Advanced Features (Episodic Memory)

| Feature | Status | Demo Command | Config Flag | Documentation |
|:---|:---:|:---|:---|:---|
| **Episodic Memory Replay** | ✅ Stable | `python3 validation/episodic_replay_demo.py` | `ENABLE_EPISODIC_MEMORY=true` | [Integration](docs/brain/EPISODIC_MEMORY_INTEGRATION_SUMMARY.md) |
| **Counterfactual Generation** | ✅ Stable | ↑ Same | `MAX_COUNTERFACTUALS=3` | [Stress Analysis](docs/brain/EPISODIC_MEMORY_STRESS_ANALYSIS.md) |
| **Skill Prior Updates** | ✅ Stable | ↑ Same | `EPISODIC_UPDATE_PRIORS=true` | [Advanced Features](docs/brain/ADVANCED_EPISODIC_MEMORY_FEATURES.md) |
| **Graph Labyrinth Integration** | ✅ Stable | ↑ Same | `EPISODIC_USE_LABYRINTH=true` | ↑ Same |
| **Forgetting Mechanism** | ✅ Stable | ↑ Same | `EPISODIC_FORGETTING=true` | ↑ Same |
| **Offline Learning** | ✅ Stable | Automatic (every 10 episodes) | `EPISODIC_REPLAY_FREQUENCY=10` | ↑ Same |

### Research Features (Experimental)

| Feature | Status | Notes |
|:---|:---:|:---|
| **Hierarchical Active Inference** | 🔬 Planned | Meta + base controllers |
| **Curiosity-Driven Exploration** | 🔬 Planned | Intrinsic motivation via Kolmogorov complexity |
| **Multi-Agent Coordination** | 🔬 Planned | Emergent communication protocols |

**Legend:** ✅ Stable | 🔬 Experimental | 📋 Planned

---

## 🧠 Key Features

### 1. The Bicameral Mind
The agent is not just a solver; it is a system with two layers:
*   **The Cortex (Active Inference):** Optimizes for Expected Free Energy ($G$). It is smart but fragile.
*   **The Brainstem (Critical States):** Monitors the Cortex. If the agent is confused, looping, or dying, the Brainstem takes over.

### 2. Critical State Protocols (The Instincts)
The system detects 5 distinct critical states and applies specific protocols:
*   **PANIC (High Entropy):** "I am confused." -> **Protocol: TANK** (Maximize Robustness).
*   **SCARCITY (Low Steps):** "I am dying." -> **Protocol: SPARTAN** (Maximize Efficiency).
*   **DEADLOCK (Loops):** "I am stuck." -> **Protocol: SISYPHUS** (Force Perturbation).
*   **NOVELTY (Surprise):** "That was weird." -> **Protocol: EUREKA** (Learn).
*   **HUBRIS (Complacency):** "I am too good." -> **Protocol: ICARUS** (Force Skepticism).

### 3. The Circuit Breaker (Escalation)
If the agent "thrashes" (oscillates between critical states), the **Escalation Protocol** triggers a hard stop to prevent resource waste.

### 4. Episodic Memory & Offline Learning (NEW)
The agent stores **counterfactual paths** ("what could have happened") and learns from them WITHOUT new experience:
- **Regret Analysis:** Identifies better choices in hindsight
- **Skill Updates:** Adjusts success rates based on counterfactual insights
- **Spatial Reasoning:** Uses graph topology for realistic alternatives
- **Memory Management:** Automatic forgetting to bound growth

---

## 📚 Documentation

The project documentation is organized in the `docs/` folder:

*   **Start Here:** `docs/reports/MACGYVER_PROJECT_FULL_ASSESSMENT.md` (Comprehensive Assessment)
*   **Design:** `docs/design/CRITICAL_STATE_PROTOCOLS.md`
*   **Philosophy:** `docs/philosophy/PROJECT_REFLECTION_AND_PATTERNS.md`
*   **Reports:** `docs/reports/FINAL_PROJECT_ASSESSMENT.md`

---

## 🛠️ Project Structure

```
macgyver_mud/
├── agent_runtime.py          # The Brain (Cortex + Brainstem + Episodic Memory)
├── critical_state.py         # The Instincts (State Detection)
├── scoring.py                # The Gauge (Skill Scoring)
├── scoring_silver.py         # The Gauge (Geometric Analysis)
├── config.py                 # The DNA (Configuration)
├── memory/                   # Episodic Memory System
│   ├── episodic_replay.py    # Counterfactual storage & replay
│   └── counterfactual_generator.py  # "What if" path generation
├── environments/             # Test Environments
│   ├── graph_labyrinth.py    # Multi-room spatial navigation
│   └── labyrinth.py          # Lyapunov testing environment
├── validation/               # The Gauntlet (Red Team Scripts)
│   ├── episodic_replay_demo.py  # Offline learning demo
│   ├── comparative_stress_test.py  # Critical states demo
│   └── ...
├── tests/                    # The Safety Net (Unit Tests)
│   ├── test_episodic_memory.py      # Episodic memory tests
│   ├── test_episodic_stress.py      # Stress tests
│   ├── test_graph_labyrinth.py      # Labyrinth tests
│   └── ...
└── docs/                     # The Wisdom (Documentation)
    ├── brain/                # Implementation artifacts
    ├── design/               # Design documents
    ├── philosophy/           # Reflections
    └── reports/              # Assessments
```

---

## 🚀 Quick Start Examples

### Enable All Features
```bash
# Start Neo4j
make neo4j-start

# Enable episodic memory with all advanced features
export ENABLE_EPISODIC_MEMORY=true
export EPISODIC_UPDATE_PRIORS=true
export EPISODIC_USE_LABYRINTH=true
export EPISODIC_FORGETTING=true

# Run agent
python3 runner.py --memory --adaptive
```

### Run Episodic Memory Demo
```bash
python3 validation/episodic_replay_demo.py
```

Expected output:
```
PHASE 1: EXPLORATION (20 steps average)
PHASE 2: REFLECTION (15 counterfactuals generated)
PHASE 3: IMPROVEMENT (30% projected improvement)

Total learning opportunities: 1686 steps saved if optimal
```


## License
MIT

## Author
mrlecko@gmail.com
