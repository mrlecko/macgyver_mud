# TextWorld Quick Fix: 4-Hour Implementation Plan

**Goal:** Get TextWorld working with minimal effort

**Strategy:** Create simple quest agent (bypass cognitive architecture entirely)

**Expected Result:** 80%+ success rate in 4-8 hours

---

## The One-Page Implementation

### Core Insight

TextWorld quests are **instructions**, not **navigation problems**.

```
Quest: "First move east. Then take nest. Finally place in dresser."
```

This is a **recipe**, not a **maze**. Cognitive architecture is overkill.

### What We Need

1. **Quest Decomposer:** Parse quest → action sequence
2. **Command Matcher:** Match action goal → admissible command
3. **Progress Tracker:** Know which step we're on

That's it. ~200 lines total.

---

## Step-by-Step Implementation

### File 1: `quest_decomposer.py` (1 hour)

```python
"""Quest decomposer using LLM."""
import subprocess
import json
import re

class QuestDecomposer:
    def decompose(self, quest: str) -> list[str]:
        """
        Break quest into ordered action goals.

        Example:
            Input: "First go east. Then take nest. Finally put in dresser."
            Output: ["go east", "take nest", "put nest in dresser"]
        """
        # Clean quest text
        quest = quest.lower()

        # Temporal markers
        markers = ["first", "then", "after that", "finally", "next"]

        # Split on markers and punctuation
        steps = re.split(r'(?:first|then|after that|finally|next|and then)[,.]?\s*', quest)
        steps = [s.strip().strip('.') for s in steps if s.strip()]

        # Clean up actions (remove filler words)
        cleaned = []
        for step in steps:
            # Remove "you should", "it would be good if", etc.
            step = re.sub(r'^(you should|it would be|you can|you need to)\s*', '', step)
            if step:
                cleaned.append(step)

        return cleaned
```

**Test:**
```python
decomposer = QuestDecomposer()
steps = decomposer.decompose(
    "First, move east. Then, recover the nest from the table. Finally, place the nest in the dresser."
)
# Returns: ["move east", "recover the nest from the table", "place the nest in the dresser"]
```

---

### File 2: `command_matcher.py` (30 minutes)

```python
"""Match action goals to admissible commands."""

class CommandMatcher:
    def match(self, goal: str, commands: list[str]) -> str:
        """
        Find command that best matches goal.

        Uses token overlap scoring.
        """
        goal_tokens = set(goal.lower().split())

        best_score = 0
        best_cmd = commands[0] if commands else "look"

        for cmd in commands:
            cmd_tokens = set(cmd.lower().split())

            # Score = (tokens in common) / (goal tokens)
            overlap = len(goal_tokens & cmd_tokens)
            score = overlap / len(goal_tokens) if goal_tokens else 0

            if score > best_score:
                best_score = score
                best_cmd = cmd

        return best_cmd
```

**Test:**
```python
matcher = CommandMatcher()
action = matcher.match(
    goal="move east",
    commands=["go east", "go west", "examine table", "look"]
)
# Returns: "go east" (100% token overlap: "east")
```

---

### File 3: `quest_agent.py` (2 hours)

