import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from agent_runtime import AgentRuntime

# Mock skills
SKILL_SPECIALIST = {
    "name": "Specialist",
    "cost": 1.0,
    "expected_goal": 10.0,
    "expected_info": 0.0
}

SKILL_BALANCED = {
    "name": "Balanced",
    "cost": 1.0,
    "expected_goal": 5.0,
    "expected_info": 5.0
}

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def runtime(mock_session):
    # Mock graph interactions
    with patch('agent_runtime.get_agent') as mock_get_agent:
        mock_get_agent.return_value = {"id": 123}
        with patch('agent_runtime.get_initial_belief') as mock_belief:
            mock_belief.return_value = 0.5
            
            runtime = AgentRuntime(mock_session, "locked")
            return runtime

def test_baseline_preservation(runtime):
    """Test that when disabled, the agent picks the highest EFE skill."""
    config.ENABLE_GEOMETRIC_CONTROLLER = False
    
    # Mock scoring to return standard EFE
    # Specialist: 10.0, Balanced: 8.0
    with patch('agent_runtime.score_skill') as mock_score:
        mock_score.side_effect = lambda s, p, **kwargs: 10.0 if s["name"] == "Specialist" else 8.0
        
        skills = [SKILL_SPECIALIST, SKILL_BALANCED]
        selected = runtime.select_skill(skills)
        
        assert selected["name"] == "Specialist"

def test_geometric_panic_mode(runtime):
    """Test that when enabled + high entropy, agent picks Balanced skill."""
    config.ENABLE_GEOMETRIC_CONTROLLER = True
    
    # High entropy (p=0.5)
    runtime.p_unlocked = 0.5
    
    # Mock scoring: Specialist still has higher base score
    with patch('agent_runtime.score_skill') as mock_score:
        mock_score.side_effect = lambda s, p, **kwargs: 10.0 if s["name"] == "Specialist" else 8.0
        
        # Mock silver scoring to return k-values
        # Specialist k=0, Balanced k=0.8
        with patch('scoring_silver.build_silver_stamp') as mock_silver:
            def side_effect(name, cost, p):
                if name == "Specialist":
                    return {"k_explore": 0.0}
                else:
                    return {"k_explore": 0.8}
            mock_silver.side_effect = side_effect
            
            skills = [SKILL_SPECIALIST, SKILL_BALANCED]
            selected = runtime.select_skill(skills)
            
            # Should pick Balanced because Panic Mode demands k=0.8
            # Specialist: 10.0 + Boost(0.0 vs 0.8) = 10.0 + 0.2*5 = 11.0
            # Balanced: 8.0 + Boost(0.8 vs 0.8) = 8.0 + 1.0*5 = 13.0
            assert selected["name"] == "Balanced"

def test_geometric_flow_mode(runtime):
    """Test that when enabled + low entropy, agent picks Specialist skill."""
    config.ENABLE_GEOMETRIC_CONTROLLER = True
    
    # Low entropy (p=0.99)
    runtime.p_unlocked = 0.99
    
    with patch('agent_runtime.score_skill') as mock_score:
        mock_score.side_effect = lambda s, p, **kwargs: 10.0 if s["name"] == "Specialist" else 8.0
        
        with patch('scoring_silver.build_silver_stamp') as mock_silver:
            def side_effect(name, cost, p):
                if name == "Specialist":
                    return {"k_explore": 0.0}
                else:
                    return {"k_explore": 0.8}
            mock_silver.side_effect = side_effect
            
            skills = [SKILL_SPECIALIST, SKILL_BALANCED]
            selected = runtime.select_skill(skills)
            
            # Should pick Specialist because Flow Mode demands k=0.0
            # Specialist: 10.0 + Boost(0.0 vs 0.0) = 10.0 + 1.0*5 = 15.0
            # Balanced: 8.0 + Boost(0.8 vs 0.0) = 8.0 + 0.2*5 = 9.0
            assert selected["name"] == "Specialist"

def test_hysteresis(runtime):
    """Test that agent respects hysteresis thresholds."""
    config.ENABLE_GEOMETRIC_CONTROLLER = True
    
    # Reset state
    runtime.geo_mode = "FLOW (Efficiency)"
    runtime.switch_history = []
    
    # 1. Start Low (Flow)
    # p=0.99 -> Entropy ~0.05 (nats) / 0.08 (bits)
    runtime.p_unlocked = 0.99 
    runtime.select_skill([SKILL_SPECIALIST]) 
    assert runtime.geo_mode == "FLOW (Efficiency)"
    
    # 2. Buffer Zone (0.35 < H < 0.45)
    # p=0.92 -> Entropy ~0.40 (bits)
    # Should STAY in FLOW
    runtime.p_unlocked = 0.92
    runtime.select_skill([SKILL_SPECIALIST])
    assert runtime.geo_mode == "FLOW (Efficiency)"
    
    # 3. High Entropy (> 0.45)
    # p=0.5 -> Entropy ~1.0 (bits)
    # Should SWITCH to PANIC
    runtime.p_unlocked = 0.5
    runtime.select_skill([SKILL_SPECIALIST])
    assert runtime.geo_mode == "PANIC (Robustness)"
    
    # 4. Buffer Zone (0.35 < H < 0.45)
    # p=0.92 -> Entropy ~0.40 (bits)
    # Should STAY in PANIC
    runtime.p_unlocked = 0.92
    runtime.select_skill([SKILL_SPECIALIST])
    assert runtime.geo_mode == "PANIC (Robustness)"
    
    # 5. Low Entropy (< 0.35)
    # p=0.95 -> Entropy ~0.28 (bits)
    # Should SWITCH to FLOW
    runtime.p_unlocked = 0.95
    runtime.select_skill([SKILL_SPECIALIST])
    assert runtime.geo_mode == "FLOW (Efficiency)"

def test_memory_veto(runtime):
    """Test that Memory Veto forces Panic even with Low Entropy."""
    config.ENABLE_GEOMETRIC_CONTROLLER = True
    runtime.use_procedural_memory = True
    
    # Low Entropy (Should be FLOW)
    runtime.p_unlocked = 0.99
    
    # Mock Memory: Bad history in this context
    with patch('agent_runtime.get_skill_stats') as mock_stats:
        mock_stats.return_value = {
            "success_rate": 0.1, 
            "count": 10,
            "overall": {"uses": 10}
        }
        
        with patch('agent_runtime.score_skill', return_value=10.0):
            with patch('scoring_silver.build_silver_stamp', return_value={"k_explore": 0.0}):
                with patch('agent_runtime.score_skill_with_memory', return_value=(10.0, "explanation")):
                    
                    runtime.select_skill([SKILL_SPECIALIST])
                    
                    # Should be PANIC
                    assert "PANIC" in runtime.geo_mode
                    # Check decision log for reason if available, else just rely on mode
                    # (The explanation is not returned by select_skill, but the mode change confirms the veto)
