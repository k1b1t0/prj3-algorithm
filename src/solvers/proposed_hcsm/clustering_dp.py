"""
Pha 1: Phan cum nguyen tu C_ij = 0 va lap bang Quy hoach dong 1 chieu (1D DP Profiling).
Gom Backlog thanh cac cum Cluster (cung Repo, Module, Skill) va tinh truoc
bang gia tri toi uu Phi_b(c) cho moi muc dung luong c in [0, max_cap].
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from models import Task


@dataclass
class Cluster:
    """Cum nguyen tu gom cac task co chi phi chuyen doi bang 0 (C_ij = 0)."""
    cluster_id: int
    repository: str
    asset_module: str
    skill: str
    tasks: List[Task] = field(default_factory=list)
    total_effort: int = 0
    dp_profile: Dict[int, Tuple[float, List[Task]]] = field(default_factory=dict)

    def compute_dp(self, max_cap: int, current_sprint: int = 4) -> None:
        """Giai chinh xac bai toan 1D 0-1 Knapsack DP tinh bang gia tri Phi_b(c) cho c in [0, max_cap]."""
        self.total_effort = sum(t.e_i for t in self.tasks)
        limit = min(self.total_effort, max_cap)
        # dp[w] = (tong_utility, [danh_sach_task])
        dp: List[Tuple[float, List[Task]]] = [(0.0, []) for _ in range(limit + 1)]

        for task in self.tasks:
            eff = max(1, task.e_i)
            util = task.compute_utility(current_sprint=current_sprint)
            for w in range(limit, eff - 1, -1):
                prev_u, prev_tasks = dp[w - eff]
                if prev_u + util > dp[w][0] + 1e-6:
                    dp[w] = (round(prev_u + util, 4), prev_tasks + [task])

        # Dam bao tinh don dieu: Phi(c) >= Phi(c - 1)
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
        """Tra ve (utility_lon_nhat, tap_task_con_nhat_duoc) ung voi muc dung luong capacity."""
        if capacity <= 0 or not self.tasks:
            return 0.0, []
        cap_key = min(capacity, max(self.dp_profile.keys()) if self.dp_profile else 0)
        return self.dp_profile.get(cap_key, (0.0, []))

    def remove_tasks(self, tasks_to_remove: List[Task], max_cap: int, current_sprint: int = 4) -> None:
        """Xoa cac task da duoc gan va chay lai 1D DP tren phan task con du."""
        remove_ids = {t.id for t in tasks_to_remove}
        self.tasks = [t for t in self.tasks if t.id not in remove_ids]
        self.compute_dp(max_cap=max_cap, current_sprint=current_sprint)


def partition_clusters(
    tasks: List[Task],
    max_cap: int = 30,
    current_sprint: int = 4
) -> List[Cluster]:
    """Phan chia Backlog thanh cac cum nguyen tu C_ij = 0 va lap truoc bang DP 1 chieu."""
    groups: Dict[Tuple[str, str, str], List[Task]] = {}
    for t in tasks:
        groups.setdefault((t.repository, t.asset_module, t.skill), []).append(t)

    clusters: List[Cluster] = []
    c_id = 1
    for (repo, mod, skill), cluster_tasks in groups.items():
        # Sap xep task noi bo theo mat do utility giam dan
        cluster_tasks.sort(
            key=lambda x: x.compute_utility(current_sprint) / max(1, x.e_i),
            reverse=True
        )
        cl = Cluster(
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
