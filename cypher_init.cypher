// ============================================================================
// MacGyver Active Inference Demo - Graph Initialization
// ============================================================================
// This script creates the initial knowledge graph for the locked room scenario.
// Run with: cypher-shell -u neo4j -p password --encryption=false -f cypher_init.cypher

// ----------------------------------------------------------------------------
// 1. Clear existing data (for clean slate)
// ----------------------------------------------------------------------------
MATCH (n) DETACH DELETE n;

// ----------------------------------------------------------------------------
// 2. Create core world entities
// ----------------------------------------------------------------------------

// Create the agent
CREATE (agent:Agent {
  name: "MacGyverBot",
  created_at: datetime()
});

// Create the room
CREATE (room:Place {
  name: "Room A",
  description: "A locked room with a door and a window"
});

// Create objects in the room
CREATE (door:Object {
  name: "Door",
  type: "door",
  can_peek: true,
  description: "A door that might be locked or unlocked"
});

CREATE (window:Object {
  name: "Window",
  type: "window",
  always_escape: true,
  description: "A window that can always be used to escape, but is slow"
});

// Create state variable (represents hidden state)
CREATE (doorLockState:StateVar {
  name: "DoorLockState",
  domain: ["locked", "unlocked"],
  description: "Whether the door is currently locked or unlocked"
});

// Create initial belief (agent's uncertainty about door state)
CREATE (belief:Belief {
  p_unlocked: 0.5,
  last_updated: datetime(),
  description: "Agent's belief about door lock state"
});

// ----------------------------------------------------------------------------
// 3. Create skill/action definitions
// ----------------------------------------------------------------------------

CREATE (peekDoor:Skill {
  name: "peek_door",
  kind: "sense",
  cost: 1.0,
  description: "Look at the door to see if it's locked"
});

CREATE (tryDoor:Skill {
  name: "try_door",
  kind: "act",
  cost: 1.5,
  description: "Try to open the door and escape"
});

CREATE (goWindow:Skill {
  name: "go_window",
  kind: "act",
  cost: 2.0,
  description: "Go to the window and escape (always works, but slower)"
});

// ----------------------------------------------------------------------------
// 4. Create procedural memory: SkillStats for learning
// ----------------------------------------------------------------------------

// Create SkillStats nodes for tracking empirical performance
MATCH (peekDoor:Skill {name: "peek_door"})
CREATE (peekStats:SkillStats {
  skill_name: "peek_door",
  total_uses: 0,
  successful_episodes: 0,
  failed_episodes: 0,
  avg_steps_when_successful: 0.0,
  avg_steps_when_failed: 0.0,

  // Context-specific stats: belief state
  uncertain_uses: 0,
  uncertain_successes: 0,
  confident_locked_uses: 0,
  confident_locked_successes: 0,
  confident_unlocked_uses: 0,
  confident_unlocked_successes: 0,

  created_at: datetime(),
  last_updated: datetime()
})
CREATE (peekDoor)-[:HAS_STATS]->(peekStats);

MATCH (tryDoor:Skill {name: "try_door"})
CREATE (tryStats:SkillStats {
  skill_name: "try_door",
  total_uses: 0,
  successful_episodes: 0,
  failed_episodes: 0,
  avg_steps_when_successful: 0.0,
  avg_steps_when_failed: 0.0,

  uncertain_uses: 0,
  uncertain_successes: 0,
  confident_locked_uses: 0,
  confident_locked_successes: 0,
  confident_unlocked_uses: 0,
  confident_unlocked_successes: 0,

  created_at: datetime(),
  last_updated: datetime()
})
CREATE (tryDoor)-[:HAS_STATS]->(tryStats);

MATCH (goWindow:Skill {name: "go_window"})
CREATE (windowStats:SkillStats {
  skill_name: "go_window",
  total_uses: 0,
  successful_episodes: 0,
  failed_episodes: 0,
  avg_steps_when_successful: 0.0,
  avg_steps_when_failed: 0.0,

  uncertain_uses: 0,
  uncertain_successes: 0,
  confident_locked_uses: 0,
  confident_locked_successes: 0,
  confident_unlocked_uses: 0,
  confident_unlocked_successes: 0,

  created_at: datetime(),
  last_updated: datetime()
})
CREATE (goWindow)-[:HAS_STATS]->(windowStats);

