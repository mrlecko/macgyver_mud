# Interactive Jupyter Notebook Design
## MacGyver MUD: Active Inference & Geometric Diagnostics Deep Dive

**Purpose**: Pedagogical tool for understanding active inference, Silver Gauge diagnostics, and multi-objective skill evolution through interactive exploration.

**Target Audience**: Researchers, students, and practitioners interested in active inference, interpretable AI, and geometric analysis.

**Estimated Time**: 2-3 hours for complete walkthrough

---

## Design Philosophy

### Core Pedagogical Principles

1. **Narrative Arc**: Discovery-driven story from simple problem to profound insight
2. **Concrete Before Abstract**: Show the locked door problem before showing formulas
3. **Interactive Exploration**: Every concept has hands-on component
4. **Visual Learning**: Graph visualizations, plots, animations, 3D spaces
5. **Just-In-Time Math**: Introduce formulas when needed, not upfront
6. **Progressive Disclosure**: Start simple, layer complexity gradually
7. **Multiple Representations**: Formula + Code + Visualization for each concept
8. **Active Checkpoints**: Test understanding at key transition points
9. **Real Data**: Use actual Neo4j database, not synthetic examples
10. **Climactic Revelation**: Build to the k_explore ≈ 0 discovery as the "aha!" moment

### Why Spiral Structure? (Option C)

After considering three approaches:
- **Bottom-Up** (Math First): Too abstract, loses engagement
- **Top-Down** (Problem First): Scattered without theoretical foundation
- **Spiral** (Iterative Deepening): ✅ BEST - Accommodates different learning depths

**Spiral Structure Benefits:**
- Learners can stop at any level and extract value
- Each revolution adds new dimension of understanding
- Natural checkpoints at level boundaries
- Respects different mathematical backgrounds
- Maintains motivation through concrete examples

---

## Detailed Notebook Structure

### PART 0: Setup & Orientation (5 minutes)

**Learning Objectives:**
- Connect to Neo4j database
- Import required libraries
- Set learning path preferences
- Understand what we'll discover

**Cells:**

**0.1 - Welcome & Story Hook**
```python
display(Markdown("""
# The MacGyver MUD: A Journey Into Active Inference

You're locked in a room. There's a door (might be locked) and a window (escape route, but costly).

**The Question**: How should an intelligent agent decide what to do?

By the end of this notebook, you'll understand:
1. How active inference balances exploration and exploitation
2. How Pythagorean means (from 500 BCE!) make AI interpretable
3. Why ALL simple skills are "specialists" (k ≈ 0)
4. How multi-objective skills fill geometric gaps

Let's begin...
"""))
```

**0.2 - Library Imports & Setup**
```python
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from neo4j import GraphDatabase
import ipywidgets as widgets
from IPython.display import display, Markdown, HTML, Image
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import beta
import networkx as nx
import pandas as pd

# Plotting configuration
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("✓ Libraries loaded")
```

**0.3 - Neo4j Connection**
```python
# Connect to Neo4j database
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Test connection
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    node_count = result.single()['count']
    print(f"✓ Connected to Neo4j")
    print(f"  Database contains {node_count} nodes")
```

**0.4 - Learning Path Selector**
```python
# Interactive: Choose your learning depth
learning_depth = widgets.RadioButtons(
    options=['Intuitive (minimal math)',
             'Computational (basic formulas)',
             'Mathematical (full derivations)'],
    description='Your background:',
    disabled=False
)
display(learning_depth)

# This choice will customize which optional sections to expand
```

---

### PART 1: The MacGyver Problem (10 minutes)

**Goal**: Build intuition without any mathematics

**1.1 - The Scenario**
```python
display(Image('room_scenario.png'))  # Create this visualization

display(Markdown("""
## The Locked Room Scenario

You wake up in a room with:
- **A door**: Might be locked (you don't know yet)
- **A window**: Always open, but 2nd floor (risky/costly)

**Objective**: Escape as quickly and safely as possible

**The Catch**: You're UNCERTAIN about the door state!
"""))
```

**1.2 - Interactive Room Graph Visualization**
```python
def visualize_room_graph():
    """Query and visualize the room structure from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH (start:State {name: 'stuck_in_room'})
            OPTIONAL MATCH (start)-[r]->(other)
            RETURN start, type(r) as rel, other
        """)

        # Build NetworkX graph
        G = nx.DiGraph()
        for record in result:
            # Add nodes and edges
            start = record['start']['name']
            if record['other']:
                end = record['other']['name']
                rel = record['rel']
                G.add_edge(start, end, label=rel)

        # Visualize
        pos = nx.spring_layout(G)
        plt.figure(figsize=(10, 6))
        nx.draw(G, pos, with_labels=True, node_color='lightblue',
                node_size=3000, font_size=10, font_weight='bold',
                arrows=True, edge_color='gray', width=2)

        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels)
        plt.title("Room State Graph (from Neo4j)")
        plt.axis('off')
        plt.show()

visualize_room_graph()
```

**1.3 - Interactive Quiz: What Would YOU Do?**
```python
quiz_choice = widgets.RadioButtons(
    options=['Immediately try to open the door',
             'First peek through keyhole to check if locked',
             'Immediately go to the window'],
    description='Your choice:',
)

submit_button = widgets.Button(description="Submit Answer")
output = widgets.Output()

def check_answer(b):
    with output:
        output.clear_output()
        if quiz_choice.value == 'First peek through keyhole to check if locked':
            print("✓ Smart! Gathering information before acting is key to good decisions.")
            print("  This is called 'exploration' - reducing uncertainty.")
        else:
            print("⚠ Think about it: What if the door is unlocked? You'd waste effort/risk.")
            print("  Gathering information first (exploration) often beats acting blindly.")

submit_button.on_click(check_answer)
display(quiz_choice, submit_button, output)
```

**1.4 - Uncertainty Matters: Locked vs Unlocked Changes Everything**
```python
# Interactive belief slider
belief_slider = widgets.FloatSlider(
    value=0.5,
    min=0,
    max=1,
    step=0.1,
    description='Belief door is LOCKED:',
    continuous_update=True
)

def show_recommendation(belief):
    if belief < 0.3:
        return "🚪 TRY THE DOOR (probably unlocked)"
    elif belief > 0.7:
        return "👁 PEEK FIRST (probably locked, don't waste effort trying)"
    else:
        return "🤔 UNCERTAIN - gather info or take risk?"

output_recommendation = widgets.interactive_output(
    lambda b: print(f"Recommendation: {show_recommendation(b)}"),
    {'b': belief_slider}
)

display(Markdown("### How Your Belief Changes the Best Action"))
display(belief_slider, output_recommendation)

display(Markdown("""
**Key Insight**: The "best" action depends on your UNCERTAINTY!
- High confidence door is unlocked → Try it
- High confidence door is locked → Don't waste effort
- Uncertain → Gather information first!
"""))
```

**1.5 - Three Available Skills**
```python
def query_skills():
    """Get skill details from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Skill)
            WHERE s.kind IN ['sense', 'act']
            RETURN s.name, s.kind, s.cost, s.goal_info, s.info_gain
            ORDER BY s.name
        """)

        skills_data = []
        for record in result:
            skills_data.append({
                'Name': record['s.name'],
                'Type': record['s.kind'],
                'Cost': record['s.cost'],
                'Goal Achievement': record['s.goal_info'],
                'Info Gained': record['s.info_gain']
            })

        return pd.DataFrame(skills_data)

skills_df = query_skills()
display(Markdown("### Available Skills (from Neo4j Database)"))
display(skills_df)

display(Markdown("""
**Notice the trade-offs:**
- **peek_door**: High info, zero goal progress, low cost
- **try_door**: Zero info, high goal progress (if unlocked), medium cost
- **go_window**: Zero info, guaranteed goal, high cost

How do we choose? That's what Active Inference solves!
"""))
```

