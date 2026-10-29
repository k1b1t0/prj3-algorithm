"""
Quotient Space Reduction & Exact Intra-Cluster DP Profiling (Phase 1).
Partitions Backlog V into equivalence classes G_b (C_ij = 0) and computes
exact 1D Knapsack DP value curves Phi_b(c) for c in [1, cap_max].
Strictly no DAG logic, line limit < 200 lines.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from models import Task


@dataclass
class QuotientCluster:
    cluster_id: int
    repository: str
    asset_module: str
    skill: str
    tasks: List[Task] = field(default_factory=list)
    total_effort: int = 0
    dp_profile: Dict[int, Tuple[float, List[Task]]] = field(default_factory=dict)

    def compute_dp(self, max_cap: int, current_sprint: int = 4) -> None:
        """Compute exact 1D 0-1 Knapsack DP profile Phi_b(c) for c in [0, max_cap]."""
        self.total_effort = sum(t.e_i for t in self.tasks)
        limit = min(self.total_effort, max_cap)
        # dp[w] = (utility, [tasks])
        dp: List[Tuple[float, List[Task]]] = [(0.0, []) for _ in range(limit + 1)]

        for task in self.tasks:
            eff = max(1, task.e_i)
            util = task.compute_utility(current_sprint=current_sprint)
            for w in range(limit, eff - 1, -1):
                prev_u, prev_tasks = dp[w - eff]
                if prev_u + util > dp[w][0] + 1e-6:
                    dp[w] = (round(prev_u + util, 4), prev_tasks + [task])

        # Enforce monotonicity: Phi(c) >= Phi(c - 1)
        cur_best_u = 0.0
        cur_best_tasks: List[Task] = []
        profile: Dict[int, Tuple[float, List[Task]]] = {}
        for c in range(limit + 1):
            if dp[c][0] > cur_best_u:
                cur_best_u = dp[c][0]
                cur_best_tasks = dp[c][1]
            profile[c] = (cur_best_u, list(cur_best_tasks))

        self.dp_profile = profile

    def get_best_subset(self, capacity: int) -> Tuple[float, List[Task]]:
        """Return (best_utility, subset_tasks) fitting in capacity."""
        if capacity <= 0 or not self.tasks:
            return 0.0, []
        cap_key = min(capacity, max(self.dp_profile.keys()) if self.dp_profile else 0)
        return self.dp_profile.get(cap_key, (0.0, []))

    def remove_tasks(self, tasks_to_remove: List[Task], max_cap: int, current_sprint: int = 4) -> None:
        """Remove assigned tasks from cluster and re-run 1D DP on residuals."""
        remove_ids = {t.id for t in tasks_to_remove}
        self.tasks = [t for t in self.tasks if t.id not in remove_ids]
        self.compute_dp(max_cap=max_cap, current_sprint=current_sprint)


def partition_into_quotient_clusters(
    tasks: List[Task],
    max_cap: int = 30,
    current_sprint: int = 4
) -> List[QuotientCluster]:
    """
    Partition tasks into Zero-Distance Equivalence Classes:
    C_ij = 0 iff (repository, asset_module, skill) match exactly.
    """
    groups: Dict[Tuple[str, str, str], List[Task]] = {}
    for t in tasks:
        key = (t.repository, t.asset_module, t.skill)
        groups.setdefault(key, []).append(t)

    clusters: List[QuotientCluster] = []
    c_id = 1
    for (repo, mod, skill), cluster_tasks in groups.items():
        # Sort internal tasks by utility density
        cluster_tasks.sort(
            key=lambda x: x.compute_utility(current_sprint) / max(1, x.e_i),
            reverse=True
        )
        cl = QuotientCluster(
            cluster_id=c_id,
            repository=repo,
            asset_module=mod,
            skill=skill,
            tasks=cluster_tasks
        )
        cl.compute_dp(max_cap=max_cap, current_sprint=current_sprint)
        clusters.append(cl)
        c_id += 1

    return clusters

