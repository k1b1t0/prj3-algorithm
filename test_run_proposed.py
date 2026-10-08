import json
import sys
from pathlib import Path
from prj3_algorithm.models import Task, Team
from prj3_algorithm.proposed.pipeline import solve_proposed_pipeline


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


def run_proposed_on_scenarios():
    base_dir = Path(__file__).resolve().parent
    dataset_dir = base_dir / "dataset"
    results = {}

    for demo_file in ["demo-1.json", "demo-2.json", "demo-3.json"]:
        file_path = dataset_dir / demo_file
        if not file_path.exists():
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
        results[demo_file] = scenario_res

    # Ghi ket qua ra file output json de kiem tra
    out_file = base_dir / "proposed_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results written to: {out_file}")


if __name__ == "__main__":
    run_proposed_on_scenarios()
