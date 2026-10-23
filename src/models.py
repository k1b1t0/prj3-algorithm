from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Task:
    """Dinh nghia mot cong viec va lo hong trong Backlog (Vulnerability Task)."""
    id: int
    title: str
    repository: str
    asset_module: str
    r_i: float                       # Diem rui ro ky thuat goc (CVSS) [0.0 - 10.0]
    e_i: int                         # No luc xu ly (Story Points)
    skill: str                       # Ky nang yeu cau (OWASP A01-A10)
    earliest_sprint: int = 1         # Sprint phat hien lo hong (disc_i)
    deadline_sprint: int = 4         # Sprint han chot SLA (dead_i)
    predecessors: List[int] = field(default_factory=list) # Danh sach ID task cha (giu de tuong thich du lieu)

    @property
    def sprint_discovered(self) -> int:
        return self.earliest_sprint

    @property
    def sprint_deadline(self) -> int:
        return self.deadline_sprint

    def compute_utility(
        self,
        current_sprint: int = 4,
        alpha: float = 0.5,
        m_penalty: float = 50.0
    ) -> float:
        """
        Tinh diem Mitigation Utility u_i:
        u_i = r_i + alpha * max(0, tau - disc_i) + M_penalty * I(tau >= dead_i)
        """
        persistence = max(0, current_sprint - self.earliest_sprint)
        urgency = 1.0 if current_sprint >= self.deadline_sprint else 0.0
        return round(self.r_i + alpha * persistence + m_penalty * urgency, 4)


@dataclass
class Team:
    """Dinh nghia mot doi ky thuat tham gia Sprint (Cross-Functional Team)."""
    team_id: str
    name: str
    capacity_sp: int                 # Dung luong Story Points toi da trong sprint (cap_t)
    skills: Dict[str, float]         # Do thanh thao ky nang k_{t, s} in [0.0, 1.0]

    def get_skill_score(self, skill_name: str) -> float:
        return self.skills.get(skill_name, 0.0)


@dataclass
class ScheduleResult:
    """Ket qua lap lich cho 1 team trong sprint."""
    team_id: str
    assigned_tasks: List[Task]       # Cac task duoc chon lam theo thu tu chuoi da xep
    total_effort: int
    context_switch_cost: float       # Chi phi chuyen doi ngu canh noi bo team
    mitigated_utility: float = 0.0   # Tong utility u_i cua cac task gan cho team


@dataclass
class SprintPlan:
    """Tong hop ke hoach lap lich toan he thong trong sprint."""
    schedules: List[ScheduleResult]
    deferred_tasks: List[Task]       # Cac task bi hoan sang sprint sau
    total_risk_resolved: float       # Tong CVSS r_i da xu ly
    total_utility_resolved: float    # Tong Mitigation Utility u_i (f1)
    total_risk_deferred: float       # Tong CVSS r_i bi hoan
    total_utility_deferred: float    # Tong Mitigation Utility u_i bi hoan
    total_switch_cost: float         # Tong chi phi chuyen doi ngu canh f2
    skill_match_score: float         # Diem tuong thich ky nang trung binh
    dag_violations: int              # So luong vi pham DAG (luon 0 trong no-dag)
    solver_name: str = ""
    execution_time_ms: float = 0.0