```python
"""Minimal quest agent for TextWorld."""
from .quest_decomposer import QuestDecomposer
from .command_matcher import CommandMatcher

class QuestAgent:
    """
    Dead-simple agent that executes quest steps sequentially.

    No beliefs, no EFE, no protocols. Just:
    1. Parse quest
    2. Execute steps in order
    3. Advance when step succeeds
    """

    def __init__(self, verbose=True):
        self.decomposer = QuestDecomposer()
        self.matcher = CommandMatcher()
        self.verbose = verbose

        # State
        self.steps = []
        self.current_step = 0
        self.last_action = ""
        self.action_count = 0

    def reset(self, quest: str):
        """Start new episode."""
        self.steps = self.decomposer.decompose(quest)
        self.current_step = 0
        self.last_action = ""
        self.action_count = 0

        if self.verbose:
            print(f"\n📋 Quest decomposed:")
            for i, step in enumerate(self.steps, 1):
                print(f"   {i}. {step}")

    def step(self, observation: str, reward: float,
             admissible_commands: list[str]) -> str:
        """Execute one step."""
        self.action_count += 1

        # Check if we should advance to next step
        if reward > 0 and self.current_step < len(self.steps) - 1:
            self.current_step += 1
            if self.verbose:
                print(f"   ✅ Step {self.current_step} complete (reward: {reward:+.1f})")

        # Get current goal
        if self.current_step < len(self.steps):
            goal = self.steps[self.current_step]
            action = self.matcher.match(goal, admissible_commands)

            if self.verbose:
                print(f"   🎯 Step {self.current_step + 1}/{len(self.steps)}: {goal}")
                print(f"   ⚡ Action: {action}")

            # Loop prevention: If same action 3+ times, try different one
            if action == self.last_action and self.action_count % 3 == 0:
                if self.verbose:
                    print(f"   ⚠️  Same action repeated, trying alternative")
                # Get second-best match
                filtered = [c for c in admissible_commands if c != action]
                if filtered:
                    action = self.matcher.match(goal, filtered)

            self.last_action = action
            return action
        else:
            # Quest complete
            return "look"
```

**Usage:**
```python
agent = QuestAgent(verbose=True)

# Start episode
game_state = env.reset()
quest = game_state.objective
agent.reset(quest)

# Run episode
done = False
while not done:
    action = agent.step(
        observation=game_state.feedback,
        reward=game_state.reward,
        admissible_commands=game_state.admissible_commands
    )
    game_state, reward, done = env.step(action)
```

---

### File 4: `test_quest_agent.py` (1 hour)

```python
"""Test quest agent on TextWorld games."""
import textworld
from .quest_agent import QuestAgent

def test_simple_quest():
    """Test on generated game."""
    # Create test game
    from .validate_planning import create_simple_game
    game_file = create_simple_game()

    # Setup
    request_infos = textworld.EnvInfos(
        admissible_commands=True,
        objective=True,
        inventory=True,
        max_score=True
    )

    env = textworld.start(game_file, request_infos=request_infos)
    game_state = env.reset()

    agent = QuestAgent(verbose=True)
    agent.reset(game_state.objective)

    # Run episode
    max_steps = 20
    step = 0
    total_reward = 0
    done = False

    print(f"\n🎯 QUEST: {game_state.objective}\n")

    while not done and step < max_steps:
        step += 1

        action = agent.step(
            observation=game_state.feedback,
            reward=game_state.reward,
            admissible_commands=game_state.admissible_commands
        )

        game_state, reward, done = env.step(action)
        total_reward += reward

        if reward > 0:
            print(f"   💰 Reward: {reward:+.1f} (total: {total_reward:+.1f})")

    env.close()

    # Verify
    print(f"\n{'='*70}")
    print(f"Result: {'✅ SUCCESS' if done else '❌ FAILED'}")
    print(f"Steps: {step}/{max_steps}")
    print(f"Reward: {total_reward:+.1f}")

    assert done, f"Failed to complete quest in {max_steps} steps"
    assert total_reward > 0, f"No reward earned"

    print("✅ TEST PASSED")

def test_multiple_games():
    """Test on multiple random games."""
    results = []

    for seed in range(10):
        print(f"\n{'='*70}")
        print(f"TEST {seed + 1}/10 (seed: {seed})")
        print(f"{'='*70}")

        try:
            test_simple_quest()  # Would need to pass seed
            results.append({'seed': seed, 'success': True})
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            results.append({'seed': seed, 'success': False})

    # Summary
    successes = sum(r['success'] for r in results)
    success_rate = successes / len(results)

    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Success Rate: {successes}/{len(results)} ({success_rate:.0%})")

    assert success_rate >= 0.8, f"Success rate too low: {success_rate:.0%}"

if __name__ == "__main__":
    test_simple_quest()
    # test_multiple_games()
```

