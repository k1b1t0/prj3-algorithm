from typing import List, Tuple, Set
from models import Task, Team


def trim_cluster_for_team(
    cluster_tasks: List[Task],
    team: Team,
    skill_threshold: float = 0.5,
    current_sprint: int = 4,
    alpha: float = 0.5,
    m_penalty: float = 50.0
) -> Tuple[List[Task], List[Task]]:
    """
    Loc va chon loc task cho team (Knapsack 0-1 theo mat do u_i / e_i):
    1. Loc ky nang: k_{t, skill} >= skill_threshold.
    2. Knapsack: sap xep giam dan theo u_i / e_i, nhat den tran dung luong cap_t.
    """
    deferred: List[Task] = []
    valid_tasks: List[Task] = []

    # 1. Loc theo nguong ky nang
    for t in cluster_tasks:
        if team.get_skill_score(t.skill) >= skill_threshold:
            valid_tasks.append(t)
        else:
            deferred.append(t)

    # 2. Sap xep theo mat do utility / effort
    valid_tasks.sort(
        key=lambda t: t.compute_utility(current_sprint, alpha, m_penalty) / max(1, t.e_i),
        reverse=True
    )

    retained: List[Task] = []
    current_sp = 0
    for t in valid_tasks:
        if current_sp + t.e_i <= team.capacity_sp:
            retained.append(t)
            current_sp += t.e_i
        else:
            deferred.append(t)

    return retained, deferred
