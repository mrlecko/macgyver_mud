# Generalization Approach: From Toy Domain to Real-World Applications

**Date:** November 22, 2025
**Status:** Strategic Planning Document
**Purpose:** Define rigorous methodology for extending Critical State Protocols beyond discrete, low-dimensional test environments

---

## Executive Summary

The MacGyver MUD project successfully demonstrates that hybrid meta-cognitive architectures (optimization + rule-based overrides) can improve robustness in **discrete, fully-observable, short-horizon environments**. However, this is a narrow domain. This document outlines a rigorous, multi-phase approach to test whether the core principles generalize to:

1. Continuous state/action spaces
2. High-dimensional observations (vision, sensor arrays)
3. Partial observability (POMDPs)
4. Long time horizons (1000+ steps)
5. Real-world robotics with safety constraints

**Central Question:** Are Critical State Protocols a fundamental pattern for robust AI, or do they only work in carefully constructed toy problems?

---

## Part I: Core Technical Challenges

### Challenge 1: Entropy in Continuous State Spaces

**Current System:**
- Discrete belief distribution over 2-3 states
- Shannon entropy: $H = -\sum p_i \log p_i$
- Clean threshold: "if entropy > 0.45, trigger PANIC"

**Real-World Problem:**
- State space is $\mathbb{R}^n$ (e.g., robot joint angles, velocities)
- Belief is a continuous distribution (Gaussian, mixture, particle filter)
- Differential entropy $h(X) = -\int p(x) \log p(x) dx$ requires density estimation

**Technical Solutions (Ranked by Feasibility):**

1. **Ensemble Disagreement (Practical)**
   - Train 5-10 Q-networks with different initializations
   - Entropy proxy: $\text{Var}[Q_1(s,a), ..., Q_K(s,a)]$
   - High variance = high uncertainty = PANIC
   - **Pros:** Simple, no density estimation needed
   - **Cons:** Requires maintaining multiple models

2. **Particle Filter Entropy (Principled)**
   - Represent belief as weighted particles: $\{(s_i, w_i)\}_{i=1}^N$
   - Compute empirical entropy over particles
   - **Pros:** Theoretically sound for POMDPs
   - **Cons:** Computationally expensive (1000+ particles)

3. **Gaussian Approximation (Fast)**
   - Assume belief is Gaussian: $\mathcal{N}(\mu, \Sigma)$
   - Use analytical entropy: $h = \frac{1}{2} \log|\Sigma| + \text{const}$
   - **Pros:** Closed-form, fast
   - **Cons:** Wrong if belief is multi-modal

4. **Quantization (Fallback)**
   - Discretize continuous space into grid
   - Apply discrete entropy
   - **Pros:** Reuses existing code
   - **Cons:** Curse of dimensionality (grid size grows as $M^n$)

**Recommendation:** Start with **Ensemble Disagreement**. It's practical, interpretable, and already used in Bootstrapped DQN / TD3.

---

### Challenge 2: Deadlock Detection in Continuous Spaces

**Current System:**
- Exact state matching: "if $s_t = s_{t-2}$ and $s_{t-1} = s_{t-3}$, loop detected"
- Works for discrete states {A, B, C}

**Real-World Problem:**
- States never repeat exactly in continuous domains
- Robot might oscillate near a position without exact cycles

**Technical Solutions:**

1. **ε-Proximity Loops (Simple)**
   - Define loop if $\|s_t - s_{t-k}\| < \epsilon$ for some window $k$
   - Choose $\epsilon$ adaptively (e.g., 5% of typical state range)
   - **Pros:** Straightforward extension
   - **Cons:** Sensitive to $\epsilon$ choice, may miss slow drifts

2. **Trajectory Clustering (Robust)**
   - Embed last $N$ states as vector: $z_t = [s_{t-N}, ..., s_t]$
   - Use DBSCAN to detect repeating clusters in trajectory space
   - **Pros:** Detects complex loops
   - **Cons:** Requires trajectory history storage

3. **Information-Theoretic (Principled)**
   - Compute mutual information: $I(s_{t-k:t}; s_{t+1:t+k})$
   - Low MI = future predictable from past = stuck in attractor
   - **Pros:** Theoretically grounded
   - **Cons:** Computationally intensive

4. **Lyapunov Function Proxy (Control Theory)**
   - Define "progress metric" $V(s)$ toward goal
   - Deadlock if $\frac{d V}{dt} \approx 0$ over window
   - **Pros:** Natural for control tasks
   - **Cons:** Requires task-specific $V$ function

