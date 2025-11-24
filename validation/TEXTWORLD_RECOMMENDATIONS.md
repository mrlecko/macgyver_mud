# TextWorld Integration: Actionable Recommendations

**Date:** 2025-11-24
**For:** Project Lead
**Status:** 🔴 Critical Decision Point

---

## TL;DR

**Problem:** Cognitive agent fails 100% of TextWorld games. Simple LLM wins 100%.

**Root Cause:** Architecture designed for graph navigation, not sequential task execution.

**Recommendation:** Build minimal quest-focused agent. Don't force-fit cognitive architecture.

**Effort:** 4-8 hours (vs 40-60 hours for deep integration).

---

## The Brutal Truth

### What We Have

**Simple LLM Player** (`simple_llm_player.py`)
```
Quest: "Move east, take nest, place in dresser"
Result: ✅ WON in 3 steps
Code: 50 lines
```

**Cognitive Agent** (`cognitive_agent.py`)
```
Quest: "Move east, take nest, place in dresser"
Result: ❌ FAILED after 20 steps (stuck in loop)
Code: 983 lines + 2500 lines supporting infrastructure
```

**Performance Ratio:** Simple LLM is **infinitely better** (100% vs 0% success).

### Why This Happened

The cognitive architecture is optimized for:
- ✅ Exploring unknown graphs
- ✅ Managing uncertainty
- ✅ Breaking spatial loops

TextWorld requires:
- ❌ Following linear instructions
- ❌ Executing known sequences
- ❌ Not exploring (exploration wastes steps)

**It's like using a GPS to follow a recipe.** Wrong tool, wrong job.

---

## Decision Matrix

| Approach | Success Prob | Effort | Architecture Fit | Research Value |
|----------|-------------|--------|------------------|----------------|
| **Option A: Minimal Quest Agent** | 90% | 4-8 hours | Poor (separate impl) | High (honest limits) |
| **Option B: Deep Integration** | 40% | 40-60 hours | Medium (forced fit) | Medium (complex) |
| **Option C: Abandon TextWorld** | N/A | 0 hours | N/A | Low (incomplete) |

**Recommended:** Option A

---

## Option A: Minimal Quest Agent (Recommended)

### Philosophy

"Use the right tool for the job. LLMs excel at sequential reasoning—let them."

### Implementation

Create new file: `environments/domain4_textworld/quest_agent.py`

```python
"""
Minimal Quest-Focused Agent for TextWorld

Philosophy: Keep it simple. TextWorld quests are sequential instructions.
The cognitive architecture is overkill—use LLM for planning, simple execution loop.
"""

class QuestAgent:
    """
    Dead-simple agent that:
    1. Decomposes quest into steps using LLM
    2. Executes steps sequentially
    3. Tracks progress

    No EFE, no beliefs, no protocols. Just "what's next?"
    """

    def __init__(self, verbose=True):
        self.quest_steps = []      # ["go east", "take nest", "insert nest"]
        self.current_step = 0      # Which step we're on
        self.verbose = verbose

    def reset(self, quest: str):
        """Decompose quest at start of episode."""
        self.quest_steps = self._decompose_quest(quest)
        self.current_step = 0

    def step(self, observation: str, admissible_commands: List[str]) -> str:
        """Execute next quest step."""
        if self.current_step >= len(self.quest_steps):
            return "look"  # Quest complete, safe fallback

        # Get current goal
        goal = self.quest_steps[self.current_step]

        # Find matching command
        action = self._match_command(goal, admissible_commands)

        # Check if we should advance (heuristic: did observation change?)
        if self._step_likely_succeeded(observation):
            self.current_step += 1

        return action

    def _decompose_quest(self, quest: str) -> List[str]:
        """
        Use LLM to break quest into action sequence.

        Prompt: "Quest: [X]. Decompose into ordered action list. Format: ['action1', 'action2']"
        """
        # LLM call here
        # For now, simple heuristic parsing
        pass

    def _match_command(self, goal: str, commands: List[str]) -> str:
        """
        Match goal phrase to available command.

        Example:
        - goal: "move east"
        - commands: ["go east", "go west", "look"]
        - return: "go east" (best token overlap)
        """
        pass
```

**Full implementation:** ~200 lines (vs 2500 for cognitive agent)

### Expected Results

