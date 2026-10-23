import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple
from models import Task, Team


def assign_clusters_to_teams(clusters: List[List[Task]], teams: List[Team]) -> List[Tuple[Team, List[Task]]]:
    """
    Gan n_clusters cho n_teams su dung thuat toan Hungarian (linear_sum_assignment).
    Toi da hoa tong diem phu hop ky nang trung binh.
    """
    n_c = len(clusters)
    n_t = len(teams)

    cost_matrix = np.zeros((n_t, n_c), dtype=float)

    for i, team in enumerate(teams):
        for j, cluster in enumerate(clusters):
            if not cluster:
                cost_matrix[i, j] = 1.0
                continue
            scores = [team.get_skill_score(t.skill) for t in cluster]
            avg_score = float(np.mean(scores))
            cost_matrix[i, j] = 1.0 - avg_score

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matched_pairs: List[Tuple[Team, List[Task]]] = []
    for r, c in zip(row_ind, col_ind):
        matched_pairs.append((teams[r], clusters[c]))

    return matched_pairs
