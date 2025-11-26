"""
Agent Runtime - Core decision-making and episode execution
Implements simplified active inference control loop
"""
from typing import Dict, List, Tuple, Any
from neo4j import Session
import config
from graph_model import (
    get_agent, get_initial_belief, update_belief,
    get_skills, filter_skills_by_mode, create_episode, log_step, mark_episode_complete,
    get_skill_stats, update_skill_stats,
    get_meta_params, update_meta_params, get_recent_episodes_stats
)
from critical_state import CriticalStateMonitor, CriticalState, AgentState
from scoring import score_skill, score_skill_with_memory, compute_epistemic_value
from memory.credit_assignment import CreditAssignment

class AgentEscalationError(Exception):
    """Raised when the agent enters the ESCALATION state (Circuit Breaker)."""
    pass


class AgentRuntime:
    """
    Agent that maintains beliefs and selects actions using active inference.

    The agent:
    1. Maintains belief about door state (p_unlocked)
    2. Selects skills by scoring (goal value + info gain - cost)
    3. Simulates skill outcomes based on ground truth
    4. Updates beliefs based on observations
    5. Logs everything to Neo4j graph
    """

    def __init__(self, session: Session, door_state: str, initial_belief: float = None,
                 use_procedural_memory: bool = False,
                 adaptive_params: bool = False,
                 verbose_memory: bool = False,
                 skill_mode: str = "hybrid",
                 enable_episodic_memory: bool = None,
                 episodic_update_priors: bool = None,
                 episodic_learning_rate: float = None):
        """
        Initialize agent runtime.

        Args:
            session: Neo4j session
            door_state: Ground truth ("locked" or "unlocked")
            initial_belief: Starting belief (default from config)
            use_procedural_memory: Enable memory-influenced decisions
            adaptive_params: Enable meta-parameter adaptation
            verbose_memory: Show memory reasoning in decision logs
            skill_mode: Skill filtering mode: "crisp", "balanced", or "hybrid" (default)
            enable_episodic_memory: Enable episodic memory (overrides config if set)
            episodic_update_priors: Enable skill prior updates (overrides config if set)
            episodic_learning_rate: Learning rate for skill updates (overrides config if set)
        """
        self.session = session
        
        # Get agent from graph
        agent_data = get_agent(session, config.AGENT_NAME)
        if not agent_data:
            raise ValueError(f"Agent '{config.AGENT_NAME}' not found in graph")
        self.agent_id = agent_data["id"]
        
        self.door_state = door_state
        self.p_unlocked = initial_belief if initial_belief is not None else get_initial_belief(session, self.agent_id, config.STATE_VAR_NAME)
        
        # Store initial belief for resets
        self._initial_belief = self.p_unlocked
        
        self.use_procedural_memory = use_procedural_memory
        self.adaptive_params = adaptive_params
        self.verbose_memory = verbose_memory
        self.skill_mode = skill_mode
        
        # Resolve episodic memory flags
        if enable_episodic_memory is None:
            self.enable_episodic_memory = config.ENABLE_EPISODIC_MEMORY
        else:
            self.enable_episodic_memory = enable_episodic_memory
            
        if episodic_update_priors is None:
            self.episodic_update_priors = config.EPISODIC_UPDATE_SKILL_PRIORS
        else:
            self.episodic_update_priors = episodic_update_priors
            
        if episodic_learning_rate is None:
            self.episodic_learning_rate = config.EPISODIC_LEARNING_RATE
        else:
            self.episodic_learning_rate = episodic_learning_rate

        # Initialize tracking
        self.step_count = 0
        self.decision_log = []
        self.current_episode_id = None
        self.escaped = False
        
        # Meta-learning state
        self.episodes_completed = 0
        if self.adaptive_params:
            params = get_meta_params(session, self.agent_id)
            self.alpha = params.get("alpha", config.ALPHA)
            self.beta = params.get("beta", config.BETA)
            self.gamma = params.get("gamma", config.GAMMA)
            self.episodes_completed = params.get("episodes_completed", 0)
        else:
            self.alpha = config.ALPHA
            self.beta = config.BETA
            self.gamma = config.GAMMA

        # Initialize Credit Assignment
        self.credit_assignment = CreditAssignment(session, self.agent_id)
        
        # Initialize Critical State Monitor
        self.monitor = CriticalStateMonitor()
        self.geo_mode = "FLOW (Efficiency)" # Default mode
        
        # Initialize Lyapunov Monitor
        from control.lyapunov import StabilityMonitor
        self.lyapunov_monitor = StabilityMonitor() if config.ENABLE_LYAPUNOV_MONITORING else None
        
        # Episodic Memory (Offline Learning)
        self.episodic_memory = None
        if self.enable_episodic_memory:
            from memory.episodic_replay import EpisodicMemory
            from memory.counterfactual_generator import CounterfactualGenerator
            self.episodic_memory = EpisodicMemory(session)
            # Initialize generator for non-spatial support (labyrinth added later if available)
            self.counterfactual_generator = CounterfactualGenerator(session, None, self.agent_id)
            self.current_episode_path = []  # Track rooms visited in current episode
        else:
            self.episodic_memory = None
            self.counterfactual_generator = None
            self.current_episode_path = []
        
        # Initialize tracking attributes (used by critical state controller)
        self.steps_remaining = 100  # Default, will be set properly in reset()
        self.reward_history = []
        self.history = []
        self.last_prediction_error = 0.0
            
        # Generalized Credit Assignment (Online Safety)
        self.credit_assignment = CreditAssignment()
        
    def _get_belief_category(self, p_unlocked: float) -> str:
        """
        Categorize belief state for context matching.

        CRITICAL: Agent must NOT know ground truth (door_state).
        Uses only belief to infer likely state.

        Args:
            p_unlocked: Current belief probability

        Returns:
            Category string: "uncertain", "confident_locked", or "confident_unlocked"
        """
        if p_unlocked < config.BELIEF_THRESHOLD_CONFIDENT_LOCKED:
            return "confident_locked"
        elif p_unlocked > config.BELIEF_THRESHOLD_CONFIDENT_UNLOCKED:
            return "confident_unlocked"
        else:
            return "uncertain"

    def _estimate_distance_to_goal(self) -> int:
        """
        Estimate remaining steps to escape based on belief state.

        This is a heuristic for the MUD scenario:
        - If uncertain: need 1 step to gather info + 1 step to escape = 2 steps
        - If confident about door state: need 1 step to escape = 1 step
        - If confident door is unlocked: could escape immediately = 1 step
        - If confident door is locked: need to use window = 1 step

        For more complex scenarios, this could use graph traversal (Dijkstra).

        Returns:
            Estimated steps to goal
        """
        category = self._get_belief_category(self.p_unlocked)

        if category == "uncertain":
            # Need to gather info first, then escape
            return 2
        else:
            # Already confident, just need to execute escape
            return 1

    def select_skill(self, skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select best skill based on current belief (and optionally memory).

        Uses active inference scoring: goal value + info gain - cost
        When memory enabled: adds empirical bonus and epistemic exploration

        Args:
            skills: List of available skill dicts

        Returns:
            Selected skill dict
        """
        if not skills:
            raise ValueError("No skills available")

        # Determine context (belief-based, NOT ground truth)
        context = {"belief_category": self._get_belief_category(self.p_unlocked)}
        state_repr = context["belief_category"] # Use belief category as state for credit assignment

        scored_skills = []

        for skill in skills:
            # SAFETY CHECK: Credit Assignment
            # If this skill is known to lead to failure from this state, penalize it heavily
            if not self.credit_assignment.is_safe(state_repr, skill["name"]):
                # Apply massive penalty
                score = -999.0
                explanation = "⛔ BLOCKED by Credit Assignment (Known Failure Path)"
                scored_skills.append((score, skill, explanation))
                continue

            if self.use_procedural_memory:
                # Get skill statistics
                stats = get_skill_stats(
                    self.session, skill["name"],
                    context=context  # Only pass belief context, not door_state!
                )

                # Compute epistemic bonus (exploration)
                if self.episodes_completed < 20:
                    epistemic = compute_epistemic_value(
                        self.p_unlocked, stats, self.episodes_completed
                    )
                else:
                    epistemic = 0.0

                # Score with memory
                score, explanation = score_skill_with_memory(
                    skill, self.p_unlocked,
                    skill_stats=stats,
                    context=context,
                    memory_weight=0.5,
                    epistemic_bonus=epistemic
                )

                if self.verbose_memory:
                    skill["explanation"] = explanation

            else:
                # Pure theoretical scoring
                score = score_skill(skill, self.p_unlocked,
                                  alpha=self.alpha, beta=self.beta, gamma=self.gamma)
                explanation = None

            scored_skills.append((score, skill, explanation))

        # ====================================================================
        # CRITICAL STATE CONTROLLER (Meta-Cognition)
        # ====================================================================
        if config.ENABLE_GEOMETRIC_CONTROLLER and config.ENABLE_CRITICAL_STATE_PROTOCOLS:
            from scoring_silver import build_silver_stamp, entropy

            # Gather Metrics
            current_entropy = entropy(self.p_unlocked)

            # Use real data feeds
            agent_state = AgentState(
                entropy=current_entropy,
                history=self.history[-10:] if hasattr(self, 'history') else [],
                steps=self.steps_remaining if hasattr(self, 'steps_remaining') else 100, # Fallback if not tracked
                dist=self._estimate_distance_to_goal(),  # Use belief-based distance estimation
                rewards=self.reward_history,
                error=self.last_prediction_error
            )
            
            # Evaluate State
            critical_state = self.monitor.evaluate(agent_state)
            
            # Apply Protocols
            target_k = None
            boost_magnitude = 0.0
            mode_reason = f"State: {critical_state.name}"
            
            if critical_state == CriticalState.ESCALATION:
                # STOP_AND_ESCALATE PROTOCOL
                # The agent is thrashing or dying. Halt immediately.
                raise AgentEscalationError(f"CRITICAL FAILURE: Agent entered ESCALATION state. Reason: Meta-Cognitive Failure or Terminal Scarcity.")

            # ====================================================================
            # LYAPUNOV STABILITY CHECK (Dynamical Systems Safety)
            # ====================================================================
            v_value = None
            if self.lyapunov_monitor:
                # Update Lyapunov Monitor
                # Stress proxy: (100 - steps_remaining) / 100
                stress = (100 - agent_state.steps_remaining) / 100.0 if agent_state.steps_remaining else 0.0

                v_value = self.lyapunov_monitor.update(
                    entropy=current_entropy,
                    distance_estimate=agent_state.distance_to_goal,
                    stress=stress
                )

                # Check for Divergence (Instability)
                if self.lyapunov_monitor.is_diverging():
                    # The system is mathematically unstable. Kill it before it crashes.
                    raise AgentEscalationError(f"LYAPUNOV DIVERGENCE DETECTED: System is unstable (V={v_value:.2f}). Halting.")

            # Apply Critical State Protocols
            if critical_state == CriticalState.SCARCITY:
                # SPARTAN PROTOCOL: Ruthless Efficiency
                target_k = 0.0 # Specialist
                boost_magnitude = 2.0 # Massive boost for efficiency
                self.geo_mode = "SCARCITY (Efficiency)"
                
            elif critical_state == CriticalState.PANIC:
                # TANK PROTOCOL: Robustness
                target_k = 1.0 # Generalist
                boost_magnitude = config.BOOST_MAGNITUDE
                self.geo_mode = "PANIC (Robustness)"
                
            elif critical_state == CriticalState.DEADLOCK:
                # SISYPHUS PROTOCOL: Perturbation
                # In this demo, we just force Exploration
                target_k = 0.5 # Balanced
                boost_magnitude = 0.0
                self.geo_mode = "DEADLOCK (Perturbation)"
                
            elif critical_state == CriticalState.NOVELTY:
                # EUREKA PROTOCOL: Learning
                # Force Wait/Learn (Not fully implemented in demo skill set)
                target_k = 1.0 # Safe default
                self.geo_mode = "NOVELTY (Learning)"
                
            elif critical_state == CriticalState.HUBRIS:
                # ICARUS PROTOCOL: Skepticism
                # Force Exploration
                target_k = 1.0 # Safe default
                self.geo_mode = "HUBRIS (Skepticism)"
                
            else: # FLOW
                # Standard Active Inference
                target_k = 0.0 # Default to efficiency in Flow
                boost_magnitude = config.BOOST_MAGNITUDE
                self.geo_mode = "FLOW (Efficiency)"

            # NOTE: Boost application happens below in the unified geometric boost loop (lines 327-351)
            # The old binary boost loop (if dist < 0.2) has been removed to prevent duplicate boosts
            # The new alignment-based boost is more sophisticated and uses continuous weighting

            # Memory Veto: Check if procedural memory suggests panic mode
            # IMPORTANT: Memory veto must respect critical state priority order
            # Priority: ESCALATION > SCARCITY > PANIC > DEADLOCK > NOVELTY > HUBRIS > FLOW
            # Memory veto can only override states with LOWER priority than PANIC
            if self.use_procedural_memory and critical_state not in [CriticalState.ESCALATION, CriticalState.SCARCITY]:
                context = {"belief_category": self._get_belief_category(self.p_unlocked)}
                # Just check the first skill to get context stats
                sample_stats = get_skill_stats(self.session, skills[0]["name"], context)

                # If we have data and it's bad (< 50% success)
                overall = sample_stats.get("overall", {})
                if overall.get("uses", 0) > 2 and overall.get("success_rate", 0.5) < 0.5:
                    self.geo_mode = "PANIC (Robustness)"
                    mode_reason = "MEMORY VETO (Bad History)"
                    # Override target_k for memory-induced panic
                    target_k = 1.0  # Generalist (same as PANIC protocol)

            # 5. Apply Geometric Boost
            # boost_magnitude is set by critical state protocols above (lines 254-313)
            # All branches set it, so no fallback is needed

            boosted_skills = []
            for base_score, skill, explanation in scored_skills:
                # Skip if already penalized by credit assignment
                if base_score <= -999.0:
                    boosted_skills.append((base_score, skill, explanation))
                    continue
                    
                silver = build_silver_stamp(skill["name"], skill.get("cost", 1.0), self.p_unlocked)
                k_skill = silver["k_explore"]
                alignment = 1.0 - abs(k_skill - target_k)
                boost = alignment * boost_magnitude
                final_score = base_score + boost

                geo_expl = f" [Geo: {self.geo_mode} ({mode_reason}), k_target={target_k}, k_skill={k_skill:.2f}, Boost={boost:.2f}]"
                # Add geometric info to explanation (keep dict format if it was dict)
                if explanation:
                    if isinstance(explanation, dict):
                        # Add as new key to preserve dict structure
                        explanation['geometric_boost'] = geo_expl
                    else:
                        explanation = str(explanation) + geo_expl
                else:
                    explanation = geo_expl

                boosted_skills.append((final_score, skill, explanation))
            
            scored_skills = boosted_skills

        # Sort by score (descending) and pick best
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        best_score, best_skill, best_explanation = scored_skills[0]

        # Log decision
        self.decision_log.append({
            "step": self.step_count,
            "belief": self.p_unlocked,
            "belief_category": context["belief_category"],
            "selected": best_skill["name"],
            "score": best_score,
            "explanation": best_explanation,
            "all_scores": [(s["name"], score) for score, s, _ in scored_skills]
        })

        return best_skill

    def simulate_skill(self, skill: Dict[str, Any]) -> Tuple[str, float, bool]:
        """
        Simulate skill execution and return outcome.

        This is where ground truth (door_state) determines what actually happens.

        Args:
            skill: Skill dict with 'name'

        Returns:
            Tuple of (observation_name, updated_belief, escaped)
        """
        skill_name = skill["name"]
        p_before = self.p_unlocked

        if skill_name == "peek_door":
            # Peek reveals true door state
            if self.door_state == "locked":
                obs = "obs_door_locked"
                self.p_unlocked = config.BELIEF_DOOR_LOCKED
            else:  # unlocked
                obs = "obs_door_unlocked"
                self.p_unlocked = config.BELIEF_DOOR_UNLOCKED

            return obs, self.p_unlocked, False

        elif skill_name == "try_door":
            # Try to open door
            if self.door_state == "unlocked":
                # Success! Escape via door
                obs = "obs_door_opened"
                self.escaped = True
                # Update belief to certainty (we succeeded)
                self.p_unlocked = 0.99
                return obs, self.p_unlocked, True
            else:  # locked
                # Failed - door is stuck/locked
                obs = "obs_door_stuck"
                # This confirms door is locked
                self.p_unlocked = config.BELIEF_DOOR_STUCK
                return obs, self.p_unlocked, False

        elif skill_name == "go_window":
            # Window always works (safe escape)
            obs = "obs_window_escape"
            self.escaped = True
            # No new info about door
            return obs, self.p_unlocked, True

        # Handle balanced skills (multi-objective)
        elif skill_name == "probe_and_try":
            # Attempts to open with partial information gain
            if self.door_state == "unlocked":
                obs = "obs_door_opened"
                self.escaped = True
                self.p_unlocked = 0.99
                return obs, self.p_unlocked, True
            else:
                # Failed but gained partial info
                obs = "obs_partial_info"
                # Partial info: moves belief toward locked but not certainty
                self.p_unlocked = (self.p_unlocked + config.BELIEF_DOOR_STUCK) / 2
                return obs, self.p_unlocked, False

        elif skill_name == "informed_window":
            # Quick peek then window escape
            obs = "obs_strategic_escape"
            self.escaped = True
            # Brief peek gives some info about door state
            if self.door_state == "locked":
                self.p_unlocked = (self.p_unlocked + config.BELIEF_DOOR_LOCKED) / 2
            else:
                self.p_unlocked = (self.p_unlocked + config.BELIEF_DOOR_UNLOCKED) / 2
            return obs, self.p_unlocked, True

        elif skill_name == "exploratory_action":
            # Multi-tool approach: try multiple things
            if self.door_state == "unlocked":
                obs = "obs_door_opened"
                self.escaped = True
                self.p_unlocked = 0.99
                return obs, self.p_unlocked, True
            else:
                # Tried door (failed) but also checked window viability
                # High info gain about door state
                obs = "obs_attempted_open"
                self.p_unlocked = config.BELIEF_DOOR_STUCK
                return obs, self.p_unlocked, False

        elif skill_name == "adaptive_peek":
            # Between peek and try: some information, slight attempt
            # Primarily informational with minor goal attempt
            if self.door_state == "locked":
                obs = "obs_partial_info"
                # Good info about lock state but not perfect
                self.p_unlocked = (self.p_unlocked + config.BELIEF_DOOR_LOCKED) / 2
            else:
                # Unlocked: might partially open it or just observe
                import random
                if random.random() < 0.3:  # 30% chance of accidental success
                    obs = "obs_door_opened"
                    self.escaped = True
                    self.p_unlocked = 0.99
                    return obs, self.p_unlocked, True
                else:
                    obs = "obs_partial_info"
                    self.p_unlocked = (self.p_unlocked + config.BELIEF_DOOR_UNLOCKED) / 2
            return obs, self.p_unlocked, False

        else:
            # Unknown skill - no effect
            return "obs_unknown", self.p_unlocked, False

    def _adapt_meta_parameters(self):
        """
        Adjust exploration/exploitation based on recent performance.

        Meta-learning: If agent is doing well, can reduce exploration.
        If struggling, increase exploration.

        Only runs when adaptive_params=True and sufficient episodes completed.
        """
        if not self.adaptive_params or self.episodes_completed < 5:
            return  # Need data first

        recent = get_recent_episodes_stats(self.session, self.agent_id, limit=10)

        if recent["count"] < 5:
            return  # Not enough data

        avg_steps = recent["avg_steps"]
        success_rate = recent["success_rate"]

        # Adaptation rules
        new_params = {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma
        }

        # If doing well (low steps, high success), reduce exploration
        if avg_steps <= 2.5 and success_rate >= 0.8:
            new_params["beta"] = max(3.0, self.beta * 0.95)  # Reduce info-seeking

        # If struggling (high steps or low success), increase exploration
        elif avg_steps > 3.5 or success_rate < 0.6:
            new_params["beta"] = min(8.0, self.beta * 1.05)  # Increase info-seeking

        # If very efficient, can be more cost-sensitive
        if avg_steps <= 2.0:
            new_params["gamma"] = min(0.5, self.gamma * 1.02)

        # Update if changed
        if (new_params["alpha"] != self.alpha or
            new_params["beta"] != self.beta or
            new_params["gamma"] != self.gamma):

            update_meta_params(self.session, self.agent_id, new_params)
            self.alpha = new_params["alpha"]
            self.beta = new_params["beta"]
            self.gamma = new_params["gamma"]

    def run_episode(self, max_steps: int = None) -> str:
        """
        Run a full episode (until escaped or max steps).

        This is the main control loop:
        1. Create episode in graph
        2. Loop:
           a. Get available skills
           b. Select best skill
           c. Simulate outcome
           d. Log step
           e. Update belief in graph
           f. Check if escaped
        3. Mark episode complete

        Args:
            max_steps: Maximum steps before giving up (default from config)

        Returns:
            Episode ID (for inspection)
        """
        if max_steps is None:
            max_steps = config.MAX_STEPS

        # Reset episode state for independent episodes
        self.escaped = False
        self.step_count = 0

        # Reset belief to initial value for independent episodes
        # Each episode should start fresh to test learning strategies
        if hasattr(self, '_initial_belief'):
            self.p_unlocked = self._initial_belief
        else:
            # Store initial belief for future resets
            self._initial_belief = self.p_unlocked

        # Reset critical state tracking (Issue #7 fix)
        self.steps_remaining = max_steps
        self.reward_history = []
        self.history = []
        self.last_prediction_error = 0.0
        
        # Reset Credit Assignment history (but keep failed paths!)
        self.credit_assignment.reset()

        # Reset critical state monitor history (Issue #10 fix)
        if hasattr(self, 'monitor'):
            self.monitor.state_history = []

        # Create episode in graph
        episode_id = create_episode(self.session, self.agent_id, self.door_state)
        self.current_episode_id = episode_id
        
        self.current_episode_id = episode_id
        
        # FIX #1: Initialize path tracking for episodic memory
        if self.enable_episodic_memory:
            self.current_episode_path = []
            # Record initial state
            initial_state = {
                'step': 0,
                'belief': self.p_unlocked,
                'skill': 'start',
                'observation': f'door_{self.door_state}'
            }
            self.current_episode_path.append(initial_state)

        # Main control loop
        while not self.escaped and self.step_count < max_steps:
            # Get available skills and filter by mode
            all_skills = get_skills(self.session, self.agent_id)
            skills = filter_skills_by_mode(all_skills, self.skill_mode)

            # Select skill based on current belief
            selected_skill = self.select_skill(skills)

            # Record belief before action
            p_before = self.p_unlocked
            
            # Record step for credit assignment (state = belief category)
            belief_cat = self._get_belief_category(p_before)
            self.credit_assignment.record_step(belief_cat, selected_skill["name"])

            # Simulate skill execution
            observation, p_after, escaped = self.simulate_skill(selected_skill)
            
            # Calculate reward (proxy) for credit assignment
            # In this simple domain, we don't have explicit rewards, so we infer them
            # Success = +10, Failure/Stuck = -1, Trap (if we had one) = -10
            # For now, we assume standard step cost unless we define a trap
            reward = -1.0 
            if escaped:
                reward = 10.0
            
            # Process outcome for credit assignment
            self.credit_assignment.process_outcome(reward)
            
            # FIX #1: Track state after each action
            if self.enable_episodic_memory:
                state = {
                    'step': self.step_count + 1,
                    'belief': p_after,
                    'skill': selected_skill["name"],
                    'observation': observation
                }
                self.current_episode_path.append(state)

            # Log this step to graph
            log_step(
                self.session,
                episode_id,
                self.step_count,
                selected_skill["name"],
                observation,
                p_before,
                p_after
            )

            # Update belief in graph
            update_belief(self.session, self.agent_id, config.STATE_VAR_NAME, p_after)

            # Update step counters (Issue #8 fix)
            self.step_count += 1
            self.steps_remaining -= 1

            # Break if escaped
            if escaped:
                break

        # Mark episode as complete
        mark_episode_complete(self.session, episode_id, self.escaped, self.step_count)

        # Update skill statistics if using procedural memory
        if self.use_procedural_memory:
            context = {"belief_category": self._get_belief_category(self.p_unlocked)}
            update_skill_stats(self.session, episode_id, self.escaped, self.step_count, context)

        # Store episode in episodic memory
        if self.enable_episodic_memory and self.episodic_memory:
            self._store_episode_memory(episode_id)
            
            # Trigger offline learning every N episodes
            if self.adaptive_params and self.episodes_completed % config.EPISODIC_REPLAY_FREQUENCY == 0:
                self._perform_offline_learning()

        # Adapt meta-parameters if enabled
        if self.adaptive_params:
            self.episodes_completed += 1
            # Adapt every 5 episodes
            if self.episodes_completed % 5 == 0:
                self._adapt_meta_parameters()

            # Update episode count in graph
            update_meta_params(self.session, self.agent_id, {"episodes_completed": self.episodes_completed})

        return episode_id

    def get_trace(self) -> List[Dict[str, Any]]:
        """
        Get trace of current episode from graph.

        Returns:
            List of step dicts
        """
        if not self.current_episode_id:
            return []

        result = self.session.run("""
            MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
            MATCH (s)-[:USED_SKILL]->(sk:Skill)
            MATCH (s)-[:OBSERVED]->(o:Observation)
            WHERE id(e) = $episode_id
            RETURN s.step_index AS step_index,
                   sk.name AS skill,
                   o.name AS observation,
                   s.p_before AS p_before,
                   s.p_after AS p_after
            ORDER BY s.step_index
        """, episode_id=self.current_episode_id)

        trace = []
        for record in result:
            trace.append({
                "step_index": record["step_index"],
                "skill": record["skill"],
                "observation": record["observation"],
                "p_before": record["p_before"],
                "p_after": record["p_after"]
            })

        return trace

    def _store_episode_memory(self, episode_id: str):
        """
        Store the current episode in episodic memory with counterfactuals.
        
        Args:
            episode_id: ID of the completed episode
        """
        if not self.episodic_memory or not self.current_episode_path:
            return
        
        import json
        
        # Detect path type
        is_spatial = False
        if self.current_episode_path and isinstance(self.current_episode_path[0], str):
            is_spatial = True

        # Build actual path data
        actual_path = {
            'path_id': f'actual_{episode_id}',
            'outcome': 'success' if self.escaped else 'failure',
            'steps': self.step_count,
            'final_distance': 0 if self.escaped else 999
        }
        
        if is_spatial:
            actual_path['rooms_visited'] = self.current_episode_path
            actual_path['actions_taken'] = ['step'] * len(self.current_episode_path)
        else:
            # Generalized format for belief/state trajectories
            actual_path['path_data'] = json.dumps(self.current_episode_path)
            actual_path['state_type'] = 'belief_trajectory'
        
        try:
            # Store actual path
            self.episodic_memory.store_actual_path(episode_id, actual_path)
            
            # Generate and store counterfactuals if generator is available
            if self.counterfactual_generator:
                import config as cfg
                counterfactuals = self.counterfactual_generator.generate_alternatives(
                    actual_path,
                    max_alternates=cfg.MAX_COUNTERFACTUALS_PER_EPISODE
                )
                
                if counterfactuals:
                    self.episodic_memory.store_counterfactuals(episode_id, counterfactuals)
                    
        except Exception as e:
            print(f"Warning: Failed to store episodic memory: {e}")
            import traceback
            traceback.print_exc()
        
        # Apply forgetting mechanism to bound memory growth
        self._apply_forgetting_mechanism()
        
        # Reset path for next episode
        self.current_episode_path = []
    
    def _perform_offline_learning(self):
        """
        Perform offline learning by replaying recent episodes.
        
        This analyzes counterfactuals to identify better strategies
        without requiring new experience.
        """
        if not self.episodic_memory:
            return

        print("\n" + "="*70)
        print("OFFLINE LEARNING: Replaying recent episodes...")
        print("="*70)
        
        try:
            import config as cfg
            # Get recent episode IDs from episodic memory (EpisodicMemory nodes, not Episode nodes)
            result = self.session.run("""
                MATCH (em:EpisodicMemory)
                RETURN em.episode_id AS episode_id
                ORDER BY em.episode_id DESC
                LIMIT $num_episodes
            """, num_episodes=cfg.NUM_EPISODES_TO_REPLAY)
            
            episode_ids = [record['episode_id'] for record in result]
            if not episode_ids:
                print("Warning: No episodes found for offline learning")
                return
            
            total_regret = 0
            insights = []
            
            for ep_id in episode_ids:
                episode = self.episodic_memory.get_episode(ep_id)
                if not episode or not episode['counterfactuals']:
                    continue

                actual_steps = episode['actual_path']['steps']
                actual_outcome = episode['actual_path']['outcome']

                # FIX: Consider ALL counterfactuals, not just successful ones
                # Find best counterfactual (successful if possible, otherwise best failure)
                successful_cfs = [cf for cf in episode['counterfactuals'] if cf['outcome'] == 'success']
                failed_cfs = [cf for cf in episode['counterfactuals'] if cf['outcome'] == 'failure']

                best_cf = None
                if successful_cfs:
                    # Prefer successful counterfactuals (shortest path)
                    best_cf = min(successful_cfs, key=lambda x: x['steps'])
                elif failed_cfs and actual_outcome == 'failure':
                    # If actual path also failed, compare failed counterfactuals
                    # (Did we fail faster or slower?)
                    best_cf = min(failed_cfs, key=lambda x: x['steps'])

                if best_cf:
                    regret = self.episodic_memory.calculate_regret(
                        {'steps': actual_steps, 'outcome': actual_outcome},
                        {'steps': best_cf['steps'], 'outcome': best_cf['outcome']}
                    )

                    # Only record insights where counterfactual would have been better
                    if regret > 0:
                        total_regret += regret
                        insights.append({
                            'episode': ep_id,
                            'actual_steps': actual_steps,
                            'best_cf_steps': best_cf['steps'],
                            'regret': regret,
                            'divergence_point': best_cf['divergence_point']
                        })
            
            if insights:
                print(f"\nAnalyzed {len(insights)} episodes:")
                print(f"Total regret (improvement potential): {total_regret} steps")
                print(f"Average regret per episode: {total_regret/len(insights):.1f} steps")
                print("\nKey insights:")
                for insight in insights[:3]:  # Show top 3
                    print(f"  - Episode {insight['episode']}: Could save {insight['regret']} steps")
                    print(f"    (Diverged at step {insight['divergence_point']})")
                
                # Update skill priors if enabled
                if self.episodic_update_priors and self.use_procedural_memory:
                    self._update_skill_priors_from_insights(insights, cfg)
                    print("\n✓ Skill priors updated based on counterfactual insights")
                else:
                    print("\nNote: Skill prior updates disabled (set EPISODIC_UPDATE_PRIORS=true to enable)")
            else:
                print("No counterfactual insights available yet")
            
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"Warning: Offline learning failed: {e}")

    def _update_skill_priors_from_insights(self, insights: List[Dict], cfg):
        """
        Update skill priors based on counterfactual insights.
        
        Args:
            insights: List of dicts with episode analysis
            cfg: Config module reference
        """
        # Analyze which skills were used at divergence points
        # and penalize/reward them based on regret
        
        for insight in insights:
            episode_id = insight['episode']
            divergence_step = insight['divergence_point']
            regret = insight['regret']
            
            # Get the trace for this episode to see what skill was used
            # Note: episode_id is the Neo4j internal ID returned by create_episode()
            result = self.session.run("""
                MATCH (ep:Episode)-[:HAS_STEP]->(step:Step)
                WHERE id(ep) = $episode_id AND step.step_index = $step_index
                RETURN step.skill_name AS skill
            """, episode_id=episode_id, step_index=divergence_step)
            
            record = result.single()
            if not record:
                continue

            skill_name = record['skill']
            
            # Update skill stats based on regret
            # High regret = bad choice, lower that skill's preference
            # Low regret = good choice, increase that skill's preference
            
            # Get current skill stats
            context = {"belief_category": self._get_belief_category(self.p_unlocked)}
            stats = get_skill_stats(self.session, skill_name, context)
            
            if stats:
                # FIX #3: Calculate adjustment (negative for high regret)
                # Remove /100 divisor - regret directly affects success rate
                adjustment = -regret * self.episodic_learning_rate / cfg.EPISODIC_REGRET_SCALE_FACTOR
                
                # Update success rate (bounded between 0 and 1)
                current_rate = stats.get('success_rate', 0.5)
                new_rate = max(0.0, min(1.0, current_rate + adjustment))
                
                print(f"    Updating {skill_name}: {current_rate:.3f} -> {new_rate:.3f} (regret={regret})")
                
                # FIX #5: Update in Neo4j (this IS procedural memory integration)
                # The SkillStats nodes ARE used by procedural memory
                # Update the overall success_rate field (used by get_skill_stats)
                self.session.run("""
                    MATCH (sk:Skill {name: $skill_name})
                    MERGE (sk)-[:HAS_STATS]->(stats:SkillStats)
                    ON CREATE SET
                        stats.skill_name = $skill_name,
                        stats.success_rate = $new_rate,
                        stats.total_uses = 0,
                        stats.successful_episodes = 0,
                        stats.failed_episodes = 0,
                        stats.avg_steps_when_successful = 0.0,
                        stats.avg_steps_when_failed = 0.0,
                        stats.uncertain_uses = 0,
                        stats.uncertain_successes = 0,
                        stats.confident_locked_uses = 0,
                        stats.confident_locked_successes = 0,
                        stats.confident_unlocked_uses = 0,
                        stats.confident_unlocked_successes = 0,
                        stats.counterfactual_adjusted = true,
                        stats.last_updated = timestamp()
                    ON MATCH SET
                        stats.success_rate = $new_rate,
                        stats.counterfactual_adjusted = true,
                        stats.last_updated = timestamp()
                """, skill_name=skill_name, new_rate=new_rate)
            else:
                # FIX #5: Create stats if they don't exist
                print(f"    Creating stats for {skill_name} (first counterfactual update)")
                initial_rate = 0.5 - (regret * self.episodic_learning_rate / 10)
                initial_rate = max(0.0, min(1.0, initial_rate))
                
                self.session.run("""
                    MATCH (sk:Skill {name: $skill_name})
                    CREATE (sk)-[:HAS_STATS]->(stats:SkillStats {
                        context_belief: $context_belief,
                        success_rate: $success_rate,
                        total_uses: 0,
                        successful_uses: 0,
                        counterfactual_adjusted: true,
                        last_updated: timestamp()
                    })
                """, skill_name=skill_name, context_belief=context.get('belief_category'),
                   success_rate=initial_rate)
    
    def _apply_forgetting_mechanism(self):
        """
        Apply forgetting mechanism to bound episodic memory growth.
        
        Deletes oldest episodes when limit is exceeded.
        """
        if not config.EPISODIC_FORGETTING_ENABLED or not self.episodic_memory:
            return
        
        try:
            # Count total episodes
            result = self.session.run("""
                MATCH (e:EpisodicMemory)
                RETURN count(e) AS total
            """)
            
            total = result.single()['total']
            
            if total > config.EPISODIC_MAX_EPISODES:
                # Delete oldest episodes
                num_to_delete = total - config.EPISODIC_MAX_EPISODES
                
                # Get oldest episode IDs
                result = self.session.run("""
                    MATCH (e:EpisodicMemory)
                    RETURN e.episode_id AS episode_id
                    ORDER BY e.episode_id ASC
                    LIMIT $num_to_delete
                """, num_to_delete=num_to_delete)
                
                for record in result:
                    # Delete episode and all its paths
                    self.session.run("""
                        MATCH (e:EpisodicMemory {episode_id: $episode_id})
                        DETACH DELETE e
                    """, episode_id=record['episode_id'])
                    
                    self.session.run("""
                        MATCH (p:EpisodicPath)
                        WHERE p.path_id STARTS WITH $prefix
                        DELETE p
                    """, prefix=record['episode_id'])
                
                print(f"✓ Forgetting applied: Deleted {num_to_delete} oldest episodes")
        
        except Exception as e:
            print(f"Warning: Forgetting mechanism failed: {e}")
    
    def _initialize_counterfactual_generator(self, labyrinth):
        """
        Initialize counterfactual generator for episodic memory.
        
        Args:
            labyrinth: GraphLabyrinth instance (optional)
        """
        if not config.ENABLE_EPISODIC_MEMORY or not self.episodic_memory:
            return
        
        # Initialize counterfactual generator
        # Pass labyrinth only if enabled in config
        from memory.counterfactual_generator import CounterfactualGenerator
        
        lab_to_use = labyrinth if config.EPISODIC_USE_LABYRINTH else None

        self.counterfactual_generator = CounterfactualGenerator(self.session, lab_to_use, self.agent_id)
        
        if lab_to_use:
            print("✓ Counterfactual generator initialized (with Graph Labyrinth)")
        else:
            print("✓ Counterfactual generator initialized (Belief-Space only)")


if __name__ == "__main__":
    # Quick manual test
    from neo4j import GraphDatabase

    print("=== Agent Runtime Test ===\n")

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        print("Test 1: Unlocked door scenario")
        runtime = AgentRuntime(session, "unlocked", 0.5)
        episode_id = runtime.run_episode(max_steps=5)
        print(f"  Episode: {episode_id}")
        print(f"  Escaped: {runtime.escaped}")
        print(f"  Steps: {runtime.step_count}")

        trace = runtime.get_trace()
        for step in trace:
            print(f"    Step {step['step_index']}: {step['skill']} "
                  f"-> {step['observation']} "
                  f"(p: {step['p_before']:.2f} -> {step['p_after']:.2f})")

        print("\nTest 2: Locked door scenario")
        runtime2 = AgentRuntime(session, "locked", 0.5)
        episode_id2 = runtime2.run_episode(max_steps=5)
        print(f"  Episode: {episode_id2}")
        print(f"  Escaped: {runtime2.escaped}")
        print(f"  Steps: {runtime2.step_count}")

        trace2 = runtime2.get_trace()
        for step in trace2:
            print(f"    Step {step['step_index']}: {step['skill']} "
                  f"-> {step['observation']} "
                  f"(p: {step['p_before']:.2f} -> {step['p_after']:.2f})")

    driver.close()
    print("\n✓ Agent runtime works!")

