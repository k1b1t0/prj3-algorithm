"""
Package proposed_cas: Bo giai thuc thi theo kien truc 3 pha CAS (Cluster-Assign-Sequence).
- Pha 1: Phan cum nguyen tu C_ij = 0 va lap bang DP 1 chieu (clustering_dp.py)
- Pha 2: Phan bo da lua chon tich hop chen duong di re nhat (allocation.py, path_insertion.py)
- Pha 3: Hoan doi cum lien doi (inter_team_swap.py) va Dinh tuyen thu tu thuc thi (task_sequencing.py)
"""
from solvers.proposed_cas.clustering_dp import Cluster, partition_clusters
from solvers.proposed_cas.allocation import allocate_clusters_to_teams
from solvers.proposed_cas.path_insertion import compute_path_insertion_cost
from solvers.proposed_cas.inter_team_swap import swap_inter_team_clusters
from solvers.proposed_cas.task_sequencing import sequence_team_tasks
from solvers.proposed_cas.solver import ProposedCASSolver, solve_cas, ProposedHCSMSolver, solve_hcsm

__all__ = [
    "Cluster",
    "partition_clusters",
    "allocate_clusters_to_teams",
    "compute_path_insertion_cost",
    "swap_inter_team_clusters",
    "sequence_team_tasks",
    "ProposedCASSolver",
    "solve_cas",
    "ProposedHCSMSolver",
    "solve_hcsm",
]
