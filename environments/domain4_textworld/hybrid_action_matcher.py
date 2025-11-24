"""
Hybrid Action Matcher for TextWorld

Multi-stage approach to match actions to subgoals:
1. Template matching (fast, handles common cases)
2. Token overlap (baseline scoring)
3. LLM semantic scoring (accurate, for top candidates only)

Designed to balance speed and accuracy.
"""

import re
import subprocess
import json
from typing import List, Tuple, Dict


class HybridActionMatcher:
    """
    Intelligent action-to-subgoal matching using templates + LLM.
    """
    
    def __init__(self):
        """Initialize with action templates."""
        # Common TextWorld action patterns
        self.action_templates = {
            'navigation': {
                'pattern': r'\b(go|move|head|travel)\s+(north|south|east|west|up|down)\b',
                'keywords': ['go', 'move', 'head', 'travel', 'north', 'south', 'east', 'west'],
                'score': 10.0,
            },
            'take_item': {
                'pattern': r'\b(take|get|pick|grab)\b',
                'keywords': ['take', 'get', 'pick', 'grab'],
                'score': 8.0,
            },
            'put_item': {
                'pattern': r'\b(put|place|insert|drop)\b.*\b(in|into|on|inside)\b',
                'keywords': ['put', 'place', 'insert', 'drop', 'in', 'into', 'on'],
                'score': 8.0,
            },
            'open_unlock': {
                'pattern': r'\b(open|unlock|close|lock)\b',
                'keywords': ['open', 'unlock', 'close', 'lock'],
                'score': 7.0,
            },
            'examine_look': {
                'pattern': r'\b(examine|look|inspect|check)\b',
                'keywords': ['examine', 'look', 'inspect', 'check'],
                'score': 2.0,  # Lower priority (exploration, not achievement)
            },
        }
    
    def score_action(
        self, 
        action: str, 
        subgoal: str,
        context: str = "",
        use_llm: bool = False
    ) -> float:
        """
        Hybrid scoring: templates + tokens, optionally LLM.
        
        Args:
            action: Candidate action
            subgoal: Current subgoal to achieve
            context: Additional context (location, inventory)
            use_llm: Whether to use LLM for semantic scoring
        
        Returns:
            Score (higher = more relevant)
        """
        action_lower = action.lower()
        subgoal_lower = subgoal.lower()
        
        total_score = 0.0
        
        # Stage 1: Template matching (fast, strong signal)
        template_score = self._match_templates(action_lower, subgoal_lower)
        total_score += template_score
        
        # Stage 2: Token overlap (baseline)
        token_score = self._calculate_token_overlap(action_lower, subgoal_lower)
        total_score += token_score
        
        # Stage 3: LLM semantic (optional, for top candidates)
        if use_llm:
            llm_score = self._llm_semantic_score(action, subgoal, context)
            # LLM score is 0-1, scale to 0-10
            total_score += llm_score * 10.0
        
        return total_score
    
    def _match_templates(self, action: str, subgoal: str) -> float:
        """
        Check if action matches expected pattern from subgoal.
        
        Returns:
            Score boost if template matches
        """
        # Find which template the subgoal fits
        subgoal_template = None
        for template_name, template in self.action_templates.items():
            if re.search(template['pattern'], subgoal, re.IGNORECASE):
                subgoal_template = template
                break
        
        if not subgoal_template:
            return 0.0  # No template match
        
        # Check if action matches same template
        if re.search(subgoal_template['pattern'], action, re.IGNORECASE):
            return subgoal_template['score']
        
        # Check for keyword overlap (weaker signal)
        action_has_keyword = any(kw in action for kw in subgoal_template['keywords'])
        if action_has_keyword:
            return subgoal_template['score'] * 0.5  # Partial match
        
        return 0.0
    
    def _calculate_token_overlap(self, action: str, subgoal: str) -> float:
        """
        Token overlap scoring (baseline).
        """
        # Extract meaningful tokens (remove common words)
        stop_words = {'the', 'a', 'an', 'from', 'to', 'of', 'in', 'on', 'at'}
        
        action_tokens = set(action.split()) - stop_words
        subgoal_tokens = set(subgoal.split()) - stop_words
        
        if not subgoal_tokens:
            return 1.0  # Default
        
        overlap = len(action_tokens & subgoal_tokens)
        
        if overlap == 0:
            return 1.0  # Base score
        
        # Score based on overlap ratio
        overlap_ratio = overlap / len(subgoal_tokens)
        return 1.0 + (overlap_ratio * 5.0)  # 1.0 to 6.0 range
    
    def _llm_semantic_score(self, action: str, subgoal: str, context: str) -> float:
        """
        Use LLM to score semantic relevance (0-1).
        
        This is expensive, only call for top candidates.
        """
        prompt = f"""Score how well this action achieves the subgoal. Reply with ONLY a number from 0.0 to 1.0.

Subgoal: {subgoal}
Action: {action}

Scoring Guide:
1.0 = Directly achieves the subgoal
0.8 = Very likely to help achieve subgoal
0.5 = Might be relevant
0.2 = Tangentially related
0.0 = Completely irrelevant

Examples:
- Subgoal "go north" + Action "move north" → 1.0
- Subgoal "take key" + Action "take golden key" → 0.95
- Subgoal "take key" + Action "examine key" → 0.2
- Subgoal "go north" + Action "go south" → 0.0

Score:"""
        
        try:
            result = subprocess.run(
                ['llm', prompt],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            score_text = result.stdout.strip()
            # Extract first number found
            match = re.search(r'0\.\d+|1\.0|0|1', score_text)
            if match:
                score = float(match.group(0))
                return max(0.0, min(1.0, score))  # Clamp to [0, 1]
        except Exception as e:
            pass  # Fallback to 0.5
        
        return 0.5  # Default uncertain
    
    def select_best_action(
        self,
        actions: List[str],
        subgoal: str,
        context: str = "",
        llm_for_top_n: int = 3
    ) -> Tuple[str, float]:
        """
        Select best action using hybrid approach.
        
        Args:
            actions: Available actions
            subgoal: Current subgoal
            context: Additional context
            llm_for_top_n: Use LLM for top N candidates (default 3)
        
        Returns:
            (best_action, score)
        """
        if not actions:
            return ("look", 1.0)
        
        # Stage 1 & 2: Score all with templates + tokens (fast)
        scored_actions = []
        for action in actions:
            score = self.score_action(action, subgoal, context, use_llm=False)
            scored_actions.append((action, score))
        
        # Sort by score
        scored_actions.sort(key=lambda x: x[1], reverse=True)
        
        # Stage 3: Refine top N with LLM (expensive)
        if llm_for_top_n > 0:
            top_candidates = scored_actions[:llm_for_top_n]
            refined = []
            
            for action, base_score in top_candidates:
                llm_score = self._llm_semantic_score(action, subgoal, context)
                # Combine: 70% LLM, 30% templates/tokens
                final_score = (llm_score * 10.0 * 0.7) + (base_score * 0.3)
                refined.append((action, final_score))
            
            # Re-sort refined candidates
            refined.sort(key=lambda x: x[1], reverse=True)
            
            # Return best refined, or rest if refined all failed
            if refined:
                return refined[0]
            return scored_actions[0]
        else:
            return scored_actions[0]


# Quick test
if __name__ == "__main__":
    matcher = HybridActionMatcher()
    
    # Test 1: Navigation
    print("Test 1: Navigation")
    subgoal = "go north"
    actions = ["move north", "go south", "examine table", "take key"]
    
    best, score = matcher.select_best_action(actions, subgoal, llm_for_top_n=0)
    print(f"  Subgoal: {subgoal}")
    print(f"  Best action: {best} (score: {score:.2f})")
    print()
    
    # Test 2: Take item
    print("Test 2: Take item")
    subgoal = "take teapot"
    actions = ["take golden teapot", "take rusty key", "examine teapot", "go east"]
    
    best, score = matcher.select_best_action(actions, subgoal, llm_for_top_n=0)
    print(f"  Subgoal: {subgoal}")
    print(f"  Best action: {best} (score: {score:.2f})")
    print()
    
    # Test 3: With LLM (top 2)
    print("Test 3: With LLM refinement")
    subgoal = "put teapot in refrigerator"
    actions = [
        "insert teapot into refrigerator",
        "put teapot on table", 
        "examine refrigerator",
        "take teapot"
    ]
    
    best, score = matcher.select_best_action(actions, subgoal, llm_for_top_n=2)
    print(f"  Subgoal: {subgoal}")
    print(f"  Best action: {best} (score: {score:.2f})")
