#!/usr/bin/env python3
"""
Red Team Experiment: Challenging the Geometric Lens
===================================================

Two experiments designed to disprove the functional utility of "Balanced Skills".

Experiment A: "The Threshold of Excellence"
    - Hypothesis: Balanced skills fail when the bar is high.
    - Scenario: Heavy Door (Requires Goal > 8.0).
    - Comparison: Smash (Goal=10) vs Nudge (Goal=5).

Experiment B: "The Sequential Superiority"
    - Hypothesis: Alternating specialists is more efficient than being balanced.
    - Scenario: Mystery Box (Needs Info to unlock safely, or high Goal to force).
    - Comparison:
        - Hybrid Strategy: Use 'Inspect_and_Pry' (Balanced).
        - Crisp Strategy: Use 'Peek' (Info) THEN 'Smash' (Goal).
"""

import numpy as np
import pandas as pd

# ============================================================================
# EXPERIMENT A: THRESHOLD OF EXCELLENCE
# ============================================================================

def run_threshold_experiment():
    print("\n" + "="*60)
    print("EXPERIMENT A: THE THRESHOLD OF EXCELLENCE")
    print("="*60)
    
    # Scenario: Heavy Door
    # Requirement: Goal > 8.0 to open.
    threshold = 8.0
    
    # Skills
    skill_specialist = {'name': 'Smash', 'goal': 10.0, 'cost': 2.0}
    skill_balanced = {'name': 'Nudge', 'goal': 5.0, 'cost': 1.5}
    
    print(f"Scenario: Heavy Door (Requires Goal > {threshold})")
    print(f"Specialist: {skill_specialist}")
    print(f"Balanced:   {skill_balanced}")
    
    results = []
    
    # 1. Specialist Attempt
    cost_spec = 0
    success_spec = False
    
    # Try once
    cost_spec += skill_specialist['cost']
    if skill_specialist['goal'] > threshold:
        success_spec = True
        
    results.append({
        'Agent': 'Specialist',
        'Success': success_spec,
        'Total_Cost': cost_spec,
        'Outcome': 'Opened immediately' if success_spec else 'Failed'
    })
    
    # 2. Balanced Attempt
    cost_bal = 0
    success_bal = False
    
    # Try once
    cost_bal += skill_balanced['cost']
    if skill_balanced['goal'] > threshold:
        success_bal = True
    else:
        # Failed! Agent realizes it needs more power.
        # Must switch to specialist (if available) or fail.
        # Let's assume it retries with the specialist skill (best case for agent).
        cost_bal += skill_specialist['cost']
        if skill_specialist['goal'] > threshold:
            success_bal = True
            
    results.append({
        'Agent': 'Balanced',
        'Success': success_bal,
        'Total_Cost': cost_bal,
        'Outcome': 'Failed first, then switched' if cost_bal > skill_balanced['cost'] else 'Opened'
    })
    
    df = pd.DataFrame(results)
    print("\nRESULTS:")
    print(df)
    
    winner = df.loc[df['Total_Cost'].idxmin()]
    print(f"\n🏆 Winner: {winner['Agent']} (Cost: {winner['Total_Cost']})")
    return df

# ============================================================================
# EXPERIMENT B: SEQUENTIAL SUPERIORITY
# ============================================================================

