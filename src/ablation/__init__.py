"""
Goi ablation: Thuc nghiem boc tach danh gia dong gop doc lap cua cac thanh phan CAS (Cluster-Assign-Sequence).
He thong 6 bien the can doi 2-2-2 qua 3 pha:
- Pha 1: V1 (w/o Atomic Clustering: B = N), V2 (w/o 1D Knapsack DP: Greedy)
- Pha 2: V3 (w/o Path-Awareness: Delta C = 0), V4 (w/o Amortization: unamortized eta)
- Pha 3: V5 (w/o Inter-Swap: bo Pha 3.1), V6 (w/o Phase 3: Two-Phase Only)
"""
from .v1_no_clustering import V1NoClusteringSolver
from .v2_no_dp import V2NoDPSolver
from .v3_no_path_aware import V3NoPathAwareSolver
from .v4_no_amortization import V4NoAmortizationSolver
from .v5_no_swap import V5NoSwapSolver
from .v6_two_phase_only import V6TwoPhaseOnlySolver
from .runner import run_ablation_experiments
from .report import generate_ablation_reports

__all__ = [
    "V1NoClusteringSolver",
    "V2NoDPSolver",
    "V3NoPathAwareSolver",
    "V4NoAmortizationSolver",
    "V5NoSwapSolver",
    "V6TwoPhaseOnlySolver",
    "run_ablation_experiments",
    "generate_ablation_reports",
]
