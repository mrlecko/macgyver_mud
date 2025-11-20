# Balanced vs Crisp Policies: A Complementary Multi-Objective Example

> **⚠️ IMPORTANT (v2.0.1)**: Empirical validation revealed that claims of "superiority" were untested. MacGyver MUD has a ceiling effect (100% success both modes) that prevents performance comparison. This guide now presents balanced skills as a **complementary approach** with different analytical properties, not a proven superior alternative. See [ERRATA.md](ERRATA.md).

## Executive Summary

This document demonstrates **how balanced skills differ from** crisp (specialist) skills for multi-objective decision analysis using the Silver Gauge.

**Key Observation:**
- **Crisp skills** (original): `k_explore ≈ 0` for ALL skills → pure specialist design (by construction)
- **Balanced skills** (complementary): `k_explore ∈ [0.3, 0.9]` → genuine multi-objective trade-offs

**Status:** Analytical difference confirmed, performance difference untested.

## The Problem with Crisp Skills

### What Are Crisp Skills?

The original MacGyver MUD implementation has three skills:

```
peek_door:   goal=0.0, info=1.0  → Pure exploration
try_door:    goal>0,   info=0.0  → Pure exploitation
go_window:   goal>0,   info=0.0  → Pure exploitation
```

### The Silver Gauge Reveals Hidden Structure

When we apply the Silver Gauge to these skills:

```
                k_explore = GM(|goal|, info) / AM(|goal|, info)
```

We get:
```
peek_door:   k_explore ≈ 0.0001  (goal=0, info=1  → extreme imbalance)
try_door:    k_explore ≈ 0.0000  (goal>0, info=0  → extreme imbalance)
go_window:   k_explore ≈ 0.0000  (goal>0, info=0  → extreme imbalance)
```

**All designed crisp skills have k_explore ≈ 0 by construction!**

### Why This Happens

The `k_explore` metric measures **balance** between goal and info:
- `k_explore → 1.0`: Goal and info are comparable (balanced)
- `k_explore → 0.0`: One dimension dominates (imbalanced)

Crisp skills are **deliberately designed as pure specialists**:
- Either 100% exploration (peek) OR 100% exploitation (try/window)
- Never both simultaneously (by design choice)

This creates a **phase-separated** policy, not a **mixed-phase** policy.

### The Observation

**⚠️ v2.0.1 Correction:** This is a **design property**, not a natural universal pattern.

> The Silver Gauge measures that the deliberately designed crisp skills have extreme boundaries between exploration and exploitation, rather than smooth multi-objective trade-offs.

**Empirical Note:** Random skills do NOT show k≈0 clustering (mean k=0.57). Only deliberately extreme single-objective designs produce k≈0. See [ERRATA.md](ERRATA.md).

## The Solution: Balanced Skills

### Design Philosophy

**Balanced skills provide BOTH goal value AND information gain:**

```python
probe_and_try:        goal=60% of try_door,  info=40% of peek_door
informed_window:      goal=80% of go_window, info=30% of peek_door
exploratory_action:   goal=70% of try_door,  info=70% of peek_door
adaptive_peek:        goal=40% of try_door,  info=60% of peek_door
```

### Results at p=0.5

```
CRISP SKILLS (Pure Specialists):
peek_door            k_explore=0.0001  goal=  0.00  info=1.000
try_door             k_explore=0.0000  goal=  3.50  info=0.000
go_window            k_explore=0.0000  goal=  4.00  info=0.000

BALANCED SKILLS (Multi-Objective):
probe_and_try        k_explore=0.7332  goal=  2.10  info=0.400
informed_window      k_explore=0.5599  goal=  3.20  info=0.300
exploratory_action   k_explore=0.8000  goal=  2.80  info=0.700
adaptive_peek        k_explore=0.9165  goal=  1.40  info=0.600
```

**Balanced skills occupy the multi-objective region: k_explore ∈ [0.56, 0.92]**

## Why Balanced Skills Are Analytically Different (Not Proven Superior)

**⚠️ v2.0.1 Note:** Performance superiority is UNTESTED due to MacGyver MUD ceiling effect. The differences below are analytical properties, not validated performance benefits.

### 1. **Genuine Multi-Objective Trade-offs**

Crisp skills force a binary choice:
- Explore (peek) XOR Exploit (try/window)

Balanced skills allow blended strategies:
- Explore AND Exploit simultaneously
- Continuous spectrum of trade-offs

**Status:** Design difference confirmed, performance impact untested.

### 2. **Interpretable Geometric Metrics**

With crisp skills:
- `k_explore ≈ 0` for everything
- Metric doesn't differentiate between skills
- Phase diagram shows no variation

With balanced skills:
- `k_explore` varies meaningfully [0.3, 0.9]
- Each skill has distinct geometric signature
- Phase diagram shows rich structure

### 3. **Richer Policy Analysis**

**Crisp policy:**
```
All skills cluster at k_explore ≈ 0
→ Can't distinguish exploration vs exploitation by geometry alone
→ Must rely on raw goal/info values
```

