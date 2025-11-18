# CONTEXT_AND_GUIDANCE.md  
Neo4j "MacGyver" Active Inference Demo

You (the coding model) are implementing a **small, concrete demo** that shows how:
- a **knowledge graph** can represent a simple world,
- an **agent** maintains and updates **beliefs** about hidden state,
- the agent chooses **actions** to reduce uncertainty or reach a goal
- and each run is written back as **procedural memory** into the same graph.

This is a *showcase* for Active Inference + Knowledge Graphs + Procedural Memory,  
not a full research implementation.

---

## 1. Domain: The Locked Room MacGyver Demo

We are modelling a tiny “MacGyver-style” situation:

- There is a **room**.
- There is a **door** that may be **locked or unlocked** (hidden state).
- There is a **window** that can always be used to escape, but is “slower / less ideal”.
- There is an **agent** in the room (MacGyverBot).
- The agent has **actions** (skills) like:
  - `peek_door` – look at the door to see if it’s locked or unlocked.
  - `try_door` – try to open the door.
  - `go_window` – go to the window and escape.

We will support two scenarios:

1. **Scenario A – Door actually unlocked**
2. **Scenario B – Door actually locked**

The actual door state is part of the **ground truth environment**, not directly known
to the agent. The agent starts with **uncertain belief** (e.g. 50/50).

In each run (episode), the agent:

1. Chooses an action based on its current belief.
2. Observes an outcome (e.g. “door is locked”).
3. Updates its belief.
4. Repeats until it escapes (via door or window) or hits a max step count.

The whole point is to show:
> The agent’s choice of action is shaped by its beliefs and the expected
> information/goal value of each action.

---

## 2. Techniques We Are Using (and Why)

### 2.1 Knowledge Graph (Neo4j)

We represent the world and behaviours as a **graph** because:

- It’s a natural way to model:
  - Places, objects, agents (nodes)
  - Relationships (edges) like `LOCATED_IN`, `ACTS_ON`, etc.
- It allows us to:
  - **Visualise** the environment and past episodes.
  - **Extend** the domain simply by adding nodes/edges.
  - Use Neo4j’s Cypher to explore and debug.

The graph will contain:

- World structure (Room, Door, Window, Agent)
- Action (Skill) definitions
- State variables and beliefs
- Episode and step logs (procedural memory)

### 2.2 Active Inference–shaped Decision-Making (Simplified)

We do **not** implement full Friston-style Active Inference math.  
We implement a **simple, understandable approximation** that captures its flavour:

- The agent maintains a **belief** about a hidden state:
  - Here: `P(door_unlocked)` ∈ [0, 1].
- Each action is scored by a simple function:

```text
Score(action) = α * ExpectedGoalValue
            + β * ExpectedInfoGain
            - γ * Cost
```

* **Expected goal value**: “How likely is this action to get me out, and how good/bad is that?”
* **Expected information gain**: “How much will this action reduce uncertainty about the door?”
* **Cost**: “How expensive / risky is this action?”

Examples:

* `peek_door`:

  * High information gain when belief is uncertain (p ≈ 0.5).
  * Little direct goal value.
* `try_door`:

  * High goal value when `p_unlocked` is high.
* `go_window`:

  * Reliable escape (moderate goal value), no information gain.

This gives us **Active Inference behaviour** in miniature:

> When uncertain, **explore** (peek).
> When confident, **exploit** (try door or go window).

### 2.3 Procedural Memory

Every run writes back into Neo4j:

* An `:Episode` node for that run.
* A series of `:Step` nodes:

  * Which skill was chosen
  * What was observed
  * Snapshot of belief (e.g. `p_unlocked`)

This gives:

* A trace we can inspect in Neo4j Browser.
* A foundation to later accumulate statistics about skills in different contexts.

---

## 3. Key Components of the Solution

### 3.1 Graph Model (Neo4j Schema)

We use these labels (you can implement a minimal subset):

**World & state**

* `:Agent` – the agent node, e.g. `{name: "MacGyverBot"}`
* `:Place` – e.g. `{name: "Room A"}`
* `:Object` – e.g. `{name: "Door"}`, `{name: "Window"}`
* `:StateVar` – e.g. `{name: "DoorLockState"}`

