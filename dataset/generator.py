"""
Dataset generator for prj3-algo-no-dag.
Extracts tasks and teams from vulnerabilities_backlog.jsonl and teams.jsonl.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


def load_raw_data(data_dir: Path):
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


def select_module_tasks(module_tasks: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
    return module_tasks[:target_count]


def build_scenario(selected_tasks: List[Dict[str, Any]], teams: List[Dict[str, Any]], scenario_name: str) -> Dict[str, Any]:
    cleaned_tasks = []
    for t in selected_tasks:
        cleaned_tasks.append({
            "id": t["id"],
            "title": t.get("title", ""),
            "repository": t.get("repository", ""),
            "asset_module": t.get("asset_module", ""),
            "r_i": float(t.get("r_i", 5.0)),
            "e_i": int(t.get("e_i", 3)),
            "skill": t.get("skill", "SKILL_A01"),
            "earliest_sprint": int(t.get("earliest_sprint", 1)),
            "deadline_sprint": int(t.get("deadline_sprint", 4))
        })

    total_effort = sum(t["e_i"] for t in cleaned_tasks)
    total_risk = round(sum(t["r_i"] for t in cleaned_tasks), 2)
    total_capacity = sum(tm["capacity_sp"] for tm in teams)

    return {
        "scenario_name": scenario_name,
        "metadata": {
            "n_tasks": len(cleaned_tasks),
            "n_teams": len(teams),
            "total_effort_sp": total_effort,
            "total_capacity_sp": total_capacity,
            "total_risk": total_risk
        },
        "teams": teams,
        "tasks": cleaned_tasks
    }
