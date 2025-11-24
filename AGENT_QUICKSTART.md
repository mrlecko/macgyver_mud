# Agent Quickstart: MacGyver MUD

> **Target Audience:** AI Agents (Claude, GPT-4, Gemini) & Human Engineers
> **Objective:** Rapidly ingest, validate, and extend the MacGyver MUD architecture.
> **Time to Context:** < 2 minutes

---

## ⚡ One-Shot Bootstrap

Do not waste time manually installing dependencies or starting databases. Run this single command to initialize the environment, start Neo4j, and run the full "Red Team" test suite:

```bash
make bootstrap
```

**What this does:**
1.  Installs Python dependencies (`requirements.txt`).
2.  Starts the Neo4j graph database container (with APOC).
3.  Runs 100+ tests, including Unit, Integration, and Adversarial scenarios.

**Success Criteria:**
- Output ends with `BOOTSTRAP COMPLETE`.
- All tests pass (green).

---

## 🧠 The Mental Model (Read This First)

This is **not** a standard RL project. It is a **Bicameral Cognitive Architecture**.

### 1. The Cortex (System 1)
- **Mechanism:** Active Inference (Expected Free Energy minimization).
- **Goal:** Fast, intuitive decision-making.
- **Code:** `agent_runtime.py`, `scoring.py`.

### 2. The Brainstem (System 2)
- **Mechanism:** Critical State Protocols (Rule-based overrides).
- **Goal:** Safety, robustness, and breaking local optima.
- **Code:** `critical_state.py`, `control/lyapunov.py`.
- **Key Insight:** The agent "panics" when entropy is high and "locks down" when resources are low.

### 3. The Memory (Graph)
- **Mechanism:** Neo4j Graph Database.
- **Goal:** Explainable, structured episodic memory.
- **Code:** `graph_model.py`, `memory/`.

---

## 📚 Essential Context (Ingest in Order)

To fully understand the project's capabilities and limitations, ingest these files:

1.  **[README.md](README.md)**: High-level overview and claims.
2.  **[FULL_PROJECT_ASSESSMENT.md](FULL_PROJECT_ASSESSMENT.md)**: **CRITICAL.** A brutal, honest Red Team assessment of the project's strengths (Architecture) and weaknesses (TextWorld).
3.  **[AUTHOR_ASSESSMENT.md](AUTHOR_ASSESSMENT.md)**: Profile of the creator's "Philosopher-Engineer" archetype.
4.  **[docs/blog_series/04_72_aphorisms.md](docs/blog_series/04_72_aphorisms.md)**: The engineering philosophy ("The agent that cannot panic is the agent that will die calmly").

---

## 🛠️ Verification & Demos

After bootstrapping, verify the agent's behavior with these demos:

### 1. The "MacGyver" Escape (Active Inference)
See the agent balance exploration (peeking) and exploitation (escaping).
```bash
make demo
```

### 2. The "Honey Pot" Trap (Critical States)
See the agent get stuck in a loop, detect it (DEADLOCK), and escape.
```bash
make demo-critical
```

### 3. The "Silver Gauge" (Metrology)
See the mathematical "shape" of decisions (Exploration vs. Efficiency).
```bash
make visualize-silver
```

---

## ⚠️ Known Gotchas

- **Neo4j Startup:** Takes ~10s. `make bootstrap` handles the wait, but if you restart manually, give it time.
- **TextWorld:** The `domain4_textworld` tests are computationally expensive. They run as part of `make bootstrap` but can be skipped with `make test` (core only).
- **Docker:** Ensure Docker is running. The project relies heavily on containers.

---

## 🤖 Agent Directives

If you are an AI agent reading this:
1.  **Respect the Brainstem:** Do not try to "optimize away" the critical state protocols. They are there to prevent you from optimizing yourself into a corner.
2.  **Trust the Graph:** The Neo4j database is the source of truth. If you need to know what happened, query the graph.
3.  **Embrace the Aphorisms:** Use the "72 Aphorisms" as heuristics for your own code generation.

**Go forth and build robust minds.**