**Balanced policy:**
```
Skills distributed across geometric space
→ Can classify skills by k_explore:
  - k < 0.4: Exploitation-leaning
  - 0.4 < k < 0.7: Balanced
  - k > 0.7: Exploration-leaning
→ Geometric signatures reveal strategic intent
```

### 4. **Potential Curriculum Learning** (Theoretical)

Hypothesis: With balanced skills, you could design geometric curricula:

```python
Stage 1: Use high k_explore skills (0.7-0.9)  → Heavy exploration
Stage 2: Use mid k_explore skills (0.4-0.7)   → Balanced
Stage 3: Use low k_explore skills (0.0-0.4)   → Refined exploitation
```

This is impossible with crisp skills (all ≈ 0).

**Status:** UNTESTED hypothesis - requires validation on suitable domains.

### 5. **Potential Adaptive Meta-Learning** (Theoretical)

Hypothesis: Balanced skills could enable geometric feedback:

```python
# Crisp: Can't use k_explore (always 0)
if success_rate < 0.7:
    # Must manually choose peek_door
    select_exploration_skill()

# Balanced: Could use k_explore directly
target_k = 0.7 if success_rate < 0.7 else 0.3
best_skill = min(skills, key=lambda s: abs(s.k_explore - target_k))
```

**Status:** UNTESTED - No evidence k-value correlates with performance.

### 6. **Potential Domain Transfer** (Theoretical)

Hypothesis: Geometric patterns may transfer better than raw values:

```
Domain A (Room Escape):
  "Skills with k_explore > 0.6 early in episode lead to success"

Domain B (Maze Navigation):
  "Apply same pattern: Use k_explore > 0.6 skills early"
  → Pattern might transfer because k is dimensionless
```

**Status:** UNTESTED - Requires validation on multiple domains.

## Implementation

### 1. Add Balanced Skills to Graph

```bash
cat balanced_skills_init.cypher | docker exec -i neo4j44 \
  cypher-shell -u neo4j -p password --encryption=false
```

This creates:
- 4 balanced skills with `goal_fraction` and `info_fraction` properties
- Associated observations
- SkillStats nodes

### 2. Use Balanced Scoring

```python
from scoring_balanced import score_balanced_skill_detailed

skill = {
    "name": "probe_and_try",
    "cost": 2.0,
    "goal_fraction": 0.6,
    "info_fraction": 0.4
}

details = score_balanced_skill_detailed(skill, p_unlocked=0.5)
# Returns: goal_value, info_gain, cost, total_score, etc.
```

### 3. Generate Comparison Visualizations

```bash
python3 visualize_balanced_comparison.py
```

Creates:
- `k_explore_comparison.png` - Bar chart showing distribution
- `goal_info_space.png` - Skills in multi-objective space
- `k_explore_vs_belief.png` - How geometry changes with belief
- `phase_diagram_comparison.png` - Geometric phase space

## Visualizations

### k_explore Comparison

**Crisp Skills:**
```
peek_door   ▓░░░░░░░░░  k=0.0001
try_door    ░░░░░░░░░░  k=0.0000
go_window   ░░░░░░░░░░  k=0.0000
```

**Balanced Skills:**
```
probe_and_try       ███████▒░░  k=0.73
informed_window     █████▒░░░░  k=0.56
exploratory_action  ████████░░  k=0.80
adaptive_peek       █████████░  k=0.92
```

### Goal-Information Space

```
info_gain
    1.0 ┤  ●peek_door (pure exploration)
        │
    0.7 ┤           ●exploratory_action (balanced, high both)
        │
    0.6 ┤      ●adaptive_peek (balanced, info-leaning)
        │
    0.4 ┤           ●probe_and_try (balanced, goal-leaning)
        │
    0.3 ┤                ●informed_window (balanced, efficient)
        │
    0.0 ┤       ●try_door    ●go_window (pure exploitation)
        └────────┴────────┴────────┴────────> goal_value
        0.0      1.5      3.0      4.0
```

**Crisp skills** occupy the axes (pure goal OR pure info).
**Balanced skills** occupy the interior (goal AND info).

### Phase Diagram

**Crisp Policy:**
- All points clustered at `(k_explore ≈ 0, k_efficiency ∈ [0.7, 1.0])`
- Vertical stripe in phase space
- No horizontal variation

**Balanced Policy:**
- Points distributed across `(k_explore ∈ [0.3, 0.9], k_efficiency ∈ [0.9, 1.0])`
- 2D cloud in phase space
- Rich geometric structure

## Use Cases

### When to Use Crisp Skills

1. **Demonstrating pure specialists**
2. **Pedagogical examples** (clear separation of concerns)
3. **Revealing architectural properties** (Silver Gauge diagnostic)
4. **Simple domains** where binary explore/exploit is sufficient

### When to Use Balanced Skills

1. **Real-world applications** (most domains are multi-objective)
2. **Research on geometric policies**
3. **Curriculum learning** (need geometric progression)
4. **Meta-learning** (need geometric feedback signals)
5. **Domain transfer** (geometric patterns transfer better)
6. **Interpretability** (richer semantic structure)

## Theoretical Implications

### What This Reveals About Active Inference

