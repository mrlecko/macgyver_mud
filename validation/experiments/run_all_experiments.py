"""
Master script to run all validation experiments.

This script runs all 6 validation experiments sequentially and generates
a comprehensive summary report.

Usage:
    python run_all_experiments.py
    python run_all_experiments.py --experiments exp1 exp3  # Run specific experiments
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import all experiments
import exp1_performance_comparison
import exp2_k_space_coverage
import exp3_k_value_effectiveness
import exp4_domain_transfer
import exp5_ablation_study
import exp6_interpretability


EXPERIMENTS = {
    'exp1': {
        'name': 'Performance Comparison',
        'module': exp1_performance_comparison,
        'description': 'Test if skill mode affects performance'
    },
    'exp2': {
        'name': 'K-Space Coverage',
        'module': exp2_k_space_coverage,
        'description': 'Test if k≈0 clustering emerges naturally'
    },
    'exp3': {
        'name': 'K-Value Effectiveness',
        'module': exp3_k_value_effectiveness,
        'description': 'Correlate k-value with performance'
    },
    'exp4': {
        'name': 'Domain Transfer',
        'module': exp4_domain_transfer,
        'description': 'Test Silver Gauge transfer to new domains'
    },
    'exp5': {
        'name': 'Ablation Study',
        'module': exp5_ablation_study,
        'description': 'Compare Silver Gauge to baselines'
    },
    'exp6': {
        'name': 'Interpretability',
        'module': exp6_interpretability,
        'description': 'Test k-coefficient behavior prediction'
    }
}


def run_experiment(exp_id: str) -> dict:
    """
    Run a single experiment and capture results.

    Args:
        exp_id: Experiment identifier (e.g., 'exp1')

    Returns:
        Dict with experiment results
    """
    exp_info = EXPERIMENTS[exp_id]

    print("\n" + "="*80)
    print(f"RUNNING: {exp_info['name']}")
    print(f"Description: {exp_info['description']}")
    print("="*80)

    start_time = datetime.now()

    try:
        # Run experiment main()
        result = exp_info['module'].main()

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        return {
            'experiment': exp_id,
            'name': exp_info['name'],
            'status': 'success',
            'elapsed_seconds': elapsed,
            'result': result
        }

    except Exception as e:
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        print(f"\n✗ ERROR: {e}")

        return {
            'experiment': exp_id,
            'name': exp_info['name'],
            'status': 'error',
            'elapsed_seconds': elapsed,
            'error': str(e)
        }


def print_summary(results: list):
    """
    Print summary of all experiment results.

    Args:
        results: List of experiment result dicts
    """
    print("\n" + "="*80)
    print("EXPERIMENT SUITE SUMMARY")
    print("="*80)
    print()

    total_time = sum(r['elapsed_seconds'] for r in results)
    success_count = sum(1 for r in results if r['status'] == 'success')

    print(f"Total experiments:  {len(results)}")
    print(f"Successful:         {success_count}")
    print(f"Failed:             {len(results) - success_count}")
    print(f"Total time:         {total_time:.1f}s ({total_time/60:.1f}m)")
    print()

    print("EXPERIMENT STATUS:")
    print("-"*80)
    for r in results:
        status_symbol = "✓" if r['status'] == 'success' else "✗"
        print(f"{status_symbol} {r['experiment']}: {r['name']:30s} "
              f"({r['elapsed_seconds']:.1f}s) - {r['status']}")

    # Show errors if any
    errors = [r for r in results if r['status'] == 'error']
    if errors:
        print("\nERRORS:")
        print("-"*80)
        for r in errors:
            print(f"\n{r['experiment']}: {r['name']}")
            print(f"  Error: {r['error']}")

    print("\n" + "="*80)

    # Results location
    results_dir = Path("validation/results")
    print(f"\nResults saved to: {results_dir.absolute()}")
    print("Plots and JSON files are available in the results directory.")
    print()


def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(
        description='Run validation experiments for MacGyver MUD Active Inference'
    )
    parser.add_argument(
        '--experiments',
        nargs='+',
        choices=list(EXPERIMENTS.keys()),
        default=list(EXPERIMENTS.keys()),
        help='Experiments to run (default: all)'
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("MACGYVER MUD VALIDATION EXPERIMENT SUITE")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Experiments to run: {', '.join(args.experiments)}")
    print()

    # Run experiments
    results = []

    for exp_id in args.experiments:
        result = run_experiment(exp_id)
        results.append(result)

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    if all(r['status'] == 'success' for r in results):
        print("✓ All experiments completed successfully!")
        sys.exit(0)
    else:
        print("✗ Some experiments failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
