"""
Baseline 1: Greedy-CVSS / Greedy-Utility.
1. Sap xep Backlog giam dan theo Mitigation Utility u_i (neu use_utility=True) hoac CVSS r_i.
2. Duyet tuan tu: gan cho team dau tien dat nguong skill (>= 0.5) va con du Story Points.
"""
import time
from typing import List, Dict, Optional
from models import Task, Team, ScheduleResult, SprintPlan
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan
from solvers.base import BaseSolver


class GreedyCVSSSolver(BaseSolver):
    def __init__(self, name: str = "Greedy-CVSS", skill_threshold: float = 0.5, use_utility: bool = True):
        super().__init__(name=name)
        self.skill_threshold = skill_threshold
        self.use_utility = use_utility

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        use_u = kwargs.get("use_utility", self.use_utility)

        # 1. Sap xep backlog theo do uu tien (u_i hoac CVSS r_i)
        if use_u:
            sorted_tasks = sorted(
                tasks,
                key=lambda t: t.compute_utility(current_sprint=current_sprint),
                reverse=True
            )
        else:
            sorted_tasks = sorted(tasks, key=lambda t: t.r_i, reverse=True)

        teams_dict = {tm.team_id: tm for tm in teams}
        team_assigned: Dict[str, List[Task]] = {tm.team_id: [] for tm in teams}
        team_efforts: Dict[str, int] = {tm.team_id: 0 for tm in teams}
        task_to_team: Dict[int, str] = {}

        # 2. Duyet tuan tu: gan cho team dau tien thoa man skill va dung luong
        for task in sorted_tasks:
            for tm in teams:
                rem_cap = tm.capacity_sp - team_efforts[tm.team_id]
                if rem_cap >= task.e_i and tm.get_skill_score(task.skill) >= skill_thresh:
                    team_assigned[tm.team_id].append(task)
                    team_efforts[tm.team_id] += task.e_i
                    task_to_team[task.id] = tm.team_id
                    break

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

        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        return evaluate_sprint_plan(
            all_backlog_tasks=tasks,
            schedules=schedules,
            teams_dict=teams_dict,
            current_sprint=current_sprint,
            solver_name=self.name,
            execution_time_ms=exec_time_ms
        )


def solve_greedy_cvss(
    tasks: List[Task],
    teams: List[Team],
    skill_threshold: float = 0.5,
    current_sprint: int = 4,
    use_utility: bool = True
) -> SprintPlan:
    """Ham wrapper cho backward compatibility."""
    solver = GreedyCVSSSolver(skill_threshold=skill_threshold, use_utility=use_utility)
    return solver.solve(tasks, teams, current_sprint=current_sprint)
