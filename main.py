"""Unified entry point for running algorithm, benchmarks, exact solver, and generating visualizers."""
import argparse
import sys
from pathlib import Path

# Ensure src is on sys.path for internal src modules
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.run_proposed import run_proposed
from scripts.run_exact import run_exact
from scripts.run_benchmark import run_benchmark
from scripts.generate_visualizer import generate_html


def main():
    parser = argparse.ArgumentParser(
        description="Microservice DAG Vulnerability Scheduling CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  uv run main.py proposed
  uv run main.py exact --scenario demo-1
  uv run main.py benchmark
  uv run main.py visualizer
  uv run main.py all
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    # 1. Proposed algorithm runner
    sub_prop = subparsers.add_parser("proposed", help="Run proposed algorithm on demo scenarios")
    sub_prop.add_argument("--scenarios", nargs="*", default=None, help="Scenario json files (default: demo-1,2,3.json)")
    sub_prop.add_argument("--output", default=None, help="Output path (default: outputs/proposed_results.json)")

    # 2. Google OR-Tools CP-SAT exact solver runner
    sub_exact = subparsers.add_parser("exact", help="Run Google OR-Tools CP-SAT exact baseline solver")
    sub_exact.add_argument("--scenario", default="demo-1", help="Scenario to run (default: demo-1)")
    sub_exact.add_argument("--time-limit", type=float, default=30.0, help="Solver time limit in seconds")
    sub_exact.add_argument("--output", default=None, help="Output path (default: None)")

    # 3. Benchmark comparison runner
    sub_bench = subparsers.add_parser("benchmark", help="Run benchmark comparing proposed vs baselines")
    sub_bench.add_argument("--scenarios", nargs="*", default=None, help="Scenario json files (default: demo-1,2,3.json)")
    sub_bench.add_argument("--output", default=None, help="Output path (default: outputs/benchmark_summary.json)")

    # 4. Visualizer report generator
    subparsers.add_parser("visualizer", help="Generate interactive HTML visualizer from outputs/benchmark_summary.json")

    # 5. All in one
    subparsers.add_parser("all", help="Run benchmark and then generate interactive visualizer HTML")

    args = parser.parse_args()

    if args.command == "proposed":
        run_proposed(scenario_files=args.scenarios, output_path=args.output)
    elif args.command == "exact":
        run_exact([args.scenario], time_limit_sec=args.time_limit, output_path=args.output)
    elif args.command == "benchmark":
        run_benchmark(scenario_files=args.scenarios, output_path=args.output)
    elif args.command == "visualizer":
        generate_html()
    elif args.command == "all":
        run_benchmark()
        generate_html()


if __name__ == "__main__":
    main()
