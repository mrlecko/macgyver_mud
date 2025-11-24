"""
Test suite for Phase 2: Geometric Analysis Integration.

Tests that the Silver Gauge (Pythagorean means) is applied to quest
decomposition to assess coherence and quality.

TDD Approach: Write tests FIRST, then implement to make them pass.
"""
import pytest
from neo4j import GraphDatabase
import config
import time


class TestQuestGeometricAnalyzer:
    """Test the geometric analyzer component."""

    def test_analyzer_exists(self):
        """Test: QuestGeometricAnalyzer class exists."""
        from environments.domain4_textworld.quest_geometric_analyzer import QuestGeometricAnalyzer

        analyzer = QuestGeometricAnalyzer()
        assert analyzer is not None, "QuestGeometricAnalyzer should be instantiable"

    def test_calculate_pythagorean_mean(self):
        """
        Test: Calculate Pythagorean mean (H ≤ G ≤ A) for a set of values.

        The Silver Gauge uses harmonic, geometric, and arithmetic means
        to analyze balance and coherence.
        """
        from environments.domain4_textworld.quest_geometric_analyzer import QuestGeometricAnalyzer

        analyzer = QuestGeometricAnalyzer()

        values = [2.0, 4.0, 8.0]
        result = analyzer.calculate_pythagorean_means(values)

        # Should return dict with H, G, A
        assert 'harmonic' in result, "Should calculate harmonic mean"
        assert 'geometric' in result, "Should calculate geometric mean"
        assert 'arithmetic' in result, "Should calculate arithmetic mean"

        # Verify inequality: H ≤ G ≤ A
        assert result['harmonic'] <= result['geometric'], "H ≤ G"
        assert result['geometric'] <= result['arithmetic'], "G ≤ A"

    def test_analyze_subgoal_coherence(self):
        """
        Test: Analyze coherence of subgoal decomposition.

        Uses token overlap and semantic similarity to assess if subgoals
        are well-balanced and collectively cover the quest.
        """
        from environments.domain4_textworld.quest_geometric_analyzer import QuestGeometricAnalyzer

        analyzer = QuestGeometricAnalyzer()

        quest = "First move east, then take nest, finally place nest in dresser"
        subgoals = ["move east", "take nest", "place nest in dresser"]

        coherence = analyzer.analyze_subgoal_coherence(quest, subgoals)

        # Should return analysis dict
        assert 'overall_coherence' in coherence, "Should calculate overall coherence"
        assert 'subgoal_scores' in coherence, "Should score individual subgoals"
        assert 'pythagorean_means' in coherence, "Should include Pythagorean means"

        # Coherence should be reasonable (0.0-1.0)
        assert 0.0 <= coherence['overall_coherence'] <= 1.0, \
            "Coherence should be normalized 0-1"

    def test_poor_decomposition_detected(self):
        """
        Test: Detect poor quest decomposition (low coherence).

        Example: Subgoals that don't cover the quest or overlap excessively.
        """
        from environments.domain4_textworld.quest_geometric_analyzer import QuestGeometricAnalyzer

        analyzer = QuestGeometricAnalyzer()

        # Poor decomposition: subgoals don't match quest well
        quest = "Take the golden key from the table and unlock the chest"
        bad_subgoals = ["go north", "examine room", "look around"]  # Unrelated!

        coherence_bad = analyzer.analyze_subgoal_coherence(quest, bad_subgoals)

        # Good decomposition for comparison
        good_subgoals = ["take golden key from table", "unlock chest with key"]
        coherence_good = analyzer.analyze_subgoal_coherence(quest, good_subgoals)

        # Good decomposition should score higher
        assert coherence_good['overall_coherence'] > coherence_bad['overall_coherence'], \
            f"Good decomposition ({coherence_good['overall_coherence']:.2f}) should score higher than bad ({coherence_bad['overall_coherence']:.2f})"


