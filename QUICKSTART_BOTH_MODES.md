# Quick Start: Comparing Both Reward Modes

## What This Demonstrates

This project shows how **reward design impacts learned behavior** using the same procedural memory mechanism in two different modes:

1. **NAIVE mode**: Agent learns to "game the metric" (lazy but efficient)
2. **STRATEGIC mode**: Agent learns smart information-gathering strategies

## Quick Demo (5 Minutes)

### 1. Run Naive Mode (Shows Metric Gaming)

```bash
# Run 20 episodes with naive rewards
for i in {1..20}; do
    ./run.sh --door-state $([ $((i % 2)) -eq 0 ] && echo "locked" || echo "unlocked") \
             --use-memory --reward-mode=naive --quiet
done
```

**What you'll see:**
- Early episodes: Mixed strategies
- Late episodes: **go_window spam** (agent learned the lazy path)
- Agent abandons information-gathering

### 2. Run Strategic Mode (Shows Smart Learning)

```bash
# Reset and run 20 episodes with strategic rewards
docker exec -i neo4j44 cypher-shell -u neo4j -p password --encryption=false \
    "MATCH (s:SkillStats) SET s.total_uses=0, s.successful_episodes=0"

for i in {1..20}; do
    ./run.sh --door-state $([ $((i % 2)) -eq 0 ] && echo "locked" || echo "unlocked") \
             --use-memory --reward-mode=strategic --quiet
done
```

**What you'll see:**
- Consistent **peek → act** strategy
- Information-gathering maintained
- Context-appropriate decisions

### 3. Run Full Comparison

```bash
# Comprehensive statistical comparison
NEO4J_URI=bolt://localhost:17687 NEO4J_USER=neo4j NEO4J_PASSWORD=password \
    python3.11 experiments/reward_mode_comparison.py
```

**Output:**
- 50 episodes per mode
- Side-by-side comparison
- Statistical analysis (p-values)
- Skill usage patterns

## Expected Results

### NAIVE Mode (SLOW_PENALTY = 4.0)

**Behavior:**
- Episodes 1-10: Learning phase (1.7 steps avg)
- Episodes 41-50: Pure go_window spam (1.0 steps avg)

**Skill Usage:**
- go_window: 72% (dominant)
- peek_door: 17% (abandoned)
- try_door: 12% (rarely used)

**Sample Late Episodes:**
```
Ep41 (unlocked): go_window (1 step) ← LAZY!
Ep42 (locked):   go_window (1 step)
Ep43 (unlocked): go_window (1 step)
```

**Lesson:** Agent optimizes steps, not strategy. This is metric gaming!

---

### STRATEGIC Mode (SLOW_PENALTY = 6.0)

**Behavior:**
- Episodes 1-10: Learning phase (2.3 steps avg)
- Episodes 41-50: Stable strategy (2.0 steps avg)

**Skill Usage:**
- peek_door: 52% (maintained)
- try_door: 24% (when unlocked)
- go_window: 23% (when locked)

**Sample Late Episodes:**
```
Ep41 (unlocked): peek → try_door (2 steps) ← SMART!
Ep42 (locked):   peek → go_window (2 steps)
Ep43 (unlocked): peek → try_door (2 steps)
```

**Lesson:** Agent gathers information, then acts optimally based on context.

---

## Key Takeaways

### 1. Same Memory Mechanism → Different Outcomes

Both modes use **identical procedural memory** - the only difference is SLOW_PENALTY (4.0 vs 6.0).

This proves: **What you measure determines what you get.**

### 2. Metric Gaming is Real

Naive mode shows how agents can optimize the wrong thing. This happens in real AI systems!

### 3. Reward Design is Critical

Strategic mode shows that **small reward changes** (4.0 → 6.0) can produce **dramatically better behavior**.

### 4. Intelligence vs. Efficiency

- Naive: More efficient (1.2 steps) but less intelligent (no reasoning)
- Strategic: Less efficient (2.0 steps) but more intelligent (informed decisions)

**Which is better?** Depends on your goals! That's the lesson.

---

## Interactive Exploration

### Try Different Scenarios

```bash
# Watch a single episode with verbose memory reasoning
./run.sh --door-state locked --use-memory --reward-mode=strategic --verbose-memory

# Compare baseline (no memory) vs memory
./run.sh --door-state locked                           # baseline
./run.sh --door-state locked --use-memory              # with memory (strategic)
./run.sh --door-state locked --use-memory --reward-mode=naive  # with memory (naive)
```

### Query Learning Stats

```bash
# Check what the agent learned
docker exec neo4j44 cypher-shell -u neo4j -p password --encryption=false \
    "MATCH (s:Skill)-[:HAS_STATS]->(stats)
     RETURN s.name, stats.total_uses, stats.successful_episodes"
```

---

## For Educators

### Classroom Activity (30 minutes)

1. **Demonstrate Problem** (10 min)
   - Run naive mode, show metric gaming
   - Ask: "Why did the agent do this?"

2. **Discuss Solution** (10 min)
   - Explain reward design impact
   - Ask: "How should we fix this?"

3. **Show Fix** (10 min)
   - Run strategic mode
   - Compare results side-by-side
   - Discuss: Intelligence vs. efficiency trade-off

### Discussion Questions

- Is the naive agent "wrong"? (No - it optimizes what we measured!)
- How does this relate to real AI systems?
- What other reward structures could we try?
- When is efficiency more important than intelligence?

---

## Technical Details

### Reward Structure Differences

**NAIVE (SLOW_PENALTY = 4.0):**
```python
go_window score = 10.0 (escape) - 4.0 (slow) - 0.6 (cost) = 5.4
peek_door score = 0.0 (no goal) + 6.0 (info) - 0.3 (cost) = 5.7

# Initially peek wins, but with memory:
go_window + memory = 5.4 + 1.5 (100% success) = 6.9  ← Wins!
```

**STRATEGIC (SLOW_PENALTY = 6.0):**
```python
go_window score = 10.0 (escape) - 6.0 (slow) - 0.6 (cost) = 3.4
peek_door score = 0.0 (no goal) + 6.0 (info) - 0.3 (cost) = 5.7

# Even with memory:
go_window + memory = 3.4 + 1.5 = 4.9  ← Still loses to peek!
```

This shows how a 2-point penalty difference creates completely different behavior.

---

## Next Steps

**For Students:**
- Try creating your own reward mode
- Experiment with different SLOW_PENALTY values
- Modify the scenario (add new skills, hidden states)

**For Researchers:**
- Extend to more complex environments
- Test different memory architectures
- Compare to other learning algorithms

**For Practitioners:**
- Use as template for reward design testing
- Apply lessons to real system design
- Demonstrate to stakeholders why metrics matter

---

## Support

**Issues?** Check RED_TEAM_FINAL_ASSESSMENT.md for detailed analysis

**Questions?** See full documentation in README.md

**Want to extend?** Architecture is clean and well-tested (80/80 tests passing)

---

**Key Message:** The comparison between modes is the lesson. Both modes work correctly - they just optimize for different things. That's exactly the point!
