# Test Commands Reference

Quick reference for all test commands in the MacGyver MUD project.

---

## Core Tests (Original Functionality - 83 tests)

```bash
# Run all core tests
make test

# Or directly:
NEO4J_URI=bolt://localhost:17687 NEO4J_USER=neo4j NEO4J_PASSWORD=password \
  python3 -m pytest test_scoring.py test_graph_model.py test_agent_runtime.py test_procedural_memory.py -v
```

**Expected:** 83 passed

**Breakdown:**
- `test_scoring.py`: 24 tests (entropy, goal value, info gain, scoring)
- `test_graph_model.py`: 17 tests (Neo4j I/O, silver integration)
- `test_agent_runtime.py`: 14 tests (agent behavior, episodes)
- `test_procedural_memory.py`: 28 tests (memory integration, learning)

---

## Silver Gauge Tests (22 tests)

```bash
# Run silver tests only
make test-silver

# Or directly:
NEO4J_URI=bolt://localhost:17687 NEO4J_USER=neo4j NEO4J_PASSWORD=password \
  python3 -m pytest test_scoring_silver.py -v
```

**Expected:** 22 passed

**Coverage:**
- Pythagorean means (HM, GM, AM)
- `build_silver_stamp` functionality
- Shape coefficients (k_explore, k_efficiency)
- Edge cases
- JSON serialization

---

## Complete Test Suite (105 tests)

```bash
# Run ALL tests (core + silver)
make test-all

# Or directly:
NEO4J_URI=bolt://localhost:17687 NEO4J_USER=neo4j NEO4J_PASSWORD=password \
  python3 -m pytest test_*.py -v
```

**Expected:** 105 passed (83 core + 22 silver)

---

## Silver Validation Suite (7 validations)

```bash
# Run accuracy validations
make validate-silver

# Or directly:
python3 validate_silver_accuracy.py
```

**Expected:** 7/7 validations pass

**Validations:**
1. Pythagorean Invariants (HM ≤ GM ≤ AM)
2. Shape Coefficient Bounds (k ∈ [0,1])
3. Base Score Preservation (exact match)
4. Component Consistency
5. Geometric Interpretability
6. **Decision Invariance (100% behavioral fidelity)**
7. All Values Finite

---

## Full Silver Test Suite

```bash
# Unit tests + validation
make test-silver-full
```

**Expected:** 22 tests + 7 validations, all pass

---

## Runner Tests (CLI Functionality)

```bash
# Unlocked door scenario
python3 runner.py --door-state unlocked --quiet
# Expected: ESCAPED (2 steps: peek → try_door)

# Locked door scenario
python3 runner.py --door-state locked --quiet
# Expected: ESCAPED (2 steps: peek → go_window)

# Verbose output
python3 runner.py --door-state unlocked
# Expected: Full trace with table and summary
```

---

## Query Silver Data

```bash
# Recent silver data
make query-silver

# Full stamp JSON
make query-silver-full

# Statistical summary
make silver-analysis
```

---

## Comparison Tests

```bash
# Compare silver vs default (behavioral equivalence)
make compare-silver
```

**Expected:** 100% decision invariance shown

---

## Quick Validation Workflow

```bash
# 1. Validate silver accuracy
make validate-silver

# 2. Run core tests
make test

# 3. Run silver tests
make test-silver

# 4. Run complete suite
make test-all

# 5. Test CLI
python3 runner.py --door-state unlocked --quiet
python3 runner.py --door-state locked --quiet

# 6. Verify silver data stored
make query-silver
```

If all pass: ✅ System validated!

---

## Individual Module Tests

```bash
# Scoring only
pytest test_scoring.py -v

# Graph model only
pytest test_graph_model.py -v

# Agent runtime only
pytest test_agent_runtime.py -v

# Procedural memory only
pytest test_procedural_memory.py -v

# Silver gauge only
pytest test_scoring_silver.py -v
```

---

## With Coverage

```bash
# Run with coverage report
pytest test_*.py --cov=. --cov-report=html

# View coverage
open htmlcov/index.html
```

---

## Troubleshooting

### Tests fail with connection error

**Problem:** Neo4j not running

**Solution:**
```bash
make neo4j-start
# Wait ~10 seconds for Neo4j to initialize
make neo4j-query  # Verify connection
```

### Tests fail with "Agent not found"

**Problem:** Graph not initialized

**Solution:**
```bash
# Initialize graph
docker exec -i neo4j44 cypher-shell -u neo4j -p password --encryption=false < cypher_init.cypher
```

### Silver tests fail

**Problem:** `scoring_silver.py` missing or corrupted

**Solution:**
```bash
# Verify file exists
ls -l scoring_silver.py

# Run validation
python3 validate_silver_accuracy.py
```

---

## Expected Test Times

| Test Suite | Tests | Time |
|------------|-------|------|
| `test_scoring.py` | 24 | ~0.08s |
| `test_graph_model.py` | 17 | ~1.1s |
| `test_agent_runtime.py` | 14 | ~1.2s |
| `test_procedural_memory.py` | 28 | ~3.8s |
| `test_scoring_silver.py` | 22 | ~0.07s |
| **Total (make test)** | **83** | **~5.8s** |
| **Total (make test-all)** | **105** | **~5.3s** |

---

## Success Criteria

✅ **All tests pass** = Original + Silver both functional
✅ **105/105 tests** = Complete validation
✅ **7/7 validations** = Mathematical correctness + behavioral fidelity
✅ **Runner works** = End-to-end functionality
✅ **Silver data stored** = Integration successful

---

**Current Status (2025-11-19):**
- Core tests: ✅ 83/83 passing
- Silver tests: ✅ 22/22 passing
- Validations: ✅ 7/7 passing
- **Total: ✅ 105/105 passing (100%)**
