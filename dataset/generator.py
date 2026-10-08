"""
Dataset generator for prj3-algorithm.
Trich xuat du lieu tu vulnerabilities_backlog.jsonl va teams.jsonl thanh 3 tap demo JSON:
- demo-1.json: Quy mo nho (2 teams, 20 tasks, chuoi DAG ro ret trong train-ticket modules)
- demo-2.json: Quy mo chuan (3 teams, 40 tasks, can cat tia PCKP)
- demo-3.json: Quy mo lon (4 teams, 60 tasks, nhieu modules va skills)
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def load_raw_data(data_dir: Path):
    # Doc backlog va teams tu thu muc crawl
    tasks = []
    with open(data_dir / "vulnerabilities_backlog.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))

    teams = []
    with open(data_dir / "teams.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                teams.append(json.loads(line))

    return tasks, teams


def select_connected_subgraph(module_tasks: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
    # Chon tap task co ket noi DAG manh nhat (bao gom ca nut goc va nut con)
    # Tim cac task co predecessors
    task_map = {t["id"]: t for t in module_tasks}
    
    # Tim cac nut goc (duoc tro den nhieu nhat)
    pred_counts = {}
    for t in module_tasks:
        for p in t.get("predecessors", []):
            if p in task_map:
                pred_counts[p] = pred_counts.get(p, 0) + 1

    selected_ids = set()
    # Uu tien dua nut goc quan trong vao truoc
    for root_id in sorted(pred_counts.keys(), key=lambda k: pred_counts[k], reverse=True):
        if len(selected_ids) >= target_count:
            break
        selected_ids.add(root_id)
        # Them cac nut con truc tiep cua nut goc nay
        for t in module_tasks:
            if root_id in t.get("predecessors", []) and len(selected_ids) < target_count:
                selected_ids.add(t["id"])

    # Neu chua du target_count, lay them cac task con lai trong module
    for t in module_tasks:
        if len(selected_ids) >= target_count:
            break
        selected_ids.add(t["id"])

    return [task_map[tid] for tid in selected_ids]


def build_scenario(selected_tasks: List[Dict[str, Any]], teams: List[Dict[str, Any]], scenario_name: str) -> Dict[str, Any]:
    # Chi giu cac predecessor nam trong tap task duoc chon de dam bao DAG hop le
    selected_ids = {t["id"] for t in selected_tasks}
    
    cleaned_tasks = []
    for t in selected_tasks:
        preds = [p for p in t.get("predecessors", []) if p in selected_ids]
        cleaned_tasks.append({
            "id": t["id"],
            "title": t.get("title", ""),
            "repository": t.get("repository", ""),
            "asset_module": t.get("asset_module", ""),
            "r_i": float(t.get("r_i", 5.0)),
            "e_i": int(t.get("e_i", 3)),
            "skill": t.get("skill", "SKILL_A01"),
            "earliest_sprint": int(t.get("earliest_sprint", 1)),
            "deadline_sprint": int(t.get("deadline_sprint", 4)),
            "predecessors": preds
        })

    total_effort = sum(t["e_i"] for t in cleaned_tasks)
    total_risk = round(sum(t["r_i"] for t in cleaned_tasks), 2)
    total_edges = sum(len(t["predecessors"]) for t in cleaned_tasks)
    total_capacity = sum(tm["capacity_sp"] for tm in teams)

    return {
        "scenario_name": scenario_name,
        "metadata": {
            "n_tasks": len(cleaned_tasks),
            "n_teams": len(teams),
            "total_effort_sp": total_effort,
            "total_capacity_sp": total_capacity,
            "total_risk": total_risk,
            "total_dag_edges": total_edges
        },
        "teams": teams,
        "tasks": cleaned_tasks
    }


def generate_datasets():
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = repo_root / "dataset" / "prj3-dataset-crawl" / "target"
    out_dir = Path(__file__).resolve().parent

    tasks, raw_teams = load_raw_data(raw_dir)

    # Chuan hoa thong tin 4 teams
    team_t1 = {
        "team_id": "t1",
        "name": "Team 1 (Core & Backend)",
        "capacity_sp": 30,
        "skills": raw_teams[0]["skills"]
    }
    team_t2 = {
        "team_id": "t2",
        "name": "Team 2 (Business & Payment)",
        "capacity_sp": 30,
        "skills": raw_teams[1]["skills"]
    }
    team_t3 = {
        "team_id": "t3",
        "name": "Team 3 (Infra & Gateway)",
        "capacity_sp": 30,
        "skills": raw_teams[2]["skills"]
    }
    team_t4 = {
        "team_id": "t4",
        "name": "Team 4 (Security & Operations)",
        "capacity_sp": 30,
        "skills": {
            "SKILL_A01": 0.8, "SKILL_A02": 0.7, "SKILL_A03": 0.5, "SKILL_A04": 0.6,
            "SKILL_A05": 0.9, "SKILL_A06": 0.85, "SKILL_A07": 0.5, "SKILL_A08": 0.6,
            "SKILL_A09": 0.95, "SKILL_A10": 0.9
        }
    }

    # 1. DEMO-1: 2 teams (t1, t2), 20 tasks
    # Lay 10 tasks tu ts-order-service va 10 tasks tu ts-station-service (cung repo train-ticket)
    order_tasks = [t for t in tasks if t["asset_module"] == "ts-order-service"]
    station_tasks = [t for t in tasks if t["asset_module"] == "ts-station-service"]
    
    sub1 = select_connected_subgraph(order_tasks, 10)
    sub2 = select_connected_subgraph(station_tasks, 10)
    selected_demo1 = sub1 + sub2

    scenario_1 = build_scenario(selected_demo1, [team_t1, team_t2], "demo-1 (Small & Dense DAG)")
    with open(out_dir / "demo-1.json", "w", encoding="utf-8") as f:
        json.dump(scenario_1, f, indent=2, ensure_ascii=False)
    print(f"Generated demo-1.json: {scenario_1['metadata']}")

    # 2. DEMO-2: 3 teams (t1, t2, t3), 40 tasks (Tong dung luong 90 SP, effort ~120-130 SP can cat tia)
    # Lay tu 3 modules: ts-order-service (15), ts-order-other-service (15), ts-station-service (10)
    other_order_tasks = [t for t in tasks if t["asset_module"] == "ts-order-other-service"]
    
    sub_d2_1 = select_connected_subgraph(order_tasks, 15)
    sub_d2_2 = select_connected_subgraph(other_order_tasks, 15)
    sub_d2_3 = select_connected_subgraph(station_tasks, 10)
    selected_demo2 = sub_d2_1 + sub_d2_2 + sub_d2_3

    scenario_2 = build_scenario(selected_demo2, [team_t1, team_t2, team_t3], "demo-2 (Standard Sprint & Trimming)")
    with open(out_dir / "demo-2.json", "w", encoding="utf-8") as f:
        json.dump(scenario_2, f, indent=2, ensure_ascii=False)
    print(f"Generated demo-2.json: {scenario_2['metadata']}")

    # 3. DEMO-3: 4 teams (t1, t2, t3, t4), 60 tasks (Tong dung luong 120 SP, effort ~180-200 SP)
    # Ket hop 2 repo: train-ticket (ts-order-service, ts-order-other-service, ts-station-service) va skywalking (skywalking-webui)
    sky_tasks = [t for t in tasks if t["asset_module"] == "skywalking-webui"]
    food_tasks = [t for t in tasks if t["asset_module"] == "ts-food-service"]

    sub_d3_1 = select_connected_subgraph(order_tasks, 15)
    sub_d3_2 = select_connected_subgraph(other_order_tasks, 15)
    sub_d3_3 = select_connected_subgraph(station_tasks, 10)
    sub_d3_4 = select_connected_subgraph(sky_tasks, 12)
    sub_d3_5 = select_connected_subgraph(food_tasks, 8)
    selected_demo3 = sub_d3_1 + sub_d3_2 + sub_d3_3 + sub_d3_4 + sub_d3_5

    scenario_3 = build_scenario(selected_demo3, [team_t1, team_t2, team_t3, team_t4], "demo-3 (Stress Test & High Contention)")
    with open(out_dir / "demo-3.json", "w", encoding="utf-8") as f:
        json.dump(scenario_3, f, indent=2, ensure_ascii=False)
    print(f"Generated demo-3.json: {scenario_3['metadata']}")


if __name__ == "__main__":
    generate_datasets()
