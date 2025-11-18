# SPEC: Neo4j “MacGyver” Active Inference Demo

**MacGyver in a Knowledge Graph: Tiny Active Inference Demo on Neo4j**

**One-liner:**  
A small but real example where an agent navigates a Neo4j knowledge graph, maintains beliefs about hidden state, chooses actions to reduce uncertainty or reach a goal, and logs its experience as procedural memory.

> This spec is written so that **a coding LLM or human** can implement v1
> safely and predictably. When in doubt, follow the **“v1 subset”** rules.

---

## 0. Audience & Expectations

This is for an **implementation agent** (coding LLM) and/or a human engineer who:

- Knows basic **Python 3**
- Can connect to **Neo4j** with the official Python driver
- Can run **Cypher** scripts

You **do not** need:

- Advanced RL libraries
- Full Friston-style Active Inference maths
- Web frameworks or complex infra

You **must** keep v1:

- **Small**
- **Deterministic**
- **Explainable**

---

## 1. Framing / Elevator Pitch

> “I built a toy ‘locked room’ scenario in Neo4j where an agent has to escape.  
> The world (room, door, window, agent) lives as a knowledge graph.  
> The agent has skills like `peek_door`, `try_door`, `go_window`.  
> A Python runner reads that graph, maintains an explicit belief about the door lock,  
> and chooses actions that trade off **information gain** vs **escaping fast**.  
> Each run writes an episode trace back into Neo4j, so the graph becomes both  
> **world model** and **procedural memory**.”

**Demoable in 5–10 minutes**:

- Run: `python runner.py --door-state unlocked`  
- Run: `python runner.py --door-state locked`  
- Show the traces and the graph in Neo4j Browser.

---

## 2. System Goals & Non-Goals

### 2.1 Goals

1. **Concrete & runnable**

   - `python runner.py` connects to Neo4j.
   - It runs **2 scenarios** (door locked / door unlocked).
   - Prints clear traces to the console.
   - You can open Neo4j Browser and see:
     - World graph
     - Episode + steps for each run.

2. **Graph-first**

   - World entities, skills, and episodes all live as **nodes and relationships**.
   - No “mystery world” hidden only in Python code.
   - Code handles **control & scoring**, graph holds **structure & memory**.

3. **Active-inference-shaped behaviour**

   - The agent keeps a belief `P(door_unlocked)` in memory.
   - Actions are chosen based on:
     - Expected goal value
     - Expected information gain
     - Simple action cost
   - Observations update the belief.
   - Behaviour pattern:
     - **Uncertain → explore** (`peek_door`)
     - **Confident → exploit** (`try_door` / `go_window`)

4. **Procedural memory**

   - Each run creates an `:Episode` node.
   - Each time step is a `:Step` node with:
     - Selected skill
     - Observation
     - Belief before & after
   - Linked together so you can inspect the run afterwards.

5. **Extensible**

   - Easy to add **more rooms, tools, skills** by editing the graph.
   - Easy to imagine:
     - additional state variables
     - additional “MacGyver” actions.

### 2.2 Non-Goals (for v1 only)

- **No** full variational calculus or factor graphs.
  - We approximate “free energy” with a simple scoring:
    - `score = α·GoalValue + β·InfoGain − γ·Cost`
- **No** multi-agent coordination.
- **No** large world map.
  - 1 room, 1 door, 1 window is enough.
- **No** LLM integration in v1 code.
  - LLMs stay out of the runtime; they can *explain* or *design* skills later, but v1 is pure Python+Neo4j.

---

## 3. Domain: The Locked Room “MacGyver” Scenario

We model a tiny **MacGyver-style** escape situation:

- One **room** (`Room A`).
- One **door** (may be `locked` or `unlocked`).
- One **window** (always usable to escape, but treated as “slower / less ideal”).
- One **agent** (`MacGyverBot`).
- The agent has **skills**:
  - `peek_door` – sense skill; reveals if the door is locked/unlocked.
  - `try_door` – attempt to open the door.
  - `go_window` – go to the window and escape.

We support two **scenarios**:

1. **Scenario A – Door unlocked**
2. **Scenario B – Door locked**

The **true door state** is **not** directly known to the agent at the start:

- The world has a “ground truth” door lock status (`locked` or `unlocked`).
- The agent has a **belief** `p_unlocked` (starts at 0.5).

