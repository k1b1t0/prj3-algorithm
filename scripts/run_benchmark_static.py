"""
Plan A: Static Benchmark CLI Runner Shim.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.static import run_benchmark_static

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Plan A: Static Snapshot Benchmark")
    parser.add_argument("--scenarios", nargs="+", default=["small_40", "medium_100", "large_500"])
    parser.add_argument("--instances", type=int, default=5)
    parser.add_argument("--weights", nargs="+", type=float, default=[0.25, 0.50, 0.75])
    parser.add_argument("--solvers", nargs="+", default=["hcsm", "gls", "cpsat", "greedy"])
    parser.add_argument("--clean", action="store_true", default=False)
    args = parser.parse_args()
    run_benchmark_static(scenarios=args.scenarios, instances_count=args.instances, weights=args.weights, solvers_to_run=args.solvers, clean=args.clean)
