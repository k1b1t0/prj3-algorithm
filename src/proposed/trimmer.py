from typing import List, Tuple, Set
from models import Task, Team


def trim_cluster_for_team(
    cluster_tasks: List[Task],
    team: Team,
    skill_threshold: float = 0.5
) -> Tuple[List[Task], List[Task]]:
    # Lam gon cum cong viec cho team (No-DAG Knapsack Selection):
    # 1. Loc cung ky nang: Neu diem ky nang < skill_threshold, loai sang deferred
    # 2. Greedy Knapsack: Nhat task theo ty so r_i / e_i giam dan den tran dung luong
    deferred: List[Task] = []
    valid_tasks: List[Task] = []

    # Buoc 1: Loc theo nguong ky nang
    for t in cluster_tasks:
        if team.get_skill_score(t.skill) >= skill_threshold:
            valid_tasks.append(t)
        else:
            deferred.append(t)

    # Buoc 2: Sap xep theo mat do rui ro
    valid_tasks.sort(key=lambda t: t.r_i / max(1, t.e_i), reverse=True)

    retained: List[Task] = []
    current_sp = 0
    for t in valid_tasks:
        if current_sp + t.e_i <= team.capacity_sp:
            retained.append(t)
            current_sp += t.e_i
        else:
            deferred.append(t)

    return retained, deferred

