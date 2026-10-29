"""
Cheapest Open-Path Insertion for Quotient Super-Nodes.
Calculates exact context switch cost delta when inserting cluster into team path.
Strictly no DAG logic, line limit < 200 lines.
"""
from typing import List, Tuple
from .quotient_dp import QuotientCluster


def cluster_distance(
    c1: QuotientCluster,
    c2: QuotientCluster,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """Context switch distance between two quotient clusters in [0, 1]."""
    if c1.cluster_id == c2.cluster_id:
        return 0.0
    diff_repo = 1.0 if c1.repository != c2.repository else 0.0
    diff_mod = 1.0 if c1.asset_module != c2.asset_module else 0.0
    diff_skill = 1.0 if c1.skill != c2.skill else 0.0
    return round(w_repo * diff_repo + w_mod * diff_mod + w_skill * diff_skill, 4)


def compute_path_cost(path: List[QuotientCluster]) -> float:
    """Sum of context switch costs along open sequence of clusters."""
    if len(path) <= 1:
        return 0.0
    cost = 0.0
    for i in range(len(path) - 1):
        cost += cluster_distance(path[i], path[i + 1])
    return round(cost, 4)


def compute_cheapest_insertion(
    candidate: QuotientCluster,
    path: List[QuotientCluster]
) -> Tuple[float, int]:
    """
    Find best insertion position on open path pi_t that minimizes delta C.
    Returns (min_delta_c, best_index).
    """
    if not path:
        return 0.0, 0

    # If cluster is already visited on the path, insertion has 0 context overhead
    for idx, c in enumerate(path):
        if c.cluster_id == candidate.cluster_id:
            return 0.0, idx

    # If candidate shares repo/module/skill with any cluster in path, delta is 0 if merged adjacent
    for idx, c in enumerate(path):
        if cluster_distance(c, candidate) == 0.0:
            return 0.0, idx + 1

    n = len(path)
    # Option 1: Insert at head (pos 0)
    best_delta = cluster_distance(candidate, path[0])
    best_pos = 0

    # Option 2: Insert at tail (pos n)
    tail_delta = cluster_distance(path[-1], candidate)
    if tail_delta < best_delta:
        best_delta = tail_delta
        best_pos = n

    # Option 3: Insert between path[i-1] and path[i]
    for i in range(1, n):
        d_in = cluster_distance(path[i - 1], candidate) + cluster_distance(candidate, path[i])
        d_out = cluster_distance(path[i - 1], path[i])
        delta = round(d_in - d_out, 4)
        if delta < best_delta:
            best_delta = delta
            best_pos = i

    return round(best_delta, 4), best_pos

