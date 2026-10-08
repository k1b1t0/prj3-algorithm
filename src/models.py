from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Task:
    # Dinh nghia mot cong viec lo hong trong backlog
    id: int
    title: str
    repository: str
    asset_module: str
    r_i: float                       # Diem rui ro (CVSS / MLDBN)
    e_i: int                         # No luc xu ly (Story Points)
    skill: str                       # Ky nang yeu cau (OWASP A01-A10)
    earliest_sprint: int = 1
    deadline_sprint: int = 4
    predecessors: List[int] = field(default_factory=list) # Danh sach task cha


@dataclass
class Team:
    # Dinh nghia mot doi phat trien hoac bao mat
    team_id: str
    name: str
    capacity_sp: int                 # Dung luong toi da trong 1 sprint
    skills: Dict[str, float]         # Do thanh thao ky nang k_{t, sk} in [0.0, 1.0]

    def get_skill_score(self, skill_name: str) -> float:
        # Lay do thanh thao cua team voi ky nang cu the
        return self.skills.get(skill_name, 0.0)


@dataclass
class ScheduleResult:
    # Ket qua lap lich cho 1 team trong sprint
    team_id: str
    assigned_tasks: List[Task]       # Cac task duoc chon lam theo thu tu da xep
    total_effort: int
    context_switch_cost: float


@dataclass
class SprintPlan:
    # Tong hop ket qua lap lich toan he thong trong sprint
    schedules: List[ScheduleResult]
    deferred_tasks: List[Task]       # Cac task bi hoan sang sprint sau
    total_risk_resolved: float
    total_risk_deferred: float
    total_switch_cost: float
    skill_match_score: float
    dag_violations: int
