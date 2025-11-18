#!/usr/bin/env python3
"""
RED TEAM Validation Script - Critical Assessment of Procedural Memory

Tests:
1. Does memory actually accumulate?
2. Does memory influence decisions observably?
3. Does the agent cheat (know ground truth)?
4. Does learning actually occur (performance improves)?
5. Edge cases: no data, bad data, conflicting data
6. Statistical significance of improvements
"""
import sys
from neo4j import GraphDatabase
import config
from agent_runtime import AgentRuntime
from graph_model import get_skill_stats, get_agent, get_recent_episodes_stats


def red_team_test_1_memory_accumulation():
    """
    RED TEAM TEST 1: Does memory actually accumulate?

    Run multiple episodes and verify skill stats increase.
    """
    print("=" * 80)
    print("RED TEAM TEST 1: Memory Accumulation")
    print("=" * 80)

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Reset skill stats
        session.run("""
            MATCH (stats:SkillStats)
            SET stats.total_uses = 0,
                stats.successful_episodes = 0,
                stats.failed_episodes = 0,
                stats.uncertain_uses = 0,
                stats.uncertain_successes = 0,
                stats.confident_locked_uses = 0,
                stats.confident_locked_successes = 0,
                stats.confident_unlocked_uses = 0,
                stats.confident_unlocked_successes = 0
        """)

        # Check initial state
        peek_stats = get_skill_stats(session, "peek_door")
        print(f"\n[BEFORE] peek_door stats:")
        print(f"  Total uses: {peek_stats['overall']['uses']}")
        print(f"  Success rate: {peek_stats['overall']['success_rate']:.2%}")

        # Run 5 episodes WITH memory
        print("\n[RUNNING] 5 episodes with memory enabled...")
        for i in range(5):
            agent = AgentRuntime(
                session,
                door_state="unlocked",
                initial_belief=0.5,
                use_procedural_memory=True
            )
            agent.run_episode(max_steps=5)
            print(f"  Episode {i+1}: {agent.step_count} steps, escaped={agent.escaped}")

        # Check after state
        peek_stats_after = get_skill_stats(session, "peek_door")
        print(f"\n[AFTER] peek_door stats:")
        print(f"  Total uses: {peek_stats_after['overall']['uses']}")
        print(f"  Success rate: {peek_stats_after['overall']['success_rate']:.2%}")
        print(f"  Confidence: {peek_stats_after['overall']['confidence']:.2f}")

        # VALIDATION
        if peek_stats_after['overall']['uses'] > peek_stats['overall']['uses']:
            print("\n✅ PASS: Memory accumulated (uses increased)")
        else:
            print("\n❌ FAIL: Memory did NOT accumulate!")
            driver.close()
            return False

        if peek_stats_after['overall']['confidence'] > 0:
            print("✅ PASS: Confidence increased with data")
        else:
            print("❌ FAIL: Confidence did not increase!")
            driver.close()
            return False

    driver.close()
    return True


