import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from models import Task, Team, ScheduleResult, SprintPlan


def compute_context_distance(
    task_a: Task,
    task_b: Task,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """
    Khoảng cách chuyển đổi ngữ cảnh giữa 2 task: C_ij in [0, 1]
    C_ij = w_repo * I(repo_a != repo_b) + w_mod * I(mod_a != mod_b) + w_skill * I(skill_a != skill_b)
    C_ij = 0 khi và chỉ khi cùng Repo, cùng Module và cùng nhóm Skill.
    """
    if task_a.id == task_b.id:
        return 0.0
    diff_repo = 1.0 if task_a.repository != task_b.repository else 0.0
    diff_mod = 1.0 if task_a.asset_module != task_b.asset_module else 0.0
    diff_skill = 1.0 if task_a.skill != task_b.skill else 0.0
    return round(w_repo * diff_repo + w_mod * diff_mod + w_skill * diff_skill, 4)


def compute_mitigation_utility(
    task: Task,
    current_sprint: int = 4,
    alpha: float = 0.5,
    m_penalty: float = 50.0
) -> float:
    """
    Điểm Lợi ích Giảm nhẹ Rủi ro (Mitigation Utility - u_i):
    u_i = r_i + alpha * max(0, tau - disc_i) + M_penalty * I(tau >= dead_i)
    """
    return task.compute_utility(current_sprint=current_sprint, alpha=alpha, m_penalty=m_penalty)


def evaluate_schedule_switch_cost(
    tasks: List[Task],
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """Tính tổng chi phí chuyển đổi ngữ cảnh trên chuỗi task: sum C_{pi_k, pi_{k+1}}"""
    if len(tasks) <= 1:
        return 0.0
    cost = 0.0
    for k in range(len(tasks) - 1):
        cost += compute_context_distance(tasks[k], tasks[k + 1], w_repo, w_mod, w_skill)
    return round(cost, 4)


def check_dag_violations(scheduled_tasks: List[Task]) -> int:
    """
    Kiểm tra vi phạm thứ tự DAG nội bộ chuỗi:
    Trả về số lượng cặp (cha, con) mà cha xuất hiện sau con.
    """
    task_order = {t.id: idx for idx, t in enumerate(scheduled_tasks)}
    violations = 0
    for t in scheduled_tasks:
        for p_id in t.predecessors:
            if p_id in task_order:
                if task_order[p_id] > task_order[t.id]:
                    violations += 1
    return violations


def compute_skill_match_score(tasks: List[Task], team: Team) -> float:
    """Tính điểm tương thích kỹ năng trung bình của team trên tập task được giao."""
    if not tasks:
        return 1.0
    scores = [team.get_skill_score(t.skill) for t in tasks]
    return round(float(np.mean(scores)), 4)


def evaluate_sprint_plan(
    all_backlog_tasks: List[Task],
    schedules: List[ScheduleResult],
    teams_dict: Dict[str, Team],
    current_sprint: int = 4,
    alpha: float = 0.5,
    m_penalty: float = 50.0,
    solver_name: str = "",
    execution_time_ms: float = 0.0
) -> SprintPlan:
    """
    Tổng hợp và đánh giá toàn diện các chỉ số của một SprintPlan:
    - f1: total_utility_resolved (sum u_i)
    - f2: total_switch_cost (sum C_ij)
    - total_risk_resolved (sum r_i)
    - dag_violations: kiểm tra thứ tự nội bộ, cha bị bỏ rơi, và vi phạm intra-team (cha và con khác team)
    """
    task_to_team: Dict[int, str] = {}
    total_switch_cost = 0.0
    total_dag_violations = 0
    total_assigned_tasks: List[Task] = []
    sms_weighted_sum = 0.0

    # Cập nhật utility cho từng schedule
    updated_schedules: List[ScheduleResult] = []
    for sch in schedules:
        team = teams_dict[sch.team_id]
        total_switch_cost += sch.context_switch_cost
        total_dag_violations += check_dag_violations(sch.assigned_tasks)

        sch_utility = 0.0
        for t in sch.assigned_tasks:
            task_to_team[t.id] = sch.team_id
            total_assigned_tasks.append(t)
            sms_weighted_sum += team.get_skill_score(t.skill)
            sch_utility += t.compute_utility(current_sprint, alpha, m_penalty)

        updated_schedules.append(ScheduleResult(
            team_id=sch.team_id,
            assigned_tasks=sch.assigned_tasks,
            total_effort=sch.total_effort,
            context_switch_cost=sch.context_switch_cost,
            mitigated_utility=round(sch_utility, 4)
        ))

    scheduled_ids = set(task_to_team.keys())
    deferred_tasks = [t for t in all_backlog_tasks if t.id not in scheduled_ids]

    # Kiểm tra ràng buộc DAG toàn cục:
    # 1. Ràng buộc kéo theo: Nếu con được chọn, cha bắt buộc phải được chọn trong cùng sprint
    # 2. Ràng buộc Intra-team: Nếu con và cha cùng được chọn, bắt buộc phải thuộc cùng 1 team
    for t in total_assigned_tasks:
        for p_id in t.predecessors:
            if p_id not in scheduled_ids:
                total_dag_violations += 1  # Cha bị bỏ rơi sang backlog
            elif task_to_team[p_id] != task_to_team[t.id]:
                total_dag_violations += 1  # Cha và con bị gán cho 2 team khác nhau

    total_risk_resolved = round(sum(t.r_i for t in total_assigned_tasks), 2)
    total_risk_deferred = round(sum(t.r_i for t in deferred_tasks), 2)

    total_utility_resolved = round(
        sum(t.compute_utility(current_sprint, alpha, m_penalty) for t in total_assigned_tasks), 2
    )
    total_utility_deferred = round(
        sum(t.compute_utility(current_sprint, alpha, m_penalty) for t in deferred_tasks), 2
    )

    sms = round(sms_weighted_sum / len(total_assigned_tasks), 4) if total_assigned_tasks else 0.0

    return SprintPlan(
        schedules=updated_schedules,
        deferred_tasks=deferred_tasks,
        total_risk_resolved=total_risk_resolved,
        total_utility_resolved=total_utility_resolved,
        total_risk_deferred=total_risk_deferred,
        total_utility_deferred=total_utility_deferred,
        total_switch_cost=round(total_switch_cost, 4),
        skill_match_score=sms,
        dag_violations=total_dag_violations,
        solver_name=solver_name,
        execution_time_ms=execution_time_ms
    )


def extract_pareto_front(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Trích xuất mặt Pareto không bị thống trị (Non-dominated Pareto Front).
    Mục tiêu: Maximize f1 (Utility), Minimize f2 (Switch Cost).
    Trả về danh sách các điểm (f1, f2) được sắp xếp tăng dần theo f1 (và f2 cũng tăng dần).
    """
    if not points:
        return []

    # Loại bỏ điểm trùng
    unique_points = sorted(list(set(points)), key=lambda p: (p[0], -p[1]))

    pareto: List[Tuple[float, float]] = []
    for p in unique_points:
        f1_p, f2_p = p
        # Điểm p bị thống trị nếu tồn tại q sao cho q[0] >= p[0] và q[1] <= p[1] với ít nhất 1 bất đẳng thức ngặt
        dominated = False
        for q in unique_points:
            if (q[0] >= f1_p and q[1] <= f2_p) and (q[0] > f1_p or q[1] < f2_p):
                dominated = True
                break
        if not dominated:
            pareto.append(p)

    # Sắp xếp theo f1 tăng dần
    pareto.sort(key=lambda p: p[0])
    return pareto


def compute_hypervolume(
    pareto_points: List[Tuple[float, float]],
    ref_point: Tuple[float, float]
) -> float:
    """
    Tính chỉ số Hypervolume (HV) 2 chiều cho mặt Pareto.
    Mục tiêu: Maximize f1, Minimize f2.
    ref_point = (f1_ref, f2_ref) với f1_ref <= min(f1), f2_ref >= max(f2).
    Diện tích được giới hạn bởi Mặt Pareto và Điểm chuẩn ref_point.
    """
    front = extract_pareto_front(pareto_points)
    if not front:
        return 0.0

    f1_ref, f2_ref = ref_point

    # Lọc các điểm tốt hơn ref_point
    valid_points = [p for p in front if p[0] >= f1_ref and p[1] <= f2_ref]
    if not valid_points:
        return 0.0

    # Sắp xếp tăng dần theo f1
    valid_points.sort(key=lambda p: p[0])

    area = 0.0
    prev_f1 = f1_ref
    for f1, f2 in valid_points:
        width = f1 - prev_f1
        height = f2_ref - f2
        if width > 0 and height > 0:
            area += width * height
        prev_f1 = max(prev_f1, f1)

    return round(area, 4)
