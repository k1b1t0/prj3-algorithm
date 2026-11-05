"""
Pha 2 Ho tro: Tinh toan chi phi chen cum vao chuoi hanh trinh cua doi (Path Insertion).
Xac dinh vi tri chen toi uu tren chuoi ho lam tang chi phi chuyen doi Delta C nho nhat.
"""
from typing import List, Tuple
from .clustering_dp import Cluster


def cluster_distance(
    c1: Cluster,
    c2: Cluster,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """Khoang cach chuyen doi ngu canh giua 2 cum trong doan [0, 1]."""
    if c1.cluster_id == c2.cluster_id:
        return 0.0
    diff_repo = 1.0 if c1.repository != c2.repository else 0.0
    diff_mod = 1.0 if c1.asset_module != c2.asset_module else 0.0
    diff_skill = 1.0 if c1.skill != c2.skill else 0.0
    return round(w_repo * diff_repo + w_mod * diff_mod + w_skill * diff_skill, 4)


def compute_path_cost(path: List[Cluster]) -> float:
    """Tong chi phi chuyen doi tren chuoi cac cum."""
    if len(path) <= 1:
        return 0.0
    cost = 0.0
    for i in range(len(path) - 1):
        cost += cluster_distance(path[i], path[i + 1])
    return round(cost, 4)


def compute_path_insertion_cost(
    candidate: Cluster,
    path: List[Cluster]
) -> Tuple[float, int]:
    """Tim vi tri chen tot nhat tren chuoi mo cua doi de Delta C tang them la nho nhat."""
    if not path:
        return 0.0, 0

    for idx, c in enumerate(path):
        if c.cluster_id == candidate.cluster_id:
            return 0.0, idx

    best_delta = cluster_distance(candidate, path[0])
    best_pos = 0

    cost_end = cluster_distance(path[-1], candidate)
    if cost_end < best_delta:
        best_delta = cost_end
        best_pos = len(path)

    for i in range(len(path) - 1):
        delta = (
            cluster_distance(path[i], candidate)
            + cluster_distance(candidate, path[i + 1])
            - cluster_distance(path[i], path[i + 1])
        )
        if delta < best_delta:
            best_delta = delta
            best_pos = i + 1

    return round(best_delta, 4), best_pos