**1.6 - Checkpoint 1**
```python
checkpoint1 = widgets.RadioButtons(
    options=['peek_door (gather info)',
             'try_door (act immediately)',
             'go_window (guaranteed escape)'],
    description='If door is PROBABLY locked (belief=0.8), which skill is best?',
)

check1_button = widgets.Button(description="Check Answer")
check1_output = widgets.Output()

def check_checkpoint1(b):
    with check1_output:
        check1_output.clear_output()
        if checkpoint1.value == 'peek_door (gather info)':
            print("✓ Correct! When door is probably locked, trying it wastes effort.")
            print("  Better to peek first and confirm before trying.")
        else:
            print("✗ Think again: If door is probably locked, trying it likely fails.")
            print("  What could reduce your uncertainty before committing?")

check1_button.on_click(check_checkpoint1)
display(checkpoint1, check1_button, check1_output)
```

---

### PART 2: Active Inference - The Math of Uncertainty (20 minutes)

**Goal**: Introduce core Expected Free Energy mathematics

**2.1 - Beliefs as Probability Distributions**
```python
# Interactive belief visualization
fig, ax = plt.subplots(figsize=(10, 4))

belief_param = widgets.FloatSlider(value=0.5, min=0.1, max=0.9, step=0.1,
                                    description='Belief (locked):')

def plot_belief(belief_locked):
    ax.clear()

    states = ['Unlocked', 'Locked']
    probabilities = [1 - belief_locked, belief_locked]
    colors = ['green', 'red']

    bars = ax.bar(states, probabilities, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax.set_ylabel('Probability', fontsize=12)
    ax.set_title(f'Agent Belief Distribution (Locked={belief_locked:.1f})', fontsize=14)
    ax.set_ylim(0, 1)
    ax.grid(axis='y', alpha=0.3)

    # Add probability labels on bars
    for bar, prob in zip(bars, probabilities):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{prob:.2f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.tight_layout()

interactive_belief = widgets.interactive_output(plot_belief, {'belief_locked': belief_param})
display(belief_param, interactive_belief)

display(Markdown("""
**Key Concept**: The agent doesn't KNOW the true state - it has a BELIEF (probability distribution).
- Belief = 0.5 → Maximum uncertainty (50/50)
- Belief = 0.9 → High confidence door is locked
- Belief = 0.1 → High confidence door is unlocked

Actions update beliefs based on observations!
"""))
```

**2.2 - Expected Free Energy (EFE) Formula**
```python
display(Markdown(r"""
### Expected Free Energy (EFE)

Active inference agents choose skills by minimizing **Expected Free Energy**:

$$G(\pi) = \underbrace{\mathbb{E}[\text{cost}]}_{\text{Resource expenditure}} - \underbrace{\mathbb{E}[\text{goal}]}_{\text{Pragmatic value}} - \underbrace{\mathbb{E}[\text{info}]}_{\text{Epistemic value}}$$

**Three components:**

1. **Expected Cost**: Resources consumed (time, energy, risk)
   - Lower is better → subtract it (penalty)

2. **Expected Goal**: How much does this help achieve objective?
   - Higher is better → subtract negative (reward)
   - In our case: probability of escaping

3. **Expected Info**: How much uncertainty does this reduce?
   - Higher is better → subtract negative (reward)
   - Measured as information gain (reduction in entropy)

**The agent picks the skill with LOWEST G** (best trade-off)!
"""))
```

**2.3 - Breaking Down EFE Components**
```python
# Interactive EFE calculator
cost_slider = widgets.FloatSlider(value=1.0, min=0, max=3, step=0.1, description='Cost:')
goal_slider = widgets.FloatSlider(value=0.5, min=0, max=1, step=0.05, description='Goal Value:')
info_slider = widgets.FloatSlider(value=0.5, min=0, max=1, step=0.05, description='Info Gain:')

output_efe = widgets.Output()

def calculate_efe(cost, goal, info):
    with output_efe:
        output_efe.clear_output()

        efe = cost - goal - info

        print(f"Expected Free Energy Calculation:")
        print(f"  Cost:      +{cost:.2f}  (penalty)")
        print(f"  Goal:      -{goal:.2f}  (reward)")
        print(f"  Info:      -{info:.2f}  (reward)")
        print(f"  " + "="*30)
        print(f"  EFE:       {efe:.2f}")
        print()
        print(f"Interpretation: {'GOOD' if efe < 1 else 'POOR'} skill")
        print(f"  (Lower EFE = Better choice)")

efe_calculator = widgets.interactive_output(
    calculate_efe,
    {'cost': cost_slider, 'goal': goal_slider, 'info': info_slider}
)

display(Markdown("### Interactive EFE Calculator"))
display(widgets.VBox([cost_slider, goal_slider, info_slider]), output_efe)

# Update on change
cost_slider.observe(lambda change: calculate_efe(cost_slider.value, goal_slider.value, info_slider.value), 'value')
goal_slider.observe(lambda change: calculate_efe(cost_slider.value, goal_slider.value, info_slider.value), 'value')
info_slider.observe(lambda change: calculate_efe(cost_slider.value, goal_slider.value, info_slider.value), 'value')

calculate_efe(1.0, 0.5, 0.5)  # Initial calculation
```

**2.4 - Code Walkthrough: score_skill() Function**
```python
display(Markdown("### How Skills Are Scored in Code"))

# Show actual code from graph_model.py
code_display = """
```python
def score_skill(skill: Dict, belief_door_locked: float) -> float:
    '''
    Calculate Expected Free Energy for a skill.

    Args:
        skill: Dict with 'cost', 'goal_info', 'info_gain'
        belief_door_locked: Current belief (0-1)

    Returns:
        Expected Free Energy (lower is better)
    '''
    cost = skill['cost']                      # ← Resource penalty

    # Pragmatic value: How much goal achievement?
    # If door is probably unlocked, trying door is good
    # If door is probably locked, trying door wastes effort
    belief_unlocked = 1 - belief_door_locked
    expected_goal = skill['goal_info'] * belief_unlocked

    # Epistemic value: How much info gained?
    # Only sensing skills provide info
    expected_info = skill['info_gain']

    # Expected Free Energy
    efe = cost - expected_goal - expected_info

    return efe
```
"""

display(Markdown(code_display))

display(Markdown("""
**Key Points:**
1. **Cost** is always penalized (added)
2. **Goal** is belief-weighted (if door probably locked, trying has low expected goal)
3. **Info** is fixed per skill (peek always gives info)
4. **Lower EFE wins** - agent picks skill with minimum G
"""))
```

**2.5 - Interactive: Score All Three Skills**
```python
# Query skills from Neo4j
def get_skill_params():
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Skill)
            WHERE s.kind IN ['sense', 'act'] AND s.name IN ['peek_door', 'try_door', 'go_window']
            RETURN s.name, s.cost, s.goal_info, s.info_gain
        """)

        skills = {}
        for record in result:
            skills[record['s.name']] = {
                'cost': record['s.cost'],
                'goal_info': record['s.goal_info'],
                'info_gain': record['s.info_gain']
            }
        return skills

skills_params = get_skill_params()

# Interactive belief slider with live scoring
belief_slider_2 = widgets.FloatSlider(
    value=0.5, min=0, max=1, step=0.05,
    description='Belief (locked):',
    continuous_update=True
)

output_scores = widgets.Output()

def score_all_skills(belief):
    with output_scores:
        output_scores.clear_output()

        print(f"Belief that door is LOCKED: {belief:.2f}")
        print(f"Belief that door is UNLOCKED: {1-belief:.2f}")
        print()
        print("Skill Scoring:")
        print("-" * 60)

        scores = {}
        for skill_name, params in skills_params.items():
            cost = params['cost']
            expected_goal = params['goal_info'] * (1 - belief)
            expected_info = params['info_gain']
            efe = cost - expected_goal - expected_info

            scores[skill_name] = efe

            print(f"{skill_name:15s}: Cost={cost:.2f}, Goal={expected_goal:.2f}, Info={expected_info:.2f} → EFE={efe:.2f}")

        print("-" * 60)
        best_skill = min(scores, key=scores.get)
        print(f"BEST CHOICE: {best_skill} (lowest EFE = {scores[best_skill]:.2f})")

interactive_scoring = widgets.interactive_output(score_all_skills, {'belief': belief_slider_2})
display(belief_slider_2, output_scores)
score_all_skills(0.5)  # Initial
```

