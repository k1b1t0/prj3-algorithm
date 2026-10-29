"""
Module quan ly va tinh toan Can Chuan Hoa (Objective Bounds) cho bai toan Da Muc Tieu:
- f1: Mitigation Utility (Loi ich giam nhe rui ro)
- f2: Context Switch Cost (Chi phi chuyen doi ngu canh)
- Z(w) = w * norm(f1) - (1 - w) * norm(f2) voi w in [0.0, 1.0]

Su dung duy nhat Co Che Chuan:
Can Tinh Toan Hoc (Static Mathematical Bounds) tinh nhanh tu Fractional Knapsack va tran dung luong.
"""
from dataclasses import dataclass
from typing import List, Optional
from models import Task, Team


@dataclass
class ObjectiveBounds:
    f1_min: float = 0.0
    f1_max: float = 1.0
    f2_min: float = 0.0
    f2_max: float = 1.0
    method: str = "static"

    def normalize_f1(self, f1: float) -> float:
        if self.f1_max <= self.f1_min:
            return 0.0
        return max(0.0, min(1.0, (f1 - self.f1_min) / (self.f1_max - self.f1_min)))

    def normalize_f2(self, f2: float) -> float:
        if self.f2_max <= self.f2_min:
            return 0.0
        return max(0.0, min(1.0, (f2 - self.f2_min) / (self.f2_max - self.f2_min)))

    def compute_z(self, f1: float, f2: float, w: float) -> float:
        """Tinh diem vo huong hoa chuan hoa Z(w) = w * norm_f1 - (1 - w) * norm_f2."""
        norm_f1 = self.normalize_f1(f1)
        norm_f2 = self.normalize_f2(f2)
        return round(w * norm_f1 - (1.0 - w) * norm_f2, 4)

    def get_effective_lambda(self, w: float) -> float:
        """
        Quy doi he so trong so w ve he so phat lambda tuong duong cua ham thong thuong (Z = f1 - lambda * f2):
        lambda_effective = ((1 - w) / w) * (f1_range / f2_range)
        """
        if w <= 0.0:
            return 1e6
        if w >= 1.0:
            return 0.0
        f1_range = max(1e-6, self.f1_max - self.f1_min)
        f2_range = max(1e-6, self.f2_max - self.f2_min)
        return ((1.0 - w) / w) * (f1_range / f2_range)


def compute_static_bounds(
    tasks: List[Task],
    teams: List[Team],
    current_sprint: int = 4
) -> ObjectiveBounds:
    """
    Tinh can tinh toan hoc tu Instance trong O(N log N):
    - f1_max: Giai Fractional Knapsack voi tran dung luong tong.
    - f2_max: So task nho nhat nhat duoc tru di M doi (moi buoc chuyen doi toi da 1.0).
    """
    if not tasks or not teams:
        return ObjectiveBounds(f1_min=0.0, f1_max=1.0, f2_min=0.0, f2_max=1.0, method="static")

    total_cap = sum(tm.capacity_sp for tm in teams)
    n_teams = len(teams)

    # 1. Tinh f1_max bang Fractional Knapsack
    task_utilities = [t.compute_utility(current_sprint=current_sprint) for t in tasks]
    tasks_with_density = []
    for t, u in zip(tasks, task_utilities):
        effort = max(1, t.e_i)
        tasks_with_density.append((u / effort, u, effort))

    tasks_with_density.sort(key=lambda x: x[0], reverse=True)

    rem_cap = total_cap
    f1_max = 0.0
    for density, u, e in tasks_with_density:
        if rem_cap <= 0:
            break
        if e <= rem_cap:
            f1_max += u
            rem_cap -= e
        else:
            f1_max += density * rem_cap
            rem_cap = 0
            break

    # 2. Tinh f2_max: So buoc chuyen doi toi da co the
    sorted_efforts = sorted([max(1, t.e_i) for t in tasks])
    k_max = 0
    cur_cap = 0
    for eff in sorted_efforts:
        if cur_cap + eff <= total_cap:
            cur_cap += eff
            k_max += 1
        else:
            break

    max_transitions = max(1, k_max - n_teams)
    f2_max = float(max_transitions) * 1.0

    return ObjectiveBounds(
        f1_min=0.0,
        f1_max=round(f1_max, 4),
        f2_min=0.0,
        f2_max=round(f2_max, 4),
        method="static"
    )

