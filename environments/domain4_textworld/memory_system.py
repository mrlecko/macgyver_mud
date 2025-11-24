"""
Memory Retrieval System for TextWorld Cognitive Agent.

Implements episodic memory retrieval from Neo4j using Cypher queries
to find relevant past experiences that inform current decision-making.
"""
from typing import List, Dict, Any, Optional
import time


class MemoryRetriever:
    """
    Retrieves relevant past experiences (Episodic Memory) to guide current actions.

    Uses Cypher queries against Neo4j to find episodes with similar:
    - Room/location context
    - Action patterns
    - Object interactions

    Balances relevance (similarity) with recency (recent memories weighted higher).
    """

    def __init__(self, session=None, verbose: bool = False):
        """
        Initialize memory retriever.

        Args:
            session: Neo4j session for querying graph database
            verbose: Print debug information
        """
        self.session = session
        self.verbose = verbose

    def retrieve_relevant_memories(self, context: str, action: str,
                                   current_subgoal: str = None,
                                   quest: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to the current context and proposed action.

        NOW QUEST-AWARE (Option B - Phase 1):
        - Filters by current subgoal if provided (hierarchical isolation)
        - Filters by quest similarity if provided
        - Falls back to generic retrieval (backward compatible)

        Strategy:
        1. Extract entities from context (room, objects)
        2. Extract action verb from action
        3. Query Neo4j for similar past episodes (NOW with quest/subgoal filters)
        4. Score by relevance + recency
        5. Return top 3-5 memories

        Args:
            context: Description of current room/state
                    Format: "Current Room: X\nVisible Objects: Y\nInventory: Z"
            action: The action being considered (e.g., "take key")
            current_subgoal: Optional current subgoal for filtering (NEW)
            quest: Optional quest text for similarity matching (NEW)

        Returns:
            List of memory dicts with keys:
            - action: What was done
            - outcome: 'positive', 'negative', or 'neutral'
            - confidence: 0.0-1.0 (relevance * recency)
            - summary: Brief description
            - context: Optional room/situation
        """
        if not self.session:
            if self.verbose:
                print("   ⚠️ No Neo4j session - memory disabled")
            return []

        # Extract entities for matching
        room = self._extract_room_from_context(context)
        action_verb = self._extract_action_verb(action)

        if not action_verb:
            return []  # Can't match without action verb

        try:
            # Query Neo4j for relevant episodes (NOW with quest/subgoal context)
            memories = self._query_similar_episodes(
                room, action_verb, action,
                current_subgoal=current_subgoal,
                quest=quest
            )

            if self.verbose and memories:
                subgoal_info = f" (subgoal: {current_subgoal})" if current_subgoal else ""
                print(f"   💭 Retrieved {len(memories)} memories for '{action}'{subgoal_info}")
                for m in memories:
                    print(f"      - {m['summary']} (conf: {m['confidence']:.2f})")

            return memories

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Memory retrieval error: {e}")
            return []

    def retrieve_quest_episodes(self, quest: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve past episodes for the same or similar quest (episodic memory).

        NEW (Option B - Phase 1): Quest-level memory retrieval for learning
        from past quest attempts.

        Args:
            quest: Quest text to match
            limit: Maximum episodes to return

        Returns:
            List of episode dicts with keys:
            - quest: Quest text
            - success: Boolean
            - total_reward: Final reward
            - step_count: Number of steps taken
            - subgoals_completed: List of subgoals completed
            - confidence: Relevance score
        """
        if not self.session:
            if self.verbose:
                print("   ⚠️ No Neo4j session - memory disabled")
            return []

        try:
            # Extract key tokens from quest for matching
            quest_tokens = set(quest.lower().split())
            stopwords = {'the', 'a', 'an', 'first', 'then', 'finally', 'and', 'or', 'from', 'to', 'in', 'on'}
            quest_tokens_clean = quest_tokens - stopwords

            # Query for episodes with similar quests
            query = """
            MATCH (e:Episode:TextWorldEpisode)
            WHERE e.quest IS NOT NULL
              AND e.timestamp > timestamp() - (30 * 24 * 60 * 60 * 1000)  // Last 30 days
            RETURN e.quest AS quest,
                   e.success AS success,
                   e.total_reward AS total_reward,
                   e.step_count AS step_count,
                   e.subgoals_completed AS subgoals_completed,
                   e.timestamp AS timestamp
            ORDER BY e.timestamp DESC
            LIMIT $limit
            """

            result = self.session.run(query, limit=limit * 2)  # Get more, filter in Python

            episodes = []
            for record in result:
                episode_quest = record['quest']
                if not episode_quest:
                    continue

                # Calculate quest similarity (token overlap)
                episode_tokens = set(episode_quest.lower().split()) - stopwords
                overlap = len(quest_tokens_clean & episode_tokens)
                similarity = overlap / max(len(quest_tokens_clean), 1)

                # Only include if reasonably similar
                if similarity > 0.3:
                    episodes.append({
                        'quest': episode_quest,
                        'success': record['success'],
                        'total_reward': record['total_reward'],
                        'step_count': record['step_count'],
                        'subgoals_completed': record['subgoals_completed'],
                        'confidence': round(similarity, 2)
                    })

            # Sort by confidence and limit
            episodes.sort(key=lambda x: x['confidence'], reverse=True)
            episodes = episodes[:limit]

            if self.verbose and episodes:
                print(f"   💭 Retrieved {len(episodes)} quest episodes")
                for ep in episodes:
                    status = "✅" if ep['success'] else "❌"
                    print(f"      {status} {ep['quest'][:50]}... (conf: {ep['confidence']:.2f})")

            return episodes

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Quest episode retrieval error: {e}")
            return []

    def _extract_room_from_context(self, context: str) -> str:
        """
        Extract room name from context string.

        Args:
            context: Context string with format "Current Room: X\n..."

        Returns:
            Room name or "Unknown"
        """
        if "Current Room:" in context:
            lines = context.split('\n')
            for line in lines:
                if "Current Room:" in line:
                    return line.split("Current Room:")[1].strip()
        return "Unknown"

    def _extract_action_verb(self, action: str) -> str:
        """
        Extract primary verb from action string.

        Args:
            action: Action string (e.g., "take the key")

        Returns:
            Action verb (e.g., "take") or empty string
        """
        if not action:
            return ""

        # Common TextWorld verbs
        verbs = ['take', 'drop', 'examine', 'open', 'close', 'unlock',
                 'lock', 'put', 'insert', 'go', 'eat', 'drink', 'look', 'inventory']

        action_lower = action.lower()
        for verb in verbs:
            if action_lower.startswith(verb):
                return verb

        # Fallback: first word
        return action.split()[0].lower() if action else ""

    def _query_similar_episodes(self, room: str, action_verb: str,
                                full_action: str, limit: int = 5,
                                current_subgoal: str = None,
                                quest: str = None) -> List[Dict[str, Any]]:
        """
        Query Neo4j for episodes with similar context and actions.

        NOW QUEST-AWARE (Option B - Phase 1):
        - Filters by subgoal if provided (hierarchical isolation)
        - Boosts memories from similar quests

        Scoring:
        - Room match: +2 points
        - Action verb match: +2 points
        - Exact action match: +1 point
        - Subgoal match: +3 points (NEW - highest priority)
        - Quest similarity: +1 point (NEW)
        - Recency: decay over 7 days

        Args:
            room: Current room name
            action_verb: Action verb (e.g., "take")
            full_action: Full action string for exact matching
            limit: Maximum memories to return
            current_subgoal: Current subgoal for filtering (NEW)
            quest: Current quest for similarity matching (NEW)

        Returns:
            List of memory dicts sorted by relevance
        """
        # Build query with optional quest/subgoal filters
        # CRITICAL: If subgoal provided, ONLY match memories from that subgoal
        # (hierarchical isolation for memory!)

        if current_subgoal:
            # Quest-aware query: Filter by subgoal
            # CRITICAL for hierarchical isolation:
            # - ONLY match steps where subgoal = current_subgoal OR subgoal IS NULL (legacy)
            # - This automatically EXCLUDES steps with different subgoals
            query = """
            MATCH (e:Episode:TextWorldEpisode)-[:CONTAINS]->(s:Step)
            WHERE (s.room = $room OR s.action CONTAINS $action_verb)
              AND e.timestamp > timestamp() - (14 * 24 * 60 * 60 * 1000)  // Last 14 days
              AND (s.subgoal = $subgoal OR s.subgoal IS NULL)  // Match current subgoal or legacy only
            WITH e, s,
                 CASE WHEN s.room = $room THEN 2 ELSE 0 END +
                 CASE WHEN s.action CONTAINS $action_verb THEN 2 ELSE 0 END +
                 CASE WHEN toLower(s.action) = toLower($full_action) THEN 1 ELSE 0 END +
                 CASE WHEN s.subgoal = $subgoal THEN 3 ELSE 0 END
                 AS relevance_score,
                 (timestamp() - e.timestamp) / (24.0 * 60 * 60 * 1000) AS days_ago
            WHERE relevance_score > 0
            RETURN DISTINCT
                   s.action AS action,
                   s.outcome AS outcome,
                   s.reward AS reward,
                   s.room AS context_room,
                   s.subgoal AS step_subgoal,
                   relevance_score,
                   days_ago,
                   e.success AS episode_success
            ORDER BY relevance_score DESC, days_ago ASC
            LIMIT $limit
            """

            result = self.session.run(
                query,
                room=room,
                action_verb=action_verb,
                full_action=full_action,
                subgoal=current_subgoal,
                limit=limit
            )
        else:
            # Generic query (backward compatible)
            query = """
            MATCH (e:Episode:TextWorldEpisode)-[:CONTAINS]->(s:Step)
            WHERE (s.room = $room OR s.action CONTAINS $action_verb)
              AND e.timestamp > timestamp() - (14 * 24 * 60 * 60 * 1000)  // Last 14 days
            WITH e, s,
                 CASE WHEN s.room = $room THEN 2 ELSE 0 END +
                 CASE WHEN s.action CONTAINS $action_verb THEN 2 ELSE 0 END +
                 CASE WHEN toLower(s.action) = toLower($full_action) THEN 1 ELSE 0 END
                 AS relevance_score,
                 (timestamp() - e.timestamp) / (24.0 * 60 * 60 * 1000) AS days_ago
            WHERE relevance_score > 0
            RETURN DISTINCT
                   s.action AS action,
                   s.outcome AS outcome,
                   s.reward AS reward,
                   s.room AS context_room,
                   null AS step_subgoal,
                   relevance_score,
                   days_ago,
                   e.success AS episode_success
            ORDER BY relevance_score DESC, days_ago ASC
            LIMIT $limit
            """

            result = self.session.run(
                query,
                room=room,
                action_verb=action_verb,
                full_action=full_action,
                limit=limit
            )

        memories = []
        for record in result:
            # Calculate confidence based on relevance and recency
            relevance = record['relevance_score'] / 5.0  # Normalize to 0-1 (max score is 5)
            days_ago = record['days_ago']
            recency = max(0.0, 1.0 - (days_ago / 14.0))  # Decay over 14 days
            confidence = (relevance * 0.7) + (recency * 0.3)  # Weight relevance more

            # Determine outcome
            reward = record['reward']
            if reward is not None:
                if reward > 0:
                    outcome = 'positive'
                elif reward < 0:
                    outcome = 'negative'
                else:
                    outcome = 'neutral'
            else:
                outcome = record['outcome'] if record['outcome'] else 'neutral'

            # Build summary
            context_room = record['context_room'] if record['context_room'] else 'unknown room'
            action_text = record['action']
            reward_text = f"+{reward}" if reward and reward > 0 else str(reward)

            summary = f"In {context_room}, '{action_text}' → {outcome}"
            if reward is not None:
                summary += f" (reward: {reward_text})"

            memories.append({
                'action': action_text,
                'outcome': outcome,
                'confidence': round(confidence, 2),
                'summary': summary,
                'context': context_room
            })

        return memories

    def store_episode(self, episode_data: Dict[str, Any]) -> bool:
        """
        Store episode in Neo4j for future retrieval.

        NOW QUEST-AWARE (Option B - Phase 1): Stores quest and subgoal labels
        for hierarchical memory retrieval.

        This is called by the agent after each episode to build
        the memory database.

        Args:
            episode_data: Dict with keys:
                - episode_id: Unique identifier
                - steps: List of step dicts (action, room, reward, outcome, subgoal)
                - total_reward: Final reward
                - success: Boolean
                - goal: Optional goal string
                - quest: Optional quest text (NEW)
                - subgoals: Optional list of subgoals (NEW)
                - subgoals_completed: Optional list of completed subgoals (NEW)

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.session:
            return False

        try:
            # Create episode node (NOW with quest metadata)
            episode_query = """
            CREATE (e:Episode:TextWorldEpisode {
                id: $id,
                timestamp: timestamp(),
                total_reward: $total_reward,
                success: $success,
                goal: $goal,
                quest: $quest,
                subgoals: $subgoals,
                subgoals_completed: $subgoals_completed,
                step_count: $step_count
            })
            RETURN e.id AS id
            """

            self.session.run(
                episode_query,
                id=episode_data['episode_id'],
                total_reward=episode_data.get('total_reward', 0.0),
                success=episode_data.get('success', False),
                goal=episode_data.get('goal'),
                quest=episode_data.get('quest'),  # NEW
                subgoals=episode_data.get('subgoals'),  # NEW
                subgoals_completed=episode_data.get('subgoals_completed'),  # NEW
                step_count=len(episode_data.get('steps', []))
            )

            # Create step nodes (NOW with subgoal labels)
            for i, step in enumerate(episode_data.get('steps', [])):
                step_query = """
                MATCH (e:Episode {id: $ep_id})
                CREATE (e)-[:CONTAINS]->(s:Step {
                    step_number: $step_num,
                    action: $action,
                    room: $room,
                    reward: $reward,
                    outcome: $outcome,
                    subgoal: $subgoal
                })
                """

                self.session.run(
                    step_query,
                    ep_id=episode_data['episode_id'],
                    step_num=i,
                    action=step.get('action', 'unknown'),
                    room=step.get('room', 'Unknown'),
                    reward=step.get('reward', 0.0),
                    outcome=step.get('outcome', 'neutral'),
                    subgoal=step.get('subgoal')  # NEW
                )

            if self.verbose:
                quest_info = f" quest: {episode_data.get('quest', 'N/A')[:30]}..." if episode_data.get('quest') else ""
                print(f"   💾 Stored episode {episode_data['episode_id']} ({len(episode_data.get('steps', []))} steps){quest_info}")

            return True

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Episode storage error: {e}")
            return False


# Test code
if __name__ == "__main__":
    """Test memory retrieval with mock data."""
    from neo4j import GraphDatabase
    import os

    print("="*70)
    print("MEMORY RETRIEVAL SYSTEM TEST")
    print("="*70)

    # Connect to Neo4j
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:17687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'macgyver_pass')

    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()

    # Create retriever
    retriever = MemoryRetriever(session=session, verbose=True)

    # Test 1: Store a mock episode
    print("\n--- Test 1: Store Episode ---")
    episode = {
        'episode_id': f'test_ep_{int(time.time())}',
        'total_reward': 3.0,
        'success': True,
        'goal': 'Find key and unlock chest',
        'steps': [
            {'action': 'look around', 'room': 'Attic', 'reward': 0.0, 'outcome': 'neutral'},
            {'action': 'take key', 'room': 'Attic', 'reward': 1.0, 'outcome': 'positive'},
            {'action': 'go east', 'room': 'Attic', 'reward': 0.0, 'outcome': 'neutral'},
            {'action': 'unlock chest with key', 'room': 'Bedroom', 'reward': 2.0, 'outcome': 'positive'},
        ]
    }

    stored = retriever.store_episode(episode)
    print(f"Stored: {stored}")

    # Test 2: Retrieve memories
    print("\n--- Test 2: Retrieve Memories ---")
    context = "Current Room: Bedroom\nVisible Objects: chest, bed\nInventory: empty"
    action = "unlock chest with key"

    memories = retriever.retrieve_relevant_memories(context, action)

    print(f"\nRetrieved {len(memories)} memories:")
    for i, mem in enumerate(memories, 1):
        print(f"{i}. {mem['summary']}")
        print(f"   Outcome: {mem['outcome']}, Confidence: {mem['confidence']}")

    # Cleanup
    session.close()
    driver.close()

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
