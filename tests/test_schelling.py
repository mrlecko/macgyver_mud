import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring.schelling import SalienceMetric

def test_uniqueness_detection():
    """Test that unique options get higher scores."""
    metric = SalienceMetric()
    
    options = [
        {'name': 'room_a', 'color': 'grey'},
        {'name': 'room_b', 'color': 'grey'},
        {'name': 'room_c', 'color': 'grey'},
        {'name': 'room_d', 'color': 'red'}  # Unique
    ]
    
    scores = metric.calculate_salience(options)
    
    assert scores['room_d'] > scores['room_a']
    assert scores['room_d'] > scores['room_b']
    assert scores['room_a'] == scores['room_b'] # Identical options score same

def test_extremeness_detection():
    """Test that min/max values get higher scores."""
    metric = SalienceMetric()
    
    options = [
        {'name': 'door_1', 'height': 10},
        {'name': 'door_2', 'height': 12},
        {'name': 'door_3', 'height': 11},
        {'name': 'door_4', 'height': 20}  # Max (Extreme)
    ]
    
    scores = metric.calculate_salience(options)
    
    # Max value should be salient
    assert scores['door_4'] > scores['door_1']
    assert scores['door_4'] > scores['door_2']

def test_centrality_detection():
    """Test that central options get higher scores."""
    metric = SalienceMetric()
    
    # 1D positions
    options = [
        {'name': 'pos_0', 'x': 0},
        {'name': 'pos_1', 'x': 1},
        {'name': 'pos_5', 'x': 5}, # Center (of 0-10 range implied or relative)
        {'name': 'pos_9', 'x': 9},
        {'name': 'pos_10', 'x': 10}
    ]
    
    # We need to tell metric the bounds or let it infer
    scores = metric.calculate_salience(options)
    
    # Midpoint should be salient
    assert scores['pos_5'] > scores['pos_1']
    assert scores['pos_5'] > scores['pos_9']

def test_empty_options():
    """Test handling of empty input."""
    metric = SalienceMetric()
    scores = metric.calculate_salience([])
    assert scores == {}

if __name__ == "__main__":
    # Manual run
    try:
        test_uniqueness_detection()
        print("Uniqueness Test: PASS")
        test_extremeness_detection()
        print("Extremeness Test: PASS")
        test_centrality_detection()
        print("Centrality Test: PASS")
        print("\nALL TESTS PASSED")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
