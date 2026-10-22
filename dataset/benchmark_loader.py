"""
Benchmark Dataset Loader & Generator.
Quản lý 3 kịch bản chuẩn (small_40, medium_100, large_500) và 5 instances độc lập cho mỗi kịch bản.
Đọc từ kho dữ liệu thực tế (dataset/prj3-dataset-crawl/target) và lưu cache vào dataset/benchmark/.
"""
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any
from models import Task, Team


BENCHMARK_DIR = Path(__file__).resolve().parent / "benchmark"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)


def get_standard_teams(n_teams: int) -> List[Team]:
    """Tạo danh sách n_teams theo chuẩn Scrum (30 SP / team) với kỹ năng OWASP đa dạng."""
    all_profiles = [
        # Team 1: Core & Backend (Mạnh A01, A03, A07)
        {"team_id": "t1", "name": "Team 1 (Core & Backend)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.9, "SKILL_A02": 0.7, "SKILL_A03": 0.85, "SKILL_A04": 0.6,
            "SKILL_A05": 0.65, "SKILL_A06": 0.55, "SKILL_A07": 0.9, "SKILL_A08": 0.6,
            "SKILL_A09": 0.7, "SKILL_A10": 0.65
        }},
        # Team 2: Business & Payment (Mạnh A02, A04, A05)
        {"team_id": "t2", "name": "Team 2 (Business & Payment)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.6, "SKILL_A02": 0.95, "SKILL_A03": 0.65, "SKILL_A04": 0.85,
            "SKILL_A05": 0.9, "SKILL_A06": 0.6, "SKILL_A07": 0.5, "SKILL_A08": 0.7,
            "SKILL_A09": 0.6, "SKILL_A10": 0.75
        }},
        # Team 3: Infra & Gateway (Mạnh A05, A06, A09)
        {"team_id": "t3", "name": "Team 3 (Infra & Gateway)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.55, "SKILL_A02": 0.6, "SKILL_A03": 0.7, "SKILL_A04": 0.65,
            "SKILL_A05": 0.95, "SKILL_A06": 0.9, "SKILL_A07": 0.6, "SKILL_A08": 0.65,
            "SKILL_A09": 0.9, "SKILL_A10": 0.7
        }},
        # Team 4: Security Operations (Mạnh A01, A02, A08, A10)
        {"team_id": "t4", "name": "Team 4 (Security & Ops)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.85, "SKILL_A02": 0.8, "SKILL_A03": 0.6, "SKILL_A04": 0.7,
            "SKILL_A05": 0.8, "SKILL_A06": 0.75, "SKILL_A07": 0.65, "SKILL_A08": 0.95,
            "SKILL_A09": 0.85, "SKILL_A10": 0.95
        }},
        # Team 5: Data & Analytics
        {"team_id": "t5", "name": "Team 5 (Data & Analytics)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.75, "SKILL_A02": 0.6, "SKILL_A03": 0.9, "SKILL_A04": 0.8,
            "SKILL_A05": 0.7, "SKILL_A06": 0.65, "SKILL_A07": 0.7, "SKILL_A08": 0.6,
            "SKILL_A09": 0.65, "SKILL_A10": 0.6
        }},
        # Team 6: Frontend & Client API
        {"team_id": "t6", "name": "Team 6 (Frontend & API)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.7, "SKILL_A02": 0.85, "SKILL_A03": 0.8, "SKILL_A04": 0.6,
            "SKILL_A05": 0.6, "SKILL_A06": 0.55, "SKILL_A07": 0.8, "SKILL_A08": 0.7,
            "SKILL_A09": 0.6, "SKILL_A10": 0.65
        }},
        # Team 7: Platform Engineering
        {"team_id": "t7", "name": "Team 7 (Platform Eng)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.6, "SKILL_A02": 0.7, "SKILL_A03": 0.65, "SKILL_A04": 0.75,
            "SKILL_A05": 0.9, "SKILL_A06": 0.95, "SKILL_A07": 0.6, "SKILL_A08": 0.85,
            "SKILL_A09": 0.9, "SKILL_A10": 0.8
        }},
        # Team 8: Enterprise Integration
        {"team_id": "t8", "name": "Team 8 (Integration)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.8, "SKILL_A02": 0.75, "SKILL_A03": 0.7, "SKILL_A04": 0.9,
            "SKILL_A05": 0.75, "SKILL_A06": 0.8, "SKILL_A07": 0.65, "SKILL_A08": 0.7,
            "SKILL_A09": 0.8, "SKILL_A10": 0.75
        }},
    ]

    selected = all_profiles[:n_teams]
    return [
        Team(
            team_id=p["team_id"],
            name=p["name"],
            capacity_sp=p["capacity_sp"],
            skills=p["skills"]
        )
        for p in selected
    ]


