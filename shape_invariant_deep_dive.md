# Shape-Invariant Learning: A Unified Framework for Robust Latent Representations

**A Deep Dive into Pythagorean Means, Active Inference, and JEPA-GPT Hybrid Architectures**

---

## Table of Contents

1. [ELI5: Why Shape Matters More Than Size](#eli5-why-shape-matters-more-than-size)
2. [Mathematical Foundations: The Pythagorean Trinity](#mathematical-foundations-the-pythagorean-trinity)
3. [Active Inference: Measuring Decision Geometry](#active-inference-measuring-decision-geometry)
4. [The JEPA Insight: Influence vs Strength](#the-jepa-insight-influence-vs-strength)
5. [The Problem: Why Autoregressive Models Drift](#the-problem-why-autoregressive-models-drift)
6. [The Solution: Shape-Preserving Latent Constraints](#the-solution-shape-preserving-latent-constraints)
7. [Architecture Blueprint: JEPA-GPT with Geometric Constraints](#architecture-blueprint-jepa-gpt-with-geometric-constraints)
8. [Implementation Details](#implementation-details)
9. [Theoretical Implications](#theoretical-implications)
10. [Experimental Validation Path](#experimental-validation-path)
11. [Beyond Narrative: Universal Applications](#beyond-narrative-universal-applications)

---

## ELI5: Why Shape Matters More Than Size

### The Playground Analogy

Imagine you're on a playground deciding between three activities:

- **Swinging** gives you 10 joy points
- **Climbing** gives you 8 joy points
- **Sliding** gives you 2 joy points

You pick swinging. Easy choice, right?

But now imagine tomorrow the same activities give you:

- **Swinging**: 100 joy points
- **Climbing**: 80 joy points
- **Sliding**: 20 joy points

You still pick swinging! Even though the *numbers* are 10× bigger, the **shape** of your preference stayed the same. Swinging is still #1, climbing #2, sliding #3.

### The Shape vs Size Distinction

**Size** = How big the numbers are (10 vs 100)
**Shape** = How the numbers relate to each other (10:8:2 has the same shape as 100:80:20)

Now here's the clever part: **What if we could measure JUST the shape, ignoring the size?**

That's what Pythagorean means do. They give us numbers between 0 and 1 that describe:
- How **balanced** two things are (is it 10 vs 10, or 100 vs 1?)
- Whether that balance is **series-like** (bottleneck) or **parallel-like** (complementary)

### Why This Matters for AI

When an AI makes decisions (like in a game, or writing a story), it's juggling multiple goals:

**In a game:**
- Goal: "Win the level" (worth 5 points)
- Information: "Learn what's behind that door" (worth 3 points)
- Cost: "This action costs 1 energy" (costs 1 point)

**In writing a story:**
- Theme: "Stay true to the character" (importance: 7)
- Pacing: "Keep the reader engaged" (importance: 6)
- Coherence: "Don't contradict earlier events" (importance: 9)

The AI could just add these up: 5 + 3 - 1 = 7 total score. Pick the action with highest score. Done.

**But here's what we lose:** We don't know if this was a "balanced exploration" (goal=5, info=5) or a "goal-dominated choice" (goal=9, info=1). Both might sum to 10, but they're *different kinds of decisions*.

### The Silver Gauge Trick

The "silver gauge" approach says:

1. **Yes, use the total score to pick the action** (AI behavior unchanged)
2. **But ALSO record the shape** (balanced? dominated? efficient?)
3. **Store this shape as a fingerprint** alongside the decision

Later, you can look back and see:
- "Ah, the AI was exploring steadily (balanced) for the first 10 steps"
- "Then it shifted to pure goal-seeking (goal-dominated) at step 15"
- "And at step 20 it made a very inefficient choice (high cost, low benefit)"

This is **observability without invasiveness**. You're not changing what the AI does—you're just creating a better measurement instrument.

---

### The Bridge to Language Models

Now here's where it gets really interesting.

**GPT models** generate text one word at a time. Each word is chosen based on what came before. This works beautifully for local coherence (the next sentence makes sense), but over long distances, the model can **drift**.

Why? Because GPT is adding up token probabilities, but it's not explicitly tracking the **shape** of the semantic space it's navigating.

Imagine writing a mystery novel:
- Early chapters: Theme=mystery, Pacing=slow-build (shape: 7:4)
- Middle chapters should maintain that shape: Theme=mystery, Pacing=rising (shape: 7:6)
- But GPT might drift to: Theme=action, Pacing=frenetic (shape: 3:9)

The **shape changed**, even if the text is locally fluent!

**JEPA** (Joint-Embedding Predictive Architecture) learns to predict the *next embedding* in latent space, not the next raw token. It naturally focuses on high-influence features.

**The hypothesis:** If we add **shape-preserving constraints** to JEPA's latent space, we can:
1. Keep GPT's local fluency
2. Prevent long-range drift
3. Maintain semantic coherence by preserving the geometric structure of the narrative

The rest of this document explores exactly how to do that.

---

## Mathematical Foundations: The Pythagorean Trinity

### The Three Classical Means

For two positive numbers `a` and `b`, we have three fundamental ways to compute their "average":

#### 1. Harmonic Mean (HM) - The Bottleneck View

```
HM(a,b) = 2 / (1/a + 1/b) = 2ab / (a+b)
```

**What it captures:** Series/bottleneck behavior. Dominated by the smaller value.

**Physical interpretation:** If you drive to work at speed `a` and return at speed `b`, your *average speed* for the round trip is the harmonic mean (not arithmetic!).

**Example:**
- HM(10, 10) = 10 ✓ balanced
- HM(100, 1) ≈ 1.98 ✗ bottlenecked by the small value

**When to use:** Rates, speeds, worst-case scenarios, series resistors.

#### 2. Geometric Mean (GM) - The Balanced View

```
GM(a,b) = √(a·b)
```

**What it captures:** Multiplicative/balanced relationships. The "natural" mean for growth rates.

**Physical interpretation:** The side length of a square with the same area as a rectangle with sides `a` and `b`.

**Example:**
- GM(10, 10) = 10 ✓ balanced
- GM(100, 1) = 10 ○ balanced geometric view
- GM(4, 9) = 6 (area 36 = 4×9)

**When to use:** Growth rates, aspect ratios, geometric problems, index numbers.

#### 3. Arithmetic Mean (AM) - The Optimistic View

```
AM(a,b) = (a + b) / 2
```

**What it captures:** Simple average. Equal weight to both values.

**Physical interpretation:** The midpoint on a number line.

**Example:**
- AM(10, 10) = 10 ✓ balanced
- AM(100, 1) = 50.5 ⚠ large value pulls average up

**When to use:** Linear combinations, expected values, everyday "average."

### The Fundamental Inequality

For all positive `a, b`:

```
HM(a,b) ≤ GM(a,b) ≤ AM(a,b)
```

**Equality holds** if and only if `a = b` (perfect balance).

The **spread** between these means tells you about imbalance:
- All three equal → perfectly balanced
- Wide spread → highly imbalanced

### The Shape Coefficient

Define the **dimensionless balance coefficient**:

```
k = GM / AM
```

**Properties:**
- `k ∈ [0, 1]` (bounded, scale-invariant)
- `k = 1` ⟺ perfect balance (`a = b`)
- `k → 0` as imbalance increases
- `k` is dimensionless (no units)
- `k` is invariant under scaling: `k(λa, λb) = k(a, b)` for any λ > 0

**This is the key insight:** `k` captures the **intrinsic geometric shape** of the relationship, independent of magnitude.

### Example: Decision Landscape

Consider three different decisions:

| Decision | Goal | Info | AM | GM | k = GM/AM |
|----------|------|------|-----|-----|-----------|
| A | 5 | 5 | 5.0 | 5.0 | 1.000 |
| B | 9 | 1 | 5.0 | 3.0 | 0.600 |
| C | 10 | 0.1 | 5.05 | 1.0 | 0.198 |

All three have similar arithmetic means (~5), but:
- **A is balanced exploration** (k ≈ 1)
- **B is goal-biased** (k = 0.6)
- **C is pure exploitation** (k ≈ 0.2)

The shape coefficient `k` reveals the **decision geometry** that AM alone obscures.

### Extension to Multiple Dimensions

For `n` values, we can compute:

```
HM_n = n / (1/a₁ + 1/a₂ + ... + 1/aₙ)
GM_n = ⁿ√(a₁·a₂·...·aₙ)
AM_n = (a₁ + a₂ + ... + aₙ) / n
```

And define multi-dimensional shape coefficients:

```
k_global = GM_n / AM_n
```

Or pairwise invariants between specific components.

---

## Active Inference: Measuring Decision Geometry

### The Active Inference Framework

Active inference is a theory of decision-making under uncertainty where an agent:

1. Maintains **beliefs** about hidden states (e.g., "Is the door locked?")
2. Has **goals** (desired states: "I want to be in the next room")
3. Can take **actions** that:
   - Change the world state (instrumental value)
   - Reveal information about the world (epistemic value)
   - Incur costs (energy, time, risk)

The agent's objective is to minimize **expected free energy**, which naturally balances:
- **Goal-seeking** (pragmatic value)
- **Information-seeking** (epistemic value)
- **Cost minimization** (efficiency)

### Standard Scoring Approach

Traditional active inference scoring computes:

```python
total_score = α·goal_value + β·info_gain - γ·cost
```

Where `α, β, γ` are hyperparameters that weight the three components.

**Problem:** This scalar collapses multi-dimensional structure. Two very different decisions can have the same score:

```
Decision 1: goal=10, info=0, cost=1  → score = 10α - γ
Decision 2: goal=5,  info=5, cost=1  → score = 5α + 5β - γ
```

If we tune hyperparameters so these are equal, we **lose information about the decision's character**.

### The Silver Gauge Enhancement

The silver gauge approach **augments** (not replaces) the scoring:

```python
# 1. Compute standard active inference score
total_score = α·goal_value + β·info_gain - γ·cost

# 2. Extract shape invariants
k_explore = GM(goal, info) / AM(goal, info)
k_efficiency = GM(goal+info, cost) / AM(goal+info, cost)

# 3. Return both
return {
    "score": total_score,           # Decision-making (unchanged)
    "k_explore": k_explore,          # Observability (new)
    "k_efficiency": k_efficiency,    # Observability (new)
}
```

### What Each Invariant Captures

#### k_explore: Exploration vs Exploitation Balance

```
k_explore = GM(goal, info) / AM(goal, info)
```

- **k ≈ 1.0:** Balanced exploration-exploitation (goal ≈ info)
- **k ≈ 0.5:** Moderate bias toward one component
- **k → 0:** Strong bias (pure exploration or pure exploitation)

**Interpretation:**
- High k_explore → agent is simultaneously seeking goals and information
- Low k_explore → agent is specialized (either laser-focused on goals OR pure curiosity)

#### k_efficiency: Benefit vs Cost Trade-off

```
benefit = goal + info
k_efficiency = GM(benefit, cost) / AM(benefit, cost)
```

- **k ≈ 1.0:** Cost is commensurate with benefit (balanced trade)
- **k → 0:** Either very cheap (cost << benefit) or very expensive (cost >> benefit)

**Interpretation:**
- High k_efficiency with benefit > cost → worthwhile action
- High k_efficiency with cost > benefit → expensive but proportional
- Low k_efficiency → extreme imbalance (either "too good to be true" or "obviously wasteful")

### Canonical Example: The Door Problem

You're in a room with a closed door. Is it locked? You have three actions:

#### Action 1: "peek" (look through keyhole)
```
goal_value = 0.0   (doesn't get you into room)
info_gain = 0.8    (reveals lock state)
cost = 0.1         (very cheap)

k_explore = GM(0.0, 0.8) / AM(0.0, 0.8) = 0 / 0.4 = 0.0
k_efficiency = GM(0.8, 0.1) / AM(0.8, 0.1) ≈ 0.63
```

**Shape signature:** Pure exploration (k_explore ≈ 0), highly efficient.

#### Action 2: "try" (test if door opens)
```
goal_value = 0.5   (50% chance to enter if unlocked)
info_gain = 1.0    (definitively reveals lock state)
cost = 0.3         (moderate cost)

k_explore = GM(0.5, 1.0) / AM(0.5, 1.0) ≈ 0.94
k_efficiency = GM(1.5, 0.3) / AM(1.5, 0.3) ≈ 0.75
```

**Shape signature:** Balanced exploration-exploitation (k_explore ≈ 0.94), good efficiency.

#### Action 3: "force" (break down door)
```
goal_value = 1.0   (guaranteed to get through)
info_gain = 0.0    (learn nothing about lock)
cost = 5.0         (very expensive, noisy, permanent)

k_explore = GM(1.0, 0.0) / AM(1.0, 0.0) = 0.0
k_efficiency = GM(1.0, 5.0) / AM(1.0, 5.0) ≈ 0.74
```

**Shape signature:** Pure exploitation (k_explore ≈ 0), questionable efficiency.

### Emergent Patterns Across Episodes

The power of shape invariants becomes clear when tracking them over time:

**Example trajectory:**

| Step | Action | k_explore | k_efficiency | Interpretation |
|------|--------|-----------|--------------|----------------|
| 1 | peek | 0.00 | 0.85 | Pure info-gathering |
| 2 | peek | 0.00 | 0.85 | Still exploring |
| 3 | try | 0.94 | 0.75 | Balanced attempt |
| 4 | try | 0.94 | 0.75 | Repeat balanced attempt |
| 5 | force | 0.00 | 0.74 | Pure exploitation |

**Pattern:** The agent transitions from pure exploration → balanced probing → forced exploitation.

**If we only had total_score**, we'd see:
```
[3.2, 3.2, 4.5, 4.5, 6.1]
```

Just increasing numbers. The **qualitative shift in decision character** is invisible.

### Why This Matters: Hyperparameter Robustness

One of the most powerful properties: **shape invariants are robust to hyperparameter scaling**.

If you change `α, β, γ` in your scoring function, the `total_score` values will change, but if the agent's *policy* remains stable, the shape invariants should remain similar.

**Example:**

Original hyperparameters: `α=1.0, β=1.0, γ=1.0`

```
Action: try
goal=0.5, info=1.0, cost=0.3
score = 0.5·1.0 + 1.0·1.0 - 0.3·1.0 = 1.2
k_explore = 0.94
```

New hyperparameters: `α=2.0, β=0.5, γ=0.1`

```
Action: try
goal=0.5, info=1.0, cost=0.3
score = 0.5·2.0 + 1.0·0.5 - 0.3·0.1 = 1.47
k_explore = 0.94  (UNCHANGED)
```

The **score changed** but the **shape didn't**. This means:

1. You can compare policies across different reward scales
2. Shape invariants reveal intrinsic strategy independent of tuning
3. You can detect when hyperparameter changes actually alter decision geometry (vs just rescaling)

### Storage and Querying in Neo4j

In the MacGyver demo, each `Step` node can store:

```cypher
CREATE (s:Step {
    step_id: 42,
    action: "try_door",
    total_score: 4.5,

    // Silver stamp
    k_explore: 0.94,
    k_efficiency: 0.75,
    goal_value: 0.5,
    info_gain: 1.0,
    cost: 0.3,

    // Full Pythagorean means if desired
    hm_goal_info: 0.67,
    gm_goal_info: 0.71,
    am_goal_info: 0.75
})
```

Then query patterns:

```cypher
// Find steps with balanced exploration
MATCH (s:Step)
WHERE s.k_explore > 0.9
RETURN s.action, s.k_explore, s.k_efficiency
ORDER BY s.step_id

// Find efficiency phase transitions
MATCH (s1:Step)-[:NEXT]->(s2:Step)
WHERE abs(s2.k_efficiency - s1.k_efficiency) > 0.3
RETURN s1.step_id, s2.step_id,
       s1.k_efficiency AS before,
       s2.k_efficiency AS after

// Cluster episodes by exploration strategy
MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
WITH e, avg(s.k_explore) AS mean_k_explore
WHERE mean_k_explore > 0.8
RETURN e.episode_id, mean_k_explore
```

This enables **geometric queries** about agent behavior that are independent of reward scaling.

---

## The JEPA Insight: Influence vs Strength

### The Autoencoder Limitation

Classic autoencoders learn representations by reconstructing input pixels:

```
Input Image → [Encoder] → Latent z → [Decoder] → Reconstructed Image

Loss = ||Original - Reconstructed||²  (pixel-wise)
```

**Problem:** This loss treats every pixel equally. In the Cart Pole example:

- Background pixels (white, static): 99% of the image
- Pole pixels (moving, informative): 1% of the image

The autoencoder will allocate capacity to minimize total reconstruction error, which means:
- Sharp background (lots of pixels, easy to compress)
- Blurry pole (few pixels, hard to compress)

**The background has high signal strength but low influence.**
**The pole has low signal strength but high influence.**

Pixel-wise reconstruction is **strength-biased**.

### JEPA's Latent-Space Prediction

JEPA (Joint-Embedding Predictive Architecture) takes a different approach:

```
Context Input x → [x-encoder] → z_x
Target Input y  → [y-encoder] → z_y
Action a        → [included in predictor]

Predictor: ẑ_y = P(z_x, a)

Loss = ||ẑ_y - z_y||²  (latent-space distance)
```

**Key difference:** The loss is computed in **embedding space**, not pixel space.

This means:
1. The encoder can **choose** what to represent
2. Features that help predict the next latent state are preserved
3. Features that don't contribute to prediction are discarded

**JEPA is influence-biased.**

### What Gets Preserved?

In the Cart Pole task, the encoder learns to:

✓ **Preserve:** Pole angle, cart position, angular velocity, cart velocity
✗ **Discard:** Background color, exact pixel positions, noise

Why? Because to predict `z_{t+1}` from `z_t` and action `a`, you need the **state variables that evolve under the dynamics**, not the irrelevant details.

This is exactly the distinction between:
- **High-influence features** (p_a): Features that matter for downstream predictions
- **High-strength features** (pixel intensity): Features that are visually prominent

### The Collapse Problem

But JEPA has a major failure mode: **representation collapse**.

If both encoders output constant vectors:
```
z_x = [0, 0, 0, 0]  (always)
z_y = [0, 0, 0, 0]  (always)
```

And the predictor does:
```
ẑ_y = z_x  (identity)
```

Then the loss is zero! Perfect score, useless representation.

**Standard solutions:**
1. **Exponential moving average (EMA) of encoder weights** - prevents both encoders from collapsing together
2. **Variance regularization** - encourage embeddings to vary across batches
3. **Gradient propagation from task loss** - in RL, backprop the actor/critic losses through the encoder

The JEPA paper tests these and finds that #3 (task gradients) works best, but #2 (variance regularization) can work alone with careful tuning.

### The Missing Piece: Structural Constraints

Current JEPA relies on:
- Prediction accuracy (latent distance)
- Variance regularization (preventing collapse)
- Task gradients (grounding in behavior)

But there's no explicit constraint on **preserving the geometric structure of the latent space**.

**What if the encoder learns:**
```
z_1 = [1, 0, 0, 0]  (cart left, pole upright)
z_2 = [0, 1, 0, 0]  (cart center, pole upright)
z_3 = [0, 0, 1, 0]  (cart right, pole upright)
```

vs.

```
z_1 = [1, 0, 0, 0]  (cart left, pole upright)
z_2 = [0.5, 0.5, 0, 0]  (cart center, pole upright)
z_3 = [0.3, 0.7, 0, 0]  (cart right, pole upright)
```

Both could achieve similar prediction loss, but they have **different geometric structure**.

**The first representation:** Orthogonal basis, clean separability
**The second representation:** Oblique coordinates, confounded dimensions

Over training, if the geometry isn't explicitly constrained, it can **drift** - not collapse, but gradually warp into less interpretable, less stable configurations.

---

## The Problem: Why Autoregressive Models Drift

### The Fluency vs Coherence Tradeoff

GPT-style models are **locally optimal, globally unconstrained**.

**Local optimality:** Each token is chosen to maximize `P(token | context)`, which produces:
- Grammatically correct sentences
- Semantically appropriate word choices
- Smooth transitions between ideas

**Global incoherence:** Over long sequences, small drifts compound:
- Character personalities shift subtly
- Plot threads get abandoned
- Thematic focus wanders
- Tone becomes inconsistent

### Why Does This Happen?

**1. No Explicit State Tracking**

GPT doesn't maintain a "narrative state" variable. It has:
- Hidden states (transformer layers)
- Attention over context window
- Implicit learned patterns

But no explicit `θ_narrative = [theme_coherence, pacing, tension, character_state]`.

**2. Greedy Local Optimization**

At each step:
```
token_t = argmax P(token | tokens_{1:t-1})
```

This is myopic. The model doesn't explicitly optimize:
```
"Choose token_t such that the TRAJECTORY of narrative state
 from t=0 to t=T remains on the thematic manifold"
```

**3. Compounding Errors**

Even small drifts compound:

```
Step 1: Theme = [mystery: 0.8, romance: 0.2]  ✓ intended
Step 100: Theme = [mystery: 0.75, romance: 0.25]  ○ slight drift
Step 500: Theme = [mystery: 0.6, romance: 0.4]  ⚠ noticeable drift
Step 1000: Theme = [mystery: 0.3, romance: 0.7]  ✗ genre shift!
```

Each step was locally fluent, but the trajectory wandered.

### The Attention Window Limitation

Transformers have finite context windows (even with techniques like RoPE, ALiBi, etc.):

- GPT-4: ~128k tokens
- Claude: ~200k tokens

For very long-form generation (novels, codebases, multi-session conversations), you eventually **lose direct access to early context**.

Even with retrieval-augmented generation (RAG), you're now dependent on:
- The quality of your retrieval system
- The salience of retrieved chunks
- The model's ability to integrate retrieved context

**There's no "semantic backbone"** that persists across the entire generation.

### Existing Mitigation Strategies

**1. Prompt engineering**
- Explicit instructions: "Maintain a mysterious tone throughout"
- Periodic reminders: "Remember, the protagonist is shy and analytical"

**Problem:** Relies on surface-level language, doesn't constrain latent geometry.

**2. Constrained decoding**
- Classifier-guided sampling: Reject tokens that reduce "mystery score"
- Reinforcement learning from human feedback (RLHF): Train on preference data

**Problem:** Post-hoc correction, doesn't prevent latent drift.

**3. Hierarchical planning**
- Generate outline first, then fill in details
- Multi-stage generation with consistency checks

**Problem:** Plans themselves can drift, and enforcing plan-adherence is still a constraint problem.

**4. Retrieval of earlier text**
- Periodically retrieve similar passages from earlier in the document
- Use retrieved context to ground continuation

**Problem:** Similarity is typically embedding-distance, which doesn't explicitly preserve geometric structure.

### What's Missing: Geometric Continuity

All of these approaches treat coherence as a **constraint satisfaction problem**:

"Make sure the output satisfies property P"

What we actually want is **trajectory optimization**:

"Navigate latent space along a geodesic that preserves structural invariants"

**Example:**

Imagine narrative state as a point in a high-dimensional space:
```
z_narrative = [theme, pacing, tension, char_1_state, char_2_state, ...]
```

We want:
```
z_0 → z_1 → z_2 → ... → z_T
```

such that the **shape invariants** of the trajectory are preserved:

```
k_theme_pacing(z_t) ≈ k_theme_pacing(z_0)  ∀t
k_tension_resolution(z_t) follows intended arc
k_char1_agency(z_t) remains consistent
```

Current approaches don't give us tools to express or enforce this.

---

## The Solution: Shape-Preserving Latent Constraints

### Core Hypothesis

**If we explicitly constrain the geometric structure of latent space using Pythagorean invariants, we can prevent drift while maintaining local fluency.**

### The Architecture

```
Input sequence → [JEPA Encoder] → z_semantic
z_semantic + action/token → [Predictor] → ẑ_next
ẑ_next → [GPT Decoder] → output tokens
```

With three loss components:

**1. JEPA Loss (latent prediction)**
```
L_JEPA = ||ẑ_next - z_next||²
```

**2. GPT Loss (fluency)**
```
L_GPT = -log P(tokens | z_semantic)
```

**3. Shape Loss (geometric constraint) ← NEW**
```
L_shape = Σ ||k_i(ẑ_next) - k_i(z_next)||²
```

Where `k_i` are shape invariants computed over latent dimensions.

### Defining Shape Invariants for Narrative

For a narrative embedding `z = [z₁, z₂, ..., z_n]`, we define:

**Decomposition into interpretable components:**

Assume the encoder has been structured (or encouraged through auxiliary losses) to disentangle:

```
z = [theme_dims, pacing_dims, character_dims, plot_dims, style_dims]
```

**Example:**
- `theme_dims`: [mystery, romance, horror, comedy] (4D)
- `pacing_dims`: [action_density, dialogue_ratio] (2D)
- `character_dims`: [char1_agency, char1_emotion, char2_agency, char2_emotion] (4D)
- `plot_dims`: [tension, foreshadowing, resolution] (3D)
- `style_dims`: [formality, descriptiveness] (2D)

Total: 15D embedding

**Shape invariants:**

```python
# Theme balance
theme_vec = z[0:4]
k_theme = GM(theme_vec) / AM(theme_vec)  # How balanced across genres?

# Pacing balance
pacing_vec = z[4:6]
k_pacing = GM(pacing_vec) / AM(pacing_vec)  # Action vs dialogue balance

# Character agency balance
char1_agency = z[6]
char2_agency = z[8]
k_agency = GM(char1_agency, char2_agency) / AM(char1_agency, char2_agency)

# Plot-pacing coupling
plot_tension = z[10]
pacing_action = z[4]
k_plot_pacing = GM(plot_tension, pacing_action) / AM(plot_tension, pacing_action)
```

These invariants should:
- **Remain stable** when the narrative is "on track"
- **Evolve smoothly** during intentional transitions (e.g., rising action)
- **Not jump discontinuously** due to local token choices

### The Shape-Preserving Loss

```python
def shape_loss(z_pred, z_target, z_context):
    """
    Enforce that predicted embedding preserves geometric structure.

    Args:
        z_pred: Predicted next latent state [batch, embed_dim]
        z_target: Actual next latent state [batch, embed_dim]
        z_context: Previous latent state [batch, embed_dim]
    """

    # Extract component vectors
    theme_pred = z_pred[:, 0:4]
    theme_tgt = z_target[:, 0:4]
    theme_ctx = z_context[:, 0:4]

    pacing_pred = z_pred[:, 4:6]
    pacing_tgt = z_target[:, 4:6]

    # Compute shape invariants
    k_theme_pred = geometric_mean(theme_pred) / arithmetic_mean(theme_pred)
    k_theme_tgt = geometric_mean(theme_tgt) / arithmetic_mean(theme_tgt)

    k_pacing_pred = geometric_mean(pacing_pred) / arithmetic_mean(pacing_pred)
    k_pacing_tgt = geometric_mean(pacing_tgt) / arithmetic_mean(pacing_tgt)

    # Shape preservation loss
    loss_theme = (k_theme_pred - k_theme_tgt)**2
    loss_pacing = (k_pacing_pred - k_pacing_tgt)**2

    # Smooth evolution loss (prevent sudden jumps)
    k_theme_ctx = geometric_mean(theme_ctx) / arithmetic_mean(theme_ctx)
    loss_continuity = (k_theme_pred - k_theme_ctx)**2

    # Combined
    return loss_theme + loss_pacing + 0.5 * loss_continuity
```

### Why This Works: Theoretical Intuition

**1. Scale invariance**

If the model learns to rescale embeddings (e.g., multiply all theme dimensions by 2), the shape invariants remain unchanged:

```
k(2·theme) = GM(2·theme) / AM(2·theme)
           = 2·GM(theme) / 2·AM(theme)
           = GM(theme) / AM(theme)
           = k(theme)
```

This prevents the model from "escaping" the constraint via rescaling.

**2. Geometric grounding**

The shape coefficient `k = GM/AM` has a clear geometric interpretation:

- For a 2D vector `(a, b)`, `k` is related to the **eccentricity** of the ellipse with semi-axes `a` and `b`
- For higher dimensions, it captures the **volume-to-sum ratio** of the component simplex
- `k ≈ 1` means components are balanced (isotropic)
- `k → 0` means components are anisotropic (dominated by one direction)

**3. Differentiability**

All operations (sqrt, division, mean) are differentiable, so gradients flow cleanly:

```
∂L_shape/∂z_pred is well-defined → backprop through encoder
```

**4. Composability**

You can define multiple shape invariants for different aspects:

```
L_shape = Σ_i λ_i · ||k_i(ẑ) - k_i(z)||²
```

And weight them according to importance.

### Comparison to Existing Approaches

| Approach | Pro | Con |
|----------|-----|-----|
| **RLHF** | Aligned with human preferences | Requires expensive preference data, doesn't prevent drift |
| **Classifier guidance** | Simple to implement | Post-hoc, high inference cost, doesn't constrain geometry |
| **VAE regularization** | Smooth latent space | Doesn't preserve specific structural properties |
| **Contrastive learning** | Good for discrimination | Doesn't enforce smooth trajectories |
| **Shape invariants (ours)** | Geometric, differentiable, interpretable | Requires structured embeddings |

---

## Architecture Blueprint: JEPA-GPT with Geometric Constraints

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SHAPE-PRESERVING JEPA-GPT                 │
└─────────────────────────────────────────────────────────────┘

Input: Text sequence x_t = [tok_1, ..., tok_t]

┌──────────────────┐
│ JEPA x-Encoder   │  (Vision Transformer or Text Encoder)
│   V(θ, x_t)      │
└────────┬─────────┘
         │
         v
    z_t ∈ ℝ^d  (Structured embedding)
         │
    ┌────┴─────┐
    │          │
    v          v
┌───────┐  ┌──────────────┐
│ Shape │  │  Predictor   │  Input: z_t + action/next_token_hint
│ Calc  │  │   P(z_t)     │
└───┬───┘  └──────┬───────┘
    │             │
    │             v
    │        ẑ_{t+1} (predicted next embedding)
    │             │
    │        ┌────┴─────┐
    │        │          │
    │        v          v
    │   ┌────────┐  ┌──────────┐
    │   │ JEPA   │  │  Shape   │
    │   │ Loss   │  │  Loss    │ ← Compare k(ẑ) vs k(z_target)
    │   └────────┘  └──────────┘
    │
    v
┌──────────────────┐
│  GPT Decoder     │  Input: z_t
│  (Transformer)   │  Output: Next tokens
└────────┬─────────┘
         │
         v
    token_{t+1}, token_{t+2}, ...
         │
         v
    ┌────────┐
    │ GPT    │
    │ Loss   │  (Standard cross-entropy)
    └────────┘

Total Loss = α·L_JEPA + β·L_shape + γ·L_GPT
```

### Component Details

#### 1. JEPA x-Encoder

**Architecture:** Transformer encoder (or Vision Transformer for multimodal)

**Input:** Sequence of tokens/patches with positional encoding

**Output:** Structured embedding `z_t ∈ ℝ^d`

**Key design choice:** The embedding space should be **semantically factored**:

```python
class StructuredEncoder(nn.Module):
    def __init__(self, vocab_size, embed_dim=512):
        super().__init__()
        self.token_embed = nn.Embedding(vocab_size, embed_dim)
        self.transformer = TransformerEncoder(
            d_model=embed_dim,
            nhead=8,
            num_layers=6
        )

        # Project to structured semantic space
        # [theme, pacing, character, plot, style]
        self.semantic_head = nn.Linear(embed_dim, d_semantic)

    def forward(self, tokens):
        x = self.token_embed(tokens)
        x = self.transformer(x)

        # Pool (e.g., CLS token or mean pooling)
        z_raw = x[:, 0, :]  # CLS token

        # Project to semantic space
        z_semantic = self.semantic_head(z_raw)

        return z_semantic
```

**Training consideration:** You may want auxiliary losses to encourage disentanglement:

```python
# Encourage theme dimensions to be orthogonal to pacing dimensions
theme = z[:, 0:4]
pacing = z[:, 4:6]
L_orthogonal = (theme @ pacing.T).pow(2).mean()

# Encourage theme dimensions to sum to ~1 (simplex constraint)
theme_sum = theme.sum(dim=1)
L_simplex = (theme_sum - 1).pow(2).mean()
```

#### 2. JEPA y-Encoder (Target Encoder)

**Architecture:** Identical to x-encoder

**Weights:** Exponential moving average of x-encoder:

```python
# Initialize
y_encoder.load_state_dict(x_encoder.state_dict())

# Update (no gradients)
with torch.no_grad():
    for param_x, param_y in zip(x_encoder.parameters(),
                                  y_encoder.parameters()):
        param_y.data = 0.99 * param_y.data + 0.01 * param_x.data
```

**Purpose:** Provides stable target embeddings while preventing collapse.

#### 3. Predictor Network

**Architecture:** Shallow MLP (2-3 layers)

**Input:**
- `z_t` (current embedding)
- `a_t` (action/token hint - optional)

**Output:** `ẑ_{t+1}` (predicted next embedding)

```python
class Predictor(nn.Module):
    def __init__(self, d_semantic, d_action, hidden_dim=256):
        super().__init__()
        self.fc1 = nn.Linear(d_semantic + d_action, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, d_semantic)

    def forward(self, z_t, a_t):
        x = torch.cat([z_t, a_t], dim=-1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        z_pred = self.fc3(x)
        return z_pred
```

**Design rationale:** Keep it shallow so prediction task forces rich encodings.

#### 4. Shape Calculator

**Purpose:** Extract geometric invariants from embeddings.

```python
class ShapeInvariantCalculator:
    def __init__(self, semantic_structure):
        """
        Args:
            semantic_structure: Dict mapping component names to slice indices
                e.g., {"theme": slice(0,4), "pacing": slice(4,6), ...}
        """
        self.structure = semantic_structure

    def compute_invariants(self, z):
        """
        Args:
            z: [batch, d_semantic] embedding tensor

        Returns:
            invariants: Dict of shape coefficients
        """
        invariants = {}

        for name, idx_slice in self.structure.items():
            component = z[:, idx_slice]

            # Ensure positive (for geometric mean)
            component = F.softplus(component) + 1e-8

            # Pythagorean means
            gm = geometric_mean(component, dim=-1)
            am = arithmetic_mean(component, dim=-1)

            # Shape coefficient
            k = gm / (am + 1e-8)

            invariants[f"k_{name}"] = k

        # Pairwise invariants (e.g., theme-pacing coupling)
        theme = z[:, self.structure["theme"]]
        pacing = z[:, self.structure["pacing"]]

        theme_mag = theme.norm(dim=-1)
        pacing_mag = pacing.norm(dim=-1)

        k_theme_pacing = geometric_mean_pair(theme_mag, pacing_mag) / \
                         arithmetic_mean_pair(theme_mag, pacing_mag)

        invariants["k_theme_pacing"] = k_theme_pacing

        return invariants

def geometric_mean(x, dim=-1, eps=1e-8):
    """Geometric mean along dimension."""
    log_x = torch.log(x + eps)
    return torch.exp(log_x.mean(dim=dim))

def arithmetic_mean(x, dim=-1):
    """Arithmetic mean along dimension."""
    return x.mean(dim=dim)

def geometric_mean_pair(a, b, eps=1e-8):
    """GM of two tensors."""
    return torch.sqrt((a + eps) * (b + eps))

def arithmetic_mean_pair(a, b):
    """AM of two tensors."""
    return 0.5 * (a + b)
```

#### 5. GPT Decoder

**Architecture:** Standard autoregressive transformer decoder

**Input:** Semantic embedding `z_t` (as prefix context)

**Output:** Token probabilities for continuation

```python
class GPTDecoder(nn.Module):
    def __init__(self, vocab_size, d_semantic, d_model=512, num_layers=12):
        super().__init__()

        # Project semantic embedding to decoder space
        self.semantic_proj = nn.Linear(d_semantic, d_model)

        # Standard GPT decoder
        self.transformer = GPT2Model.from_pretrained("gpt2")
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(self, z_semantic, token_context):
        """
        Args:
            z_semantic: [batch, d_semantic] - semantic embedding
            token_context: [batch, seq_len] - token IDs

        Returns:
            logits: [batch, seq_len, vocab_size]
        """
        # Project semantic embedding
        z_proj = self.semantic_proj(z_semantic)  # [batch, d_model]

        # Prepend as "semantic token"
        z_proj = z_proj.unsqueeze(1)  # [batch, 1, d_model]

        # Get token embeddings
        token_embeds = self.transformer.wte(token_context)  # [batch, seq_len, d_model]

        # Concatenate
        inputs = torch.cat([z_proj, token_embeds], dim=1)

        # Decode
        hidden = self.transformer(inputs_embeds=inputs).last_hidden_state

        # LM head
        logits = self.lm_head(hidden[:, 1:, :])  # Skip semantic token position

        return logits
```

**Key insight:** The semantic embedding `z_semantic` acts as a **soft constraint** on the generation, similar to how a prompt guides GPT, but now with geometric structure preserved.

### Training Procedure

#### Phase 1: JEPA Pre-training (Optional)

Train the encoder/predictor on prediction task without GPT decoder:

```python
for batch in dataloader:
    # Get context and target sequences
    x_context = batch["context"]  # tokens[t-2:t]
    y_target = batch["target"]    # tokens[t-1:t+1]
    action = batch["action"]      # e.g., next token (teacher forcing)

    # Encode
    z_x = x_encoder(x_context)
    z_y = y_encoder(y_target)  # no grad

    # Predict
    z_pred = predictor(z_x, action)

    # JEPA loss
    L_jepa = F.mse_loss(z_pred, z_y)

    # Shape loss
    k_pred = shape_calc.compute_invariants(z_pred)
    k_target = shape_calc.compute_invariants(z_y)

    L_shape = sum((k_pred[key] - k_target[key]).pow(2).mean()
                   for key in k_pred.keys())

    # Variance regularization (prevent collapse)
    L_var = -z_x.var(dim=0).mean()
    L_var = torch.clamp(L_var, max=0)  # Only penalize if variance too low

    # Total
    loss = L_jepa + 0.1 * L_shape + 0.01 * L_var

    loss.backward()
    optimizer.step()

    # Update y-encoder (EMA)
    update_ema(x_encoder, y_encoder, momentum=0.99)
```

#### Phase 2: Joint Training with GPT

```python
for batch in dataloader:
    # Get sequences
    x_context = batch["context"]
    y_target_seq = batch["target"]
    tokens_to_generate = batch["continuation"]

    # === JEPA Branch ===
    z_x = x_encoder(x_context)
    z_y = y_encoder(y_target_seq)  # no grad
    z_pred = predictor(z_x, action_hint)

    L_jepa = F.mse_loss(z_pred, z_y)

    k_pred = shape_calc.compute_invariants(z_pred)
    k_target = shape_calc.compute_invariants(z_y)
    L_shape = sum((k_pred[key] - k_target[key]).pow(2).mean()
                   for key in k_pred.keys())

    # === GPT Branch ===
    # Use z_x to condition GPT decoder
    logits = gpt_decoder(z_x, tokens_to_generate[:-1])
    L_gpt = F.cross_entropy(
        logits.reshape(-1, vocab_size),
        tokens_to_generate[1:].reshape(-1)
    )

    # === Combined Loss ===
    loss = 1.0 * L_jepa + 0.5 * L_shape + 1.0 * L_gpt

    loss.backward()
    optimizer.step()
    update_ema(x_encoder, y_encoder, momentum=0.99)
```

#### Phase 3: Fine-tuning (Optional)

Once the encoder produces stable, structured embeddings, you can:

1. **Freeze encoder**, fine-tune decoder for fluency
2. **Curriculum learning**: Gradually increase sequence length
3. **Targeted shape constraints**: Adjust λ weights for specific aspects

### Inference

```python
def generate_with_shape_preservation(
    initial_context,
    max_length=1000,
    shape_target=None,
    temperature=1.0
):
    """
    Generate text while preserving geometric structure.

    Args:
        initial_context: Starting tokens
        max_length: Max tokens to generate
        shape_target: Dict of target shape coefficients (optional)
        temperature: Sampling temperature
    """

    generated = initial_context.copy()

    # Encode initial context
    z_current = x_encoder(initial_context)

    # Extract initial shape
    if shape_target is None:
        k_initial = shape_calc.compute_invariants(z_current)
        shape_target = {k: v.clone() for k, v in k_initial.items()}

    for _ in range(max_length):
        # Decode next tokens
        logits = gpt_decoder(z_current, generated[-context_len:])
        next_token_logits = logits[:, -1, :] / temperature

        # Sample
        probs = F.softmax(next_token_logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)

        # Append
        generated.append(next_token)

        # Re-encode with new token
        z_next = x_encoder(generated[-context_len:])

        # Check shape drift
        k_next = shape_calc.compute_invariants(z_next)

        drift = sum((k_next[key] - shape_target[key]).abs().mean()
                    for key in k_next.keys())

        if drift > DRIFT_THRESHOLD:
            # Apply corrective sampling
            # (Could reject and resample, or adjust decoder logits)
            print(f"Warning: Shape drift detected at step {len(generated)}")

        z_current = z_next

    return generated
```

---

## Implementation Details

### Hyperparameter Recommendations

Based on the JEPA RL paper and active inference principles:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `d_semantic` | 64-256 | Small enough to force compression, large enough for disentanglement |
| `EMA momentum` | 0.99 | Standard for target network updates |
| `λ_shape` | 0.1-0.5 | Enough to matter, not so much it dominates JEPA loss |
| `Predictor layers` | 2-3 | Shallow to force work onto encoder |
| `Predictor hidden dim` | 256-512 | Comparable to semantic dim |
| `Variance reg weight` | 0.01 | Safety net, shouldn't be needed if EMA works |

### Semantic Structure Design

**Option 1: Manual decomposition**

Define component ranges explicitly:

```python
SEMANTIC_STRUCTURE = {
    "theme": slice(0, 4),      # 4D one-hot-ish (mystery, romance, etc.)
    "pacing": slice(4, 6),     # 2D (action density, dialogue ratio)
    "character": slice(6, 14), # 8D (4 chars × 2 aspects each)
    "plot": slice(14, 17),     # 3D (tension, foreshadowing, resolution)
    "style": slice(17, 20),    # 3D (formality, descriptiveness, humor)
}
```

**Option 2: Learned decomposition with auxiliary losses**

Let the network learn the decomposition, but encourage it via:

```python
# Disentanglement loss (e.g., β-VAE style)
# Encourage statistical independence between component groups

def disentanglement_loss(z, structure):
    losses = []
    components = [z[:, s] for s in structure.values()]

    # Encourage low mutual information between components
    for i, comp_i in enumerate(components):
        for j, comp_j in enumerate(components):
            if i < j:
                # Pearson correlation
                corr = torch.corrcoef(torch.stack([comp_i.mean(0),
                                                     comp_j.mean(0)]))[0, 1]
                losses.append(corr.abs())

    return sum(losses) / len(losses)
```

### Preventing Collapse: Practical Tips

From the JEPA paper, collapse manifests as:

```
Batch variance of z_x < 1e-7
```

**Detection:**

```python
def check_collapse(z, threshold=1e-5):
    var = z.var(dim=0).mean().item()
    if var < threshold:
        print(f"⚠️  Possible collapse detected: var={var:.2e}")
        return True
    return False
```

**Prevention strategies:**

1. **EMA target encoder** (most important)
2. **Variance regularization** (safety net)
3. **Task gradient backprop** (if applicable)
4. **Initialization:** Start both encoders with same weights
5. **Learning rate:** Use lower LR for y-encoder updates (implicit in EMA)
6. **Batch size:** Larger batches → more stable variance estimates

### Computational Cost

**Compared to baseline GPT:**

| Component | Cost | Notes |
|-----------|------|-------|
| x-encoder forward | +1× transformer pass | Comparable to GPT layer |
| y-encoder forward | +1× transformer pass | No gradients |
| Predictor | +0.1× (shallow MLP) | Negligible |
| Shape calculation | +0.01× (means) | Negligible |
| JEPA loss backward | +1× encoder grads | Similar to GPT backward |
| Shape loss backward | +0.1× encoder grads | Adds to JEPA grads |

**Total:** ~2-3× training cost of baseline GPT (two encoder passes + one decoder pass).

**Inference:** If you freeze the encoder after training, inference cost is:
- One encoder pass (amortized over context)
- Standard GPT decoding

So inference overhead is minimal (you're encoding context anyway).

### Data Requirements

**Good news:** JEPA is self-supervised, so you don't need labeled shape invariants.

**Data format:**

```
{
    "context": [tokens at t-k to t],
    "target": [tokens at t to t+k],
    "action_hint": next_token (for teacher forcing)
}
```

This is the same data you'd use for language modeling!

**Curriculum:**

1. **Short sequences first** (128 tokens) - learn local structure
2. **Medium sequences** (512 tokens) - learn paragraph-scale coherence
3. **Long sequences** (2048+ tokens) - learn document-scale structure

### Monitoring During Training

**Key metrics:**

```python
# 1. Embedding variance (detect collapse)
z_var = z_x.var(dim=0).mean()

# 2. JEPA prediction error
jepa_error = (z_pred - z_y).pow(2).mean()

# 3. Shape preservation error
shape_error = sum((k_pred[key] - k_target[key]).pow(2).mean()
                   for key in k_pred.keys())

# 4. Individual shape coefficients (interpretability)
for key, value in k_pred.items():
    wandb.log({f"shape/{key}": value.mean()})

# 5. Shape trajectory smoothness
# Track k values over sequence, measure variance
k_theme_trajectory = [k_t["k_theme"] for k_t in k_history]
k_smoothness = np.var(k_theme_trajectory)
```

**Healthy training:**

- `z_var` > 0.01 (no collapse)
- `jepa_error` decreasing
- `shape_error` decreasing
- `k_*` values stable within episodes, smooth transitions between episodes

---

## Theoretical Implications

### 1. Factorization of Signal into Influence and Magnitude

Classical information theory gives us:

```
I(X; Y) = H(X) - H(X|Y)
```

Mutual information between variables X and Y.

But this doesn't distinguish:
- **Influence**: How much does X affect the evolution of Y?
- **Strength**: How much information does X carry in total?

**Example:**

In an image:
- Background pixels: High strength (lots of bits), low influence (doesn't affect prediction)
- Pole position: Low strength (few pixels), high influence (crucial for prediction)

The Pythagorean means + JEPA combination operationalizes this distinction:

```
JEPA latent space → encodes high-influence features
Pythagorean invariants → factor influence into shape vs magnitude
```

This gives us a **three-level hierarchy**:

1. **Raw signal** (pixels, tokens) - strength-dominated
2. **JEPA embedding** (latent features) - influence-filtered
3. **Shape invariants** (geometric structure) - magnitude-invariant

### 2. Geodesics in Semantic Space

If we think of the latent space as a Riemannian manifold, the shape-preserving constraint is asking:

*"Navigate along trajectories that preserve the local geometric structure."*

This is analogous to **parallel transport** in differential geometry:

When moving a vector along a curved surface, parallel transport preserves the vector's "shape" relative to the local geometry.

In our case:
- The "vector" is the semantic state `z`
- The "surface" is the narrative manifold
- "Parallel transport" = preserving shape invariants during generation

**Formally:**

Let `M` be the semantic manifold, and `γ(t)` be a trajectory in `M`:

```
γ: [0, T] → M
γ(t) = z_t (semantic state at time t)
```

We want `γ` to satisfy:

```
∇_γ̇ k = 0
```

Where `k` is the vector of shape invariants, and `∇` is the covariant derivative.

In plain English: **The shape invariants should change smoothly (or not at all) as we move along the trajectory.**

Our loss function is a discretized, soft version of this:

```
L_shape = Σ ||k(z_t) - k(z_{t-1})||²
```

### 3. Universal Approximation with Geometric Constraints

A concern: **Does adding shape constraints reduce expressivity?**

**Answer:** Not fundamentally. The shape invariants constrain the *geometry* of trajectories, not the *reachability* of states.

**Analogy:**

Imagine navigating a city:
- **No constraints:** You can teleport anywhere instantly (high expressivity, no coherence)
- **Road network:** You must follow streets (geometric constraint, still reach all locations)

Shape constraints are like the road network: They enforce **how** you get from A to B, not **whether** you can get there.

**Formal argument:**

The space of trajectories with bounded shape variation is:

```
T_k = {γ: [0,T] → M | ||k(γ(t+1)) - k(γ(t))|| < ε ∀t}
```

This is still an **infinite-dimensional space** (infinite ways to smoothly evolve).

Constraining shape is analogous to adding smoothness regularization (like in splines), which:
- ✓ Reduces overfitting
- ✓ Improves interpolation
- ✓ Maintains expressivity for well-posed problems

### 4. Connection to Active Inference and Free Energy

In active inference, agents minimize **variational free energy**:

```
F = -log P(observations) + KL(beliefs || prior)
```

This naturally balances:
- **Accuracy** (fit observations)
- **Complexity** (stay close to prior)

The shape-preserving loss has a similar flavor:

```
L_total = L_prediction + λ·L_shape
```

Where:
- `L_prediction` = accuracy (JEPA loss + GPT loss)
- `L_shape` = complexity regularization (stay on the semantic manifold)

**Interpretation:** We're giving the model a **geometric prior** over semantic trajectories.

Instead of saying "stay close to this specific embedding," we say "maintain this geometric structure."

This is a **weaker** (more flexible) prior than point-wise regularization, but **stronger** (more structured) than no regularization.

### 5. Relation to Symmetry and Invariance

**Fundamental insight:** Shape coefficients `k = GM/AM` are **scale-invariant**.

This is a **gauge symmetry**:

```
z → λ·z  (rescaling)
k(z) → k(λ·z) = k(z)  (invariant)
```

In physics, gauge symmetries are profound - they often reveal conserved quantities (Noether's theorem).

**What is conserved in our system?**

The **relational structure** between semantic components.

If theme and pacing have shape `k_theme_pacing = 0.9` (balanced), this relationship is invariant to:
- Overall "loudness" of the representation (scaling)
- Absolute values of individual components

**This is why shape invariants are powerful:** They capture **intrinsic geometry** that transcends arbitrary choices of scale.

### 6. Learning as Geometry Discovery

Standard deep learning: **Learn a function `f: X → Y`**.

JEPA: **Learn a latent space where prediction is simple.**

JEPA + Shape: **Learn a latent space with explicit geometric structure where prediction respects intrinsic invariants.**

This is moving from:
- **Function approximation** → **Representation learning** → **Geometry discovery**

The model isn't just memorizing patterns; it's discovering the **low-dimensional geometric skeleton** that governs the data.

---

## Experimental Validation Path

### Phase 1: Proof of Concept (Week 1-2)

**Goal:** Verify that shape-preserving loss prevents collapse and improves coherence on a toy task.

**Task:** Cart Pole from images (replicate JEPA RL paper)

**Metrics:**
1. ✓ Embedding variance > threshold (no collapse)
2. ✓ JEPA prediction error decreases
3. ✓ Shape coefficients are stable within episodes
4. ✓ RL performance comparable to baseline

**Implementation:**
- Use JEPA architecture from paper
- Add shape loss over (cart_position, pole_angle) components
- Track `k_cart_pole = GM(pos, angle) / AM(pos, angle)`

**Success criteria:**
- Model trains without collapse
- Shape coefficient remains ±0.1 within episodes
- RL performance within 10% of baseline

**Estimated compute:** 1 GPU-day (CartPole is fast)

---

### Phase 2: Text Coherence (Week 3-4)

**Goal:** Demonstrate that shape invariants improve long-form text coherence.

**Dataset:** WikiText-103 or PG-19 (long documents)

**Architecture:**
- Small GPT (e.g., 124M params like GPT-2 small)
- JEPA encoder (6 layers, d=256)
- Structured semantic space (16D total)

**Semantic structure:**
```
topic: 4D (narrative, expository, dialogue, description)
formality: 2D (casual, formal)
complexity: 2D (simple, complex)
sentiment: 2D (positive, negative)
coherence: 2D (local, global)
```

**Baseline comparisons:**
1. **GPT baseline** (standard language model)
2. **VAE-GPT** (VAE latent space, no shape constraint)
3. **JEPA-GPT** (no shape constraint)
4. **JEPA-GPT + Shape** (our approach)

**Metrics:**
1. **Perplexity** (fluency)
2. **Embedding drift** over 1000 tokens:
   ```
   drift = ||z_1000 - z_0|| / 1000
   ```
3. **Shape stability**:
   ```
   stability = 1 - var([k_t for t in range(1000)])
   ```
4. **Human evaluation** (coherence at 500+ tokens)

**Evaluation procedure:**
- Generate 100 samples of 1000 tokens each
- Measure drift and stability
- Rank samples by coherence (human annotators)

**Success criteria:**
- Shape-constrained model has ≤50% drift of baseline
- Shape coefficients vary <0.2 over 1000 tokens
- Human preference for shape-constrained outputs ≥60%

**Estimated compute:** 4 GPU-days (small model, limited training)

---

### Phase 3: Narrative Generation (Week 5-8)

**Goal:** Generate coherent multi-paragraph stories.

**Dataset:** Writing Prompts dataset, ROC Stories, or custom fiction dataset

**Semantic structure:**
```
theme: 6D (adventure, mystery, romance, horror, comedy, drama)
pacing: 3D (action_density, dialogue_ratio, description_ratio)
character_state: 8D (protagonist emotions/agency, antagonist emotions/agency)
plot: 4D (exposition, rising_action, climax, resolution)
tone: 3D (serious, humorous, suspenseful)
```

**Training:**
1. Pre-train JEPA encoder on story corpus (self-supervised)
2. Fine-tune with GPT decoder
3. Add shape constraints gradually (curriculum: 0 → 0.1 → 0.5)

**Evaluation:**

**Automatic metrics:**
1. **Thematic drift:**
   ```
   # Encode story in chunks
   z_chunks = [encode(story[i:i+100]) for i in range(0, len(story), 100)]
   k_theme = [GM(z.theme) / AM(z.theme) for z in z_chunks]
   drift = variance(k_theme)
   ```

2. **Character consistency:**
   ```
   # Track character embedding stability
   char1_trajectory = [z.character[:2] for z in z_chunks]
   consistency = 1 - variance(char1_trajectory)
   ```

3. **Plot structure adherence:**
   ```
   # Check if plot dimensions follow expected arc
   plot_trajectory = [z.plot for z in z_chunks]
   # Expected: [high_exposition, rising_action, peak_climax, resolution]
   correlation_with_ideal_arc = ...
   ```

**Human evaluation:**
- Generate 50 stories (500-1000 words each)
- Annotators rate on 5-point scale:
  1. Thematic coherence
  2. Character consistency
  3. Plot structure
  4. Overall quality

**Success criteria:**
- Thematic drift <30% of baseline
- Character consistency >70%
- Plot structure correlation >0.6
- Human quality rating ≥4.0/5.0

**Estimated compute:** 20 GPU-days (medium model, longer sequences)

---

### Phase 4: Ablation Studies (Week 9-10)

**Question:** Which components matter?

**Variants to test:**

1. **No shape loss** (λ_shape = 0)
2. **Shape on random components** (k over arbitrary dimension pairs)
3. **Only global shape** (k over entire embedding, not structured)
4. **Different means:**
   - HM/AM ratio instead of GM/AM
   - Quadratic mean (RMS)
5. **Different semantic structures:**
   - Coarse (4D total)
   - Medium (16D - default)
   - Fine (64D)

**Metrics:**
- Coherence (embedding drift)
- Fluency (perplexity)
- Human preference

**Expected findings:**

| Variant | Coherence | Fluency | Interpretation |
|---------|-----------|---------|----------------|
| No shape loss | Low | High | Baseline: fluent but drifts |
| Random components | Low | Medium | Shape constraint needs semantic structure |
| Global shape only | Medium | High | Better than nothing, but misses fine structure |
| HM/AM ratio | Medium | Medium | Different geometry, may work but less balanced |
| Coarse structure | Medium | High | Not enough expressivity |
| Fine structure | High | Medium | Risk of overfitting/complexity |

---

### Phase 5: Scaling (Week 11-12)

**Goal:** Test whether approach scales to larger models and longer sequences.

**Experiments:**

1. **Model size:** 124M → 350M → 1.3B params
2. **Sequence length:** 512 → 2048 → 8192 tokens
3. **Dataset size:** 100M → 1B → 10B tokens

**Metrics:**
- Training stability (collapse rate)
- Inference speed (overhead)
- Coherence at different scales

**Expected challenges:**

1. **Memory:** Two encoder passes + one decoder pass
   - *Mitigation:* Gradient checkpointing, mixed precision

2. **Compute:** ~2-3× training cost
   - *Mitigation:* Use smaller encoder than decoder (e.g., encoder=6 layers, decoder=12 layers)

3. **Collapse at scale:** Larger models may be more prone to mode collapse
   - *Mitigation:* Stronger variance regularization, larger batch sizes

**Success criteria:**
- Model scales to 1B+ params without collapse
- Coherence improvements hold at 2048+ tokens
- Training time <3× baseline GPT

---

### Phase 6: Real-World Application (Week 13-16)

**Goal:** Deploy in a practical setting.

**Candidate applications:**

**A. Long-form content generation**
- Blog posts, technical documentation, stories
- **Evaluation:** User study comparing shape-constrained vs baseline
- **Metrics:** Completion rate, user satisfaction, edit distance

**B. Dialogue systems**
- Multi-turn conversations with personality consistency
- **Evaluation:** Character consistency across 20+ turn conversations
- **Metrics:** Personality drift, user engagement

**C. Code generation**
- Multi-file codebases with architectural consistency
- **Evaluation:** Does generated code follow consistent patterns?
- **Metrics:** Style consistency, architectural coherence

**D. Scientific writing**
- Generate paper sections maintaining methodological coherence
- **Evaluation:** Do different sections align on approach?
- **Metrics:** Citation coherence, methodological consistency

**Success criteria:**
- User preference >60% for shape-constrained outputs
- Measurable reduction in human editing required
- Practical deployment feasible (latency, cost)

---

## Beyond Narrative: Universal Applications

### 1. Reinforcement Learning (The Original Context)

**Active inference agents** (like MacGyver) could use shape invariants for:

**A. Policy introspection**

Track `k_explore` over episodes:
```
Episode 1: mean(k_explore) = 0.92  (balanced exploration-exploitation)
Episode 50: mean(k_explore) = 0.35  (shifted to exploitation)
```

**Use case:** Detect when agent has converged vs still exploring.

**B. Transfer learning**

Compare shape signatures across tasks:
```
Task A: k_explore = 0.8, k_efficiency = 0.6
Task B: k_explore = 0.8, k_efficiency = 0.6
→ Similar decision geometry, good transfer candidate
```

**C. Curriculum design**

Order tasks by shape complexity:
```
Easy tasks: k values stable (low variance)
Hard tasks: k values fluctuate (high variance)
→ Train on stable tasks first
```

---

### 2. Multi-Agent Systems

**Problem:** Coordinating multiple agents with different reward functions.

**Solution:** Use shape invariants to measure **strategic alignment**.

**Example: Team of robots**

Robot A: {explore: 0.7, efficiency: 0.8}
Robot B: {explore: 0.72, efficiency: 0.78}
Robot C: {explore: 0.2, efficiency: 0.9}

**Interpretation:**
- A and B have similar strategies (balanced exploration)
- C is pure exploitation specialist
- Team composition is complementary

**Use case:** Dynamic team formation based on shape compatibility.

---

### 3. Scientific Discovery

**Problem:** Exploring chemical/material space while maintaining synthetic feasibility.

**Representation:**
```
z_molecule = [novelty, synthesizability, property_target, stability]
```

**Shape invariants:**
```
k_novelty_feasibility = GM(novelty, synthesizability) / AM(...)
```

**Search strategy:**
- High `k`: Balanced exploration (novel but feasible)
- Low `k`: Speculative (highly novel, uncertain feasibility)

**Use case:** Guide generative models to propose molecules with desired geometric properties in chemical space.

---

### 4. Recommendation Systems

**Problem:** Balancing exploration (diverse recommendations) vs exploitation (known preferences).

**Representation:**
```
z_recommendation = [user_preference_match, novelty, diversity, serendipity]
```

**Shape invariants:**
```
k_exploration = GM(preference_match, novelty) / AM(...)
k_diversity = GM(diversity, serendipity) / AM(...)
```

**Use case:**
- Personalized exploration: tune `k` based on user history
- Avoid filter bubbles: enforce minimum `k_diversity`

---

### 5. Time Series Forecasting

**Problem:** Maintaining structural properties during long-horizon prediction.

**Example: Economic forecasting**

```
z_economy = [gdp_growth, inflation, unemployment, consumer_sentiment]
```

**Shape invariants:**
```
k_phillips_curve = GM(inflation, unemployment) / AM(...)
```

**Constraint:** Phillips curve relationship should remain stable across forecasts.

**Use case:** Ensure long-horizon economic forecasts respect known structural relationships.

---

### 6. Creative Design

**Problem:** Generating novel designs while maintaining brand identity.

**Example: Logo generation**

```
z_design = [complexity, symmetry, color_balance, brand_alignment]
```

**Shape invariants:**
```
k_brand = GM(brand_alignment, novelty) / AM(...)
```

**Constraint:** Maintain `k_brand` close to exemplar logos.

**Use case:** Generate variations that feel "on-brand" while exploring creative space.

---

### 7. Neuroscience & Brain-Computer Interfaces

**Problem:** Decoding neural signals while maintaining physiological plausibility.

**Representation:**
```
z_neural = [motor_intent, cognitive_load, arousal, attention]
```

**Shape invariants:**
```
k_cognitive_motor = GM(cognitive_load, motor_intent) / AM(...)
```

**Use case:** Detect anomalous brain states (k values outside normal range).

---

### 8. Climate Modeling

**Problem:** Multi-scale climate predictions respecting physical constraints.

**Representation:**
```
z_climate = [temperature, precipitation, ocean_currents, ice_coverage]
```

**Shape invariants:**
```
k_water_cycle = GM(precipitation, ocean_currents) / AM(...)
```

**Physical constraint:** Water cycle balance should be preserved across timescales.

**Use case:** Ensure climate models maintain thermodynamic consistency.

---

## Conclusion & Next Steps

### What We've Established

1. **Pythagorean means provide scale-invariant measures of balance** between components.

2. **Shape coefficients (k = GM/AM) capture intrinsic geometric structure** independent of magnitude.

3. **Active inference naturally produces multi-component trade-offs** (goal, info, cost) amenable to shape analysis.

4. **JEPA learns influence-sensitive representations** by predicting in latent space rather than pixel space.

5. **Combining JEPA with shape-preserving constraints** offers a path to coherent long-form generation.

6. **The approach is theoretically grounded** in differential geometry (parallel transport), information theory (influence vs strength), and active inference (free energy).

7. **Implementation is tractable** using standard deep learning tools.

### The Core Innovation

**Factoring latent representations into:**

```
Latent space = Semantic Structure × Magnitude

Where:
- Semantic Structure = preserved via shape invariants (k coefficients)
- Magnitude = free to vary as needed for fluency
```

This is a **gauge symmetry** that makes certain properties invariant to rescaling.

### Immediate Next Steps

**For the MacGyver demo:**

1. ✅ You already have `scoring_silver.py` computing shape invariants
2. ➡️ Visualize k_explore and k_efficiency trajectories in Neo4j
3. ➡️ Create dashboard showing:
   - Shape invariants over time
   - Phase transitions (exploration → exploitation)
   - Efficiency patterns

**For JEPA-GPT:**

1. ➡️ Implement toy version on WikiText-103 (Phase 2 above)
2. ➡️ Measure embedding drift with and without shape constraints
3. ➡️ If promising, scale to narrative generation (Phase 3)

### Open Questions

**1. Optimal semantic decomposition?**

How should we factor embeddings into interpretable components?
- Hand-designed (interpretable but limited)
- Learned with auxiliary losses (flexible but may drift)
- Hybrid (bootstrap with hand-designed, refine via learning)

**2. Which invariants matter most?**

Should we constrain:
- All pairwise k coefficients? (comprehensive but high-dimensional)
- Only critical pairs? (efficient but may miss interactions)
- Hierarchical (global k, then component k's)

**3. How tight should constraints be?**

- Soft constraints (loss-based, current approach)
- Hard constraints (project onto manifold)
- Adaptive (tighten when drift detected)

**4. Generalization across domains?**

Will shape invariants learned on one corpus transfer to another?
- If yes: powerful generalization
- If no: need domain-specific shape priors

### Broader Implications

**If this approach works, it suggests:**

1. **Geometry is more fundamental than magnitude** in semantic representations.

2. **Coherence is a geometric property**, not just a statistical one.

3. **We can factor "what to say" (magnitude) from "how things relate" (shape)**.

4. **Invariant structure provides a universal language** for comparing policies, models, and strategies across different scales and domains.

This could be a **principled solution to the long-range coherence problem** in autoregressive generation.

---

## References & Further Reading

### Pythagorean Means
- Bullen, P.S. (2003). *Handbook of Means and Their Inequalities*. Springer.
- Hardy, G.H., Littlewood, J.E., Pólya, G. (1952). *Inequalities*. Cambridge University Press.

### JEPA & Self-Supervised Learning
- LeCun, Y. (2022). "A Path Towards Autonomous Machine Intelligence." *OpenReview*.
- Assran, M., et al. (2023). "Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture." *CVPR*.
- Bardes, A., et al. (2022). "VICReg: Variance-Invariance-Covariance Regularization for Self-Supervised Learning." *ICLR*.

### Active Inference
- Friston, K., et al. (2017). "Active Inference: A Process Theory." *Neural Computation*.
- Parr, T., Pezzulo, G., Friston, K. (2022). *Active Inference: The Free Energy Principle in Mind, Brain, and Behavior*. MIT Press.

### Representation Learning & Disentanglement
- Bengio, Y., et al. (2013). "Representation Learning: A Review and New Perspectives." *PAMI*.
- Higgins, I., et al. (2017). "β-VAE: Learning Basic Visual Concepts with a Constrained Variational Framework." *ICLR*.
- Locatello, F., et al. (2019). "Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations." *ICML*.

### Geometric Deep Learning
- Bronstein, M., et al. (2021). "Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges." *arXiv:2104.13478*.
- Cohen, T., Welling, M. (2016). "Group Equivariant Convolutional Networks." *ICML*.

### Long-Form Text Generation
- Rashkin, H., et al. (2020). "PlotMachines: Outline-Conditioned Generation with Dynamic Plot State Tracking." *EMNLP*.
- Goldfarb-Tarrant, S., et al. (2020). "Content Planning for Neural Story Generation with Aristotelian Rescoring." *EMNLP*.
- Yang, K., et al. (2022). "Re3: Generating Longer Stories With Recursive Reprompting and Revision." *EMNLP*.

---

**Document Version:** 1.0
**Date:** 2025-11-25
**Author:** Claude (with Juan)
**Status:** Theoretical framework + implementation blueprint