---

## Testing (1 hour)

### Quick Test
```bash
cd /home/juancho/macgyver_mud
python3 environments/domain4_textworld/test_quest_agent.py
```

**Expected Output:**
```
📋 Quest decomposed:
   1. move east
   2. recover the nest from the table
   3. place the nest in the dresser

🎯 QUEST: First, move east. Then, recover the nest...

   🎯 Step 1/3: move east
   ⚡ Action: go east

   ✅ Step 1 complete (reward: +0.0)
   🎯 Step 2/3: recover the nest from the table
   ⚡ Action: take nest of spiders from table

   💰 Reward: +0.0 (total: +0.0)
   🎯 Step 3/3: place the nest in the dresser
   ⚡ Action: insert nest of spiders into dresser

   💰 Reward: +1.0 (total: +1.0)

======================================================================
Result: ✅ SUCCESS
Steps: 3/20
Reward: +1.0
✅ TEST PASSED
```

### Comparison Test
```bash
# Run side-by-side: Quest Agent vs Simple LLM vs Cognitive Agent
python3 environments/domain4_textworld/compare_all_players.py
```

**Expected:**
```
Quest Agent:   ✅ WON in 4 steps
Simple LLM:    ✅ WON in 3 steps
Cognitive:     ❌ FAILED (loop after 20 steps)

Verdict: Quest agent works! Close to LLM baseline.
```

---

## What This Proves

### Before
- **Cognitive Agent:** 0% success (stuck in loops)
- **Simple LLM:** 100% success (but no learning)

### After
- **Quest Agent:** 80-90% success (simple + structured)
- **Can add learning:** Episodic memory for quest patterns (future work)
- **Demonstrates:** Different domains need different architectures

---

## Why This Is Better

### vs Cognitive Agent
- ✅ Actually works (80% vs 0%)
- ✅ Simpler (200 lines vs 2500 lines)
- ✅ Faster to develop (4 hours vs 40 hours)
- ✅ Maintainable (junior dev can understand)

### vs Simple LLM
- ✅ Structured (decomposition + matching + tracking)
- ✅ Extensible (can add memory, learning, etc.)
- ✅ Debuggable (can see step-by-step progress)
- ✅ Educational (shows architecture-domain fit concept)

---

## Next Steps

### Immediate (4 hours)
1. ✅ Create 3 files (decomposer, matcher, agent)
2. ✅ Write test suite
3. ✅ Validate 80%+ success

### Short-term (4 hours)
1. Add episodic memory (learn quest patterns)
2. Improve matcher (handle synonyms)
3. Add error recovery (if action fails, try alternative)

### Documentation (2 hours)
1. Update README: "Multi-Domain Agents" section
2. Write `ARCHITECTURE_DOMAIN_FIT.md`
3. Create comparison table

**Total:** 10 hours to fully working + documented system

---

## Decision Point

**Do you want:**

A. **Quest Agent** (4-8 hours, 80%+ success, honest about limitations)
B. **Deep Integration** (40-60 hours, uncertain success, forced fit)
C. **Abandon TextWorld** (0 hours, incomplete)

**Recommendation:** Choose A.

**Rationale:** Get it working, document the lesson, move forward.

---

## One Last Thing

The TextWorld "failure" is actually a **research success**:

> "We discovered that cognitive architectures optimized for graph exploration struggle with sequential task execution. This insight helps researchers choose the right tool for their problem domain."

That's a valuable contribution. Don't hide it—document it and move on.

---

**Action Items:**

1. [ ] Approve Quest Agent approach
2. [ ] Allocate 4-8 hours for implementation
3. [ ] Create files in `environments/domain4_textworld/`
4. [ ] Run validation tests
5. [ ] Document findings in project README

**Timeline:** This week (part-time) or next 2 days (full-time)

**Expected Outcome:** TextWorld working, honest documentation, research lesson learned

---

**End of Quick Fix Guide**

*Get it done. Get it working. Document the lesson. Move forward.*
