"""
Proposed Matheuristic: Hybrid 4-Phase (Spectral Clustering + Hungarian + PCKP Trimmer + Bitmask DP).
Tốc độ siêu nhanh (< 0.05s), tối ưu hóa cấu trúc mô-đun và chi phí chuyển đổi ngữ cảnh.
"""
import time
from typing import List, Dict
from models import Task, Team, ScheduleResult, SprintPlan
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan
from solvers.base import BaseSolver
from solvers.proposed_4phase.clustering import cluster_tasks
from solvers.proposed_4phase.assignment import assign_clusters_to_teams
from solvers.proposed_4phase.trimmer import trim_cluster_for_team
from solvers.proposed_4phase.dp_sequencing import sequence_tasks_dp


class Proposed4PhaseSolver(BaseSolver):
    def __init__(self, name: str = "Proposed-4Phase", skill_threshold: float = 0.5, random_state: int = 42):
        super().__init__(name=name)
        self.skill_threshold = skill_threshold
        self.random_state = random_state

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        r_state = kwargs.get("random_state", self.random_state)
        teams_dict = {tm.team_id: tm for tm in teams}

        if not tasks:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            return evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)

        # Pha 1: Phân cụm phổ cân bằng (Spectral Clustering)
        clusters = cluster_tasks(tasks, n_clusters=len(teams), random_state=r_state)

        # Pha 2: Ghép cặp Team - Cụm bằng Hungarian matching
        matched_pairs = assign_clusters_to_teams(clusters, teams)

        # Pha 3 & Pha 4: Cắt tỉa PCKP Leaf Pruning & Sắp xếp thứ tự Bitmask DP
        schedules: List[ScheduleResult] = []
        for team, cluster in matched_pairs:
            retained_tasks, _ = trim_cluster_for_team(
                cluster, team,
                skill_threshold=skill_thresh,
                current_sprint=current_sprint
            )
            ordered_tasks = sequence_tasks_dp(retained_tasks)
            effort = sum(t.e_i for t in ordered_tasks)
            cost = evaluate_schedule_switch_cost(ordered_tasks)

            schedules.append(ScheduleResult(
                team_id=team.team_id,
                assigned_tasks=ordered_tasks,
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


def solve_proposed_pipeline(
    tasks: List[Task],
    teams: List[Team],
    skill_threshold: float = 0.5,
    current_sprint: int = 4,
    random_state: int = 42
) -> SprintPlan:
    """Wrapper function cho backward compatibility."""
    solver = Proposed4PhaseSolver(skill_threshold=skill_threshold, random_state=random_state)
    return solver.solve(tasks, teams, current_sprint=current_sprint)
