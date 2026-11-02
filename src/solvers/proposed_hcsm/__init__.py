"""
Package proposed_hcsm: Bo giai thuc thi theo kien truc 3 pha H-CSM.
- Pha 1: Phan cum nguyen tu C_ij = 0 va lap bang DP 1 chieu (clustering_dp.py)
- Pha 2: Phan bo da lua chon tich hop chen duong di re nhat (allocation.py, path_insertion.py)
- Pha 3: Hoan doi cum lien doi (inter_team_swap.py) va Dinh tuyen thu tu thuc thi (task_sequencing.py)
"""
from solvers.proposed_hcsm.clustering_dp import Cluster, partition_clusters
from solvers.proposed_hcsm.allocation import allocate_clusters_to_teams
from solvers.proposed_hcsm.path_insertion import compute_path_insertion_cost
from solvers.proposed_hcsm.inter_team_swap import swap_inter_team_clusters
from solvers.proposed_hcsm.task_sequencing import sequence_team_tasks
from solvers.proposed_hcsm.solver import ProposedHCSMSolver, solve_hcsm

__all__ = [
    "Cluster",
    "partition_clusters",
    "allocate_clusters_to_teams",
    "compute_path_insertion_cost",
    "swap_inter_team_clusters",
    "sequence_team_tasks",
    "ProposedHCSMSolver",
    "solve_hcsm",
]
