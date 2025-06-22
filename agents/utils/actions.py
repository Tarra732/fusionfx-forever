# agents/utils/actions.py

import numpy as np
from itertools import product

class ActionSpace:
    """Discrete action space for the meta controller"""
    
    def __init__(self, action_config):
        """
        action_config: dict with action names and their possible values
        Example: {
            "risk_appetite": [0.05, 0.1, 0.2, 0.3],
            "pair_expansion": [0, 1, 2],
            "retrain_frequency": [7, 14, 30]
        }
        """
        self.action_config = action_config
        self.action_names = list(action_config.keys())
        self.action_values = list(action_config.values())
        
        # Generate all possible action combinations
        self.action_combinations = list(product(*self.action_values))
        self.size = len(self.action_combinations)
    
    def decode(self, action_idx):
        """Convert action index to action dictionary"""
        if action_idx >= self.size:
            action_idx = action_idx % self.size
        
        combination = self.action_combinations[action_idx]
        return dict(zip(self.action_names, combination))
    
    def encode(self, action_dict):
        """Convert action dictionary to action index"""
        values = tuple(action_dict[name] for name in self.action_names)
        try:
            return self.action_combinations.index(values)
        except ValueError:
            # If exact match not found, find closest
            return 0
    
    def sample(self):
        """Sample a random action"""
        action_idx = np.random.randint(self.size)
        return self.decode(action_idx)
    
    def get_action_bounds(self):
        """Get the bounds for each action dimension"""
        bounds = {}
        for name, values in self.action_config.items():
            bounds[name] = {"min": min(values), "max": max(values), "options": values}
        return bounds