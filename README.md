# MacGyver MUD: Geometric Meta-Cognition Demo

A demonstration of **Active Inference**, **Procedural Memory**, and **Geometric Meta-Cognition** using Neo4j as a knowledge graph backend.

> **🌟 NEW (Nov 2025):** This project now features a **Hybrid Geometric Controller** that dynamically balances Robustness and Efficiency at runtime. See [ASSESSMENT_AND_SCORE.md](ASSESSMENT_AND_SCORE.md) for a deep technical dive.

## Overview

This project implements a "MacGyver in a Knowledge Graph" scenario where an agent:
1.  **Navigates** a Neo4j knowledge graph representing a locked room.
2.  **Maintains Beliefs** about hidden states (e.g., "is the door locked?").
3.  **Optimizes Decisions** using Active Inference (Expected Free Energy).
4.  **Adapts Strategy** using **Geometric Meta-Cognition** (The "Silver Gauge").

## Key Features

### 1. Active Inference & Procedural Memory
The agent balances **Exploration** (Info Gain) and **Exploitation** (Goal Value). It learns from past episodes to bias future decisions.
*   **Naive Mode:** Learns lazy behaviors (metric gaming).
*   **Strategic Mode:** Learns information-gathering patterns.

### 2. The Geometric Lens (Silver Gauge)
We use **Pythagorean Means** to quantify the "shape" of a skill:
*   **Specialists ($k \approx 0$):** High Goal OR High Info. Efficient but fragile.
*   **Generalists ($k \approx 1$):** Balanced Goal AND Info. Robust but expensive.

### 3. Geometric Meta-Cognition (The Controller)
The agent monitors its own **Entropy (Confusion)** to dynamically set a target strategy:
*   **Panic Mode (High Entropy):** Demands **Robustness** ($k \to 1$). "I'm confused, so I'll play it safe."
*   **Flow Mode (Low Entropy):** Demands **Efficiency** ($k \to 0$). "I know what to do, so I'll optimize."

### 4. Hybrid Architecture (Mitigations)
To prevent instability and delusion, the system includes:
*   **Hysteresis:** Prevents oscillation ("Jitterbug") when entropy is near the threshold.
*   **Memory Veto:** Checks historical success rates. If the agent is **Confident but Wrong** (Delusion), memory overrides the controller to force caution.

## Quick Start

### Prerequisites
*   Docker (for Neo4j)
*   Python 3.11+

### Setup
```bash
make dev-init  # Install deps + Start Neo4j
```

### Running the Agent

**Standard Run (Active Inference):**
```bash
python runner.py --door-state locked --use-memory
```

**Enable Geometric Controller:**
Edit `config.py` or use the flag (if supported by CLI, otherwise edit config):
```python
# config.py
ENABLE_GEOMETRIC_CONTROLLER = True
```

**Compare Behaviors:**
```bash
# 1. Run Baseline (Controller=False)
python runner.py --door-state locked --use-memory

# 2. Run Adaptive (Controller=True)
# (The agent will switch strategies based on uncertainty)
```

## Documentation Map

*   **[ASSESSMENT_AND_SCORE.md](ASSESSMENT_AND_SCORE.md):** **START HERE.** Comprehensive technical assessment, system diagram, and critical scoring.
*   **[GEOMETRIC_META_COGNITION.md](GEOMETRIC_META_COGNITION.md):** Design document for the runtime controller.
*   **[ANALYSIS_GEOMETRIC_MITIGATION.md](ANALYSIS_GEOMETRIC_MITIGATION.md):** Deep dive into the "Jitterbug" and "Mimic" failure modes and their solutions.
*   **[FINAL_REPORT.md](FINAL_REPORT.md):** Original deep analysis of the Silver Gauge framework.
*   **[PYTHAGOREAN_MEANS_EXPLAINED.md](PYTHAGOREAN_MEANS_EXPLAINED.md):** ELI5 guide to the math.

## Project Structure
```
macgyver_mud/
├── agent_runtime.py          # Core Logic (Active Inference + Geometric Controller)
├── scoring_silver.py         # Pythagorean Means & Entropy Logic
├── config.py                 # Configuration (Enable/Disable Controller)
├── validation/               # Experiments & Red Team Scripts
│   ├── adaptive_red_team.py  # Stress tests for the Controller
│   └── geometric_controller_test.py
├── tests/                    # Unit Tests
│   └── test_geometric_controller.py
└── ...
```

## License
MIT

## Author
mrlecko@gmail.com