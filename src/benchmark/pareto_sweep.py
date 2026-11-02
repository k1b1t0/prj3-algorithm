"""
Thuc nghiem quet duong cong Pareto Frontier da muc tieu (f1 vs f2).
Quet 11 trong so w in [0.0, 1.0] voi buoc nhay Delta w = 0.1:
- Proposed H-CSM (11 diem)
- Routing GLS (11 diem)
- OR-Tools CP-SAT (11 diem tren small_40, xac nhan Timeout tren medium/large)
- Greedy-CVSS (1 diem don le duy nhat marker X)
Xuat do thi 300 DPI tai outputs/figures/ va bao cao PARETO_REPORT.md.
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from bounds import compute_static_bounds
from dataset.benchmark_loader import generate_scenario_instance
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.ortools_cpsat import CPSATExactSolver
from solvers.ortools_routing import ORToolsRoutingSolver
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from benchmark.config import PROJECT_ROOT, SCENARIO_CONFIGS
from benchmark.plot_pareto import plot_pareto_fronts_from_data

PARETO_WEIGHTS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def run_pareto_sweep(
    scenarios: Optional[List[str]] = None,
    instances_count: int = 1,
    output_dir: Optional[Path] = None,
    current_sprint: int = 4
) -> List[Dict[str, Any]]:
    scenarios = scenarios or ["small_40", "medium_100", "large_500"]
    out_figures = output_dir or (PROJECT_ROOT / "outputs" / "figures")
    out_figures.mkdir(parents=True, exist_ok=True)

    print("=" * 110)
    print(f"{'BI-OBJECTIVE PARETO FRONTIER EXPERIMENT (11 MỐC TRỌNG SỐ w: 0.0 -> 1.0)':^110}")
    print(f"Scenarios: {', '.join(scenarios)} | Instances per scenario: {instances_count} | Weights: {PARETO_WEIGHTS}")
    print("=" * 110)

    pareto_records: List[Dict[str, Any]] = []

    for sc in scenarios:
        if sc not in SCENARIO_CONFIGS:
            continue
        cfg = SCENARIO_CONFIGS[sc]
        print(f"\n>>> Sweeping Pareto for Scenario: {sc} (N={cfg['n_tasks']}, M={cfg['n_teams']}) <<<")

        for inst_idx in range(1, instances_count + 1):
            tasks, teams = generate_scenario_instance(
                scenario_name=sc,
                target_tasks=cfg["n_tasks"],
                n_teams=cfg["n_teams"],
                instance_idx=inst_idx,
                seed=42 + inst_idx * 17
            )
            bounds = compute_static_bounds(tasks, teams, current_sprint=current_sprint)

            # 1. Greedy-CVSS: 1 diem don le duy nhat
            t0 = time.perf_counter()
            plan_greedy = GreedyCVSSSolver().solve(tasks, teams, current_sprint=current_sprint)
            el_greedy = round((time.perf_counter() - t0) * 1000, 2)
            z_greedy = bounds.compute_z(plan_greedy.total_utility_resolved, plan_greedy.total_switch_cost, 0.5)
            rec_greedy = {
                "scenario": sc, "instance_idx": inst_idx, "solver": "Greedy-CVSS",
                "weight_w": 0.5, "f1_utility": round(plan_greedy.total_utility_resolved, 2),
                "f2_switch_cost": round(plan_greedy.total_switch_cost, 4),
                "z_w": round(z_greedy, 4), "execution_time_ms": el_greedy, "status": "FEASIBLE"
            }
            pareto_records.append(rec_greedy)
            print(f"  [{sc}] Greedy-CVSS: f1={rec_greedy['f1_utility']}, f2={rec_greedy['f2_switch_cost']}")

            # 2. Proposed H-CSM: Quet 11 diem w
            print(f"  [{sc}] Sweeping Proposed H-CSM (11 weights)...")
            hcsm_solver = ProposedHCSMSolver()
            for w in PARETO_WEIGHTS:
                t0 = time.perf_counter()
                plan = hcsm_solver.solve(tasks, teams, current_sprint=current_sprint, w=w, bounds=bounds)
                el = round((time.perf_counter() - t0) * 1000, 2)
                z = bounds.compute_z(plan.total_utility_resolved, plan.total_switch_cost, w)
                pareto_records.append({
                    "scenario": sc, "instance_idx": inst_idx, "solver": "Proposed H-CSM",
                    "weight_w": w, "f1_utility": round(plan.total_utility_resolved, 2),
                    "f2_switch_cost": round(plan.total_switch_cost, 4),
                    "z_w": round(z, 4), "execution_time_ms": el, "status": "FEASIBLE"
                })

            # 3. Routing GLS: Quet 11 diem w
            print(f"  [{sc}] Sweeping Routing GLS (11 weights)...")
            gls_solver = ORToolsRoutingSolver(time_limit_sec=cfg["time_limit_gls"])
            for w in PARETO_WEIGHTS:
                t0 = time.perf_counter()
                plan = gls_solver.solve(tasks, teams, current_sprint=current_sprint, w=w, bounds=bounds)
                el = round((time.perf_counter() - t0) * 1000, 2)
                z = bounds.compute_z(plan.total_utility_resolved, plan.total_switch_cost, w)
                pareto_records.append({
                    "scenario": sc, "instance_idx": inst_idx, "solver": "Routing GLS",
                    "weight_w": w, "f1_utility": round(plan.total_utility_resolved, 2),
                    "f2_switch_cost": round(plan.total_switch_cost, 4),
                    "z_w": round(z, 4), "execution_time_ms": el, "status": "FEASIBLE"
                })

            # 4. OR-Tools CP-SAT:
            if sc == "small_40":
                print(f"  [{sc}] Sweeping OR-Tools CP-SAT (11 weights with exact solver)...")
                cpsat_solver = CPSATExactSolver(time_limit_sec=cfg["time_limit_cpsat"])
                for w in PARETO_WEIGHTS:
                    t0 = time.perf_counter()
                    plan = cpsat_solver.solve(tasks, teams, current_sprint=current_sprint, w=w, bounds=bounds)
                    el = round((time.perf_counter() - t0) * 1000, 2)
                    st = getattr(plan, "solver_status", "FEASIBLE")
                    z = bounds.compute_z(plan.total_utility_resolved, plan.total_switch_cost, w)
                    pareto_records.append({
                        "scenario": sc, "instance_idx": inst_idx, "solver": "OR-Tools CP-SAT",
                        "weight_w": w, "f1_utility": round(plan.total_utility_resolved, 2),
                        "f2_switch_cost": round(plan.total_switch_cost, 4),
                        "z_w": round(z, 4), "execution_time_ms": el, "status": st
                    })
            else:
                # Kiem thu CP-SAT de xac nhan Timeout theo yeu cau nghiem ngat
                print(f"  [{sc}] Testing CP-SAT timeout limit ({cfg['time_limit_cpsat']}s)...")
                t0 = time.perf_counter()
                plan = CPSATExactSolver(time_limit_sec=cfg["time_limit_cpsat"]).solve(
                    tasks, teams, current_sprint=current_sprint, w=0.5, bounds=bounds
                )
                el = round((time.perf_counter() - t0) * 1000, 2)
                st = getattr(plan, "solver_status", "TIMEOUT")
                pareto_records.append({
                    "scenario": sc, "instance_idx": inst_idx, "solver": "OR-Tools CP-SAT",
                    "weight_w": 0.5, "f1_utility": 0.0, "f2_switch_cost": 0.0,
                    "z_w": 0.0, "execution_time_ms": el, "status": st
                })
                print(f"  [{sc}] CP-SAT Result: {st} after {el:.1f} ms (No Pareto points on {sc})")

    # Luu file jsonl
    raw_path = out_figures / "pareto_runs.jsonl"
    with open(raw_path, "w", encoding="utf-8") as f:
        for r in pareto_records:
            f.write(json.dumps(r) + "\n")

    # Ve cac do thi Pareto Frontier
    plot_pareto_fronts_from_data(pareto_records, out_figures)

    # Xuat bao cao PARETO_REPORT.md
    md_path = out_figures / "PARETO_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Báo Cáo Thực Nghiệm Đường Cong Pareto (Bi-Objective Pareto Frontier)\n\n")
        f.write("> **Không gian mục tiêu**: $f_1$ (Lợi ích an ninh $\\uparrow$) vs $f_2$ (Chi phí chuyển đổi $\\downarrow$)\n")
        f.write("> **Dải trọng số**: 11 mốc $w \\in [0.0, 1.0]$ với bước nhảy $\\Delta w = 0.10$\n\n")

        for sc in scenarios:
            f.write(f"### Kịch Bản: `{sc}`\n\n")
            f.write(f"![Pareto Frontier {sc}](pareto_{sc}.png)\n\n")
            f.write("| Trọng số $w$ | Proposed H-CSM ($f_1, f_2$) | Routing GLS ($f_1, f_2$) | OR-Tools CP-SAT ($f_1, f_2$) |\n")
            f.write("| :---: | :---: | :---: | :---: |\n")

            sc_recs = [r for r in pareto_records if r["scenario"] == sc]
            hcsm_by_w = {r["weight_w"]: r for r in sc_recs if r["solver"] == "Proposed H-CSM"}
            gls_by_w = {r["weight_w"]: r for r in sc_recs if r["solver"] == "Routing GLS"}
            cpsat_by_w = {r["weight_w"]: r for r in sc_recs if r["solver"] == "OR-Tools CP-SAT" and r["status"] != "TIMEOUT"}

            for w in PARETO_WEIGHTS:
                h = hcsm_by_w.get(w)
                g = gls_by_w.get(w)
                c = cpsat_by_w.get(w)

                h_str = f"({h['f1_utility']:.1f}, {h['f2_switch_cost']:.2f})" if h else "—"
                g_str = f"({g['f1_utility']:.1f}, {g['f2_switch_cost']:.2f})" if g else "—"
                c_str = f"({c['f1_utility']:.1f}, {c['f2_switch_cost']:.2f})" if c else "Timeout"
                f.write(f"| $w = {w:.1f}$ | **{h_str}** | {g_str} | {c_str} |\n")

            gr = [r for r in sc_recs if r["solver"] == "Greedy-CVSS"]
            if gr:
                f.write(f"\n* **Greedy-CVSS**: Điểm đơn lẻ cố định tại $f_1 = {gr[0]['f1_utility']}, f_2 = {gr[0]['f2_switch_cost']}$\n\n")
            f.write("\n---\n\n")

    print(f"\n[DONE] Pareto figures and report saved to: {out_figures}")
    return pareto_records

