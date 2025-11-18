// ============================================================================
// MacGyver Active Inference Demo - Showcase Queries
// ============================================================================
// Use these queries in Neo4j Browser to explore the knowledge graph
// Browser URL: http://localhost:17474

// ----------------------------------------------------------------------------
// 1. View the entire world structure
// ----------------------------------------------------------------------------
// Shows: Agent, Room, Objects, Skills, and their relationships
MATCH (n)
WHERE n:Agent OR n:Place OR n:Object OR n:Skill
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;

// ----------------------------------------------------------------------------
// 2. View all episodes (memory)
// ----------------------------------------------------------------------------
// Shows: All episodes with their outcomes
MATCH (e:Episode)
RETURN e.id AS episode_id,
       e.door_state AS ground_truth,
       e.escaped AS escaped,
       e.total_steps AS steps,
       e.created_at AS timestamp
ORDER BY e.created_at DESC;

// ----------------------------------------------------------------------------
// 3. View latest episode trace
// ----------------------------------------------------------------------------
// Shows: Full trace of most recent episode with belief evolution
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH (e)-[:HAS_STEP]->(s:Step)
MATCH (s)-[:USED_SKILL]->(sk:Skill)
MATCH (s)-[:OBSERVED]->(o:Observation)
RETURN s.step_index AS step,
       sk.name AS skill,
       o.name AS observation,
       s.p_before AS belief_before,
       s.p_after AS belief_after,
       (s.p_after - s.p_before) AS belief_change
ORDER BY s.step_index;

// ----------------------------------------------------------------------------
// 4. Visualize episode as graph
// ----------------------------------------------------------------------------
// Shows: Episode flow as a visual graph
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH path = (e)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
MATCH (s)-[:OBSERVED]->(o:Observation)
RETURN path, o;

// ----------------------------------------------------------------------------
// 5. Compare different episodes
// ----------------------------------------------------------------------------
// Shows: Side-by-side comparison of locked vs unlocked scenarios
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 2
MATCH (e)-[:HAS_STEP]->(s:Step)-[:USED_SKILL]->(sk:Skill)
RETURN e.door_state AS scenario,
       collect(sk.name) AS skill_sequence,
       e.total_steps AS steps,
       e.escaped AS escaped
ORDER BY e.created_at DESC;

// ----------------------------------------------------------------------------
// 6. Skill usage statistics
// ----------------------------------------------------------------------------
// Shows: How often each skill was used and in what contexts
MATCH (s:Step)-[:USED_SKILL]->(sk:Skill)
RETURN sk.name AS skill,
       count(s) AS times_used,
       avg(s.p_before) AS avg_belief_when_used,
       collect(DISTINCT s.p_before) AS belief_values
ORDER BY times_used DESC;

// ----------------------------------------------------------------------------
// 7. Belief evolution patterns
// ----------------------------------------------------------------------------
// Shows: How beliefs changed over all episodes
MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
RETURN e.id AS episode,
       s.step_index AS step,
       s.p_before AS belief_before,
       s.p_after AS belief_after,
       CASE
         WHEN s.p_after > s.p_before THEN 'increased'
         WHEN s.p_after < s.p_before THEN 'decreased'
         ELSE 'unchanged'
       END AS belief_direction
ORDER BY e.created_at, s.step_index;

// ----------------------------------------------------------------------------
// 8. Successful vs failed escape attempts
// ----------------------------------------------------------------------------
// Shows: Success rate by door state
MATCH (e:Episode)
RETURN e.door_state AS scenario,
       count(e) AS total_episodes,
       sum(CASE WHEN e.escaped THEN 1 ELSE 0 END) AS successful,
       avg(e.total_steps) AS avg_steps
GROUP BY e.door_state;

// ----------------------------------------------------------------------------
// 9. Information gain analysis
// ----------------------------------------------------------------------------
// Shows: Which observations provided most information
MATCH (s:Step)-[:OBSERVED]->(o:Observation)
WHERE s.p_before <> s.p_after
RETURN o.name AS observation,
       count(s) AS times_observed,
       avg(abs(s.p_after - s.p_before)) AS avg_belief_change,
       max(abs(s.p_after - s.p_before)) AS max_belief_change
ORDER BY avg_belief_change DESC;

// ----------------------------------------------------------------------------
// 10. Agent decision tree (most recent episode)
// ----------------------------------------------------------------------------
// Shows: Decision path with belief states
MATCH (e:Episode)
WITH e ORDER BY e.created_at DESC LIMIT 1
MATCH (e)-[:HAS_STEP]->(s:Step)
MATCH (s)-[:USED_SKILL]->(sk:Skill)
MATCH (s)-[:OBSERVED]->(o:Observation)
RETURN s.step_index AS step,
       'p=' + toString(round(s.p_before * 100) / 100.0) AS belief_state,
       sk.name AS chosen_skill,
       o.name AS result,
       'p=' + toString(round(s.p_after * 100) / 100.0) AS new_belief
ORDER BY s.step_index;

// ----------------------------------------------------------------------------
// 11. Clear all episodes (reset for new demo)
// ----------------------------------------------------------------------------
// WARNING: This deletes all episode data!
// Uncomment to use:
// MATCH (s:Step) DETACH DELETE s;
// MATCH (e:Episode) DETACH DELETE e;
// MATCH (a:Agent)-[:HAS_BELIEF]->(b:Belief)
// SET b.p_unlocked = 0.5;

// ----------------------------------------------------------------------------
// 12. Full graph overview (everything)
// ----------------------------------------------------------------------------
// Shows: Complete graph including episodes
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 200;
