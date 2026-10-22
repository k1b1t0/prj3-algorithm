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
    Sắp xếp thứ tự thực hiện nội bộ của team bằng Topological Bitmask DP:
    - Mục tiêu: Tối thiểu hóa tổng chi phí chuyển đổi ngữ cảnh sum C_{pi_k, pi_{k+1}}
    - Ràng buộc: 100% tuân thủ thứ tự topo DAG (cha luôn làm trước con)
    """
    n = len(tasks)
    if n <= 1:
        return tasks

    id_to_idx = {t.id: i for i, t in enumerate(tasks)}
    req_mask = [0] * n
    for i, t in enumerate(tasks):
        for p in t.predecessors:
            if p in id_to_idx:
                req_mask[i] |= (1 << id_to_idx[p])

    c_dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                c_dist[i][j] = compute_context_distance(tasks[i], tasks[j], w_repo, w_mod, w_skill)

    # Nếu n <= 14: Bitmask DP chính xác O(2^n * n^2)
    if n <= 14:
        dp: Dict[Tuple[int, int], float] = {}
        parent: Dict[Tuple[int, int], int] = {}

        # Khởi tạo: các task không có cha trong tập này có thể đứng đầu
        for i in range(n):
            if req_mask[i] == 0:
                mask = 1 << i
                dp[(mask, i)] = 0.0

        target_mask = (1 << n) - 1

        for mask_len in range(1, n):
            for (mask, u), cost in list(dp.items()):
                if bin(mask).count("1") != mask_len:
                    continue
                for v in range(n):
                    if not (mask & (1 << v)):
                        # Kiểm tra toàn bộ cha của v đã làm chưa
                        if (mask & req_mask[v]) == req_mask[v]:
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

    # Nếu n > 14: Greedy Topological Sort
    return _greedy_topological_sort(tasks, req_mask, c_dist)


def _greedy_topological_sort(tasks: List[Task], req_mask: List[int], c_dist: List[List[float]]) -> List[Task]:
    n = len(tasks)
    visited_mask = 0
    order = []
    last_idx: Optional[int] = None

    while len(order) < n:
        candidates = []
        for v in range(n):
            if not (visited_mask & (1 << v)):
                if (visited_mask & req_mask[v]) == req_mask[v]:
                    candidates.append(v)

        if not candidates:
            candidates = [v for v in range(n) if not (visited_mask & (1 << v))]

        if last_idx is None:
            chosen = candidates[0]
        else:
            chosen = min(candidates, key=lambda v: c_dist[last_idx][v])

        order.append(chosen)
        visited_mask |= (1 << chosen)
        last_idx = chosen

    return [tasks[i] for i in order]
