"""Runner for benchmarking Proposed Algorithm vs Baselines across scenarios."""
import argparse
import json
import sys
from pathlib import Path

# Add project root and src/ to path so this script can run standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from models import Task, Team
from proposed.pipeline import solve_proposed_pipeline
from baselines.greedy_cvss import solve_greedy_cvss
from baselines.knapsack_topo import solve_knapsack_topo


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

    print("=" * 86)
    print(f"{'BENCHMARK COMPARISON: PROPOSED (ESSC+DP) vs BASELINES':^86}")
    print("=" * 86)

    all_results = {}

    for sc_file in scenario_files:
        sc_path = dataset_dir / sc_file if not Path(sc_file).is_absolute() and not Path(sc_file).exists() else Path(sc_file)
        if not sc_path.exists():
            print(f"[Warning] Scenario file not found: {sc_path}")
            continue

        name, tasks, teams = load_scenario(sc_path)
        print(f"\n>>> SCENARIO: {name} (N={len(tasks)} tasks, |T|={len(teams)} teams)")
        print(f"{'Method':<26} | {'Risk Resolved':<14} | {'Switch Cost':<12} | {'SMS (0-1)':<10} | {'DAG Violations':<14}")
        print("-" * 86)

        # 1. Proposed Algorithm
        plan_prop = solve_proposed_pipeline(tasks, teams)
        print(f"{'1. Proposed (ESSC+DP)':<26} | {plan_prop.total_risk_resolved:<14.1f} | {plan_prop.total_switch_cost:<12.2f} | {plan_prop.skill_match_score:<10.3f} | {plan_prop.dag_violations:<14}")

        # 2. Baseline 1: Greedy CVSS
        plan_greedy = solve_greedy_cvss(tasks, teams)
        print(f"{'2. Greedy CVSS':<26} | {plan_greedy.total_risk_resolved:<14.1f} | {plan_greedy.total_switch_cost:<12.2f} | {plan_greedy.skill_match_score:<10.3f} | {plan_greedy.dag_violations:<14}")

        # 3. Baseline 2: Knapsack Topo
        plan_knap = solve_knapsack_topo(tasks, teams)
        print(f"{'3. Knapsack Topo':<26} | {plan_knap.total_risk_resolved:<14.1f} | {plan_knap.total_switch_cost:<12.2f} | {plan_knap.skill_match_score:<10.3f} | {plan_knap.dag_violations:<14}")

        all_results[sc_path.name] = {
            "scenario": name,
            "tasks_count": len(tasks),
            "teams_count": len(teams),
            "proposed": {
                "risk_resolved": plan_prop.total_risk_resolved,
                "switch_cost": plan_prop.total_switch_cost,
                "sms": plan_prop.skill_match_score,
                "dag_violations": plan_prop.dag_violations,
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
                "team_schedules": [
                    {
                        "team_id": r.team_id,
                        "tasks_sequence": [t.id for t in r.assigned_tasks]
                    } for r in plan_greedy.schedules
                ]
            },
            "knapsack_topo": {
                "risk_resolved": plan_knap.total_risk_resolved,
                "switch_cost": plan_knap.total_switch_cost,
                "sms": plan_knap.skill_match_score,
                "dag_violations": plan_knap.dag_violations,
                "team_schedules": [
                    {
                        "team_id": r.team_id,
                        "tasks_sequence": [t.id for t in r.assigned_tasks]
                    } for r in plan_knap.schedules
                ]
            }
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nFull benchmark summary written to: {output_path}\n")
    return all_results


def main():
    parser = argparse.ArgumentParser(description="Run Benchmark: Proposed vs Baselines")
    parser.add_argument("--scenarios", nargs="*", default=None, help="Scenario json files to run (default: demo-1.json, demo-2.json, demo-3.json)")
    parser.add_argument("--output", default=None, help="Path to save benchmark summary JSON")
    args = parser.parse_args()

    run_benchmark(scenario_files=args.scenarios, output_path=args.output)


if __name__ == "__main__":
    main()
