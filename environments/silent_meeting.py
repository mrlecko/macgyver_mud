import random
from scoring.schelling import SalienceMetric

class SilentMeetingEnvironment:
    """
    The Silent Meeting: A multi-agent coordination test.
    
    Scenario:
    - Two agents are placed in a grid of rooms.
    - Each room has a description.
    - Agents must choose the SAME room to meet in.
    - No communication is allowed.
    - Success = Both agents choose the same room.
    """
    
    def __init__(self):
        self.rooms = self._generate_rooms()
        self.metric = SalienceMetric()
        
    def _generate_rooms(self):
        """Generate a set of rooms, one of which is a Schelling Point."""
        rooms = [
            {'name': 'Room A', 'color': 'grey', 'feature': 'dust', 'x': 0},
            {'name': 'Room B', 'color': 'grey', 'feature': 'cobwebs', 'x': 1},
            {'name': 'Room C', 'color': 'grey', 'feature': 'shadows', 'x': 2},
            {'name': 'Room D', 'color': 'grey', 'feature': 'echoes', 'x': 3},
            # The Schelling Point: Unique color, unique feature, central-ish
            {'name': 'Room S', 'color': 'RED', 'feature': 'FOUNTAIN', 'x': 2.5} 
        ]
        return rooms
        
    def run_experiment(self, num_trials=100):
        """
        Run the experiment with two agents.
        
        Agent Logic:
        - Naive: Picks random room.
        - Schelling: Picks room with highest Salience.
        """
        naive_success = 0
        schelling_success = 0
        
        for _ in range(num_trials):
            # Shuffle rooms so position in list doesn't matter
            shuffled_rooms = self.rooms.copy()
            random.shuffle(shuffled_rooms)
            
            # --- Naive Agents ---
            # Pick random room
            choice_1 = random.choice(shuffled_rooms)['name']
            choice_2 = random.choice(shuffled_rooms)['name']
            if choice_1 == choice_2:
                naive_success += 1
                
            # --- Schelling Agents ---
            # Calculate salience
            scores = self.metric.calculate_salience(shuffled_rooms)
            # Pick max salience
            choice_1 = max(scores, key=scores.get)
            choice_2 = max(scores, key=scores.get) # Deterministic given same input
            
            if choice_1 == choice_2:
                schelling_success += 1
                
        return {
            'naive_rate': naive_success / num_trials,
            'schelling_rate': schelling_success / num_trials,
            'schelling_choice': choice_1 # What did they pick?
        }
