from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Task:
    """Vulnerability task entity in the Backlog."""
    id: int
    title: str
    repository: str
    asset_module: str
    r_i: float                       # CVSS technical risk [0.0 - 10.0]
    e_i: int                         # Effort in Story Points
    skill: str                       # OWASP skill category (SKILL_A01 - SKILL_A10)
    earliest_sprint: int = 1         # Sprint discovered (disc_i)
    deadline_sprint: int = 4         # SLA deadline sprint (dead_i)

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
        alpha: float = 0.5,
        m_penalty: float = 50.0
    ) -> float:
        """
        Compute dynamic mitigation utility:
        u_i = r_i + alpha * max(0, tau - disc_i) + M_penalty * I(tau >= dead_i)
        """
        persistence = max(0, current_sprint - self.earliest_sprint)
        urgency = 1.0 if current_sprint >= self.deadline_sprint else 0.0
        return round(self.r_i + alpha * persistence + m_penalty * urgency, 4)

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
    """Scrum engineering team entity."""
    team_id: str
    name: str
    capacity_sp: int                 # Sprint capacity in SP (cap_t)
    skills: Dict[str, float]         # Skill competency matrix in [0.0, 1.0]

    def get_skill_score(self, skill_name: str) -> float:
        return self.skills.get(skill_name, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "capacity_sp": self.capacity_sp,
            "skills": self.skills,
        }


@dataclass
class ScheduleResult:
    """Team schedule result in a Sprint."""
    team_id: str
    assigned_tasks: List[Task]       # Assigned tasks in execution sequence pi_m
    total_effort: int
    context_switch_cost: float       # Internal team context switch cost
    mitigated_utility: float = 0.0

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
    """Consolidated Sprint Plan across all teams."""
    schedules: List[ScheduleResult]
    deferred_tasks: List[Task]
    total_risk_resolved: float       # Sum CVSS r_i
    total_utility_resolved: float    # Sum utility u_i (f1)
    total_risk_deferred: float
    total_utility_deferred: float
    total_switch_cost: float         # Context switch cost (f2)
    skill_match_score: float
    solver_name: str = ""
    execution_time_ms: float = 0.0
    trace_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_name": self.solver_name,
            "execution_time_ms": self.execution_time_ms,
            "f1_utility": round(self.total_utility_resolved, 2),
            "f2_switch_cost": round(self.total_switch_cost, 4),
            "total_risk_resolved": round(self.total_risk_resolved, 2),
            "skill_match_score": round(self.skill_match_score, 4),
            "assigned_task_count": sum(len(s.assigned_tasks) for s in self.schedules),
            "deferred_task_count": len(self.deferred_tasks),
            "schedules": [s.to_dict() for s in self.schedules],
            "deferred_task_ids": [t.id for t in self.deferred_tasks],
            "trace_details": self.trace_details,
        }
