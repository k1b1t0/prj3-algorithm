import numpy as np
from typing import List, Dict, Tuple, Set, Optional, Any
from models import Task, Team, ScheduleResult, SprintPlan
from bounds import ObjectiveBounds, compute_static_bounds


# ==============================================================================
# NHOM 1: CAC HAM VAT LY & KHOANG CACH (Dung ca khi giai toan va cham diem)
# ==============================================================================

def compute_context_distance(
    task_a: Task,
    task_b: Task,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """
    Khoang cach / chi phi chuyen doi ngu canh giua 2 task: C_ij in [0, 1].
    C_ij = w_repo * I(repo_a != repo_b) + w_mod * I(mod_a != mod_b) + w_skill * I(skill_a != skill_b).
    C_ij = 0 khi va chi khi cung Repo, cung Module, va cung Skill.
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
    alpha: float = 0.6,
    m_penalty: float = 0.0
) -> float:
    """Diem uu tien giam nhe rui ro dong u_i in (0, 1]."""
    return task.compute_utility(current_sprint=current_sprint, alpha=alpha, m_penalty=m_penalty)


def evaluate_schedule_switch_cost(
    tasks: List[Task],
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """Tinh tong chi phi chuyen doi tren mot chuoi cong viec cua doi: sum C_{pi_k, pi_{k+1}}."""
    if len(tasks) <= 1:
        return 0.0
    cost = 0.0
    for k in range(len(tasks) - 1):
        cost += compute_context_distance(tasks[k], tasks[k + 1], w_repo, w_mod, w_skill)
    return round(cost, 4)


# ==============================================================================
# NHOM 2: HAM DONG GOI & DANH GIA NGHIEM (EVALUATOR)
# ==============================================================================

def evaluate_sprint_plan(
    all_backlog_tasks: List[Task],
    schedules: List[ScheduleResult],
    teams_dict: Dict[str, Team],
    current_sprint: int = 4,
    alpha: float = 0.6,
    m_penalty: float = 0.0,
    solver_name: str = "",
    execution_time_ms: float = 0.0,
    trace_details: Optional[Dict[str, Any]] = None
) -> SprintPlan:
    """
    Tong hop va cham diem toan bo SprintPlan:
    - Tra ve 2 muc tieu cot loi: f1 (mitigation utility) va f2 (context switch cost).
    - Tach danh sach task thanh viec duoc lam (assigned) va viec bi hoan (deferred).
    - Ghi nhan runtime execution_time_ms do tu solver.
    """
    task_to_team: Dict[int, str] = {}
    total_switch_cost = 0.0
    total_assigned_tasks: List[Task] = []

    updated_schedules: List[ScheduleResult] = []
    for sch in schedules:
        total_switch_cost += sch.context_switch_cost

        sch_utility = 0.0
        for t in sch.assigned_tasks:
            task_to_team[t.id] = sch.team_id
            total_assigned_tasks.append(t)
            sch_utility += t.compute_utility(current_sprint=current_sprint, alpha=alpha, m_penalty=m_penalty)

        updated_schedules.append(ScheduleResult(
            team_id=sch.team_id,
            assigned_tasks=sch.assigned_tasks,
            total_effort=sch.total_effort,
            context_switch_cost=sch.context_switch_cost,
            mitigated_utility=round(sch_utility, 4)
        ))

    scheduled_ids = set(task_to_team.keys())
    deferred_tasks = [t for t in all_backlog_tasks if t.id not in scheduled_ids]

    total_risk_resolved = round(sum(t.r_i for t in total_assigned_tasks), 2)
    total_risk_deferred = round(sum(t.r_i for t in deferred_tasks), 2)

    total_utility_resolved = round(
        sum(t.compute_utility(current_sprint=current_sprint, alpha=alpha, m_penalty=m_penalty) for t in total_assigned_tasks), 2
    )
    total_utility_deferred = round(
        sum(t.compute_utility(current_sprint=current_sprint, alpha=alpha, m_penalty=m_penalty) for t in deferred_tasks), 2
    )

    return SprintPlan(
        schedules=updated_schedules,
        deferred_tasks=deferred_tasks,
        total_risk_resolved=total_risk_resolved,
        total_utility_resolved=total_utility_resolved,
        total_risk_deferred=total_risk_deferred,
        total_utility_deferred=total_utility_deferred,
        total_switch_cost=round(total_switch_cost, 4),
        solver_name=solver_name,
        execution_time_ms=execution_time_ms,
        trace_details=trace_details or {}
    )


# ==============================================================================
# NHOM 3: CONG CU PHAN TICH THUC NGHIEM & PARETO (Phuc vu viet bai bao / benchmark)
# ==============================================================================

def extract_pareto_front(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Trich xuat tap nghiem khong bi troi (Pareto Front): Maximize f1, Minimize f2."""
    if not points:
        return []
    unique_points = sorted(list(set(points)), key=lambda p: (p[0], -p[1]))
    pareto: List[Tuple[float, float]] = []
    for p in unique_points:
        f1_p, f2_p = p
        dominated = False
        for q in unique_points:
            if (q[0] >= f1_p and q[1] <= f2_p) and (q[0] > f1_p or q[1] < f2_p):
                dominated = True
                break
        if not dominated:
            pareto.append(p)
    pareto.sort(key=lambda p: p[0])
    return pareto


def compute_hypervolume(
    pareto_points: List[Tuple[float, float]],
    ref_point: Tuple[float, float]
) -> float:
    """Tinh dien tich bao phu Hypervolume 2D giua Pareto Front va diem tham chieu ref_point."""
    front = extract_pareto_front(pareto_points)
    if not front:
        return 0.0

    f1_ref, f2_ref = ref_point
    valid_points = [p for p in front if p[0] >= f1_ref and p[1] <= f2_ref]
    if not valid_points:
        return 0.0

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


def compute_wilcoxon_pvalue(
    scores_proposed: List[float],
    scores_baseline: List[float],
    alternative: str = "greater"
) -> float:
    """
    Kiem dinh thong ke phi tham so Wilcoxon Signed-Rank Test giua 2 bo diem paired.
    Tra ve p-value in [0.0, 1.0].
    """
    if len(scores_proposed) != len(scores_baseline) or len(scores_proposed) < 3:
        return 1.0
    diffs = [round(a - b, 6) for a, b in zip(scores_proposed, scores_baseline)]
    if all(d == 0 for d in diffs):
        return 1.0
    try:
        from scipy.stats import wilcoxon
        stat, p_val = wilcoxon(scores_proposed, scores_baseline, alternative=alternative, zero_method="wilcox")
        return round(float(p_val), 4)
    except Exception:
        wins = sum(1 for d in diffs if d > 0)
        if wins == len(diffs):
            return round(1.0 / (2 ** len(diffs)), 4)
        return 0.5
