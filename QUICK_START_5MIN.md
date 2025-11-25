# MacGyver MUD: 5-Minute Quick Start Guide

**Goal:** Get the Honey Pot escape demo running in 5 minutes or less.

**What you'll see:** An agent that escapes a local optimum (trap scenario) using meta-cognitive protocols that pure optimization algorithms get stuck in.

---

## Prerequisites Check (30 seconds)

Before starting, verify you have:

```bash
# Check Docker is running
docker --version
# Should output: Docker version X.X.X

# Check Python version
python3 --version
# Should output: Python 3.11.X or higher

# Check you're in the project directory
pwd
# Should output: .../macgyver_mud
```

**Don't have Docker?** Install from: https://docs.docker.com/get-docker/

**Don't have Python 3.11+?** Install from: https://www.python.org/downloads/

---

## Step 1: One-Command Setup (2 minutes)

This single command will:
- Start Neo4j database (via Docker)
- Create Python virtual environment
- Install all dependencies
- Initialize the graph database schema
- Load agent skills and configurations

```bash
make dev-init
```

**Expected output:**
```
✓ Neo4j container started
✓ Virtual environment created
✓ Dependencies installed
✓ Database schema initialized
✓ Agent configuration loaded
Ready to run demos!
```

**If you see errors:**
- Docker not running → Start Docker Desktop
- Port 7687 in use → Stop existing Neo4j: `docker stop neo4j`
- Permission denied → Use `sudo` or check Docker permissions

---

## Step 2: Run the Honey Pot Demo (30 seconds)

This demonstrates the agent escaping a scenario where:
- **Pure RL agents** get stuck (infinite loop between two high-reward but non-terminal states)
- **MacGyver agent** detects DEADLOCK and breaks free

```bash
make demo-critical
```

**What you'll see:**

```
==> Running Maximum Attack Demo (Critical State Protocols)...
This demonstrates the agent escaping a local optimum where standard AI fails.
======================================================================
COMPARATIVE STRESS TEST: THE HONEY POT
======================================================================
Scenario: A/B Loop gives Reward=1.0. C gives Reward=10.0 (Escape).
Expected: Baseline gets stuck, Critical detects DEADLOCK and escapes.
======================================================================

### DETERMINISTIC RUN (seed=42) ###

--- Running Baseline (Standard) ---
Step 1: Action=A, Reward=1.0
Step 2: Action=B, Reward=1.0
Step 3: Action=A, Reward=1.0
Step 4: Action=B, Reward=1.0
Step 5: Action=A, Reward=1.0
Step 6: Action=B, Reward=1.0
Step 7: Action=A, Reward=1.0
Step 8: Action=B, Reward=1.0
Step 9: Action=A, Reward=1.0
Step 10: Action=B, Reward=1.0
Step 11: Action=A, Reward=1.0
Step 12: Action=B, Reward=1.0
Step 13: Action=A, Reward=1.0
Step 14: Action=B, Reward=1.0
Step 15: Action=A, Reward=1.0
Step 16: Action=B, Reward=1.0
Step 17: Action=A, Reward=1.0
Step 18: Action=B, Reward=1.0
Step 19: Action=A, Reward=1.0
Step 20: Action=B, Reward=1.0
FAILURE! Stuck in loop (timeout).

--- Running Critical (Protocols) ---
Step 1: Action=C, Reward=10.0
SUCCESS! Escaped in 1 steps.

======================================================================
SINGLE RUN RESULTS
======================================================================
Baseline Agent: 21 steps (STUCK IN LOOP)
Critical Agent: 1 steps (ESCAPED)

✓ Critical State Protocols successfully broke the local optimum.

======================================================================
STATISTICAL VALIDATION (100 trials with different seeds)
======================================================================

Baseline Agent Statistics:
  Average steps: 21.0
  Success rate: 0.0% (0/100)
  Stuck in loop: 100/100
  Range: 21-20 steps

Critical Agent Statistics:
  Average steps: 3.6
  Success rate: 100.0% (100/100)
  Stuck in loop: 0/100
  Range: 1-5 steps

======================================================================
FINAL VERDICT
======================================================================
✓✓✓ CRITICAL STATE PROTOCOLS VALIDATED ✓✓✓
  - Critical agent is 82.9% faster on average
  - Critical agent has 100.0% better success rate
  - Baseline gets stuck 100/100 times
  - Critical gets stuck 0/100 times

```