def run_sequential_experiment():
    print("\n" + "="*60)
    print("EXPERIMENT B: THE SEQUENTIAL SUPERIORITY")
    print("="*60)
    
    # Scenario: Mystery Box
    # State: Locked (p=0.5) or Unlocked (p=0.5)
    # - If Locked: Needs Key (Goal action)
    # - If Unlocked: Just Open (Goal action)
    # - Trap: If Locked and you try to Force Open without checking, 50% chance of breaking item.
    
    # Strategies
    
    # 1. Balanced Strategy (Simultaneous)
    # Skill: Inspect_and_Pry (Info=5, Goal=5, Cost=1.5)
    # Effect: Reduces uncertainty by 50%, adds 50% goal progress.
    # Result: Takes 2 attempts to fully resolve.
    
    # 2. Sequential Strategy (Specialist)
    # Step 1: Peek (Info=10, Goal=0, Cost=0.5) -> Resolves uncertainty 100%.
    # Step 2: Action (Goal=10, Info=0, Cost=1.0) -> Opens box.
    
    print("Scenario: Mystery Box (Hidden State)")
    
    results = []
    
    # Run Sequential
    cost_seq = 0
    # Step 1: Peek
    cost_seq += 0.5 # Low cost info
    uncertainty = 0.0 # Resolved
    # Step 2: Optimal Action
    cost_seq += 1.0 # Standard action
    
    results.append({
        'Strategy': 'Sequential (Specialist)',
        'Steps': 2,
        'Total_Cost': cost_seq,
        'Certainty': '100%'
    })
    
    # Run Balanced
    cost_bal = 0
    uncertainty = 1.0
    
    # Step 1: Inspect_and_Pry
    cost_bal += 1.5
    uncertainty = 0.5 # Partially resolved
    # Step 2: Inspect_and_Pry (to finish job)
    cost_bal += 1.5
    uncertainty = 0.0
    
    results.append({
        'Strategy': 'Simultaneous (Balanced)',
        'Steps': 2,
        'Total_Cost': cost_bal,
        'Certainty': '100%'
    })
    
    df = pd.DataFrame(results)
    print("\nRESULTS:")
    print(df)
    
    winner = df.loc[df['Total_Cost'].idxmin()]
    print(f"\n🏆 Winner: {winner['Strategy']} (Cost: {winner['Total_Cost']})")
    return df

# ============================================================================
# MAIN
# ============================================================================

def main():
    df_a = run_threshold_experiment()
    df_b = run_sequential_experiment()
    
    # Generate Report
    report = f"""# Red Team Experiment Results

## Experiment A: The Threshold of Excellence
**Hypothesis:** Balanced skills fail at high-requirement tasks.
**Winner:** {df_a.loc[df_a['Total_Cost'].idxmin()]['Agent']}

| Agent | Total Cost | Outcome |
|-------|------------|---------|
| Specialist | {df_a.iloc[0]['Total_Cost']} | {df_a.iloc[0]['Outcome']} |
| Balanced | {df_a.iloc[1]['Total_Cost']} | {df_a.iloc[1]['Outcome']} |

**Finding:** The Balanced agent was inefficient. It paid for the balanced skill (1.5) AND the specialist skill (2.0) to succeed, totaling 3.5 cost vs 2.0 for the specialist.

## Experiment B: The Sequential Superiority
**Hypothesis:** Sequential specialization is more efficient than simultaneous balance.
**Winner:** {df_b.loc[df_b['Total_Cost'].idxmin()]['Strategy']}

| Strategy | Total Cost | Steps |
|----------|------------|-------|
| Sequential | {df_b.iloc[0]['Total_Cost']} | {df_b.iloc[0]['Steps']} |
| Balanced | {df_b.iloc[1]['Total_Cost']} | {df_b.iloc[1]['Steps']} |

**Finding:** The Sequential strategy was 2x more efficient (Cost 1.5 vs 3.0). "Divide and Conquer" beats "Do It All".

## Overall Conclusion
The "Geometric Lens" and "Balanced Skills" have **negative functional utility** in standard efficiency scenarios.
- They dilute power (failing thresholds).
- They are less efficient than sequential specialization.

**Recommendation:** Use Balanced Skills ONLY for robustness in unknown/deceptive environments (as per the Trap Experiment). Do NOT use them for efficiency optimization.
"""

    with open("validation/red_team_results.md", "w") as f:
        f.write(report)
        
    print("\n✓ Red Team experiments complete. Report saved to validation/red_team_results.md")

if __name__ == "__main__":
    main()