**Beliefs**

* `:Belief` – agent’s explicit belief for a state variable, e.g. `{p_unlocked: 0.5}`

**Skills / Actions**

* `:Skill` – actions the agent can choose, e.g.:

  * `{name: "peek_door", kind: "sense", cost: 1.0}`
  * `{name: "try_door", kind: "act", cost: 1.5}`
  * `{name: "go_window", kind: "act", cost: 2.0}`

**Observations / Effects** (v1 can be simpler)

* `:Observation` – what the agent perceives, e.g.:

  * `obs_door_locked`, `obs_door_unlocked`, `obs_door_opened`, `obs_window_escape`

**Episodes**

* `:Episode` – one simulation run, e.g. `{id: "...", door_state: "locked"}`
* `:Step` – one action+observation, e.g. `{index: 0, p_unlocked_before: 0.5, p_unlocked_after: 0.2}`

**Relationships (minimum set)**

* `(agent:Agent)-[:LOCATED_IN]->(room:Place)`

* `(door:Object)-[:LOCATED_IN]->(room)`

* `(window:Object)-[:LOCATED_IN]->(room)`

* `(agent)-[:HAS_BELIEF]->(belief:Belief)`

* `(belief)-[:ABOUT]->(doorLock:StateVar)`

* `(skill:Skill)-[:ACTS_ON]->(target:Object)`
  e.g. `peek_door` and `try_door` act on `Door`, `go_window` acts on `Window`.

* `(episode:Episode)-[:HAS_STEP]->(step:Step)`

* `(step)-[:PERFORMED_BY]->(agent)`

* `(step)-[:USED_SKILL]->(skill)`

* `(step)-[:OBSERVED]->(obs:Observation)`

You can keep **effects and conditions** implicit in code for v1 (simpler):

* e.g. store the mapping “if skill==peek_door and door_state==locked → observation=obs_door_locked”.

We do NOT need full-blown `:Condition` and `:Effect` nodes in v1 unless you want to — keep it lean.

---

## 4. Why This Arrangement of Components?

We want a design that:

1. **Clearly separates concerns**:

   * **Graph**: world state, skills, and memory.
   * **Python runtime**: beliefs, scoring, control loop.
2. **Makes the demo explainable**:

   * We can show the graph in Neo4j browser:

     * Here is the world.
     * Here is the episode.
   * We can show simple, readable code for scoring and belief updates.
3. **Is easy to extend**:

   * Add more rooms, tools, and skills by adding nodes and relationships.
   * Eventually move more logic from code into the graph (e.g. explicit preconditions/effects).
4. **Is safe for a coding model**:

   * Limited complexity.
   * Clear function boundaries.
   * Simple numeric logic.

---

## 5. Implementation Guidance (Idiot-Proof for the Coding Model)

### 5.1 Overall Repo Layout

Please implement something like this:

```text
neo-macgyver-demo/
  README.md
  CONTEXT_AND_GUIDANCE.md       # this file
  requirements.txt
  cypher_init.cypher            # sets up the initial graph
  config.py                     # Neo4j connection / scenario config
  graph_model.py                # read/write utils for Neo4j
  scoring.py                    # scoring & belief update functions
  agent_runtime.py              # control loop for agent
  runner.py                     # entry point CLI
```

### 5.2 Technology Choices

* **Language**: Python 3
* **Neo4j driver**: use the official `neo4j` Python driver.
* No need for web frameworks, ORMs, or anything heavy.

### 5.3 Step-by-step Implementation Plan

**Step 1 – Setup Neo4j and `cypher_init.cypher`**

* `cypher_init.cypher` should:

  * DELETE all existing nodes/relationships (for a clean slate).
  * CREATE:

    * 1 `:Agent` node
    * 1 `:Place` node
    * 2 `:Object` nodes (`Door`, `Window`)
    * 1 `:StateVar` (`DoorLockState`)
    * 1 `:Belief` node linked to the agent (`HAS_BELIEF`) and to the state var (`ABOUT`)
    * 3 `:Skill` nodes (`peek_door`, `try_door`, `go_window`)
    * 4 `:Observation` nodes (locked, unlocked, door opened, window escape)
  * Create the basic location and skill relations:

    * `LOCATED_IN`, `HAS_BELIEF`, `ABOUT`, `ACTS_ON`.

