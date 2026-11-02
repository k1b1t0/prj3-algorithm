"""
File dieu phoi chay toan bo thuc nghiem boc tach Ablation Study.
Chay 7 cau hinh (Full H-CSM va 6 bien the V1 - V6) tren 3 kich ban tinh tai w = 0.50.
"""
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from bounds import compute_static_bounds
from dataset.benchmark_loader import generate_scenario_instance
from benchmark.config import PROJECT_ROOT, SCENARIO_CONFIGS, DEFAULT_SCENARIOS, DEFAULT_NUM_INSTANCES
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from .v1_no_clustering import V1NoClusteringSolver
from .v2_no_dp import V2NoDPSolver
from .v3_no_path_aware import V3NoPathAwareSolver
from .v4_no_amortization import V4NoAmortizationSolver
from .v5_no_swap import V5NoSwapSolver
from .v6_two_phase_only import V6TwoPhaseOnlySolver
from .report import generate_ablation_reports


def run_ablation_experiments(
    scenarios: Optional[List[str]] = None,
    instances_count: Optional[int] = None,
    weight_w: float = 0.50,
    output_dir: Optional[Path] = None,
    current_sprint: int = 4
) -> List[Dict[str, Any]]:
    """Dieu phoi chay toan bo thuc nghiem boc tach Ablation."""
    scenarios = scenarios or DEFAULT_SCENARIOS
    instances_count = instances_count or DEFAULT_NUM_INSTANCES
    out_dir = output_dir or (PROJECT_ROOT / "outputs" / "ablation")

    # Danh sach 7 cau hinh tham gia boc tach (Full H-CSM + 6 bien the)
    solvers = [
        ProposedHCSMSolver(name="Full H-CSM"),
        V1NoClusteringSolver(),
        V2NoDPSolver(),
        V3NoPathAwareSolver(),
        V4NoAmortizationSolver(),
        V5NoSwapSolver(),
        V6TwoPhaseOnlySolver(),
    ]

    print("=" * 110)
    print(f"{'ABLATION EXPERIMENTS SUITE (3 KỊCH BẢN STATIC, w=0.50)':^110}")
    print(f"Scenarios: {', '.join(scenarios)} | Instances: {instances_count} | Configurations: {len(solvers)}")
    print("=" * 110)

    raw_runs: List[Dict[str, Any]] = []

    for sc in scenarios:
        if sc not in SCENARIO_CONFIGS:
            continue
        cfg = SCENARIO_CONFIGS[sc]
        print(f"\n>>> Running Ablation for Scenario: {sc} (N={cfg['n_tasks']}, M={cfg['n_teams']}) <<<")

        for inst_idx in range(1, instances_count + 1):
            tasks, teams = generate_scenario_instance(
                scenario_name=sc,
                target_tasks=cfg["n_tasks"],
                n_teams=cfg["n_teams"],
                instance_idx=inst_idx,
                seed=42 + inst_idx * 17
            )
            bounds = compute_static_bounds(tasks, teams, current_sprint=current_sprint)

            for solver in solvers:
                t0 = time.perf_counter()
                plan = solver.solve(tasks, teams, current_sprint=current_sprint, w=weight_w, bounds=bounds)
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
                z_val = bounds.compute_z(plan.total_utility_resolved, plan.total_switch_cost, weight_w)

                rec = {
                    "scenario": sc,
                    "instance_idx": inst_idx,
                    "variant": solver.name,
                    "weight_w": weight_w,
                    "f1_utility": round(plan.total_utility_resolved, 2),
                    "f2_switch_cost": round(plan.total_switch_cost, 4),
                    "z_w": round(z_val, 4),
                    "execution_time_ms": elapsed_ms,
                    "assigned_task_count": sum(len(s.assigned_tasks) for s in plan.schedules),
                    "deferred_task_count": len(plan.deferred_tasks),
                }
                raw_runs.append(rec)

            print(f"  [{sc} | Inst {inst_idx:02d}/{instances_count:02d}] Finished 7 configurations successfully.")

    # Xuat toan bo file bao cao
    summary_rows = generate_ablation_reports(raw_runs, out_dir)
    return summary_rows
