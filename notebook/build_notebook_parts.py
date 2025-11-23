#!/usr/bin/env python3
"""
Script to build remaining parts of the MacGyver MUD Deep Dive notebook.
This adds Parts 2-8 to the existing notebook.
"""

import json
import sys

def create_part2_cells():
    """Part 2: Active Inference - The Math of Uncertainty"""
    cells = []

    # Part 2 Header
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "# PART 2: Active Inference - The Math of Uncertainty\n",
            "\n",
            "**Time**: 20 minutes\n",
            "\n",
            "**Goals**:\n",
            "- Understand Expected Free Energy (EFE) formula\n",
            "- See how beliefs are probability distributions\n",
            "- Calculate EFE for all three skills\n",
            "- Visualize decision boundaries\n",
            "\n",
            "**Now we formalize the intuition mathematically!**"
        ]
    })

    # 2.1 Beliefs as Probability Distributions
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.1 Beliefs as Probability Distributions"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 📊 From Intuition to Mathematics\n",
            "\n",
            "Previously, we talked about \"belief\" as a single number (0-1).\n",
            "\n",
            "**More formally**: A belief is a **probability distribution** over possible states.\n",
            "\n",
            "**In our case**:\n",
            "- State space: {Unlocked, Locked}\n",
            "- Belief: P(Locked) = b, P(Unlocked) = 1-b\n",
            "\n",
            "Let's visualize how beliefs evolve:\n",
            "\"\"\"))\n",
            "\n",
            "# Interactive belief visualization\n",
            "fig, ax = plt.subplots(figsize=(12, 5))\n",
            "\n",
            "belief_param = widgets.FloatSlider(\n",
            "    value=0.5, min=0.01, max=0.99, step=0.01,\n",
            "    description='Belief (locked):',\n",
            "    style={'description_width': 'initial'},\n",
            "    continuous_update=True,\n",
            "    readout_format='.0%'\n",
            ")\n",
            "\n",
            "output_belief_dist = widgets.Output()\n",
            "\n",
            "def plot_belief(change):\n",
            "    belief_locked = belief_param.value\n",
            "    with output_belief_dist:\n",
            "        clear_output(wait=True)\n",
            "        \n",
            "        states = ['Unlocked', 'Locked']\n",
            "        probabilities = [1 - belief_locked, belief_locked]\n",
            "        colors_viz = ['#2ecc71', '#e74c3c']\n",
            "        \n",
            "        fig, ax = plt.subplots(figsize=(10, 5))\n",
            "        bars = ax.bar(states, probabilities, color=colors_viz, alpha=0.7, \n",
            "                     edgecolor='black', linewidth=2)\n",
            "        ax.set_ylabel('Probability', fontsize=12)\n",
            "        ax.set_title(f'Agent Belief Distribution (Locked={belief_locked:.1%})', \n",
            "                    fontsize=14, fontweight='bold')\n",
            "        ax.set_ylim(0, 1.1)\n",
            "        ax.grid(axis='y', alpha=0.3)\n",
            "        \n",
            "        # Add probability labels\n",
            "        for bar, prob in zip(bars, probabilities):\n",
            "            height = bar.get_height()\n",
            "            ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,\n",
            "                   f'{prob:.1%}', ha='center', va='bottom', \n",
            "                   fontsize=14, fontweight='bold')\n",
            "        \n",
            "        # Uncertainty measure\n",
            "        entropy = -(belief_locked * np.log2(belief_locked + 1e-10) + \n",
            "                   (1-belief_locked) * np.log2(1-belief_locked + 1e-10))\n",
            "        \n",
            "        ax.text(0.5, 0.95, f'Uncertainty (entropy): {entropy:.3f} bits',\n",
            "               ha='center', va='top', transform=ax.transAxes,\n",
            "               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),\n",
            "               fontsize=11)\n",
            "        \n",
            "        plt.tight_layout()\n",
            "        plt.show()\n",
            "        \n",
            "        # Interpretation\n",
            "        if entropy > 0.9:\n",
            "            print(\"\\n⚠ HIGH UNCERTAINTY - You really don't know!\")\n",
            "        elif entropy < 0.5:\n",
            "            print(\"\\n✓ LOW UNCERTAINTY - You're fairly confident!\")\n",
            "        else:\n",
            "            print(\"\\n~ MODERATE UNCERTAINTY\")\n",
            "\n",
            "belief_param.observe(plot_belief, names='value')\n",
            "display(belief_param, output_belief_dist)\n",
            "plot_belief(None)  # Initial display"
        ]
    })

    # 2.2 Expected Free Energy Formula
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.2 Expected Free Energy (EFE) Formula"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(r\"\"\"\n",
            "### 🧮 The Core Formula\n",
            "\n",
            "Active inference agents choose actions by minimizing **Expected Free Energy** (G):\n",
            "\n",
            "$$G(\\pi) = \\underbrace{\\mathbb{E}[\\text{cost}]}_{\\text{Resource penalty}} - \\underbrace{\\mathbb{E}[\\text{goal}]}_{\\text{Pragmatic value}} - \\underbrace{\\mathbb{E}[\\text{info}]}_{\\text{Epistemic value}}$$\n",
            "\n",
            "### Breaking It Down:\n",
            "\n",
            "**1. Expected Cost** (Resources consumed)\n",
            "- Time, energy, risk\n",
            "- **Higher cost = worse** → Add to G (penalty)\n",
            "- Example: window costs 2.0 (risky jump)\n",
            "\n",
            "**2. Expected Goal** (How much does this help achieve objective?)\n",
            "- Probability of escaping\n",
            "- **Higher goal = better** → Subtract from G (reward)\n",
            "- Example: try_door gives goal=1.0 IF door unlocked\n",
            "- So expected_goal = 1.0 × P(Unlocked)\n",
            "\n",
            "**3. Expected Info** (How much uncertainty does this reduce?)\n",
            "- Information gain (reduction in entropy)\n",
            "- **Higher info = better** → Subtract from G (reward)\n",
            "- Example: peek_door gives info=1.0 (learns state)\n",
            "\n",
            "### The Rule:\n",
            "**Choose skill with LOWEST G** (best trade-off)\n",
            "\n",
            "---\n",
            "\n",
            "💡 **Key Insight**: This formula naturally balances:\n",
            "- Exploration (info gain)\n",
            "- Exploitation (goal achievement)  \n",
            "- Efficiency (minimizing cost)\n",
            "\n",
            "No separate \"epsilon-greedy\" or \"UCB\" needed!\n",
            "\"\"\"))"
        ]
    })

    # 2.3 Interactive EFE Calculator
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.3 Interactive EFE Calculator"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 🧪 Play with the Formula\n",
            "\n",
            "Adjust the parameters and see how EFE changes:\n",
            "\"\"\"))\n",
            "\n",
            "cost_slider = widgets.FloatSlider(\n",
            "    value=1.0, min=0, max=3, step=0.1, \n",
            "    description='Cost:', style={'description_width': 'initial'})\n",
            "goal_slider = widgets.FloatSlider(\n",
            "    value=0.5, min=0, max=1, step=0.05, \n",
            "    description='Goal Value:', style={'description_width': 'initial'})\n",
            "info_slider = widgets.FloatSlider(\n",
            "    value=0.5, min=0, max=1, step=0.05, \n",
            "    description='Info Gain:', style={'description_width': 'initial'})\n",
            "\n",
            "output_efe = widgets.Output()\n",
            "\n",
            "def calculate_efe(change):\n",
            "    cost = cost_slider.value\n",
            "    goal = goal_slider.value\n",
            "    info = info_slider.value\n",
            "    \n",
            "    with output_efe:\n",
            "        clear_output(wait=True)\n",
            "        \n",
            "        efe = cost - goal - info\n",
            "        \n",
            "        print(\"=\"*60)\n",
            "        print(\"Expected Free Energy Calculation:\")\n",
            "        print(\"=\"*60)\n",
            "        print(f\"  Cost (penalty):    +{cost:.2f}\")\n",
            "        print(f\"  Goal (reward):     -{goal:.2f}\")\n",
            "        print(f\"  Info (reward):     -{info:.2f}\")\n",
            "        print(\"-\" * 60)\n",
            "        print(f\"  EFE = {cost:.2f} - {goal:.2f} - {info:.2f} = {efe:.2f}\")\n",
            "        print(\"=\"*60)\n",
            "        \n",
            "        if efe < 0:\n",
            "            print(\"\\n✓✓ EXCELLENT skill (negative EFE = high net benefit!)\")\n",
            "        elif efe < 0.5:\n",
            "            print(\"\\n✓ GOOD skill (low EFE = decent trade-off)\")\n",
            "        elif efe < 1.5:\n",
            "            print(\"\\n~ OKAY skill (moderate EFE)\")\n",
            "        else:\n",
            "            print(\"\\n✗ POOR skill (high EFE = bad trade-off)\")\n",
            "        \n",
            "        print(\"\\n💡 Remember: LOWER EFE = BETTER choice!\")\n",
            "\n",
            "# Observe all sliders\n",
            "cost_slider.observe(calculate_efe, names='value')\n",
            "goal_slider.observe(calculate_efe, names='value')\n",
            "info_slider.observe(calculate_efe, names='value')\n",
            "\n",
            "display(widgets.VBox([cost_slider, goal_slider, info_slider]))\n",
            "display(output_efe)\n",
            "calculate_efe(None)  # Initial calculation"
        ]
    })

    # 2.4 Code Walkthrough
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.4 Code Implementation: score_skill()"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 💻 How Skills Are Scored in Code\n",
            "\n",
            "Let's look at the actual implementation:\n",
            "\"\"\"))\n",
            "\n",
            "# Show the code\n",
            "print(\"\"\"\n",
            "def score_skill(skill: Dict, belief_door_locked: float) -> float:\n",
            "    '''\n",
            "    Calculate Expected Free Energy for a skill.\n",
            "    \n",
            "    Args:\n",
            "        skill: Dict with 'cost', 'goal_info', 'info_gain'\n",
            "        belief_door_locked: Current belief that door is locked (0-1)\n",
            "    \n",
            "    Returns:\n",
            "        Expected Free Energy (lower is better)\n",
            "    '''\n",
            "    # 1. Cost (always a penalty)\n",
            "    cost = skill['cost']\n",
            "    \n",
            "    # 2. Expected goal (belief-weighted)\n",
            "    # If door is probably unlocked, trying door has high expected goal\n",
            "    # If door is probably locked, trying door has low expected goal\n",
            "    belief_unlocked = 1 - belief_door_locked\n",
            "    expected_goal = skill['goal_info'] * belief_unlocked\n",
            "    \n",
            "    # 3. Expected info (fixed per skill)\n",
            "    # Sensing skills provide info, action skills don't\n",
            "    expected_info = skill['info_gain']\n",
            "    \n",
            "    # 4. Calculate EFE\n",
            "    efe = cost - expected_goal - expected_info\n",
            "    \n",
            "    return efe\n",
            "\"\"\")\n",
            "\n",
            "display(Markdown(\"\"\"\n",
            "### 🔍 Key Points:\n",
            "\n",
            "1. **Cost** is always added (penalty)\n",
            "2. **Goal** is belief-weighted:\n",
            "   - If door probably unlocked → high expected_goal for try_door\n",
            "   - If door probably locked → low expected_goal for try_door\n",
            "3. **Info** is fixed per skill:\n",
            "   - peek_door always gives info=1.0\n",
            "   - try_door never gives info (info=0.0)\n",
            "4. **Lower EFE wins** - agent picks skill with minimum G\n",
            "\n",
            "This belief-weighting is why the optimal choice changes based on your belief!\n",
            "\"\"\"))"
        ]
    })

    return cells


