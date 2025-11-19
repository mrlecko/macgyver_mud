# MacGyver MUD: Interactive Active Inference Notebook

**Learn Active Inference through an interactive locked-door escape scenario.**

**Duration**: 45-60 minutes | **Level**: Beginner to Intermediate | **Format**: Jupyter Notebook with widgets

---

## What You'll Learn

By the end of this notebook, you'll understand:

1. **Active Inference Basics** - How agents balance beliefs, observations, and actions
2. **Expected Free Energy (EFE)** - The core decision-making metric
3. **Bayesian Belief Updates** - How observations change beliefs
4. **The Silver Gauge (k≈0)** - A geometric approach to balancing exploration vs exploitation

### The Core Insight

The notebook builds to a key revelation: **when k≈0**, exploration and exploitation are perfectly balanced. This uses Pythagorean means (HM ≤ GM ≤ AM) to create a principled balance coefficient.

---

## Quick Start

### Prerequisites

```bash
# Python 3.8+
pip install jupyter numpy pandas matplotlib networkx ipywidgets neo4j scipy seaborn plotly
```

### Optional: Neo4j (for graph visualizations)

```bash
# Start Neo4j (requires Docker)
make neo4j-start

# Or manually:
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/macgyver123 \
  neo4j:latest
```

**Note**: The notebook works fine without Neo4j (uses fallback data).

### Run the Notebook

```bash
jupyter notebook MacGyverMUD_Essentials.ipynb
```

Then run cells sequentially from top to bottom.

---

## Notebook Structure

| Part | Cells | Duration | What You'll Learn |
|------|-------|----------|-------------------|
| **0: Setup** | 5 | 5 min | Imports, Neo4j connection, introduction |
| **1: The Scenario** | 9 | 10 min | MacGyver MUD, beliefs, skills, checkpoints 1-2 |
| **2: Expected Free Energy** | 11 | 15 min | EFE formula, calculator, comparisons, checkpoint 3 |
| **3: Bayesian Updates** | 10 | 12 min | Update mechanics, simulator, episodes, checkpoint 4 |
| **4: Silver Gauge ⭐** | 13 | 20 min | Pythagorean means, k≈0 revelation, checkpoint 5 |
| **5: Explore** | 6 | 8 min | Neo4j playground, next steps, resources |
| **TOTAL** | **54** | **~60 min** | Complete Active Inference understanding |

### Part 4 is the climax

- The k≈0 insight
- Geometric balance coefficient
- **This is the key pedagogical moment**

---

## Features

### Interactive Widgets (13 total)
- Belief sliders with live recommendations
- EFE calculator
- Bayesian update simulator
- Pythagorean means calculator
- Neo4j query playground
- k-coefficient design challenge

### Visualizations
- NetworkX graph of state space
- Matplotlib belief distributions
- 3-panel Bayesian update diagrams
- Skill comparison charts
- Pythagorean means inequality plots

### Checkpoints (5 total)
1. First action decision
2. Skill scoring mechanics
3. EFE calculation
4. Bayesian posterior calculation
5. k-coefficient design challenge

---

## Key Files

```
macgyver_mud/
├── MacGyverMUD_Essentials.ipynb  # Main notebook (START HERE)
├── macgyver_utils.py             # Helper functions and widgets
├── NOTEBOOK_README_V2.md         # This file
└── data/
    └── kb_macgyver.json          # Knowledge base (for Neo4j)
```

---

## Usage Tips

### First Time Through
1. Run all cells in order (don't skip)
2. Interact with every widget
3. Answer all checkpoints
4. Read the markdown explanations
5. Focus on Part 4 (the revelation)

### If You Only Have 30 Minutes
1. Run cells 1-25 (Parts 0-2) - Basics
2. **Jump to cells 36-48 (Part 4)** - The Silver Gauge revelation
3. This gives you the core insight

### Going Deeper
- Complete Part 5 Neo4j playground
- Read the collapsed detail sections
- See `FINAL_REPORT.md` for full analysis

---

## Troubleshooting

### Neo4j Connection Failed

**This is OK!** The notebook uses fallback data. You'll still learn everything, just without interactive graph visualizations.

To fix (optional):
```bash
docker ps | grep neo4j          # Check if running
make neo4j-start                # Start if needed
# Restart notebook kernel and re-run setup cells
```

### Widget Not Displaying

```bash
jupyter nbextension enable --py widgetsnbextension
# Restart Jupyter
```

### Import Error: macgyver_utils

Make sure `macgyver_utils.py` is in the same directory as the notebook.

---

## Comparison to v1

| Metric | v1 (DeepDive) | v2 (Essentials) | Improvement |
|--------|---------------|-----------------|-------------|
| Cells | 89 | 54 | 39% shorter |
| Duration | 2-3 hours | 45-60 min | 50% faster |
| Code complexity | 32 cells >1000 chars | 0 cells >1000 chars | Much cleaner |
| Documentation | 12 files | 3 files | 75% simpler |
| Core value | Same | Same | **Maintained** |

**Bottom line**: Same insights, half the time, cleaner code.

---

## Learning Outcomes

After completing this notebook, you'll be able to:

- ✅ Explain Active Inference in simple terms
- ✅ Calculate Expected Free Energy for actions
- ✅ Perform Bayesian belief updates
- ✅ Understand exploration vs exploitation trade-offs
- ✅ Apply the Silver Gauge k≈0 principle
- ✅ Recognize when Pythagorean means reveal balance

---

## Next Steps

### Want More?
- **Advanced scenarios** - See `examples/blended_skills.py`
- **Memory systems** - See `examples/memory_integration.py`
- **Full documentation** - See project `README.md`
- **Deep analysis** - See `FINAL_REPORT.md`

### Apply It
- Try different scenarios
- Implement Active Inference in your projects
- Experiment with k-coefficients
- Explore Neo4j graphs

### Go Deeper
- Active Inference papers (see Resources below)
- Pythagorean means mathematics
- Implement your own EFE calculations
- Design new balance coefficients

---

## Resources

### Active Inference
- [Parr, Pezzulo, & Friston (2022)](https://mitpress.mit.edu/9780262045353/) - Active Inference textbook
- [FreeEnergyPrinciple.org](https://www.freeenergyprinciple.org/) - Community resources

### Pythagorean Means
- [Wikipedia: Pythagorean Means](https://en.wikipedia.org/wiki/Pythagorean_means)
- AM-GM Inequality applications

### Neo4j
- [Neo4j Graph Academy](https://graphacademy.neo4j.com/) - Free courses
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

---

## Credits

**Created by**: Human-AI collaboration
**Framework**: Parr, Pezzulo, & Friston (Active Inference)
**Key Contribution**: Silver Gauge k≈0 geometric balance metric
**License**: MIT

---

## Feedback & Contributions

- **Issues**: Open an issue in the project repo
- **Questions**: See troubleshooting above
- **Contributions**: PRs welcome

---

## Version History

### v2.0 - Essentials (Current)
- 54 cells (down from 89)
- Extracted code to `macgyver_utils.py`
- Single clean README
- Improved pedagogical flow
- 5 interactive checkpoints

### v1.0 - DeepDive
- 89 cells, all code inline
- 12 documentation files
- Complete but verbose

---

**Ready to learn? Open `MacGyverMUD_Essentials.ipynb` and let's go!** 🚀
