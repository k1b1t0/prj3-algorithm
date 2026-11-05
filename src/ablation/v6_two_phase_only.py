"""
Bien the V6: w/o Phase 3 (Dung ngay sau Pha 2 — Two-Phase Only).
Bo qua ca Pha 3.1 (Inter-Team Swap) lan Pha 3.2 (Bitmask DP Open-TSP).
Ket qua phan bo va thu tu task tu Pha 2 duoc giu nguyen de danh gia truc tiep.
Kiem chung vai tro hoan thien hau ky cua toan bo Pha 3 doi voi giai thuat de xuat.
"""
from typing import List, Dict
from models import Task, Team
from solvers.proposed_cas.solver import ProposedCASSolver


class V6TwoPhaseOnlySolver(ProposedCASSolver):
    """Bien the V6: Dung ngay sau Pha 2, bo qua ca Pha 3.1 va Pha 3.2."""

    def __init__(self, name: str = "V6", **kwargs):
        super().__init__(name=name, **kwargs)

    def run_phase3_swap(
        self,
        team_tasks: Dict[str, List[Task]],
        teams: List[Team],
        skill_thresh: float
    ) -> Dict[str, List[Task]]:
        """Bo qua Pha 3.1: Giu nguyen ket qua phan bo tu Pha 2."""
        return team_tasks

    def run_phase3_sequencing(self, tasks: List[Task], current_sprint: int) -> List[Task]:
        """Bo qua Pha 3.2: Giu nguyen thu tu tasks tu Pha 2."""
        return tasks
