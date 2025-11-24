"""
Integration tests for TextWorld memory system.

Tests memory retrieval, episode storage, and integration with cognitive agent.
"""
import pytest
from unittest.mock import Mock, MagicMock
from environments.domain4_textworld.memory_system import MemoryRetriever
from environments.domain4_textworld.cognitive_agent import TextWorldCognitiveAgent
import time


class TestMemoryRetrieval:
    """Test memory retrieval functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock session
        self.mock_session = MagicMock()
        self.retriever = MemoryRetriever(session=self.mock_session, verbose=False)

    def test_extract_room_from_context(self):
        """Test room extraction from context string."""
        context = "Current Room: Attic\nVisible Objects: chest\nInventory: empty"
        room = self.retriever._extract_room_from_context(context)
        assert room == "Attic"

    def test_extract_room_no_match(self):
        """Test room extraction when not present."""
        context = "Some text without room info"
        room = self.retriever._extract_room_from_context(context)
        assert room == "Unknown"

    def test_extract_action_verb_common(self):
        """Test action verb extraction for common verbs."""
        assert self.retriever._extract_action_verb("take the key") == "take"
        assert self.retriever._extract_action_verb("go east") == "go"
        assert self.retriever._extract_action_verb("examine chest") == "examine"
        assert self.retriever._extract_action_verb("unlock door with key") == "unlock"

    def test_extract_action_verb_fallback(self):
        """Test action verb extraction fallback."""
        verb = self.retriever._extract_action_verb("custom action here")
        assert verb == "custom"

    def test_retrieve_no_session(self):
        """Test retrieval with no session returns empty."""
        retriever = MemoryRetriever(session=None)
        memories = retriever.retrieve_relevant_memories("context", "action")
        assert memories == []

    def test_retrieve_no_action_verb(self):
        """Test retrieval with empty action returns empty."""
        memories = self.retriever.retrieve_relevant_memories("context", "")
        assert memories == []


class TestMemoryStorage:
    """Test episode storage functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.retriever = MemoryRetriever(session=self.mock_session, verbose=False)

    def test_store_episode_structure(self):
        """Test that episode is stored with correct structure."""
        episode_data = {
            'episode_id': 'test_123',
            'total_reward': 5.0,
            'success': True,
            'goal': 'Test goal',
            'steps': [
                {'action': 'take key', 'room': 'Attic', 'reward': 1.0, 'outcome': 'positive'},
                {'action': 'go east', 'room': 'Attic', 'reward': 0.0, 'outcome': 'neutral'},
            ]
        }

        # Mock session.run to return success
        self.mock_session.run.return_value = None

        result = self.retriever.store_episode(episode_data)

        assert result == True
        # Verify session.run was called (episode + 2 steps = 3 calls)
        assert self.mock_session.run.call_count == 3

    def test_store_episode_no_session(self):
        """Test storage with no session returns False."""
        retriever = MemoryRetriever(session=None)
        result = retriever.store_episode({'episode_id': 'test'})
        assert result == False

    def test_store_episode_handles_errors(self):
        """Test storage gracefully handles errors."""
        self.mock_session.run.side_effect = Exception("DB error")

        episode_data = {
            'episode_id': 'test_456',
            'steps': []
        }

        result = self.retriever.store_episode(episode_data)
        assert result == False


