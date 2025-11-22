#!/usr/bin/env python3
"""
Integration test for skill mode functionality.
Tests filter_skills_by_mode and runner integration without requiring Neo4j.
"""

from graph_model import filter_skills_by_mode


def test_filter_crisp():
    """Test crisp mode filters correctly"""
    all_skills = [
        {"name": "peek_door", "kind": "sense", "cost": 1.0},
        {"name": "try_door", "kind": "act", "cost": 1.5},
        {"name": "go_window", "kind": "act", "cost": 2.0},
        {"name": "probe_and_try", "kind": "balanced", "cost": 2.0},
        {"name": "adaptive_peek", "kind": "balanced", "cost": 1.3}
    ]

    result = filter_skills_by_mode(all_skills, "crisp")
    assert len(result) == 3
    assert all(s["kind"] != "balanced" for s in result)
    print("✓ Crisp mode filter works")


def test_filter_balanced():
    """Test balanced mode filters correctly"""
    all_skills = [
        {"name": "peek_door", "kind": "sense", "cost": 1.0},
        {"name": "try_door", "kind": "act", "cost": 1.5},
        {"name": "go_window", "kind": "act", "cost": 2.0},
        {"name": "probe_and_try", "kind": "balanced", "cost": 2.0},
        {"name": "adaptive_peek", "kind": "balanced", "cost": 1.3}
    ]

    result = filter_skills_by_mode(all_skills, "balanced")
    assert len(result) == 2
    assert all(s["kind"] == "balanced" for s in result)
    print("✓ Balanced mode filter works")


def test_filter_hybrid():
    """Test hybrid mode returns all skills"""
    all_skills = [
        {"name": "peek_door", "kind": "sense", "cost": 1.0},
        {"name": "try_door", "kind": "act", "cost": 1.5},
        {"name": "go_window", "kind": "act", "cost": 2.0},
        {"name": "probe_and_try", "kind": "balanced", "cost": 2.0},
        {"name": "adaptive_peek", "kind": "balanced", "cost": 1.3}
    ]

    result = filter_skills_by_mode(all_skills, "hybrid")
    assert len(result) == 5
    print("✓ Hybrid mode filter works")


def test_invalid_mode():
    """Test that invalid mode raises error"""
    all_skills = [{"name": "peek_door", "kind": "sense", "cost": 1.0}]

    try:
        filter_skills_by_mode(all_skills, "invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid skill_mode" in str(e)
        print("✓ Invalid mode raises error correctly")


def test_runner_accepts_skill_mode():
    """Test that runner.py accepts --skill-mode argument"""
    import subprocess
    import sys

    # Test that --help shows skill-mode
    result = subprocess.run(
        [sys.executable, "runner.py", "--help"],
        capture_output=True,
        text=True
    )

    assert "--skill-mode" in result.stdout
    assert "crisp" in result.stdout
    assert "balanced" in result.stdout
    assert "hybrid" in result.stdout
    print("✓ Runner accepts --skill-mode argument")


if __name__ == "__main__":
    print("=" * 70)
    print("SKILL MODE INTEGRATION TESTS")
    print("=" * 70)
    print()

    test_filter_crisp()
    test_filter_balanced()
    test_filter_hybrid()
    test_invalid_mode()
    test_runner_accepts_skill_mode()

    print()
    print("=" * 70)
    print("✓ ALL INTEGRATION TESTS PASSED")
    print("=" * 70)
    print()
    print("Skill mode functionality is working correctly!")
    print("  - Crisp mode: filters to base skills only")
    print("  - Balanced mode: filters to multi-objective skills only")
    print("  - Hybrid mode: uses all skills")
    print("  - Runner CLI: accepts and validates --skill-mode flag")
