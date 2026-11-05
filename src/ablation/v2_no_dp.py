"""
Bien the V2: w/o 1D Knapsack DP (Bo Quy hoach dong 1 chieu noi cum).
Van gom cum theo lop C_ij = 0, nhung thay vi giai 0-1 Knapsack DP Phi_b(c),
thuat toan dung chien luoc tham lam: xep task theo mat do u_i / e_i giam dan roi nhat tich luy.
Kiem chung loi ich cua viec giai chinh xac Knapsack 1D doi voi f1 va chong nghen ba lo (fragmentation).
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass
from models import Task
from solvers.proposed_cas.solver import ProposedCASSolver
from solvers.proposed_cas.clustering_dp import Cluster


@dataclass
class GreedyCluster(Cluster):
    """Cum nguyen tu su dung nhat tham lam u_i / e_i thay vi 1D 0-1 Knapsack DP."""

    def compute_dp(self, max_cap: int, current_sprint: int = 4) -> None:
        """Xay dung profile Phi_b(c) bang nhat tham lam theo ti so u_i / e_i giam dan."""
        self.total_effort = sum(t.e_i for t in self.tasks)
        limit = min(self.total_effort, max_cap)

        # Sap xep task theo mat do utility u_i / e_i giam dan
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (t.compute_utility(current_sprint) / max(1, t.e_i), t.compute_utility(current_sprint)),
            reverse=True
        )

        profile: Dict[int, Tuple[float, List[Task]]] = {0: (0.0, [])}
        for c in range(1, limit + 1):
            rem = c
            picked: List[Task] = []
            util = 0.0
            for t in sorted_tasks:
                if t.e_i <= rem:
                    picked.append(t)
                    util += t.compute_utility(current_sprint)
                    rem -= t.e_i
            profile[c] = (round(util, 4), picked)

        self.dp_profile = profile


class V2NoDPSolver(ProposedCASSolver):
    """Bien the V2: Thay the 1D Knapsack DP bang phuong phap nhat tham lam."""

    def __init__(self, name: str = "V2", **kwargs):
        super().__init__(name=name, **kwargs)

    def run_phase1(self, tasks: List[Task], max_cap: int, current_sprint: int) -> List[Cluster]:
        """Pha 1: Phan cum theo (repo, module, skill) nhung tao cac GreedyCluster."""
        groups: Dict[Tuple[str, str, str], List[Task]] = {}
        for t in tasks:
            groups.setdefault((t.repository, t.asset_module, t.skill), []).append(t)

        clusters: List[Cluster] = []
        c_id = 1
        for (repo, mod, skill), cluster_tasks in groups.items():
            cl = GreedyCluster(
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
