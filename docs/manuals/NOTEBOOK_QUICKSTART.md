# Interactive Notebook Quick Start

## 🚀 5-Minute Launch Guide

### Step 1: Start Neo4j
```bash
make neo4j-start
```
Wait ~10 seconds for Neo4j to start.

### Step 2: Initialize Database
```bash
make init
make init-balanced
```

### Step 3: Install Jupyter (if needed)
```bash
pip install jupyter ipywidgets
```

### Step 4: Launch Notebook
```bash
make notebook
```

The notebook will open in your browser automatically!

---

## 📖 What to Expect

### Part 0-1: Setup & Problem (15 min)
- Connect to database ✓
- See the locked room scenario
- Interactive quizzes and sliders
- Build intuition

### Part 2: The Math (20 min)
- Expected Free Energy formula
- Interactive EFE calculator
- Real-time skill scoring
- Decision boundary plots

### Part 4: THE REVELATION ⭐ (25 min)
**This is the climax!**
- Pythagorean means calculator
- Apply Silver Gauge to skills
- **Discover**: k≈0 for ALL skills!
- Geometric gap visualization
- Design your own balanced skill

### Part 5: The Solution (20 min)
- Meet balanced skills
- See k ∈ [0.85, 1.00]
- Complete geometric spectrum
- Gap filled!

**Total: ~80 minutes (or pace yourself across sessions)**

---

## 💡 Quick Tips

### First Time?
1. **Choose "Computational"** learning path (good balance)
2. **Read every markdown cell** (context matters!)
3. **Run cells in order** (top to bottom)
4. **Play with sliders** (interactive = fun!)

### Stuck?
- **Kernel died?** → Kernel → Restart & Clear Output
- **Neo4j error?** → Check `make neo4j-status`
- **Import error?** → Install missing library
- **Widget not working?** → Reload page

### Want More?
- **Full guide**: `NOTEBOOK_README.md`
- **Design doc**: `NOTEBOOK_DESIGN.md`
- **Project docs**: `README.md`

---

## 🎯 The Key Moment

**Part 4, Cell ~45**: When you calculate Silver Gauge for crisp skills...

```python
k_explore values:
- peek_door: 0.0001
- try_door: 0.0000
- go_window: 0.0000
```

**ALL ≈ 0!**

This is the revelation that drives everything else. 🤯

---

## ⚡ Speed Run (30 min)

Want the essence quickly?

1. Run **Part 0** (cells 0-9): Setup
2. Skim **Part 1** (cells 10-22): Problem
3. Quick **Part 2** (cells 23-38): Read formulas, skip exercises
4. **PART 4** (cells 39-56): **DO NOT SKIP!** This is it!
5. Quick **Part 5** (cells 57-66): See the solution

Even in speed-run mode, Part 4 is unmissable!

---

## 🎓 After the Notebook

### Try the Real Agent
```bash
python runner.py --skill-mode hybrid --door-state locked
```

### Generate Visualizations
```bash
make visualize-balanced
```

### Read Deep Dives
- `FINAL_REPORT.md` - Complete analysis
- `PYTHAGOREAN_MEANS_EXPLAINED.md` - Math details

---

**Ready? Launch with: `make notebook`**

🎉 Enjoy the journey!
