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
    Bộ giải mã Topo (Topological Decoder):
    Duyệt tuần tự theo danh sách ưu tiên.
    Đảm bảo 100% phương án sinh ra đều KHẢ THI (0 DAG violations, đúng capacity, đúng skill).
    Thành phần Memetic: Tối ưu hóa chuỗi nội bộ từng team bằng sequence_tasks_dp.
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

        # 0 nghĩa là hoãn sang sprint sau
        if t_idx <= 0 or t_idx not in team_idx_map:
            continue

        team = team_idx_map[t_idx]

        # 1. Kiểm tra kỹ năng team >= skill_threshold
        if team.get_skill_score(task.skill) < skill_threshold:
            continue

        # 2. Kiểm tra dung lượng còn lại
        if remaining_cap[t_idx] < task.e_i:
            continue

        # 3. Kiểm tra ràng buộc DAG: Toàn bộ task cha phải được nhận VÀ phải cùng thuộc team này (Intra-team)
        parents_valid = True
        for p in task.predecessors:
            if p not in task_to_team or task_to_team[p] != t_idx:
                parents_valid = False
                break

        if not parents_valid:
            continue

        # Thỏa mãn cả 3 điều kiện: Nhận task vào team
        team_assigned[t_idx].append(task)
        remaining_cap[t_idx] -= task.e_i
        task_to_team[tid] = t_idx

    # Sắp xếp chuỗi công việc cho từng team (Memetic Component)
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
