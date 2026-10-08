from typing import List, Dict
from ..models import Task, Team, ScheduleResult, SprintPlan
from ..metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan
from .clustering import cluster_tasks
from .assignment import assign_clusters_to_teams
from .trimmer import trim_cluster_for_team
from .dp_sequencing import sequence_tasks_dp


def solve_proposed_pipeline(
    tasks: List[Task],
    teams: List[Team],
    skill_threshold: float = 0.5
) -> SprintPlan:
    # Pipeline 4 giai doan cua thuat toan de xuat:
    # Giai doan 1: Gom cum pho can bang (ESSC / Spectral Clustering) thanh k = |T| cum
    clusters = cluster_tasks(tasks, n_clusters=len(teams))

    # Giai doan 2: Gán cụm cho teams bằng Hungarian matching
    matched_pairs = assign_clusters_to_teams(clusters, teams)

    # Giai doan 3: Loc nguong ky nang & Lam gon dung luong (Leaf Pruning PCKP <= cap_t)
    # Giai doan 4: Lap lich thu tu thuc hien bang Topological Bitmask DP
    schedules: List[ScheduleResult] = []
    teams_dict = {tm.team_id: tm for tm in teams}

    for team, cluster in matched_pairs:
        # Buoc 3: Cat tia
        retained_tasks, _ = trim_cluster_for_team(cluster, team, skill_threshold=skill_threshold)

        # Buoc 4: Tim thu tu toi uu
        ordered_tasks = sequence_tasks_dp(retained_tasks)
        effort = sum(t.e_i for t in ordered_tasks)
        cost = evaluate_schedule_switch_cost(ordered_tasks)

        schedules.append(ScheduleResult(
            team_id=team.team_id,
            assigned_tasks=ordered_tasks,
            total_effort=effort,
            context_switch_cost=cost
        ))

    # Danh gia toan dien ke hoach sprint
    return evaluate_sprint_plan(tasks, schedules, teams_dict)
