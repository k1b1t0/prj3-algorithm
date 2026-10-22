"""
Baseline 1: Greedy-CVSS (Industry Standard Practice).
Mô phỏng quy trình phân bổ thực tế trong các đội Scrum / Jira / CSOC:
1. Sắp xếp Backlog giảm dần theo rủi ro (hoặc u_i).
2. Duyệt tuần tự: Kiểm tra cha đã làm chưa, nếu cha đã làm thì ép cùng team với cha (Intra-team).
3. Gán cho team đầu tiên thỏa mãn ngưỡng kỹ năng (>= 0.5) và đủ dung lượng Story Points.
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

        # 1. Sắp xếp Backlog giảm dần
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

        for task in sorted_tasks:
            # Kiểm tra ràng buộc cha-con DAG
            # 1. Toàn bộ task cha phải được nhận trong sprint
            all_parents_done = all(p in task_to_team for p in task.predecessors)
            if not all_parents_done:
                continue

            # 2. Ràng buộc intra-team: Nếu có cha, bắt buộc phải cùng team với các cha
            parent_teams = {task_to_team[p] for p in task.predecessors}
            if len(parent_teams) > 1:
                # Nếu các cha lại bị chia vào nhiều team khác nhau thì không thể thỏa intra-team
                continue
            
            mandatory_team_id: Optional[str] = parent_teams.pop() if parent_teams else None

            # Tìm team phù hợp
            best_team: Optional[Team] = None
            if mandatory_team_id is not None:
                tm = teams_dict[mandatory_team_id]
                rem_cap = tm.capacity_sp - team_efforts[tm.team_id]
                if rem_cap >= task.e_i and tm.get_skill_score(task.skill) >= skill_thresh:
                    best_team = tm
            else:
                for tm in teams:
                    rem_cap = tm.capacity_sp - team_efforts[tm.team_id]
                    if rem_cap >= task.e_i and tm.get_skill_score(task.skill) >= skill_thresh:
                        best_team = tm
                        break

            if best_team is not None:
                team_assigned[best_team.team_id].append(task)
                team_efforts[best_team.team_id] += task.e_i
                task_to_team[task.id] = best_team.team_id

        # Đóng gói ScheduleResult cho từng team
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
    """Hàm wrapper cho backward compatibility."""
    solver = GreedyCVSSSolver(skill_threshold=skill_threshold, use_utility=use_utility)
    return solver.solve(tasks, teams, current_sprint=current_sprint)