**Recommendation:** Use **ε-Proximity Loops** for initial testing, upgrade to **Trajectory Clustering** if needed.

---

### Challenge 3: Action Exploration in Continuous Control

**Current System:**
- Discrete actions: {move_to_B, move_to_C, move_to_D}
- Exploration: "pick action NOT in learned set"

**Real-World Problem:**
- Action space is $\mathbb{R}^m$ (e.g., 7-DOF robot arm torques)
- What does "explore a new action" mean?

**Technical Solutions:**

1. **Noise Injection (Standard RL)**
   - Add Gaussian noise: $a' = a + \mathcal{N}(0, \sigma^2 I)$
   - Increase $\sigma$ when HUBRIS/PANIC triggered
   - **Pros:** Already used in DDPG/TD3
   - **Cons:** Random, not necessarily "novel"

2. **Intrinsic Motivation Boost (Principled)**
   - Add curiosity bonus: $r' = r + \beta \cdot \text{Novelty}(s, a)$
   - Increase $\beta$ during critical states
   - Use count-based, prediction-error, or RND for novelty
   - **Pros:** Directed exploration
   - **Cons:** Requires novelty model

3. **Policy Entropy Regularization (Practical)**
   - Maximize $H[\pi(a|s)]$ during PANIC
   - Forces policy to be multi-modal, less deterministic
   - **Pros:** Fits naturally in actor-critic
   - **Cons:** May degrade performance

4. **Option Discovery (Hierarchical)**
   - Maintain library of skills/options
   - HUBRIS: Try unused options
   - **Pros:** Structured exploration
   - **Cons:** Requires hierarchical RL framework

**Recommendation:** **Noise Injection** for simplicity, **Intrinsic Motivation Boost** for rigor.

---

### Challenge 4: Threshold Adaptation

**Current System:**
- Hard-coded: `PANIC_ENTROPY = 0.45`, `HUBRIS_STREAK = 6`
- Tuned by hand for 5-step MUD

**Real-World Problem:**
- Different tasks need different thresholds
- Even same task might need different thresholds at different skill levels

**Technical Solutions:**

1. **Meta-Learning (MAML-style)**
   - Outer loop: Optimize thresholds $\theta = \{\tau_\text{panic}, \tau_\text{hubris}, ...\}$
   - Inner loop: Run episodes with current $\theta$
   - Update $\theta$ via gradient of meta-objective (e.g., safety violations)
   - **Pros:** Principled, learns from experience
   - **Cons:** Requires large dataset of tasks

2. **Bayesian Optimization (Sample-Efficient)**
   - Treat thresholds as hyperparameters
   - Use Gaussian Process to model performance $f(\theta)$
   - Iteratively select $\theta$ to maximize expected improvement
   - **Pros:** Sample-efficient
   - **Cons:** Black-box, no interpretability

3. **Self-Tuning via Performance Feedback (Practical)**
   - Start with conservative thresholds (trigger early)
   - If false positive rate > target, relax thresholds
   - If catastrophic failure occurs, tighten thresholds
   - **Pros:** Simple, online
   - **Cons:** May oscillate

4. **Context-Dependent Thresholds (Conditional)**
   - Learn $\tau(s, \text{history})$ as function of state
   - E.g., PANIC threshold higher in "safe" regions, lower near cliffs
   - **Pros:** Adaptive to environment structure
   - **Cons:** Adds model complexity

**Recommendation:** Start with **Self-Tuning**, upgrade to **Bayesian Optimization** if budget allows.

---

### Challenge 5: Computational Overhead

**Current System:**
- Neo4j query every step (10-50ms)
- JSON serialization (5-10ms)
- Geometric analysis (2-5ms)
- **Total:** 20-65ms per decision

**Real-World Requirements:**
- Robotics: <10ms decision latency
- Games: <16ms (60 FPS)
- Autonomous vehicles: <100ms

**Technical Solutions:**

1. **Remove Neo4j (Essential)**
   - Replace with in-memory circular buffer
   - Store last 1000 steps in RAM
   - **Speedup:** 10-50ms → <1ms

2. **Simplify Geometric Analysis (Practical)**
   - Precompute entropy only when needed (not every step)
   - Cache recent computations
   - **Speedup:** 2-5ms → <0.5ms

3. **Asynchronous Monitoring (Parallelism)**
   - Run critical state checks in separate thread
   - Main loop always has most recent assessment available
   - **Pros:** Decouples decision latency from analysis latency
   - **Cons:** Slight staleness

