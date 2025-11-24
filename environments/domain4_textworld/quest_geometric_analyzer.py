"""
Quest Geometric Analyzer - Silver Gauge Application.

Applies Pythagorean means (Harmonic, Geometric, Arithmetic) to analyze
the quality and coherence of quest decompositions.

The Silver Gauge principle: H ≤ G ≤ A
- When H ≈ G ≈ A: Balanced, coherent decomposition
- When H << A: High variance, unbalanced decomposition

Option B - Phase 2: Geometric Analysis
"""
from typing import List, Dict, Any
import math


class QuestGeometricAnalyzer:
    """
    Analyzes quest decomposition quality using geometric (Pythagorean mean) analysis.

    The Silver Gauge uses three classical means:
    - Harmonic Mean (H): Sensitive to small values, penalizes imbalance
    - Geometric Mean (G): Balanced middle ground
    - Arithmetic Mean (A): Standard average

    For coherent decompositions: H ≈ G ≈ A (ratio close to 1.0)
    For incoherent decompositions: H << G < A (large spread)
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize geometric analyzer.

        Args:
            verbose: Print debug information
        """
        self.verbose = verbose

    def calculate_pythagorean_means(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate Pythagorean means (H, G, A) for a set of values.

        Args:
            values: List of positive numbers

        Returns:
            Dict with keys: harmonic, geometric, arithmetic
        """
        if not values or len(values) == 0:
            return {'harmonic': 0.0, 'geometric': 0.0, 'arithmetic': 0.0}

        # Filter out zeros/negatives for harmonic and geometric means
        positive_values = [v for v in values if v > 0]
        if not positive_values:
            return {'harmonic': 0.0, 'geometric': 0.0, 'arithmetic': 0.0}

        n = len(positive_values)

        # Harmonic mean: H = n / (1/x1 + 1/x2 + ... + 1/xn)
        harmonic = n / sum(1.0 / v for v in positive_values)

        # Geometric mean: G = (x1 * x2 * ... * xn) ^ (1/n)
        product = math.prod(positive_values)
        geometric = product ** (1.0 / n)

        # Arithmetic mean: A = (x1 + x2 + ... + xn) / n
        arithmetic = sum(positive_values) / n

        return {
            'harmonic': round(harmonic, 4),
            'geometric': round(geometric, 4),
            'arithmetic': round(arithmetic, 4)
        }

    def analyze_subgoal_coherence(self, quest: str, subgoals: List[str]) -> Dict[str, Any]:
        """
        Analyze the coherence of a quest decomposition using the Silver Gauge.

        Coherence is measured by:
        1. Token coverage: How well do subgoals cover the quest?
        2. Token overlap: Are subgoals distinct or redundant?
        3. Balance: Are subgoals similar in complexity? (via Pythagorean means)

        Args:
            quest: Original quest text
            subgoals: List of decomposed subgoals

        Returns:
            Dict with keys:
            - overall_coherence: Float 0.0-1.0
            - subgoal_scores: List of individual scores
            - pythagorean_means: Dict with H, G, A
            - balance_ratio: H/A (closer to 1.0 = more balanced)
        """
        if not subgoals or len(subgoals) == 0:
            return {
                'overall_coherence': 0.0,
                'subgoal_scores': [],
                'pythagorean_means': {'harmonic': 0.0, 'geometric': 0.0, 'arithmetic': 0.0},
                'balance_ratio': 0.0
            }

        # Extract tokens
        stopwords = {'the', 'a', 'an', 'first', 'then', 'finally', 'and', 'or', 'from', 'to', 'in', 'on', 'with'}
        quest_tokens = set(quest.lower().split()) - stopwords

        # Score each subgoal by coverage of quest tokens
        subgoal_scores = []
        for subgoal in subgoals:
            subgoal_tokens = set(subgoal.lower().split()) - stopwords

            if len(quest_tokens) == 0:
                coverage = 0.0
            else:
                # Coverage: what fraction of quest tokens appear in this subgoal?
                overlap = len(quest_tokens & subgoal_tokens)
                coverage = overlap / len(quest_tokens)

            # Distinctness: penalize if subgoal has NO quest tokens (irrelevant)
            if len(subgoal_tokens) == 0:
                distinctness = 0.0
            else:
                distinctness = len(quest_tokens & subgoal_tokens) / len(subgoal_tokens)

            # Combined score: balance coverage and distinctness
            score = (coverage + distinctness) / 2.0
            subgoal_scores.append(score)

        # Calculate Pythagorean means of subgoal scores
        pythagorean_means = self.calculate_pythagorean_means(subgoal_scores)

        # Balance ratio: H/A (1.0 = perfectly balanced, <1.0 = unbalanced)
        if pythagorean_means['arithmetic'] > 0:
            balance_ratio = pythagorean_means['harmonic'] / pythagorean_means['arithmetic']
        else:
            balance_ratio = 0.0

        # Overall coherence: geometric mean of subgoal scores
        # This captures both individual quality and balance
        overall_coherence = pythagorean_means['geometric']

        if self.verbose:
            print(f"   📐 Quest: {quest[:50]}...")
            print(f"   📐 Subgoals: {len(subgoals)}")
            print(f"   📐 Scores: {[f'{s:.2f}' for s in subgoal_scores]}")
            print(f"   📐 Pythagorean means: H={pythagorean_means['harmonic']:.3f}, "
                  f"G={pythagorean_means['geometric']:.3f}, A={pythagorean_means['arithmetic']:.3f}")
            print(f"   📐 Balance ratio (H/A): {balance_ratio:.3f}")
            print(f"   📐 Overall coherence: {overall_coherence:.3f}")

        return {
            'overall_coherence': round(overall_coherence, 4),
            'subgoal_scores': [round(s, 4) for s in subgoal_scores],
            'pythagorean_means': pythagorean_means,
            'balance_ratio': round(balance_ratio, 4)
        }


# Test code
if __name__ == "__main__":
    """Test geometric analyzer."""

    print("=" * 70)
    print("QUEST GEOMETRIC ANALYZER TEST")
    print("=" * 70)

    analyzer = QuestGeometricAnalyzer(verbose=True)

    # Test 1: Good decomposition
    print("\n--- Test 1: Good Decomposition ---")
    quest1 = "First move east, then take nest, finally place nest in dresser"
    subgoals1 = ["move east", "take nest", "place nest in dresser"]

    analysis1 = analyzer.analyze_subgoal_coherence(quest1, subgoals1)
    print(f"Overall coherence: {analysis1['overall_coherence']:.3f}")

    # Test 2: Poor decomposition
    print("\n--- Test 2: Poor Decomposition ---")
    quest2 = "Take the golden key from the table and unlock the chest"
    subgoals2 = ["go north", "examine room", "look around"]  # Unrelated!

    analysis2 = analyzer.analyze_subgoal_coherence(quest2, subgoals2)
    print(f"Overall coherence: {analysis2['overall_coherence']:.3f}")

    # Test 3: Pythagorean means
    print("\n--- Test 3: Pythagorean Means ---")
    values = [2.0, 4.0, 8.0]
    means = analyzer.calculate_pythagorean_means(values)
    print(f"Values: {values}")
    print(f"H={means['harmonic']:.3f}, G={means['geometric']:.3f}, A={means['arithmetic']:.3f}")
    print(f"Inequality: {means['harmonic']} ≤ {means['geometric']} ≤ {means['arithmetic']}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
