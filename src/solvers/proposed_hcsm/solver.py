"""
Thuat toan de xuat: H-CSM (Hierarchical Capacitated Cluster-Simulate-Match).
Kien truc dieu phoi 3 pha:
- Pha 1: Phan cum nguyen tu C_ij = 0 va lap bang 1D DP (clustering_dp.py).
- Pha 2: Phan bo da lua chon tich hop chen duong di re nhat (allocation.py, path_insertion.py).
- Pha 3: Hoan doi cum lien doi (inter_team_swap.py) va Dinh tuyen noi bo doi (task_sequencing.py).
"""
import time
from typing import List, Dict, Optional

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import ObjectiveBounds, compute_static_bounds
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan
from solvers.base import BaseSolver
from .clustering_dp import partition_clusters, Cluster
from .allocation import allocate_clusters_to_teams
from .inter_team_swap import swap_inter_team_clusters
from .task_sequencing import sequence_team_tasks


class ProposedHCSMSolver(BaseSolver):
    """Bo giai dieu phoi chinh cua thuat toan H-CSM."""

    def __init__(
        self,
        name: str = "Proposed-H-CSM",
        skill_threshold: float = 0.5,
        default_w: float = 0.5,
        w_repo: float = 0.5,
        w_mod: float = 0.3,
        w_skill: float = 0.2
    ):
        super().__init__(name=name)
        self.skill_threshold = skill_threshold
        self.default_w = default_w
        self.w_repo = w_repo
        self.w_mod = w_mod
        self.w_skill = w_skill

    def run_phase1(self, tasks: List[Task], max_cap: int, current_sprint: int) -> List[Cluster]:
        """Pha 1: Phan cum C_ij = 0 va lap bang DP 1 chieu."""
        return partition_clusters(tasks=tasks, max_cap=max_cap, current_sprint=current_sprint)

    def run_phase2(
        self,
        clusters: List[Cluster],
        teams: List[Team],
        w: float,
        bounds: ObjectiveBounds,
        skill_thresh: float,
        current_sprint: int
    ) -> Dict[str, List[Task]]:
        """Pha 2: Phan bo cum vao cac doi kem chen duong di re nhat."""
        _, team_tasks, _ = allocate_clusters_to_teams(
            clusters=clusters,
            teams=teams,
            w=w,
            f1_max=bounds.f1_max,
            f2_max=bounds.f2_max,
            skill_threshold=skill_thresh,
            current_sprint=current_sprint
        )
        return team_tasks

    def run_phase3_swap(
        self,
        team_tasks: Dict[str, List[Task]],
        teams: List[Team],
        skill_thresh: float
    ) -> Dict[str, List[Task]]:
        """Pha 3.1: Hoan doi cum giua hai doi (1-0 Relocate, 1-1 Block Swap) de giam f2."""
        return swap_inter_team_clusters(
            team_tasks=team_tasks,
            teams=teams,
            skill_threshold=skill_thresh,
            w_repo=self.w_repo,
            w_mod=self.w_mod,
            w_skill=self.w_skill
        )

    def run_phase3_sequencing(self, tasks: List[Task], current_sprint: int) -> List[Task]:
        """Pha 3.2: Dinh tuyen thu tu thuc thi noi bo doi bang Bitmask DP Open-TSP."""
        return sequence_team_tasks(
            tasks=tasks,
            current_sprint=current_sprint,
            w_repo=self.w_repo,
            w_mod=self.w_mod,
            w_skill=self.w_skill
        )

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        w: Optional[float] = None,
        bounds: Optional[ObjectiveBounds] = None,
        **kwargs
    ) -> SprintPlan:
        """Dieu phoi toan bo quy trinh 3 pha de tao ke hoach Sprint toi uu."""
        t0 = time.perf_counter()
        w_val = self.default_w if w is None else w
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        teams_dict = {tm.team_id: tm for tm in teams}
        max_cap = max((tm.capacity_sp for tm in teams), default=30)

        if bounds is None:
            bounds = compute_static_bounds(tasks, teams, current_sprint=current_sprint)

        if not tasks or not teams:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            plan = evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)
            plan.solver_name = self.name
            plan.execution_time_ms = round((time.perf_counter() - t0) * 1000, 2)
            return plan

        # Dieu phoi 3 pha
        clusters = self.run_phase1(tasks, max_cap, current_sprint)
        team_tasks = self.run_phase2(clusters, teams, w_val, bounds, skill_thresh, current_sprint)
        team_tasks = self.run_phase3_swap(team_tasks, teams, skill_thresh)

        # Dinh tuyen thu tu va tinh chi phi cho tung doi
        schedules: List[ScheduleResult] = []
        for tm in teams:
            ordered_tasks = self.run_phase3_sequencing(team_tasks[tm.team_id], current_sprint)
            effort = sum(t.e_i for t in ordered_tasks)
            cost = evaluate_schedule_switch_cost(ordered_tasks, self.w_repo, self.w_mod, self.w_skill)
            utility = sum(t.compute_utility(current_sprint) for t in ordered_tasks)

            schedules.append(ScheduleResult(
                team_id=tm.team_id,
                assigned_tasks=ordered_tasks,
                total_effort=effort,
                context_switch_cost=cost,
                mitigated_utility=round(utility, 4)
            ))

        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        plan = evaluate_sprint_plan(
            all_backlog_tasks=tasks,
            schedules=schedules,
            teams_dict=teams_dict,
            current_sprint=current_sprint,
            solver_name=self.name,
            execution_time_ms=exec_time_ms
        )
        return plan


def solve_hcsm(tasks: List[Task], teams: List[Team], current_sprint: int = 4, w: float = 0.5, **kwargs) -> SprintPlan:
    """Ham bọc tien ich goi truc tiep ProposedHCSMSolver.solve()."""
    return ProposedHCSMSolver(**kwargs).solve(tasks, teams, current_sprint=current_sprint, w=w)