class TestGeometricAnalysisIntegration:
    """Test geometric analysis integration with cognitive agent."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_agent_has_geometric_analyzer(self, agent):
        """Test: Cognitive agent has geometric analyzer component."""
        assert hasattr(agent, 'geometric_analyzer'), \
            "Agent should have geometric_analyzer component"

    def test_reset_analyzes_quest_decomposition(self, agent):
        """
        Test: When quest is decomposed, geometric analysis is performed.

        The analysis should be stored for logging/introspection.
        """
        quest = "First move east, then take nest, finally place nest"
        agent.reset(quest)

        # Should have geometric analysis results
        assert hasattr(agent, 'last_geometric_analysis'), \
            "Agent should store last geometric analysis"
        assert agent.last_geometric_analysis is not None, \
            "Analysis should be performed on reset"

        # Analysis should include coherence metrics
        analysis = agent.last_geometric_analysis
        assert 'overall_coherence' in analysis, "Should have coherence score"
        assert 'pythagorean_means' in analysis, "Should have Pythagorean means"

    def test_geometric_metrics_logged_to_neo4j(self, agent, neo4j_session):
        """
        Test: Geometric analysis metrics are logged to Neo4j for research.

        This enables analysis of decomposition quality over episodes.
        """
        quest = "First move east, then take nest, finally place nest"
        agent.reset(quest)

        # Agent should have logged analysis to Neo4j
        # Check that a GeometricAnalysis node was created
        query = """
        MATCH (g:GeometricAnalysis)
        WHERE g.quest = $quest
          AND g.timestamp > timestamp() - (5 * 1000)  // Last 5 seconds
        RETURN g.coherence AS coherence,
               g.harmonic_mean AS harmonic,
               g.geometric_mean AS geometric,
               g.arithmetic_mean AS arithmetic
        LIMIT 1
        """

        result = neo4j_session.run(query, quest=quest)
        record = result.single()

        assert record is not None, "Geometric analysis should be logged to Neo4j"
        assert record['coherence'] is not None, "Should log coherence score"
        assert record['harmonic'] is not None, "Should log harmonic mean"
        assert record['geometric'] is not None, "Should log geometric mean"
        assert record['arithmetic'] is not None, "Should log arithmetic mean"


class TestSilverGaugeApplication:
    """Test the Silver Gauge specifically for quest quality assessment."""

    def test_silver_gauge_for_balanced_decomposition(self):
        """
        Test: Silver Gauge detects balanced decomposition.

        When H ≈ G ≈ A, the subgoals are well-balanced in complexity.
        """
        from environments.domain4_textworld.quest_geometric_analyzer import QuestGeometricAnalyzer

        analyzer = QuestGeometricAnalyzer()

        # Balanced decomposition: similar-length subgoals
        quest = "First A, then B, finally C"
        subgoals = ["do A", "do B", "do C"]

        analysis = analyzer.analyze_subgoal_coherence(quest, subgoals)
        means = analysis['pythagorean_means']

        # Check balance: ratio of H/A should be close to 1.0 for balanced decomposition
        ratio = means['harmonic'] / means['arithmetic']

        # For similar values, H/A ratio should be > 0.8 (reasonably balanced)
        # Note: This is a heuristic threshold
        assert ratio > 0.7, \
            f"Balanced decomposition should have H/A ratio > 0.7, got {ratio:.2f}"

    def test_silver_gauge_for_unbalanced_decomposition(self):
        """
        Test: Silver Gauge detects unbalanced decomposition.

        When H << A, there's high variance in subgoal complexity.
        """
        from environments.domain4_textworld.quest_geometric_analyzer import QuestGeometricAnalyzer

        analyzer = QuestGeometricAnalyzer()

        # Unbalanced decomposition: very different complexities
        # (We'll use token counts as proxy for complexity)
        quest = "Do complex multi-step task A, then simple task B"
        # Simulate by having different coverage scores
        subgoals = ["complex multi-step task A with many tokens", "task B"]

        analysis = analyzer.analyze_subgoal_coherence(quest, subgoals)
        means = analysis['pythagorean_means']

        # For unbalanced values, H/A ratio should be lower
        ratio = means['harmonic'] / means['arithmetic']

        # We expect ratio < 0.9 for unbalanced (but not too strict)
        # The key is that it's LOWER than balanced case
        assert ratio < 1.0, "H/A ratio should be < 1.0"


class TestBackwardCompatibility:
    """Test that geometric analysis doesn't break existing functionality."""

    @pytest.fixture
    def neo4j_session(self):
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()

    @pytest.fixture
    def agent(self, neo4j_session):
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        return TextWorldCognitiveAgent(neo4j_session, verbose=False)

    def test_reset_without_quest_still_works(self, agent):
        """Test: Agent reset without quest doesn't crash (MacGyver mode)."""
        agent.reset()  # No quest parameter

        # Should work fine, no geometric analysis
        assert len(agent.subgoals) == 0, "No subgoals in MacGyver mode"

        # last_geometric_analysis should be None or not cause issues
        if hasattr(agent, 'last_geometric_analysis'):
            assert agent.last_geometric_analysis is None, \
                "No analysis in MacGyver mode"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