class TestAgentMemoryIntegration:
    """Test memory integration with cognitive agent."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock session
        mock_session = MagicMock()

        # Create agent
        self.agent = TextWorldCognitiveAgent(session=mock_session, verbose=False)

        # Mock memory retrieval to avoid Neo4j calls
        self.agent.memory.retrieve_relevant_memories = Mock(return_value=[])

    def test_agent_has_memory_system(self):
        """Test that agent has memory retriever."""
        assert hasattr(self.agent, 'memory')
        assert isinstance(self.agent.memory, MemoryRetriever)

    def test_memory_bonus_with_positive_memory(self):
        """Test that positive memories give bonus."""
        # Set up agent beliefs (needed for context building)
        self.agent.beliefs = {
            'current_room': 'Attic',
            'rooms': {'Attic': {}},
            'inventory': []
        }

        # Mock memory with positive outcome
        self.agent.memory.retrieve_relevant_memories = Mock(return_value=[
            {
                'action': 'take key',
                'outcome': 'positive',
                'confidence': 0.9,
                'summary': 'Taking key worked well'
            }
        ])

        # Calculate bonus (only takes action parameter)
        bonus = self.agent.calculate_memory_bonus("take key")

        # Should be positive
        assert bonus > 0

    def test_memory_bonus_with_negative_memory(self):
        """Test that negative memories give penalty."""
        # Set up agent beliefs
        self.agent.beliefs = {
            'current_room': 'Kitchen',
            'rooms': {'Kitchen': {}},
            'inventory': []
        }

        # Mock memory with negative outcome
        self.agent.memory.retrieve_relevant_memories = Mock(return_value=[
            {
                'action': 'eat poison',
                'outcome': 'negative',
                'confidence': 0.95,
                'summary': 'Eating poison was bad'
            }
        ])

        bonus = self.agent.calculate_memory_bonus("eat poison")

        # Should be negative
        assert bonus < 0

    def test_memory_bonus_no_memories(self):
        """Test bonus is zero when no memories retrieved."""
        self.agent.beliefs = {'current_room': 'Test', 'rooms': {'Test': {}}, 'inventory': []}
        self.agent.memory.retrieve_relevant_memories = Mock(return_value=[])

        bonus = self.agent.calculate_memory_bonus("action")
        assert bonus == 0.0

    def test_save_episode_calls_memory_store(self):
        """Test that save_episode uses memory system."""
        # Set up agent state
        self.agent.action_history = [
            {'action': 'look'},
            {'action': 'take key'}
        ]
        self.agent.observation_history = [
            {'room': 'Attic'},
            {'room': 'Attic'}
        ]
        self.agent.reward_history = [0.0, 1.0]
        self.agent.current_step = 2

        # Mock memory.store_episode
        self.agent.memory.store_episode = Mock(return_value=True)

        # Save episode
        self.agent.save_episode()

        # Verify store_episode was called
        self.agent.memory.store_episode.assert_called_once()

        # Verify episode data structure
        call_args = self.agent.memory.store_episode.call_args[0][0]
        assert 'episode_id' in call_args
        assert 'steps' in call_args
        assert len(call_args['steps']) == 2
        assert call_args['total_reward'] == 1.0
        assert call_args['success'] == True

    def test_save_episode_includes_goal_from_plan(self):
        """Test that saved episode includes goal from plan."""
        from environments.domain4_textworld.plan import Plan, PlanStep

        # Set up plan
        plan = Plan(
            goal="Test goal from plan",
            strategy="Test strategy",
            steps=[PlanStep("Step 1", "test")],
            success_criteria="Success",
            contingencies={}
        )
        self.agent.current_plan = plan

        # Set up minimal episode data
        self.agent.action_history = [{'action': 'test'}]
        self.agent.observation_history = [{'room': 'Test'}]
        self.agent.reward_history = [0.0]
        self.agent.current_step = 1

        # Mock storage
        self.agent.memory.store_episode = Mock(return_value=True)

        # Save episode
        self.agent.save_episode()

        # Verify goal was included
        call_args = self.agent.memory.store_episode.call_args[0][0]
        assert call_args['goal'] == "Test goal from plan"

    def test_save_episode_graceful_on_error(self):
        """Test that save_episode doesn't crash on storage error."""
        # Set up minimal data
        self.agent.action_history = [{'action': 'test'}]
        self.agent.observation_history = [{'room': 'Test'}]
        self.reward_history = [0.0]

        # Mock storage to raise error
        self.agent.memory.store_episode = Mock(side_effect=Exception("Storage error"))

        # Should not crash
        try:
            self.agent.save_episode()
            # If we get here, test passed (no exception)
            assert True
        except Exception:
            pytest.fail("save_episode should not raise exception on storage error")


class TestMemoryInfluencesDecisions:
    """Test that memory system is integrated with agent."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_session = MagicMock()
        self.agent = TextWorldCognitiveAgent(session=mock_session, verbose=False)

    def test_memory_system_is_initialized(self):
        """Test that agent has memory retriever configured."""
        assert hasattr(self.agent, 'memory')
        assert isinstance(self.agent.memory, MemoryRetriever)
        assert self.agent.memory.session is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
