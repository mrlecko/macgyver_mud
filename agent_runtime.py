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
from scoring_silver import score_skill
from critical_state import CriticalStateMonitor, CriticalState, AgentState
from scoring import score_skill_with_memory, compute_epistemic_value

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
                 skill_mode: str = "hybrid"):
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
        """
        self.session = session
        self.door_state = door_state
        self.use_procedural_memory = use_procedural_memory
        self.adaptive_params = adaptive_params
        self.verbose_memory = verbose_memory
        self.skill_mode = skill_mode

        # Get agent from graph
        agent = get_agent(session, config.AGENT_NAME)
        if not agent:
            raise ValueError(f"Agent '{config.AGENT_NAME}' not found in graph")

        self.agent_id = agent["id"]

        # Initialize belief
        if initial_belief is None:
            # Try to get from graph, or use config default
            belief = get_initial_belief(session, self.agent_id, config.STATE_VAR_NAME)
            self.p_unlocked = belief if belief is not None else config.INITIAL_BELIEF
        else:
            self.p_unlocked = initial_belief

        # Get meta-parameters (dynamic if adaptive)
        if adaptive_params:
            meta = get_meta_params(session, self.agent_id)
            self.alpha = meta["alpha"]
            self.beta = meta["beta"]
            self.gamma = meta["gamma"]
            self.episodes_completed = meta["episodes"]
        else:
            self.alpha = config.ALPHA
            self.beta = config.BETA
            self.gamma = config.GAMMA
            self.episodes_completed = 0

        # Episode state
        self.escaped = False
        self.current_episode_id = None
        self.step_count = 0

        # Decision log for verbose mode
        self.decision_log = []
        
        # Geometric Controller State
        self.geo_mode = "FLOW (Efficiency)" # Default
        self.switch_history = [] # For oscillation detection
        self.monitor = CriticalStateMonitor() # Critical State Monitor
        
        # Data Feeds for Critical States
        self.reward_history = []
        self.last_prediction_error = 0.0

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
        if p_unlocked < 0.3:
            return "confident_locked"
        elif p_unlocked > 0.7:
            return "confident_unlocked"
        else:
            return "uncertain"

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

        scored_skills = []

        for skill in skills:
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
                dist=10, # Placeholder: In real app, this would be Dijkstra distance
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

            elif critical_state == CriticalState.SCARCITY:
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

            # Apply Boosts based on Target K
            if target_k is not None:
                for i, (score, skill, expl) in enumerate(scored_skills):
                    stamp = build_silver_stamp(skill)
                    # Calculate distance to target k
                    dist = abs(stamp['k'] - target_k)
                    # Boost if close
                    if dist < 0.2:
                        new_score = score + boost_magnitude
                        scored_skills[i] = (new_score, skill, expl + f" [BOOST: {critical_state.name}]")
                context = {"belief_category": self._get_belief_category(self.p_unlocked)}
                # Just check the first skill to get context stats
                sample_stats = get_skill_stats(self.session, skills[0]["name"], context)
                
                # If we have data and it's bad (< 50% success)
                if sample_stats["count"] > 2 and sample_stats["success_rate"] < 0.5:
                    new_mode = "PANIC (Robustness)"
                    mode_reason = "MEMORY VETO (Bad History)"
            
            self.geo_mode = new_mode
            
            # Set Target k based on mode
            if "PANIC" in self.geo_mode:
                target_k = 0.8
            else:
                target_k = 0.0

            # 5. Apply Geometric Boost
            BOOST_MAGNITUDE = 5.0
            
            boosted_skills = []
            for base_score, skill, explanation in scored_skills:
                silver = build_silver_stamp(skill["name"], skill.get("cost", 1.0), self.p_unlocked)
                k_skill = silver["k_explore"]
                alignment = 1.0 - abs(k_skill - target_k)
                boost = alignment * BOOST_MAGNITUDE
                final_score = base_score + boost
                
                geo_expl = f" [Geo: {self.geo_mode} ({mode_reason}), k_target={target_k}, k_skill={k_skill:.2f}, Boost={boost:.2f}]"
                if explanation:
                    explanation += geo_expl
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

        # Create episode in graph
        episode_id = create_episode(self.session, self.agent_id, self.door_state)
        self.current_episode_id = episode_id
        self.step_count = 0

        # Main control loop
        while not self.escaped and self.step_count < max_steps:
            # Get available skills and filter by mode
            all_skills = get_skills(self.session, self.agent_id)
            skills = filter_skills_by_mode(all_skills, self.skill_mode)

            # Select skill based on current belief
            selected_skill = self.select_skill(skills)

            # Record belief before action
            p_before = self.p_unlocked

            # Simulate skill execution
            observation, p_after, escaped = self.simulate_skill(selected_skill)

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

            self.step_count += 1

            # Break if escaped
            if escaped:
                break

        # Mark episode as complete
        mark_episode_complete(self.session, episode_id, self.escaped, self.step_count)

        # Update skill statistics if using procedural memory
        if self.use_procedural_memory:
            context = {"belief_category": self._get_belief_category(self.p_unlocked)}
            update_skill_stats(self.session, episode_id, self.escaped, self.step_count, context)

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
