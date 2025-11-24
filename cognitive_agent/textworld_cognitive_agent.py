import random, time
from graph_model import get_skills
from neo4j import GraphDatabase
import config
from environments.domain4_textworld.textworld_adapter import TextWorldAdapter
from perception.llm_parser import LLMPerception
from planning.simple_graph_planner import GraphPlanner
from memory.episodic_replay import EpisodicMemory
from agent_runtime import AgentRuntime

from graph_utils import update_graph_from_state

class CognitiveTextWorldAgent:
    """Full Cognitive Agent for TextWorld.

    It combines:
    * LLMPerception for parsing observations
    * GraphPlanner for navigation planning
    * AgentRuntime for active‑inference, procedural memory, and critical‑state meta‑control
    * EpisodicMemory for offline replay
    """

    def __init__(self, session, seed: int = None):
        self.session = session
        # Initialise core components
        self.perception = LLMPerception(model_name="gpt-4o-mini")
        self.planner = GraphPlanner(session)
        self.episodic_mem = EpisodicMemory(session) if getattr(config, "ENABLE_EPISODIC_MEMORY", False) else None
        # AgentRuntime handles belief, skill scoring, credit assignment, critical state
        self.runtime = AgentRuntime(session, door_state="unknown", use_procedural_memory=True,
                                    adaptive_params=True, verbose_memory=False, skill_mode="hybrid")
        # Import get_skills function for skill retrieval
        # get_skills imported at module level
        # TextWorld environment adapter
        self.adapter = TextWorldAdapter(session)
        if seed is not None:
            self.adapter.generate_game(seed=seed)
        # Reset environment to start a fresh episode
        self.adapter.reset()

    def run_episode(self, max_steps: int = 30):
        # Reset environment and internal trackers
        init_state = self.adapter.reset()
        obs = init_state.feedback
        total_reward = 0
        visited_rooms = []
        for step in range(max_steps):
            # ---------- Perception ----------
            parsed_state = self.perception.parse(obs)
            # Update Neo4j graph with the new room / exits information
            update_graph_from_state(self.session, parsed_state)
            # Track visited rooms for episodic memory
            room_name = parsed_state.get("room_name")
            if room_name:
                visited_rooms.append(room_name)
            # ---------- Get admissible commands ----------
            admissible = self.adapter.get_admissible_commands()
            # ---------- Build skill list (inject planner move if available) ----------
            skills = get_skills(self.session, self.runtime.agent_id)
            # ---------- Select skill via active‑inference ----------
            
            # Planner provides a path to an external exit if we know the current room
            planner_plan = None
            if self.planner and room_name:
                planner_plan = self.planner.plan_to_exit(room_name)
                if planner_plan:
                    # Create a temporary skill representing the first direction of the plan
                    direction = planner_plan[0]
                    go_skill = {"name": f"go {direction}", "cost": 1}
                    # Prepend so the active‑inference can consider it first
                    skills = [go_skill] + skills
            # ---------- Select skill via active‑inference ----------
            selected_skill = self.runtime.select_skill(skills)
            # ---------- Map skill to a concrete TextWorld command ----------
            action = selected_skill["name"] if selected_skill["name"] in admissible else random.choice(admissible)
            # ---------- Execute action ----------
            next_state, reward, done = self.adapter.step(action)
            obs = next_state.feedback
            total_reward += reward
            # ---------- Break on terminal condition ----------
            if done:
                break
        # ---------- Store episodic memory (if enabled) ----------
        if self.episodic_mem:
            episode_id = f"cog_{int(time.time())}"
            actual_path = {
                "path_id": f"actual_{episode_id}",
                "outcome": "success" if total_reward > 0 else "failure",
                "steps": step + 1,
                "final_distance": 0 if total_reward > 0 else 999,
                "rooms_visited": visited_rooms,
                "actions_taken": []
            }
            self.episodic_mem.store_actual_path(episode_id, actual_path)
        return total_reward, step + 1, visited_rooms