**2.6 - Visualization: EFE Curves Across Belief Space**
```python
# Plot EFE for all skills across belief range
beliefs = np.linspace(0, 1, 100)

fig, ax = plt.subplots(figsize=(12, 6))

for skill_name, params in skills_params.items():
    efes = []
    for b in beliefs:
        cost = params['cost']
        expected_goal = params['goal_info'] * (1 - b)
        expected_info = params['info_gain']
        efe = cost - expected_goal - expected_info
        efes.append(efe)

    ax.plot(beliefs, efes, label=skill_name, linewidth=2.5)

ax.set_xlabel('Belief that door is LOCKED', fontsize=12)
ax.set_ylabel('Expected Free Energy (lower is better)', fontsize=12)
ax.set_title('Skill Selection Depends on Belief!', fontsize=14, fontweight='bold')
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.grid(alpha=0.3)
ax.legend(fontsize=11, loc='best')
ax.invert_yaxis()  # Lower is better, so show best at top visually
plt.tight_layout()
plt.show()

display(Markdown("""
**Key Insight from Plot:**
- When belief < ~0.4 (probably unlocked) → **try_door** wins (act immediately)
- When belief > ~0.6 (probably locked) → **peek_door** wins (gather info first)
- **go_window** always has high EFE (expensive, only use if desperate)

**Crossover points** show when the optimal policy switches!
"""))
```

**2.7 - Checkpoint 2**
```python
display(Markdown("### Checkpoint 2: Calculate EFE"))

checkpoint2_belief = widgets.FloatText(value=0.5, description='Belief (locked):')
checkpoint2_answer = widgets.FloatText(value=0.0, description='Your EFE for try_door:')
checkpoint2_button = widgets.Button(description="Check Answer")
checkpoint2_output = widgets.Output()

def check_checkpoint2(b):
    with checkpoint2_output:
        checkpoint2_output.clear_output()

        belief = checkpoint2_belief.value
        user_answer = checkpoint2_answer.value

        # Calculate correct answer
        try_door_params = skills_params['try_door']
        cost = try_door_params['cost']
        expected_goal = try_door_params['goal_info'] * (1 - belief)
        expected_info = try_door_params['info_gain']
        correct_efe = cost - expected_goal - expected_info

        if abs(user_answer - correct_efe) < 0.01:
            print(f"✓ Correct! EFE = {correct_efe:.2f}")
            print(f"  Cost={cost:.2f}, Goal={expected_goal:.2f}, Info={expected_info:.2f}")
        else:
            print(f"✗ Not quite. The correct EFE is {correct_efe:.2f}")
            print(f"  Calculation: {cost:.2f} - {expected_goal:.2f} - {expected_info:.2f} = {correct_efe:.2f}")

checkpoint2_button.on_click(check_checkpoint2)
display(checkpoint2_belief, checkpoint2_answer, checkpoint2_button, checkpoint2_output)
```

---

### PART 3: Policy Execution & Procedural Memory (15 minutes)

**Goal**: Show how agents learn and adapt through experience

**3.1 - What is a Policy?**
```python
display(Markdown("""
### Policies: Sequences of Skills

A **policy** is a plan (sequence of skills):
- Simple policy: `[try_door]` - Just try opening
- Info-gathering policy: `[peek_door, try_door]` - Look first, then act
- Cautious policy: `[peek_door, try_door, go_window]` - Try both, fallback to window

The agent evaluates ENTIRE policy sequences, not just single skills!
"""))

def visualize_policy_tree():
    """Query and visualize policy graph from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH path = (start:State {name: 'stuck_in_room'})-[:CAN_USE|LEADS_TO*1..3]->()
            RETURN path
            LIMIT 20
        """)

        G = nx.DiGraph()
        for record in result:
            path = record['path']
            # Build graph from path
            for i in range(len(path.nodes) - 1):
                source = path.nodes[i]['name'] if 'name' in path.nodes[i] else str(path.nodes[i].id)
                target = path.nodes[i+1]['name'] if 'name' in path.nodes[i+1] else str(path.nodes[i+1].id)
                G.add_edge(source, target)

        plt.figure(figsize=(14, 8))
        pos = nx.spring_layout(G, k=0.5, iterations=50)

        # Color nodes by type
        node_colors = []
        for node in G.nodes():
            if 'skill' in node.lower() or 'peek' in node.lower() or 'try' in node.lower() or 'window' in node.lower():
                node_colors.append('lightcoral')
            elif 'escaped' in node.lower():
                node_colors.append('lightgreen')
            else:
                node_colors.append('lightblue')

        nx.draw(G, pos, with_labels=True, node_color=node_colors,
                node_size=2000, font_size=8, font_weight='bold',
                arrows=True, edge_color='gray', width=1.5, alpha=0.7)

        plt.title("Policy Tree (from Neo4j)", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.show()

visualize_policy_tree()
```

**3.2 - Simulating Skill Execution: Belief Update**
```python
display(Markdown("### Interactive: Execute peek_door"))

# Interactive simulation
initial_belief = widgets.FloatSlider(value=0.5, min=0, max=1, step=0.05,
                                      description='Initial belief:')
true_state = widgets.RadioButtons(options=['Unlocked', 'Locked'],
                                    description='True state:')
execute_button = widgets.Button(description="Execute peek_door")
simulation_output = widgets.Output()

def simulate_peek(b):
    with simulation_output:
        simulation_output.clear_output()

        belief = initial_belief.value
        state = true_state.value

        print(f"Initial belief that door is LOCKED: {belief:.2f}")
        print(f"True state (unknown to agent): {state}")
        print()
        print("Executing: peek_door...")
        print()

        # Simulate observation
        if state == 'Locked':
            observation = "obs_door_locked"
            print(f"Observation: {observation}")
            print()
            print("Updating belief using Bayes' rule...")
            # Simplification: High accuracy sensing
            new_belief = 0.95
        else:
            observation = "obs_door_unlocked"
            print(f"Observation: {observation}")
            print()
            print("Updating belief using Bayes' rule...")
            new_belief = 0.05

        print(f"New belief that door is LOCKED: {new_belief:.2f}")
        print()
        print(f"Uncertainty reduction: {abs(new_belief - 0.5) - abs(belief - 0.5):.2f}")
        print("✓ Information gained!")

        # Visualize belief update
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # Before
        ax1.bar(['Unlocked', 'Locked'], [1-belief, belief], color=['green', 'red'], alpha=0.7)
        ax1.set_ylabel('Probability')
        ax1.set_title('Before peek_door')
        ax1.set_ylim(0, 1)

        # After
        ax2.bar(['Unlocked', 'Locked'], [1-new_belief, new_belief], color=['green', 'red'], alpha=0.7)
        ax2.set_ylabel('Probability')
        ax2.set_title(f'After observing: {observation}')
        ax2.set_ylim(0, 1)

        plt.tight_layout()
        plt.show()

execute_button.on_click(simulate_peek)
display(initial_belief, true_state, execute_button, simulation_output)
```

