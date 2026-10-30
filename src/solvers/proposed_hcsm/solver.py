"""
Proposed Algorithm: H-CSM (Hierarchical Capacitated Cluster-Simulate-Match).
Quotient-DP Matheuristic (3-Phase Architecture):
- Phase 1: Quotient Space Reduction & Exact Intra-Cluster DP Profiling.
- Phase 2: Unified Multiple-Choice Quotient Allocation with Exact Path Insertion.
- Phase 3: Inter-Team Quotient Consolidation & Exact Bitmask DP Open-TSP.
Strictly no DAG logic, line limit < 200 lines.
"""
import time
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import ObjectiveBounds, compute_static_bounds
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan, extract_pareto_front, compute_hypervolume
from solvers.base import BaseSolver
from .quotient_dp import partition_into_quotient_clusters
from .quotient_allocation import allocate_quotient_clusters
from .inter_team_swap import consolidate_inter_team_quotients
from .block_tsp import sequence_team_tasks_block_tsp
from .logger import print_phase_trace


class ProposedHCSMSolver(BaseSolver):
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

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        w: Optional[float] = None,
        bounds: Optional[ObjectiveBounds] = None,
        verbose: bool = False,
        detailed: bool = False,
        **kwargs
    ) -> SprintPlan:
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

        # Phase 1: Quotient Space Reduction & Exact Intra-Cluster DP Profiling
        clusters = partition_into_quotient_clusters(tasks=tasks, max_cap=max_cap, current_sprint=current_sprint)

        # Phase 2: Unified Multiple-Choice Quotient Allocation with Exact Path Insertion
        team_paths, team_tasks, team_rem_cap = allocate_quotient_clusters(
            clusters=clusters, teams=teams, w=w_val, f1_max=bounds.f1_max, f2_max=bounds.f2_max,
            skill_threshold=skill_thresh, current_sprint=current_sprint
        )

        # Phase 3.1: Inter-Team Quotient Consolidation
        team_tasks = consolidate_inter_team_quotients(
            team_tasks=team_tasks, teams=teams, skill_threshold=skill_thresh,
            w_repo=self.w_repo, w_mod=self.w_mod, w_skill=self.w_skill
        )

        # Phase 3.2: Intra-Team Exact Bitmask DP Open-TSP
        schedules: List[ScheduleResult] = []
        routing_traces: Dict[str, Any] = {}
        for tm in teams:
            raw_tasks = team_tasks[tm.team_id]
            ordered_tasks, route_info = sequence_team_tasks_block_tsp(
                tasks=raw_tasks, current_sprint=current_sprint,
                w_repo=self.w_repo, w_mod=self.w_mod, w_skill=self.w_skill
            )
            effort = sum(t.e_i for t in ordered_tasks)
            cost = evaluate_schedule_switch_cost(ordered_tasks, self.w_repo, self.w_mod, self.w_skill)
            utility = sum(t.compute_utility(current_sprint) for t in ordered_tasks)

            schedules.append(ScheduleResult(
                team_id=tm.team_id, assigned_tasks=ordered_tasks, total_effort=effort,
                context_switch_cost=cost, mitigated_utility=round(utility, 4)
            ))
            routing_traces[tm.team_id] = route_info

        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        trace_details = {
            "weight_w": w_val,
            "bounds": {"f1_max": bounds.f1_max, "f2_max": bounds.f2_max},
            "phase1": {
                "input_task_count": len(tasks),
                "cluster_count": len(clusters),
                "clusters": [{"id": c.cluster_id, "repo": c.repository, "mod": c.asset_module, "effort": c.total_effort} for c in clusters]
            },
            "phase2": {"rem_cap": team_rem_cap},
            "phase3": {"team_routes": routing_traces}
        }

        plan = evaluate_sprint_plan(
            all_backlog_tasks=tasks, schedules=schedules, teams_dict=teams_dict,
            current_sprint=current_sprint, solver_name=self.name,
            execution_time_ms=exec_time_ms, trace_details=trace_details
        )

        if verbose or detailed:
            print_phase_trace(plan, trace_details, detailed=detailed)

        return plan

    def solve_pareto(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        n_points: int = 11,
        ref_point: Tuple[float, float] = (0.0, 30.0),
        **kwargs
    ) -> Tuple[List[SprintPlan], List[Tuple[float, float]], float]:
        """Sweep w in [0.0, 1.0] across n_points to build Pareto Front."""
        bounds = compute_static_bounds(tasks, teams, current_sprint=current_sprint)
        weights = np.linspace(0.0, 1.0, n_points)
        plans: List[SprintPlan] = []
        pts: List[Tuple[float, float]] = []

        for w in weights:
            plan = self.solve(tasks, teams, current_sprint=current_sprint, w=float(w), bounds=bounds, **kwargs)
            plans.append(plan)
            pts.append((plan.total_utility_resolved, plan.total_switch_cost))

        front = extract_pareto_front(pts)
        hv = compute_hypervolume(front, ref_point)
        return plans, front, hv


def solve_hcsm(tasks: List[Task], teams: List[Team], current_sprint: int = 4, w: float = 0.5, **kwargs) -> SprintPlan:
    return ProposedHCSMSolver(**kwargs).solve(tasks, teams, current_sprint=current_sprint, w=w)
