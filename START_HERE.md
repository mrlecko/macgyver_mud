# 🚀 START HERE - MacGyver MUD Notebook v2.0

## What Is This?

An interactive Jupyter notebook teaching Active Inference through a locked-door escape scenario.

**Duration**: 45-60 minutes
**Level**: Beginner friendly
**Key Insight**: The k≈0 geometric balance principle

---

## Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install jupyter numpy pandas matplotlib networkx ipywidgets neo4j scipy seaborn plotly
```

### 2. (Optional) Start Neo4j
```bash
make neo4j-start
# OR: Skip this - notebook works fine without it
```

### 3. Run the Notebook
```bash
jupyter notebook MacGyverMUD_Essentials.ipynb
```

**Then run cells in order from top to bottom.**

---

## Files You Need

### Use These ⭐
```
MacGyverMUD_Essentials.ipynb  # Main notebook - RUN THIS
macgyver_utils.py             # Helper code (auto-imported)
NOTEBOOK_README_V2.md         # Full documentation
```

### Ignore These (Legacy)
```
MacGyverMUD_DeepDive.ipynb    # Old 89-cell version (too long)
NOTEBOOK_README.md            # Old documentation
FINAL_RED_TEAM_HONEST.md      # Review that led to v2
build_notebook_*.py           # Build scripts (not needed)
```

---

## What You'll Learn

1. **Active Inference** - How agents make decisions under uncertainty
2. **Expected Free Energy** - The decision-making formula
3. **Bayesian Updates** - How beliefs change with evidence
4. **Silver Gauge (k≈0)** - Geometric balance between explore/exploit

---

## The Key Insight (Part 4)

> **⚠️ Note**: See [ERRATA.md](ERRATA.md) - k≈0 is a design property, not natural emergence.

The notebook builds to a climax around minute 42:

**All deliberately designed simple skills have k≈0 (by construction)!**

This shows that both exploration AND exploitation can be specialists (just in opposite directions). The k-coefficient measures specialist vs generalist, not explore vs exploit.

This observation motivates the complementary multi-objective skill design.

---

## Troubleshooting

### "Neo4j connection failed"
**This is fine!** Notebook uses fallback data. You'll still learn everything.

### "Widget not displaying"
```bash
jupyter nbextension enable --py widgetsnbextension
```

### "Can't import macgyver_utils"
Make sure `macgyver_utils.py` is in the same folder as the notebook.

---

## Time Budget

| Part | Time | What |
|------|------|------|
| 0-1 | 15 min | Setup + scenario |
| 2 | 15 min | Expected Free Energy |
| 3 | 12 min | Bayesian updates |
| 4 ⭐ | 20 min | **The key insight** |
| 5 | 8 min | Explore & next steps |

**Only have 30 minutes?**
- Run cells 1-25 (basics)
- Jump to cells 36-48 (key insight)

---

## After You Finish

### Want More?
- Read `FINAL_REPORT.md` - Comprehensive analysis
- See `examples/blended_skills.py` - Advanced skills
- Run `python runner.py` - Execute the agent

### Questions?
- See `NOTEBOOK_README_V2.md` - Full documentation
- See `V2_SUMMARY.md` - Implementation details

---

## Why v2?

v1 was **89 cells** and took **2-3 hours**. Too long.

v2 is **54 cells** and takes **45-60 min**. Just right.

Same insights, half the time, cleaner code.

---

**Ready? Open `MacGyverMUD_Essentials.ipynb` and let's go!** 🎓
