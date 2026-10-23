from typing import List, Dict, Tuple
from models import Task, Team, ScheduleResult, SprintPlan
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan
from solvers.proposed_4phase.dp_sequencing import sequence_tasks_dp
from solvers.proposed_nsga2.chromosome import Chromosome


def decode_chromosome(
    chrom: Chromosome,
    tasks: List[Task],
    teams: List[Team],
    current_sprint: int = 4,
    skill_threshold: float = 0.5,
    apply_memetic_dp: bool = True
) -> SprintPlan:
    """
    Bo giai ma uu tien (Priority Decoder):
    Duyet tuan tu theo danh sach uu tien.
    Dam bao 100% phuong an sinh ra deu KHA THI (dung capacity, dung skill).
    Thanh phan Memetic: Toi uu hoa chuoi noi bo tung team bang sequence_tasks_dp.
    """
    task_map = {t.id: t for t in tasks}
    teams_dict = {tm.team_id: tm for tm in teams}
    team_idx_map = {idx + 1: tm for idx, tm in enumerate(teams)}

    remaining_cap = {idx + 1: tm.capacity_sp for idx, tm in enumerate(teams)}
    team_assigned: Dict[int, List[Task]] = {idx + 1: [] for idx, tm in enumerate(teams)}
    task_to_team: Dict[int, int] = {}

    for tid in chrom.priority:
        if tid not in task_map:
            continue
        task = task_map[tid]
        t_idx = chrom.assignment.get(tid, 0)

        # 0 nghia la hoan sang sprint sau
        if t_idx <= 0 or t_idx not in team_idx_map:
            continue

        team = team_idx_map[t_idx]

        # 1. Kiem tra ky nang team >= skill_threshold
        if team.get_skill_score(task.skill) < skill_threshold:
            continue

        # 2. Kiem tra dung luong con lai
        if remaining_cap[t_idx] < task.e_i:
            continue

        # Thoa man ca 2 dieu kien (skill va capacity): Nhan task vao team
        team_assigned[t_idx].append(task)
        remaining_cap[t_idx] -= task.e_i
        task_to_team[tid] = t_idx

    # Sap xep chuoi cong viec cho tung team (Memetic Component)
    schedules: List[ScheduleResult] = []
    for t_idx, team in team_idx_map.items():
        assigned = team_assigned[t_idx]
        if apply_memetic_dp and len(assigned) > 1:
            ordered = sequence_tasks_dp(assigned)
        else:
            ordered = assigned

        effort = sum(t.e_i for t in ordered)
        cost = evaluate_schedule_switch_cost(ordered)
        schedules.append(ScheduleResult(
            team_id=team.team_id,
            assigned_tasks=ordered,
            total_effort=effort,
            context_switch_cost=cost
        ))

    plan = evaluate_sprint_plan(
        all_backlog_tasks=tasks,
        schedules=schedules,
        teams_dict=teams_dict,
        current_sprint=current_sprint
    )

    chrom.objectives = (plan.total_utility_resolved, plan.total_switch_cost)
    chrom.decoded_plan = plan
    return plan