**Important**:
Ground truth door state (locked/unlocked) will be passed to the Python runner as a configuration parameter (not stored in the graph for v1).

---

**Step 2 – `config.py`**

Provide:

* Neo4j URI, user, password (read from env vars is ideal).
* Scenario settings, e.g.:

  ```python
  DOOR_STATE = "locked"  # or "unlocked"
  MAX_STEPS = 5
  ```

---

**Step 3 – `graph_model.py`**

Implement small helper functions, for example:

* `get_agent(tx, name) -> dict with id and properties`
* `get_initial_belief(tx, agent_id, statevar_name) -> float p_unlocked`
* `get_skills_for_agent_in_place(tx, agent_id) -> list[dict]`

  * For v1 you can just return all `:Skill` nodes.
* `create_episode(tx, agent_id, door_state) -> episode_id`
* `log_step(tx, episode_id, step_index, skill_name, obs_name, p_before, p_after)`

Constraints:

* Keep functions **small and specific**.
* Do not embed decision logic here – just graph IO.
* Use explicit Cypher queries; no dynamic string-building from untrusted input.

---

**Step 4 – `scoring.py`**

Implement:

* `entropy(p)` for a Bernoulli variable.
* `expected_goal_value(skill_name, p_unlocked)` – simple heuristics:

  * `try_door`: higher when `p_unlocked` is high.
  * `go_window`: constant moderate value.
  * `peek_door`: ~0.
* `expected_info_gain(skill_name, p_unlocked)`:

  * `peek_door`: use entropy(p_unlocked)
  * others: 0.
* `score_skill(skill, p_unlocked, alpha=1.0, beta=0.5, gamma=0.1)`
  where `skill` is a dict containing at least `name` and `cost`.

Make sure:

* Higher score = more desirable.
* The function is deterministic and easy to read.

---

**Step 5 – `agent_runtime.py`**

Implement:

* Class `AgentRuntime` with fields:

  * `p_unlocked` (float belief)
  * `door_state` (string `"locked"` or `"unlocked"`, from config)
  * `session` (Neo4j driver session)

Methods:

1. `select_skill(skills) -> dict`

   * Use `scoring.score_skill` to pick the best skill.
2. `simulate_skill(skill) -> (obs_name: str, p_after: float, escaped: bool)`

   * Use `door_state` + `skill["name"]` to decide:

     * If `peek_door`:

       * If `door_state=="locked"` → observation `obs_door_locked`, update belief to a low value (e.g. 0.05).
       * If `door_state=="unlocked"` → observation `obs_door_unlocked`, update belief to a high value (e.g. 0.95).
       * `escaped=False`.
     * If `try_door`:

       * If `door_state=="unlocked"` → observation `obs_door_opened`, `p_after` near 0.99, `escaped=True`.
       * If `door_state=="locked"` → observation `obs_door_locked` or `obs_door_opened` (fail), `escaped=False`, maybe slightly lower `p_unlocked`.
     * If `go_window`:

       * Always `obs_window_escape`, `escaped=True`, `p_after = p_before` (no info).
3. `run_episode(max_steps) -> episode_id`

   * Create an Episode node.
   * Loop up to `max_steps`:

     * Query available skills.
     * Select skill.
     * Simulate outcome.
     * Log step to graph.
     * Update `p_unlocked`.
     * Stop if `escaped`.

---

**Step 6 – `runner.py`**

* Parse CLI args (e.g. `--door-state locked|unlocked`).
* Establish Neo4j driver.
* Optionally run `cypher_init.cypher` at start (or assume user already did).
* Instantiate `AgentRuntime` with:

  * The session
  * Initial belief (`0.5`)
  * Door state from arg.
* Call `run_episode(MAX_STEPS)`.
* Print a clear trace of:

  * Step index
  * Skill chosen
  * Observation
  * p_unlocked before/after
* Exit.

---

## 6. Test Plan & Success Criteria

We want to be very clear about what “done” looks like.

### 6.1 Unit-like tests (logic)

You can add lightweight tests or just manual checks:

