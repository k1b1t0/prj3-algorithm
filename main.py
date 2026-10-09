"""Unified entry point for running algorithm, benchmarks, and generating visualizers."""
import argparse
import sys
from pathlib import Path

# Ensure src and scripts are importable
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_proposed import run_proposed
from run_benchmark import run_benchmark
from generate_visualizer import generate_html


def main():
    parser = argparse.ArgumentParser(
        description="Microservice DAG Vulnerability Scheduling CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  uv run main.py proposed
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

    # 2. Benchmark comparison runner
    sub_bench = subparsers.add_parser("benchmark", help="Run benchmark comparing proposed vs baselines")
    sub_bench.add_argument("--scenarios", nargs="*", default=None, help="Scenario json files (default: demo-1,2,3.json)")
    sub_bench.add_argument("--output", default=None, help="Output path (default: outputs/benchmark_summary.json)")

    # 3. Visualizer report generator
    subparsers.add_parser("visualizer", help="Generate interactive HTML visualizer from outputs/benchmark_summary.json")

    # 4. All in one
    subparsers.add_parser("all", help="Run benchmark and then generate interactive visualizer HTML")

    args = parser.parse_args()

    if args.command == "proposed":
        run_proposed(scenario_files=args.scenarios, output_path=args.output)
    elif args.command == "benchmark":
        run_benchmark(scenario_files=args.scenarios, output_path=args.output)
    elif args.command == "visualizer":
        generate_html()
    elif args.command == "all":
        run_benchmark()
        generate_html()


if __name__ == "__main__":
    main()
