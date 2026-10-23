from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from models import SprintPlan


@dataclass
class Chromosome:
    """
    Nhiem sac the 2 phan (Two-Part Chromosome) cho Memetic NSGA-II:
    - priority: Hoan vi thu tu uu tien [v_1, v_2, ..., v_N] (task IDs)
    - assignment: Vector chi dinh team {task_id: team_idx} (1..M, hoac 0: hoan)
    - objectives: (f1, f2) trong do f1 = Mitigated Utility (max), f2 = Switch Cost (min)
    """
    priority: List[int]
    assignment: Dict[int, int]
    objectives: Tuple[float, float] = (0.0, 0.0)  # (f1, f2)
    rank: int = 0                                 # Xep hang Pareto (0 la Front 1)
    crowding_dist: float = 0.0                    # Khoang cach tap trung
    decoded_plan: Optional[SprintPlan] = None     # Phuong an SprintPlan kha thi hoan chinh

    def dominates(self, other: "Chromosome") -> bool:
        """
        Kiem tra ca the nay co thong tri ca the other khong.
        Maximize f1, Minimize f2:
        self thong tri other neu:
        self.f1 >= other.f1 VA self.f2 <= other.f2 VA it nhat 1 bat dang thuc ngat.
        """
        f1_self, f2_self = self.objectives
        f1_other, f2_other = other.objectives
        better_or_equal = (f1_self >= f1_other) and (f2_self <= f2_other)
        strictly_better = (f1_self > f1_other) or (f2_self < f2_other)
        return better_or_equal and strictly_better
