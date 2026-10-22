from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from models import SprintPlan


@dataclass
class Chromosome:
    """
    Nhiễm sắc thể 2 phần (Two-Part Chromosome) cho Memetic NSGA-II:
    - priority: Hoán vị thứ tự ưu tiên Topo [v_1, v_2, ..., v_N] (task IDs)
    - assignment: Vector chỉ định team {task_id: team_idx} (1..M, hoặc 0: hoãn)
    - objectives: (f1, f2) trong đó f1 = Mitigated Utility (max), f2 = Switch Cost (min)
    """
    priority: List[int]
    assignment: Dict[int, int]
    objectives: Tuple[float, float] = (0.0, 0.0)  # (f1, f2)
    rank: int = 0                                 # Xếp hạng Pareto (0 là Front 1)
    crowding_dist: float = 0.0                    # Khoảng cách tập trung
    decoded_plan: Optional[SprintPlan] = None     # Phương án SprintPlan khả thi hoàn chỉnh

    def dominates(self, other: "Chromosome") -> bool:
        """
        Kiểm tra cá thể này có thống trị cá thể other không.
        Maximize f1, Minimize f2:
        self thống trị other nếu:
        self.f1 >= other.f1 VÀ self.f2 <= other.f2 VÀ ít nhất 1 bất đẳng thức ngặt.
        """
        f1_self, f2_self = self.objectives
        f1_other, f2_other = other.objectives
        better_or_equal = (f1_self >= f1_other) and (f2_self <= f2_other)
        strictly_better = (f1_self > f1_other) or (f2_self < f2_other)
        return better_or_equal and strictly_better
