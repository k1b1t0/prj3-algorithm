from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Task:
    """Định nghĩa một công việc vá lỗ hổng trong Backlog (Vulnerability Task)."""
    id: int
    title: str
    repository: str
    asset_module: str
    r_i: float                       # Điểm rủi ro kỹ thuật gốc (CVSS) [0.0 - 10.0]
    e_i: int                         # Nỗ lực xử lý (Story Points)
    skill: str                       # Kỹ năng yêu cầu (OWASP A01-A10)
    earliest_sprint: int = 1         # Sprint phát hiện lỗ hổng (disc_i)
    deadline_sprint: int = 4         # Sprint hạn chót SLA (dead_i)
    predecessors: List[int] = field(default_factory=list) # Danh sách ID task cha (DAG)

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
        Tính điểm Mitigation Utility u_i:
        u_i = r_i + alpha * max(0, tau - disc_i) + M_penalty * I(tau >= dead_i)
        """
        persistence = max(0, current_sprint - self.earliest_sprint)
        urgency = 1.0 if current_sprint >= self.deadline_sprint else 0.0
        return round(self.r_i + alpha * persistence + m_penalty * urgency, 4)


@dataclass
class Team:
    """Định nghĩa một đội kỹ thuật tham gia Sprint (Cross-Functional Team)."""
    team_id: str
    name: str
    capacity_sp: int                 # Dung lượng Story Points tối đa trong sprint (cap_t)
    skills: Dict[str, float]         # Độ thành thạo kỹ năng k_{t, s} in [0.0, 1.0]

    def get_skill_score(self, skill_name: str) -> float:
        return self.skills.get(skill_name, 0.0)


@dataclass
class ScheduleResult:
    """Kết quả lập lịch cho 1 team trong sprint."""
    team_id: str
    assigned_tasks: List[Task]       # Các task được chọn làm theo thứ tự chuỗi đã xếp
    total_effort: int
    context_switch_cost: float       # Chi phí chuyển đổi ngữ cảnh nội bộ team
    mitigated_utility: float = 0.0   # Tổng utility u_i của các task gán cho team


@dataclass
class SprintPlan:
    """Tổng hợp kế hoạch lập lịch toàn hệ thống trong sprint."""
    schedules: List[ScheduleResult]
    deferred_tasks: List[Task]       # Các task bị hoãn sang sprint sau
    total_risk_resolved: float       # Tổng CVSS r_i đã xử lý
    total_utility_resolved: float    # Tổng Mitigation Utility u_i (f1)
    total_risk_deferred: float       # Tổng CVSS r_i bị hoãn
    total_utility_deferred: float    # Tổng Mitigation Utility u_i bị hoãn
    total_switch_cost: float         # Tổng chi phí chuyển đổi ngữ cảnh f2
    skill_match_score: float         # Điểm tương thích kỹ năng trung bình
    dag_violations: int              # Số lượng vi phạm ràng buộc thứ tự DAG
    solver_name: str = ""
    execution_time_ms: float = 0.0
