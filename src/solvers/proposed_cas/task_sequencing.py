"""
Pha 3.2: Dinh tuyen thu tu thuc thi noi bo doi (Task Sequencing).
- Gom cac task cua doi thanh K cum (cung repo, module, skill).
- Voi K <= 12: Giai Bitmask DP Open-TSP tim thu tu cum toi uu f2 (O(2^K * K^2)).
- Voi K > 12: Sap xep phan cap theo repo -> module -> skill.
- Noi bo cum: Xep task theo u_i / e_i giam dan.
"""
from typing import List, Dict, Tuple
from models import Task
from metrics import compute_context_distance


def sequence_team_tasks(
    tasks: List[Task],
    current_sprint: int = 4,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> List[Task]:
    """Dinh tuyen thu tu thuc thi cac task cua doi nham cuc tieu hoa chi phi f2."""
    if len(tasks) <= 1:
        return tasks

    # 1. Gom task theo cum (repo, module, skill)
    groups: Dict[Tuple[str, str, str], List[Task]] = {}
    for t in tasks:
        groups.setdefault((t.repository, t.asset_module, t.skill), []).append(t)

    # Sap xep noi bo moi cum theo mat do u_i / e_i giam dan
    blocks: List[List[Task]] = []
    for block_tasks in groups.values():
        block_tasks.sort(
            key=lambda t: (t.compute_utility(current_sprint) / max(1, t.e_i), t.compute_utility(current_sprint)),
            reverse=True
        )
        blocks.append(block_tasks)

    K = len(blocks)
    if K == 1:
        return blocks[0]

    # 2. Xay dung ma tran khoang cach K x K giua cac cum
    dist = [[0.0] * K for _ in range(K)]
    for u in range(K):
        rep_u = blocks[u][0]
        for v in range(u + 1, K):
            d = compute_context_distance(rep_u, blocks[v][0], w_repo, w_mod, w_skill)
            dist[u][v] = d
            dist[v][u] = d

    # 3. Giai Bitmask DP Open-TSP neu K <= 12
    if K <= 12:
        dp: Dict[Tuple[int, int], float] = {(1 << i, i): 0.0 for i in range(K)}
        parent: Dict[Tuple[int, int], int] = {}
        target_mask = (1 << K) - 1

        for mask_len in range(1, K):
            for (mask, u), cost in list(dp.items()):
                if bin(mask).count("1") != mask_len:
                    continue
                for v in range(K):
                    if not (mask & (1 << v)):
                        new_mask = mask | (1 << v)
                        new_cost = cost + dist[u][v]
                        state = (new_mask, v)
                        if state not in dp or new_cost < dp[state]:
                            dp[state] = new_cost
                            parent[state] = u

        best_cost = float("inf")
        best_last = -1
        for u in range(K):
            state = (target_mask, u)
            if state in dp and dp[state] < best_cost:
                best_cost = dp[state]
                best_last = u

        if best_last != -1:
            order_indices = []
            curr_mask, curr_last = target_mask, best_last
            while curr_last is not None:
                order_indices.append(curr_last)
                prev = parent.get((curr_mask, curr_last))
                curr_mask ^= (1 << curr_last)
                curr_last = prev

            order_indices.reverse()
            ordered_tasks: List[Task] = []
            for b_idx in order_indices:
                ordered_tasks.extend(blocks[b_idx])
            return ordered_tasks

    # 4. Fallback khi K > 12: Sap xep phan cap theo repo -> module -> skill
    blocks.sort(key=lambda b: (b[0].repository, b[0].asset_module, b[0].skill))
    ordered_tasks = []
    for b in blocks:
        ordered_tasks.extend(b)
    return ordered_tasks