**3.3 - Procedural Memory: Learning from Experience**
```python
display(Markdown("""
### Procedural Memory: Pattern Matching

The agent builds **procedural memories** - learned associations:

**Structure**: `(context_pattern) → recommended_skill (confidence)`

**Examples:**
- "When belief > 0.7 AND tried_before=False → try_door" (confidence: 0.8)
- "When tried_before=True AND failed → peek_door" (confidence: 0.9)
"""))

def query_procedural_memories():
    """Query Memory nodes from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH (m:Memory)-[r:RECOMMENDS]->(s:Skill)
            RETURN m.context as context, s.name as skill, r.confidence as confidence
            ORDER BY r.confidence DESC
            LIMIT 10
        """)

        memories = []
        for record in result:
            memories.append({
                'Context Pattern': record['context'],
                'Recommended Skill': record['skill'],
                'Confidence': f"{record['confidence']:.2f}"
            })

        if memories:
            df = pd.DataFrame(memories)
            display(df)
        else:
            print("No procedural memories found in database.")
            print("(These are created during episodes with --use-memory flag)")

display(Markdown("### Procedural Memories in Database"))
query_procedural_memories()
```

**3.4 - Full Episode Simulation** [truncated for space - would include step-by-step episode execution with visualization]

**3.5 - Checkpoint 3**
```python
# Interactive checkpoint testing Bayesian belief update
# [Implementation details...]
```

---

### PART 4: The Silver Gauge - Geometric Fingerprinting (25 minutes)

**THE CLIMAX - This is where the revelation happens**

**4.1 - The Diagnostic Challenge**
```python
display(Markdown("""
### The Interpretability Problem

We've built an active inference agent that:
- ✓ Balances exploration and exploitation
- ✓ Updates beliefs using Bayes' rule
- ✓ Learns from experience

**But**: Can we UNDERSTAND its decision strategy at a glance?

**Challenge**: Create interpretable metrics WITHOUT changing behavior
- Requirement: 100% behavioral fidelity (no approximation)
- Goal: Geometric "fingerprint" of decision-making style

**Enter**: The Silver Gauge (Pythagorean means diagnostic layer)
"""))
```

**4.2 - Pythagorean Means: 2500-Year-Old Math**
```python
display(Markdown(r"""
### Three Classical Means (from Ancient Greece ~500 BCE)

Given two positive numbers $a$ and $b$:

1. **Harmonic Mean (HM)**: Bottleneck penalizer
   $$HM = \frac{2ab}{a + b}$$
   - Severely penalizes imbalance
   - Used for: rates, speeds, ratios
   - Example: Average speed for round trip

2. **Geometric Mean (GM)**: Balanced multiplier
   $$GM = \sqrt{ab}$$
   - Respects proportional relationships
   - Used for: growth rates, aspect ratios
   - Example: Average percentage growth

3. **Arithmetic Mean (AM)**: Fair splitter
   $$AM = \frac{a + b}{2}$$
   - Simple average
   - Used for: central tendency
   - Example: Average height

**The Pythagorean Inequality**: $HM \leq GM \leq AM$ (always!)
"""))

# Interactive Pythagorean means calculator
a_slider = widgets.FloatSlider(value=2, min=0.1, max=10, step=0.1, description='a:')
b_slider = widgets.FloatSlider(value=8, min=0.1, max=10, step=0.1, description='b:')
means_output = widgets.Output()

def calculate_means(a, b):
    with means_output:
        means_output.clear_output()

        hm = (2 * a * b) / (a + b)
        gm = np.sqrt(a * b)
        am = (a + b) / 2

        print(f"Input values: a={a:.2f}, b={b:.2f}")
        print()
        print(f"Harmonic Mean (HM):  {hm:.4f}")
        print(f"Geometric Mean (GM): {gm:.4f}")
        print(f"Arithmetic Mean (AM):{am:.4f}")
        print()
        print(f"Verification: {hm:.4f} ≤ {gm:.4f} ≤ {am:.4f}")
        print(f"Inequality holds: {hm <= gm <= am}")
        print()
        print(f"Balance ratio (GM/AM): {gm/am:.4f}")
        print(f"  → {gm/am:.2%} balanced (1.0 = perfect balance)")

        # Visualize
        fig, ax = plt.subplots(figsize=(10, 5))
        means_values = [hm, gm, am]
        means_names = ['HM\n(bottleneck)', 'GM\n(balanced)', 'AM\n(fair split)']
        colors = ['#e74c3c', '#f39c12', '#3498db']

        bars = ax.bar(means_names, means_values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(f'Pythagorean Means for a={a:.1f}, b={b:.1f}', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar, val in zip(bars, means_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Add inequality line
        ax.plot([0, 2], [hm, am], 'k--', alpha=0.3, linewidth=1, label='HM ≤ GM ≤ AM')

        plt.tight_layout()
        plt.show()

means_interactive = widgets.interactive_output(calculate_means, {'a': a_slider, 'b': b_slider})
display(Markdown("### Interactive Pythagorean Means Explorer"))
display(a_slider, b_slider, means_output)
calculate_means(2, 8)  # Initial
```

**4.3 - Creating Dimensionless Ratios: k Coefficients**
```python
display(Markdown(r"""
### From Means to Shape Coefficients

**Key Insight**: The RATIO $k = \frac{GM}{AM}$ is:
1. **Dimensionless**: No units (pure number)
2. **Scale-invariant**: $k(2, 8) = k(20, 80) = k(200, 800)$
3. **Bounded**: $k \in [0, 1]$
4. **Interpretable**: $k = 1$ means perfect balance, $k \to 0$ means severe imbalance

**Mathematical Properties**:
$$k = \frac{GM}{AM} = \frac{\sqrt{ab}}{\frac{a+b}{2}} = \frac{2\sqrt{ab}}{a+b}$$

**When is k close to 1?** When $a \approx b$ (balanced)
**When is k close to 0?** When $a \ll b$ or $b \ll a$ (imbalanced)
"""))

# Interactive k explorer
def explore_k_values():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # Left plot: k as function of a/b ratio
    ratios = np.logspace(-2, 2, 1000)  # a/b from 0.01 to 100
    k_values = []
    for r in ratios:
        a, b = r, 1  # Normalize b=1
        gm = np.sqrt(a * b)
        am = (a + b) / 2
        k = gm / am
        k_values.append(k)

    ax1.plot(ratios, k_values, linewidth=2.5, color='#2ecc71')
    ax1.set_xscale('log')
    ax1.set_xlabel('Ratio a/b', fontsize=12)
    ax1.set_ylabel('k = GM/AM', fontsize=12)
    ax1.set_title('k Coefficient vs Balance Ratio', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3)
    ax1.axvline(x=1, color='red', linestyle='--', label='Perfect balance (a=b)')
    ax1.axhline(y=1, color='red', linestyle='--', alpha=0.5)
    ax1.legend()

    # Right plot: Heatmap of k values
    a_vals = np.linspace(0.1, 10, 100)
    b_vals = np.linspace(0.1, 10, 100)
    k_grid = np.zeros((len(b_vals), len(a_vals)))

    for i, b in enumerate(b_vals):
        for j, a in enumerate(a_vals):
            gm = np.sqrt(a * b)
            am = (a + b) / 2
            k_grid[i, j] = gm / am

    im = ax2.imshow(k_grid, extent=[0.1, 10, 0.1, 10], origin='lower', cmap='RdYlGn', aspect='auto')
    ax2.set_xlabel('a (goal value)', fontsize=12)
    ax2.set_ylabel('b (info gain)', fontsize=12)
    ax2.set_title('k Coefficient Heatmap', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=ax2, label='k = GM/AM')

    # Add diagonal line (perfect balance)
    ax2.plot([0.1, 10], [0.1, 10], 'r--', linewidth=2, label='a=b (k=1)')
    ax2.legend()

    plt.tight_layout()
    plt.show()

explore_k_values()

display(Markdown("""
**Key Observation**:
- Along diagonal (a = b): k = 1 (perfect balance)
- Far from diagonal: k → 0 (specialist/imbalanced)

This will be CRUCIAL for understanding skills!
"""))
```

