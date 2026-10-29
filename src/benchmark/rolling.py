"""
Plan B: Multi-Sprint Rolling Benchmark Runner.
Simulates realistic operations across 8 consecutive Sprints x 5 random seeds x 4 solvers.
"""
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional

from bounds import compute_static_bounds
from dataset.teams import get_standard_teams
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.cpsat_exact import CPSATExactSolver
from solvers.ortools_routing import ORToolsRoutingSolver
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from benchmark.config import (
    PROJECT_ROOT, DEFAULT_ROLLING_SEEDS, DEFAULT_NUM_SPRINTS,
    DEFAULT_TASKS_PER_SPRINT, DEFAULT_SOLVERS
)
from benchmark.rolling_pool import generate_rolling_backlog_pool
from benchmark.rolling_agg import aggregate_rolling_scorecard, print_rolling_scorecard


def _step_solver(s_key_norm, backlog, teams, s, cpsat_to, gls_to):
    t0 = time.perf_counter()
    if s_key_norm == "hcsm":
        bnds = compute_static_bounds(backlog, teams, current_sprint=s)
        plan = ProposedHCSMSolver().solve(backlog, teams, current_sprint=s, w=0.5, bounds=bnds)
    elif s_key_norm == "gls":
        bnds = compute_static_bounds(backlog, teams, current_sprint=s)
        plan = ORToolsRoutingSolver(time_limit_sec=gls_to).solve(backlog, teams, current_sprint=s, w=0.5, bounds=bnds)
    elif s_key_norm == "greedy":
        plan = GreedyCVSSSolver().solve(backlog, teams, current_sprint=s)
    elif s_key_norm == "cpsat":
        bnds = compute_static_bounds(backlog, teams, current_sprint=s)
        plan = CPSATExactSolver(time_limit_sec=cpsat_to).solve(backlog, teams, current_sprint=s, w=0.5, bounds=bnds)
    else:
        raise ValueError(f"Unknown solver: {s_key_norm}")
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    return plan, elapsed_ms


