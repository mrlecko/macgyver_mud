# MacGyver MUD Validation Experiments

This directory contains 6 complete validation experiments for the MacGyver MUD Active Inference framework with Silver Gauge metrics.

## Overview

The validation suite tests key hypotheses about the MacGyver Active Inference agent and the Silver Gauge interpretability framework:

1. **Skill mode effectiveness** - Do crisp/balanced/hybrid skills affect performance?
2. **K-space clustering** - Does k≈0 clustering emerge naturally?
3. **K-value effectiveness** - Does k-value correlate with performance?
4. **Domain transfer** - Does Silver Gauge transfer to new domains?
5. **Ablation study** - Is Silver Gauge better than baselines?
6. **Interpretability** - Do k-coefficients predict behavior?

## Experiments

### Experiment 1: Performance Comparison (`exp1_performance_comparison.py`)

**Hypothesis**: Balanced/hybrid skills should perform better in high-uncertainty scenarios.

**Method**:
- Conditions: crisp, balanced, hybrid skill modes
- 100 trials per condition
- 50/50 locked/unlocked doors
- Statistical test: One-way ANOVA + pairwise t-tests

**Metrics**:
- Success rate
- Average steps to goal
- Escape via door percentage

**Runtime**: ~5-10 minutes

---

### Experiment 2: K-Space Coverage (`exp2_k_space_coverage.py`)

**Hypothesis**: >80% of random skill combinations should cluster near k≈0 (specialist zone).

**Method**:
- Generate 1000 random skill combinations
- Calculate k_explore for each
- Test clustering hypothesis
- Statistical test: Bootstrap CI + Chi-square goodness of fit

**Metrics**:
- Percentage with k < 0.05
- Distribution statistics
- Clustering by belief state

**Runtime**: ~2-3 minutes

---

### Experiment 3: K-Value Effectiveness (`exp3_k_value_effectiveness.py`)

**Hypothesis**: Skills with k≈0 should show better performance.

**Method**:
- Create skills across k-spectrum: 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
- Run 50 episodes per k-value
- Correlate k-value with performance
- Statistical test: Pearson correlation + regression

**Metrics**:
- Performance score (success × efficiency)
- Correlation coefficients
- Optimal k-range identification

**Runtime**: ~10-15 minutes

---

### Experiment 4: Domain Transfer (`exp4_domain_transfer.py`)

**Hypothesis**: k≈0 clustering should appear in other crisp decision domains.

**Method**:
- Test 3 domains: MacGyver, Foraging, Navigation
- Sample 500 random skills per domain
- Compare clustering patterns
- Statistical test: Chi-square goodness of fit per domain

**Metrics**:
- K-distribution per domain
- Cross-domain clustering consistency
- Chi-square test results

**Runtime**: ~3-5 minutes

---

### Experiment 5: Ablation Study (`exp5_ablation_study.py`)

**Hypothesis**: Silver Gauge provides better interpretability than baselines.

**Method**:
- Conditions: no_metric, entropy_based, silver_gauge
- 100 episodes per condition
- Compare interpretability, prediction accuracy, consistency
- Statistical test: Paired t-tests

**Metrics**:
- Interpretability score (feature richness + clarity)
- Prediction accuracy (consistency in similar states)
- Consistency score (variance in decisions)

**Runtime**: ~10-15 minutes

---

### Experiment 6: Interpretability (`exp6_interpretability.py`)

**Hypothesis**: k_explore coefficient should predict explore vs exploit behavior.

**Method**:
- Run 200 episodes tracking k-coefficients
- Train logistic regression: k-values → action type
- Evaluate prediction accuracy
- Statistical test: Logistic regression + ROC AUC

**Metrics**:
- ROC AUC for behavior prediction
- Correlation: k_explore vs exploration
- Feature importance (coefficients)
- Temporal consistency

**Runtime**: ~10-15 minutes

---

## Installation & Dependencies

All experiments use the existing validation utilities:

```bash
validation/
├── utils/
│   ├── experiment_utils.py   # ExperimentRunner, set_seed
│   ├── stats_utils.py         # Statistical tests
│   └── plot_utils.py          # Visualization
└── experiments/
    ├── exp1_performance_comparison.py
    ├── exp2_k_space_coverage.py
    ├── exp3_k_value_effectiveness.py
    ├── exp4_domain_transfer.py
    ├── exp5_ablation_study.py
    ├── exp6_interpretability.py
    └── run_all_experiments.py
```