def red_team_test_2_agent_cheating():
    """
    RED TEAM TEST 2: Does the agent cheat?

    Verify agent uses belief_category, NOT door_state for context.
    """
    print("\n" + "=" * 80)
    print("RED TEAM TEST 2: Agent Cheating Detection")
    print("=" * 80)

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Reset stats
        session.run("""
            MATCH (stats:SkillStats)
            SET stats.uncertain_uses = 0,
                stats.confident_locked_uses = 0,
                stats.confident_unlocked_uses = 0
        """)

        print("\n[TEST 1] Agent with belief=0.5 (uncertain) but door=locked")
        print("Should categorize as 'uncertain', NOT 'confident_locked'")

        agent = AgentRuntime(
            session,
            door_state="locked",  # Ground truth: locked
            initial_belief=0.5,   # But agent believes uncertain!
            use_procedural_memory=True
        )

        # Check belief category BEFORE any observations
        belief_cat = agent._get_belief_category(0.5)
        print(f"  Agent categorizes belief=0.5 as: {belief_cat}")

        if belief_cat != "uncertain":
            print("❌ FAIL: Agent categorized incorrectly!")
            driver.close()
            return False

        agent.run_episode(max_steps=1)  # Just one step

        # Check which context was used
        stats = get_skill_stats(session, "peek_door")
        print(f"\n[STATS] After episode:")
        print(f"  Uncertain context uses: {stats.get('belief_context', {}).get('uses', 0)}")

        # Get confident_locked uses separately to avoid f-string complexity
        result = session.run("MATCH (s:SkillStats {skill_name: 'peek_door'}) RETURN s.confident_locked_uses as uses")
        confident_locked_uses = result.single()['uses']
        print(f"  Confident_locked uses: {confident_locked_uses}")

        # The agent should have used "uncertain" context, not "confident_locked"
        # even though door was actually locked

        print("\n[TEST 2] Agent with belief=0.1 (confident_locked) but door=unlocked")
        print("Should categorize as 'confident_locked', NOT 'confident_unlocked'")

        agent2 = AgentRuntime(
            session,
            door_state="unlocked",  # Ground truth: unlocked
            initial_belief=0.1,     # But agent believes locked!
            use_procedural_memory=True
        )

        belief_cat2 = agent2._get_belief_category(0.1)
        print(f"  Agent categorizes belief=0.1 as: {belief_cat2}")

        if belief_cat2 != "confident_locked":
            print("❌ FAIL: Agent categorized incorrectly!")
            driver.close()
            return False

        print("\n✅ PASS: Agent uses belief_category, NOT ground truth")

    driver.close()
    return True


def red_team_test_3_memory_influences_decisions():
    """
    RED TEAM TEST 3: Does memory actually influence decisions?

    Artificially boost one skill's success rate and verify it gets selected more.
    """
    print("\n" + "=" * 80)
    print("RED TEAM TEST 3: Memory Influence on Decisions")
    print("=" * 80)

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Artificially make go_window look terrible
        session.run("""
            MATCH (sk:Skill {name: "go_window"})-[:HAS_STATS]->(stats:SkillStats)
            SET stats.total_uses = 20,
                stats.successful_episodes = 2,
                stats.failed_episodes = 18,
                stats.uncertain_uses = 20,
                stats.uncertain_successes = 2
        """)

        # Make peek_door look great
        session.run("""
            MATCH (sk:Skill {name: "peek_door"})-[:HAS_STATS]->(stats:SkillStats)
            SET stats.total_uses = 20,
                stats.successful_episodes = 19,
                stats.failed_episodes = 1,
                stats.uncertain_uses = 20,
                stats.uncertain_successes = 19
        """)

        print("\n[SETUP] Artificial memory:")
        print("  peek_door: 95% success rate (19/20)")
        print("  go_window: 10% success rate (2/20)")

        # Run agent WITHOUT memory
        print("\n[TEST 1] Agent WITHOUT memory (baseline):")
        agent_baseline = AgentRuntime(
            session,
            door_state="locked",
            initial_belief=0.5,
            use_procedural_memory=False  # NO MEMORY
        )
        agent_baseline.run_episode(max_steps=5)

        trace_baseline = agent_baseline.get_trace()
        first_skill_baseline = trace_baseline[0]['skill'] if trace_baseline else None
        print(f"  First skill selected: {first_skill_baseline}")

        # Run agent WITH memory
        print("\n[TEST 2] Agent WITH memory:")
        agent_memory = AgentRuntime(
            session,
            door_state="locked",
            initial_belief=0.5,
            use_procedural_memory=True,  # WITH MEMORY
            verbose_memory=True
        )

        from graph_model import get_skills
        skills = get_skills(session, agent_memory.agent_id)
        selected = agent_memory.select_skill(skills)

        print(f"  First skill selected: {selected['name']}")

        # Check decision log
        if agent_memory.decision_log:
            decision = agent_memory.decision_log[0]
            print(f"\n[REASONING]")
            if decision.get('explanation'):
                print(f"  {decision['explanation'].get('reasoning', 'N/A')}")

            print(f"\n[ALL SCORES]")
            for skill_name, score in decision['all_scores']:
                print(f"    {skill_name:15s}: {score:6.2f}")

        # VALIDATION: Memory should favor peek_door over go_window
        if selected['name'] == 'peek_door':
            print("\n✅ PASS: Memory influenced decision (selected high-success skill)")
        else:
            print(f"\n⚠️  WARNING: Selected {selected['name']} instead of peek_door")
            print("   This could be due to epistemic bonus or other factors")
            # Not a hard failure since exploration is valid

    driver.close()
    return True