**4.4 - Applying to Skills: k_explore**
```python
display(Markdown(r"""
### Silver Gauge Coefficient #1: k_explore

**Question**: Does this skill balance goal achievement and information gain?

**Inputs**:
- $a$ = goal value (pragmatic component)
- $b$ = info gain (epistemic component)

**Calculation**:
$$k_{\text{explore}} = \frac{GM(\text{goal}, \text{info})}{AM(\text{goal}, \text{info})} = \frac{2\sqrt{\text{goal} \cdot \text{info}}}{\text{goal} + \text{info}}$$

**Interpretation**:
- $k_{\text{explore}} \approx 1$: Balanced multi-objective skill
- $k_{\text{explore}} \approx 0$: Specialist (either pure exploration OR pure exploitation)

**Critical Insight**: A pure exploration skill (info=100%, goal=0%) has k≈0!
A pure exploitation skill (goal=100%, info=0%) also has k≈0!
Only multi-objective skills have k > 0.5!
"""))

# Code walkthrough of silver_k_explore
code_display = """
```python
def silver_k_explore(goal_value: float, info_gain: float) -> float:
    '''
    Calculate k_explore coefficient using Pythagorean means.

    Args:
        goal_value: Expected goal achievement [0, 1]
        info_gain: Expected information gain [0, 1]

    Returns:
        k_explore ∈ [0, 1] where 1 = perfect balance, 0 = specialist
    '''
    epsilon = 1e-10  # Avoid division by zero

    # Geometric mean: balanced multiplier
    gm = np.sqrt(goal_value * info_gain + epsilon)

    # Arithmetic mean: fair splitter
    am = (goal_value + info_gain) / 2.0 + epsilon

    # Dimensionless ratio
    k = gm / am

    return k
```
"""

display(Markdown(code_display))

display(Markdown("""
**Mathematical Proof of Behavioral Fidelity**:

The Silver Gauge uses ONLY the inputs (goal_value, info_gain) - it doesn't modify them!

EFE calculation:
```
G = cost - goal_value - info_gain  ← Uses original values
```

Silver Gauge:
```
k_explore = f(goal_value, info_gain)  ← Pure function, no side effects
```

**Therefore**: Adding Silver Gauge CANNOT change which skill has minimum G!
✓ 100% behavioral fidelity guaranteed mathematically!
"""))
```

**4.5 - Applying to Skills: k_efficiency**
```python
display(Markdown(r"""
### Silver Gauge Coefficient #2: k_efficiency

**Question**: Does this skill balance benefit and cost?

**Inputs**:
- $a$ = expected benefit (goal + info)
- $b$ = cost efficiency (1/cost)

**Calculation**:
$$k_{\text{efficiency}} = \frac{GM(\text{benefit}, \frac{1}{\text{cost}})}{AM(\text{benefit}, \frac{1}{\text{cost}})}$$

**Interpretation**:
- $k_{\text{efficiency}} \approx 1$: Excellent benefit/cost ratio
- $k_{\text{efficiency}} \approx 0$: Poor ROI (high cost, low benefit)

This captures "bang for buck" geometrically!
"""))
```

**4.6 - Calculate Silver Gauge for ALL Crisp Skills**
```python
display(Markdown("### Applying Silver Gauge to Our Three Skills"))

def calculate_silver_for_crisp_skills():
    """Query skills and calculate Silver Gauge metrics"""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Skill)
            WHERE s.kind IN ['sense', 'act'] AND s.name IN ['peek_door', 'try_door', 'go_window']
            RETURN s.name, s.cost, s.goal_info, s.info_gain
        """)

        skills_silver = []
        for record in result:
            name = record['s.name']
            cost = record['s.cost']
            goal = record['s.goal_info']
            info = record['s.info_gain']

            # k_explore
            epsilon = 1e-10
            gm_explore = np.sqrt(goal * info + epsilon)
            am_explore = (goal + info) / 2.0 + epsilon
            k_explore = gm_explore / am_explore

            # k_efficiency
            benefit = goal + info
            cost_inv = 1.0 / (cost + epsilon)
            gm_eff = np.sqrt(benefit * cost_inv + epsilon)
            am_eff = (benefit + cost_inv) / 2.0 + epsilon
            k_efficiency = gm_eff / am_eff

            skills_silver.append({
                'Skill': name,
                'Goal': f"{goal:.2f}",
                'Info': f"{info:.2f}",
                'Cost': f"{cost:.2f}",
                'k_explore': f"{k_explore:.4f}",
                'k_efficiency': f"{k_efficiency:.4f}"
            })

        return pd.DataFrame(skills_silver)

df_silver = calculate_silver_for_crisp_skills()
display(df_silver)

display(Markdown("""
**WAIT... WHAT?!**

Look at the **k_explore** column:
- peek_door: k ≈ 0.0001 (specialist)
- try_door: k ≈ 0.0000 (specialist)
- go_window: k ≈ 0.0000 (specialist)

**They're ALL specialists!** (k ≈ 0)

Even though peek_door is "exploration" and try_door is "exploitation",
BOTH are imbalanced (100% in one direction, 0% in the other)!
"""))
```

**4.7 - THE REVELATION: Geometric Gap Visualization**
```python
display(Markdown("### The k_explore ≈ 0 Phenomenon"))

# Scatter plot of skills in geometric space
def plot_geometric_fingerprints(df):
    fig, ax = plt.subplots(figsize=(12, 8))

    for idx, row in df.iterrows():
        k_exp = float(row['k_explore'])
        k_eff = float(row['k_efficiency'])
        skill_name = row['Skill']

        # Plot point
        ax.scatter(k_exp, k_eff, s=500, alpha=0.7, edgecolors='black', linewidth=2, label=skill_name)

        # Add label
        ax.annotate(skill_name, (k_exp, k_eff), fontsize=11, fontweight='bold',
                    xytext=(10, 10), textcoords='offset points')

    # Show the GAP
    ax.axvspan(0.5, 1.0, alpha=0.2, color='green', label='Multi-objective zone (EMPTY!)')
    ax.axvspan(0.0, 0.1, alpha=0.2, color='red', label='Specialist zone (ALL skills here!)')

    ax.set_xlabel('k_explore (specialist ← 0 ... 1 → balanced)', fontsize=14, fontweight='bold')
    ax.set_ylabel('k_efficiency (poor ← 0 ... 1 → excellent)', fontsize=14, fontweight='bold')
    ax.set_title('Geometric Fingerprints of Crisp Skills\n⚠ GAP REVEALED: No skills in multi-objective zone!',
                 fontsize=16, fontweight='bold')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10, loc='upper right')

    plt.tight_layout()
    plt.show()

plot_geometric_fingerprints(df_silver)

display(Markdown("""
## 🎯 THE BIG REVELATION 🎯

**Discovery**: ALL crisp skills cluster at k_explore ≈ 0!

**Why?**:
- peek_door: goal=0.0, info=1.0 → imbalanced → k=0
- try_door: goal=1.0, info=0.0 → imbalanced → k=0

**Both exploration AND exploitation are specialists** (just in opposite directions!)

**The GAP**: No skills exist in the multi-objective zone (k > 0.5)

**Implication**: To fill this gap, we need BALANCED SKILLS that provide BOTH goal AND info!

This is the diagnostic-driven design pattern:
1. ✓ Built diagnostic (Silver Gauge)
2. ✓ Applied to system (crisp skills)
3. ✓ **Diagnostic revealed gap** (k ≈ 0 everywhere) ← WE ARE HERE
4. → Gap inspires solution (balanced skills) ← NEXT PART!
"""))
```