4. **Compiled Implementation (Performance)**
   - Rewrite hot paths in C++/Rust
   - Use SIMD for vector operations
   - **Speedup:** 10-100x

**Recommendation:** **Remove Neo4j** immediately. Implement **Asynchronous Monitoring** for real-time systems.

---

## Part II: Generalization Roadmap (4 Phases)

### Phase 1: Analytical Extension (2-4 weeks)

**Goal:** Formalize critical state detection for continuous domains without implementation.

**Tasks:**
1. Derive entropy measures for Gaussian beliefs
2. Prove conditions under which ε-proximity detects loops
3. Analyze threshold sensitivity (∂Performance/∂τ)
4. Identify theoretical failure modes

**Deliverables:**
- Technical report with proofs
- Sensitivity analysis plots
- Failure mode catalog

**Success Criteria:**
- Theoretical framework for continuous case exists
- Can predict when protocols will/won't work
- Identified at least 3 potential failure modes

---

### Phase 2: Continuous Control Benchmarks (6-8 weeks)

**Goal:** Test protocols in standard continuous RL benchmarks.

**Environments (Ordered by Difficulty):**

1. **CartPole-v1 (Baseline)**
   - State: $\mathbb{R}^4$ (position, velocity, angle, angular velocity)
   - Action: Discrete {left, right}
   - Horizon: 500 steps
   - **Why:** Simple, fast iteration, still continuous state

2. **Pendulum-v1 (Continuous Action)**
   - State: $\mathbb{R}^3$ (cos θ, sin θ, velocity)
   - Action: $\mathbb{R}^1$ (torque ∈ [-2, 2])
   - Horizon: 200 steps
   - **Why:** Tests continuous action exploration

3. **HalfCheetah-v4 (Mujoco)**
   - State: $\mathbb{R}^{17}$ (joint positions, velocities)
   - Action: $\mathbb{R}^6$ (joint torques)
   - Horizon: 1000 steps
   - **Why:** Standard benchmark, complex dynamics

4. **Humanoid-v4 (Hard)**
   - State: $\mathbb{R}^{376}$ (high-dim)
   - Action: $\mathbb{R}^{17}$
   - Horizon: 1000 steps
   - **Why:** Tests scalability to high dimensions

**Implementation:**
- Base algorithm: SAC (Soft Actor-Critic) or TD3
- Add critical state layer on top
- Ensemble of 5 Q-networks for entropy estimation

**Baselines:**
- SAC (vanilla)
- SAC + entropy regularization
- SAC + curiosity (RND)

**Metrics:**
1. **Performance:** Average return over 10 seeds
2. **Robustness:** Success rate when environment parameters perturbed ±20%
3. **Sample Efficiency:** Steps to reach 90% of max performance
4. **Catastrophic Failure Rate:** % of episodes with return < -1000

**Success Criteria (Per Environment):**
- Match or exceed SAC baseline in 3/4 metrics
- At least one metric shows ≥20% improvement
- No metric degrades by >10%

**Failure Criteria (Triggers Phase Re-evaluation):**
- Critical states never trigger (irrelevant)
- Critical states trigger every step (false positives)
- Performance < 50% of baseline (overhead too high)

---

### Phase 3: High-Dimensional & Partial Observability (8-12 weeks)

**Goal:** Test in vision-based and partially observable environments.

**Environments:**

1. **Atari Games (Vision)**
   - State: $84 \times 84 \times 4$ grayscale frames
   - Action: Discrete (game-dependent)
   - Horizon: 27,000 steps (30 min gameplay)
   - **Focus Games:**
     - Montezuma's Revenge (sparse rewards, exploration)
     - Breakout (local optima: stuck in corner)
     - Pitfall (deceptive rewards)

2. **DM Control Suite (Pixels)**
   - State: $64 \times 64 \times 3$ RGB
   - Action: Continuous
   - Tasks: Reacher, Walker, Quadruped
   - **Why:** Combines vision + continuous control

3. **POMDPs (Partial Observability)**
   - State: Hidden (e.g., robot localization)
   - Observation: Noisy sensors
   - **Test Environments:**
     - Tiger Problem (classic POMDP)
     - Rocksample (large POMDP)
   - **Why:** Tests belief state entropy

**Technical Additions:**
- Use particle filters or belief RNNs for state estimation
- Entropy computed over belief distribution, not observation
- Deadlock detection in belief space (not observation space)

