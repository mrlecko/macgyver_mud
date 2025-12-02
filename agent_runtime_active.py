"""
Active Inference Agent Runtime (parallel path)

Implements a principled Active Inference control loop with:
- Generative model (A/B/C/D)
- Bayesian belief updates
- Policy evaluation via Expected Free Energy (risk + ambiguity - epistemic value)

This sits alongside the heuristic agent_runtime.AgentRuntime and can be
selected via configuration without affecting the existing path.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Sequence, Tuple, Any

import numpy as np
from neo4j import Session

import config
from graph_model import create_episode, log_step, mark_episode_complete, get_skills, get_agent
import json
from critical_state import CriticalStateMonitor, CriticalState, AgentState
from scoring import score_skill_with_memory
# Optional: silver gauge (disabled by default to avoid regressions)
try:
    from scoring_silver import build_silver_stamp
except Exception:
    build_silver_stamp = None
from memory.episodic_replay import EpisodicMemory

MODEL_SCHEMA_VERSION = "1.1"
EFE_PANIC_THRESHOLD = 5.0


def _softmax(x: np.ndarray) -> np.ndarray:
    """Stable softmax for preference vectors."""
    shifted = x - np.max(x)
    exp = np.exp(shifted)
    return exp / np.sum(exp)


def _entropy(probs: np.ndarray) -> float:
    """Shannon entropy (nats)."""
    probs = np.clip(probs, 1e-12, 1.0)
    return -float(np.sum(probs * np.log(probs)))


def _kl(p: np.ndarray, q: np.ndarray) -> float:
    """KL divergence D_KL(p || q)."""
    p = np.clip(p, 1e-12, 1.0)
    q = np.clip(q, 1e-12, 1.0)
    return float(np.sum(p * np.log(p / q)))


@dataclass
class GenerativeModel:
    """
    Discrete generative model components:
    - A: p(o | s, a)  (obs x state x action)
    - B: p(s' | s, a) (state' x state x action)
    - C: log preferences over observations
    - D: prior over states
    """

    states: List[str]
    observations: List[str]
    actions: List[str]
    A: np.ndarray  # shape (obs, state, action)
    B: np.ndarray  # shape (state, state, action)
    C: np.ndarray  # shape (obs,)
    D: np.ndarray  # shape (state,)
    action_costs: Optional[List[float]] = None
    dirichlet_A: Optional[np.ndarray] = None  # concentration parameters for A
    dirichlet_B: Optional[np.ndarray] = None  # concentration parameters for B
    action_kinds: Optional[List[str]] = None
    preference_counts: Optional[np.ndarray] = None  # counts for C learning

    def __post_init__(self) -> None:
        self._normalize()
        if self.action_costs is None:
            self.action_costs = [1.0 for _ in self.actions]
        elif len(self.action_costs) != len(self.actions):
            raise ValueError("action_costs length must match actions")
        if self.dirichlet_A is None:
            # Initialize with ones (uniform Dirichlet)
            self.dirichlet_A = np.ones_like(self.A)
        if self.dirichlet_B is None:
            self.dirichlet_B = np.ones_like(self.B)
        if self.preference_counts is None:
            self.preference_counts = np.ones_like(self.C)

    def _normalize(self) -> None:
        """Ensure A/B are normalized and derive preference distribution."""
        for action_idx in range(len(self.actions)):
            for state_idx in range(len(self.states)):
                a_slice = self.A[:, state_idx, action_idx]
                a_sum = np.sum(a_slice)
                if a_sum == 0:
                    raise ValueError("A slice sums to zero; check likelihoods.")
                self.A[:, state_idx, action_idx] = a_slice / a_sum

                b_slice = self.B[:, state_idx, action_idx]
                b_sum = np.sum(b_slice)
                if b_sum == 0:
                    raise ValueError("B slice sums to zero; check transitions.")
                self.B[:, state_idx, action_idx] = b_slice / b_sum

        d_sum = np.sum(self.D)
        if d_sum == 0:
            raise ValueError("D prior sums to zero; cannot normalize.")
        self.D = self.D / d_sum

        self.preference_dist = _softmax(self.C)

    def validate(self) -> None:
        """Validate normalization invariants."""
        for action_idx in range(len(self.actions)):
            for state_idx in range(len(self.states)):
                if not np.isclose(np.sum(self.A[:, state_idx, action_idx]), 1.0):
                    raise ValueError("A is not normalized")
                if not np.isclose(np.sum(self.B[:, state_idx, action_idx]), 1.0):
                    raise ValueError("B is not normalized")
        if not np.isclose(np.sum(self.preference_dist), 1.0):
            raise ValueError("Preferences are not normalized")
        if not np.isclose(np.sum(self.D), 1.0):
            raise ValueError("D prior is not normalized")


def build_door_model_defaults() -> GenerativeModel:
    """
    Default 2-state door model used in tests and quickstarts.

    States: locked, unlocked
    Observations: open_success, open_fail
    Actions:
        - sense: pure observation, perfectly disambiguates the door
        - force: attempt to open; success depends on true state
    """
    states = ["locked", "unlocked"]
    observations = ["open_success", "open_fail"]
    actions = ["sense", "force"]

    A = np.zeros((len(observations), len(states), len(actions)))
    # sense action: perfect observation of door state
    A[observations.index("open_fail"), states.index("locked"), actions.index("sense")] = 1.0
    A[observations.index("open_success"), states.index("unlocked"), actions.index("sense")] = 1.0
    # force action: noisy outcome depending on state
    A[observations.index("open_success"), states.index("locked"), actions.index("force")] = 0.2
    A[observations.index("open_fail"), states.index("locked"), actions.index("force")] = 0.8
    A[observations.index("open_success"), states.index("unlocked"), actions.index("force")] = 0.9
    A[observations.index("open_fail"), states.index("unlocked"), actions.index("force")] = 0.1

    B = np.zeros((len(states), len(states), len(actions)))
    for action in actions:
        # Door state does not change in this toy model
        B[states.index("locked"), states.index("locked"), actions.index(action)] = 1.0
        B[states.index("unlocked"), states.index("unlocked"), actions.index(action)] = 1.0

    # Preferences: strong desire for successful opening
    C = np.array([0.0, -4.0])  # log preferences: success >> failure
    D = np.array([0.5, 0.5])   # uniform prior

    return GenerativeModel(
        states=states,
        observations=observations,
        actions=actions,
        A=A,
        B=B,
        C=C,
        D=D,
        action_costs=[0.5, 1.0],
    )


class ActiveInferenceRuntime:
    """
    Minimal Active Inference runtime with Expected Free Energy policy evaluation.

    This class does not assume a specific environment; callers provide observations.
    If a Neo4j session is passed, decisions and outcomes are logged for traceability.
    """

    def __init__(
        self,
        model: GenerativeModel,
        temperature: float = 1.0,
        session: Optional[Session] = None,
        stochastic: bool = False,
        skill_priors: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.session = session
        self.eps = 1e-12
        self.action_costs = np.array(model.action_costs or [1.0 for _ in model.actions], dtype=float)
        self.cost_weight = 3.0  # scales action cost into EFE (penalize costly actions)
        self.info_weight = 2.0  # scales epistemic value
        self.sense_bonus_weight = 1.0  # encourages sensing under uncertainty
        self.stochastic = stochastic  # if True, sample observations instead of MAP
        self.trace: List[Dict[str, Any]] = []
        self.escaped: bool = False
        self.agent_id: Optional[str] = None
        self.monitor = CriticalStateMonitor()
        self.current_critical_state = CriticalState.FLOW
        self.episodic_memory = EpisodicMemory(session) if session is not None else None
        if self.session is not None:
            agent = get_agent(self.session, config.AGENT_NAME)
            if agent:
                self.agent_id = agent["id"]
        # Procedural memory priors (skill -> stats)
        self.skill_priors = skill_priors or {}

    def _action_idx(self, action: str) -> int:
        return self.model.actions.index(action)

    def _observation_idx(self, observation: str) -> int:
        return self.model.observations.index(observation)

    def _predict_state(self, prior_belief: np.ndarray, action: str) -> np.ndarray:
        """Predict next-state belief using B and current action."""
        a_idx = self._action_idx(action)
        # B has shape (state', state, action)
        predicted = self.model.B[:, :, a_idx] @ prior_belief
        predicted = predicted / np.sum(predicted)
        return predicted

    def _predict_observations(self, state_belief: np.ndarray, action: str) -> np.ndarray:
        """Predict observation distribution given state belief and action."""
        a_idx = self._action_idx(action)
        # For each observation, marginalize over states
        obs_dist = self.model.A[:, :, a_idx] @ state_belief
        obs_dist = obs_dist / np.sum(obs_dist)
        return obs_dist

    def update_belief(self, prior_belief: np.ndarray, action: str, observation: str) -> np.ndarray:
        """
        Bayesian update of beliefs given an action and received observation.

        p(s | o, a) ∝ p(o | s, a) * p(s' | s, a) * p(s)
        """
        predicted_state = self._predict_state(prior_belief, action)
        likelihood = self.model.A[self._observation_idx(observation), :, self._action_idx(action)]
        posterior = likelihood * predicted_state
        posterior = posterior / np.sum(posterior)
        return posterior

    def evaluate_policies(self, prior_belief: np.ndarray, depth: int = 2, max_nodes: Optional[int] = None) -> List[Tuple[Tuple[str, ...], float]]:
        """
        Enumerate fixed-length policies and score them via Expected Free Energy.

        Returns:
            List of (policy, efe) sorted by ascending efe.
        """
        policies = list(product(self.model.actions, repeat=depth))
        if max_nodes is not None and len(policies) > max_nodes:
            policies = policies[:max_nodes]
        scored: List[Tuple[Tuple[str, ...], float]] = []
        for policy in policies:
            efe = self._expected_free_energy(prior_belief, policy)
            scored.append((policy, efe))
        scored.sort(key=lambda x: x[1])
        return scored

    def evaluate_policies_beam(self, prior_belief: np.ndarray, depth: int, beam_width: int) -> List[Tuple[Tuple[str, ...], float]]:
        """
        Beam search approximation to reduce combinatorial growth.
        """
        beam: List[Tuple[Tuple[str, ...], float]] = [(tuple(), 0.0)]
        for _ in range(depth):
            candidates: List[Tuple[Tuple[str, ...], float]] = []
            for policy_prefix, _ in beam:
                for action in self.model.actions:
                    new_policy = policy_prefix + (action,)
                    efe_partial = self._expected_free_energy(prior_belief, new_policy)
                    candidates.append((new_policy, efe_partial))
            candidates.sort(key=lambda x: x[1])
            beam = candidates[:beam_width]
        return beam

    def select_action(self, prior_belief: np.ndarray, depth: int = 2, max_policies: Optional[int] = None, beam_width: Optional[int] = None, max_nodes: Optional[int] = None) -> Tuple[str, List[Tuple[Tuple[str, ...], float]]]:
        """
        Select an action using a softmax over negative EFE of candidate policies.
        Returns the first action of the sampled best policy plus the full ranking.
        """
        entropy_now = _entropy(prior_belief)
        if beam_width is not None:
            scored = self.evaluate_policies_beam(prior_belief, depth=depth, beam_width=beam_width)
        else:
            scored = self.evaluate_policies(prior_belief, depth=depth, max_nodes=max_nodes)
        if max_policies is not None and len(scored) > max_policies:
            scored = scored[:max_policies]
        efes = np.array([s[1] for s in scored])
        adjusted = []
        for (policy, efe) in scored:
            first_action = policy[0]
            # Silver gauge bias only under high entropy (confusion/deadlock) and if available
            if entropy_now > 0.6 and build_silver_stamp is not None:
                try:
                    a_idx = self._action_idx(first_action)
                    cost = float(self.action_costs[a_idx])
                    p_unlock = float(prior_belief[self.model.states.index("unlocked")]) if "unlocked" in self.model.states else float(np.max(prior_belief))
                    stamp = build_silver_stamp(first_action, cost, p_unlock)
                    k_explore = float(stamp.get("k_explore_balance", 0.0))
                    k_roi = float(stamp.get("k_eff_roi", 0.0))
                    # Gentle bias: tie-breaker under uncertainty (small effect)
                    efe *= (1.0 - 0.0 * k_explore)
                    efe -= 0.0 * k_roi
                except Exception:
                    pass
            # Procedural priors
            stats = self.skill_priors.get(first_action) if self.skill_priors else None
            if stats:
                success = stats.get("success_rate", 0.5)
                confidence = stats.get("confidence", 0.0)
                efe -= 4.0 * success * max(confidence, 0.0)
            adjusted.append((policy, efe))
        scored = sorted(adjusted, key=lambda x: x[1])
        efes = np.array([s[1] for s in scored])
        # Convert to action probabilities via softmax over -EFE (lower is better)
        policy_probs = _softmax(-efes / max(self.temperature, self.eps))
        best_policy_idx = int(np.argmax(policy_probs))
        best_policy = scored[best_policy_idx][0]
        return best_policy[0], scored

    def _expected_free_energy(self, prior_belief: np.ndarray, policy: Sequence[str]) -> float:
        """
        Compute Expected Free Energy for a fixed policy.

        G = risk + ambiguity - epistemic value
        """
        belief = prior_belief.copy()
        total_efe = 0.0

        for action in policy:
            predicted_state = self._predict_state(belief, action)
            obs_dist = self._predict_observations(predicted_state, action)
            likelihood = self.model.A[:, :, self._action_idx(action)]
            prior_entropy = _entropy(belief)
            max_entropy = np.log(len(self.model.states))
            cost_scale = prior_entropy / max_entropy if max_entropy > 0 else 1.0

            # Risk: divergence from preferred outcomes
            risk = -np.sum(obs_dist * np.log(self.model.preference_dist + self.eps))

            # Ambiguity: expected entropy of likelihood given predicted state
            state_entropies = np.array([_entropy(likelihood[:, s_idx]) for s_idx in range(len(self.model.states))])
            ambiguity = float(np.sum(predicted_state * state_entropies))

            # Epistemic value: expected information gain from observing outcomes
            info_gain = 0.0
            for obs_idx in range(len(self.model.observations)):
                likelihood_vec = likelihood[obs_idx, :]
                joint = likelihood_vec * predicted_state
                if joint.sum() == 0:
                    continue
                posterior = joint / np.sum(joint)
                info_gain += obs_dist[obs_idx] * _kl(posterior, predicted_state)

            cost_penalty = self.cost_weight * self.action_costs[self._action_idx(action)]
            if self.model.action_kinds:
                kind = self.model.action_kinds[self._action_idx(action)]
                if kind == "act":
                    cost_penalty *= 2.0
            sense_bonus = 0.0
            if self.model.action_kinds:
                kind = self.model.action_kinds[self._action_idx(action)]
                if kind == "sense":
                    sense_bonus = prior_entropy * self.sense_bonus_weight
            efe_step = risk + ambiguity - self.info_weight * info_gain + cost_penalty * cost_scale - sense_bonus
            total_efe += efe_step
            # Use predicted state as prior for the next step of this policy
            belief = predicted_state

        return float(total_efe)

    # --- Learning helpers ---

    def update_likelihoods(self, action: str, state_idx: int, obs_idx: int, learning_rate: float = 1.0) -> None:
        """Simple Dirichlet update for A given an observation."""
        a_idx = self._action_idx(action)
        self.model.dirichlet_A[obs_idx, state_idx, a_idx] += learning_rate
        # Normalize updated slice
        counts = self.model.dirichlet_A[:, state_idx, a_idx]
        self.model.A[:, state_idx, a_idx] = counts / np.sum(counts)

    def update_transitions(self, action: str, prev_state_idx: int, next_state_idx: int, learning_rate: float = 1.0) -> None:
        """Simple Dirichlet update for B given a state transition."""
        a_idx = self._action_idx(action)
        self.model.dirichlet_B[next_state_idx, prev_state_idx, a_idx] += learning_rate
        counts = self.model.dirichlet_B[:, prev_state_idx, a_idx]
        self.model.B[:, prev_state_idx, a_idx] = counts / np.sum(counts)

    def update_preferences(self, obs_idx: int, learning_rate: float = 1.0) -> None:
        """Update preference counts for observed outcome."""
        self.model.preference_counts[obs_idx] += learning_rate
        self.model.C = np.log(self.model.preference_counts + self.eps)

    def update_from_episode(self, transitions: List[Tuple[int, str, int, int]], learning_rate: float = 1.0) -> None:
        """
        Apply episodic updates to A/B using a list of transitions.
        Each transition: (state_idx, action_name, obs_idx, next_state_idx)
        """
        for state_idx, action_name, obs_idx, next_state_idx in transitions:
            self.update_likelihoods(action_name, state_idx, obs_idx, learning_rate)
            self.update_transitions(action_name, state_idx, next_state_idx, learning_rate)
            # Update preference counts toward observed outcomes
            if hasattr(self.model, "preference_counts") and self.model.preference_counts is not None:
                self.model.preference_counts[obs_idx] += learning_rate
        # Refresh normalized distributions after updates
        self.model._normalize()

    def update_critical_state(self, entropy_now: float, efe: float, steps_remaining: int) -> None:
        agent_state = AgentState(
            entropy=entropy_now,
            history=[],
            steps=steps_remaining,
            dist=1.0,
            rewards=[],
            error=0.0,
        )
        # Free-energy driven panic/escalation
        if efe > EFE_PANIC_THRESHOLD:
            self.current_critical_state = CriticalState.PANIC
        else:
            self.current_critical_state = self.monitor.evaluate(agent_state)

    # --- Episode Execution (toy locked-room environment) ---

    def _state_index(self, door_state: str) -> int:
        try:
            return self.model.states.index(door_state)
        except ValueError as exc:
            raise ValueError(f"Unknown door state '{door_state}', expected one of {self.model.states}") from exc

    def _sample_observation(self, state_idx: int, action_idx: int) -> Tuple[int, str]:
        """
        Sample an observation given true state and action.

        MAP by default for determinism; if self.stochastic, draw from distribution.
        """
        obs_dist = self.model.A[:, state_idx, action_idx]
        if self.stochastic:
            obs_idx = int(np.random.choice(len(obs_dist), p=obs_dist))
        else:
            obs_idx = int(np.argmax(obs_dist))
        return obs_idx, self.model.observations[obs_idx]

    def run_episode(
        self,
        door_state: str,
        max_steps: int = 5,
        initial_belief: Optional[np.ndarray] = None,
        policy_depth: int = 2,
        max_policies: Optional[int] = None,
        beam_width: Optional[int] = None,
    ) -> Optional[str]:
        """
        Run a toy locked-room episode using the generative model and a ground-truth state.

        Returns:
            Episode id (if logged), else None.
        """
        self.trace = []
        self.escaped = False

        belief = initial_belief if initial_belief is not None else self.model.D.copy()
        episode_id = self.start_episode(door_state=door_state) if self.session else None
        transitions: List[Tuple[int, str, int, int]] = []
        true_state_idx = self._state_index(door_state)

        for step in range(max_steps):
            action, scored = self.select_action(belief, depth=policy_depth, max_policies=max_policies, beam_width=beam_width)
            action_idx = self._action_idx(action)
            state_idx = true_state_idx

            obs_idx, observation = self._sample_observation(state_idx, action_idx)
            posterior = self.update_belief(belief, action, observation)
            efe = scored[0][1] if scored else 0.0
            # Learning updates
            self.update_likelihoods(action, state_idx, obs_idx, learning_rate=1.0)
            self.update_preferences(obs_idx, learning_rate=0.5)
            transitions.append((state_idx, action, obs_idx, state_idx))

            self.trace.append(
                {
                    "step_index": step,
                    "action": action,
                    "observation": observation,
                    "p_before": float(belief[self.model.states.index("unlocked")]),
                    "p_after": float(posterior[self.model.states.index("unlocked")]),
                    "efe": float(efe),
                }
            )
            if episode_id is not None:
                self.log_decision(episode_id, step, action, belief, posterior, efe, observation)

            belief = posterior
            # Critical-state update based on entropy and EFE
            entropy_now = _entropy(belief)
            self.update_critical_state(entropy_now, efe, max_steps - step)

            if ("escape" in observation) or ("opened" in observation) or ("open_success" in observation) or ("obs_door_opened" in observation):
                self.escaped = True
                break
            if observation == "obs_window_escape" or "window" in observation:
                self.escaped = True
                break

        if episode_id is not None:
            self.complete_episode(episode_id, escaped=self.escaped, total_steps=len(self.trace))
        # Automatic episodic replay: use trace to update A/B
        if transitions:
            self.update_from_episode(transitions, learning_rate=0.5)
        # Store episodic memory (optional) with raw trace
        if self.episodic_memory and episode_id is not None:
            import json
            path_data = {
                "path_id": f"path-{episode_id}",
                "path_data": json.dumps(self.trace),
                "state_type": "belief",
                "outcome": "success" if self.escaped else "failure",
                "steps": len(self.trace),
                "final_distance": 0 if self.escaped else len(self.trace),
            }
            self.episodic_memory.store_actual_path(str(episode_id), path_data)
        return episode_id

    def get_trace(self) -> List[Dict[str, Any]]:
        """Return the recorded step trace for this episode."""
        return self.trace

    # --- Neo4j logging helpers (optional) ---

    def start_episode(self, door_state: str, metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Create an episode node if session is available."""
        if self.session is None or self.agent_id is None:
            return None
        return create_episode(self.session, self.agent_id, door_state)

    def log_decision(
        self,
        episode_id: str,
        step: int,
        action: str,
        belief_before: np.ndarray,
        belief_after: np.ndarray,
        efe: float,
        observation: Optional[str] = None,
    ) -> None:
        """Log a single decision/observation step to Neo4j."""
        if self.session is None:
            return
        log_step(
            self.session,
            episode_id=episode_id,
            step_index=step,
            skill_name=action,
            observation=observation or "",
            p_before=float(belief_before[self.model.states.index("unlocked")]),
            p_after=float(belief_after[self.model.states.index("unlocked")]),
            silver_stamp=None,
        )

    def complete_episode(self, episode_id: str, escaped: bool, total_steps: int) -> None:
        """Mark an episode as complete in Neo4j."""
        if self.session is None:
            return
        mark_episode_complete(self.session, episode_id, escaped, total_steps)


# --- Model builders ---

def build_model_from_graph(session: Session) -> GenerativeModel:
    """
    Build a generative model from Neo4j skill/observation/state definitions.

    Uses heuristic likelihoods aligned to the locked-room scenario.
    Falls back to defaults if required entities are missing.
    """
    try:
        skills = get_skills(session, agent_id=None)  # agent_id unused in query
        preferred_names = {"peek_door", "try_door", "go_window"}
        filtered_skills = [s for s in skills if s["name"] in preferred_names]
        skills_to_use = filtered_skills if filtered_skills else skills
        actions = [s["name"] for s in skills_to_use]
        action_kinds = [s.get("kind", "") for s in skills_to_use]
        action_costs = [float(s.get("cost", 1.0)) if s.get("cost") is not None else 1.0 for s in skills_to_use]

        obs_records = session.run("MATCH (o:Observation) RETURN o.name AS name ORDER BY o.name")
        observations_raw = [r["name"] for r in obs_records]
        preferred_obs = {
            "obs_door_locked",
            "obs_door_unlocked",
            "obs_door_opened",
            "obs_door_stuck",
            "obs_window_escape",
        }
        observations = [o for o in observations_raw if o in preferred_obs] or observations_raw
        state_record = session.run(
            "MATCH (s:StateVar {name: $name}) RETURN s.domain AS domain",
            name=config.STATE_VAR_NAME,
        ).single()
        domain = state_record["domain"] if state_record and state_record.get("domain") else None
        states = domain if domain else ["locked", "unlocked"]
        # If domain missing, try to use persisted GenerativeModel states
        if domain is None:
            persisted = load_model_from_graph(session)
            if persisted:
                states = persisted.states
        if len(states) != 2:
            states = ["locked", "unlocked"]

        # Minimal sanity
        if not actions or not observations or len(states) != 2:
            return build_door_model_defaults()

        # Initialize likelihoods/transition with sensible defaults for this world
        A = np.zeros((len(observations), len(states), len(actions)))
        B = np.zeros((len(states), len(states), len(actions)))

        # Default transitions: state is static
        for a_idx in range(len(actions)):
            for s_idx in range(len(states)):
                B[s_idx, s_idx, a_idx] = 1.0

        # Helper maps
        def oi(name: str) -> int:
            return observations.index(name) if name in observations else 0

        def ai(name: str) -> Optional[int]:
            return actions.index(name) if name in actions else None

        # Likelihoods: sense vs act derived from graph semantics
        peek_idx = ai("peek_door")
        if peek_idx is not None and "obs_door_locked" in observations and "obs_door_unlocked" in observations:
            A[oi("obs_door_locked"), states.index("locked"), peek_idx] = 1.0
            A[oi("obs_door_unlocked"), states.index("unlocked"), peek_idx] = 1.0

        try_idx = ai("try_door")
        if try_idx is not None:
            # When unlocked, likely succeeds; when locked, likely fails
            A[oi("obs_door_opened"), states.index("unlocked"), try_idx] = 0.95
            A[oi("obs_door_stuck"), states.index("unlocked"), try_idx] = 0.05
            A[oi("obs_door_opened"), states.index("locked"), try_idx] = 0.05
            A[oi("obs_door_stuck"), states.index("locked"), try_idx] = 0.95

        window_idx = ai("go_window")
        if window_idx is not None and "obs_window_escape" in observations:
            # Always escape via window
            A[oi("obs_window_escape"), :, window_idx] = 1.0

        # If any slices missing, fall back to defaults
        if not np.any(A):
            return build_door_model_defaults()

        # Preferences: prefer escape observations, mildly prefer info
        prefs = {name: 0.0 for name in observations}
        if "obs_door_opened" in prefs:
            prefs["obs_door_opened"] = 0.5
        if "obs_window_escape" in prefs:
            prefs["obs_window_escape"] = 0.3
        if "obs_door_unlocked" in prefs:
            prefs["obs_door_unlocked"] = 0.2
        if "obs_door_locked" in prefs:
            prefs["obs_door_locked"] = 0.0
        if "obs_door_stuck" in prefs:
            prefs["obs_door_stuck"] = -0.2

        C = np.array([prefs[o] for o in observations], dtype=float)

        # Prior D from Belief, fallback to uniform
        belief_record = session.run("MATCH (b:Belief) RETURN b.p_unlocked AS p_unlocked LIMIT 1").single()
        p_unlocked = belief_record["p_unlocked"] if belief_record and belief_record.get("p_unlocked") is not None else 0.5
        p_unlocked = float(p_unlocked)
        D = np.array([1.0 - p_unlocked, p_unlocked], dtype=float)

        return GenerativeModel(
            states=states,
            observations=observations,
            actions=actions,
            A=A,
            B=B,
            C=C,
            D=D,
            action_costs=action_costs,
            action_kinds=action_kinds,
        )
    except Exception:
        # Fail-safe: keep the system running with a known-good default
        return build_door_model_defaults()


# --- Persistence helpers (optional) ---

def save_model_to_graph(session: Session, model: GenerativeModel) -> None:
    """
    Persist generative model parameters into Neo4j for transparency.
    Stored on a singleton node labeled :GenerativeModel with name=config.AGENT_NAME.
    """
    session.run(
        """
        MERGE (g:GenerativeModel {name: $name})
        SET g.states = $states,
            g.observations = $observations,
            g.actions = $actions,
            g.A = $A_json,
            g.B = $B_json,
            g.C = $C_json,
            g.D = $D_json,
            g.action_costs = $action_costs_json,
            g.dirichlet_A = $dirichlet_A_json,
            g.dirichlet_B = $dirichlet_B_json,
            g.version = $version
        """,
        name=config.AGENT_NAME,
        states=model.states,
        observations=model.observations,
        actions=model.actions,
        A_json=json.dumps(model.A.tolist()),
        B_json=json.dumps(model.B.tolist()),
        C_json=json.dumps(model.C.tolist()),
        D_json=json.dumps(model.D.tolist()),
        action_costs_json=json.dumps(list(model.action_costs or [])),
        dirichlet_A_json=json.dumps(model.dirichlet_A.tolist() if model.dirichlet_A is not None else []),
        dirichlet_B_json=json.dumps(model.dirichlet_B.tolist() if model.dirichlet_B is not None else []),
        version=MODEL_SCHEMA_VERSION,
    )


def load_model_from_graph(session: Session) -> Optional[GenerativeModel]:
    """Load a persisted generative model if present; otherwise return None."""
    record = session.run(
        """
        MATCH (g:GenerativeModel {name: $name})
        RETURN g.states AS states, g.observations AS observations,
               g.actions AS actions, g.A AS A, g.B AS B, g.C AS C, g.D AS D,
               g.action_costs AS action_costs, g.dirichlet_A AS dirichlet_A,
               g.dirichlet_B AS dirichlet_B, g.version AS version
        """,
        name=config.AGENT_NAME,
    ).single()
    if not record:
        return None
    if record.get("version") and record["version"] != MODEL_SCHEMA_VERSION:
        # Schema mismatch; caller can decide to rebuild instead
        return None
    states = record["states"]
    observations = record["observations"]
    actions = record["actions"]
    A = np.array(json.loads(record["A"]), dtype=float)
    B = np.array(json.loads(record["B"]), dtype=float)
    C = np.array(json.loads(record["C"]), dtype=float)
    D = np.array(json.loads(record["D"]), dtype=float)
    action_costs = json.loads(record["action_costs"]) if record.get("action_costs") else [1.0 for _ in actions]
    dirichlet_A = np.array(json.loads(record["dirichlet_A"]), dtype=float) if record.get("dirichlet_A") else np.ones_like(A)
    dirichlet_B = np.array(json.loads(record["dirichlet_B"]), dtype=float) if record.get("dirichlet_B") else np.ones_like(B)
    return GenerativeModel(states, observations, actions, A, B, C, D, action_costs=action_costs, dirichlet_A=dirichlet_A, dirichlet_B=dirichlet_B)
