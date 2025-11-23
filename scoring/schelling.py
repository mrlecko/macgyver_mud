from typing import List, Dict, Any, Optional
from collections import Counter

class SalienceMetric:
    """
    Calculates the 'Salience' of options to enable coordination without communication.
    Salience is based on:
    1. Uniqueness (Rarity)
    2. Extremeness (Min/Max values)
    3. Centrality (Symmetry)
    """
    
    def calculate_salience(self, options: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate salience scores for a list of options.
        
        Args:
            options: List of dicts, e.g., [{'name': 'A', 'color': 'red'}, ...]
            
        Returns:
            Dict mapping option name to salience score (0.0 to 1.0+)
        """
        if not options:
            return {}
            
        scores = {opt['name']: 0.0 for opt in options}
        
        # 1. Uniqueness (Categorical features)
        self._score_uniqueness(options, scores)
        
        # 2. Extremeness (Numerical features)
        self._score_extremeness(options, scores)
        
        # 3. Centrality (Numerical positions)
        self._score_centrality(options, scores)
        
        return scores
    
    def _score_uniqueness(self, options: List[Dict[str, Any]], scores: Dict[str, float]):
        """Score options that have unique feature values."""
        # Collect all feature values
        features = {} # feature_name -> [values]
        for opt in options:
            for key, val in opt.items():
                if key == 'name': continue
                if isinstance(val, (str, bool)): # Categorical
                    if key not in features: features[key] = []
                    features[key].append(val)
        
        # Find unique values
        for key, values in features.items():
            counts = Counter(values)
            for opt in options:
                if key in opt:
                    val = opt[key]
                    # If this value appears only once, it's unique
                    if counts[val] == 1:
                        scores[opt['name']] += 1.0
                        
    def _score_extremeness(self, options: List[Dict[str, Any]], scores: Dict[str, float]):
        """Score options that have min or max numerical values."""
        # Collect numerical features
        features = {}
        for opt in options:
            for key, val in opt.items():
                if isinstance(val, (int, float)) and key != 'x': # x handled in centrality
                    if key not in features: features[key] = []
                    features[key].append(val)
                    
        for key, values in features.items():
            if len(values) < 3: continue # Need enough items for extremeness to matter
            
            min_val = min(values)
            max_val = max(values)
            
            if min_val == max_val: continue
            
            for opt in options:
                if key in opt:
                    val = opt[key]
                    if val == max_val:
                        scores[opt['name']] += 0.5 # Max is salient
                    elif val == min_val:
                        scores[opt['name']] += 0.5 # Min is salient

    def _score_centrality(self, options: List[Dict[str, Any]], scores: Dict[str, float]):
        """Score options that are spatially central."""
        # Check for 'x' coordinate
        x_values = [opt['x'] for opt in options if 'x' in opt]
        if not x_values: return
        
        min_x = min(x_values)
        max_x = max(x_values)
        midpoint = (min_x + max_x) / 2
        span = max_x - min_x
        
        if span == 0: return
        
        for opt in options:
            if 'x' in opt:
                dist = abs(opt['x'] - midpoint)
                # Closer to midpoint = higher score
                # Normalize: 1.0 at center, 0.0 at edges
                centrality = 1.0 - (dist / (span / 2))
                if centrality > 0.8: # Only reward being very close to center
                    scores[opt['name']] += centrality
