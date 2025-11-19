"""
MacGyver MUD Utilities
======================

Core functions and widget builders for Active Inference demonstrations.
Extracted from verbose notebook to keep notebook cells clean and focused.

Author: Claude + Human collaboration
License: MIT
"""

from IPython.display import display, Markdown, HTML, clear_output
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import ipywidgets as widgets
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Global connection state
NEO4J_CONNECTED = False
DRIVER = None

# Color palette
COLORS = {
    'unlocked': '#2ecc71',  # Green
    'locked': '#e74c3c',     # Red
    'info': '#3498db',       # Blue
    'warning': '#f39c12',    # Orange
    'neutral': '#95a5a6'     # Gray
}

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def run_query(query, **params):
    """
    Execute Neo4j query and return results as list of dicts.

    Args:
        query: Cypher query string
        **params: Query parameters

    Returns:
        List of dictionaries with query results
    """
    if not NEO4J_CONNECTED or DRIVER is None:
        return []

    try:
        with DRIVER.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]
    except Exception as e:
        print(f"Query error: {e}")
        return []


# ============================================================================
# ACTIVE INFERENCE CORE
# ============================================================================

def silver_k_explore(goal_value, info_gain):
    """
    Calculate k_explore coefficient using Pythagorean means.

    The Silver Gauge balances exploration (info gain) vs exploitation (goal).
    k ≈ 0 suggests perfect balance (geometric mean ≈ arithmetic mean).

    Args:
        goal_value: Goal achievement fraction (0-1)
        info_gain: Information gain fraction (0-1)

    Returns:
        k_explore coefficient (0-1), where lower = more balanced
    """
    if goal_value <= 0 or info_gain <= 0:
        return 1.0  # Maximum imbalance

    gm = np.sqrt(goal_value * info_gain)
    am = (goal_value + info_gain) / 2

    if am == 0:
        return 1.0

    return gm / am


def silver_k_efficiency(benefit, cost):
    """
    Calculate k_efficiency coefficient.

    Balances benefit vs cost using Pythagorean means.

    Args:
        benefit: Benefit value
        cost: Cost value

    Returns:
        k_efficiency coefficient (0-1)
    """
    if benefit <= 0 or cost <= 0:
        return 1.0

    # Use 1/cost to compare benefit with inverse cost
    inv_cost = 1.0 / cost
    gm = np.sqrt(benefit * inv_cost)
    am = (benefit + inv_cost) / 2

    if am == 0:
        return 1.0

    return gm / am


def score_skill(skill, belief_locked):
    """
    Calculate Expected Free Energy (EFE) for a skill.

    EFE = cost - expected_goal - expected_info
    Lower EFE is better (less "surprise"/more preferred)

    Args:
        skill: Dict with 'name', 'cost', 'goal', 'info_gain'
        belief_locked: Probability door is locked (0-1)

    Returns:
        EFE value (lower is better)
    """
    cost = skill['cost']
    goal = skill['goal']
    info_gain = skill['info_gain']

    # Expected goal: goal value × P(success)
    # For try_door: succeeds only if unlocked
    if skill['name'] == 'try_door':
        expected_goal = goal * (1 - belief_locked)
    else:
        # peek_door always gets its goal (observing)
        expected_goal = goal

    # Expected info gain (simplified: just use the value)
    expected_info = info_gain

    # EFE formula
    efe = cost - expected_goal - expected_info

    return efe


