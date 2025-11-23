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
├── agent_runtime.py          # The Brain (Cortex + Brainstem)
├── critical_state.py         # The Instincts (State Detection)
├── scoring_silver.py         # The Gauge (Geometric Analysis)
├── config.py                 # The DNA (Configuration)
├── validation/               # The Gauntlet (Red Team Scripts)
├── tests/                    # The Safety Net (Unit Tests)
└── docs/                     # The Wisdom (Documentation)
```

## License
MIT

## Author
mrlecko@gmail.com
