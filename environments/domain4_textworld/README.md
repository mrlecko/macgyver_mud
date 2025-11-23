# Domain 4: TextWorld Integration

This folder contains the TextWorld (Interactive Fiction) integration for multi-domain validation.

## Purpose

TextWorld is **THE PERFECT FIT** for this architecture because it demonstrates:
- ✅ **Graph-based reasoning** - Rooms, objects, relationships (Neo4j native!)
- ✅ **Skill composition** - "take key → go north → unlock door"
- ✅ **Multi-step planning** - Quests require sequences
- ✅ **Episodic memory** - "What if I examined the painting first?"
- ✅ **Counterfactual learning** - Offline reasoning about alternatives
- ✅ **Natural language** - Interpretable actions and states
- ✅ **Symbolic knowledge** - "key unlocks door" (knowledge graphs!)

## Why TextWorld Over CartPole

**CartPole tests:** Continuous dynamics only (already proven by Labyrinth)  
**TextWorld tests:** Graph reasoning, planning, episodic memory, skills - **ALL core features!**

## Files

- `test_textworld_setup.py` - Verification test (6 tests)
- `graph_schema.py` - (Coming) Neo4j schema for game world
- `textworld_adapter.py` - (Coming) Adapter for Critical State integration
- `textworld_agent.py` - (Coming) Agent with protocols

## Quick Start

1. **Verify TextWorld works:**
   ```bash
   python3 environments/domain4_textworld/test_textworld_setup.py
   ```

2. **Follow implementation plan:**
   See `TEXTWORLD_IMPLEMENTATION_PLAN.md` in project root

## Integration Status

- [x] TextWorld installed
- [x] Setup test created
- [x] Implementation plan complete
- [ ] Graph schema designed
- [ ] Adapter created
- [ ] Critical state mapping done
- [ ] Agents implemented
- [ ] Tests added
- [ ] Validation completed

## What Makes This Domain Special

Unlike CartPole (which doesn't use graphs, skills, or planning), TextWorld:
- **Uses Neo4j naturally** - Game world IS a graph
- **Tests skill system** - Actions map to named skills
- **Enables counterfactuals** - "What if I went left instead?"
- **Shows transfer learning** - Same protocols, different quests
- **Is interpretable** - Natural language everything

**This showcases what makes the architecture unique.**