def simulate_belief_update(prior_locked, true_state, action):
    """
    Simulate Bayesian belief update.

    Args:
        prior_locked: Prior P(locked) (0-1)
        true_state: True door state ('locked' or 'unlocked')
        action: Action taken ('peek_door' or 'try_door')

    Returns:
        (posterior_locked, observation)
    """
    if action == 'peek_door':
        # 95% accurate sensing
        if true_state == 'locked':
            obs = 'locked' if np.random.rand() < 0.95 else 'unlocked'
        else:
            obs = 'unlocked' if np.random.rand() < 0.95 else 'locked'

        # Bayesian update
        if obs == 'locked':
            # P(locked|obs_locked) = P(obs_locked|locked) × P(locked) / P(obs_locked)
            likelihood = 0.95
            marginal = 0.95 * prior_locked + 0.05 * (1 - prior_locked)
            posterior_locked = (likelihood * prior_locked) / marginal
        else:
            # P(locked|obs_unlocked) = P(obs_unlocked|locked) × P(locked) / P(obs_unlocked)
            likelihood = 0.05
            marginal = 0.05 * prior_locked + 0.95 * (1 - prior_locked)
            posterior_locked = (likelihood * prior_locked) / marginal

        return posterior_locked, obs

    else:
        # try_door: observation is success/failure
        obs = 'failed' if true_state == 'locked' else 'succeeded'
        # After trying, we know for certain
        posterior_locked = 1.0 if obs == 'failed' else 0.0
        return posterior_locked, obs


def simulate_episode(initial_belief, true_door_state, max_steps=5):
    """
    Simulate complete episode with skill selection.

    Args:
        initial_belief: Initial P(locked)
        true_door_state: 'locked' or 'unlocked'
        max_steps: Maximum steps before giving up

    Returns:
        List of step dicts with belief, action, observation
    """
    belief_locked = initial_belief
    history = []

    # Skill definitions
    skills = [
        {'name': 'peek_door', 'cost': 1.0, 'goal': 0.0, 'info_gain': 0.8},
        {'name': 'try_door', 'cost': 2.0, 'goal': 10.0, 'info_gain': 0.0},
    ]

    for step in range(max_steps):
        # Score all skills
        scores = {s['name']: score_skill(s, belief_locked) for s in skills}

        # Choose action with lowest EFE
        chosen_action = min(scores, key=scores.get)

        # Execute action
        new_belief, obs = simulate_belief_update(belief_locked, true_door_state, chosen_action)

        # Record step
        history.append({
            'step': step + 1,
            'belief_locked': belief_locked,
            'action': chosen_action,
            'observation': obs,
            'new_belief': new_belief,
            'scores': scores.copy()
        })

        belief_locked = new_belief

        # Check if done
        if chosen_action == 'try_door':
            break

    return history


# ============================================================================
# VISUALIZATION HELPERS
# ============================================================================

