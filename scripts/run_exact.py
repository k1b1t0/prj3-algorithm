"""Runner for executing Google OR-Tools CP-SAT exact baseline on scenarios."""
import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from models import Task, Team
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


def run_exact(scenario_files=None, time_limit_sec=30.0, output_path=None):
    dataset_dir = PROJECT_ROOT / "dataset"
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if scenario_files is None:
        scenario_files = ["demo-1.json"]
    elif isinstance(scenario_files, str):
        scenario_files = [scenario_files]

    results = {}

    for sc_file in scenario_files:
        if not sc_file.endswith(".json"):
            sc_file = f"{sc_file}.json"
        sc_path = dataset_dir / sc_file if not Path(sc_file).is_absolute() and not Path(sc_file).exists() else Path(sc_file)
        if not sc_path.exists():
            print(f"[Warning] Scenario file not found: {sc_path}")
            continue

        name, tasks, teams = load_scenario(sc_path)
        print(f"\n=======================================================")
        print(f"[*] RUNNING OR-TOOLS CP-SAT EXACT: {name}")
        print(f"    Tasks: {len(tasks)}, Teams: {len(teams)}, Time Limit: {time_limit_sec}s")
        print(f"=======================================================")

        plan = solve_cpsat_exact(tasks, teams, time_limit_sec=time_limit_sec)

        status = getattr(plan, "solver_status", "UNKNOWN")
        duration = getattr(plan, "solve_duration", 0.0)
        raw_obj = getattr(plan, "raw_objective", 0.0)
        best_bound = getattr(plan, "best_bound", 0.0)

        print(f"[+] Status: {status} in {duration:.3f}s")
        print(f"[+] Objective Value (Z): {raw_obj:.4f} (Best Bound: {best_bound:.4f})")
        print(f"[+] Risk Resolved: {plan.total_risk_resolved:.1f}")
        print(f"[+] Context Switch Cost: {plan.total_switch_cost:.2f}")
        print(f"[+] Skill Match Score (SMS): {plan.skill_match_score:.4f}")
        print(f"[+] DAG Violations: {plan.dag_violations}")

        sc_info = {
            "scenario": name,
            "status": status,
            "duration": duration,
            "objective_value": raw_obj,
            "best_bound": best_bound,
            "metrics": {
                "risk_resolved": plan.total_risk_resolved,
                "switch_cost": plan.total_switch_cost,
                "sms": plan.skill_match_score,
                "dag_violations": plan.dag_violations
            },
            "team_schedules": []
        }

        for sch in plan.schedules:
            print(f"\n  Team {sch.team_id}: {len(sch.assigned_tasks)} tasks, Effort: {sch.total_effort} SP, Switch Cost: {sch.context_switch_cost}")
            task_ids = [t.id for t in sch.assigned_tasks]
            print(f"    Sequence: {task_ids}")
            sc_info["team_schedules"].append({
                "team_id": sch.team_id,
                "total_effort": sch.total_effort,
                "switch_cost": sch.context_switch_cost,
                "sequence": task_ids
            })

        results[sc_path.name] = sc_info

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[+] Saved exact results to: {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run Google OR-Tools CP-SAT Exact Solver")
    parser.add_argument("--scenario", default="demo-1", help="Scenario to run (e.g. demo-1, demo-2, demo-3)")
    parser.add_argument("--time-limit", type=float, default=30.0, help="Solver time limit in seconds")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    run_exact([args.scenario], time_limit_sec=args.time_limit, output_path=args.output)


if __name__ == "__main__":
    main()
