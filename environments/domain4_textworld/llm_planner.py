
from typing import List

class LLMPlanner:
    """
    Generates high-level plans using an LLM (mocked).
    Breaks down complex goals into sequential steps.
    """
    
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        
    def generate_plan(self, goal: str, context: str) -> List[str]:
        """
        Generate a sequence of steps to achieve the goal.
        
        Args:
            goal: The high-level objective (e.g., "Open the safe")
            context: Current world state description
            
        Returns:
            List of action strings (e.g., ['find key', 'take key'])
        """
        # MOCK LOGIC
        # In a real system, we would prompt the LLM:
        # "Given the goal '{goal}' and context '{context}', list the steps to solve it."
        
        if "safe" in goal.lower():
            return ['find key', 'take key', 'unlock safe', 'open safe']
            
        if "eat" in goal.lower():
            return ['find food', 'take food', 'eat food']
            
        return ['explore']
