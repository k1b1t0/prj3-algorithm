"""
Bien the V5: w/o Inter-Swap (Bo hoan doi cum lien doi).
Bo qua hoan toan Pha 3.1 (1-0 Relocate va 1-1 Block Swap).
Chuyen thang ket qua phan bo tu Pha 2 sang Pha 3.2 de chay Bitmask DP Open-TSP.
Kiem chung dong gop doc lap cua viec hoan doi cum giua hai doi trong viec keo giam chi phi f2.
"""
from typing import List, Dict
from models import Task, Team
from solvers.proposed_hcsm.solver import ProposedHCSMSolver


class V5NoSwapSolver(ProposedHCSMSolver):
    """Bien the V5: Bo qua Pha 3.1 hoan doi cum lien doi."""

    def __init__(self, name: str = "V5", **kwargs):
        super().__init__(name=name, **kwargs)

    def run_phase3_swap(
        self,
        team_tasks: Dict[str, List[Task]],
        teams: List[Team],
        skill_thresh: float
    ) -> Dict[str, List[Task]]:
        """Pha 3.1: Bo qua hoan doi, giu nguyen tap task da phan bo tu Pha 2."""
        return team_tasks

