"""
Runner CLI cho Plan A: Static Benchmark.
Su dung cac tham so mac dinh toan cuc tu benchmark.config.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.config import (
    DEFAULT_NUM_INSTANCES, DEFAULT_SCENARIOS, DEFAULT_WEIGHTS, DEFAULT_SOLVERS
)
from benchmark.static import run_benchmark_static

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Plan A: Static Snapshot Benchmark")
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--instances", type=int, default=DEFAULT_NUM_INSTANCES)
    parser.add_argument("--weights", nargs="+", type=float, default=DEFAULT_WEIGHTS)
    parser.add_argument("--solvers", nargs="+", default=DEFAULT_SOLVERS)
    parser.add_argument("--clean", action="store_true", default=True)
    parser.add_argument("--time-limit-cpsat", type=float, default=None)
    args = parser.parse_args()
    run_benchmark_static(
        scenarios=args.scenarios, instances_count=args.instances,
        weights=args.weights, solvers_to_run=args.solvers, clean=args.clean,
        time_limit_cpsat=args.time_limit_cpsat
    )
