"""
Benchmark Dataset Loader & Instance Generator.
Loads benchmark scenarios (small_40, medium_100, large_500) and caches to dataset/benchmark/.
"""
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any
from models import Task, Team
from dataset.teams import get_standard_teams

BENCHMARK_DIR = Path(__file__).resolve().parent / "benchmark"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_pool() -> List[Dict[str, Any]]:
    """Doc kho du lieu 2.103 task tu raw dataset crawl (read-only)."""
    raw_file = Path(__file__).resolve().parent.parent.parent / "dataset" / "prj3-dataset-crawl" / "target" / "vulnerabilities_backlog.jsonl"
    tasks = []
    if raw_file.exists():
        with open(raw_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
    return tasks


def generate_scenario_instance(
    scenario_name: str,
    target_tasks: int,
    n_teams: int,
    instance_idx: int,
    seed: int
) -> Tuple[List[Task], List[Team]]:
    """Load or generate 1 instance for the scenario, returning (tasks, teams)."""
    cache_path = BENCHMARK_DIR / f"{scenario_name}_inst{instance_idx}.json"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = [
            Task(
                id=int(t["id"]),
                title=str(t["title"]),
                repository=str(t["repository"]),
                asset_module=str(t["asset_module"]),
                r_i=float(t["r_i"]),
                e_i=int(t["e_i"]),
                skill=str(t["skill"]),
                earliest_sprint=int(t.get("earliest_sprint", 1)),
                deadline_sprint=int(t.get("deadline_sprint", 4))
            )
            for t in data["tasks"]
        ]
        teams = [
            Team(
                team_id=str(tm["team_id"]),
                name=str(tm["name"]),
                capacity_sp=int(tm["capacity_sp"]),
                skills=tm["skills"]
            )
            for tm in data["teams"]
        ]
        return tasks, teams

    raw_tasks = load_raw_pool()
    rng = random.Random(seed)

    if raw_tasks:
        module_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for t in raw_tasks:
            module_groups[t.get("asset_module", "core")].append(t)

        modules_shuffled = list(module_groups.keys())
        rng.shuffle(modules_shuffled)

        selected_raw: List[Dict[str, Any]] = []
        seen_ids = set()
        for m in modules_shuffled:
            mod_tasks = list(module_groups[m])
            rng.shuffle(mod_tasks)
            take_count = min(len(mod_tasks), max(5, target_tasks // 4))
            added = 0
            for t in mod_tasks:
                if t["id"] not in seen_ids:
                    seen_ids.add(t["id"])
                    selected_raw.append(t)
                    added += 1
                    if added >= take_count or len(selected_raw) >= target_tasks:
                        break
            if len(selected_raw) >= target_tasks:
                break
    else:
        selected_raw = []
        repos = ["train-ticket", "skywalking", "spring-petclinic", "piggy-metrics"]
        skills = [f"SKILL_A{i:02d}" for i in range(1, 11)]
        for i in range(1, target_tasks + 1):
            repo = rng.choice(repos)
            selected_raw.append({
                "id": i,
                "title": f"Vuln-{i}",
                "repository": repo,
                "asset_module": f"{repo}-mod-{rng.randint(1, 5)}",
                "r_i": round(rng.uniform(3.0, 9.8), 1),
                "e_i": rng.randint(2, 6),
                "skill": rng.choice(skills),
                "earliest_sprint": rng.randint(1, 3),
                "deadline_sprint": rng.randint(3, 5)
            })

    cleaned_tasks = [
        {
            "id": t["id"],
            "title": t.get("title", f"Task {t['id']}"),
            "repository": t.get("repository", "repo1"),
            "asset_module": t.get("asset_module", "mod1"),
            "r_i": float(t.get("r_i", 5.0)),
            "e_i": int(t.get("e_i", 3)),
            "skill": t.get("skill", "SKILL_A01"),
            "earliest_sprint": int(t.get("earliest_sprint", 1)),
            "deadline_sprint": int(t.get("deadline_sprint", 4))
        }
        for t in selected_raw
    ]

    teams_obj = get_standard_teams(n_teams)
    teams_dict_list = [tm.to_dict() for tm in teams_obj]

    scenario_data = {
        "scenario_name": f"{scenario_name}_inst{instance_idx}",
        "metadata": {
            "target_tasks": target_tasks,
            "n_tasks": len(cleaned_tasks),
            "n_teams": n_teams,
            "total_capacity_sp": sum(tm.capacity_sp for tm in teams_obj),
            "total_effort_sp": sum(t["e_i"] for t in cleaned_tasks),
            "instance_idx": instance_idx,
            "seed": seed
        },
        "teams": teams_dict_list,
        "tasks": cleaned_tasks
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, indent=2, ensure_ascii=False)

    tasks_result = [
        Task(
            id=t["id"],
            title=t["title"],
            repository=t["repository"],
            asset_module=t["asset_module"],
            r_i=t["r_i"],
            e_i=t["e_i"],
            skill=t["skill"],
            earliest_sprint=t["earliest_sprint"],
            deadline_sprint=t["deadline_sprint"]
        )
        for t in cleaned_tasks
    ]
    return tasks_result, teams_obj
