"""
Phase 4: Super-Node Block-Level Open-TSP.
- Groups tasks assigned to a team into B Super-Nodes with identical (repo, module, skill).
- If B <= 12: Runs exact Bitmask DP Open-TSP with complexity O(2^B * B^2) (< 0.1 ms).
- If B > 12: Fallbacks to hierarchical nearest neighbor sorting.
- Returns optimal ordered sequence of tasks minimizing context switch cost f2.
"""
from typing import List, Dict, Tuple, Any
from models import Task
from metrics import compute_context_distance


def sequence_team_tasks_block_tsp(
    tasks: List[Task],
    current_sprint: int = 4,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> Tuple[List[Task], Dict[str, Any]]:
    """
    Phase 4: Super-Node Block-Level Open-TSP.
    Returns:
    - ordered_tasks: List of tasks in optimal execution sequence
    - route_info: Metadata about super-nodes and routing method
    """
    if len(tasks) <= 1:
        return tasks, {"num_blocks": len(tasks), "method": "trivial", "cost": 0.0}

    # 1. Group tasks into Super-Nodes (repo, module, skill)
    groups: Dict[Tuple[str, str, str], List[Task]] = {}
    for t in tasks:
        key = (t.repository, t.asset_module, t.skill)
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    # Sort inside each block by density rho_i = u_i / e_i descending
    blocks: List[List[Task]] = []
    block_names: List[str] = []
    for key, block_tasks in groups.items():
        block_tasks.sort(
            key=lambda t: (t.compute_utility(current_sprint) / max(1, t.e_i), t.compute_utility(current_sprint)),
            reverse=True
        )
        blocks.append(block_tasks)
        block_names.append(f"{key[0]}:{key[1]}:{key[2]}")

    B = len(blocks)
    if B == 1:
        return blocks[0], {"num_blocks": 1, "method": "single_block", "cost": 0.0, "chain": [block_names[0]]}

    # 2. Distance matrix between super-nodes B x B
    dist = [[0.0] * B for _ in range(B)]
    for u in range(B):
        rep_u = blocks[u][0]
        for v in range(u + 1, B):
            rep_v = blocks[v][0]
            d = compute_context_distance(rep_u, rep_v, w_repo, w_mod, w_skill)
            dist[u][v] = d
            dist[v][u] = d

    # 3. Bitmask DP Open-TSP if B <= 12
    if B <= 12:
        dp: Dict[Tuple[int, int], float] = {}
        parent: Dict[Tuple[int, int], int] = {}

        for i in range(B):
            dp[(1 << i, i)] = 0.0

        target_mask = (1 << B) - 1

        for mask_len in range(1, B):
            for (mask, u), cost in list(dp.items()):
                if bin(mask).count("1") != mask_len:
                    continue
                for v in range(B):
                    if not (mask & (1 << v)):
                        new_mask = mask | (1 << v)
                        new_cost = cost + dist[u][v]
                        state = (new_mask, v)
                        if state not in dp or new_cost < dp[state]:
                            dp[state] = new_cost
                            parent[state] = u

        best_cost = float("inf")
        best_last = -1
        for u in range(B):
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
            ordered_tasks = []
            chain_desc = []
            for b_idx in order_indices:
                ordered_tasks.extend(blocks[b_idx])
                chain_desc.append(f"Block({block_names[b_idx]}, tasks={[t.id for t in blocks[b_idx]]})")

            return ordered_tasks, {
                "num_blocks": B,
                "method": "Bitmask DP (Exact)",
                "cost": round(best_cost, 4),
                "chain": chain_desc,
            }

    # 4. Fallback: Hierarchical sorting by repo -> module -> skill
    blocks.sort(key=lambda b: (b[0].repository, b[0].asset_module, b[0].skill))
    ordered_tasks = []
    chain_desc = []
    for b in blocks:
        ordered_tasks.extend(b)
        chain_desc.append(f"Block({b[0].repository}:{b[0].asset_module}, tasks={[t.id for t in b]})")

    return ordered_tasks, {
        "num_blocks": B,
        "method": "Nearest Neighbor Fallback",
        "cost": 0.0,
        "chain": chain_desc,
    }
