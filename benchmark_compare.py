import json
import sys
from pathlib import Path
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


def run_benchmark():
    base_dir = Path(__file__).resolve().parent
    dataset_dir = base_dir / "dataset"
    scenarios = ["demo-1.json", "demo-2.json", "demo-3.json"]

    print("=" * 86)
    print(f"{'BENCHMARK COMPARISON: PROPOSED (ESSC+DP) vs BASELINES':^86}")
    print("=" * 86)

    all_results = {}

    for sc_file in scenarios:
        sc_path = dataset_dir / sc_file
        if not sc_path.exists():
            continue

        name, tasks, teams = load_scenario(sc_path)
        print(f"\n>>> SCENARIO: {name} (N={len(tasks)} tasks, |T|={len(teams)} teams)")
        print(f"{'Method':<26} | {'Risk Resolved':<14} | {'Switch Cost':<12} | {'SMS (0-1)':<10} | {'DAG Violations':<14}")
        print("-" * 86)

        # 1. Proposed Algorithm
        plan_prop = solve_proposed_pipeline(tasks, teams)
        print(f"{'1. Proposed (ESSC+DP)':<26} | {plan_prop.total_risk_resolved:<14.1f} | {plan_prop.total_switch_cost:<12.2f} | {plan_prop.skill_match_score:<10.3f} | {plan_prop.dag_violations:<14}")

        # 2. Baseline 1: Greedy-CVSS
        plan_greedy = solve_greedy_cvss(tasks, teams)
        print(f"{'2. Baseline Greedy-CVSS':<26} | {plan_greedy.total_risk_resolved:<14.1f} | {plan_greedy.total_switch_cost:<12.2f} | {plan_greedy.skill_match_score:<10.3f} | {plan_greedy.dag_violations:<14}")

        # 3. Baseline 2: Knapsack + Kahn Topo
        plan_knap = solve_knapsack_topo(tasks, teams)
        print(f"{'3. Baseline Knapsack-Topo':<26} | {plan_knap.total_risk_resolved:<14.1f} | {plan_knap.total_switch_cost:<12.2f} | {plan_knap.skill_match_score:<10.3f} | {plan_knap.dag_violations:<14}")

        # Tinh ty le giam chi phi Switch Cost so voi baselines
        sw_base = min(plan_greedy.total_switch_cost, plan_knap.total_switch_cost) if min(plan_greedy.total_switch_cost, plan_knap.total_switch_cost) > 0 else 1.0
        diff_pct = (1.0 - plan_prop.total_switch_cost / sw_base) * 100
        print(f"--> Proposed reduces Context Switch Cost by: {diff_pct:+.1f}% compared to best baseline!")

        all_results[sc_file] = {
            "scenario": name,
            "proposed": {
                "risk_resolved": plan_prop.total_risk_resolved,
                "switch_cost": plan_prop.total_switch_cost,
                "sms": plan_prop.skill_match_score,
                "dag_violations": plan_prop.dag_violations
            },
            "greedy_cvss": {
                "risk_resolved": plan_greedy.total_risk_resolved,
                "switch_cost": plan_greedy.total_switch_cost,
                "sms": plan_greedy.skill_match_score,
                "dag_violations": plan_greedy.dag_violations
            },
            "knapsack_topo": {
                "risk_resolved": plan_knap.total_risk_resolved,
                "switch_cost": plan_knap.total_switch_cost,
                "sms": plan_knap.skill_match_score,
                "dag_violations": plan_knap.dag_violations
            }
        }

    # Ghi file tong hop ket qua
    out_file = base_dir / "benchmark_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nFull benchmark summary written to: {out_file}\n")


if __name__ == "__main__":
    run_benchmark()