**New Baselines:**
- DQN, Rainbow (Atari)
- DrQ-v2 (pixel-based)
- POMDP solvers (for small POMDPs)

**Success Criteria:**
- Atari: Improve on at least 2/3 hard exploration games
- DM Control: Match DrQ-v2 on 2/3 tasks
- POMDP: Better than myopic policy on both benchmarks

---

### Phase 4: Real-World Validation (12-16 weeks)

**Goal:** Demonstrate practical value in realistic scenarios.

**Scenario 1: Sim-to-Real Robotic Manipulation**

**Setup:**
- Simulated robot arm (Pybullet/Isaac Gym)
- Task: Pick-and-place with deformable objects
- Critical Challenge: Sim-to-real gap (simulation inaccurate)

**Hypothesis:**
- HUBRIS protocol detects when simulation-trained policy overconfident in real world
- Forces exploration in real environment to discover actual dynamics

**Validation:**
- Train in simulation with critical states
- Deploy on real robot
- Measure: Success rate, damage incidents, adaptation speed

**Success Criteria:**
- Adapt to real robot faster than baseline (fewer real-world samples)
- Zero catastrophic failures (drops, collisions) in 100 trials

---

**Scenario 2: Autonomous Driving (CARLA Simulator)**

**Setup:**
- CARLA urban driving simulator
- Task: Navigate town without collisions
- Critical Challenge: Adversarial scenarios (pedestrian jaywalking, sudden braking)

**Hypothesis:**
- DEADLOCK detects when vehicle stuck in narrow space
- PANIC detects when entering unfamiliar road conditions
- SCARCITY detects when fuel/battery low

**Validation:**
- 1000 test episodes with random scenarios
- Measure: Collision rate, route completion, fuel efficiency

**Success Criteria:**
- Collision rate < 1% (vs. baseline 5-10%)
- No "stuck" incidents (timeout without progress)

---

**Scenario 3: Multi-Agent Coordination**

**Setup:**
- 3-5 agents cooperating in warehouse task
- Task: Efficient item retrieval, avoid collisions
- Critical Challenge: Distributed decision-making

**Hypothesis:**
- Agents detect HUBRIS when coordination strategy failing
- Agents detect DEADLOCK when agents blocking each other

**Validation:**
- Measure: Task completion time, collision rate, fairness (load balance)

**Success Criteria:**
- Outperform independent learners by ≥30%
- Adaptive to agent failure (1 agent goes offline)

---

## Part III: Rigorous Validation Methodology

### Statistical Requirements

**Minimum Standards:**
- **Seeds:** 10+ random seeds per experiment
- **Confidence Intervals:** Report mean ± 95% CI
- **Hypothesis Testing:** Paired t-test vs. baseline (p < 0.05 for "improvement" claim)
- **Multiple Comparisons:** Bonferroni correction when testing multiple metrics
- **Effect Size:** Report Cohen's d (require |d| > 0.5 for "meaningful")

**Computational Budget:**
- Phase 2: ~500 CPU-hours
- Phase 3: ~2000 GPU-hours
- Phase 4: ~5000 GPU-hours + robot time

---

### Ablation Study Framework

For each environment, test:

1. **Full System** (all 5 protocols)
2. **No Hubris** (test necessity of each protocol)
3. **No Panic**
4. **No Deadlock**
5. **No Novelty**
6. **No Scarcity**
7. **Only Panic** (test sufficiency of each protocol)
8. **Only Hubris**
9. **Etc.**

**Analysis:**
- Which protocols matter most? (performance drop when removed)
- Which are redundant? (no drop when removed)
- Which combinations synergize? (pairwise interactions)

---

### Red Team Scenarios (Adversarial Testing)

**Goal:** Deliberately construct environments where protocols SHOULD fail.

**Adversarial Environment 1: Threshold Hell**
- Design environment where optimal PANIC threshold varies 10x across different regions
- **Expected Outcome:** Fixed thresholds fail, adaptive thresholds succeed
- **Validates:** Need for threshold adaptation

**Adversarial Environment 2: The Crying Wolf**
- High-entropy states are actually safe (e.g., noisy sensors)
- **Expected Outcome:** PANIC triggers constantly, degrades performance
- **Validates:** Need for false positive mitigation

**Adversarial Environment 3: Chaotic Dynamics**
- Environment is inherently chaotic (small state changes → large effects)
- **Expected Outcome:** ε-proximity deadlock detection fails (states never close)
- **Validates:** Limitations of proximity-based methods

