// ============================================================
// BALANCED SKILLS: Multi-Objective Trade-off Demonstration
// ============================================================
//
// This script adds "balanced" variants of skills that provide
// BOTH goal value AND information gain, creating genuine
// multi-objective trade-offs with k_explore ∈ [0.3, 0.7]
//
// These complement the existing "crisp" skills (pure specialists)
// to demonstrate the difference in geometric signatures.
//

// --- Add Balanced Skills ---

// 1. "probe_and_try" - Cautious door approach
//    - Provides SOME information (minor peek effect)
//    - Provides SOME goal value (attempted opening)
//    - Cost: 2.0 (more expensive than peek alone)
CREATE (s1:Skill {
    name: "probe_and_try",
    description: "Carefully examine door while attempting to open it",
    cost: 2.0,
    kind: "balanced",
    // Custom fields for balanced scoring
    goal_fraction: 0.6,      // 60% of try_door's goal value
    info_fraction: 0.4,      // 40% of peek_door's info gain
    created_at: datetime()
});

// 2. "informed_window" - Strategic window escape
//    - Quick glance at door state (some info)
//    - Then use window (guaranteed escape)
//    - Cost: 2.2 (slightly more than pure window)
CREATE (s2:Skill {
    name: "informed_window",
    description: "Quickly check door state before using window",
    cost: 2.2,
    kind: "balanced",
    goal_fraction: 0.8,      // 80% of go_window's goal value
    info_fraction: 0.3,      // 30% of peek_door's info gain
    created_at: datetime()
});

// 3. "exploratory_action" - Multi-tool approach
//    - Try multiple approaches simultaneously
//    - High information AND high goal potential
//    - Cost: 2.5 (expensive but powerful)
CREATE (s3:Skill {
    name: "exploratory_action",
    description: "Systematically test multiple escape routes",
    cost: 2.5,
    kind: "balanced",
    goal_fraction: 0.7,      // 70% of try_door's goal value
    info_fraction: 0.7,      // 70% of peek_door's info gain
    created_at: datetime()
});

// 4. "adaptive_peek" - Partial commitment peek
//    - More than just looking, less than full attempt
//    - Balanced exploration and goal-seeking
//    - Cost: 1.3 (between peek and try)
CREATE (s4:Skill {
    name: "adaptive_peek",
    description: "Examine door with partial attempt to open",
    cost: 1.3,
    kind: "balanced",
    goal_fraction: 0.4,      // 40% of try_door's goal value
    info_fraction: 0.6,      // 60% of peek_door's info gain
    created_at: datetime()
});

// --- Create SkillStats for each balanced skill ---
MATCH (s:Skill) WHERE s.kind = "balanced"
CREATE (stats:SkillStats {
    skill_name: s.name,
    times_used: 0,
    times_succeeded: 0,
    avg_reward: 0.0,
    created_at: datetime()
})
CREATE (s)-[:HAS_STATS]->(stats);

// --- Add observations for balanced skills ---

// Balanced observations (partial information)
CREATE (o1:Observation {
    name: "obs_partial_info",
    description: "Door appears to be in uncertain state",
    created_at: datetime()
});

CREATE (o2:Observation {
    name: "obs_attempted_open",
    description: "Door was tested but outcome unclear",
    created_at: datetime()
});

CREATE (o3:Observation {
    name: "obs_strategic_escape",
    description: "Escaped after gathering some information",
    created_at: datetime()
});

// Link balanced skills to possible observations
MATCH (s:Skill {name: "probe_and_try"}), (o:Observation)
WHERE o.name IN ["obs_door_opened", "obs_door_stuck", "obs_partial_info"]
CREATE (s)-[:MAY_OBSERVE]->(o);

MATCH (s:Skill {name: "informed_window"}), (o:Observation)
WHERE o.name IN ["obs_window_escape", "obs_partial_info"]
CREATE (s)-[:MAY_OBSERVE]->(o);

MATCH (s:Skill {name: "exploratory_action"}), (o:Observation)
WHERE o.name IN ["obs_door_opened", "obs_window_escape", "obs_partial_info", "obs_attempted_open"]
CREATE (s)-[:MAY_OBSERVE]->(o);

MATCH (s:Skill {name: "adaptive_peek"}), (o:Observation)
WHERE o.name IN ["obs_door_locked", "obs_door_unlocked", "obs_partial_info", "obs_attempted_open"]
CREATE (s)-[:MAY_OBSERVE]->(o);

// --- Summary ---
MATCH (s:Skill) WHERE s.kind = "balanced"
RETURN s.name AS skill, s.cost AS cost,
       s.goal_fraction AS goal_frac, s.info_fraction AS info_frac
ORDER BY s.cost;