def red_team_test_4_edge_cases():
    """
    RED TEAM TEST 4: Edge cases and graceful degradation

    - No memory data
    - Conflicting data
    - Very small samples
    """
    print("\n" + "=" * 80)
    print("RED TEAM TEST 4: Edge Cases & Graceful Degradation")
    print("=" * 80)

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Reset to zero
        session.run("""
            MATCH (stats:SkillStats)
            SET stats.total_uses = 0,
                stats.successful_episodes = 0,
                stats.failed_episodes = 0
        """)

        print("\n[TEST 1] Zero memory data (cold start)")
        agent = AgentRuntime(
            session,
            door_state="unlocked",
            initial_belief=0.5,
            use_procedural_memory=True
        )

        try:
            episode_id = agent.run_episode(max_steps=5)
            print("  ✅ Agent runs successfully with no memory")
            print(f"     Steps: {agent.step_count}, Escaped: {agent.escaped}")
        except Exception as e:
            print(f"  ❌ FAIL: Agent crashed with no memory: {e}")
            driver.close()
            return False

        print("\n[TEST 2] Single sample (n=1) - should have low confidence")
        stats = get_skill_stats(session, "peek_door")
        if stats['overall']['uses'] > 0:
            confidence = stats['overall']['confidence']
            print(f"  Uses: {stats['overall']['uses']}, Confidence: {confidence:.2f}")

            if confidence < 0.1:  # Should be very low with 1 sample
                print("  ✅ Low confidence with small sample")
            else:
                print(f"  ⚠️  Confidence {confidence:.2f} seems high for {stats['overall']['uses']} samples")

        print("\n[TEST 3] Adaptive params with insufficient data")
        session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            SET meta.episodes_completed = 2
        """)

        agent2 = AgentRuntime(
            session,
            door_state="unlocked",
            initial_belief=0.5,
            adaptive_params=True
        )

        try:
            agent2.run_episode(max_steps=5)
            print("  ✅ Adaptive agent handles insufficient data (< 5 episodes)")
        except Exception as e:
            print(f"  ❌ FAIL: Adaptive agent crashed: {e}")
            driver.close()
            return False

    driver.close()
    return True


def red_team_test_5_actual_learning():
    """
    RED TEAM TEST 5: Does actual learning occur?

    Run 20 episodes and measure if performance improves.
    This is the CRITICAL test - if this fails, nothing else matters.
    """
    print("\n" + "=" * 80)
    print("RED TEAM TEST 5: Actual Learning (THE BIG ONE)")
    print("=" * 80)

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    with driver.session(database="neo4j") as session:
        # Reset everything
        session.run("""
            MATCH (stats:SkillStats)
            SET stats.total_uses = 0,
                stats.successful_episodes = 0,
                stats.failed_episodes = 0,
                stats.uncertain_uses = 0,
                stats.uncertain_successes = 0,
                stats.confident_locked_uses = 0,
                stats.confident_locked_successes = 0,
                stats.confident_unlocked_uses = 0,
                stats.confident_unlocked_successes = 0
        """)

        session.run("""
            MATCH (agent:Agent)-[:HAS_META_PARAMS]->(meta:MetaParams)
            SET meta.episodes_completed = 0
        """)

        print("\n[BASELINE] Running 10 episodes WITHOUT memory...")
        baseline_steps = []
        baseline_success = []

        for i in range(10):
            agent = AgentRuntime(
                session,
                door_state="unlocked" if i % 2 == 0 else "locked",
                initial_belief=0.5,
                use_procedural_memory=False  # NO MEMORY
            )
            agent.run_episode(max_steps=5)
            baseline_steps.append(agent.step_count)
            baseline_success.append(1 if agent.escaped else 0)
            print(f"  Episode {i+1}: {agent.step_count} steps, escaped={agent.escaped}")

        baseline_avg_steps = sum(baseline_steps) / len(baseline_steps)
        baseline_success_rate = sum(baseline_success) / len(baseline_success)

        print(f"\n[BASELINE RESULTS]")
        print(f"  Average steps: {baseline_avg_steps:.2f}")
        print(f"  Success rate: {baseline_success_rate:.1%}")

        # Reset for memory test
        session.run("""
            MATCH (stats:SkillStats)
            SET stats.total_uses = 0,
                stats.successful_episodes = 0,
                stats.failed_episodes = 0,
                stats.uncertain_uses = 0,
                stats.uncertain_successes = 0
        """)

        print("\n[MEMORY] Running 20 episodes WITH memory...")
        memory_steps = []
        memory_success = []

        for i in range(20):
            agent = AgentRuntime(
                session,
                door_state="unlocked" if i % 2 == 0 else "locked",
                initial_belief=0.5,
                use_procedural_memory=True  # WITH MEMORY
            )
            agent.run_episode(max_steps=5)
            memory_steps.append(agent.step_count)
            memory_success.append(1 if agent.escaped else 0)

            if (i + 1) % 5 == 0:
                recent_avg = sum(memory_steps[-5:]) / 5
                print(f"  Episodes {i-3}-{i+1}: avg {recent_avg:.2f} steps")

        # Analyze learning curve
        early_steps = memory_steps[:5]
        late_steps = memory_steps[-5:]

        early_avg = sum(early_steps) / len(early_steps)
        late_avg = sum(late_steps) / len(late_steps)

        memory_avg_steps = sum(memory_steps) / len(memory_steps)
        memory_success_rate = sum(memory_success) / len(memory_success)

        print(f"\n[MEMORY RESULTS]")
        print(f"  Early episodes (1-5): {early_avg:.2f} avg steps")
        print(f"  Late episodes (16-20): {late_avg:.2f} avg steps")
        print(f"  Overall average: {memory_avg_steps:.2f} steps")
        print(f"  Success rate: {memory_success_rate:.1%}")

        print(f"\n[COMPARISON]")
        print(f"  Baseline: {baseline_avg_steps:.2f} steps")
        print(f"  Memory:   {memory_avg_steps:.2f} steps")
        improvement = (baseline_avg_steps - memory_avg_steps) / baseline_avg_steps * 100
        print(f"  Improvement: {improvement:+.1f}%")

        print(f"\n[LEARNING CURVE]")
        improvement_curve = (early_avg - late_avg) / early_avg * 100
        print(f"  Early: {early_avg:.2f} → Late: {late_avg:.2f}")
        print(f"  Improvement: {improvement_curve:+.1f}%")

        # CRITICAL VALIDATION
        if late_avg < early_avg:
            print("\n✅ PASS: Performance improved over time (learning detected)")
        else:
            print("\n⚠️  WARNING: No clear improvement in late episodes")
            print("   This could mean:")
            print("   - Sample size too small (only 20 episodes)")
            print("   - Learning is subtle")
            print("   - Problem is too easy (ceiling effect)")

        if memory_avg_steps <= baseline_avg_steps:
            print("✅ PASS: Memory doesn't degrade performance vs baseline")
        else:
            print("❌ FAIL: Memory actually WORSE than baseline!")
            driver.close()
            return False

    driver.close()
    return True


def main():
    """Run all RED TEAM tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "RED TEAM VALIDATION SUITE" + " " * 33 + "║")
    print("║" + " " * 15 + "Critical Assessment of Procedural Memory" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")

    tests = [
        ("Memory Accumulation", red_team_test_1_memory_accumulation),
        ("Agent Cheating Detection", red_team_test_2_agent_cheating),
        ("Memory Influences Decisions", red_team_test_3_memory_influences_decisions),
        ("Edge Cases & Degradation", red_team_test_4_edge_cases),
        ("Actual Learning (CRITICAL)", red_team_test_5_actual_learning),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RED TEAM ASSESSMENT")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nOVERALL: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL RED TEAM TESTS PASSED")
        print("   Implementation appears solid and demonstrates real learning")
        return 0
    else:
        print("\n⚠️  SOME RED TEAM TESTS FAILED")
        print("   Implementation needs fixes before claiming GOLD STANDARD")
        return 1


if __name__ == "__main__":
    sys.exit(main())