1. **Entropy function**

   * `entropy(0)` and `entropy(1)` should be 0.
   * `entropy(0.5)` should be maximal (> entropy(0.2) and entropy(0.8)).

2. **Scoring behaviour**

   * At `p_unlocked = 0.5`, `peek_door` should score highest due to info gain.
   * At `p_unlocked = 0.9`, `try_door` should score higher than `peek_door`.
   * At `p_unlocked = 0.1`, `go_window` should score higher than `try_door`.

3. **Belief updates**

   * After observing `obs_door_locked` from `peek_door`, `p_unlocked` should be low (e.g. 0.05).
   * After observing `obs_door_unlocked`, `p_unlocked` should be high (e.g. 0.95).

### 6.2 Scenario tests (end-to-end)

**Scenario A – Door unlocked**

* Run: `python runner.py --door-state unlocked`
* Expected behaviour:

  * Step 1: likely `peek_door`
  * Step 2: `try_door`
  * Escape via door in ≤ 3 steps.
* In Neo4j:

  * There is an `:Episode` node with `door_state = "unlocked"`.
  * It has 2–3 `:Step` nodes linked via `HAS_STEP`.
  * Steps reference the correct `:Skill` and `:Observation` nodes.

**Scenario B – Door locked**

* Run: `python runner.py --door-state locked`
* Expected behaviour:

  * Step 1: `peek_door`
  * Step 2: `go_window`
  * Escape via window in ≤ 3 steps.
* Neo4j checks similar to Scenario A but with:

  * Final observation `obs_window_escape`.

If behaviour differs slightly (e.g. the agent sometimes skips peek), that is acceptable **as long as** the scoring logic clearly reflects the intended trade-offs and the demo still showcases “uncertainty → information-seeking behaviour”.

### 6.3 Negative tests (what it should NOT do)

* The agent **must not** ignore belief:

  * It should not always choose the same skill regardless of `p_unlocked`.
* The environment logic **must not** be entirely hard-coded in a way that contradicts the graph:

  * Objects and skills should exist as nodes in Neo4j.
* The code **must not** silently fail if Neo4j is empty:

  * It should provide a clear error (“No Agent found” or “No Skills found”) instead.

---

## 7. Additional Guidance & “Gotchas”

### 7.1 Keep It Simple and Readable

* This is a **demo**, not a microservice.
* Prefer **straightforward code** over clever abstractions.
* Small functions, clear names.

### 7.2 Make Traces Human-Friendly

* When printing steps in `runner.py`, show something like:

  ```text
  Episode door_state=locked
  Step 0: p_unlocked_before=0.50, action=peek_door, observation=obs_door_locked, p_after=0.05
  Step 1: p_unlocked_before=0.05, action=go_window, observation=obs_window_escape, p_after=0.05
  ESCAPED via window in 2 steps.
  ```

This makes it very easy to demo.

### 7.3 Leave Extension Hooks

* You can add TODO comments for future extensions:

  * Additional state variables.
  * More tools and skills.
  * Recording simple stats on `:Skill` nodes (e.g. `uses`, `successes`).

### 7.4 Avoid Over-Engineering

Do **not**:

* Introduce an RL library.
* Introduce complex factor graph libraries.
* Implement a general POMDP solver.

Those are out of scope.
We just need a **small, rational, graph-backed example**.

---

## 8. Success Summary

We consider the implementation successful if:

1. **Setup**: Running `cypher_init.cypher` creates a small, inspectable graph with:

   * Agent, Room, Door, Window, StateVar, Belief, Skills, Observations.
2. **Runner**: Running `runner.py` with `--door-state unlocked` and `--door-state locked`:

   * Produces believable traces matching the “peek when uncertain, exploit when confident” pattern.
   * Creates `:Episode` and `:Step` nodes with correct relationships in Neo4j.
3. **Explainability**: The code and graph together make it easy to explain:

   * What the agent believed.
   * Why it picked each action.
   * How observations changed its beliefs.
4. **Extensibility**: It is straightforward to see how to add:

   * More rooms and objects.
   * More skills and more complex situations.

If all of the above hold, we have a **solid demo** of:

> Active-inference-shaped behaviour + procedural memory + knowledge graph
> in a small, MacGyver-flavoured locked-room scenario.