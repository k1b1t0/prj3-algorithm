"""
Plan A: Static Snapshot Benchmark Runner.
Evaluates solvers across scenarios (small_40, medium_100, large_500), 5 instances, weights w in {0.25, 0.50, 0.75}.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from bounds import compute_static_bounds
from dataset.benchmark_loader import generate_scenario_instance
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.cpsat_exact import CPSATExactSolver
from solvers.ortools_routing import ORToolsRoutingSolver
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from benchmark.config import PROJECT_ROOT, SCENARIO_CONFIGS
from benchmark.static_agg import aggregate_static_metrics, print_static_summary_table


def _solve_for_weight(solver_key, tasks, teams, w, bounds, cfg, current_sprint):
    t_start = time.perf_counter()
    if solver_key in ["hcsm", "proposed_hcsm", "proposed"]:
        plan = ProposedHCSMSolver().solve(tasks, teams, current_sprint=current_sprint, w=w, bounds=bounds)
        name = "Proposed H-CSM"
    elif solver_key in ["gls", "routing", "ortools_routing"]:
        plan = ORToolsRoutingSolver(time_limit_sec=cfg["time_limit_gls"]).solve(
            tasks, teams, current_sprint=current_sprint, w=w, bounds=bounds
        )
        name = "Routing GLS"
    elif solver_key in ["cpsat", "cpsat_exact", "exact"]:
        plan = CPSATExactSolver(time_limit_sec=cfg["time_limit_cpsat"]).solve(
            tasks, teams, current_sprint=current_sprint, w=w, bounds=bounds
        )
        name = "OR-Tools CP-SAT"
    elif solver_key in ["greedy", "greedy_cvss"]:
        plan = GreedyCVSSSolver().solve(tasks, teams, current_sprint=current_sprint)
        name = "Greedy-CVSS"
    else:
        raise ValueError(f"Unknown solver key: {solver_key}")

    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
    return plan, name, elapsed_ms


def run_benchmark_static(
    scenarios: Optional[List[str]] = None,
    instances_count: int = 5,
    weights: Optional[List[float]] = None,
    solvers_to_run: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    current_sprint: int = 4,
    skip_cpsat_large: bool = True,
    clean: bool = False
) -> Dict[str, Any]:
    scenarios = scenarios or ["small_40", "medium_100", "large_500"]
    weights = weights or [0.25, 0.50, 0.75]
    solvers_to_run = solvers_to_run or ["hcsm", "gls", "cpsat", "greedy"]

    out_base = output_dir or (PROJECT_ROOT / "outputs" / "static")
    out_base.mkdir(parents=True, exist_ok=True)
    assignments_dir = out_base / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_base / "raw_runs.jsonl"
    summary_path = out_base / "summary_metrics.csv"
    if clean and raw_path.exists():
        raw_path.unlink()

    print("=" * 110)
    print(f"{'PLAN A: STATIC SNAPSHOT BENCHMARK SUITE':^110}")
    print(f"Scenarios: {', '.join(scenarios)} | Instances: {instances_count} | Weights: {weights}")
    print("=" * 110)

    raw_runs: List[Dict[str, Any]] = []

    for sc in scenarios:
        if sc not in SCENARIO_CONFIGS:
            continue
        cfg = SCENARIO_CONFIGS[sc]
        print(f"\n>>> Running Scenario: {sc} (N={cfg['n_tasks']}, M={cfg['n_teams']}, Cap={cfg['n_teams']*30} SP) <<<")

        for inst_idx in range(1, instances_count + 1):
            tasks, teams = generate_scenario_instance(
                scenario_name=sc, target_tasks=cfg["n_tasks"],
                n_teams=cfg["n_teams"], instance_idx=inst_idx, seed=42 + inst_idx * 17
            )
            bounds = compute_static_bounds(tasks, teams, current_sprint=current_sprint)

            for s_key in solvers_to_run:
                s_key_norm = s_key.lower().strip()
                if s_key_norm in ["cpsat", "cpsat_exact", "exact"] and sc == "large_500" and skip_cpsat_large:
                    for w in weights:
                        rec = {
                            "scenario": sc, "instance_idx": inst_idx, "solver": "OR-Tools CP-SAT",
                            "solver_key": "cpsat", "weight_w": w, "f1_utility": 0.0, "f2_switch_cost": 0.0,
                            "z_w": 0.0, "execution_time_ms": cfg["time_limit_cpsat"] * 1000,
                            "total_risk_resolved": 0.0, "assigned_task_count": 0,
                            "deferred_task_count": len(tasks), "status": "TIMEOUT"
                        }
                        raw_runs.append(rec)
                        with open(raw_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(rec) + "\n")
                    print(f"  [{sc} | Inst {inst_idx}] CP-SAT: Skipped (Combinatorial explosion -> TIMEOUT)")
                    continue

                for w in weights:
                    plan, s_name, elapsed_ms = _solve_for_weight(s_key_norm, tasks, teams, w, bounds, cfg, current_sprint)
                    z_val = bounds.compute_z(plan.total_utility_resolved, plan.total_switch_cost, w)
                    status = getattr(plan, "solver_status", "FEASIBLE")

                    rec = {
                        "scenario": sc, "instance_idx": inst_idx, "solver": s_name,
                        "solver_key": s_key_norm, "weight_w": w,
                        "f1_utility": round(plan.total_utility_resolved, 2),
                        "f2_switch_cost": round(plan.total_switch_cost, 4),
                        "z_w": round(z_val, 4), "execution_time_ms": elapsed_ms,
                        "total_risk_resolved": round(plan.total_risk_resolved, 2),
                        "assigned_task_count": sum(len(s.assigned_tasks) for s in plan.schedules),
                        "deferred_task_count": len(plan.deferred_tasks), "status": status
                    }
                    raw_runs.append(rec)
                    with open(raw_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")

                    if abs(w - 0.5) < 1e-4:
                        with open(assignments_dir / f"{sc}_{s_key_norm}_inst{inst_idx}.json", "w", encoding="utf-8") as tf:
                            json.dump(plan.to_dict(), tf, indent=2)

                    print(f"  [{sc} | Inst {inst_idx}] {s_name:<18} (w={w:.2f}) -> f1={rec['f1_utility']:>7.1f}, f2={rec['f2_switch_cost']:>5.2f}, Z={rec['z_w']:>6.3f}, Time={rec['execution_time_ms']:>7.1f} ms [{status}]")

    summary_rows = aggregate_static_metrics(raw_runs, scenarios, summary_path)
    print_static_summary_table(summary_rows)
    return {"raw_runs": raw_runs, "summary": summary_rows}

