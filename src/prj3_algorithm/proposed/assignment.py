import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple
from ..models import Task, Team


def assign_clusters_to_teams(clusters: List[List[Task]], teams: List[Team]) -> List[Tuple[Team, List[Task]]]:
    # Gán n_clusters cho n_teams su dung thuat toan Hungarian (linear_sum_assignment)
    # Tối đa hóa tổng điểm phù hợp kỹ năng = Tối thiểu hóa chi phí (1.0 - compatibility)
    n_c = len(clusters)
    n_t = len(teams)
    
    # Ma tran chi phi cost_matrix[i, j]: Team i nhan Cluster j
    cost_matrix = np.zeros((n_t, n_c), dtype=float)

    for i, team in enumerate(teams):
        for j, cluster in enumerate(clusters):
            if not cluster:
                cost_matrix[i, j] = 1.0
                continue
            # Diem phu hop trung binh cua team tren cac task trong cum
            scores = [team.get_skill_score(t.skill) for t in cluster]
            avg_score = float(np.mean(scores))
            cost_matrix[i, j] = 1.0 - avg_score

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matched_pairs: List[Tuple[Team, List[Task]]] = []
    for r, c in zip(row_ind, col_ind):
        matched_pairs.append((teams[r], clusters[c]))

    return matched_pairs
