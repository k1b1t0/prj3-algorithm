"""
1. Google OR-Tools CP-SAT (Exact Global Optimum / MIP Baseline)
2. Proposed (ESSC + Hungarian + PCKP Trimmer + Topological DP)
3. Greedy-CVSS (Standard Industry Practice)
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Add project root and src/ to path so this script can run standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from models import Task, Team, SprintPlan
from proposed.pipeline import solve_proposed_pipeline
from baselines.greedy_cvss import solve_greedy_cvss
from baselines.cpsat_exact import solve_cpsat_exact


def load_scenario(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = [
        Task(
            id=t["id"],
            title=t["title"],
            repository=t["repository"],
            asset_module=t["asset_module"],
            r_i=t["r_i"],
            e_i=t["e_i"],
            skill=t["skill"],
            earliest_sprint=t["earliest_sprint"],
            deadline_sprint=t["deadline_sprint"],
            predecessors=t.get("predecessors", [])
        )
        for t in data["tasks"]
    ]

    teams = [
        Team(
            team_id=tm["team_id"],
            name=tm["name"],
            capacity_sp=tm["capacity_sp"],
            skills=tm["skills"]
        )
        for tm in data["teams"]
    ]

    return data["scenario_name"], tasks, teams


def compute_z_score(plan: SprintPlan, teams: list, lambda_switch: float = 1.0, mu_skill: float = 1.0) -> float:
    """
    Tính hàm mục tiêu toàn diện Z:
    Z = sum(r_i) - lambda * sum(C_ij) + mu * sum(k_{t, skill_i})
    Nếu vi phạm DAG thì Z = 0
    """
    if plan.dag_violations > 0:
        return 0.0

    teams_dict = {tm.team_id: tm for tm in teams}
    skill_sum = 0.0
    for sch in plan.schedules:
        team = teams_dict[sch.team_id]
        for t in sch.assigned_tasks:
            skill_sum += team.get_skill_score(t.skill)

    z = plan.total_risk_resolved - lambda_switch * plan.total_switch_cost + mu_skill * skill_sum
    return round(z, 4)


def run_benchmark(scenario_files=None, output_path=None):
    dataset_dir = PROJECT_ROOT / "dataset"
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if scenario_files is None:
        scenario_files = ["demo-1.json", "demo-2.json", "demo-3.json"]
    if output_path is None:
        output_path = outputs_dir / "benchmark_summary.json"
    else:
        output_path = Path(output_path)

    # Time limits cho CP-SAT theo từng kịch bản
    scenario_time_limits = {
        "demo-1.json": 15.0,
        "demo-2.json": 30.0,
        "demo-3.json": 60.0,
    }

    print("=" * 105)
    print(f"{'BENCHMARK COMPARISON: PROPOSED (ESSC+DP) vs BASELINES':^105}")
    print("=" * 105)

    all_results = {}

    for sc_file in scenario_files:
        sc_path = dataset_dir / sc_file if not Path(sc_file).is_absolute() and not Path(sc_file).exists() else Path(sc_file)
        if not sc_path.exists():
            print(f"[Warning] Scenario file not found: {sc_path}")
            continue

        name, tasks, teams = load_scenario(sc_path)
        print(f"\n>>> SCENARIO: {name} (N={len(tasks)} tasks, |T|={len(teams)} teams)")
        print(f"{'Method':<28} | {'Risk Resolved':<14} | {'Switch Cost':<12} | {'SMS (0-1)':<10} | {'Opt. Gap (%)':<13} | {'Runtime (s)':<11}")
        print("-" * 105)

        # 1. Baseline Exact: Google OR-Tools CP-SAT
        t_limit = scenario_time_limits.get(sc_path.name, 30.0)
        t0 = time.time()
        plan_exact = solve_cpsat_exact(tasks, teams, time_limit_sec=t_limit)
        time_exact = time.time() - t0
        z_exact = compute_z_score(plan_exact, teams)
        exact_status = getattr(plan_exact, "solver_status", "FEASIBLE")

        exact_label = f"1. OR-Tools CP-SAT ({exact_status})"
        print(f"{exact_label:<28} | {plan_exact.total_risk_resolved:<14.1f} | {plan_exact.total_switch_cost:<12.2f} | {plan_exact.skill_match_score:<10.3f} | {'0.0% (Exact)':<13} | {time_exact:<11.3f}")

        # 2. Proposed Algorithm (ESSC + Hungarian + Trimmer + DP)
        t0 = time.time()
        plan_prop = solve_proposed_pipeline(tasks, teams)
        time_prop = time.time() - t0
        z_prop = compute_z_score(plan_prop, teams)
        gap_prop = max(0.0, (z_exact - z_prop) / max(0.0001, z_exact) * 100.0) if z_exact > 0 else 0.0
        print(f"{'2. Proposed (ESSC+DP)':<28} | {plan_prop.total_risk_resolved:<14.1f} | {plan_prop.total_switch_cost:<12.2f} | {plan_prop.skill_match_score:<10.3f} | {f'{gap_prop:.2f}%':<13} | {time_prop:<11.4f}")

        # 3. Baseline Practice: Greedy CVSS (Industry Standard)
        t0 = time.time()
        plan_greedy = solve_greedy_cvss(tasks, teams)
        time_greedy = time.time() - t0
        z_greedy = compute_z_score(plan_greedy, teams)
        gap_greedy = max(0.0, (z_exact - z_greedy) / max(0.0001, z_exact) * 100.0) if z_exact > 0 else 0.0
        print(f"{'3. Greedy CVSS':<28} | {plan_greedy.total_risk_resolved:<14.1f} | {plan_greedy.total_switch_cost:<12.2f} | {plan_greedy.skill_match_score:<10.3f} | {f'{gap_greedy:.2f}%':<13} | {time_greedy:<11.4f}")

        speedup = time_exact / max(0.00001, time_prop)

        all_results[sc_path.name] = {
            "scenario": name,
            "tasks_count": len(tasks),
            "teams_count": len(teams),
            "z_exact": z_exact,
            "exact_status": exact_status,
            "speedup_proposed_vs_exact": round(speedup, 1),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "module": t.asset_module,
                    "risk": t.r_i,
                    "effort": t.e_i,
                    "skill": t.skill,
                    "preds": t.predecessors
                }
                for t in tasks
            ],
            "exact": {
                "risk_resolved": plan_exact.total_risk_resolved,
                "switch_cost": plan_exact.total_switch_cost,
                "sms": plan_exact.skill_match_score,
                "dag_violations": plan_exact.dag_violations,
                "z_score": z_exact,
                "gap_pct": 0.0,
                "runtime_sec": round(time_exact, 4),
                "team_schedules": [
                    {
                        "team_id": r.team_id,
                        "tasks_sequence": [t.id for t in r.assigned_tasks]
                    } for r in plan_exact.schedules
                ]
            },
            "proposed": {
                "risk_resolved": plan_prop.total_risk_resolved,
                "switch_cost": plan_prop.total_switch_cost,
                "sms": plan_prop.skill_match_score,
                "dag_violations": plan_prop.dag_violations,
                "z_score": z_prop,
                "gap_pct": round(gap_prop, 2),
                "runtime_sec": round(time_prop, 4),
                "team_schedules": [
                    {
                        "team_id": r.team_id,
                        "tasks_sequence": [t.id for t in r.assigned_tasks]
                    } for r in plan_prop.schedules
                ]
            },
            "greedy_cvss": {
                "risk_resolved": plan_greedy.total_risk_resolved,
                "switch_cost": plan_greedy.total_switch_cost,
                "sms": plan_greedy.skill_match_score,
                "dag_violations": plan_greedy.dag_violations,
                "z_score": z_greedy,
                "gap_pct": round(gap_greedy, 2),
                "runtime_sec": round(time_greedy, 4),
                "team_schedules": [
                    {
                        "team_id": r.team_id,
                        "tasks_sequence": [t.id for t in r.assigned_tasks]
                    } for r in plan_greedy.schedules
                ]
            }
        }

    # Ghi file JSON cho visualizer
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Benchmark summary JSON written to: {output_path}\n")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Run Benchmark: Proposed vs Baselines")
    parser.add_argument("--scenarios", nargs="*", default=None, help="Scenario json files to run")
    parser.add_argument("--output", default=None, help="Path to save benchmark summary JSON")
    args = parser.parse_args()

    run_benchmark(scenario_files=args.scenarios, output_path=args.output)


if __name__ == "__main__":
    main()