Each **episode**:

1. Agent selects a skill based on current belief.
2. Environment returns an **observation**.
3. Agent updates belief given that observation.
4. Log the step into the graph.
5. Stop when the agent escapes (door or window) or hits `MAX_STEPS`.

---

## 4. Architecture Overview

Three layers working together:

1. **Neo4j Graph Layer**

   - Stores:
     - World entities (`Agent`, `Place`, `Object`, `StateVar`)
     - Skills (`Skill`)
     - Observations (`Observation`)
     - Episodes and steps (`Episode`, `Step`, relationships)
     - Initial belief (`Belief` node)
   - You can inspect and query it with Cypher.

2. **Python Runtime Layer**

   - Connects to Neo4j (official `neo4j` driver).
   - Reads world/skill definitions.
   - Maintains local belief `p_unlocked`.
   - Applies scoring to choose a skill.
   - Simulates the environment’s response (observation).
   - Updates belief and writes episode/steps back to Neo4j.

3. **CLI / Demo Layer**

   - `runner.py` accepts arguments:
     - `--door-state locked|unlocked`
     - maybe `--max-steps` etc.
   - Runs the episode, prints a human-readable trace.
   - Designed to be demoed live.

---

## 5. Neo4j Graph Model

Think of 3 conceptual subgraphs:

1. **World graph** – what exists in the environment.
2. **Procedural graph** – what actions exist.
3. **Episode graph** – what happened in a specific run.

### 5.1 Node Labels (Conceptual Model)

You **do not** need to instantiate all of these for v1.  
We explicitly mark **v1 required** vs **optional**.

#### Core Domain Nodes

- `:Agent` **(v1 required)**
  - Example: `{name: "MacGyverBot"}`
- `:Place` **(v1 required)**
  - Example: `{name: "Room A"}`
- `:Object` **(v1 required)**
  - Examples:
    - `{name: "Door", type: "door"}`
    - `{name: "Window", type: "window"}`
- `:StateVar` **(v1 required)**
  - Example:
    - `{name: "DoorLockState", domain: ["locked", "unlocked"]}`

*(Optional for later)*

- `:Property` – explicit state facts (e.g. “breakable”, “flammable”)
- `:Scenario` – to tag different initial conditions.

#### Procedural Nodes

- `:Skill` **(v1 required)**
  - Example:
    - `{name: "peek_door", cost: 1.0, kind: "sense"}`
    - `{name: "try_door", cost: 1.5, kind: "act"}`
    - `{name: "go_window", cost: 2.0, kind: "act"}`

*(Optional v2+)*

- `:Condition` – predicates like `door_locked`, `has_crowbar`.
- `:Effect` – state changes like `door_unlocked`, `escape_via_window`.

#### Beliefs & State

- `:Belief` **(v1 required)**
  - Example: `{p_unlocked: 0.5}`
  - One node per agent/statevar pair is enough for v1.

#### Episode / Memory Nodes

- `:Episode` **(v1 required)**
  - Example:
    - `{id: "episode-uuid", door_state: "locked", started_at: "...", scenario: "locked"}`

- `:Step` **(v1 required)**
  - Example:
    - `{index: 0, p_unlocked_before: 0.5, p_unlocked_after: 0.95}`

- `:Observation` **(v1 required)**
  - Examples:
    - `{name: "obs_door_locked"}`
    - `{name: "obs_door_unlocked"}`
    - `{name: "obs_door_opened"}`
    - `{name: "obs_window_escape"}`

*(Optional v2+)*

- `:SkillStats` – aggregated stats per skill / context.

### 5.2 Relationships (Conceptual)

#### World Structure

- `(agent:Agent)-[:LOCATED_IN]->(room:Place)`
- `(object:Object)-[:LOCATED_IN]->(room:Place)`
- *(later)* `(place1:Place)-[:CONNECTED_TO {via:"door"}]->(place2:Place)`

#### Beliefs

- `(agent)-[:HAS_BELIEF]->(belief:Belief)`
- `(belief)-[:ABOUT]->(state:StateVar)`

#### Skills and Targets

- `(skill:Skill)-[:ACTS_ON]->(target:Object|Place)`
  - e.g. `peek_door` and `try_door` act on `Door`
  - `go_window` acts on `Window`

*(Optional v2+ – not required in v1 code)*