- **Success Rate:** 80-90% (vs 0% current)
- **Development Time:** 4-8 hours
- **Maintenance:** Low (simple code, few dependencies)

### What We Learn

1. **When to use cognitive architecture:** Graph exploration, uncertainty, safety-critical
2. **When to use simple LLM:** Sequential tasks, clear instructions, known world
3. **Honest limitations:** Research value in showing boundaries

### Documentation Updates

1. **README:** Add section "Domain-Specific Agents"
   ```markdown
   ## Multi-Domain Support

   - **MacGyver MUD:** Cognitive architecture (navigation, uncertainty)
   - **Graph Labyrinth:** Cognitive architecture (spatial reasoning)
   - **TextWorld:** Quest agent (sequential task execution)

   **Lesson:** Different problem domains need different architectures.
   ```

2. **New Doc:** `docs/ARCHITECTURE_DOMAIN_FIT.md`
   - When cognitive architecture excels
   - When it struggles
   - How to choose the right tool

---

## Option B: Deep Integration (Not Recommended)

### What It Would Take

1. **Quest Decomposition Module** (8-12 hours)
   - Temporal parsing: "first X, then Y"
   - Dependency tracking: X must complete before Y
   - Progress monitoring: X ✅, Y ⏳, Z ⬜

2. **Hierarchical Control Layer** (12-16 hours)
   - Level 1: Quest decomposer (strategic)
   - Level 2: Plan executor (tactical)
   - Level 3: EFE scoring (reactive)
   - Strategic overrides tactical

3. **Loop Detection Overhaul** (4-6 hours)
   - Current: Detects A → A
   - Needed: Detects A → B → A → B (oscillations)

4. **Critical State Re-integration** (6-8 hours)
   - Make protocols quest-aware
   - DEADLOCK should break loops without breaking quests

5. **Progress Tracking** (4-6 hours)
   - Track completed sub-goals
   - Boost "next step" actions
   - Penalize "already done" actions

6. **Testing & Debugging** (8-12 hours)
   - Integration tests
   - Edge cases
   - Performance tuning

**Total:** 42-60 hours

### Risks

- ❌ May still underperform simple LLM (complex systems have emergent bugs)
- ❌ Increases codebase complexity (maintenance burden)
- ❌ Unclear research value (forced fit rather than natural alignment)

### When To Choose This

- If you need to prove architecture is "universal"
- If you have 2-3 weeks of development time
- If deep integration is a research goal

**Current Assessment:** Not worth it. Simple LLM already proves TextWorld is solvable.

---

## Option C: Abandon TextWorld

### Rationale

- MacGyver MUD + Graph Labyrinth already demonstrate cognitive architecture
- TextWorld is fundamentally different problem domain
- Forcing fit dilutes research focus

### Pros

- ✅ No additional development
- ✅ Clear scope: "Cognitive architecture for graph navigation"

### Cons

- ❌ Leaves work incomplete
- ❌ Doesn't learn from failure
- ❌ Misses opportunity to document limitations

**Assessment:** Viable but less valuable than Option A. Better to document "why it doesn't fit" than to abandon.

---

## Detailed Implementation: Option A

### Step 1: Create Quest Decomposer (2 hours)

**File:** `environments/domain4_textworld/quest_decomposer.py`

```python
import subprocess
import json

class QuestDecomposer:
    """
    Breaks TextWorld quests into sequential action goals.

    Uses LLM to parse temporal logic:
    "First, move east. Then, take nest. Finally, place in dresser."
    → ["go east", "take nest", "insert nest into dresser"]
    """

    def decompose(self, quest: str) -> List[str]:
        """
        Convert quest text into ordered action sequence.

        Returns:
            List of action goals (natural language, not commands)
        """
        prompt = f"""
        TextWorld Quest: {quest}

        Decompose this quest into ordered action steps.
        Return JSON array: ["step1", "step2", "step3"]

        Example:
        Quest: "First go north, then take the key, finally unlock the door"
        Output: ["go north", "take key", "unlock door"]

        Output:
        """

        result = subprocess.run(
            ['llm', prompt],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse JSON response
        steps = json.loads(result.stdout.strip())
        return steps
```

### Step 2: Create Command Matcher (1 hour)

