"""
Bien the V1: w/o Atomic Clustering (Bo gom cum lop tuong duong C_ij = 0).
Coi moi task le la 1 cum don nguyen rieng biet (B = N, c = e_i, Phi(c) = u_i).
Kiem chung vai tro cua Khong gian thuong trong viec giam so luong thuc the va khau hao chi phi chen.
"""
from typing import List
from models import Task
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from solvers.proposed_hcsm.clustering_dp import Cluster


class V1NoClusteringSolver(ProposedHCSMSolver):
    """Bien the V1: B = N (khong gom cum nguyen tu C_ij = 0 o Pha 1)."""

    def __init__(self, name: str = "V1", **kwargs):
        super().__init__(name=name, **kwargs)

    def run_phase1(self, tasks: List[Task], max_cap: int, current_sprint: int) -> List[Cluster]:
        """Pha 1: Coi moi task le la 1 cum don nguyen doc lap (B = N)."""
        clusters: List[Cluster] = []
        for idx, t in enumerate(tasks, start=1):
            cl = Cluster(
                cluster_id=idx,
                repository=t.repository,
                asset_module=t.asset_module,
                skill=t.skill,
                tasks=[t]
            )
            cl.compute_dp(max_cap=max_cap, current_sprint=current_sprint)
            clusters.append(cl)
        return clusters