- `(skill)-[:REQUIRES_CONDITION]->(condition:Condition)`
- `(condition)-[:ABOUT]->(Object|StateVar)`
- `(skill)-[:YIELDS_EFFECT]->(effect:Effect)`
- `(effect)-[:UPDATES]->(state:StateVar)`
- `(effect)-[:EMITS_OBSERVATION]->(obs:Observation)`

#### Episode Log

- `(episode:Episode)-[:HAS_STEP]->(step:Step)`
- `(step)-[:PERFORMED_BY]->(agent:Agent)`
- `(step)-[:USED_SKILL]->(skill:Skill)`
- `(step)-[:OBSERVED]->(obs:Observation)`
- *(Optional)* `(step)-[:NEXT]->(nextStep:Step)`

### 5.3 v1 Minimal Concrete Graph

For **v1 implementation**, use this minimal graph setup.

#### Nodes

```cypher
CREATE
  (agent:Agent {name: "MacGyverBot"}),

  (room:Place {name: "Room A"}),

  (door:Object   {name: "Door",   type: "door"}),
  (window:Object {name: "Window", type: "window"}),

  (doorLock:StateVar {name: "DoorLockState", domain: ["locked","unlocked"]}),

  (belief:Belief {p_unlocked: 0.5}),

  (obsLocked:Observation        {name: "obs_door_locked"}),
  (obsUnlocked:Observation      {name: "obs_door_unlocked"}),
  (obsDoorOpened:Observation    {name: "obs_door_opened"}),
  (obsWindowEscape:Observation  {name: "obs_window_escape"}),

  (peekDoor:Skill {name: "peek_door", cost: 1.0, kind: "sense"}),
  (tryDoor:Skill  {name: "try_door",  cost: 1.5, kind: "act"}),
  (goWindow:Skill {name: "go_window", cost: 2.0, kind: "act"});
```

#### Relationships

```cypher
// Locations
CREATE
  (agent)-[:LOCATED_IN]->(room),
  (door)-[:LOCATED_IN]->(room),
  (window)-[:LOCATED_IN]->(room);

// Belief link
CREATE
  (agent)-[:HAS_BELIEF]->(belief),
  (belief)-[:ABOUT]->(doorLock);

// Skills and targets
CREATE
  (peekDoor)-[:ACTS_ON]->(door),
  (tryDoor)-[:ACTS_ON]->(door),
  (goWindow)-[:ACTS_ON]->(window);
```

**Important for v1:**

* **Do NOT** encode door’s *true* lock state in the graph.
  The *true* door state (`locked`/`unlocked`) is supplied **at runtime** via config/CLI.
* Leave the more detailed `Condition`/`Effect` modelling for **later versions**.

---

## 6. Python Implementation Design

### 6.1 Repo Layout

```text
neo-macgyver-demo/
  README.md
  CONTEXT_AND_GUIDANCE.md       # separate doc you already have
  requirements.txt
  cypher_init.cypher            # creates the minimal graph above
  config.py                     # Neo4j + scenario config
  graph_model.py                # read/write helpers for Neo4j
  scoring.py                    # scoring & entropy
  agent_runtime.py              # agent loop & belief updates
  runner.py                     # CLI entry point
```

### 6.2 `requirements.txt`

```text
neo4j
rich        # optional, for nicer console output
```

---

## 7. Module-by-Module Responsibilities

### 7.1 `config.py`

Purpose:

* Hold configuration constants and environment-sourced settings.

Contents (v1):

* Neo4j connection config:

  ```python
  NEO4J_URI = "bolt://localhost:7687"
  NEO4J_USER = "neo4j"
  NEO4J_PASSWORD = "password"  # or read from os.environ
  ```

* Scenario config defaults:

  ```python
  DEFAULT_DOOR_STATE = "locked"   # "locked" or "unlocked"
  MAX_STEPS = 5
  INITIAL_P_UNLOCKED = 0.5
  ```

### 7.2 `graph_model.py`

Purpose:

* **Simple, explicit** helper functions for graph I/O.
* No decision logic; only query/update Neo4j.

Implement functions like:

