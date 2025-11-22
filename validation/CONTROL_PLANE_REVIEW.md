The Control Plane: Hysteresis & Memory Veto
A Deep Dive into Hybrid Geometric Control
1. Introduction: The Need for a Control Plane
In our initial implementation of the Geometric Controller, we mapped Entropy directly to Strategy: $$ Strategy = f(Entropy) $$

High Entropy $\rightarrow$ Robustness (Panic Mode)
Low Entropy $\rightarrow$ Efficiency (Flow Mode)
The Failure: This direct mapping proved naive. It assumed that:

Entropy is stable (it's not; it fluctuates).
Entropy is accurate (it's not; the agent can be delusional).
To fix this, we introduced a Control Plane—a layer of meta-logic that sits between the raw signal (Entropy) and the decision (Strategy). This Control Plane implements two critical mechanisms: Hysteresis and the Memory Veto.

2. Hysteresis: The Stability Mechanism
A. The Context: "The Jitterbug"
The Problem: When the agent's entropy hovered near the switching threshold (e.g., $0.4$), tiny fluctuations caused the agent to flip-flop between "Panic" and "Flow" every step. The Effect: The agent became paralyzed, spending all its energy switching strategies rather than acting. This is a classic control theory failure known as Oscillation.

B. The Mechanics: Dual Thresholds
We replaced the single threshold ($T$) with two:

$T_{high}$ (0.45): The "Panic" Threshold.
$T_{low}$ (0.35): The "Flow" Threshold.
The Logic:

Enter Panic: Only if $H > T_{high}$.
Exit Panic: Only if $H < T_{low}$.
The Dead Zone: If $0.35 < H < 0.45$, do nothing. Keep the previous state.
This creates a "buffer" that absorbs noise. The agent must be significantly confident to leave Panic Mode, and significantly confused to enter it.

C. The Meta-Monitor (Derivative Control)
We added a second layer of stability: Rate Monitoring.

Mechanism: We track the switch_rate (number of mode switches in the last $N$ steps).
Rule: If switches > 2 in window=5:
Diagnosis: "I am oscillating. I don't know what I want."
Action: Force Panic Mode.
Innovation: This is a form of derivative control. We are reacting not just to the state (Entropy), but to the instability of the state.
3. The Memory Veto: The Truth Mechanism
A. The Context: "The Mimic"
The Problem: The agent encountered a trap that looked safe.

Belief: "This door is safe." ($P(Safe) \approx 0.9$)
Entropy: Low ($H \approx 0.1$).
Controller: "Low Entropy $\rightarrow$ Flow Mode (Efficiency)."
Result: The agent chose a Specialist skill (efficient) and died.
The Failure: The Geometric Controller is Garbage In, Garbage Out. If the agent's belief is wrong (Delusion), the controller amplifies the error by authorizing risky efficiency.

B. The Mechanics: The Epistemic Check
We introduced a check against Ground Truth (Procedural Memory) before authorizing Efficiency.

The Logic:

Trigger: Controller proposes "Flow Mode" (Efficiency).
Query: "Check Procedural Memory for this context."
Evaluate: Calculate Historical Success Rate ($R_{success}$).
The Veto: $$ \text{If } R_{success} < 0.5 \implies \text{VETO Flow Mode} \rightarrow \text{Force Panic Mode} $$
C. The Innovation: Epistemic Vigilance
This mechanism acknowledges that Internal Confidence $\neq$ External Truth.

Entropy measures Internal Consistency ("Do I think I know?").
Memory measures Empirical Reality ("Did I actually succeed last time?").
By allowing Memory to Veto Entropy, we created a system that is Humble. It trusts its experience more than its feelings.

4. Synthesis: The Hybrid Architecture
The final Control Plane fuses these elements into a robust decision loop:

Input: Current Entropy ($H$).
Stability Check (Hysteresis):
Is $H$ in the Dead Zone? $\rightarrow$ Hold State.
Is $H$ extreme? $\rightarrow$ Propose Switch.
Meta-Check (Oscillation):
Am I switching too fast? $\rightarrow$ Force Panic.
Truth Check (Memory Veto):
(If Flow Proposed): Does history agree?
No? $\rightarrow$ Force Panic.
Output: Target Strategy ($k$).
5. Conclusion
The addition of Hysteresis and Memory Veto transformed the Geometric Controller from a naive signal processor into a Resilient Cognitive Architecture.

Hysteresis gives it Patience (resistance to noise).
Memory Veto gives it Wisdom (resistance to delusion).
This is the difference between a "Smart Algorithm" and an "Intelligent Agent."