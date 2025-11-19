# Quick Start Guide - Validation Experiments

## Prerequisites

1. **Neo4j Running**
   ```bash
   docker ps | grep neo4j
   ```

2. **MacGyver Graph Initialized**
   ```bash
   # Check if agent exists
   python -c "from neo4j import GraphDatabase; import config; \
   driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)); \
   with driver.session(database='neo4j') as s: \
       result = s.run('MATCH (a:Agent) RETURN count(a) as count'); \
       print(f'Agents found: {result.single()[\"count\"]}'); \
   driver.close()"
   ```

## Run All Experiments (Recommended)

```bash
cd /home/juancho/macgyver_mud
python validation/experiments/run_all_experiments.py
```

This will:
- Run all 6 experiments sequentially
- Save results to `validation/results/`
- Generate plots
- Print summary report
- Take ~40-60 minutes

## Run Individual Experiments

```bash
# Experiment 1: Performance Comparison (~5-10 min)
python validation/experiments/exp1_performance_comparison.py

# Experiment 2: K-Space Coverage (~2-3 min)
python validation/experiments/exp2_k_space_coverage.py

# Experiment 3: K-Value Effectiveness (~10-15 min)
python validation/experiments/exp3_k_value_effectiveness.py

# Experiment 4: Domain Transfer (~3-5 min)
python validation/experiments/exp4_domain_transfer.py

# Experiment 5: Ablation Study (~10-15 min)
python validation/experiments/exp5_ablation_study.py

# Experiment 6: Interpretability (~10-15 min)
python validation/experiments/exp6_interpretability.py
```

## Run Specific Experiments Only

```bash
# Run experiments 1, 2, and 4
python validation/experiments/run_all_experiments.py --experiments exp1 exp2 exp4
```

## Check Results

```bash
# List all result files
ls -lh validation/results/

# View latest experiment results
ls -lt validation/results/ | head -10

# View plots
open validation/results/*.png  # macOS
xdg-open validation/results/*.png  # Linux
```

## Interpret Results

### Experiment 1 - Success Criteria
- Statistical significance: p < 0.05 in ANOVA
- Effect size: η² > 0.06 (medium effect)
- Look for: Which skill mode has highest success rate?

### Experiment 2 - Success Criteria
- >80% of k-values should be < 0.05
- 95% CI should not include 0.20
- Look for: Clear clustering near k≈0

### Experiment 3 - Success Criteria
- Significant correlation: |r| > 0.3, p < 0.05
- Negative correlation preferred (low k = better performance)
- Look for: Optimal k-value range

### Experiment 4 - Success Criteria
- All domains show clustering (>60% with k < 0.05)
- Chi-square tests not significant (p > 0.05 = good fit)
- Look for: Consistent patterns across domains

### Experiment 5 - Success Criteria
- SilverGauge > EntropyBased > NoMetric
- Significant paired t-tests (p < 0.05)
- Effect sizes: d > 0.4
- Look for: Clear ordering in interpretability scores

### Experiment 6 - Success Criteria
- ROC AUC > 0.7 (good prediction)
- k_explore coefficient significant (p < 0.05)
- Look for: k_explore as top predictor

## Troubleshooting

### "Connection refused" Error
```bash
# Start Neo4j
docker start <neo4j-container>

# Or check config
python -c "import config; print(config.NEO4J_URI)"
```

### "ModuleNotFoundError"
```bash
# Ensure you're in the right directory
cd /home/juancho/macgyver_mud

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### "No skills found"
```bash
# Initialize graph
python init_graph.py
```

### Slow Performance
```bash
# Run single experiment first to test
python validation/experiments/exp2_k_space_coverage.py

# Or reduce trial counts (edit exp files)
```

## Quick Test

```bash
# Test all imports (< 1 second)
python -c "
import sys
sys.path.insert(0, 'validation/experiments')
import exp1_performance_comparison
import exp2_k_space_coverage
import exp3_k_value_effectiveness
import exp4_domain_transfer
import exp5_ablation_study
import exp6_interpretability
print('✓ All experiments import successfully!')
"
```

## Output Files

Each experiment creates:

1. **JSON file**: `validation/results/expN_<timestamp>.json`
   - Complete results data
   - Statistical test outputs
   - Raw measurements

2. **Plot files**: `validation/results/expN_*.png`
   - Publication-quality figures
   - 300 DPI resolution
   - Clear labels and legends

3. **Console output**:
   - Summary statistics
   - Statistical test results
   - Interpretation

## Example Workflow

```bash
# 1. Quick test (2-3 min)
python validation/experiments/exp2_k_space_coverage.py

# 2. Check output
ls validation/results/exp2*

# 3. If successful, run all
python validation/experiments/run_all_experiments.py

# 4. Review results
cat validation/results/exp*_*.json | grep -A5 "analysis"
```

## Common Parameters

All experiments use these standard settings:
- **Random seed**: 42 (for reproducibility)
- **Results dir**: `validation/results/`
- **Database**: neo4j (default)
- **Plot DPI**: 300
- **Alpha level**: 0.05

To modify, edit the experiment file's `main()` function.

## Getting Help

1. **Check README**: `validation/experiments/README.md`
2. **View docstrings**: `python -c "import exp1_performance_comparison; help(exp1_performance_comparison)"`
3. **Read summary**: `VALIDATION_EXPERIMENTS_SUMMARY.md`

## Success Checklist

After running experiments, verify:

- [ ] JSON files created in `validation/results/`
- [ ] PNG plot files generated
- [ ] Console shows "✓ All experiments completed successfully!"
- [ ] No error messages in output
- [ ] Statistical tests show expected patterns
- [ ] Plots are clear and readable

---

**Total Time**: ~40-60 minutes for full suite
**Requirements**: Neo4j running, Python 3.8+
**Support**: See README.md for detailed documentation
