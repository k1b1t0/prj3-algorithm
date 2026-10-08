from typing import List, Dict, Set
from collections import deque
from models import Task, Team, ScheduleResult, SprintPlan
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan


def _kahn_topological_sort(tasks: List[Task]) -> List[Task]:
    # Sap xep thu tu thuan topo co ban (Kahn's algorithm)
    # Khong he toi uu hoa ham chi phi khoang cach C_ij
    if len(tasks) <= 1:
        return tasks

    task_map = {t.id: t for t in tasks}
    current_ids = set(task_map.keys())

    # Tinh in-degree trong do thi con
    in_degree = {tid: 0 for tid in current_ids}
    adj = {tid: [] for tid in current_ids}

    for t in tasks:
        for p in t.predecessors:
            if p in current_ids:
                adj[p].append(t.id)
                in_degree[t.id] += 1

    # Queue chua cac task co in-degree == 0
    queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
    ordered_ids = []

    while queue:
        u = queue.popleft()
        ordered_ids.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # Truong hop phong ve neu co task chua vao
    for tid in current_ids:
        if tid not in ordered_ids:
            ordered_ids.append(tid)

    return [task_map[tid] for tid in ordered_ids]


def solve_knapsack_topo(
    tasks: List[Task],
    teams: List[Team],
    skill_threshold: float = 0.5
) -> SprintPlan:
    # Baseline 2: Knapsack doc lap + Topological Sort co ban
    # 1. Sap xep task theo ty so r_i / e_i giam dan
    # 2. Gan cho team co ky nang hop le bang knapsack greedy
    # 3. Thu tu thuc hien chi sap xep theo Kahn Topological Sort, khong toi uu context switch C_ij
    sorted_tasks = sorted(tasks, key=lambda t: t.r_i / t.e_i, reverse=True)
    teams_dict = {tm.team_id: tm for tm in teams}

    team_assigned: Dict[str, List[Task]] = {tm.team_id: [] for tm in teams}
    team_efforts: Dict[str, int] = {tm.team_id: 0 for tm in teams}
    assigned_ids: Set[int] = set()

    for task in sorted_tasks:
        # Kiem tra neu cha da duoc nhan chua
        all_parents_done = all(p in assigned_ids for p in task.predecessors)
        if not all_parents_done:
            continue

        # Tim team con cho va phu hop ky nang
        for tm in teams:
            rem_cap = tm.capacity_sp - team_efforts[tm.team_id]
            if rem_cap >= task.e_i and tm.get_skill_score(task.skill) >= skill_threshold:
                team_assigned[tm.team_id].append(task)
                team_efforts[tm.team_id] += task.e_i
                assigned_ids.add(task.id)
                break

    # Sap xep thu tu bang Kahn Topological Sort co ban
    schedules: List[ScheduleResult] = []
    for tm in teams:
        assigned = team_assigned[tm.team_id]
        ordered = _kahn_topological_sort(assigned)
        effort = sum(t.e_i for t in ordered)
        cost = evaluate_schedule_switch_cost(ordered)
        schedules.append(ScheduleResult(
            team_id=tm.team_id,
            assigned_tasks=ordered,
            total_effort=effort,
            context_switch_cost=cost
        ))

    return evaluate_sprint_plan(tasks, schedules, teams_dict)