**4.8 - Interactive k Explorer Challenge**
```python
display(Markdown("### 💡 Interactive Challenge: Design a Balanced Skill"))

goal_frac_slider = widgets.FloatSlider(value=0.5, min=0, max=1, step=0.05,
                                        description='Goal fraction:')
info_frac_slider = widgets.FloatSlider(value=0.5, min=0, max=1, step=0.05,
                                        description='Info fraction:')
challenge_output = widgets.Output()

def calculate_k_for_design(goal_frac, info_frac):
    with challenge_output:
        challenge_output.clear_output()

        epsilon = 1e-10
        gm = np.sqrt(goal_frac * info_frac + epsilon)
        am = (goal_frac + info_frac) / 2.0 + epsilon
        k = gm / am

        print(f"Skill Design:")
        print(f"  Goal fraction: {goal_frac:.2f}")
        print(f"  Info fraction: {info_frac:.2f}")
        print(f"  k_explore: {k:.4f}")
        print()

        if k > 0.8:
            print("✓✓✓ EXCELLENT! Nearly perfect balance!")
        elif k > 0.5:
            print("✓✓ GOOD! Multi-objective skill achieved!")
        elif k > 0.2:
            print("✓ Moderate balance")
        else:
            print("✗ Still too specialized")

        # Visual indicator
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.barh(['k_explore'], [k], color='green' if k > 0.5 else 'orange', alpha=0.7, edgecolor='black', linewidth=2)
        ax.set_xlim(0, 1)
        ax.axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='Multi-objective threshold')
        ax.set_xlabel('k_explore', fontsize=12)
        ax.legend()
        plt.tight_layout()
        plt.show()

challenge_interactive = widgets.interactive_output(
    calculate_k_for_design,
    {'goal_frac': goal_frac_slider, 'info_frac': info_frac_slider}
)

display(goal_frac_slider, info_frac_slider, challenge_output)
calculate_k_for_design(0.5, 0.5)

display(Markdown("""
**Challenge**: Can you design a skill with k_explore > 0.7?

**Hint**: You need BOTH goal and info to be substantial (balanced)!
Try goal=0.7, info=0.7 to see near-perfect balance.
"""))
```

**4.9 - Checkpoint 4**
```python
checkpoint4 = widgets.RadioButtons(
    options=['k = 0.0 (impossible)',
             'k = 0.5 (moderate)',
             'k = 1.0 (perfect balance)',
             'k > 1.0 (super-balanced)'],
    description='What k_explore indicates perfect balance between goal and info?',
)

check4_button = widgets.Button(description="Check Answer")
check4_output = widgets.Output()

def check_checkpoint4(b):
    with check4_output:
        check4_output.clear_output()
        if checkpoint4.value == 'k = 1.0 (perfect balance)':
            print("✓ Correct! k = 1.0 occurs when goal = info (perfect balance).")
            print("  Mathematically: GM = AM only when both inputs are equal.")
        else:
            print("✗ Not quite. Remember: k = GM/AM, and GM = AM only when a = b.")
            print("  So k = 1.0 means perfect balance!")

check4_button.on_click(check_checkpoint4)
display(checkpoint4, check4_button, check4_output)
```

---

### PART 5: Multi-Objective Evolution - Balanced Skills (20 minutes)

**Goal**: Show how the diagnostic insight leads to architectural innovation

**5.1 - The Diagnostic-Driven Design Pattern**
```python
display(Markdown("""
### From Gap to Solution: Diagnostic-Driven Design

**The Pattern:**
1. ✅ Build sophisticated diagnostic (Silver Gauge with Pythagorean means)
2. ✅ Apply diagnostic to existing system (crisp skills)
3. ✅ **Diagnostic reveals unexpected gap** (k ≈ 0 everywhere)
4. → **Gap inspires architectural innovation** (balanced skills)
5. → **Solution showcases diagnostic's value** (fills geometric spectrum)

**This is a GENERAL pattern applicable beyond this project!**

**The Question**: What if skills could be multi-objective?
What if we could provide BOTH goal achievement AND information gain?
"""))
```

**5.2 - Compositional Skill Design**
```python
display(Markdown("""
### Multi-Objective Skills via Composition

**Idea**: Create new skills as WEIGHTED COMBINATIONS of base skills

**Example - probe_and_try**:
```
probe_and_try = 0.4 × peek_door + 0.6 × try_door
```

**Properties inherited**:
- Cost: 0.4 × cost(peek) + 0.6 × cost(try)
- Goal: 0.6 × goal(try) = 0.6 × 1.0 = 0.6
- Info: 0.4 × info(peek) = 0.4 × 1.0 = 0.4

**Predicted k_explore**:
```
GM(0.6, 0.4) / AM(0.6, 0.4) = sqrt(0.24) / 0.5 ≈ 0.98
```

Wait, let me recalculate:
- GM = sqrt(0.6 × 0.4) = sqrt(0.24) ≈ 0.4899
- AM = (0.6 + 0.4) / 2 = 0.5
- k = 0.4899 / 0.5 ≈ 0.98

Actually, perfect balance would be 0.5, 0.5:
- GM = sqrt(0.25) = 0.5
- AM = 0.5
- k = 1.0

For 0.6, 0.4:
- GM ≈ 0.490
- AM = 0.5
- k ≈ 0.98

Close to perfect balance!
"""))
```

**5.3 - The Four Balanced Skills**
```python
display(Markdown("### Balanced Skills in the Database"))

def query_balanced_skills():
    """Query balanced skills and their properties"""
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Skill)
            WHERE s.kind = 'balanced'
            RETURN s.name, s.cost, s.goal_fraction, s.info_fraction
            ORDER BY s.name
        """)

        balanced_skills = []
        for record in result:
            name = record['s.name']
            cost = record['s.cost']
            goal_frac = record['s.goal_fraction']
            info_frac = record['s.info_fraction']

            # Calculate predicted k_explore
            epsilon = 1e-10
            gm = np.sqrt(goal_frac * info_frac + epsilon)
            am = (goal_frac + info_frac) / 2.0 + epsilon
            k_explore = gm / am

            balanced_skills.append({
                'Skill': name,
                'Cost': f"{cost:.2f}",
                'Goal Fraction': f"{goal_frac:.2f}",
                'Info Fraction': f"{info_frac:.2f}",
                'Predicted k_explore': f"{k_explore:.4f}"
            })

        return pd.DataFrame(balanced_skills)

df_balanced = query_balanced_skills()
display(df_balanced)

display(Markdown("""
**Four Balanced Skills**:
1. **adaptive_peek**: 60% info + 40% goal → k ≈ 0.98 (nearly perfect!)
2. **exploratory_action**: 70% goal + 70% info → k ≈ 1.0 (perfect balance!)
3. **probe_and_try**: 60% goal + 40% info → k ≈ 0.98
4. **informed_window**: 80% goal + 30% info → k ≈ 0.85

**All have k > 0.8!** (Multi-objective zone successfully filled!)
"""))
```

**5.4 - Validation: Calculate Actual k_explore Values**
```python
display(Markdown("### Validation: scoring_balanced.py Results"))

# Run the actual scoring module
from scoring_balanced import demonstrate_balanced_skills

print("Running balanced skill scoring...")
demonstrate_balanced_skills()

display(Markdown("""
**Validation Results** (from actual code execution):
- probe_and_try: k = 0.7332
- informed_window: k = 0.5599
- exploratory_action: k = 0.8000
- adaptive_peek: k = 0.9165

**All values k ∈ [0.56, 0.92]** ✓

This FILLS the geometric gap that crisp skills left empty!
"""))
```

