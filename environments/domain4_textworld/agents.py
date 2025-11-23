"""
TextWorld agents: Baseline and Critical State Protocol variants.

This module demonstrates how different agents can plug into the TextWorld adapter.
- Baseline: Simple random/heuristic agent without critical state monitoring
- Critical: Agent with Critical State Protocol oversight
"""
import random
from critical_state import CriticalStateMonitor, CriticalState


class BaselineTextWorldAgent:
    """
    Baseline agent for TextWorld without critical state monitoring.
    
    Strategy: Random action selection from admissible commands.
    """
    
    def __init__(self):
        self.name = "Baseline (Random)"
    
    def select_action(self, admissible_commands):
        """
        Select an action from available commands.
        
        Args:
            admissible_commands: List of valid command strings
        
        Returns:
            Selected command string
        """
        if not admissible_commands:
            return "look"  # Default fallback
        
        # Random selection
        return random.choice(admissible_commands)


class CriticalTextWorldAgent:
    """
    Agent with Critical State Protocol monitoring.
    
    Uses same baseline strategy but with meta-cognitive oversight
    to detect and respond to critical states (PANIC, DEADLOCK, etc.)
    """
    
    def __init__(self):
        self.name = "Critical (Protocols)"
        self.monitor = CriticalStateMonitor()
        self.baseline = BaselineTextWorldAgent()
        
        # Track patterns for DEADLOCK detection
        self.recent_actions = []
    
    def select_action(self, admissible_commands, adapter):
        """
        Select action with critical state protocol oversight.
        
        Args:
            admissible_commands: List of valid commands
            adapter: TextWorldAdapter instance for state access
        
        Returns:
            Selected command string
        """
        if not admissible_commands:
            return "look"
        
        # Get agent state for critical monitoring
        agent_state = adapter.get_agent_state()
        
        # Check critical state
        critical_state = self.monitor.evaluate(agent_state)
        
        # Respond based on critical state
        if critical_state == CriticalState.PANIC:
            # PANIC: High entropy/confusion
            # Protocol: TANK (robustness over efficiency)
            # Strategy: Choose simpler, safer actions
            action = self._panic_action(admissible_commands)
        
        elif critical_state == CriticalState.DEADLOCK:
            # DEADLOCK: Repeated pattern detected
            # Protocol: SISYPHUS (force perturbation)
            # Strategy: Break the pattern with different action
            action = self._deadlock_action(admissible_commands)
        
        elif critical_state == CriticalState.SCARCITY:
            # SCARCITY: Running out of moves
            # Protocol: SPARTAN (efficiency)
            # Strategy: Focus on goal-directed actions
            action = self._scarcity_action(admissible_commands)
        
        elif critical_state == CriticalState.NOVELTY:
            # NOVELTY: High prediction error (surprise)
            # Protocol: EUREKA (learning mode)
            # Strategy: Explore to update world model
            action = self._novelty_action(admissible_commands)
        
        elif critical_state == CriticalState.HUBRIS:
            # HUBRIS: Overconfidence
            # Protocol: ICARUS (skepticism)
            # Strategy: Don't be complacent
            action = self.baseline.select_action(admissible_commands)
        
        else:  # FLOW
            # Normal operation
            action = self.baseline.select_action(admissible_commands)
        
        # Track for pattern detection
        self.recent_actions.append(action)
        if len(self.recent_actions) > 10:
            self.recent_actions.pop(0)
        
        return action
    
    def _panic_action(self, commands):
        """
        PANIC protocol: Choose safer, simpler actions.
        
        Prefer actions like 'look', 'inventory', 'examine' over complex moves.
        """
        # Prioritize information-gathering commands
        safe_commands = [c for c in commands if any(
            keyword in c.lower() for keyword in ['look', 'inventory', 'examine', 'check']
        )]
        
        if safe_commands:
            return random.choice(safe_commands)
        return random.choice(commands)
    
    def _deadlock_action(self, commands):
        """
        DEADLOCK protocol: Break repetitive pattern.
        
        Avoid recently used actions.
        """
        # Filter out recently used actions
        if self.recent_actions:
            new_commands = [c for c in commands if c not in self.recent_actions[-3:]]
            if new_commands:
                return random.choice(new_commands)
        
        return random.choice(commands)
    
    def _scarcity_action(self, commands):
        """
        SCARCITY protocol: Focus on efficiency.
        
        Prioritize goal-directed actions.
        """
        # Prioritize actions that might advance quest
        goal_commands = [c for c in commands if any(
            keyword in c.lower() for keyword in ['take', 'open', 'unlock', 'use', 'go']
        )]
        
        if goal_commands:
            return random.choice(goal_commands)
        return random.choice(commands)
    
    def _novelty_action(self, commands):
        """
        NOVELTY protocol: Explore to learn.
        
        Try new actions to update world model.
        """
        # Try commands we haven't used recently
        if self.recent_actions:
            novel_commands = [c for c in commands if c not in self.recent_actions]
            if novel_commands:
                return random.choice(novel_commands)
        
        return random.choice(commands)


def run_episode(agent, adapter, max_steps=100, verbose=False):
    """
    Run one episode with given agent.
    
    Args:
        agent: Agent instance (Baseline or Critical)
        adapter: TextWorldAdapter instance
        max_steps: Maximum steps per episode
        verbose: Print detailed output
    
    Returns:
        dict with episode results
    """
    adapter.reset()
    total_reward = 0
    critical_states = []
    
    for step in range(max_steps):
        # Get admissible commands
        commands = adapter.get_admissible_commands()
        
        if not commands:
            if verbose:
                print(f"  Step {step}: No commands available, ending episode")
            break
        
        # Select action
        if isinstance(agent, CriticalTextWorldAgent):
            action = agent.select_action(commands, adapter)
            # Track critical state
            agent_state = adapter.get_agent_state()
            critical = agent.monitor.evaluate(agent_state)
            critical_states.append(critical)
        else:
            action = agent.select_action(commands)
        
        # Execute action
        state, reward, done = adapter.step(action)
        total_reward += reward
        
        if verbose and step % 10 == 0:
            print(f"  Step {step}: '{action}' → reward={total_reward:.1f}")
        
        if done:
            if verbose:
                print(f"  Episode ended at step {step+1}")
            break
    
    return {
        'total_reward': total_reward,
        'steps': step + 1,
        'critical_states': critical_states,
        'done': done if 'done' in locals() else False
    }


if __name__ == "__main__":
    """Quick test of agents."""
    from neo4j import GraphDatabase
    import config
    from environments.domain4_textworld.textworld_adapter import TextWorldAdapter
    
    # Setup
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    session = driver.session(database="neo4j")
    adapter = TextWorldAdapter(session)
    adapter.generate_game(seed=42)
    
    print("=" * 70)
    print("TEXTWORLD AGENTS TEST")
    print("=" * 70)
    
    # Test baseline
    print("\n--- Baseline Agent ---")
    baseline = BaselineTextWorldAgent()
    result = run_episode(baseline, adapter, verbose=True)
    print(f"Result: {result['total_reward']:.1f} reward in {result['steps']} steps")
    
    # Test critical
    print("\n--- Critical Agent ---")
    critical = CriticalTextWorldAgent()
    result = run_episode(critical, adapter, verbose=True)
    print(f"Result: {result['total_reward']:.1f} reward in {result['steps']} steps")
    
    from collections import Counter
    state_counts = Counter(result['critical_states'])
    print(f"Critical states: {dict(state_counts)}")
    
    adapter.close()
    session.close()
    driver.close()
