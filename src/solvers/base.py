"""
BaseSolver interface cho cac thuat toan.
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
        """Giai bai toan dieu do va tra ve SprintPlan."""
        pass
