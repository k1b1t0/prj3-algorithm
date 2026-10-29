"""
Runner CLI cho Plan B: Multi-Sprint Rolling Benchmark.
Su dung cac tham so mac dinh toan cuc tu benchmark.config.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.config import (
    DEFAULT_ROLLING_SEEDS, DEFAULT_NUM_SPRINTS,
    DEFAULT_TASKS_PER_SPRINT, DEFAULT_SOLVERS
)
from benchmark.rolling import run_benchmark_rolling

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Plan B: Multi-Sprint Rolling Benchmark")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_ROLLING_SEEDS)
    parser.add_argument("--sprints", type=int, default=DEFAULT_NUM_SPRINTS)
    parser.add_argument("--tasks-per-sprint", type=int, default=DEFAULT_TASKS_PER_SPRINT)
    parser.add_argument("--solvers", nargs="+", default=DEFAULT_SOLVERS)
    parser.add_argument("--clean", action="store_true", default=True)
    args = parser.parse_args()
    run_benchmark_rolling(
        seeds=args.seeds, num_sprints=args.sprints,
        tasks_per_sprint=args.tasks_per_sprint, solvers_to_run=args.solvers,
        clean=args.clean
    )