def run_benchmark_rolling(
    seeds: Optional[List[int]] = None,
    num_sprints: Optional[int] = None,
    tasks_per_sprint: Optional[int] = None,
    n_teams: int = 2,
    solvers_to_run: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    cpsat_timeout_sec: float = 15.0,
    gls_timeout_sec: float = 1.0,
    clean: bool = True
) -> Dict[str, Any]:
    seeds = seeds or DEFAULT_ROLLING_SEEDS
    num_sprints = num_sprints or DEFAULT_NUM_SPRINTS
    tasks_per_sprint = tasks_per_sprint or DEFAULT_TASKS_PER_SPRINT
    solvers_to_run = solvers_to_run or DEFAULT_SOLVERS
    out_base = output_dir or (PROJECT_ROOT / "outputs" / "rolling")
    out_base.mkdir(parents=True, exist_ok=True)
    traces_dir = out_base / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    scorecard_path = out_base / "rolling_scorecard.csv"
    runs_path = out_base / "rolling_runs.jsonl"
    if clean and runs_path.exists():
        runs_path.unlink()

    print("=" * 110)
    print(f"{'PLAN B: MULTI-SPRINT ROLLING BENCHMARK SUITE (8 Sprints)':^110}")
    print(f"Seeds: {seeds} | Sprints: {num_sprints} | Teams: {n_teams} (Cap={n_teams*30} SP/sprint)")
    print("=" * 110)

    solver_seed_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    all_sprint_records: List[Dict[str, Any]] = []
    teams_template = get_standard_teams(n_teams)
    solver_names = {"hcsm": "Proposed H-CSM", "gls": "Routing GLS", "greedy": "Greedy-CVSS", "cpsat": "OR-Tools CP-SAT"}

    for seed_idx, seed in enumerate(seeds):
        print(f"\n=======================================================\n  RUN SEED {seed} ({seed_idx + 1}/{len(seeds)})\n=======================================================")
        cohorts = generate_rolling_backlog_pool(seed, tasks_per_sprint=tasks_per_sprint, num_sprints=num_sprints)

        for s_key in solvers_to_run:
            s_key_norm = s_key.lower().strip()
            s_name = solver_names.get(s_key_norm, s_key)
            print(f"\n--- Simulating: {s_name} (Seed {seed}) ---")

            deferred_pool: List = []
            timed_out_at: Optional[int] = None
            auc_tve, breaches, total_f2, total_z = 0.0, 0, 0.0, 0.0

            for s in range(1, num_sprints + 1):
                cur_backlog = list(deferred_pool) + list(cohorts[s])
                if timed_out_at is not None:
                    rec = {"seed": seed, "solver": s_name, "solver_key": s_key_norm, "sprint": s, "backlog_count": len(cur_backlog), "tve": 0.0, "breaches": 0, "f2": 0.0, "z_w": 0.0, "time_ms": cpsat_timeout_sec * 1000, "status": "TIMEOUT"}
                    all_sprint_records.append(rec)
                    with open(runs_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")
                    continue

                bounds = compute_static_bounds(cur_backlog, teams_template, current_sprint=s)
                plan, elapsed_ms = _step_solver(s_key_norm, cur_backlog, teams_template, s, cpsat_timeout_sec, gls_timeout_sec)

                if s_key_norm == "cpsat" and ("UNKNOWN" in getattr(plan, "solver_status", "") or plan.execution_time_ms >= (cpsat_timeout_sec * 950)):
                    timed_out_at = s
                    print(f"  [Sprint {s}] CP-SAT Exceeded Timeout Limit ({cpsat_timeout_sec}s) -> TERMINATED")
                    rec = {"seed": seed, "solver": s_name, "solver_key": s_key_norm, "sprint": s, "backlog_count": len(cur_backlog), "tve": 0.0, "breaches": 0, "f2": 0.0, "z_w": 0.0, "time_ms": elapsed_ms, "status": "TIMEOUT"}
                    all_sprint_records.append(rec)
                    with open(runs_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")
                    continue

                deferred_pool = plan.deferred_tasks
                tve_s = sum(t.compute_utility(current_sprint=s) for t in deferred_pool)
                br_s = sum(1 for t in deferred_pool if s >= t.deadline_sprint)
                f2_s = plan.total_switch_cost
                z_s = bounds.compute_z(plan.total_utility_resolved, f2_s, w=0.5)

                auc_tve += tve_s
                breaches += br_s
                total_f2 += f2_s
                total_z += z_s

                rec = {
                    "seed": seed, "solver": s_name, "solver_key": s_key_norm, "sprint": s,
                    "backlog_count": len(cur_backlog), "assigned_count": sum(len(sch.assigned_tasks) for sch in plan.schedules),
                    "deferred_count": len(deferred_pool), "tve": round(tve_s, 2), "breaches": br_s,
                    "f2": round(f2_s, 4), "z_w": round(z_s, 4), "time_ms": elapsed_ms, "status": "COMPLETED"
                }
                all_sprint_records.append(rec)
                with open(runs_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec) + "\n")

                with open(traces_dir / f"trace_seed{seed}_{s_key_norm}_sprint{s}.json", "w", encoding="utf-8") as tf:
                    json.dump(plan.to_dict(), tf, indent=2)

                print(f"  Sprint {s}/8 | Backlog: {len(cur_backlog):>2} | Resolved: {rec['assigned_count']:>2} | Deferred: {rec['deferred_count']:>2} | TVE: {tve_s:>6.1f} | Breaches: {br_s:>2} | f2: {f2_s:>5.2f} | Z(0.5): {z_s:>5.3f} | Time: {elapsed_ms:>6.1f} ms")

            if timed_out_at is not None:
                solver_seed_results[s_name].append({"seed": seed, "completed": False, "timeout_sprint": timed_out_at, "auc_tve": None, "total_breaches": None, "total_f2": None, "total_z": None})
            else:
                solver_seed_results[s_name].append({"seed": seed, "completed": True, "timeout_sprint": None, "auc_tve": round(auc_tve, 2), "total_breaches": breaches, "total_f2": round(total_f2, 4), "total_z": round(total_z, 4)})

    scorecard_rows = aggregate_rolling_scorecard(solver_seed_results, scorecard_path)
    print_rolling_scorecard(scorecard_rows)
    return {"scorecard": scorecard_rows, "sprint_records": all_sprint_records, "seed_results": solver_seed_results}