def create_part3_cells():
    """Part 3: Scoring Skills Across Belief Space"""
    cells = []

    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.5 Interactive: Score All Three Skills"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 🎯 Apply EFE Formula to Our Skills\n",
            "\n",
            "Let's score all three skills (peek, try, window) across different belief values:\n",
            "\"\"\"))\n",
            "\n",
            "# Get skills data\n",
            "skills_for_scoring = [\n",
            "    {'name': 'peek_door', 'cost': 1.0, 'goal_info': 0.0, 'info_gain': 1.0},\n",
            "    {'name': 'try_door', 'cost': 1.5, 'goal_info': 1.0, 'info_gain': 0.0},\n",
            "    {'name': 'go_window', 'cost': 2.0, 'goal_info': 1.0, 'info_gain': 0.0}\n",
            "]\n",
            "\n",
            "# Interactive belief slider\n",
            "belief_slider_scoring = widgets.FloatSlider(\n",
            "    value=0.5, min=0, max=1, step=0.05,\n",
            "    description='Belief (locked):',\n",
            "    style={'description_width': 'initial'},\n",
            "    continuous_update=True,\n",
            "    readout_format='.0%'\n",
            ")\n",
            "\n",
            "output_scores = widgets.Output()\n",
            "\n",
            "def score_all_skills(change):\n",
            "    belief = belief_slider_scoring.value\n",
            "    with output_scores:\n",
            "        clear_output(wait=True)\n",
            "        \n",
            "        print(\"=\"*70)\n",
            "        print(f\"Belief: {belief:.0%} LOCKED, {1-belief:.0%} UNLOCKED\")\n",
            "        print(\"=\"*70)\n",
            "        print(\"\\nSkill Scoring:\")\n",
            "        print(\"-\"*70)\n",
            "        \n",
            "        scores = {}\n",
            "        for skill in skills_for_scoring:\n",
            "            efe = score_skill(skill, belief)\n",
            "            scores[skill['name']] = efe\n",
            "            \n",
            "            expected_goal = skill['goal_info'] * (1 - belief)\n",
            "            \n",
            "            print(f\"\\n{skill['name']:15s}:\")\n",
            "            print(f\"  Cost = {skill['cost']:.2f}\")\n",
            "            print(f\"  Goal = {skill['goal_info']:.2f} × {1-belief:.2f} = {expected_goal:.2f}\")\n",
            "            print(f\"  Info = {skill['info_gain']:.2f}\")\n",
            "            print(f\"  → EFE = {efe:.2f}\")\n",
            "        \n",
            "        print(\"-\"*70)\n",
            "        best_skill = min(scores, key=scores.get)\n",
            "        print(f\"\\n🎯 BEST CHOICE: {best_skill} (EFE = {scores[best_skill]:.2f})\")\n",
            "        print(\"=\"*70)\n",
            "\n",
            "belief_slider_scoring.observe(score_all_skills, names='value')\n",
            "display(belief_slider_scoring, output_scores)\n",
            "score_all_skills(None)  # Initial"
        ]
    })

    # EFE curves visualization
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.6 Visualization: EFE Curves Across Belief Space"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 📈 Decision Boundaries\n",
            "\n",
            "Let's plot how EFE changes for each skill as beliefs change:\n",
            "\"\"\"))\n",
            "\n",
            "# Plot EFE curves\n",
            "beliefs = np.linspace(0, 1, 100)\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(14, 7))\n",
            "\n",
            "for skill in skills_for_scoring:\n",
            "    efes = []\n",
            "    for b in beliefs:\n",
            "        efe = score_skill(skill, b)\n",
            "        efes.append(efe)\n",
            "    \n",
            "    ax.plot(beliefs, efes, label=skill['name'], linewidth=3, alpha=0.8)\n",
            "\n",
            "ax.set_xlabel('Belief that door is LOCKED', fontsize=13, fontweight='bold')\n",
            "ax.set_ylabel('Expected Free Energy (lower = better)', fontsize=13, fontweight='bold')\n",
            "ax.set_title('Skill Selection Depends on Belief!', fontsize=16, fontweight='bold', pad=15)\n",
            "ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='EFE = 0')\n",
            "ax.grid(alpha=0.3)\n",
            "ax.legend(fontsize=12, loc='best')\n",
            "ax.invert_yaxis()  # Lower is better, so show best at top\n",
            "\n",
            "# Mark crossover points\n",
            "ax.axvline(x=0.5, color='red', linestyle=':', alpha=0.5, label='Decision boundary')\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "display(Markdown(\"\"\"\n",
            "### 🔍 What This Shows:\n",
            "\n",
            "**peek_door** (blue):\n",
            "- Constant EFE = 0.0 (cost=1, info=1, goal=0)\n",
            "- Always provides same value regardless of belief\n",
            "\n",
            "**try_door** (orange):\n",
            "- EFE increases as belief (locked) increases\n",
            "- When belief < ~0.5: try_door is best (probably unlocked)\n",
            "- When belief > ~0.5: peek_door is better (too uncertain to try)\n",
            "\n",
            "**go_window** (green):\n",
            "- Constant EFE = 1.0 (cost=2, goal=1, info=0)\n",
            "- Always worst option (expensive!)\n",
            "- Only use as last resort\n",
            "\n",
            "**Key Insight**: The **crossover points** show when optimal policy switches!\n",
            "\n",
            "This is Active Inference in action - balancing exploration and exploitation naturally!\n",
            "\"\"\"))"
        ]
    })

    # Checkpoint 2
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2.7 Checkpoint 2: Calculate EFE"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### ✅ Checkpoint 2: Test Your Understanding\n",
            "\n",
            "**Given**:\n",
            "- Skill: try_door\n",
            "- cost = 1.5\n",
            "- goal_info = 1.0\n",
            "- info_gain = 0.0\n",
            "- belief (locked) = 0.3\n",
            "\n",
            "**Calculate**: What is the EFE?\n",
            "\"\"\"))\n",
            "\n",
            "checkpoint2_answer = widgets.FloatText(\n",
            "    value=0.0,\n",
            "    description='Your EFE:',\n",
            "    style={'description_width': 'initial'}\n",
            ")\n",
            "\n",
            "check2_button = widgets.Button(\n",
            "    description=\"Check Answer\",\n",
            "    button_style='success'\n",
            ")\n",
            "\n",
            "check2_output = widgets.Output()\n",
            "\n",
            "def check_checkpoint2(b):\n",
            "    with check2_output:\n",
            "        clear_output()\n",
            "        \n",
            "        user_answer = checkpoint2_answer.value\n",
            "        \n",
            "        # Correct calculation\n",
            "        belief = 0.3\n",
            "        cost = 1.5\n",
            "        expected_goal = 1.0 * (1 - belief)  # 1.0 * 0.7 = 0.7\n",
            "        expected_info = 0.0\n",
            "        correct_efe = cost - expected_goal - expected_info  # 1.5 - 0.7 - 0 = 0.8\n",
            "        \n",
            "        if abs(user_answer - correct_efe) < 0.01:\n",
            "            print(\"✓ Correct!\\n\")\n",
            "            print(f\"EFE = {correct_efe:.2f}\")\n",
            "            print(\"\\nCalculation:\")\n",
            "            print(f\"  Cost = {cost:.2f}\")\n",
            "            print(f\"  Expected goal = {1.0:.2f} × {1-belief:.2f} = {expected_goal:.2f}\")\n",
            "            print(f\"  Expected info = {expected_info:.2f}\")\n",
            "            print(f\"  EFE = {cost:.2f} - {expected_goal:.2f} - {expected_info:.2f} = {correct_efe:.2f}\")\n",
            "        else:\n",
            "            print(f\"✗ Not quite. The correct EFE is {correct_efe:.2f}\\n\")\n",
            "            print(\"Hint: Remember the formula:\")\n",
            "            print(\"  EFE = cost - (goal × P(unlocked)) - info\")\n",
            "            print(f\"  EFE = {cost:.2f} - ({1.0:.2f} × {1-belief:.2f}) - {expected_info:.2f}\")\n",
            "            print(f\"  EFE = {cost:.2f} - {expected_goal:.2f} - {expected_info:.2f}\")\n",
            "            print(f\"  EFE = {correct_efe:.2f}\")\n",
            "\n",
            "check2_button.on_click(check_checkpoint2)\n",
            "display(checkpoint2_answer, check2_button, check2_output)"
        ]
    })

    # Part 2 Summary
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "### 🎯 Part 2 Summary\n",
            "\n",
            "**What we learned**:\n",
            "\n",
            "1. ✅ **Beliefs** = probability distributions over states\n",
            "2. ✅ **Expected Free Energy** = cost - goal - info\n",
            "3. ✅ **Lower EFE = better** choice\n",
            "4. ✅ **Goal is belief-weighted** - that's why beliefs matter!\n",
            "5. ✅ **Decision boundaries** emerge from EFE curves\n",
            "6. ✅ **Active inference naturally balances** exploration and exploitation\n",
            "\n",
            "**Next**: How do agents learn and adapt? → **Procedural Memory & Episodes!**"
        ]
    })

    return cells


def append_cells_to_notebook(notebook_path, new_cells):
    """Append cells to existing notebook"""
    with open(notebook_path, 'r') as f:
        nb = json.load(f)

    nb['cells'].extend(new_cells)

    with open(notebook_path, 'w') as f:
        json.dump(nb, f, indent=1)

    print(f"✓ Added {len(new_cells)} cells to notebook")


if __name__ == "__main__":
    notebook_path = "/home/juancho/macgyver_mud/MacGyverMUD_DeepDive.ipynb"

    print("Building Part 2 cells...")
    part2_cells = create_part2_cells()

    print("Building Part 3 cells (scoring)...")
    part3_cells = create_part3_cells()

    print(f"\\nTotal new cells: {len(part2_cells) + len(part3_cells)}")

    print("\\nAppending to notebook...")
    all_new_cells = part2_cells + part3_cells
    append_cells_to_notebook(notebook_path, all_new_cells)

    print("\\n✓ Notebook extended successfully!")
    print(f"  Added Parts 2-3 (Active Inference)")
    print(f"  Total new cells: {len(all_new_cells)}")