**Adversarial Environment 4: Deceptive Gradients**
- Local optima is VERY attractive, global optimum requires passing through penalty
- **Expected Outcome:** HUBRIS triggers but exploration doesn't reach global optimum
- **Validates:** Exploration quality matters, not just quantity

**Adversarial Environment 5: Resource Exhaustion**
- Critical state monitoring consumes 50% of compute budget
- **Expected Outcome:** Performance degrades despite better decisions
- **Validates:** Computational overhead matters

---

### Failure Mode Analysis

For each failure (performance < baseline), conduct root cause analysis:

1. **Protocol Never Triggered:** Irrelevant in this domain
2. **Protocol Always Triggered:** Threshold too sensitive
3. **Protocol Triggered Correctly, No Effect:** Exploration strategy ineffective
4. **Protocol Triggered Incorrectly:** False positive
5. **Computational Overhead:** Latency too high
6. **Threshold Overfitting:** Tuned for training distribution, fails on test

**Document all failure modes in:** `GENERALIZATION_FAILURE_CATALOG.md`

---

## Part IV: Decision Gates (Go/No-Go Criteria)

### After Phase 1 (Analytical Extension)

**Go Criteria:**
- Theoretical framework is sound (no logical contradictions)
- Can derive concrete entropy measures for Gaussian beliefs
- Identified at least 2 promising directions for continuous domains

**No-Go Criteria:**
- Proofs reveal fundamental impossibility (e.g., "entropy meaningless in continuous case")
- Computational complexity is intractable ($O(2^n)$ or worse)
- Theoretical analysis predicts <10% improvement over baseline

**Decision:** If No-Go, pivot to "hybrid discrete-continuous" approach or abandon generalization.

---

### After Phase 2 (Continuous Control)

**Go Criteria:**
- Works in 3/4 benchmark environments (by success criteria above)
- At least 1 environment shows dramatic improvement (≥50%)
- Ablation reveals at least 2 protocols are necessary (not redundant)

**No-Go Criteria:**
- Works in 0/4 or 1/4 environments
- No single protocol shows individual value in ablation
- Computational overhead makes real-time infeasible

**Decision:** If No-Go, protocols may be domain-specific. Publish negative result, identify boundary conditions.

---

### After Phase 3 (High-Dim/POMDP)

**Go Criteria:**
- Vision works in 2/3 Atari games
- POMDP shows value of belief-space monitoring
- No catastrophic regressions from Phase 2

**No-Go Criteria:**
- High-dimensional observations break all protocols
- Belief state entropy estimation too noisy to be useful
- Requires problem-specific engineering for each domain

**Decision:** If No-Go, restrict scope to "low-dim continuous" and document generalization limits.

---

### After Phase 4 (Real-World)

**Go Criteria:**
- Sim-to-real succeeds (adapts faster, zero catastrophic failures)
- At least 1 real-world scenario demonstrates clear practical value
- Can write deployment guide with safety guarantees

**No-Go Criteria:**
- Real-world deployment fails catastrophically
- Sim-to-real gap makes simulation results irrelevant
- Safety certification impossible (protocols unpredictable)

**Decision:** If No-Go, this remains a research contribution, not a deployable system.

---

## Part V: Honest Assessment Framework

### Scoring Rubric (For Each Environment)

| Dimension | Score | Criteria |
|-----------|-------|----------|
| **Performance** | 0-10 | 10 = Exceeds SOTA by ≥20%, 5 = Matches baseline, 0 = < 50% baseline |
| **Robustness** | 0-10 | 10 = Zero failures under perturbations, 5 = Same as baseline, 0 = Catastrophic |
| **Sample Efficiency** | 0-10 | 10 = 2x faster learning, 5 = Same as baseline, 0 = 2x slower |
| **Interpretability** | 0-10 | 10 = Can explain all triggers, 5 = Some explainable, 0 = Black box |
| **Practicality** | 0-10 | 10 = Deployable as-is, 5 = Needs engineering, 0 = Research toy only |

**Overall Assessment:**
- **Sum ≥ 40/50:** Strong generalization
- **Sum 30-39/50:** Promising, needs work
- **Sum 20-29/50:** Limited generalization
- **Sum < 20/50:** Domain-specific only

---

### Publication Strategy

**Tier 1 Venues (If Phase 2-3 Succeed):**
- NeurIPS, ICML, ICLR (main conference)
- CoRL (robotics-focused)
- AAMAS (multi-agent)

