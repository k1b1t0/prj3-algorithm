from typing import List, Dict, Tuple, Optional
from models import Task
from metrics import compute_context_distance


def sequence_tasks_dp(
    tasks: List[Task],
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> List[Task]:
    """
    Dinh tuyen chuoi thuc hien noi bo cua team (Open-TSP) bang Bitmask DP:
    - Muc tieu: Toi thieu hoa tong chi phi chuyen doi ngu canh sum C_{pi_k, pi_{k+1}}.
    """
    n = len(tasks)
    if n <= 1:
        return tasks

    c_dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                c_dist[i][j] = compute_context_distance(tasks[i], tasks[j], w_repo, w_mod, w_skill)

    # Neu n <= 14: Bitmask DP chinh xac O(2^n * n^2)
    if n <= 14:
        dp: Dict[Tuple[int, int], float] = {}
        parent: Dict[Tuple[int, int], int] = {}

        # Khoi tao: bat ky task nao cung co the dung dau chuoi
        for i in range(n):
            mask = 1 << i
            dp[(mask, i)] = 0.0

        target_mask = (1 << n) - 1

        for mask_len in range(1, n):
            for (mask, u), cost in list(dp.items()):
                if bin(mask).count("1") != mask_len:
                    continue
                for v in range(n):
                    if not (mask & (1 << v)):
                        new_mask = mask | (1 << v)
                        new_cost = cost + c_dist[u][v]
                        state = (new_mask, v)
                        if state not in dp or new_cost < dp[state]:
                            dp[state] = new_cost
                            parent[state] = u

        best_cost = float("inf")
        best_last = -1
        for u in range(n):
            state = (target_mask, u)
            if state in dp and dp[state] < best_cost:
                best_cost = dp[state]
                best_last = u

        if best_last != -1:
            order_indices = []
            curr_mask = target_mask
            curr_last = best_last
            while curr_last is not None:
                order_indices.append(curr_last)
                prev = parent.get((curr_mask, curr_last))
                curr_mask ^= (1 << curr_last)
                curr_last = prev

            order_indices.reverse()
            return [tasks[i] for i in order_indices]

    # Neu n > 14: Tham lam Nearest-Neighbor
    return _greedy_sequence(tasks, c_dist)


def _greedy_sequence(tasks: List[Task], c_dist: List[List[float]]) -> List[Task]:
    n = len(tasks)
    visited = set()
    order = []

    # Bat dau tu task dau tien
    curr = 0
    order.append(curr)
    visited.add(curr)

    while len(order) < n:
        best_nxt = None
        best_d = float("inf")
        for v in range(n):
            if v not in visited:
                if c_dist[curr][v] < best_d:
                    best_d = c_dist[curr][v]
                    best_nxt = v
        if best_nxt is None:
            best_nxt = [v for v in range(n) if v not in visited][0]
        order.append(best_nxt)
        visited.add(best_nxt)
        curr = best_nxt

    return [tasks[i] for i in order]
