import numpy as np
from typing import List, Dict, Tuple
from models import Task, Team, ScheduleResult, SprintPlan


def compute_context_distance(task_a: Task, task_b: Task, w_mod: float = 0.6, w_skill: float = 0.4) -> float:
    # Khoang cach chuyen ngu canh giua 2 task: C_ij in [0, 1]
    # C_ij = w_mod * I(mod_a != mod_b) + w_skill * I(skill_a != skill_b)
    diff_mod = 1.0 if task_a.asset_module != task_b.asset_module else 0.0
    diff_skill = 1.0 if task_a.skill != task_b.skill else 0.0
    return w_mod * diff_mod + w_skill * diff_skill


def evaluate_schedule_switch_cost(tasks: List[Task]) -> float:
    # Tinh tong chi phi chuyen ngu canh tren chuoi task duoc sap xep: sum C_{pi_k, pi_{k+1}}
    if len(tasks) <= 1:
        return 0.0
    cost = 0.0
    for k in range(len(tasks) - 1):
        cost += compute_context_distance(tasks[k], tasks[k + 1])
    return round(cost, 4)


def check_dag_violations(scheduled_tasks: List[Task]) -> int:
    # Kiem tra xem co task con nao duoc lam truoc task cha trong chuoi khong
    # Return so luong cap (cha, con) bi vi pham thu tu
    task_order = {t.id: idx for idx, t in enumerate(scheduled_tasks)}
    violations = 0
    for t in scheduled_tasks:
        for p_id in t.predecessors:
            if p_id in task_order:
                # Neu cha lam sau con thi vi pham
                if task_order[p_id] > task_order[t.id]:
                    violations += 1
    return violations


def compute_skill_match_score(tasks: List[Task], team: Team) -> float:
    # Tinh diem tuong thich ky nang trung binh cua team tren tap task duoc giao
    if not tasks:
        return 1.0
    scores = [team.get_skill_score(t.skill) for t in tasks]
    return round(float(np.mean(scores)), 4)


def evaluate_sprint_plan(
    all_backlog_tasks: List[Task],
    schedules: List[ScheduleResult],
    teams_dict: Dict[str, Team]
) -> SprintPlan:
    # Tinh toan day du 4 chi so cot loi cho mot phuong an lap lich sprint
    scheduled_task_ids = set()
    total_switch_cost = 0.0
    total_dag_violations = 0
    total_assigned_tasks: List[Task] = []
    sms_weighted_sum = 0.0

    for sch in schedules:
        team = teams_dict[sch.team_id]
        total_switch_cost += sch.context_switch_cost
        total_dag_violations += check_dag_violations(sch.assigned_tasks)
        
        for t in sch.assigned_tasks:
            scheduled_task_ids.add(t.id)
            total_assigned_tasks.append(t)
            sms_weighted_sum += team.get_skill_score(t.skill)

    # Xac dinh cac task bi hoan (deferred)
    deferred_tasks = [t for t in all_backlog_tasks if t.id not in scheduled_task_ids]

    # Kiem tra them vi pham DAG giua cac task duoc chon va task bi bo roi:
    # Neu con duoc chon lam nhung cha bi bo roi sang sprint sau thi coi la vi pham nghiem trong
    for t in total_assigned_tasks:
        for p_id in t.predecessors:
            if p_id not in scheduled_task_ids:
                total_dag_violations += 1

    total_risk_resolved = round(sum(t.r_i for t in total_assigned_tasks), 2)
    total_risk_deferred = round(sum(t.r_i for t in deferred_tasks), 2)
    sms = round(sms_weighted_sum / len(total_assigned_tasks), 4) if total_assigned_tasks else 0.0

    return SprintPlan(
        schedules=schedules,
        deferred_tasks=deferred_tasks,
        total_risk_resolved=total_risk_resolved,
        total_risk_deferred=total_risk_deferred,
        total_switch_cost=round(total_switch_cost, 4),
        skill_match_score=sms,
        dag_violations=total_dag_violations
    )