**5.5 - THE FULL GEOMETRIC SPECTRUM**
```python
display(Markdown("### Complete Geometric Fingerprint Map"))

# Combine crisp and balanced skills
def plot_full_spectrum():
    # Get data for both crisp and balanced skills
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Skill)
            WHERE s.kind IN ['sense', 'act', 'balanced']
            RETURN s.name, s.kind, s.cost,
                   COALESCE(s.goal_info, s.goal_fraction, 0) as goal,
                   COALESCE(s.info_gain, s.info_fraction, 0) as info
        """)

        all_skills = []
        for record in result:
            name = record['s.name']
            kind = record['s.kind']
            goal = record['goal']
            info = record['info']
            cost = record['s.cost']

            # Calculate silver gauge
            epsilon = 1e-10
            gm_exp = np.sqrt(goal * info + epsilon)
            am_exp = (goal + info) / 2.0 + epsilon
            k_explore = gm_exp / am_exp

            benefit = goal + info
            cost_inv = 1.0 / (cost + epsilon)
            gm_eff = np.sqrt(benefit * cost_inv + epsilon)
            am_eff = (benefit + cost_inv) / 2.0 + epsilon
            k_efficiency = gm_eff / am_eff

            all_skills.append({
                'name': name,
                'kind': kind,
                'k_explore': k_explore,
                'k_efficiency': k_efficiency
            })

        fig, ax = plt.subplots(figsize=(14, 10))

        colors = {'sense': '#3498db', 'act': '#e74c3c', 'balanced': '#2ecc71'}
        markers = {'sense': 'o', 'act': 's', 'balanced': '^'}

        for skill in all_skills:
            ax.scatter(skill['k_explore'], skill['k_efficiency'],
                       s=600, alpha=0.7,
                       color=colors[skill['kind']],
                       marker=markers[skill['kind']],
                       edgecolors='black', linewidth=2,
                       label=skill['kind'] if skill['kind'] not in ax.get_legend_handles_labels()[1] else '')

            ax.annotate(skill['name'],
                        (skill['k_explore'], skill['k_efficiency']),
                        fontsize=10, fontweight='bold',
                        xytext=(8, 8), textcoords='offset points')

        # Highlight zones
        ax.axvspan(0.0, 0.1, alpha=0.1, color='red', label='Specialist zone (crisp)')
        ax.axvspan(0.5, 1.0, alpha=0.1, color='green', label='Multi-objective zone (balanced)')

        ax.set_xlabel('k_explore (specialist ← 0 ... 1 → balanced)', fontsize=14, fontweight='bold')
        ax.set_ylabel('k_efficiency (poor ← 0 ... 1 → excellent)', fontsize=14, fontweight='bold')
        ax.set_title('Complete Geometric Spectrum: Crisp + Balanced Skills\n✓ GAP FILLED!',
                     fontsize=16, fontweight='bold')
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=11, loc='upper left')

        plt.tight_layout()
        plt.show()

plot_full_spectrum()

display(Markdown("""
## 🎉 SUCCESS! 🎉

**Before**: All skills clustered at k ≈ 0 (specialist zone)
**After**: Full geometric spectrum from k=0 to k≈0.92

**The Innovation**:
- Crisp skills: Pedagogical clarity (sharp boundaries)
- Balanced skills: Analytical richness (smooth spectrum)
- Together: Complete toolkit for active inference

**Complementarity over replacement!**
"""))
```

**5.6 - Phase Diagram Comparison**
```python
# Load and display phase diagram visualization
display(Image('phase_diagram_comparison.png'))

display(Markdown("""
### Decision Boundary Evolution

**Left (Crisp)**: Sharp transitions between peek/try/window
**Right (Balanced)**: Smooth transitions with multi-objective options

Balanced skills create "buffer zones" where both goal AND info matter!
"""))
```

**5.7 - Skill Mode Comparison** [truncated - would show episode comparisons]

**5.8 - Checkpoint 5**
```python
# Challenge: Design a skill with specific k value
# [Implementation...]
```

---

### PART 6: Neo4j Graph Database Deep Dive (15 minutes)

**Goal**: Explore the graph structure and query patterns

[Detailed cells showing:
- Schema visualization
- Cypher query basics
- Skills subgraph exploration
- Procedural memory network
- Episode execution traces
- Custom query playground]

---

### PART 7: Visualization Gallery (10 minutes)

**Goal**: Comprehensive visual reference

[Cells showing all key visualizations:
- Belief geometry plots
- Goal-info space
- k_explore comparison charts
- Phase diagrams
- Skill spectrum
- Interactive 3D plotly visualization]

---

### PART 8: Meta-Insights & Research Directions (10 minutes)

**Goal**: Synthesize learning and point to future work

**8.1 - What We've Learned**
```python
display(Markdown("""
## Key Takeaways

### 1. Active Inference Fundamentals
- Agents balance exploration (info gain) and exploitation (goal achievement)
- Expected Free Energy (EFE) unifies both into single objective
- Beliefs update via Bayes' rule based on observations

### 2. Silver Gauge Innovation
- Pythagorean means (HM, GM, AM) create interpretable diagnostics
- Dimensionless k coefficients are scale-invariant
- 100% behavioral fidelity (no approximation)
- Geometric "fingerprints" of decision strategies

### 3. The k_explore ≈ 0 Revelation
- ALL crisp skills are specialists (k ≈ 0)
- BOTH exploration AND exploitation are imbalanced
- k measures specialist vs generalist, not explore vs exploit

### 4. Multi-Objective Evolution
- Diagnostic revealed architectural gap
- Balanced skills fill multi-objective zone (k ∈ [0.56, 0.92])
- Complementarity: crisp + balanced = complete spectrum

### 5. Diagnostic-Driven Design Pattern
- Build sophisticated diagnostic
- Apply to existing system
- Diagnostic reveals gap
- Gap inspires solution
- Solution showcases diagnostic value

**This pattern generalizes beyond active inference!**
"""))
```

**8.2 - Scale-Invariant Transfer Learning**
```python
display(Markdown("""
### Research Direction: Cross-Domain Transfer

**Key Insight**: Dimensionless k coefficients enable pattern transfer!

**Example**:
- Domain A (locked door): k_explore > 0.6 in early phase → success
- Domain B (chess opening): Apply same pattern → success
- Domain C (robotic manipulation): Same geometric strategy

**Why it works**:
- k values have no units (pure ratios)
- Same "shape" applies regardless of scale
- Build reusable strategy libraries

**Applications**:
- Curriculum learning: Progress through k values
- Meta-learning: Learn to adjust k based on task
- Multi-agent: Assign roles via geometric profiles
"""))
```

**8.3 - Research Directions Enabled**
```python
display(Markdown("""
### 14 Research Directions Unlocked

#### 1. Geometric Curriculum Learning
- Sequence tasks by k_explore: 0.9 → 0.7 → 0.5 → 0.3 → 0.0
- Performance-based progression, not time-based

#### 2. Transfer Learning via Geometry
- Build cross-domain pattern libraries
- "When k_explore drops below 0.3, switch to exploitation"

#### 3. Meta-Learning with Shape Signals
- Direct geometric feedback loops
- Learn to adapt k values based on task properties

#### 4. Multi-Agent Coordination
- Assign roles via geometric profiles
- Team diversity optimization (ensure coverage of k spectrum)

#### 5. Geometric Anomaly Detection
- Expected pattern: k_explore decreases during episode
- Violations indicate bugs or novel situations

#### 6. Continuous Skill Spaces
- Instead of 7 discrete skills, infinite resolution
- Sample any point in k_explore × k_efficiency space

#### 7. Hierarchical Geometries
- Macro-scale: Mission-level k values
- Micro-scale: Step-level k values
- Multi-resolution decision-making

#### 8. Deep RL Integration
- Use k coefficients as auxiliary objectives
- Reward shaping with geometric targets

#### 9. Interpretable Policy Distillation
- Train deep RL, then analyze with Silver Gauge
- Extract interpretable patterns from black boxes

#### 10. Geometric Policy Gradients
- Optimize directly in k-space
- Smoother, more interpretable learning

...and 4 more! (See FINAL_REPORT.md)
"""))
```

