"""
Proposed Matheuristic: Cluster-Simulate-Match (CSM No-DAG).
1. Phan cum pho dua tren ma tran khoang cach ngu canh A_ij (K = M).
2. Gia lap danh gia moi cap (Team i, Cum j) bang Knapsack 0-1 u_i / e_i + uoc tinh switch cost nhanh.
3. Ghep cap toi uu toan cuc bang Hungarian Matching tren ma tran loi ich Score(i, j).
4. Dinh tuyen chuoi toi uu noi bo bang Bitmask DP cho M cap thang giai.
"""
import time
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Tuple
from models import Task, Team, ScheduleResult, SprintPlan
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan
from solvers.base import BaseSolver
from solvers.proposed_4phase.clustering import cluster_tasks
from solvers.proposed_4phase.trimmer import trim_cluster_for_team
from solvers.proposed_4phase.dp_sequencing import sequence_tasks_dp


class Proposed4PhaseSolver(BaseSolver):
    def __init__(
        self,
        name: str = "Proposed-CSM",
        skill_threshold: float = 0.5,
        lambda_switch: float = 1.0,
        random_state: int = 42
    ):
        super().__init__(name=name)
        self.skill_threshold = skill_threshold
        self.lambda_switch = lambda_switch
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
        lambda_val = kwargs.get("lambda_switch", self.lambda_switch)
        r_state = kwargs.get("random_state", self.random_state)
        teams_dict = {tm.team_id: tm for tm in teams}

        if not tasks:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            return evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)

        # Pha 1: Phan cum pho can bang theo khoang cach ngu canh (K = len(teams))
        clusters = cluster_tasks(tasks, n_clusters=len(teams), random_state=r_state)

        # Pha 2: Gia lap danh gia ma tran cap (Team i, Cum j)
        M_teams = len(teams)
        N_clusters = len(clusters)
        sim_matrix: List[List[Tuple[List[Task], int, float, float]]] = []
        gain_matrix = np.zeros((M_teams, N_clusters), dtype=float)

        for i, team in enumerate(teams):
            row_sims = []
            for j, cluster in enumerate(clusters):
                # 2a. Loc ky nang va chon knapsack theo mat do u_i / e_i
                retained_tasks, _ = trim_cluster_for_team(
                    cluster, team,
                    skill_threshold=skill_thresh,
                    current_sprint=current_sprint
                )
                # 2b. Uoc tinh chi phi switch nhanh de tinh gain
                fast_ordered = sorted(retained_tasks, key=lambda t: (t.repository, t.asset_module))
                effort = sum(t.e_i for t in fast_ordered)
                fast_cost = evaluate_schedule_switch_cost(fast_ordered)
                utility = sum(t.compute_utility(current_sprint) for t in fast_ordered)
                row_sims.append((retained_tasks, effort, fast_cost, utility))

                unused_cap = max(0, team.capacity_sp - effort)
                gain = utility - lambda_val * fast_cost - 0.1 * unused_cap
                gain_matrix[i, j] = gain

            sim_matrix.append(row_sims)

        # Pha 3: Ghep cap toi uu toan cuc (Hungarian Matching)
        max_gain = np.max(gain_matrix) if gain_matrix.size > 0 else 0.0
        cost_matrix = max_gain - gain_matrix
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # Pha 4: Dinh tuyen chuoi bang Bitmask DP cho M cap thang giai
        schedules: List[ScheduleResult] = []
        for r, c in zip(row_ind, col_ind):
            team = teams[r]
            retained_tasks = sim_matrix[r][c][0]
            ordered_tasks = sequence_tasks_dp(retained_tasks)
            effort = sum(t.e_i for t in ordered_tasks)
            cost = evaluate_schedule_switch_cost(ordered_tasks)
            utility = sum(t.compute_utility(current_sprint) for t in ordered_tasks)

            schedules.append(ScheduleResult(
                team_id=team.team_id,
                assigned_tasks=ordered_tasks,
                total_effort=effort,
                context_switch_cost=cost,
                mitigated_utility=utility
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
    lambda_switch: float = 1.0,
    current_sprint: int = 4,
    random_state: int = 42
) -> SprintPlan:
    """Wrapper function cho backward compatibility."""
    solver = Proposed4PhaseSolver(
        skill_threshold=skill_threshold,
        lambda_switch=lambda_switch,
        random_state=random_state
    )
    return solver.solve(tasks, teams, current_sprint=current_sprint)
