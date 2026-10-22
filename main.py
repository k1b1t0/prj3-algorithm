"""
Unified CLI Entry Point for SecOps Vulnerability Scheduling Algorithms & Experiments.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_experiments import run_experiments
from scripts.render_dashboard import render_html, load_data
from scripts.plot_pareto import load_raw_runs, plot_pareto_fronts, plot_summary_bars


def main():
    parser = argparse.ArgumentParser(
        description="SecOps Multi-Objective Vulnerability Scheduling CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  uv run main.py experiments --scenarios small_40 --instances 5 --seeds 42 100 2024 777 999
  uv run main.py dashboard
  uv run main.py pareto
  uv run main.py all --scenarios small_40
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # 1. Run experiments (Tier 2 runner)
    sub_exp = subparsers.add_parser("experiments", help="Run benchmark experiments on standard scenarios")
    sub_exp.add_argument("--scenarios", nargs="*", default=["small_40"], help="Scenarios list (small_40, medium_100, large_500)")
    sub_exp.add_argument("--instances", type=int, default=5, help="Number of instances per scenario (default: 5)")
    sub_exp.add_argument("--seeds", nargs="*", type=int, default=[42, 100, 2024, 777, 999], help="Random seeds")
    sub_exp.add_argument("--solvers", nargs="*", default=["greedy", "cpsat", "gurobi", "proposed_4phase", "proposed_nsga2"], help="Solvers")
    sub_exp.add_argument("--clean", action="store_true", help="Clean raw output file before starting")

    # 2. Render dashboard (Tier 3)
    sub_dash = subparsers.add_parser("dashboard", help="Render interactive HTML dashboard from outputs")
    sub_dash.add_argument("--raw", default="outputs/raw_runs.jsonl", help="Path to raw JSONL")
    sub_dash.add_argument("--summary", default="outputs/summary_metrics.csv", help="Path to summary CSV")
    sub_dash.add_argument("--output", default="outputs/dashboard.html", help="Path to output HTML")

    # 3. Plot pareto PNGs (Tier 3)
    sub_plt = subparsers.add_parser("pareto", help="Generate publication-ready Pareto & metrics PNG plots")
    sub_plt.add_argument("--raw", default="outputs/raw_runs.jsonl", help="Path to raw JSONL")
    sub_plt.add_argument("--output-dir", default="outputs/pareto_plots", help="Output directory")

    # 4. All in one
    sub_all = subparsers.add_parser("all", help="Run experiments, generate plots, and render dashboard")
    sub_all.add_argument("--scenarios", nargs="*", default=["small_40"], help="Scenarios list")
    sub_all.add_argument("--instances", type=int, default=5, help="Instances count")
    sub_all.add_argument("--seeds", nargs="*", type=int, default=[42, 100, 2024, 777, 999], help="Random seeds")
    sub_all.add_argument("--solvers", nargs="*", default=["greedy", "cpsat", "gurobi", "proposed_4phase", "proposed_nsga2"], help="Solvers")
    sub_all.add_argument("--clean", action="store_true", help="Clean raw output file before starting")

    args = parser.parse_args()

    raw_path = PROJECT_ROOT / "outputs" / "raw_runs.jsonl"
    sum_path = PROJECT_ROOT / "outputs" / "summary_metrics.csv"
    dash_path = PROJECT_ROOT / "outputs" / "dashboard.html"
    plots_dir = PROJECT_ROOT / "outputs" / "pareto_plots"

    if args.command == "experiments":
        run_experiments(
            scenarios=args.scenarios,
            instances_count=args.instances,
            seeds=args.seeds,
            solvers=args.solvers,
            raw_output_path=raw_path,
            summary_output_path=sum_path,
            clean=args.clean
        )
    elif args.command == "dashboard":
        runs, rows = load_data(raw_path, sum_path)
        render_html(runs, rows, dash_path)
    elif args.command == "pareto":
        runs = load_raw_runs(raw_path)
        plot_pareto_fronts(runs, plots_dir)
        plot_summary_bars(runs, plots_dir)
    elif args.command == "all":
        run_experiments(
            scenarios=args.scenarios,
            instances_count=args.instances,
            seeds=args.seeds,
            solvers=args.solvers,
            raw_output_path=raw_path,
            summary_output_path=sum_path,
            clean=args.clean
        )
        runs, rows = load_data(raw_path, sum_path)
        render_html(runs, rows, dash_path)
        plot_pareto_fronts(runs, plots_dir)
        plot_summary_bars(runs, plots_dir)


if __name__ == "__main__":
    main()
