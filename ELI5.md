# ELI5: MacGyver Active Inference Demo

**Explain Like I'm 5** - A simple guide to understanding this project

---

## 🤔 What Is This?

Imagine you're locked in a room and want to get out. There are two ways out:
1. **A door** - might be locked or unlocked (you don't know!)
2. **A window** - always works, but it's harder and slower

This project is a **robot brain** that figures out the smartest way to escape.

The special part? The robot:
- **Thinks** about what it believes (is the door locked?)
- **Learns** by looking around
- **Remembers** everything it tried before
- **Chooses** actions that either help it escape OR help it learn more

### The Two Big Ideas

**1. Active Inference** 🧠
- The robot doesn't just act randomly
- It balances two things:
  - "Will this help me escape?" (exploitation)
  - "Will this help me learn?" (exploration)
- When uncertain, it gathers information
- When confident, it goes for the goal

**2. Procedural Memory** 📝
- Everything the robot does is saved in a "memory graph"
- You can look back and see what it tried
- You can analyze why it made each choice
- The memory helps it get smarter over time

---

## 🎯 What Does It Do?

### The Scenario

The robot (named "MacGyverBot") starts in a room with:
- A **door** (unknown if locked or unlocked)
- A **window** (always works)
- **Initial belief**: "50/50 chance the door is unlocked"

### Available Actions

1. **Peek at door** 🔍
   - Cost: Low (1.0)
   - Effect: Learn if door is locked or unlocked
   - Doesn't escape, but gains information

2. **Try the door** 🚪
   - Cost: Medium (1.5)
   - Effect: If unlocked → escape! If locked → get stuck
   - Risky if you're not sure

3. **Use the window** 🪟
   - Cost: High (2.0)
   - Effect: Always escapes, but slow and difficult
   - Safe but not ideal

### What The Robot Does

**When door is unlocked:**
1. Peek at door (uncertain → need info)
2. See it's unlocked (belief goes 50% → 85%)
3. Try the door (confident → go for it!)
4. Escape! ✅ (2 steps, optimal)

**When door is locked:**
1. Peek at door (uncertain → need info)
2. See it's locked (belief goes 50% → 15%)
3. Use window (confident door won't work)
4. Escape! ✅ (2 steps, optimal)

---

## ⚙️ How Does It Do It?

### The Brain (Active Inference)

Think of the robot's brain as constantly asking three questions about each action:

#### 1. "Will this help me reach my goal?" (Goal Value)
- Trying an unlocked door: +10 points (escape!)
- Trying a locked door: -3 points (ouch, stuck)
- Using window: +6 points (escape but slow)
- Peeking: 0 points (doesn't escape)

#### 2. "Will this teach me something?" (Information Gain)
- When 50/50 uncertain: Peeking is very valuable (+6 points)
- When already know: Peeking is useless (0 points)
- This uses "entropy" - a math way to measure uncertainty

#### 3. "How much does this cost?" (Cost)
- Peek: -0.3 points
- Try door: -0.45 points
- Window: -0.6 points

### The Decision Formula

```
Score = (1.0 × Goal Value) + (6.0 × Info Gain) - (0.3 × Cost)
```

**Higher score = better choice**

At the start (50/50 uncertain):
- Peek: 0 + 6.0 - 0.3 = **5.7** ⭐ (wins!)
- Try door: 3.5 + 0 - 0.45 = **3.05**
- Window: 6.0 + 0 - 0.6 = **5.4**

After peeking (85% sure unlocked):
- Peek: 0 + 2.8 - 0.3 = **2.5**
- Try door: 8.7 + 0 - 0.45 = **8.25** ⭐ (wins!)
- Window: 6.0 + 0 - 0.6 = **5.4**

### The Memory (Knowledge Graph)

Everything is stored in a **Neo4j graph database**:

```
World:
  (Agent: MacGyverBot) → LOCATED_IN → (Room A)
  (Door) → LOCATED_IN → (Room A)
  (Window) → LOCATED_IN → (Room A)

Skills:
  (Skill: peek_door) - cost: 1.0
  (Skill: try_door) - cost: 1.5
  (Skill: go_window) - cost: 2.0

Memory (after running):
  (Episode #1) → HAS_STEP → (Step 0) → USED_SKILL → (peek_door)
                                     → OBSERVED → (obs_door_unlocked)
               → HAS_STEP → (Step 1) → USED_SKILL → (try_door)
                                     → OBSERVED → (obs_door_opened)
```

You can query this memory later to analyze what happened!

---

## 🎓 Why Does It Do It That Way?

### Active Inference Philosophy

Real intelligence isn't just about achieving goals - it's about:
1. **Understanding the world** (building models)
2. **Reducing uncertainty** (learning)
3. **Acting efficiently** (not wasting resources)

This is how humans and animals actually work:
- You don't just grab food randomly
- You explore to learn where food is
- Then you exploit that knowledge efficiently

### The Math Behind It

**Entropy** measures uncertainty:
- At 50/50: Maximum uncertainty = 1.0
- At 85/15: Low uncertainty = 0.61
- At 100/0: No uncertainty = 0.0

When uncertainty is high, the robot values **information gain** more than **goal achievement**.

### Graph Database for Memory

Why Neo4j instead of a regular database?
1. **Natural representation**: "Agent USED_SKILL peek_door" is intuitive
2. **Queryable**: Can ask complex questions ("What happened when door was locked?")
3. **Visualizable**: Can see the whole episode as a graph
4. **Extensible**: Easy to add more rooms, tools, skills

---

## 🚀 How To Run / Test It

### Quick Start (3 commands)

```bash
# 1. Start Neo4j
make neo4j-start

# 2. Run unlocked scenario
python runner.py --door-state unlocked

# 3. Run locked scenario
python runner.py --door-state locked
```

### Expected Output (Unlocked)

```
╭────────────────────────────────────────╮
│ MacGyver Active Inference Demo         │
│ Ground Truth: Door is unlocked         │
│ Initial Belief: p(unlocked) = 0.50     │
╰────────────────────────────────────────╯

Episode Trace
─────────────────────────────────────────
Step  Skill      Observation     p(unlocked)      Δp
  0   peek_door  door_unlocked   0.50 → 0.85   +0.35
  1   try_door   door_opened     0.85 → 0.99   +0.14

╭────────────────────────────────────────╮
│ ✓ ESCAPED VIA DOOR                     │
│ Steps Taken: 2                         │
│ Strategy: Optimal                      │
╰────────────────────────────────────────╯
```

### Run All Tests (52 tests)

```bash
# All tests should pass
pytest test_scoring.py test_graph_model.py test_agent_runtime.py -v

# Just check they pass
pytest test_scoring.py test_graph_model.py test_agent_runtime.py -q
```

### Advanced Usage

```bash
# Start with high confidence (skip exploration)
python runner.py --door-state unlocked --initial-belief 0.9

# Quiet mode (just result)
python runner.py --door-state locked --quiet

# Verbose mode (see scoring details)
python runner.py --door-state unlocked --verbose
```

---

## 📊 How To Analyze / Assess / Interpret Outcomes

### Understanding The Output

#### 1. The Trace Table

```
Step  Skill      Observation     p(unlocked)      Δp
  0   peek_door  door_unlocked   0.50 → 0.85   +0.35
```

**What each column means:**
- **Step**: Which action number (0, 1, 2...)
- **Skill**: What action the robot chose
- **Observation**: What the robot saw happen
- **p(unlocked)**: Belief before → after
- **Δp**: How much belief changed

#### 2. Belief Changes

**Big changes** mean the robot learned a lot:
- `0.50 → 0.85` (+0.35): Strong evidence door is unlocked
- `0.50 → 0.15` (-0.35): Strong evidence door is locked

**Small/no changes** mean no new information:
- `0.85 → 0.99` (+0.14): Already knew, just confirmed
- `0.15 → 0.15` (0.00): Window doesn't tell us about door

#### 3. Strategy Assessment

**Optimal strategies:**
- Unlocked: peek → try_door (2 steps)
- Locked: peek → go_window (2 steps)

**Suboptimal but working:**
- Going straight to window (1 step, but wastes opportunity)
- Peeking twice (3 steps, over-cautious)

**Failed:**
- Trying locked door repeatedly (never escapes)
- Never reaching window (timeout)

### Querying Memory in Neo4j

Open http://localhost:17474 and try:

#### View Latest Episode
```cypher
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH (e)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
MATCH (s)-[:OBSERVED]->(o:Observation)
RETURN s.step_index AS step,
       sk.name AS skill,
       o.name AS observation,
       s.p_before AS belief_before,
       s.p_after AS belief_after
ORDER BY s.step_index;
```

#### Compare Both Scenarios
```cypher
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 2
MATCH (e)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
RETURN e.door_state AS scenario,
       collect(sk.name) AS actions_taken,
       e.total_steps AS steps
ORDER BY e.created_at DESC;
```

#### Visualize Episode Flow
```cypher
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH path = (e)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
MATCH (s)-[:OBSERVED]->(o:Observation)
RETURN path, o;
```

Click the graph view to see it visually!

### Key Metrics To Watch

#### 1. Exploration Behavior
**Good**: Agent peeks when p ≈ 0.5
**Bad**: Agent never peeks, or always peeks

**Why it matters**: Shows the robot balances exploration vs exploitation

#### 2. Belief Updates
**Good**: Large changes after observations (±0.35)
**Bad**: Beliefs don't change, or jump to 0/1

**Why it matters**: Conservative updates maintain adaptive behavior

#### 3. Action Selection
**Good**: Different actions at different beliefs
- p=0.5 → peek
- p=0.85 → try_door
- p=0.15 → go_window

**Bad**: Always same action regardless of belief

**Why it matters**: Shows active inference is working

#### 4. Episode Efficiency
**Good**: 2 steps for optimal path
**Acceptable**: 3-4 steps (cautious but works)
**Bad**: 5+ steps or failure to escape

**Why it matters**: Efficiency indicates good decision-making

### Interpreting Behavior Patterns

#### Pattern 1: "Peek then Act" (Expected)
```
Step 0: peek_door (gather info)
Step 1: try_door OR go_window (exploit info)
```
✅ **Meaning**: Proper active inference - explore then exploit

#### Pattern 2: "Straight to Window" (Suboptimal)
```
Step 0: go_window (safe route)
```
⚠️ **Meaning**: Too risk-averse, missing opportunity
🔧 **Fix**: Increase β (info gain weight)

#### Pattern 3: "Try Door Without Peeking" (Risky)
```
Step 0: try_door (lucky if unlocked, stuck if locked)
```
⚠️ **Meaning**: Too aggressive, not valuing information
🔧 **Fix**: Increase β or decrease α

#### Pattern 4: "Multiple Peeks" (Over-cautious)
```
Step 0: peek_door
Step 1: peek_door (again??)
```
❌ **Meaning**: Not updating beliefs properly, or scoring broken
🔧 **Fix**: Check belief updates in code

### Testing The Parameters

Want to see how parameters affect behavior?

```bash
# Edit config.py
ALPHA = 1.0   # Try changing this (goal weight)
BETA = 6.0    # Or this (info weight)
GAMMA = 0.3   # Or this (cost weight)

# Then run again
python runner.py --door-state unlocked
```

**Experiment guidelines:**
- Increase β: More exploration (more peeking)
- Increase α: More exploitation (more trying door)
- Increase γ: More cost-sensitive (cheaper actions)

### Success Criteria Checklist

✅ **Active Inference Working:**
- [ ] Agent peeks when uncertain (p ≈ 0.5)
- [ ] Agent acts when confident (p > 0.8 or p < 0.2)
- [ ] Different scenarios produce different behaviors
- [ ] Beliefs update based on observations

✅ **Procedural Memory Working:**
- [ ] Episodes logged to Neo4j
- [ ] Steps contain skills + observations + beliefs
- [ ] Can query past episodes
- [ ] Can visualize episode graphs

✅ **Demo Quality:**
- [ ] Output is clear and readable
- [ ] Behavior is explainable
- [ ] Both scenarios work optimally
- [ ] Easy to run and test

---

## 🎯 Quick Reference Card

### Run Both Scenarios
```bash
python runner.py --door-state unlocked  # Should peek then try_door
python runner.py --door-state locked    # Should peek then go_window
```

### Check Tests
```bash
pytest test_scoring.py test_graph_model.py test_agent_runtime.py -q
# Should see: 52 passed
```

### Explore Memory
```bash
# Open Neo4j Browser
open http://localhost:17474

# Run this query:
MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
RETURN e, s
```

### Understand A Run

1. **Look at first action**: Should be peek_door (exploration)
2. **Check belief change**: Should be large (±0.35)
3. **Look at second action**: Should match new belief
4. **Verify escape**: Should succeed in 2 steps

### Key Numbers

- **p = 0.50**: Maximum uncertainty (peek!)
- **p = 0.85**: Confident unlocked (try door!)
- **p = 0.15**: Confident locked (use window!)
- **Steps = 2**: Optimal performance
- **Score > 5**: Action has good justification

---

## 🤓 Deeper Understanding (For The Curious)

### What is "Active Inference" Really?

Active Inference is a theory about how brains work, proposed by Karl Friston. The core idea:

**Living things minimize "surprise"** (technically: "free energy")

They do this two ways:
1. **Update beliefs** based on observations (perception)
2. **Take actions** that either:
   - Achieve goals (exploitation)
   - Reduce uncertainty (exploration)

Our robot does both:
- Updates p(unlocked) when it peeks (perception)
- Balances goal vs info gain (action selection)

### The Math (Simplified)

**Entropy** (uncertainty):
```
H(p) = -p·log₂(p) - (1-p)·log₂(1-p)
```
At p=0.5: H=1.0 (maximum)
At p=0.85: H=0.61 (lower)

**Expected Value** (goal):
```
EV = p_unlocked × REWARD - p_locked × PENALTY
```
At p=0.9: EV = 0.9×10 - 0.1×3 = 8.7
At p=0.1: EV = 0.1×10 - 0.9×3 = -1.7

**Combined Score**:
```
Score = α·EV + β·H(p) - γ·cost
```

The magic: When H(p) is high, exploration wins. When EV is high, exploitation wins.

### Why Neo4j for Memory?

Traditional database (table):
```
episode_id | step | skill      | observation
1         | 0    | peek_door  | obs_locked
1         | 1    | go_window  | obs_escape
```

Graph database:
```
(Episode#1)-[:HAS_STEP]→(Step#0)-[:USED_SKILL]→(peek_door)
                                 [:OBSERVED]→(obs_locked)
           -[:HAS_STEP]→(Step#1)-[:USED_SKILL]→(go_window)
                                 [:OBSERVED]→(obs_escape)
```

Graph advantages:
- Natural representation of relationships
- Easy to traverse ("what happened after peeking?")
- Visualizable as actual graph
- Extensible (add new node types easily)

### Extension Ideas

Want to make it more complex?

**Easy extensions:**
- Add more rooms
- Add more objects (crowbar, key)
- Add multi-step skills ("craft tool from parts")

**Medium extensions:**
- Multiple state variables (door lock, alarm, time)
- Skills with preconditions ("need crowbar to pry door")
- Learning from past episodes (procedural memory affects scoring)

**Hard extensions:**
- Multiple agents (coordination)
- Full variational inference (proper Bayesian updates)
- LLM integration (explain reasoning, generate skills)

---

## 📚 Further Reading

### Active Inference
- [Karl Friston's Original Paper](https://www.fil.ion.ucl.ac.uk/~karl/)
- "The Free Energy Principle" (simplified explanations online)
- "Active Inference: The Free Energy Principle in Mind, Brain, and Behavior" (book)

### Knowledge Graphs
- [Neo4j Graph Database Concepts](https://neo4j.com/docs/)
- [APOC Procedures](https://neo4j.com/labs/apoc/)
- "Graph Databases" by Robinson, Webber, Eifrem

### Python + Neo4j
- [Neo4j Python Driver Documentation](https://neo4j.com/docs/python-manual/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/)

---

## ❓ FAQ

**Q: Why not just always use the window?**
A: Because when the door is unlocked, trying the door is faster and better. The robot learns to check first.

**Q: What if the robot is wrong about the door?**
A: The belief is a probability, not certainty. At p=0.85, there's still a 15% chance it's wrong. But that's the best guess given the observation.

**Q: Why peek instead of just trying the door?**
A: Peeking costs less (1.0 vs 1.5) and provides information. If the door is locked, trying wastes effort and gets you stuck. Peeking lets you make a smarter choice.

**Q: What if there are 3 doors?**
A: The same principles apply, but the graph and skills would be more complex. The active inference logic would still balance exploration and exploitation.

**Q: Is this how real AI works?**
A: This demonstrates principles used in real AI, but simplified. Real systems might use neural networks for beliefs, more complex state spaces, and hierarchical planning.

**Q: Can I add my own skills?**
A: Yes! Edit `cypher_init.cypher` to add new Skill nodes, then update `scoring.py` and `agent_runtime.py` to handle them.

---

**That's it! You now understand the MacGyver Active Inference Demo.** 🎉

Start with the basics, run the scenarios, and explore the memory graph. The more you play with it, the more you'll understand how active inference really works!
