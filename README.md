# MacGyver MUD: Active Inference Demo

A demonstration of active inference and procedural memory using Neo4j as a knowledge graph backend.

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

## Project Structure

```
macgyver_mud/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── Makefile              # Convenient commands
├── cypher_init.cypher    # Graph initialization
├── config.py             # Configuration
├── scoring.py            # Active inference scoring logic
├── graph_model.py        # Neo4j I/O operations
├── agent_runtime.py      # Agent decision-making
├── runner.py             # CLI entry point
├── docs/
│   ├── spec.md           # Detailed specification
│   ├── context_and_guidance.md  # Implementation guidance
│   └── implementation_plan.md   # Development plan
├── queries/
│   └── demo_queries.cypher      # Showcase queries for Neo4j Browser
├── scripts/
│   └── dev_neo4j_demo.sh # Neo4j startup script
└── tests/
    ├── test_scoring.py   # 24 tests
    ├── test_graph_model.py # 14 tests
    └── test_agent_runtime.py # 14 tests
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

```bash
make help           # Show all available commands
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
```

## Graph Model

The knowledge graph consists of three subgraphs:

### 1. World Graph
- **Agent**: MacGyverBot
- **Place**: Room A
- **Objects**: Door (can peek), Window (always escape)
- **StateVar**: DoorLockState {locked, unlocked}
- **Belief**: Agent's p(unlocked)

### 2. Procedural Graph
- **Skills**:
  - `peek_door` (cost: 1.0, kind: sense)
  - `try_door` (cost: 1.5, kind: act)
  - `go_window` (cost: 2.0, kind: act)
- **Observations**:
  - obs_door_locked, obs_door_unlocked
  - obs_door_opened, obs_door_stuck
  - obs_window_escape

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
# Run all tests (52 tests)
pytest test_scoring.py test_graph_model.py test_agent_runtime.py -v

# Run specific test file
pytest test_scoring.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

**Test Coverage:**
- `test_scoring.py`: 24 tests (entropy, goal value, info gain, scoring)
- `test_graph_model.py`: 14 tests (Neo4j I/O operations)
- `test_agent_runtime.py`: 14 tests (agent behavior, episodes)

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
SLOW_PENALTY = 4.0

# Belief updates
BELIEF_DOOR_LOCKED = 0.15
BELIEF_DOOR_UNLOCKED = 0.85
BELIEF_DOOR_STUCK = 0.10
```

### Implementation Status

✅ **Fully Implemented:**
- [x] Neo4j 4.4 with APOC
- [x] Graph initialization (14 nodes, 8 relationships)
- [x] Configuration system
- [x] Scoring logic (active inference)
- [x] Graph model operations
- [x] Agent runtime (decision loop)
- [x] CLI runner with rich output
- [x] Test suite (52 tests, 100% pass)
- [x] Demo queries
- [x] Documentation

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

## References

- [Full Specification](docs/spec.md)
- [Neo4j 4.4 Documentation](https://neo4j.com/docs/cypher-manual/4.4/)
- [APOC Documentation](https://neo4j.com/labs/apoc/4.4/)

## License

TBD

## Author

Active Inference & Procedural Memory Demo