```python
from neo4j import GraphDatabase
from typing import List, Dict, Any

def get_agent(tx, agent_name: str) -> Dict[str, Any]:
    # Return {id, name} for the agent node

def get_initial_belief(tx, agent_id: int, statevar_name: str) -> float:
    # Return p_unlocked from the Belief node

def get_skills(tx) -> List[Dict[str, Any]]:
    # Return all Skill nodes with their basic properties

def get_skill_by_name(tx, name: str) -> Dict[str, Any]:
    # Utility if needed

def create_episode(tx, agent_id: int, door_state: str) -> int:
    # Create :Episode node and return its ID

def log_step(
    tx,
    episode_id: int,
    index: int,
    skill_name: str,
    obs_name: str,
    p_before: float,
    p_after: float
) -> int:
    # Create :Step node, link it to Episode, Agent, Skill, Observation
```

**Constraints for implementation agent:**

* Use **parameterised Cypher** (no string concatenation with raw values).
* Keep each function **short and single-purpose**.
* If a query returns no rows for something that *must* exist (e.g. `Agent`), raise a clear error.

### 7.3 `scoring.py`

Purpose:

* Implement **entropy**, **expected goal value**, **expected info gain**, and a combined **score**.
* Encapsulate all “Active-inference-ish” logic here.

Implement:

```python
import math

def entropy(p: float) -> float:
    """Bernoulli entropy in bits."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    q = 1.0 - p
    return - (p * math.log2(p) + q * math.log2(q))
```

Then:

```python
def expected_goal_value(skill_name: str, p_unlocked: float) -> float:
    REWARD_ESCAPE = 10.0
    PENALTY_FAIL = 4.0
    SLOW_PENALTY = 2.0

    if skill_name == "try_door":
        # High payoff if unlocked; penalty otherwise
        return p_unlocked * REWARD_ESCAPE - (1.0 - p_unlocked) * PENALTY_FAIL
    elif skill_name == "go_window":
        # Always works but slightly worse (slow/inelegant)
        return REWARD_ESCAPE - SLOW_PENALTY
    elif skill_name == "peek_door":
        # Looking alone doesn't escape
        return 0.0
    else:
        return 0.0
```

And:

```python
def expected_info_gain(skill_name: str, p_unlocked: float) -> float:
    if skill_name == "peek_door":
        return entropy(p_unlocked)  # max when p ~ 0.5
    else:
        return 0.0
```

Finally, the **combined score**:

```python
def score_skill(
    skill: dict,
    p_unlocked: float,
    alpha: float = 1.0,
    beta: float = 0.5,
    gamma: float = 0.1
) -> float:
    name = skill.get("name")
    cost = float(skill.get("cost", 1.0))

    goal = expected_goal_value(name, p_unlocked)
    info = expected_info_gain(name, p_unlocked)

    return alpha * goal + beta * info - gamma * cost
```

**Behavioural expectation:**

* When `p_unlocked ≈ 0.5`, `peek_door` should often win (info gain high).
* When `p_unlocked` is high (`≈ 0.9`), `try_door` should often win.
* When `p_unlocked` is very low (`≈ 0.1`), `go_window` should often win.

### 7.4 `agent_runtime.py`

Purpose:

* Implement the **agent’s thinking loop**.
* Maintain local belief `p_unlocked`.
* Select skills and simulate outcomes.

Define a class:

```python
from typing import List, Dict, Any
from neo4j import Driver
import scoring
import graph_model

class AgentRuntime:
    def __init__(self, driver: Driver, door_state: str, initial_p: float = 0.5):
        self.driver = driver
        self.door_state = door_state          # "locked" or "unlocked"
        self.p_unlocked = float(initial_p)

        # Optionally cache agent_id or other IDs here
```

Methods:

1. **Skill selection**

   ```python
   def select_skill(self, skills: List[Dict[str, Any]]) -> Dict[str, Any]:
       # Use scoring.score_skill to compute a score for each skill.
       # Return the dict with the highest score.
   ```