**Tier 2 Venues (If Mixed Results):**
- NeurIPS/ICML Workshops (SafeRL, Exploration, Meta-Learning)
- AAAI, IJCAI

**Tier 3 (If Mostly Negative):**
- ArXiv preprint documenting "When Critical States Don't Generalize"
- Workshop on Negative Results

**Intellectual Honesty Requirement:**
- If results are negative, publish them
- Don't cherry-pick successful environments
- Report ALL experiments in appendix

---

## Part VI: Resource Requirements

### Personnel

- **1 Senior Researcher** (PhD-level): Architecture design, theoretical analysis
- **2 ML Engineers**: Implementation, experiments
- **1 Roboticist** (Phase 4 only): Real-world deployment
- **0.5 FTE Statistician**: Experimental design, analysis

### Compute

- **Phase 2:** 20 GPUs for 3 weeks (~500 GPU-hours)
- **Phase 3:** 50 GPUs for 6 weeks (~2000 GPU-hours)
- **Phase 4:** 100 GPUs + 1 robot lab (~5000 GPU-hours + facilities)

### Timeline

- **Phase 1:** Months 1-2
- **Phase 2:** Months 2-4
- **Phase 3:** Months 4-7
- **Phase 4:** Months 7-11
- **Paper Writing:** Months 10-12

**Total Duration:** 12 months
**Total Budget:** $200K-$400K (salaries + compute + robot)

---

## Part VII: Fallback Strategies

### If Full Generalization Fails

**Fallback 1: Hybrid Discrete-Continuous**
- Restrict to environments with discrete high-level actions
- Use continuous low-level controllers
- Apply protocols at high level only

**Fallback 2: Learned Protocols**
- Don't hand-code thresholds
- Learn "when to panic" as meta-policy
- Becomes a meta-RL problem

**Fallback 3: Domain-Specific Instantiation**
- Protocols are a pattern, not a solution
- For each domain, expert defines critical states
- Provide toolkit, not turnkey system

**Fallback 4: Negative Result Publication**
- "Critical State Protocols: A Cautionary Tale"
- Document exactly where/why they fail
- Contribute boundary conditions to literature

---

## Part VIII: Success Scenarios & Claims

### Scenario 1: Full Success (Phases 1-4 All Go)

**Claim:** "Critical State Protocols provide a general framework for robust decision-making across discrete and continuous domains."

**Evidence Required:**
- Works in 8/10 benchmarks (Phase 2-3)
- Real robot deployment successful (Phase 4)
- Theoretical framework sound (Phase 1)
- Published in Tier 1 venue

---

### Scenario 2: Partial Success (Phases 1-2 Go, Phase 3 No-Go)

**Claim:** "Critical State Protocols generalize to continuous control with low-dimensional state spaces."

**Evidence Required:**
- Works in CartPole, Pendulum, HalfCheetah (4/4)
- Fails in high-dim vision tasks
- Theoretical analysis predicts this boundary

**Contribution:** A principled extension to continuous domains with known limitations.

---

### Scenario 3: Negative Result (Phase 2 No-Go)

**Claim:** "Critical State Protocols are fundamentally discrete and do not generalize to continuous domains without significant re-design."

**Evidence Required:**
- Fails in 3/4 or 4/4 continuous benchmarks
- Ablation shows protocols never trigger OR always trigger
- Root cause analysis identifies theoretical incompatibility

**Contribution:** A documented failure mode, valuable for future research.

---

## Conclusion: The Generalization Gauntlet

This document outlines a **4-phase, 12-month, empirically rigorous** approach to testing whether Critical State Protocols generalize beyond toy domains.

**Key Principles:**
1. **Incremental Complexity:** Don't jump to real robots; build up gradually
2. **Rigorous Baselines:** Compare to SOTA, not just naive agents
3. **Statistical Rigor:** 10+ seeds, confidence intervals, hypothesis testing
4. **Honest Assessment:** Publish negative results if they occur
5. **Decision Gates:** Clear Go/No-Go criteria at each phase

**Expected Outcome (Realistic):**
- 60% chance: Partial success (works in continuous, fails in high-dim)
- 30% chance: Full success (generalizes broadly with tuning)
- 10% chance: Fundamental failure (domain-specific only)

**Commitment:**
- If we discover protocols don't generalize, we say so
- If we discover they need domain-specific tuning, we document exact requirements
- We will not overstate claims based on cherry-picked results

**This is the path from toy prototype to publishable research.**