def style_plot(ax, title, xlabel, ylabel):
    """
    Apply consistent styling to matplotlib plots.

    Args:
        ax: Matplotlib axes object
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
    """
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def plot_belief_distribution(belief_locked, ax=None, show_entropy=True):
    """
    Plot belief distribution as bar chart.

    Args:
        belief_locked: P(locked) (0-1)
        ax: Matplotlib axes (creates new if None)
        show_entropy: Whether to display entropy

    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))

    states = ['Unlocked', 'Locked']
    probabilities = [1 - belief_locked, belief_locked]
    colors = [COLORS['unlocked'], COLORS['locked']]

    bars = ax.bar(states, probabilities, color=colors, alpha=0.7,
                  edgecolor='black', linewidth=2)

    ax.set_ylim(0, 1.1)
    ax.set_ylabel('Probability', fontsize=12, fontweight='bold')
    ax.set_title('Belief Distribution', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, prob in zip(bars, probabilities):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{prob:.0%}', ha='center', va='bottom',
                fontsize=14, fontweight='bold')

    # Show entropy if requested
    if show_entropy and belief_locked > 0 and belief_locked < 1:
        entropy = -(belief_locked * np.log2(belief_locked) +
                   (1-belief_locked) * np.log2(1-belief_locked))
        ax.text(0.98, 0.98, f'Entropy: {entropy:.2f} bits',
                transform=ax.transAxes, ha='right', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=11)

    return ax


def visualize_room_graph():
    """
    Query and visualize room structure from Neo4j using NetworkX.
    Shows fallback diagram if not connected.
    """
    if NEO4J_CONNECTED:
        query = """
        MATCH (s:State)-[r]->(t:State)
        RETURN s.name AS start_name, type(r) AS rel_type, t.name AS end_name
        """
        results = run_query(query)

        if results:
            G = nx.DiGraph()
            for record in results:
                G.add_edge(record['start_name'], record['end_name'],
                          label=record['rel_type'])

            plt.figure(figsize=(14, 8))
            pos = nx.spring_layout(G, k=2, iterations=50)

            # Color nodes by type
            node_colors = []
            for node in G.nodes():
                if 'escaped' in node.lower():
                    node_colors.append(COLORS['unlocked'])
                elif 'stuck' in node.lower():
                    node_colors.append(COLORS['locked'])
                else:
                    node_colors.append(COLORS['info'])

            nx.draw(G, pos, with_labels=True, node_color=node_colors,
                   node_size=4000, font_size=11, font_weight='bold',
                   arrows=True, edge_color='gray', width=2.5,
                   arrowsize=20, alpha=0.9)

            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=10)

            plt.title("MacGyver MUD State Space", fontsize=16, fontweight='bold', pad=20)
            plt.axis('off')
            plt.tight_layout()
            plt.show()
            return

    # Fallback: conceptual diagram
    display(Markdown("""
    ### Room Structure (Conceptual)

    ```
    START → [observe locked door] → ...
         → [try door] → STUCK (if locked)
                     → ESCAPED (if unlocked)
         → [try window] → ESCAPED
    ```

    *Connect to Neo4j to see interactive graph visualization*
    """))


def plot_3panel_update(prior_locked, action, observation, posterior_locked):
    """
    Create 3-panel visualization: Before → Action → After.

    Args:
        prior_locked: Prior P(locked)
        action: Action taken
        observation: Observation received
        posterior_locked: Posterior P(locked)
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

    # Panel 1: Prior belief
    plot_belief_distribution(prior_locked, ax=ax1, show_entropy=False)
    ax1.set_title('BEFORE: Prior Belief', fontsize=14, fontweight='bold')

    # Panel 2: Action taken
    ax2.axis('off')
    ax2.text(0.5, 0.7, f'Action: {action}',
             transform=ax2.transAxes, ha='center', va='center',
             fontsize=16, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor=COLORS['info'], alpha=0.3))
    ax2.text(0.5, 0.5, f'Observation:\n{observation}',
             transform=ax2.transAxes, ha='center', va='center',
             fontsize=14, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor=COLORS['warning'], alpha=0.3))
    ax2.text(0.5, 0.3, '→',
             transform=ax2.transAxes, ha='center', va='center',
             fontsize=40, fontweight='bold')

    # Panel 3: Posterior belief
    plot_belief_distribution(posterior_locked, ax=ax3, show_entropy=False)
    ax3.set_title('AFTER: Posterior Belief', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.show()


def plot_pythagorean_means(a, b):
    """
    Visualize Pythagorean means and their relationships.

    Args:
        a, b: Two positive values

    Returns:
        Dict with HM, GM, AM values
    """
    if a <= 0 or b <= 0:
        print("Values must be positive!")
        return None

    # Calculate means
    hm = 2 / (1/a + 1/b)  # Harmonic mean
    gm = np.sqrt(a * b)    # Geometric mean
    am = (a + b) / 2       # Arithmetic mean

    # Visualization
    fig, ax = plt.subplots(figsize=(12, 6))

    means_values = [hm, gm, am]
    means_labels = [f'HM\n{hm:.3f}', f'GM\n{gm:.3f}', f'AM\n{am:.3f}']
    colors = [COLORS['warning'], COLORS['info'], COLORS['unlocked']]

    bars = ax.barh(means_labels, means_values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

    ax.set_xlabel('Value', fontsize=12, fontweight='bold')
    ax.set_title(f'Pythagorean Means for a={a:.2f}, b={b:.2f}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, means_values):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f' {val:.3f}', va='center', fontsize=12, fontweight='bold')

    # Show inequality
    ax.text(0.98, 0.02, 'HM ≤ GM ≤ AM (always holds)',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=11, style='italic',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

    plt.tight_layout()
    plt.show()

    # Calculate balance
    k = gm / am if am > 0 else 1.0

    return {
        'HM': hm,
        'GM': gm,
        'AM': am,
        'k': k,
        'balance': 'EXCELLENT' if k > 0.95 else 'GOOD' if k > 0.85 else 'IMBALANCED'
    }


# ============================================================================
# DATA QUERIES
# ============================================================================

def query_crisp_skills():
    """
    Get crisp skill details from Neo4j.
    Falls back to hardcoded data if not connected.

    Returns:
        DataFrame with skill properties
    """
    # Note: Neo4j database currently doesn't have goal/info_gain properties
    # Using fallback data for pedagogical purposes

    # Fallback data (always use this for now)
    return pd.DataFrame([
        {'name': 'peek_door', 'cost': 1.0, 'goal': 0.0, 'info_gain': 0.8},
        {'name': 'try_door', 'cost': 2.0, 'goal': 10.0, 'info_gain': 0.0},
        {'name': 'go_window', 'cost': 5.0, 'goal': 8.0, 'info_gain': 0.0}
    ])


def calculate_silver_for_crisp():
    """
    Calculate Silver Gauge metrics for crisp skills.

    Returns:
        DataFrame with skills and their Silver metrics
    """
    skills_df = query_crisp_skills()

    # Calculate k_explore (balances goal vs info_gain)
    skills_df['k_explore'] = skills_df.apply(
        lambda row: silver_k_explore(row['goal'], row['info_gain'])
        if (row['goal'] is not None and row['info_gain'] is not None and
            row['goal'] > 0 and row['info_gain'] > 0) else np.nan,
        axis=1
    )

    # Calculate k_efficiency (balances benefit vs cost)
    # Use goal as benefit proxy
    skills_df['k_efficiency'] = skills_df.apply(
        lambda row: silver_k_efficiency(row['goal'], row['cost'])
        if (row['goal'] is not None and row['cost'] is not None and
            row['goal'] > 0) else np.nan,
        axis=1
    )

    return skills_df


# ============================================================================
# WIDGET BUILDERS
# ============================================================================

def create_belief_slider(callback, initial_value=0.5):
    """
    Create standard belief slider with output area.

    Args:
        callback: Function to call on value change
        initial_value: Starting value (0-1)

    Returns:
        (slider, output) tuple
    """
    slider = widgets.FloatSlider(
        value=initial_value,
        min=0, max=1, step=0.05,
        description='P(locked):',
        style={'description_width': '100px'},
        continuous_update=True,
        readout_format='.0%'
    )

    output = widgets.Output()
    slider.observe(callback, names='value')

    return slider, output


def create_quiz_widget(question, options, correct_answer, feedback_dict):
    """
    Create quiz radio buttons with check button.

    Args:
        question: Question text
        options: List of option tuples (value, label)
        correct_answer: Correct option value
        feedback_dict: Dict mapping option values to feedback strings

    Returns:
        VBox widget with quiz UI
    """
    radio = widgets.RadioButtons(
        options=options,
        description='',
        disabled=False
    )

    button = widgets.Button(
        description='Check Answer',
        button_style='success',
        icon='check'
    )

    output = widgets.Output()

    def on_check(b):
        with output:
            clear_output()
            selected = radio.value

            if selected == correct_answer:
                display(HTML(f"<div style='color: {COLORS['unlocked']}; font-weight: bold;'>✓ Correct!</div>"))
            else:
                display(HTML(f"<div style='color: {COLORS['locked']}; font-weight: bold;'>✗ Not quite.</div>"))

            if selected in feedback_dict:
                display(Markdown(feedback_dict[selected]))

    button.on_click(on_check)

    return widgets.VBox([
        widgets.HTML(f"<h4>{question}</h4>"),
        radio,
        button,
        output
    ])


def create_float_input(description, initial_value=0.0, min_val=None, max_val=None):
    """
    Create float input with validation.

    Args:
        description: Input label
        initial_value: Starting value
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        FloatText widget
    """
    kwargs = {
        'value': initial_value,
        'description': description,
        'style': {'description_width': 'initial'},
        'disabled': False
    }

    if min_val is not None:
        kwargs['min'] = min_val
    if max_val is not None:
        kwargs['max'] = max_val

    return widgets.FloatText(**kwargs)


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def show_skill_scores(belief_locked):
    """
    Display skill scores comparison table.

    Args:
        belief_locked: Current P(locked)
    """
    skills = [
        {'name': 'peek_door', 'cost': 1.0, 'goal': 0.0, 'info_gain': 0.8},
        {'name': 'try_door', 'cost': 2.0, 'goal': 10.0, 'info_gain': 0.0},
        {'name': 'go_window', 'cost': 5.0, 'goal': 8.0, 'info_gain': 0.0}
    ]

    # Calculate scores
    scores = []
    for skill in skills:
        efe = score_skill(skill, belief_locked)
        scores.append({
            'Skill': skill['name'],
            'Cost': skill['cost'],
            'Goal': skill['goal'],
            'Info': skill['info_gain'],
            'EFE': f"{efe:.2f}"
        })

    df = pd.DataFrame(scores)

    # Find best
    best_idx = df['EFE'].astype(float).idxmin()

    print(f"\n📊 Skill Scores (P(locked) = {belief_locked:.0%}):\n")
    print(df.to_string(index=False))
    print(f"\n🎯 Best choice: {df.iloc[best_idx]['Skill']} (lowest EFE)")


def show_recommendation(belief_locked):
    """
    Show action recommendation based on belief.

    Args:
        belief_locked: Current P(locked)
    """
    if belief_locked < 0.3:
        rec = "TRY THE DOOR"
        color = COLORS['unlocked']
        reason = "Low probability it's locked, go for it!"
    elif belief_locked > 0.7:
        rec = "PEEK FIRST"
        color = COLORS['info']
        reason = "High probability it's locked, gather info first."
    else:
        rec = "UNCERTAIN"
        color = COLORS['warning']
        reason = "Moderate uncertainty, could go either way."

    display(HTML(f"""
    <div style='background-color: {color}; padding: 15px; border-radius: 5px; opacity: 0.7;'>
        <h3 style='margin: 0; color: white;'>Recommendation: {rec}</h3>
        <p style='margin: 5px 0 0 0; color: white;'>{reason}</p>
    </div>
    """))


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_neo4j(uri="bolt://localhost:7687", user="neo4j", password="macgyver123"):
    """
    Initialize Neo4j connection.

    Args:
        uri: Neo4j URI
        user: Username
        password: Password

    Returns:
        True if connected, False otherwise
    """
    global NEO4J_CONNECTED, DRIVER

    try:
        DRIVER = GraphDatabase.driver(uri, auth=(user, password))
        # Test connection
        with DRIVER.session() as session:
            session.run("RETURN 1")
        NEO4J_CONNECTED = True
        print("✓ Connected to Neo4j")
        return True
    except Exception as e:
        NEO4J_CONNECTED = False
        DRIVER = None
        print(f"✗ Neo4j connection failed: {e}")
        print("  Continuing with fallback data...")
        return False


def get_connection_status():
    """Get HTML status indicator for Neo4j connection."""
    if NEO4J_CONNECTED:
        return HTML(f"<span style='color: {COLORS['unlocked']}; font-weight: bold;'>● Neo4j Connected</span>")
    else:
        return HTML(f"<span style='color: {COLORS['neutral']}; font-weight: bold;'>○ Neo4j Offline (using fallback data)</span>")
