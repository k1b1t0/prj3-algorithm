"""
Plan B: Rolling Benchmark CLI Runner Shim.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.rolling import run_benchmark_rolling

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Plan B: Multi-Sprint Rolling Benchmark")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 100, 2024, 777, 999])
    parser.add_argument("--sprints", type=int, default=8)
    parser.add_argument("--tasks-per-sprint", type=int, default=25)
    parser.add_argument("--solvers", nargs="+", default=["hcsm", "gls", "greedy", "cpsat"])
    parser.add_argument("--clean", action="store_true", default=False)
    args = parser.parse_args()
    run_benchmark_rolling(seeds=args.seeds, num_sprints=args.sprints, tasks_per_sprint=args.tasks_per_sprint, solvers_to_run=args.solvers, clean=args.clean)
