"""
Agent Runtime - Core decision-making and episode execution
Implements simplified active inference control loop
"""
from typing import Dict, List, Tuple, Any
from neo4j import Session
import config
from graph_model import (
    get_agent, get_initial_belief, update_belief,
    get_skills, create_episode, log_step, mark_episode_complete
)
from scoring import score_skill


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

    def __init__(self, session: Session, door_state: str, initial_belief: float = None):
        """
        Initialize agent runtime.

        Args:
            session: Neo4j session
            door_state: Ground truth ("locked" or "unlocked")
            initial_belief: Starting belief (default from config)
        """
        self.session = session
        self.door_state = door_state

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

        # Episode state
        self.escaped = False
        self.current_episode_id = None
        self.step_count = 0

    def select_skill(self, skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select best skill based on current belief.

        Uses active inference scoring: goal value + info gain - cost

        Args:
            skills: List of available skill dicts

        Returns:
            Selected skill dict
        """
        if not skills:
            raise ValueError("No skills available")

        # Score each skill
        scored_skills = []
        for skill in skills:
            score = score_skill(skill, self.p_unlocked)
            scored_skills.append((score, skill))

        # Sort by score (descending) and pick best
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        best_score, best_skill = scored_skills[0]

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

        else:
            # Unknown skill - no effect
            return "obs_unknown", self.p_unlocked, False

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
            # Get available skills
            skills = get_skills(self.session, self.agent_id)

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
