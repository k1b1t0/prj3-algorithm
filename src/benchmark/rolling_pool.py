"""
Backlog cohort pool generator for Plan B: Multi-Sprint Rolling Benchmark.
"""
import random
from collections import defaultdict
from typing import Dict, List, Any
from models import Task
from dataset.benchmark_loader import load_raw_pool


def generate_rolling_backlog_pool(
    seed: int,
    tasks_per_sprint: int = 25,
    num_sprints: int = 8
) -> Dict[int, List[Task]]:
    """Generates deterministic cohort of tasks arriving at each sprint s in [1..num_sprints]."""
    raw_tasks = load_raw_pool()
    rng = random.Random(seed)
    sprint_cohorts: Dict[int, List[Task]] = defaultdict(list)

    if raw_tasks:
        by_sprint: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for t in raw_tasks:
            s = int(t.get("earliest_sprint", 1))
            by_sprint[s].append(t)

        for s in range(1, num_sprints + 1):
            available = list(by_sprint[s])
            rng.shuffle(available)
            for d in available[:tasks_per_sprint]:
                sprint_cohorts[s].append(Task(
                    id=int(d["id"]),
                    title=str(d.get("title", f"Task {d['id']}")),
                    repository=str(d.get("repository", "repo1")),
                    asset_module=str(d.get("asset_module", "mod1")),
                    r_i=float(d.get("r_i", 5.0)),
                    e_i=int(d.get("e_i", 3)),
                    skill=str(d.get("skill", "SKILL_A01")),
                    earliest_sprint=s,
                    deadline_sprint=int(d.get("deadline_sprint", min(num_sprints, s + 3)))
                ))
    else:
        repos = ["train-ticket", "skywalking", "spring-petclinic", "piggy-metrics"]
        skills = [f"SKILL_A{i:02d}" for i in range(1, 11)]
        tid = 1
        for s in range(1, num_sprints + 1):
            for _ in range(tasks_per_sprint):
                sprint_cohorts[s].append(Task(
                    id=tid,
                    title=f"Task-{tid}",
                    repository=rng.choice(repos),
                    asset_module=f"mod-{rng.randint(1, 5)}",
                    r_i=round(rng.uniform(3.0, 9.8), 1),
                    e_i=rng.randint(2, 6),
                    skill=rng.choice(skills),
                    earliest_sprint=s,
                    deadline_sprint=min(num_sprints, s + rng.randint(2, 4))
                ))
                tid += 1

    return sprint_cohorts