// ----------------------------------------------------------------------------
// 5. Create meta-learning: MetaParams for adaptive agent
// ----------------------------------------------------------------------------

// Create MetaParams for tracking and adapting exploration/exploitation
MATCH (agent:Agent {name: "MacGyverBot"})
CREATE (meta:MetaParams {
  // Current parameters
  alpha: 1.0,
  beta: 6.0,
  gamma: 0.3,

  // Parameter history (for tracking adaptation)
  alpha_history: [1.0],
  beta_history: [6.0],
  gamma_history: [0.3],

  // Learning metrics
  episodes_completed: 0,
  avg_steps_last_10: 0.0,
  success_rate_last_10: 0.0,

  // Adaptation settings
  adaptation_enabled: true,
  min_episodes_before_adapt: 5,
  adapt_frequency: 5,

  created_at: datetime(),
  last_adapted: datetime()
})
CREATE (agent)-[:HAS_META_PARAMS]->(meta);

// ----------------------------------------------------------------------------
// 6. Create observation types
// ----------------------------------------------------------------------------

CREATE (obsLocked:Observation {
  name: "obs_door_locked",
  description: "Observed that the door is locked"
});

CREATE (obsUnlocked:Observation {
  name: "obs_door_unlocked",
  description: "Observed that the door is unlocked"
});

CREATE (obsDoorOpened:Observation {
  name: "obs_door_opened",
  description: "Successfully opened the door and escaped"
});

CREATE (obsDoorStuck:Observation {
  name: "obs_door_stuck",
  description: "Tried the door but it was stuck/locked"
});

CREATE (obsWindowEscape:Observation {
  name: "obs_window_escape",
  description: "Escaped via the window"
});

// ----------------------------------------------------------------------------
// 7. Create relationships - World structure
// ----------------------------------------------------------------------------

MATCH (agent:Agent {name: "MacGyverBot"})
MATCH (room:Place {name: "Room A"})
MATCH (door:Object {name: "Door"})
MATCH (window:Object {name: "Window"})
CREATE (agent)-[:LOCATED_IN]->(room),
       (door)-[:LOCATED_IN]->(room),
       (window)-[:LOCATED_IN]->(room);

// ----------------------------------------------------------------------------
// 8. Create relationships - Belief structure
// ----------------------------------------------------------------------------

MATCH (agent:Agent {name: "MacGyverBot"})
MATCH (belief:Belief)
MATCH (doorLockState:StateVar {name: "DoorLockState"})
CREATE (agent)-[:HAS_BELIEF]->(belief),
       (belief)-[:ABOUT]->(doorLockState);

// ----------------------------------------------------------------------------
// 9. Create relationships - Skill semantics
// ----------------------------------------------------------------------------

MATCH (peekDoor:Skill {name: "peek_door"})
MATCH (tryDoor:Skill {name: "try_door"})
MATCH (goWindow:Skill {name: "go_window"})
MATCH (door:Object {name: "Door"})
MATCH (window:Object {name: "Window"})
CREATE (peekDoor)-[:ACTS_ON]->(door),
       (tryDoor)-[:ACTS_ON]->(door),
       (goWindow)-[:ACTS_ON]->(window);

// ----------------------------------------------------------------------------
// 10. Create indexes for performance
// ----------------------------------------------------------------------------

CREATE INDEX agent_name IF NOT EXISTS FOR (a:Agent) ON (a.name);
CREATE INDEX skill_name IF NOT EXISTS FOR (s:Skill) ON (s.name);
CREATE INDEX observation_name IF NOT EXISTS FOR (o:Observation) ON (o.name);
CREATE INDEX episode_id IF NOT EXISTS FOR (e:Episode) ON (e.id);
CREATE INDEX skill_stats_name IF NOT EXISTS FOR (ss:SkillStats) ON (ss.skill_name);

// ----------------------------------------------------------------------------
// 11. Return summary
// ----------------------------------------------------------------------------

MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY NodeType;
