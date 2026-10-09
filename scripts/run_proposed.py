"""Runner for executing Proposed Algorithm (ESSC + Hungarian + DP) on scenarios."""
import argparse
import json
import sys
from pathlib import Path

# Add project root and src/ to path so this script can run standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from models import Task, Team
from proposed.pipeline import solve_proposed_pipeline


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


def run_proposed(scenario_files=None, output_path=None):
    dataset_dir = PROJECT_ROOT / "dataset"
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if scenario_files is None:
        scenario_files = ["demo-1.json", "demo-2.json", "demo-3.json"]
    if output_path is None:
        output_path = outputs_dir / "proposed_results.json"
    else:
        output_path = Path(output_path)

    results = {}

    for demo_file in scenario_files:
        file_path = dataset_dir / demo_file if not Path(demo_file).is_absolute() and not Path(demo_file).exists() else Path(demo_file)
        if not file_path.exists():
            print(f"[Warning] Scenario file not found: {file_path}")
            continue

        name, tasks, teams = load_scenario(file_path)
        print(f"--- Running Proposed Algorithm on {name} ---")
        plan = solve_proposed_pipeline(tasks, teams)

        scenario_res = {
            "scenario": name,
            "metrics": {
                "total_risk_resolved": plan.total_risk_resolved,
                "total_risk_deferred": plan.total_risk_deferred,
                "total_switch_cost": plan.total_switch_cost,
                "skill_match_score": plan.skill_match_score,
                "dag_violations": plan.dag_violations
            },
            "team_schedules": []
        }

        for sch in plan.schedules:
            sch_info = {
                "team_id": sch.team_id,
                "total_effort": sch.total_effort,
                "switch_cost": sch.context_switch_cost,
                "n_tasks": len(sch.assigned_tasks),
                "tasks_sequence": [
                    {
                        "id": t.id,
                        "module": t.asset_module,
                        "skill": t.skill,
                        "risk": t.r_i,
                        "effort": t.e_i,
                        "preds": t.predecessors
                    }
                    for t in sch.assigned_tasks
                ]
            }
            scenario_res["team_schedules"].append(sch_info)
            print(f"  Team {sch.team_id}: {sch_info['n_tasks']} tasks, Effort: {sch.total_effort} SP, Switch Cost: {sch.context_switch_cost}")

        print(f"  Summary: Risk Resolved={plan.total_risk_resolved}, Switch Cost={plan.total_switch_cost}, SMS={plan.skill_match_score}, DAG Violations={plan.dag_violations}\n")
        results[file_path.name] = scenario_res

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Proposed results successfully written to: {output_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Run Proposed Scheduling Algorithm")
    parser.add_argument("--scenarios", nargs="*", default=None, help="Scenario json files to run (default: demo-1.json, demo-2.json, demo-3.json)")
    parser.add_argument("--output", default=None, help="Path to save output results JSON")
    args = parser.parse_args()

    run_proposed(scenario_files=args.scenarios, output_path=args.output)


if __name__ == "__main__":
    main()