The original crisp policy shows that standard active inference with linear weights:

```
score = α·goal + β·info - γ·cost
```

can create **phase-separated** behavior even though the scoring function is continuous.

This happens when:
- Skills are designed as pure specialists
- Weights (α, β, γ) create strong preferences
- System operates in different regimes depending on belief

### Smoothness vs Crispness

**Crisp regime:**
- k_explore ≈ 0 everywhere
- Policy has sharp phase boundaries
- Agent switches between pure modes

**Smooth regime:**
- k_explore varies continuously
- Policy has gradual transitions
- Agent blends multiple objectives

**The choice of skill design determines which regime you're in.**

### Connection to Multi-Objective Optimization

Traditional Pareto analysis asks: "Is solution A dominated by solution B?"

Geometric analysis asks: "What is the shape of the trade-off?"

**Crisp skills:**
- Live on Pareto frontier (non-dominated)
- But all have same geometric shape (k ≈ 0)

**Balanced skills:**
- Also on Pareto frontier
- But have diverse geometric shapes (k ∈ [0.3, 0.9])

**Conclusion:** Geometric diversity is orthogonal to Pareto optimality.

## Practical Guidelines

### Designing Balanced Skills

**Rule 1:** Aim for `k_explore ∈ [0.3, 0.7]`

```python
# Target k_explore ≈ 0.7
goal_frac = 0.7
info_frac = 0.7
# Both high → balanced

# Target k_explore ≈ 0.5
goal_frac = 0.8
info_frac = 0.3
# Imbalanced but both nonzero
```

**Rule 2:** Cost should reflect combined value

```python
# Balanced skill provides:
# - 60% of try_door goal value
# - 40% of peek_door info value
# Cost should be between peek (1.0) and try (1.5)
cost = 1.0 + 0.6 * (1.5 - 1.0) = 1.3
```

**Rule 3:** Ensure all skills aren't balanced

```
Too uniform:  All k_explore ≈ 0.6  → No variety
Good variety: k_explore ∈ {0.3, 0.5, 0.7, 0.9}
```

### Integrating into Active Inference

**Option 1: Replace crisp skills**
- Remove peek/try/window
- Use only balanced skills
- Agent always does multi-objective reasoning

**Option 2: Augment crisp skills**
- Keep peek/try/window (0-3)
- Add balanced skills (4-7)
- Agent chooses between specialist and generalist

**Option 3: Adaptive skill set**
- Early episodes: Use balanced skills (exploration)
- Late episodes: Use crisp skills (exploitation)
- Meta-level curriculum

## Conclusion

**The Silver Gauge measured that the deliberately designed MacGyver MUD crisp skills are "crisp" (phase-separated) rather than "smooth" (multi-objective).**

This is a **design choice**—it demonstrates clean separation of concerns for pedagogical purposes.

**Balanced skills offer different analytical properties** (not proven superior):

1. ✅ Create genuine multi-objective trade-offs (analytical)
2. ✅ Produce varied k_explore metrics (confirmed)
3. ⚠️ May enable geometric curriculum learning (untested)
4. ⚠️ Could support adaptive meta-learning (untested)
5. ⚠️ Might transfer better across domains (untested)
6. ✅ Reveal different geometric structure (confirmed)

**Recommendation (v2.0.1):**

- **For pedagogy:** Use crisp skills to teach active inference fundamentals
- **For geometric analysis:** Use balanced skills to explore k-space coverage
- **For production:** Performance comparison NEEDED before claiming superiority
- **For research:** Test hypotheses about curriculum learning and transfer on harder domains

**Empirical Status:** Analytical properties confirmed, performance claims unvalidated.

---

## Files Reference

| File | Purpose |
|------|---------|
| `balanced_skills_init.cypher` | Neo4j schema for balanced skills |
| `scoring_balanced.py` | Scoring logic for multi-objective skills |
| `visualize_balanced_comparison.py` | Visualization suite |
| `BALANCED_POLICY_GUIDE.md` | This document |

## Quick Start

```bash
# 1. Add balanced skills to graph
cat balanced_skills_init.cypher | docker exec -i neo4j44 \
  cypher-shell -u neo4j -p password --encryption=false

# 2. Run comparison
python3 scoring_balanced.py

# 3. Generate visualizations
python3 visualize_balanced_comparison.py

# 4. View results
open k_explore_comparison.png
open goal_info_space.png
open k_explore_vs_belief.png
open phase_diagram_comparison.png
```

---

**Status:** ✅ Implementation Complete, ⚠️ Performance Claims Untested

**Impact:** Demonstrates the difference between specialist (crisp) and generalist (balanced) policies in active inference. Balanced skills create different (not proven superior) geometric signatures for multi-objective analysis.

**Next Steps (v2.0.1):**
1. Test on harder domains without ceiling effects
2. Validate curriculum learning hypothesis
3. Test domain transfer hypothesis
4. Compare performance empirically before claiming superiority

**See:** [ERRATA.md](ERRATA.md) and [validation/EMPIRICAL_RED_TEAM_RESULTS.md](validation/EMPIRICAL_RED_TEAM_RESULTS.md)