2. **Simulate skill outcome**

   ```python
   def simulate_skill(
       self,
       skill: Dict[str, Any]
   ) -> (str, float, bool):
       """
       Returns: (obs_name, p_after, escaped)
       """
   ```

   Rules for v1:

   * Get `name = skill["name"]`.
   * If `name == "peek_door"`:

     * If `door_state == "locked"`:

       * `obs_name = "obs_door_locked"`
       * `p_after = 0.05`
     * If `door_state == "unlocked"`:

       * `obs_name = "obs_door_unlocked"`
       * `p_after = 0.95`
     * `escaped = False`
   * If `name == "try_door"`:

     * If `door_state == "unlocked"`:

       * `obs_name = "obs_door_opened"`
       * `p_after = 0.99`
       * `escaped = True`
     * If `door_state == "locked"`:

       * `obs_name = "obs_door_locked"`
       * `p_after = max(self.p_unlocked - 0.05, 0.01)`
       * `escaped = False`
   * If `name == "go_window"`:

     * `obs_name = "obs_window_escape"`
     * `p_after = self.p_unlocked`  (no info gain)
     * `escaped = True`

3. **Run an episode**

   ```python
   def run_episode(self, max_steps: int) -> None:
       """
       Or return episode_id, depending on design.
       """
   ```

   Pseudocode:

   * Open a Neo4j session.
   * Find the agent node.
   * Create an `:Episode` node with `door_state`.
   * For `index` in `0..max_steps-1`:

     * `p_before = self.p_unlocked`
     * Fetch all skills via `graph_model.get_skills`.
     * Choose best skill via `select_skill`.
     * Simulate outcome: `obs_name, p_after, escaped`.
     * Update `self.p_unlocked = p_after`.
     * Write a `:Step` node via `graph_model.log_step(...)`.
     * Print a readable line describing the step.
     * If `escaped`: break.

**Important constraints for implementation agent:**

* **Do not** perform random choices in v1.

  * Keep behaviour deterministic given `door_state` and initial `p_unlocked`.
* **Do not** modify the graph schema beyond what’s necessary.
* **Do not** assume objects exist without checking; fail clearly if missing.

### 7.5 `runner.py`

Purpose:

* CLI entry point.
* Wire everything together.

Behaviour:

1. Parse CLI flags:

   * `--door-state` (`locked` or `unlocked`)
   * `--max-steps` (optional; default from config)
2. Create Neo4j driver using `config.NEO4J_URI`, etc.
3. Optionally run `cypher_init.cypher` once (or instruct the user to run it separately).
4. Instantiate `AgentRuntime(driver, door_state, initial_p=config.INITIAL_P_UNLOCKED)`.
5. Call `run_episode(config.MAX_STEPS)`.
6. Print final outcome (`escaped via door` or `via window`).

Print trace lines like:

```text
Episode door_state=locked
Step 0: p_before=0.50, action=peek_door, observation=obs_door_locked, p_after=0.05
Step 1: p_before=0.05, action=go_window, observation=obs_window_escape, p_after=0.05
ESCAPED via window in 2 steps.
```

---

## 8. Active-Inference-ish Logic: Full v1 Summary

We approximate Active Inference as:

* Maintain belief `p_unlocked`.

* Score each action:

  ```text
  Score(a) = α * GoalValue(a) + β * InfoGain(a) - γ * Cost(a)
  ```

* Choose the action with the highest score.

* Update belief based on observation.

* Repeat.

Belief updates are **simple steps** (not full Bayesian), but they preserve the core idea:

* “Seeing the door is locked” → drastically reduce `p_unlocked`.
* “Seeing the door unlocked / opened” → drastically increase `p_unlocked`.
* “Escaping via window” → no new info about door lock.

This is enough to:

* Make `peek_door` attractive when uncertain.
* Make `try_door` attractive when confident.
* Make `go_window` attractive when pessimistic about door.

---

## 9. Implementation Process (Idiot-Proof Task List)

**For the coding LLM / engineer, do this in order:**

1. **Create repo** with the layout in §6.1.
2. **Write `requirements.txt`** as in §6.2.
3. **Write `cypher_init.cypher`**:

   * Delete all nodes/rels.
   * Create:

     * `Agent`, `Place`, `Door`, `Window`
     * `StateVar` DoorLockState
     * `Belief` (p_unlocked=0.5)
     * Skills, Observations
   * Create relationships:

     * `LOCATED_IN`
     * `HAS_BELIEF` / `ABOUT`
     * `ACTS_ON`
4. **Write `config.py`** with Neo4j URI + `DEFAULT_DOOR_STATE`, `MAX_STEPS`, `INITIAL_P_UNLOCKED`.
5. **Implement `graph_model.py`** with the helper functions in §7.2.
6. **Implement `scoring.py`** with entropy, expected goal, info gain, and score in §7.3.
7. **Implement `agent_runtime.py`** as in §7.4.
8. **Implement `runner.py`** as in §7.5.
9. **Test** via the plan in §10.
10. Once passing, **polish**:

    * Add pretty printing (optional).
    * Add comments/docstrings for clarity.

