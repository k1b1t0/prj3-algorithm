from typing import List, Dict
from models import Task, Team, ScheduleResult, SprintPlan
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan


def solve_greedy_cvss(
    tasks: List[Task],
    teams: List[Team],
    skill_threshold: float = 0.5
) -> SprintPlan:
    # Baseline 1: Greedy-CVSS (Cach pho bien trong doanh nghiep)
    # 1. Sap xep backlog giam dan theo diem rui ro r_i
    # 2. Nhặt lần lượt từng task, gán cho team phù hợp còn đủ chỗ
    # 3. Giữ nguyên thứ tự nhặt task làm workflow của team
    sorted_tasks = sorted(tasks, key=lambda t: t.r_i, reverse=True)
    teams_dict = {tm.team_id: tm for tm in teams}
    
    team_assigned: Dict[str, List[Task]] = {tm.team_id: [] for tm in teams}
    team_efforts: Dict[str, int] = {tm.team_id: 0 for tm in teams}
    assigned_ids = set()

    for task in sorted_tasks:
        # Kiem tra xem tat ca cac cha cua task nay da duoc nhan lam chua
        all_parents_done = all(p in assigned_ids for p in task.predecessors)
        if not all_parents_done:
            # Neu cha chua duoc lam thi khong the nhan task nay
            continue

        # Tim team co ky nang thoa man va con du capacity
        best_team = None
        for tm in teams:
            rem_cap = tm.capacity_sp - team_efforts[tm.team_id]
            if rem_cap >= task.e_i and tm.get_skill_score(task.skill) >= skill_threshold:
                best_team = tm
                break

        if best_team is not None:
            team_assigned[best_team.team_id].append(task)
            team_efforts[best_team.team_id] += task.e_i
            assigned_ids.add(task.id)

    # Dong goi ScheduleResult cho tung team
    schedules: List[ScheduleResult] = []
    for tm in teams:
        assigned = team_assigned[tm.team_id]
        effort = team_efforts[tm.team_id]
        cost = evaluate_schedule_switch_cost(assigned)
        schedules.append(ScheduleResult(
            team_id=tm.team_id,
            assigned_tasks=assigned,
            total_effort=effort,
            context_switch_cost=cost
        ))

    return evaluate_sprint_plan(tasks, schedules, teams_dict)
