"""
Tầng 2: Benchmark Runner & Logger (scripts/run_experiments.py).
Điều phối thực nghiệm:
- 3 kịch bản chuẩn: small_40 (2 teams, 40 tasks), medium_100 (4 teams, 100 tasks), large_500 (8 teams, 500 tasks).
- 5 instances độc lập cho mỗi kịch bản.
- 5 seeds ngẫu nhiên cho mỗi instance.
- Solvers: greedy, cpsat, gurobi, proposed_4phase, proposed_nsga2.
- Ghi dữ liệu thô vào outputs/raw_runs.jsonl.
- Ghi bảng tổng hợp Mean ± Std vào outputs/summary_metrics.csv.
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

# Thêm đường dẫn project root và src/ vào sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from models import Task, Team, SprintPlan
from solvers.base import BaseSolver
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.cpsat_exact import CPSATExactSolver
from solvers.gurobi_exact import GurobiExactSolver, GUROBI_AVAILABLE
from solvers.proposed_4phase.solver import Proposed4PhaseSolver
from solvers.proposed_nsga2.solver import ProposedNSGA2Solver
from dataset.benchmark_loader import generate_scenario_instance


SCENARIO_CONFIGS = {
    "small_40": {"n_tasks": 40, "n_teams": 2, "time_limit": 15.0},
    "medium_100": {"n_tasks": 100, "n_teams": 4, "time_limit": 30.0},
    "large_500": {"n_tasks": 500, "n_teams": 8, "time_limit": 60.0},
}


def get_solver_instance(
    solver_key: str,
    time_limit: float,
    seed: int,
    pop_size: int = 40,
    generations: int = 30
) -> Optional[BaseSolver]:
    """Khởi tạo đối tượng solver dựa trên solver_key."""
    key = solver_key.lower().strip()
    if key in ["greedy", "greedy_cvss", "greedy-cvss"]:
        return GreedyCVSSSolver()
    elif key in ["cpsat", "cpsat_exact", "or-tools"]:
        return CPSATExactSolver(time_limit_sec=time_limit)
    elif key in ["gurobi", "gurobi_exact"]:
        if not GUROBI_AVAILABLE:
            print("[Warning] gurobipy is not available. Skipping Gurobi solver.")
            return None
        return GurobiExactSolver(time_limit_sec=time_limit)
    elif key in ["proposed", "proposed_4phase", "4phase"]:
        return Proposed4PhaseSolver(random_state=seed)
    elif key in ["nsga2", "proposed_nsga2", "nsga-ii"]:
        return ProposedNSGA2Solver(
            pop_size=pop_size,
            generations=generations,
            random_seed=seed
        )
    else:
        raise ValueError(f"Unknown solver key: {solver_key}")


def run_experiments(
    scenarios: List[str],
    instances_count: int,
    seeds: List[int],
    solvers: List[str],
    raw_output_path: Path,
    summary_output_path: Path,
    custom_time_limit: Optional[float] = None,
    nsga_pop: int = 40,
    nsga_gens: int = 30,
    clean: bool = False
):
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)

    if clean and raw_output_path.exists():
        raw_output_path.unlink()

    print("=" * 115)
    print(f"{'SEC-OPS VULNERABILITY SCHEDULING BENCHMARK SUITE':^115}")
    print(f"{'Scenarios: ' + ', '.join(scenarios) + ' | Solvers: ' + ', '.join(solvers):^115}")
    print(f"{'Instances: ' + str(instances_count) + ' | Seeds: ' + str(seeds):^115}")
    print("=" * 115)

    raw_runs: List[Dict[str, Any]] = []

    # Mở file jsonl để ghi nối tiếp từng dòng
    with open(raw_output_path, "a", encoding="utf-8") as jsonl_file:
        for sc_name in scenarios:
            if sc_name not in SCENARIO_CONFIGS:
                print(f"[Error] Scenario '{sc_name}' not configured.")
                continue

            sc_conf = SCENARIO_CONFIGS[sc_name]
            n_tasks = sc_conf["n_tasks"]
            n_teams = sc_conf["n_teams"]
            time_limit = custom_time_limit if custom_time_limit is not None else sc_conf["time_limit"]

            print(f"\n>>>> SCENARIO: {sc_name.upper()} (Tasks={n_tasks}, Teams={n_teams}, Cap={n_teams * 30} SP)")
            print(f"{'Instance':<9} | {'Solver':<18} | {'Seed':<6} | {'f1 (Utility)':<13} | {'f2 (Cost)':<10} | {'SMS':<6} | {'DAG Viol':<9} | {'Time (ms)':<11} | {'Status':<10}")
            print("-" * 115)

            for inst_idx in range(1, instances_count + 1):
                # Khởi tạo dữ liệu instance với hạt giống cố định
                inst_seed = 1000 + inst_idx * 17
                tasks, teams = generate_scenario_instance(
                    scenario_name=sc_name,
                    target_tasks=n_tasks,
                    n_teams=n_teams,
                    instance_idx=inst_idx,
                    seed=inst_seed
                )

                for solver_key in solvers:
                    # Nếu là thuật toán tiến hóa ngẫu nhiên (NSGA-II), lặp qua danh sách seeds
                    # Nếu là thuật toán đơn định (greedy, exact, 4phase), chỉ cần chạy 1 lần với seed đầu
                    is_stochastic = solver_key.lower() in ["nsga2", "proposed_nsga2", "nsga-ii"]
                    run_seeds = seeds if is_stochastic else [seeds[0]]

                    for seed in run_seeds:
                        solver = get_solver_instance(
                            solver_key=solver_key,
                            time_limit=time_limit,
                            seed=seed,
                            pop_size=nsga_pop,
                            generations=nsga_gens
                        )
                        if solver is None:
                            continue

                        try:
                            plan = solver.solve(tasks, teams, current_sprint=4)
                            status = getattr(plan, "solver_status", "OK")
                            pareto_front = getattr(plan, "pareto_front", None)
                            hypervolume = getattr(plan, "hypervolume", None)
                        except Exception as e:
                            print(f"[ERROR] Exception running {solver.name}: {e}")
                            status = f"ERROR: {str(e)[:15]}"
                            plan = None

                        if plan is not None:
                            f1_val = plan.total_utility_resolved
                            f2_val = plan.total_switch_cost
                            sms_val = plan.skill_match_score
                            dag_viol = plan.dag_violations
                            time_ms = plan.execution_time_ms
                            schedules_info = [
                                {
                                    "team_id": sch.team_id,
                                    "assigned_count": len(sch.assigned_tasks),
                                    "tasks": [t.id for t in sch.assigned_tasks],
                                    "effort": sch.total_effort,
                                    "context_switch_cost": sch.context_switch_cost
                                }
                                for sch in plan.schedules
                            ]
                        else:
                            f1_val = 0.0
                            f2_val = 0.0
                            sms_val = 0.0
                            dag_viol = -1
                            time_ms = 0.0
                            schedules_info = []

                        run_record = {
                            "scenario": sc_name,
                            "instance": inst_idx,
                            "seed": seed,
                            "solver": solver.name if solver else solver_key,
                            "solver_key": solver_key,
                            "n_tasks": n_tasks,
                            "n_teams": n_teams,
                            "total_capacity_sp": n_teams * 30,
                            "f1_utility": f1_val,
                            "f2_switch_cost": f2_val,
                            "total_risk_resolved": getattr(plan, "total_risk_resolved", 0.0) if plan else 0.0,
                            "skill_match_score": sms_val,
                            "dag_violations": dag_viol,
                            "execution_time_ms": time_ms,
                            "status": status,
                            "hypervolume": hypervolume,
                            "pareto_front": pareto_front,
                            "team_schedules": schedules_info,
                            "timestamp": time.time()
                        }

                        # Ghi vào JSONL
                        jsonl_file.write(json.dumps(run_record, ensure_ascii=False) + "\n")
                        jsonl_file.flush()
                        raw_runs.append(run_record)

                        print(f"Inst #{inst_idx:<3} | {solver.name[:18]:<18} | {seed:<6} | {f1_val:<13.1f} | {f2_val:<10.2f} | {sms_val:<6.3f} | {dag_viol:<9} | {time_ms:<11.2f} | {status:<10}")

    # Tính toán bảng tổng hợp Summary Metrics
    compute_and_save_summary(raw_runs, summary_output_path)
    print(f"\n[+] Raw runs logged to: {raw_output_path}")
    print(f"[+] Summary metrics CSV saved to: {summary_output_path}\n")


def compute_and_save_summary(raw_runs: List[Dict[str, Any]], summary_path: Path):
    """Tổng hợp Mean ± Std cho từng cặp (scenario, solver) và tính % giảm switch cost."""
    grouped = defaultdict(list)
    for r in raw_runs:
        key = (r["scenario"], r["solver"])
        grouped[key].append(r)

    # Tìm điểm f2 của Greedy cho từng scenario để so sánh switch reduction %
    greedy_f2_map = {}
    for (sc, slv), runs in grouped.items():
        if "greedy" in slv.lower():
            costs = [r["f2_switch_cost"] for r in runs if r["f2_switch_cost"] > 0]
            if costs:
                greedy_f2_map[sc] = np.mean(costs)

    summary_rows = []
    print("\n" + "=" * 125)
    print(f"{'FINAL SUMMARY BENCHMARK METRICS (Mean ± Std)':^125}")
    print("=" * 125)
    print(f"{'Scenario':<12} | {'Solver':<20} | {'Runs':<5} | {'f1 Utility':<18} | {'f2 Switch Cost':<18} | {'Switch Red. %':<14} | {'SMS (0-1)':<14} | {'Runtime (ms)':<18}")
    print("-" * 125)

    for (sc, slv), runs in sorted(grouped.items()):
        f1_vals = [r["f1_utility"] for r in runs]
        f2_vals = [r["f2_switch_cost"] for r in runs]
        sms_vals = [r["skill_match_score"] for r in runs]
        time_vals = [r["execution_time_ms"] for r in runs]
        hv_vals = [r["hypervolume"] for r in runs if r["hypervolume"] is not None]
        dag_viols = sum(r["dag_violations"] for r in runs)

        f1_m, f1_s = np.mean(f1_vals), np.std(f1_vals)
        f2_m, f2_s = np.mean(f2_vals), np.std(f2_vals)
        sms_m, sms_s = np.mean(sms_vals), np.std(sms_vals)
        time_m, time_s = np.mean(time_vals), np.std(time_vals)
        hv_m = np.mean(hv_vals) if hv_vals else 0.0
        hv_s = np.std(hv_vals) if hv_vals else 0.0

        greedy_ref = greedy_f2_map.get(sc, f2_m)
        if f1_m > 0 and greedy_ref > 0:
            reduction_pct = ((greedy_ref - f2_m) / max(0.001, greedy_ref)) * 100.0
        else:
            reduction_pct = 0.0

        row = {
            "scenario": sc,
            "solver": slv,
            "runs_count": len(runs),
            "f1_utility_mean": round(f1_m, 2),
            "f1_utility_std": round(f1_s, 2),
            "f2_switch_cost_mean": round(f2_m, 2),
            "f2_switch_cost_std": round(f2_s, 2),
            "switch_reduction_pct_vs_greedy": round(reduction_pct, 2),
            "sms_mean": round(sms_m, 3),
            "sms_std": round(sms_s, 3),
            "dag_violations_total": dag_viols,
            "execution_time_ms_mean": round(time_m, 2),
            "execution_time_ms_std": round(time_s, 2),
            "hypervolume_mean": round(hv_m, 2),
            "hypervolume_std": round(hv_s, 2),
        }
        summary_rows.append(row)

        f1_str = f"{f1_m:.1f} ± {f1_s:.1f}"
        f2_str = f"{f2_m:.2f} ± {f2_s:.2f}"
        sms_str = f"{sms_m:.3f} ± {sms_s:.3f}"
        time_str = f"{time_m:.1f} ± {time_s:.1f}"
        red_str = f"{reduction_pct:+.1f}%"

        print(f"{sc:<12} | {slv:<20} | {len(runs):<5} | {f1_str:<18} | {f2_str:<18} | {red_str:<14} | {sms_str:<14} | {time_str:<18}")

    print("=" * 125)

    # Ghi ra CSV
    if summary_rows:
        fieldnames = list(summary_rows[0].keys())
        with open(summary_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)


def main():
    parser = argparse.ArgumentParser(description="Run Benchmark Experiments: 3 Tiers Clean Architecture")
    parser.add_argument("--scenarios", nargs="*", default=["small_40", "medium_100", "large_500"], help="Scenarios to run")
    parser.add_argument("--instances", type=int, default=5, help="Number of instances per scenario (default: 5)")
    parser.add_argument("--seeds", nargs="*", type=int, default=[42, 100, 2024, 777, 999], help="Random seeds list")
    parser.add_argument("--solvers", nargs="*", default=["greedy", "cpsat", "gurobi", "proposed_4phase", "proposed_nsga2"], help="Solvers to run")
    parser.add_argument("--raw-output", default="outputs/raw_runs.jsonl", help="Path to save raw JSONL runs")
    parser.add_argument("--summary-output", default="outputs/summary_metrics.csv", help="Path to save summary CSV")
    parser.add_argument("--time-limit", type=float, default=None, help="Solver time limit override in seconds")
    parser.add_argument("--nsga-pop", type=int, default=40, help="NSGA-II population size")
    parser.add_argument("--nsga-gens", type=int, default=30, help="NSGA-II generations")
    parser.add_argument("--clean", action="store_true", help="Clean raw output file before starting")

    args = parser.parse_args()

    raw_path = PROJECT_ROOT / args.raw_output
    summary_path = PROJECT_ROOT / args.summary_output

    run_experiments(
        scenarios=args.scenarios,
        instances_count=args.instances,
        seeds=args.seeds,
        solvers=args.solvers,
        raw_output_path=raw_path,
        summary_output_path=summary_path,
        custom_time_limit=args.time_limit,
        nsga_pop=args.nsga_pop,
        nsga_gens=args.nsga_gens,
        clean=args.clean
    )


if __name__ == "__main__":
    main()