---

## 10. Test Plan & Success Criteria

### 10.1 Unit-Level Checks

You may implement as simple functions or manual checks.

1. **Entropy**

   * `entropy(0.0)` and `entropy(1.0)` should be `0.0`.
   * `entropy(0.5)` should be:

     * greater than `entropy(0.2)`
     * greater than `entropy(0.8)`

2. **Scoring**

   * At `p_unlocked = 0.5`:

     * `score(peek_door)` should be **higher** than `score(try_door)` and `score(go_window)` (info gain).
   * At `p_unlocked = 0.9`:

     * `score(try_door)` should be **highest**.
   * At `p_unlocked = 0.1`:

     * `score(go_window)` should be **highest**.

3. **Belief Updates**

   * After `peek_door` with `door_state="locked"`:

     * `p_unlocked` should become `≈0.05`.
   * After `peek_door` with `door_state="unlocked"`:

     * `p_unlocked` should become `≈0.95`.
   * After `try_door` with `door_state="unlocked"`:

     * `p_unlocked` should be ≈0.99 and `escaped=True`.

### 10.2 End-to-End Scenarios

**Scenario A – Door unlocked**

* Command:
  `python runner.py --door-state unlocked`

* Expected pattern (not necessarily exact, but similar):

  ```text
  Episode door_state=unlocked
  Step 0: ... action=peek_door   ... observation=obs_door_unlocked ... p_after≈0.95
  Step 1: ... action=try_door    ... observation=obs_door_opened   ... escaped=True
  ```

* Inspect Neo4j:

  ```cypher
  MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
  WHERE e.door_state = "unlocked"
  RETURN e, s ORDER BY s.index;
  ```

  Check:

  * Steps exist
  * Linked to correct `Skill` and `Observation`.

**Scenario B – Door locked**

* Command:
  `python runner.py --door-state locked`

* Expected pattern:

  ```text
  Episode door_state=locked
  Step 0: ... action=peek_door   ... observation=obs_door_locked   ... p_after≈0.05
  Step 1: ... action=go_window   ... observation=obs_window_escape ... escaped=True
  ```

* Neo4j inspection similar to Scenario A.

### 10.3 Negative / Guard Tests

* Agent **must not** always pick the same skill regardless of `p_unlocked`.
* If no `Agent` or `Skill` nodes are found, code should:

  * Raise a clear error, not crash mysteriously.
* The code **must not** rely on random seeds for core decisions in v1.

### 10.4 Success Criteria (Summary)

The demo is considered **successful** if:

1. You can **run both scenarios** from the CLI.
2. The agent’s behaviour matches the **explore → exploit** intuition.
3. Episodes and steps are **visible and interpretable** in Neo4j.
4. The codebase is **small, readable, and obviously extensible**.

---

## 11. Extension Hooks (For Conversation & Future Work)

You don’t implement these in v1, but you can talk about them.

1. **MacGyver Upgrade**

   * Add more objects: `Battery`, `Wire`, `MetalBar`, etc.
   * Add skills like `combine_tools`, `craft_hook`, `jam_door`.
   * Represent tool combinations and preconditions in the graph.

2. **Contextual Skill Stats**

   * Add `:SkillStats` nodes attached to `:Skill`.
   * Track `uses`, `successes`, `avg_steps` in certain contexts.
   * Use them to bias skill scoring in future episodes.

3. **Richer Hidden State**

   * More `:StateVar`s: `AlarmStatus`, `GuardDistance`, etc.
   * Move closer to a **factorised generative model**.

4. **LLM Integration (Phase 2)**

   * Keep Neo4j as **ground truth**.
   * Use LLMs to:

     * Propose new skills and subgraphs.
     * Provide natural language explanations for episodes.

5. **Real-World Domain Swap**

   * Replace “locked room” with:

     * Data pipeline repair scenario
     * Server outage triage
     * Customer onboarding flows
   * Same pattern: graph of resources, skills, and hidden states;
     agent acts to reduce uncertainty and restore service.

---

**End of Enhanced Specification**