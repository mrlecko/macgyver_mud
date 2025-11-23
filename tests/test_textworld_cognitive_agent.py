"""
Test suite for TextWorld Cognitive Agent.

TDD Approach:
1. Write test (RED)
2. Implement minimal code (GREEN)
3. Refactor (REFACTOR)
4. Repeat

Phase 1 Focus: Basic agent chassis
- Belief state representation
- Simple EFE scoring
- Basic episode execution
"""
import pytest
from neo4j import GraphDatabase
import config


# ============================================================================
# PHASE 1: BASIC AGENT CHASSIS
# ============================================================================

class TestBeliefState:
    """Test 1-2: Belief state initialization and updates."""
    
    @pytest.fixture
    def neo4j_session(self):
        """Provide Neo4j session for testing."""
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        session = driver.session(database="neo4j")
        yield session
        session.close()
        driver.close()
    
    def test_belief_state_initialization(self, neo4j_session):
        """
        Test 1: Agent initializes with empty belief state.
        
        This test will FAIL initially because TextWorldCognitiveAgent doesn't exist yet.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        
        agent = TextWorldCognitiveAgent(neo4j_session, verbose=False)
        
        # Should start with empty beliefs
        assert agent.beliefs is not None
        assert len(agent.beliefs.get('rooms', {})) == 0
        assert len(agent.beliefs.get('objects', {})) == 0
        assert agent.beliefs.get('current_room') is None
        assert agent.current_step == 0
    
    def test_belief_update_from_observation(self, neo4j_session):
        """
        Test 2: Agent updates beliefs from text observation.
        
        Example: "You are in a kitchen. You can see: a rusty key, a wooden table."
        Should extract: room=kitchen, objects=[key, table]
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        
        agent = TextWorldCognitiveAgent(neo4j_session)
        
        # Simulate TextWorld observation
        observation = "You are in a kitchen. You can see: a rusty key, a wooden table."
        feedback = ""
        
        agent.update_beliefs(observation, feedback)
        
        # Should have recorded observation
        assert len(agent.observation_history) == 1
        assert agent.observation_history[0]['observation'] == observation
        
        # Step counter should increment
        assert agent.current_step == 1


class TestEFEScoring:
    """Test 3: Basic Expected Free Energy scoring."""
    
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
    
    def test_basic_efe_calculation(self, neo4j_session):
        """
        Test 3: EFE scoring for actions.
        
        Given:
        - Current state
        - Available actions
        - Quest goal
        
        Should return:
        - Scored actions (higher = better)
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        
        agent = TextWorldCognitiveAgent(neo4j_session)
        
        # Test action scoring
        actions = [
            'look',           # Info-gathering
            'take key',       # Goal-directed
            'examine table',  # Info-gathering
        ]
        
        scores = {}
        for action in actions:
            score = agent.score_action(action, agent.beliefs)
            scores[action] = score
        
        # Info-gathering should score reasonably
        assert scores['look'] > 0
        assert scores['examine table'] > 0
        
        # All scores should be finite
        for action, score in scores.items():
            assert score > -100
            assert score < 100


class TestActionSelection:
    """Test 4: Action selection from scored options."""
    
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
    
    def test_select_highest_efe_action(self, neo4j_session):
        """
        Test 4: Agent selects action with highest EFE score.
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        
        agent = TextWorldCognitiveAgent(neo4j_session)
        
        # Give it commands
        commands = ['look', 'inventory', 'take key', 'go north']
        
        selected = agent.select_action(commands)
        
        # Should select something valid
        assert selected in commands
        
        # Should have tracked the decision
        assert len(agent.action_history) == 1
        assert agent.action_history[0]['action'] == selected


class TestEpisodeExecution:
    """Test 5: Basic episode execution."""
    
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
    
    def test_simple_episode_completion(self, neo4j_session):
        """
        Test 5: Agent can complete a simple episode.
        
        Simple scenario:
        - 1 room
        - 1 object (key)
        - 1 goal (take key)
        
        Should:
        - Initialize
        - Observe
        - Act
        - Complete
        """
        from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
        
        agent = TextWorldCognitiveAgent(neo4j_session)
        
        # Simulate simple episode
        observation = "You are in a room. You see: a golden key."
        feedback = ""
        reward = 0
        done = False
        commands = ['look', 'take key', 'examine key']
        
        # Step 1
        action = agent.step(observation, feedback, reward, done, commands)
        assert action in commands
        
        # Agent should have state
        assert agent.current_step == 1
        assert len(agent.observation_history) == 1
        assert len(agent.action_history) == 1
        
        # Step 2 with reward
        reward = 10
        done = True
        action = agent.step(observation, "You take the key.", reward, done, ['inventory'])
        
        # Should track completion
        assert agent.done == True
        assert len(agent.reward_history) == 2
        assert agent.reward_history[-1] == 10


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
