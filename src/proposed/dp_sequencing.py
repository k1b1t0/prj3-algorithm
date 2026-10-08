from typing import List, Dict, Tuple, Optional
from models import Task
from metrics import compute_context_distance


def sequence_tasks_dp(tasks: List[Task]) -> List[Task]:
    # Sap xep thu tu thuc hien noi bo cua team bang Topological Bitmask DP:
    # Muc tieu: Toi thieu hoa tong chi phi chuyen doi ngu canh sum C_{pi_k, pi_{k+1}}
    # Rang buoc: 100% tuan thu thu tu topo DAG (cha phai lam truoc con)
    n = len(tasks)
    if n <= 1:
        return tasks

    id_to_idx = {t.id: i for i, t in enumerate(tasks)}
    # Xay dung mat na phu thuoc: mask_req[i] chua cac bit cha cua task i
    req_mask = [0] * n
    for i, t in enumerate(tasks):
        for p in t.predecessors:
            if p in id_to_idx:
                req_mask[i] |= (1 << id_to_idx[p])

    # Tinh ma tran khoang cach c_dist[i][j]
    c_dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                c_dist[i][j] = compute_context_distance(tasks[i], tasks[j])

    # Neu so luong task nho (<= 14): Chay Bitmask DP chinh xac
    if n <= 14:
        # dp[(mask, last_task)] = min_cost
        # parent[(mask, last_task)] = prev_task
        dp: Dict[Tuple[int, int], float] = {}
        parent: Dict[Tuple[int, int], int] = {}

        # Khoi tao: cac task khong co cha co the bat dau dau tien
        for i in range(n):
            if req_mask[i] == 0:
                mask = 1 << i
                dp[(mask, i)] = 0.0

        target_mask = (1 << n) - 1

        # Duyet qua cac trang thai mask theo thu tu so bit tang dan
        for mask_len in range(1, n):
            for (mask, u), cost in list(dp.items()):
                if bin(mask).count("1") != mask_len:
                    continue
                # Thu them task v vao sau u
                for v in range(n):
                    if not (mask & (1 << v)):
                        # Kiem tra xem tat ca cac cha cua v da lam chua
                        if (mask & req_mask[v]) == req_mask[v]:
                            new_mask = mask | (1 << v)
                            new_cost = cost + c_dist[u][v]
                            state = (new_mask, v)
                            if state not in dp or new_cost < dp[state]:
                                dp[state] = new_cost
                                parent[state] = u

        # Tim nghiem tot nhat khi mask = target_mask
        best_cost = float("inf")
        best_last = -1
        for u in range(n):
            state = (target_mask, u)
            if state in dp and dp[state] < best_cost:
                best_cost = dp[state]
                best_last = u

        if best_last != -1:
            # Truy vet nguoc lai de lay chuoi thu tu
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

    # Neu n > 14 hoac phong truong hop DP khong tim thay: Dung Greedy Topological Sort
    return _greedy_topological_sort(tasks, req_mask, c_dist)


def _greedy_topological_sort(tasks: List[Task], req_mask: List[int], c_dist: List[List[float]]) -> List[Task]:
    # Thuat toan tham lam topo: luon chon task hop le ke tiep co C_{last, v} nho nhat
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
            # Truong hop phong ve: lay dai task chua tham
            candidates = [v for v in range(n) if not (visited_mask & (1 << v))]

        if last_idx is None:
            # Chon task dau tien co it phu thuoc nhat
            chosen = candidates[0]
        else:
            # Chon task co context distance toi thieu tu last_idx
            chosen = min(candidates, key=lambda v: c_dist[last_idx][v])

        order.append(chosen)
        visited_mask |= (1 << chosen)
        last_idx = chosen

    return [tasks[i] for i in order]