```python
class CommandMatcher:
    """
    Matches action goal to admissible command.

    Example:
    - Goal: "go north"
    - Commands: ["go north", "go south", "examine table"]
    - Match: "go north" (exact token overlap)
    """

    def match(self, goal: str, commands: List[str]) -> str:
        """
        Find best command match for goal.

        Uses token overlap scoring:
        - goal: "take key"
        - "take golden key" → score 2/2 = 1.0
        - "examine key" → score 1/2 = 0.5
        - "take chest" → score 1/2 = 0.5 (but different noun)
        """
        goal_tokens = set(goal.lower().split())

        best_score = 0
        best_command = commands[0] if commands else "look"

        for cmd in commands:
            cmd_tokens = set(cmd.lower().split())
            overlap = len(goal_tokens & cmd_tokens)
            score = overlap / len(goal_tokens) if goal_tokens else 0

            if score > best_score:
                best_score = score
                best_command = cmd

        return best_command
```

### Step 3: Create Quest Agent (1 hour)

```python
class QuestAgent:
    """
    Minimal agent for TextWorld quest completion.

    Architecture:
    1. Decompose quest → action sequence
    2. For each step: match goal → admissible command
    3. Track progress → advance when step succeeds
    """

    def __init__(self):
        self.decomposer = QuestDecomposer()
        self.matcher = CommandMatcher()
        self.steps = []
        self.current_step = 0
        self.last_obs = ""

    def reset(self, quest: str):
        self.steps = self.decomposer.decompose(quest)
        self.current_step = 0
        print(f"📋 Quest decomposed into {len(self.steps)} steps:")
        for i, step in enumerate(self.steps, 1):
            print(f"   {i}. {step}")

    def step(self, observation: str, admissible_commands: List[str]) -> str:
        # Check if current step complete
        if self._step_succeeded(observation):
            self.current_step += 1
            print(f"   ✅ Step {self.current_step} complete")

        # Get next action
        if self.current_step < len(self.steps):
            goal = self.steps[self.current_step]
            action = self.matcher.match(goal, admissible_commands)
            print(f"   🎯 Goal: {goal} → Action: {action}")
        else:
            action = "look"  # Quest complete

        self.last_obs = observation
        return action

    def _step_succeeded(self, observation: str) -> bool:
        """
        Heuristic: Did observation change significantly?

        If observation changed, likely action succeeded.
        This is crude but effective for TextWorld.
        """
        if not self.last_obs:
            return False

        # Simple text similarity
        prev_words = set(self.last_obs.lower().split())
        curr_words = set(observation.lower().split())

        # If >40% words changed, step likely succeeded
        total = len(prev_words | curr_words)
        common = len(prev_words & curr_words)
        similarity = common / total if total > 0 else 1.0

        return similarity < 0.6  # Changed significantly
```

### Step 4: Test & Validate (4 hours)

Create `environments/domain4_textworld/test_quest_agent.py`:

```python
def test_quest_agent():
    """Test quest agent on generated games."""
    agent = QuestAgent()

    # Generate 10 test games
    for seed in range(10):
        game = create_game(seed)
        result = run_episode(agent, game, max_steps=20)

        print(f"Seed {seed}: {'✅' if result['success'] else '❌'} "
              f"({result['steps']} steps, {result['reward']:+.1f} reward)")

    # Calculate stats
    success_rate = sum(r['success'] for r in results) / len(results)
    avg_steps = sum(r['steps'] for r in results) / len(results)

    print(f"\n📊 Results:")
    print(f"   Success Rate: {success_rate:.0%}")
    print(f"   Avg Steps: {avg_steps:.1f}")

    assert success_rate >= 0.8, f"Success rate too low: {success_rate:.0%}"
```

**Acceptance Criteria:**
- ✅ Success rate ≥ 80%
- ✅ No loops (max 2 repeated actions)
- ✅ Average steps ≤ 10 (efficient)

---

## Timeline & Milestones

### Week 1: Implementation
- **Day 1:** Quest decomposer + command matcher (3 hours)
- **Day 2:** Quest agent + integration (2 hours)
- **Day 3:** Testing & debugging (4 hours)

### Week 2: Validation
- **Day 1:** Generate 50 test games, run validation suite
- **Day 2:** Compare vs simple LLM baseline
- **Day 3:** Red team edge cases (ambiguous quests, long sequences)

### Week 3: Documentation
- **Day 1:** Update README, write architecture fit doc
- **Day 2:** Write "Lessons from TextWorld" report
- **Day 3:** Create comparison table (cognitive arch vs quest agent vs LLM)