def load_raw_pool() -> List[Dict[str, Any]]:
    """Đọc kho dữ liệu 2.103 task từ raw dataset crawl (chỉ đọc)."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_file = repo_root / "dataset" / "prj3-dataset-crawl" / "target" / "vulnerabilities_backlog.jsonl"
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
    """Sinh 1 instance cho kịch bản và lưu cache vào JSON."""
    cache_path = BENCHMARK_DIR / f"{scenario_name}_inst{instance_idx}.json"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = [
            Task(
                id=t["id"],
                title=t["title"],
                repository=t["repository"],
                asset_module=t["asset_module"],
                r_i=float(t["r_i"]),
                e_i=int(t["e_i"]),
                skill=t["skill"],
                earliest_sprint=int(t.get("earliest_sprint", 1)),
                deadline_sprint=int(t.get("deadline_sprint", 4)),
                predecessors=t.get("predecessors", [])
            )
            for t in data["tasks"]
        ]
        teams = [
            Team(
                team_id=tm["team_id"],
                name=tm["name"],
                capacity_sp=int(tm["capacity_sp"]),
                skills=tm["skills"]
            )
            for tm in data["teams"]
        ]
        return tasks, teams

    # Nếu chưa có cache, bốc mẫu từ raw pool với seed cụ thể
    raw_tasks = load_raw_pool()
    rng = random.Random(seed)

    if raw_tasks:
        # Nhóm task theo module để giữ cấu trúc intra-module DAG
        module_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for t in raw_tasks:
            module_groups[t.get("asset_module", "core")].append(t)

        modules_shuffled = list(module_groups.keys())
        rng.shuffle(modules_shuffled)

        selected_raw: List[Dict[str, Any]] = []
        for m in modules_shuffled:
            mod_tasks = list(module_groups[m])
            rng.shuffle(mod_tasks)
            take_count = min(len(mod_tasks), max(5, target_tasks // 4))
            selected_raw.extend(mod_tasks[:take_count])
            if len(selected_raw) >= target_tasks:
                break

        selected_raw = selected_raw[:target_tasks]
    else:
        # Fallback tổng hợp nếu không có file gốc
        selected_raw = []
        repos = ["train-ticket", "skywalking", "spring-petclinic", "piggy-metrics"]
        skills = [f"SKILL_A{i:02d}" for i in range(1, 11)]
        for i in range(1, target_tasks + 1):
            repo = rng.choice(repos)
            mod = f"{repo}-mod-{rng.randint(1, 5)}"
            skill = rng.choice(skills)
            r_i = round(rng.uniform(3.0, 9.8), 1)
            e_i = rng.randint(2, 6)
            preds = [i - 1] if i > 1 and rng.random() < 0.15 else []
            selected_raw.append({
                "id": i,
                "title": f"Vuln-{i}",
                "repository": repo,
                "asset_module": mod,
                "r_i": r_i,
                "e_i": e_i,
                "skill": skill,
                "earliest_sprint": rng.randint(1, 3),
                "deadline_sprint": rng.randint(3, 5),
                "predecessors": preds
            })

    selected_ids = {t["id"] for t in selected_raw}
    cleaned_tasks = []
    for t in selected_raw:
        valid_preds = [p for p in t.get("predecessors", []) if p in selected_ids]
        cleaned_tasks.append({
            "id": t["id"],
            "title": t.get("title", f"Task {t['id']}"),
            "repository": t.get("repository", "repo1"),
            "asset_module": t.get("asset_module", "mod1"),
            "r_i": float(t.get("r_i", 5.0)),
            "e_i": int(t.get("e_i", 3)),
            "skill": t.get("skill", "SKILL_A01"),
            "earliest_sprint": int(t.get("earliest_sprint", 1)),
            "deadline_sprint": int(t.get("deadline_sprint", 4)),
            "predecessors": valid_preds
        })

    teams_obj = get_standard_teams(n_teams)
    teams_dict_list = [
        {
            "team_id": tm.team_id,
            "name": tm.name,
            "capacity_sp": tm.capacity_sp,
            "skills": tm.skills
        }
        for tm in teams_obj
    ]

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
            deadline_sprint=t["deadline_sprint"],
            predecessors=t["predecessors"]
        )
        for t in cleaned_tasks
    ]

    return tasks_result, teams_obj
