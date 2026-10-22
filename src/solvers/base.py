"""
BaseSolver Interface for All Solvers in Tier 1.
Mọi thuật toán (Exact, Greedy, Proposed 4-Phase, NSGA-II) đều kế thừa BaseSolver.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from models import Task, Team, SprintPlan


class BaseSolver(ABC):
    def __init__(self, name: str = "BaseSolver"):
        self.name = name

    @abstractmethod
    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        """
        Nhận vào tập backlog tasks và danh sách teams, trả về một SprintPlan hoàn chỉnh.
        Thuần túy thuật toán, không chứa code logging, visualize hay CLI.
        """
        pass