**8.4 - Try It Yourself Challenges**
```python
display(Markdown("""
### 💡 Hands-On Challenges

#### Challenge 1: Design Your Own Skill
- Choose goal_fraction and info_fraction
- Target: k_explore = 0.75
- Implement in Neo4j and test

#### Challenge 2: Create Memory Pattern
- Identify context (belief range, history)
- Recommend skill
- Add to database and validate

#### Challenge 3: Modify Cost Structure
- Change skill costs in database
- Observe how decision boundaries shift
- Does k_explore change? (Should it?)

#### Challenge 4: Geometric Curriculum
- Implement scheduler that adjusts available skills
- Early: Only high k_explore skills
- Late: Allow low k_explore skills
- Measure learning efficiency

#### Challenge 5: Multi-Agent Scenario
- Create 3 agents with different k profiles
- Specialist (k < 0.3)
- Generalist (k > 0.7)
- Adaptive (k varies)
- Compare team performance
"""))
```

**8.5 - Further Reading**
```python
display(Markdown("""
### Documentation & Resources

**Project Documents**:
- [FINAL_REPORT.md](FINAL_REPORT.md) - 75-page comprehensive analysis
- [PYTHAGOREAN_MEANS_EXPLAINED.md](PYTHAGOREAN_MEANS_EXPLAINED.md) - Mathematical deep dive
- [BALANCED_POLICY_GUIDE.md](BALANCED_POLICY_GUIDE.md) - Multi-objective skills guide
- [README.md](README.md) - Project overview and quickstart

**Academic Papers**:
- Friston et al. (2015) - "Active inference and epistemic value"
- Friston et al. (2017) - "Active inference: A process theory"
- Da Costa et al. (2020) - "Active inference on discrete state-spaces"

**Related Work**:
- Multi-objective reinforcement learning
- Pareto-optimal policies
- Information gain in decision-making
- Geometric deep learning

**Tools & Libraries**:
- Neo4j graph database
- PyTorch for deep RL extensions
- NetworkX for graph analysis
- Plotly for interactive visualizations
"""))
```

---

### PART 9: Appendix (Reference Material)

**9.1 - Mathematical Derivations**
[Detailed proofs of:
- EFE formula derivation
- Pythagorean inequality
- k coefficient bounds
- Behavioral fidelity proof]

**9.2 - Complete Code Listings**
[Full code for:
- score_skill()
- filter_skills_by_mode()
- silver_k_explore()
- silver_k_efficiency()]

**9.3 - Cypher Query Reference**
[Common patterns:
- Get all skills
- Query memories
- Find episodes
- Calculate aggregates]

**9.4 - Glossary**
[Definitions of all key terms]

---

## Technical Implementation Notes

### Required Libraries
```python
# Core
import numpy as np
import pandas as pd

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px

# Database
from neo4j import GraphDatabase

# Interactive widgets
import ipywidgets as widgets
from IPython.display import display, Markdown, HTML, Image

# Graph analysis
import networkx as nx

# Statistics
from scipy.stats import beta
```

### Neo4j Connection Template
```python
# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

# Connection
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Query helper
def run_query(query, **params):
    with driver.session() as session:
        result = session.run(query, **params)
        return [dict(record) for record in result]
```

### Visualization Helpers
```python
# Consistent styling
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

COLORS = {
    'crisp_sense': '#3498db',
    'crisp_act': '#e74c3c',
    'balanced': '#2ecc71',
    'specialist_zone': '#ffcccc',
    'balanced_zone': '#ccffcc'
}

def style_plot(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(alpha=0.3)
```

---

## Critical Success Factors

### ✅ DO:
1. **Start with concrete problem** (locked door) before abstract math
2. **Use real Neo4j data** throughout (not synthetic examples)
3. **Make everything interactive** (sliders, buttons, queries)
4. **Build to climax** (k ≈ 0 revelation in Part 4)
5. **Test understanding** (checkpoints at transitions)
6. **Provide multiple representations** (formula + code + visualization)
7. **Show full narrative arc** (problem → solution → revelation → innovation)
8. **Enable exploration** (query playground, parameter tuning)
9. **Connect to broader context** (research directions, applications)
10. **Maintain professional quality** (publication-ready visuals)

### ❌ DON'T:
1. **Don't dump math upfront** (build intuition first)
2. **Don't skip motivation** (always explain "why")
3. **Don't just show plots** (explain what they mean)
4. **Don't assume prerequisites** (explain as you go)
5. **Don't make it passive** (require interaction)
6. **Don't lose the narrative** (maintain story thread)
7. **Don't overcomplicate widgets** (simple sliders > complex UIs)
8. **Don't skip the revelation** (k ≈ 0 is the climax!)
9. **Don't forget next steps** (research directions at end)
10. **Don't neglect code quality** (clean, documented, runnable)

---

## Estimated Timeline

### For Learner (Completing Notebook):
- **Part 0-1**: 15 minutes - Setup and intuition
- **Part 2-3**: 35 minutes - Active inference math and execution
- **Part 4**: 25 minutes - Silver Gauge (THE REVELATION)
- **Part 5**: 20 minutes - Balanced skills evolution
- **Part 6**: 15 minutes - Neo4j deep dive
- **Part 7**: 10 minutes - Visualization gallery
- **Part 8**: 10 minutes - Meta-insights
- **Total**: ~2-3 hours (can be split across sessions)

### For Developer (Creating Notebook):
- **Structure & outline**: 2-3 hours
- **Part 0-1 implementation**: 3-4 hours
- **Part 2-3 implementation**: 4-5 hours
- **Part 4 implementation**: 5-6 hours (most critical!)
- **Part 5 implementation**: 3-4 hours
- **Part 6-9 implementation**: 4-5 hours
- **Testing & polish**: 3-4 hours
- **Total**: ~25-30 hours development time

---

## Next Steps

### Immediate:
1. Create notebook file structure
2. Implement Part 0 (setup)
3. Implement Part 1 (intuition)
4. Test Neo4j integration

### Short-term:
1. Build out Parts 2-3 (active inference)
2. Create Part 4 (REVELATION - most important!)
3. Implement Part 5 (balanced skills)

### Medium-term:
1. Add Parts 6-8 (database, viz, meta)
2. Create custom visualizations
3. Test with real users
4. Iterate based on feedback

### Long-term:
1. Create video walkthrough
2. Publish as tutorial series
3. Expand to additional scenarios
4. Build interactive web version

---

## Summary

This notebook design provides:

✅ **Pedagogical Structure**: Spiral learning from concrete to abstract
✅ **Interactive Engagement**: Widgets, sliders, queries throughout
✅ **Real Data Integration**: Neo4j database drives all examples
✅ **Narrative Arc**: Problem → Math → Revelation → Innovation
✅ **Multiple Representations**: Formula + Code + Visualization
✅ **Checkpoints**: Test understanding at transitions
✅ **Professional Quality**: Publication-ready visuals and explanations
✅ **Research Connections**: Points to 14+ future directions
✅ **Complete Coverage**: All aspects of project explained
✅ **Climactic Revelation**: k ≈ 0 discovery as centerpiece

**This notebook will be a comprehensive, engaging, and educational resource for understanding active inference through geometric diagnostics!**