**Requirements**:
- Python 3.8+
- Neo4j database running (with MacGyver graph initialized)
- Dependencies: numpy, scipy, matplotlib, seaborn, scikit-learn, neo4j

## Running Experiments

### Run All Experiments

```bash
cd /home/juancho/macgyver_mud
python validation/experiments/run_all_experiments.py
```

### Run Specific Experiments

```bash
# Run only experiments 1 and 3
python validation/experiments/run_all_experiments.py --experiments exp1 exp3
```

### Run Individual Experiment

```bash
# Run experiment 1
python validation/experiments/exp1_performance_comparison.py
```

## Output

Each experiment produces:

1. **JSON results file**: `validation/results/expN_*.json`
   - Raw data
   - Summary statistics
   - Statistical test results

2. **Plots**: `validation/results/expN_*.png`
   - Visualizations of key findings
   - Comparison plots
   - Distribution plots

3. **Console report**: Formatted summary printed to stdout

### Example Output Structure

```
validation/results/
├── exp1_performance_comparison_20251119_143000.json
├── exp1_success_comparison.png
├── exp1_steps_comparison.png
├── exp2_k_distribution.png
├── exp2_k_by_belief.png
├── exp3_k_vs_performance.png
├── exp4_domain_comparison.png
├── exp5_interpretability.png
├── exp6_roc_curve.png
└── exp6_feature_importance.png
```

## Reproducibility

All experiments use fixed random seeds:
- `set_seed(42)` for numpy random operations
- Deterministic Neo4j queries
- Fixed trial orders

To reproduce results:
1. Ensure Neo4j database is in clean state
2. Run experiments with default settings
3. Compare JSON output files

## Statistical Tests Used

| Experiment | Test(s) | Purpose |
|------------|---------|---------|
| Exp 1 | One-way ANOVA, pairwise t-tests | Compare skill modes |
| Exp 2 | Bootstrap CI, Chi-square GOF | Test clustering hypothesis |
| Exp 3 | Pearson correlation, regression | Correlate k with performance |
| Exp 4 | Chi-square GOF (per domain) | Test domain transfer |
| Exp 5 | Paired t-tests | Compare to baselines |
| Exp 6 | Logistic regression, ROC AUC | Predict behavior |

All tests use α = 0.05 significance level with appropriate corrections (e.g., Bonferroni).

## Interpretation Guide

### What to Look For

**Experiment 1**: Do hybrid skills show higher success rates? Lower step counts?

**Experiment 2**: Is >80% of k-values below 0.05? This confirms specialist clustering.

**Experiment 3**: Is there negative correlation between k and performance? This supports k≈0 optimality.

**Experiment 4**: Do all domains show similar clustering? This validates domain-invariance.

**Experiment 5**: Does Silver Gauge have higher interpretability scores? Better prediction accuracy?

**Experiment 6**: Is ROC AUC > 0.7? Are k-coefficients significant predictors?

### Success Criteria

An experiment is considered successful if:
1. All trials complete without errors
2. Statistical tests meet significance thresholds
3. Results align with stated hypotheses
4. Plots clearly show predicted patterns

## Customization

### Modify Parameters

Each experiment has adjustable parameters in its `main()` function:

```python
# Example: Increase trials in Experiment 1
runner = ExperimentRunner(...)
results = run_condition_trials(
    driver=driver,
    skill_mode='crisp',
    n_trials=200,  # Changed from 100
    locked_pct=0.5
)
```

### Add New Experiments

1. Create `expN_*.py` following existing structure
2. Import in `run_all_experiments.py`
3. Add to `EXPERIMENTS` dict
4. Document in this README

## Troubleshooting

### Neo4j Connection Errors

Ensure Neo4j is running:
```bash
# Check Neo4j status
docker ps | grep neo4j

# Restart if needed
docker restart <neo4j-container>
```

### Memory Issues

For large experiments, increase Python memory:
```bash
export PYTHONMAXMEMORY=4GB
python validation/experiments/run_all_experiments.py
```

### Plotting Errors

If matplotlib backend issues occur:
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
```

## Citation

If you use these experiments in your research:

```bibtex
@software{macgyver_validation_2025,
  title = {MacGyver MUD Validation Experiments},
  author = {MacGyver Team},
  year = {2025},
  url = {https://github.com/yourusername/macgyver_mud}
}
```

## License

Same license as parent MacGyver MUD project.

## Contact

For questions or issues with the validation suite, please open an issue on GitHub.

---

**Last Updated**: November 19, 2025
**Version**: 1.0
**Maintainer**: MacGyver Team