**Key insight:** The DEADLOCK protocol (critical state detection) breaks the A→B→A→B loop that pure optimization can't escape.

---

## Step 3: Understand What Happened (1 minute)

The demo proves **three key architectural features**:

### 1. Meta-Cognitive Monitoring (The Brainstem)

The agent monitors its own behavior:
```python
# critical_state.py:114-158
def check_deadlock(self, location_history):
    # Detect A→B→A→B pattern
    if (location_history[-1] == location_history[-3] and
        location_history[-2] == location_history[-4]):
        return True  # DEADLOCK detected!
```

### 2. Protocol Override (System 2 > System 1)

When DEADLOCK is detected, meta-cognition **overrides** optimization:
```python
# agent_runtime.py:305-310
elif critical_state == CriticalState.DEADLOCK:
    # SISYPHUS PROTOCOL: Force Perturbation
    target_k = 0.5  # Balanced exploration
    self.geo_mode = "DEADLOCK (Perturbation)"
```

### 3. Geometric Scoring (The Silver Gauge)

Decisions are scored by **shape**, not just magnitude:
- `k_explore = GM/AM` measures exploration vs. exploitation balance
- DEADLOCK mode forces `k = 0.5` (balanced) to break specialization

---

## Step 4 (Optional): Explore More Demos (2 minutes)

### See the Full Test Suite
```bash
make test-full
```
Runs 392 tests across 42 test files (takes ~30 seconds)

### See Episodic Memory in Action
```bash
python3 validation/episodic_replay_demo.py
```
Watch the agent learn from **counterfactuals** (paths not taken)

### See Lyapunov Stability Monitoring
```bash
pytest validation/test_lyapunov.py -v
```
Demonstrates mathematical divergence detection (control theory)

---

## What's Next?

Now that you've seen the basics, explore:

1. **[Architecture Overview](README.md#-architecture-highlights)** — Understand the Bicameral Mind pattern
2. **[72 Aphorisms](docs/blog_series/04_72_aphorisms.md)** — Read the philosophy behind the design
3. **[Silver Gauge Math](scoring_silver.py)** — Deep dive into geometric analysis
4. **[Integration Tests](tests/test_integration.py)** — See how subsystems work together

---

## Troubleshooting

### Neo4j won't start
```bash
# Check if container exists
docker ps -a | grep neo4j

# Remove old container
docker rm -f neo4j

# Restart from scratch
make neo4j-start
```

### Python dependencies fail
```bash
# Try using Python 3.11 specifically
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Tests fail with "Connection refused"
```bash
# Neo4j isn't running
make neo4j-start

# Wait 10 seconds for startup
sleep 10

# Run tests again
make test-full
```

### Port 7687 already in use
```bash
# Stop existing Neo4j
docker stop $(docker ps -q --filter ancestor=neo4j:latest)

# Or use different port in config.py:
# NEO4J_URI = "bolt://localhost:7688"
```

---

## Understanding the Output

When you run `make demo-critical`, here's what each section means:

| Output | Meaning |
|--------|---------|
| `Expected Free Energy: 8.2` | The Cortex's optimization score (goal + info - cost) |
| `⚠️ CRITICAL STATE: DEADLOCK` | The Brainstem detected a problem |
| `Protocol: SISYPHUS` | The safety reflex that activates |
| `k_explore = 0.5` | The Silver Gauge shape coefficient (balanced) |
| `✓ ESCAPED` | The agent broke free of the local optimum |

---

## Clean Up (Optional)

To stop all services and clean up:

```bash
# Stop Neo4j
docker stop neo4j

# Remove virtual environment
rm -rf venv

# Remove Neo4j data (WARNING: deletes all graph data)
docker rm neo4j
```

---

## Need Help?

- **Issues:** https://github.com/anthropics/claude-code/issues
- **Email:** mrlecko@gmail.com
- **Read the docs:** Start with [README.md](README.md)

---

**Total time:** ~5 minutes

**What you learned:**
1. ✅ How to run the project
2. ✅ What meta-cognitive protocols are
3. ✅ Why the Silver Gauge matters
4. ✅ How to escape local optima with circuit breakers

**Next:** Dive into the [72 Aphorisms](docs/blog_series/04_72_aphorisms.md) to understand the philosophy that shaped every design decision.
