"""
Tests for Schelling Points (Future Work)

PLACEHOLDER: This feature is marked for future implementation.
"""

import pytest

@pytest.mark.skip(reason="Schelling Points feature is future work")
def test_schelling_placeholder():
    """Placeholder test for future Schelling Points implementation."""
    from scoring.schelling import SalienceMetric
    metric = SalienceMetric()
    assert metric.compute_salience("option", {}) == 0.5
