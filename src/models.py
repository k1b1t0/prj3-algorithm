from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# ==============================================================================
# INPUT
# ==============================================================================

@dataclass
class Task:
    """Thuc the lo hong an ninh trong Backlog."""
    id: int
    title: str
    repository: str
    asset_module: str
    r_i: float                       # Diem rui ro ky thuat CVSS [0.0 - 10.0]
    e_i: int                         # Cong suc uoc luong (Story Points)
    skill: str                       # Nhom ky nang OWASP (SKILL_A01 - SKILL_A10)
    earliest_sprint: int = 1         # Sprint phat hien lo hong (disc_i)
    deadline_sprint: int = 4         # Sprint han chot cam ket SLA (dead_i)

    @property
    def sprint_discovered(self) -> int:
        return self.earliest_sprint

    @property
    def disc_i(self) -> int:
        return self.earliest_sprint

    @property
    def sprint_deadline(self) -> int:
        return self.deadline_sprint

    @property
    def dead_i(self) -> int:
        return self.deadline_sprint

    def compute_utility(
        self,
        current_sprint: int = 4,
        alpha: float = 0.6,
        m_penalty: float = 0.0,
        criticality: float = 1.0,
        gamma: float = 1.5
    ) -> float:
        """
        Diem uu tien giam nhe rui ro u_i in (0, 1] (tham khao cong thuc VULCON):
        s_hat = r_i / 10.0 in [0, 1]
        p_hat = min(1.0, (elapsed / sla_window) ** gamma) in [0, 1]
        u_i = criticality * (alpha * s_hat + (1 - alpha) * p_hat)
        """
        s_hat = min(1.0, max(0.0, self.r_i / 10.0))
        elapsed = max(0, current_sprint - self.earliest_sprint)
        sla_window = max(1, self.deadline_sprint - self.earliest_sprint)
        p_hat = min(1.0, (elapsed / sla_window) ** gamma)
        u_base = criticality * (alpha * s_hat + (1.0 - alpha) * p_hat)
        # Cong them diem phat tre han neu can
        overdue_bump = 0.1 if (current_sprint >= self.deadline_sprint and m_penalty > 0) else 0.0
        return round(min(1.0, max(0.01, u_base + overdue_bump)), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "repository": self.repository,
            "asset_module": self.asset_module,
            "r_i": self.r_i,
            "e_i": self.e_i,
            "skill": self.skill,
            "disc_i": self.earliest_sprint,
            "dead_i": self.deadline_sprint,
        }


@dataclass
class Team:
    """Thuc the doi ky thuat Scrum."""
    team_id: str
    name: str
    capacity_sp: int                 # Tran dung luong Sprint theo Story Points (cap_t)
    skills: Dict[str, float]         # Ma tran diem ky nang [0.0, 1.0]

    def get_skill_score(self, skill_name: str) -> float:
        return self.skills.get(skill_name, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "capacity_sp": self.capacity_sp,
            "skills": self.skills,
        }


# ==============================================================================
# OUTPUT
# ==============================================================================

@dataclass
class ScheduleResult:
    """Ket qua phan bo va chuoi thuc thi cua rieng 1 doi trong Sprint."""
    team_id: str
    assigned_tasks: List[Task]       # Chuoi task theo thu tu thuc thi pi_t
    total_effort: int                # Tong Story Points thuc te (phai <= capacity_sp)
    context_switch_cost: float       # Tong chi phi chuyen doi noi bo doi
    mitigated_utility: float = 0.0   # Tong diem uu tien mang lai boi doi nay

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "task_ids_sequence": [t.id for t in self.assigned_tasks],
            "total_effort": self.total_effort,
            "context_switch_cost": round(self.context_switch_cost, 4),
            "mitigated_utility": round(self.mitigated_utility, 4),
            "tasks": [t.to_dict() for t in self.assigned_tasks],
        }


@dataclass
class SprintPlan:
    """Ke hoach Sprint tong the cua toan bo cac doi (nghiem hoan chinh)."""
    schedules: List[ScheduleResult]  # Danh sach ke hoach tung doi
    deferred_tasks: List[Task]       # Cac task bi hoan (luu lai backlog)
    total_risk_resolved: float       # Tong diem CVSS goc da giai quyet
    total_utility_resolved: float    # Muc tieu f1: Tong mitigation utility dat duoc
    total_risk_deferred: float       # Tong CVSS bi hoan
    total_utility_deferred: float    # Tong utility bi hoan
    total_switch_cost: float         # Muc tieu f2: Tong chi phi chuyen doi cua ca Sprint
    skill_match_score: float = 1.0   # Chi so phu (giu de tuong thich cu)
    solver_name: str = ""            # Ten thuat toan giai (CAS, CP-SAT, Greedy, ...)
    execution_time_ms: float = 0.0   # Thoi gian chay (mili-giay)
    trace_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_name": self.solver_name,
            "execution_time_ms": self.execution_time_ms,
            "f1_utility": round(self.total_utility_resolved, 2),
            "f2_switch_cost": round(self.total_switch_cost, 4),
            "total_risk_resolved": round(self.total_risk_resolved, 2),
            "assigned_task_count": sum(len(s.assigned_tasks) for s in self.schedules),
            "deferred_task_count": len(self.deferred_tasks),
            "schedules": [s.to_dict() for s in self.schedules],
            "deferred_task_ids": [t.id for t in self.deferred_tasks],
            "trace_details": self.trace_details,
        }
