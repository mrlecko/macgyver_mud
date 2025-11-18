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
// 4. Create observation types
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
// 5. Create relationships - World structure
// ----------------------------------------------------------------------------

MATCH (agent:Agent {name: "MacGyverBot"})
MATCH (room:Place {name: "Room A"})
MATCH (door:Object {name: "Door"})
MATCH (window:Object {name: "Window"})
CREATE (agent)-[:LOCATED_IN]->(room),
       (door)-[:LOCATED_IN]->(room),
       (window)-[:LOCATED_IN]->(room);

// ----------------------------------------------------------------------------
// 6. Create relationships - Belief structure
// ----------------------------------------------------------------------------

MATCH (agent:Agent {name: "MacGyverBot"})
MATCH (belief:Belief)
MATCH (doorLockState:StateVar {name: "DoorLockState"})
CREATE (agent)-[:HAS_BELIEF]->(belief),
       (belief)-[:ABOUT]->(doorLockState);

// ----------------------------------------------------------------------------
// 7. Create relationships - Skill semantics
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
// 8. Create indexes for performance
// ----------------------------------------------------------------------------

CREATE INDEX agent_name IF NOT EXISTS FOR (a:Agent) ON (a.name);
CREATE INDEX skill_name IF NOT EXISTS FOR (s:Skill) ON (s.name);
CREATE INDEX observation_name IF NOT EXISTS FOR (o:Observation) ON (o.name);
CREATE INDEX episode_id IF NOT EXISTS FOR (e:Episode) ON (e.id);

// ----------------------------------------------------------------------------
// 9. Return summary
// ----------------------------------------------------------------------------

MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY NodeType;
