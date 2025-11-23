import random
import numpy as np

class LabyrinthEnvironment:
    """
    The Labyrinth of Entropy: A procedural environment to test Lyapunov stability.
    
    Modes:
    - 'infinite': Endless rooms, high entropy, no goal. Tests Divergence.
    - 'goal': Hidden center, distance gradient. Tests Convergence.
    """
    def __init__(self, mode='infinite', goal_distance=20, max_steps=100):
        self.mode = mode
        self.start_distance = goal_distance
        self.max_steps = max_steps
        self.reset()
        
    def reset(self):
        self.current_step = 0
        self.distance = self.start_distance
        self.stress = 0.0
        self.entropy = 1.0 # Start confused
        self.history = []
        self.done = False
        
        return self._get_state()
        
    def _get_state(self):
        """Return current state dictionary."""
        return {
            'description': self._generate_description(),
            'entropy': self.entropy,
            'distance_estimate': self.distance, # Agent 'senses' distance
            'stress': self.stress,
            'step': self.current_step
        }
        
    def _generate_description(self):
        """Generate a procedural room description."""
        adjectives = ['dark', 'twisting', 'echoing', 'cold', 'shifting', 'ancient']
        nouns = ['hallway', 'chamber', 'corridor', 'tunnel', 'void', 'nexus']
        features = ['glowing runes', 'dripping water', 'whispering shadows', 'floating dust']
        
        desc = f"A {random.choice(adjectives)} {random.choice(nouns)} with {random.choice(features)}."
        return desc
        
    def step(self, action):
        """
        Execute action.
        Actions: 'move', 'rest', 'scan'
        """
        self.current_step += 1
        self.stress += 0.05 # Fatigue accumulates unbounded for testing
        
        reward = 0
        info = {}
        
        if self.mode == 'infinite':
            # Infinite mode: Moving just leads to more entropy
            if action == 'move':
                self.entropy += 0.1 # Unbounded entropy growth
                # Distance drifts away (Divergence)
                self.distance += random.choice([0, 1])
                self.distance = max(10, self.distance)
                
            elif action == 'scan':
                self.entropy = max(0.0, self.entropy - 0.2)
                
            elif action == 'rest':
                self.stress = max(0.0, self.stress - 0.3)
                
        elif self.mode == 'goal':
            # Goal mode: Moving can reduce distance
            if action == 'move':
                # 70% chance to move closer if entropy is low (agent knows where to go)
                # 30% chance if entropy is high (random walk)
                success_prob = 0.8 if self.entropy < 0.5 else 0.3
                
                if random.random() < success_prob:
                    self.distance -= 1
                    reward = 1
                else:
                    self.distance += 0 # Stay or drift
                    
                self.entropy = min(1.0, self.entropy + 0.1) # New room
                
            elif action == 'scan':
                self.entropy = max(0.0, self.entropy - 0.3) # Scanning helps more in goal mode
                
            elif action == 'rest':
                self.stress = max(0.0, self.stress - 0.3)
        
        # Check termination
        if self.distance <= 0:
            self.done = True
            reward += 100
            info['outcome'] = 'success'
        elif self.current_step >= self.max_steps:
            self.done = True
            reward -= 10
            info['outcome'] = 'timeout'
        elif self.stress >= 1.0:
            self.done = True
            reward -= 50
            info['outcome'] = 'exhaustion'
            
        return self._get_state(), reward, self.done, info
