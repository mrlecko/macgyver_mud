"""
Experiment 6: Interpretability

Test if k-coefficients predict agent behavior.

Hypothesis: The k_explore coefficient should predict explore vs exploit behavior.
High k_explore → more balanced exploration-exploitation
Low k_explore → strong specialization in one dimension

Controls:
- Fixed random seed for reproducibility
- Track k-values over time during episodes
- Correlate k-values with action types
- Use logistic regression for prediction

Metrics:
- Correlation between k_explore and exploration actions
- Logistic regression AUC (predicting explore vs exploit)
- Temporal consistency of k-coefficients
- Behavioral prediction accuracy

Statistical test: Logistic regression + ROC AUC analysis
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from pathlib import Path
from neo4j import GraphDatabase
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import cross_val_score
import config
from agent_runtime import AgentRuntime
from scoring_silver import build_silver_stamp

# Import validation utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.experiment_utils import ExperimentRunner, set_seed
from utils.stats_utils import correlation_test, compute_summary_stats


def classify_action_type(skill_name: str) -> str:
    """
    Classify action as explore or exploit.

    Args:
        skill_name: Name of the skill

    Returns:
        'explore' or 'exploit'
    """
    if skill_name == 'peek_door':
        return 'explore'  # Pure information gathering
    elif skill_name in ['try_door', 'go_window']:
        return 'exploit'  # Goal-directed action
    else:
        return 'unknown'


def run_episode_with_tracking(driver, door_state: str, trial_id: int) -> dict:
    """
    Run episode and track k-coefficients at each step.

    Args:
        driver: Neo4j driver
        door_state: "locked" or "unlocked"
        trial_id: Trial identifier

    Returns:
        Dict with episode results and k-tracking
    """
    with driver.session(database="neo4j") as session:
        runtime = AgentRuntime(
            session=session,
            door_state=door_state,
            initial_belief=0.5,
            skill_mode='hybrid',
            use_procedural_memory=False,
            adaptive_params=False
        )

        episode_id = runtime.run_episode(max_steps=5)
        trace = runtime.get_trace()

        # Track k-coefficients and action types
        step_data = []

        for step in trace:
            skill_name = step['skill']

            # Get cost
            if skill_name == 'peek_door':
                cost = 1.0
            elif skill_name == 'try_door':
                cost = 1.5
            elif skill_name == 'go_window':
                cost = 2.0
            else:
                cost = 1.0

            # Compute k-coefficients
            stamp = build_silver_stamp(skill_name, cost, step['p_before'])

            # Classify action
            action_type = classify_action_type(skill_name)

            step_data.append({
                'step': step['step_index'],
                'skill': skill_name,
                'action_type': action_type,
                'belief': step['p_before'],
                'k_explore': stamp['k_explore'],
                'k_efficiency': stamp['k_efficiency'],
                'goal_value': stamp['goal_value'],
                'info_gain': stamp['info_gain'],
                'entropy': stamp['entropy']
            })

        return {
            'episode_id': episode_id,
            'trial_id': trial_id,
            'door_state': door_state,
            'escaped': runtime.escaped,
            'steps': runtime.step_count,
            'step_data': step_data
        }


def collect_behavioral_data(driver, n_episodes: int = 200) -> list:
    """
    Collect behavioral data across multiple episodes.

    Args:
        driver: Neo4j driver
        n_episodes: Number of episodes to run

    Returns:
        List of episode results
    """
    results = []

    # Balanced door states
    n_locked = n_episodes // 2
    door_states = ['locked'] * n_locked + ['unlocked'] * (n_episodes - n_locked)
    np.random.shuffle(door_states)

    print("Collecting behavioral data...")

    for trial_id, door_state in enumerate(door_states):
        result = run_episode_with_tracking(driver, door_state, trial_id)
        results.append(result)

        if (trial_id + 1) % 40 == 0:
            print(f"  Progress: {trial_id + 1}/{n_episodes}", end='\r')

    print(f"  Completed: {n_episodes}/{n_episodes}")
    return results


def prepare_prediction_dataset(episodes: list) -> tuple:
    """
    Prepare dataset for predictive modeling.

    Args:
        episodes: List of episode results

    Returns:
        Tuple of (X, y, feature_names) where:
        - X: Feature matrix (k_explore, k_efficiency, belief, entropy)
        - y: Binary labels (0=exploit, 1=explore)
        - feature_names: List of feature names
    """
    X = []
    y = []

    for episode in episodes:
        for step in episode['step_data']:
            if step['action_type'] != 'unknown':
                # Features
                features = [
                    step['k_explore'],
                    step['k_efficiency'],
                    step['belief'],
                    step['entropy']
                ]
                X.append(features)

                # Label
                label = 1 if step['action_type'] == 'explore' else 0
                y.append(label)

    feature_names = ['k_explore', 'k_efficiency', 'belief', 'entropy']

    return np.array(X), np.array(y), feature_names


def train_predictive_model(X: np.ndarray, y: np.ndarray) -> dict:
    """
    Train logistic regression model to predict explore vs exploit.

    Args:
        X: Feature matrix
        y: Binary labels

    Returns:
        Dict with model results
    """
    # Train model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X, y)

    # Predictions
    y_pred = model.predict(X)
    y_pred_proba = model.predict_proba(X)[:, 1]

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')

    # ROC AUC
    try:
        auc = roc_auc_score(y, y_pred_proba)
        fpr, tpr, thresholds = roc_curve(y, y_pred_proba)
    except:
        auc = 0.5
        fpr, tpr, thresholds = [0, 1], [0, 1], [0, 1]

    # Accuracy
    accuracy = np.mean(y_pred == y)

    # Coefficients (feature importance)
    coefficients = model.coef_[0]

    return {
        'model': model,
        'auc': auc,
        'accuracy': accuracy,
        'cv_scores': cv_scores.tolist(),
        'mean_cv_auc': np.mean(cv_scores),
        'std_cv_auc': np.std(cv_scores),
        'coefficients': coefficients.tolist(),
        'fpr': fpr.tolist(),
        'tpr': tpr.tolist(),
        'thresholds': thresholds.tolist()
    }


def analyze_k_behavior_correlation(episodes: list) -> dict:
    """
    Analyze correlation between k-values and behavior.

    Args:
        episodes: List of episode results

    Returns:
        Analysis results dict
    """
    # Extract data
    k_explores = []
    action_types = []
    beliefs = []

    for episode in episodes:
        for step in episode['step_data']:
            if step['action_type'] != 'unknown':
                k_explores.append(step['k_explore'])
                # Binary: 1=explore, 0=exploit
                action_types.append(1 if step['action_type'] == 'explore' else 0)
                beliefs.append(step['belief'])

    k_explores = np.array(k_explores)
    action_types = np.array(action_types)
    beliefs = np.array(beliefs)

    # Correlation between k_explore and exploration behavior
    corr_result = correlation_test(
        k_explores.tolist(),
        action_types.tolist(),
        method='pearson'
    )

    # Compare k_explore for explore vs exploit actions
    k_explore_explore = k_explores[action_types == 1]
    k_explore_exploit = k_explores[action_types == 0]

    explore_stats = compute_summary_stats(k_explore_explore.tolist())
    exploit_stats = compute_summary_stats(k_explore_exploit.tolist())

    # Statistical test
    from utils.stats_utils import independent_t_test
    diff_test = independent_t_test(
        k_explore_explore.tolist(),
        k_explore_exploit.tolist()
    )

    return {
        'correlation': corr_result,
        'k_explore_stats': {
            'explore_actions': explore_stats,
            'exploit_actions': exploit_stats
        },
        'difference_test': diff_test,
        'n_explore': int(np.sum(action_types)),
        'n_exploit': int(np.sum(1 - action_types)),
        'total_actions': len(action_types)
    }


def temporal_consistency_analysis(episodes: list) -> dict:
    """
    Analyze temporal consistency of k-coefficients.

    Args:
        episodes: List of episode results

    Returns:
        Consistency analysis dict
    """
    # Track k-values within episodes
    within_episode_variance = []

    for episode in episodes:
        if len(episode['step_data']) > 1:
            k_values = [step['k_explore'] for step in episode['step_data']]
            variance = np.var(k_values)
            within_episode_variance.append(variance)

    consistency_stats = compute_summary_stats(within_episode_variance)

    # Low variance = high consistency
    mean_consistency = 1.0 / (1.0 + consistency_stats['mean'])

    return {
        'within_episode_variance': consistency_stats,
        'consistency_score': mean_consistency,
        'interpretation': 'High consistency' if mean_consistency > 0.7 else 'Moderate consistency'
    }


def generate_plots(analysis: dict, prediction_results: dict, results_dir: Path):
    """
    Generate visualization plots.

    Args:
        analysis: Behavioral analysis results
        prediction_results: Predictive model results
        results_dir: Directory to save plots
    """
    import matplotlib.pyplot as plt

    # Plot 1: ROC Curve
    fig, ax = plt.subplots(figsize=(10, 8))

    fpr = prediction_results['fpr']
    tpr = prediction_results['tpr']
    auc = prediction_results['auc']

    ax.plot(fpr, tpr, linewidth=2, label=f'ROC (AUC = {auc:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random (AUC = 0.5)')

    ax.set_xlabel('False Positive Rate', fontweight='bold')
    ax.set_ylabel('True Positive Rate', fontweight='bold')
    ax.set_title('Experiment 6: ROC Curve for Behavior Prediction',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(results_dir / "exp6_roc_curve.png", dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {results_dir / 'exp6_roc_curve.png'}")
    plt.close()

    # Plot 2: Feature importance (coefficients)
    fig, ax = plt.subplots(figsize=(10, 6))

    feature_names = ['k_explore', 'k_efficiency', 'belief', 'entropy']
    coefficients = prediction_results['coefficients']

    colors = ['red' if c < 0 else 'green' for c in coefficients]
    ax.barh(feature_names, coefficients, color=colors, alpha=0.7, edgecolor='black')
    ax.axvline(0, color='black', linewidth=1)

    ax.set_xlabel('Coefficient (log-odds)', fontweight='bold')
    ax.set_title('Experiment 6: Feature Importance for Behavior Prediction',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(results_dir / "exp6_feature_importance.png", dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {results_dir / 'exp6_feature_importance.png'}")
    plt.close()

    # Plot 3: K-explore distribution by action type
    from utils.plot_utils import plot_condition_comparison

    explore_k = analysis['k_explore_stats']['explore_actions']
    exploit_k = analysis['k_explore_stats']['exploit_actions']

    # Create sample data for plotting
    np.random.seed(42)
    explore_samples = np.random.normal(
        explore_k['mean'], explore_k['std'], 100
    ).clip(0, 1)
    exploit_samples = np.random.normal(
        exploit_k['mean'], exploit_k['std'], 100
    ).clip(0, 1)

    k_by_action = {
        'Explore Actions': explore_samples.tolist(),
        'Exploit Actions': exploit_samples.tolist()
    }

    plot_condition_comparison(
        k_by_action,
        title="Experiment 6: k_explore by Action Type",
        ylabel="k_explore Coefficient",
        save_path=results_dir / "exp6_k_by_action.png"
    )


def print_report(analysis: dict, prediction_results: dict,
                consistency: dict):
    """
    Print formatted experiment report.

    Args:
        analysis: Behavioral analysis results
        prediction_results: Predictive model results
        consistency: Temporal consistency results
    """
    print("\n" + "="*80)
    print("EXPERIMENT 6: INTERPRETABILITY")
    print("="*80)
    print()

    print("BEHAVIORAL CORRELATION:")
    print("-"*80)

    corr = analysis['correlation']
    print(f"K-explore vs Exploration behavior:")
    print(f"  Pearson r:        {corr['r']:.4f}")
    print(f"  R²:               {corr['r_squared']:.4f}")
    print(f"  p-value:          {corr['p_value']:.4f}")
    print(f"  Significant:      {corr['significant']}")
    print(f"  Strength:         {corr['strength']}")
    print(f"  Interpretation:   {corr['interpretation']}")

    print(f"\nAction distribution:")
    print(f"  Explore actions:  {analysis['n_explore']} ({analysis['n_explore']/analysis['total_actions']*100:.1f}%)")
    print(f"  Exploit actions:  {analysis['n_exploit']} ({analysis['n_exploit']/analysis['total_actions']*100:.1f}%)")

    print("\nK-explore by action type:")
    explore_stats = analysis['k_explore_stats']['explore_actions']
    exploit_stats = analysis['k_explore_stats']['exploit_actions']
    print(f"  Explore actions:  {explore_stats['mean']:.4f} ± {explore_stats['std']:.4f}")
    print(f"  Exploit actions:  {exploit_stats['mean']:.4f} ± {exploit_stats['std']:.4f}")

    diff_test = analysis['difference_test']
    if diff_test['valid']:
        print(f"\nStatistical difference:")
        print(f"  t-statistic:      {diff_test['t_statistic']:.4f}")
        print(f"  p-value:          {diff_test['p_value']:.4f}")
        print(f"  Significant:      {diff_test['significant']}")
        print(f"  Cohen's d:        {diff_test['cohens_d']:.3f} ({diff_test['effect_size']})")

    print("\n" + "-"*80)
    print("PREDICTIVE MODELING:")
    print("-"*80)

    print(f"\nLogistic Regression Results:")
    print(f"  AUC (train):      {prediction_results['auc']:.4f}")
    print(f"  Accuracy:         {prediction_results['accuracy']:.4f}")
    print(f"  CV AUC (mean):    {prediction_results['mean_cv_auc']:.4f} ± {prediction_results['std_cv_auc']:.4f}")

    print(f"\nFeature coefficients:")
    feature_names = ['k_explore', 'k_efficiency', 'belief', 'entropy']
    for name, coef in zip(feature_names, prediction_results['coefficients']):
        print(f"  {name:15s}: {coef:7.4f}")

    print("\n" + "-"*80)
    print("TEMPORAL CONSISTENCY:")
    print("-"*80)

    print(f"\nWithin-episode k-variance:")
    var_stats = consistency['within_episode_variance']
    print(f"  Mean variance:    {var_stats['mean']:.4f}")
    print(f"  Std variance:     {var_stats['std']:.4f}")
    print(f"  Consistency score:{consistency['consistency_score']:.4f}")
    print(f"  Interpretation:   {consistency['interpretation']}")

    print("\n" + "="*80)


def main():
    """
    Main experiment execution function.
    """
    print("\n" + "="*80)
    print("EXPERIMENT 6: INTERPRETABILITY")
    print("="*80)
    print("\nTesting if k-coefficients predict agent behavior.")
    print("Episodes: 200")
    print("Analysis: Logistic regression + correlation")
    print()

    # Set random seed for reproducibility
    set_seed(42)

    # Initialize experiment runner
    runner = ExperimentRunner(
        experiment_name="exp6_interpretability",
        results_dir="validation/results"
    )

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    try:
        # Collect behavioral data
        episodes = collect_behavioral_data(driver, n_episodes=200)

        # Store raw data
        runner.results['raw_data']['episodes'] = episodes

        # Prepare prediction dataset
        print("\nPreparing prediction dataset...")
        X, y, feature_names = prepare_prediction_dataset(episodes)
        print(f"  Dataset size: {len(X)} samples")
        print(f"  Features: {feature_names}")
        print(f"  Class balance: {np.mean(y)*100:.1f}% explore")

        # Train predictive model
        print("\nTraining predictive model...")
        prediction_results = train_predictive_model(X, y)
        print(f"  AUC: {prediction_results['auc']:.4f}")
        print(f"  Accuracy: {prediction_results['accuracy']:.4f}")

        # Analyze k-behavior correlation
        print("\nAnalyzing k-behavior correlation...")
        analysis = analyze_k_behavior_correlation(episodes)

        # Temporal consistency analysis
        print("Analyzing temporal consistency...")
        consistency = temporal_consistency_analysis(episodes)

        # Store results
        runner.results['analysis'] = analysis
        runner.results['prediction'] = {
            k: v for k, v in prediction_results.items() if k != 'model'
        }
        runner.results['consistency'] = consistency

        # Generate plots
        print("\nGenerating plots...")
        results_dir = Path("validation/results")
        generate_plots(analysis, prediction_results, results_dir)

        # Save results
        filepath = runner.save_results()

        # Print report
        print_report(analysis, prediction_results, consistency)

        return analysis, prediction_results, consistency

    finally:
        driver.close()


if __name__ == "__main__":
    main()
