"""
Diem vao CLI tap trung cho toan bo thuc nghiem SecOps Vulnerability Scheduling.
Commands:
  python main.py static     - Chay Plan A: Static Snapshot Benchmark
  python main.py rolling    - Chay Plan B: Multi-Sprint Rolling Benchmark
  python main.py inspect    - Kiem toan 1 instance chi tiet voi Phase Logger
  python main.py plot       - Xuat toan bo bieu do (4 Line Charts & Pareto Fronts)
  python main.py test       - Chay toan bo Unit Tests
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bounds import compute_static_bounds
from dataset.benchmark_loader import generate_scenario_instance
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.cpsat_exact import CPSATExactSolver
from solvers.ortools_routing import ORToolsRoutingSolver
from benchmark.config import (
    DEFAULT_NUM_INSTANCES, DEFAULT_SCENARIOS, DEFAULT_WEIGHTS,
    DEFAULT_SOLVERS, DEFAULT_ROLLING_SEEDS, DEFAULT_NUM_SPRINTS,
    DEFAULT_TASKS_PER_SPRINT
)
from benchmark import run_benchmark_static, run_benchmark_rolling, plot_all_benchmarks


def run_inspect(scenario: str, instance_idx: int, solver_key: str, weight_w: float, detailed: bool):
    print("=" * 88)
    print(f"Inspecting Instance: {scenario} (Inst {instance_idx}) | Solver: {solver_key} | w: {weight_w}")
    print("=" * 88)

    cfg = {"small_40": (40, 2), "medium_100": (100, 4), "large_500": (500, 8)}.get(scenario, (40, 2))
    tasks, teams = generate_scenario_instance(
        scenario_name=scenario, target_tasks=cfg[0], n_teams=cfg[1],
        instance_idx=instance_idx, seed=42 + instance_idx * 17
    )
    bounds = compute_static_bounds(tasks, teams, current_sprint=4)
    s_norm = solver_key.lower().strip()

    if s_norm in ["proposed", "hcsm", "proposed_hcsm"]:
        plan = ProposedHCSMSolver().solve(
            tasks, teams, current_sprint=4, w=weight_w, bounds=bounds, verbose=True, detailed=detailed
        )
    elif s_norm in ["greedy", "greedy_cvss"]:
        plan = GreedyCVSSSolver().solve(tasks, teams, current_sprint=4)
    elif s_norm in ["gls", "routing"]:
        plan = ORToolsRoutingSolver(time_limit_sec=5.0).solve(tasks, teams, current_sprint=4, w=weight_w, bounds=bounds)
    elif s_norm in ["cpsat", "exact"]:
        plan = CPSATExactSolver(time_limit_sec=60.0).solve(tasks, teams, current_sprint=4, w=weight_w, bounds=bounds)
    else:
        raise ValueError(f"Unknown solver: {solver_key}")

    z_val = bounds.compute_z(plan.total_utility_resolved, plan.total_switch_cost, weight_w)
    print(f"\nFinal Result: f1={plan.total_utility_resolved:.1f}, f2={plan.total_switch_cost:.2f}, Z({weight_w:.2f})={z_val:.4f}, Time={plan.execution_time_ms:.1f} ms")


def main():
    parser = argparse.ArgumentParser(
        description="SecOps Multi-Objective Vulnerability Scheduling Benchmark Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    sub_static = sub.add_parser("static", help="Run Plan A: Static Snapshot Benchmark")
    sub_static.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    sub_static.add_argument("--instances", type=int, default=DEFAULT_NUM_INSTANCES)
    sub_static.add_argument("--weights", nargs="+", type=float, default=DEFAULT_WEIGHTS)
    sub_static.add_argument("--solvers", nargs="+", default=DEFAULT_SOLVERS)
    sub_static.add_argument("--clean", action="store_true", default=True)
    sub_static.add_argument("--skip-cpsat-medium", action="store_true", default=True)

    sub_rolling = sub.add_parser("rolling", help="Run Plan B: Multi-Sprint Rolling Benchmark")
    sub_rolling.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_ROLLING_SEEDS)
    sub_rolling.add_argument("--sprints", type=int, default=DEFAULT_NUM_SPRINTS)
    sub_rolling.add_argument("--tasks-per-sprint", type=int, default=DEFAULT_TASKS_PER_SPRINT)
    sub_rolling.add_argument("--solvers", nargs="+", default=DEFAULT_SOLVERS)
    sub_rolling.add_argument("--clean", action="store_true", default=True)

    sub_insp = sub.add_parser("inspect", help="Inspect single instance with PhaseLogger")
    sub_insp.add_argument("--scenario", default="small_40", choices=["small_40", "medium_100", "large_500"])
    sub_insp.add_argument("--instance", type=int, default=1)
    sub_insp.add_argument("--solver", default="proposed")
    sub_insp.add_argument("--weight", type=float, default=0.50)
    sub_insp.add_argument("--detailed", action="store_true", default=True)

    sub_plot = sub.add_parser("plot", help="Generate publication-ready figures")
    sub_plot.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "figures"))

    sub.add_parser("test", help="Run complete unit test suite")

    args = parser.parse_args()

    if args.command == "static":
        run_benchmark_static(
            scenarios=args.scenarios, instances_count=args.instances,
            weights=args.weights, solvers_to_run=args.solvers, clean=args.clean,
            skip_cpsat_medium=args.skip_cpsat_medium
        )
    elif args.command == "rolling":
        run_benchmark_rolling(
            seeds=args.seeds, num_sprints=args.sprints,
            tasks_per_sprint=args.tasks_per_sprint, solvers_to_run=args.solvers, clean=args.clean
        )
    elif args.command == "inspect":
        run_inspect(
            scenario=args.scenario, instance_idx=args.instance,
            solver_key=args.solver, weight_w=args.weight, detailed=args.detailed
        )
    elif args.command == "plot":
        plot_all_benchmarks(Path(args.output_dir))
    elif args.command == "test":
        cmd = [sys.executable, "-m", "unittest", "discover", "tests"]
        subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)


if __name__ == "__main__":
    main()