**Total Time:** ~20 hours over 3 weeks (part-time)

---

## Success Metrics

### Quantitative
- **Success Rate:** ≥ 80% (vs 0% current, 100% simple LLM)
- **Steps to Completion:** ≤ 10 average (vs 20+ current)
- **Loop Resistance:** ≤ 2 repeated actions (vs infinite loops current)

### Qualitative
- **Code Simplicity:** ≤ 300 lines (vs 2500 current)
- **Maintainability:** Junior dev can understand in <30 min
- **Research Value:** Demonstrates "architecture-domain fit" insight

---

## What Success Looks Like

### Before (Current State)
```
🧠 Cognitive Agent vs 🤖 Simple LLM

Game 1: ❌ FAILED (loop) vs ✅ WON (3 steps)
Game 2: ❌ FAILED (loop) vs ✅ WON (5 steps)
Game 3: ❌ FAILED (loop) vs ✅ WON (4 steps)

Result: Cognitive agent fundamentally broken for TextWorld.
```

### After (Option A Complete)
```
🎯 Quest Agent vs 🤖 Simple LLM vs 🧠 Cognitive Agent

Game 1: ✅ WON (4 steps) vs ✅ WON (3 steps) vs ❌ FAILED
Game 2: ✅ WON (6 steps) vs ✅ WON (5 steps) vs ❌ FAILED
Game 3: ✅ WON (5 steps) vs ✅ WON (4 steps) vs ❌ FAILED

Result: Quest agent works. Different domains need different tools.

Documentation:
- README: "Multi-Domain Architecture" section
- New Doc: "Why Cognitive Architecture Failed at TextWorld"
- Research Value: Honest assessment of architecture boundaries
```

---

## FAQ

### Q: Why not fix the cognitive agent instead of creating new one?

**A:** Fixing would require 40-60 hours of refactoring. Quest agent takes 4-8 hours and will perform better. The cognitive architecture is fundamentally misaligned with sequential task execution.

### Q: Doesn't this mean the architecture is limited?

**A:** Yes, and that's valuable research insight! Every architecture has boundaries. Documenting "when to use X vs Y" is a research contribution.

### Q: What about episodic memory / learning?

**A:** Quest agent can still use episodic memory to learn quest patterns over time. That's a future enhancement (2-4 additional hours).

### Q: Will this make the project look bad?

**A:** No—it demonstrates research maturity. Projects that claim "universal" solutions without limitations are less credible. Honest assessment is a strength.

### Q: Can't we just tune the parameters?

**A:** No. This is not a tuning problem. The architecture is designed for exploration (high β for info gain). TextWorld punishes exploration. This is a structural mismatch.

---

## Recommendation Summary

**Choose Option A: Minimal Quest Agent**

**Rationale:**
1. ✅ Will actually work (80%+ success vs 0% current)
2. ✅ Low effort (4-8 hours vs 40-60 hours)
3. ✅ High research value (demonstrates architecture boundaries)
4. ✅ Maintains project integrity (honest about limitations)

**Next Actions:**
1. Approve implementation plan
2. Allocate 20 hours over 3 weeks
3. Create `quest_agent.py` and validation suite
4. Document learnings in `ARCHITECTURE_DOMAIN_FIT.md`

**Expected Outcome:**
- TextWorld working (80%+ success rate)
- Research contribution: "When Cognitive Architectures Don't Fit"
- Project positioned as mature, honest research

---

## Closing Thoughts

The TextWorld integration didn't fail because of bad engineering—it failed because we tried to use a navigation system to execute a recipe. That's a design mismatch, not a skill issue.

**The valuable insight:** Cognitive architectures excel at **uncertain, exploratory** domains (graphs, mazes, navigation). They struggle with **deterministic, instructional** domains (recipes, procedures, quests).

**The research contribution:** Documenting this boundary helps future researchers choose the right tool for their problem. That's more valuable than pretending the architecture is universal.

**The path forward:** Build a simple quest agent (4-8 hours), validate it works (80%+), and document the lesson learned. This strengthens the project by demonstrating intellectual honesty and research maturity.

---

**End of Recommendations**

*"Premature optimization is the root of all evil." - Donald Knuth*

*In this case, premature architecture was the root. Let's use the simple tool that actually works.*
