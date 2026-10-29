"""
Proposed Algorithm: H-CSM (Hierarchical Capacitated Cluster-Simulate-Match).
4-Phase Matheuristic:
- Phase 1: Pure Atomic Coarsening & Capacitated Chunking.
- Phase 2: Multi-Cluster Packing with Global Objective Delta Z(w) / Effort.
- Phase 3: Residual Backfill & Hard Guardrail (S(i, m, w) > 0).
- Phase 4: Super-Node Block-Level Open-TSP via Bitmask DP (B <= 12).
"""
import time
from typing import List, Dict, Tuple, Optional, Any

import numpy as np

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import ObjectiveBounds, compute_static_bounds
from metrics import evaluate_schedule_switch_cost, evaluate_sprint_plan, extract_pareto_front, compute_hypervolume
from solvers.base import BaseSolver
from solvers.proposed_hcsm.coarsening import create_atomic_chunks
from solvers.proposed_hcsm.packing import pack_chunks_to_teams
from solvers.proposed_hcsm.backfill import backfill_residual_tasks
from solvers.proposed_hcsm.block_tsp import sequence_team_tasks_block_tsp
from solvers.proposed_hcsm.logger import print_phase_trace


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

        # Phase 1: Atomic Coarsening & Capacitated Chunking
        chunks, _ = create_atomic_chunks(tasks=tasks, teams=teams, current_sprint=current_sprint)

        # Phase 2: Multi-Cluster Packing with Delta Z(w)
        team_chunks, team_rem_cap, unassigned_chunks, packing_trace = pack_chunks_to_teams(
            chunks=chunks, teams=teams, w=w_val, f1_max=bounds.f1_max, f2_max=bounds.f2_max,
            skill_threshold=skill_thresh, w_repo=self.w_repo, w_mod=self.w_mod, w_skill=self.w_skill
        )

        assigned_tasks_by_team: Dict[str, List[Task]] = {tm.team_id: [] for tm in teams}
        for tm in teams:
            for ch in team_chunks[tm.team_id]:
                assigned_tasks_by_team[tm.team_id].extend(ch.tasks)

        unassigned_tasks = [t for ch in unassigned_chunks for t in ch.tasks]

        # Phase 3: Residual Backfill & Hard Guardrail (S > 0)
        assigned_tasks_by_team, team_rem_cap, remaining_unassigned, accepted_backfill, blocked_backfill = backfill_residual_tasks(
            assigned_tasks_by_team=assigned_tasks_by_team, unassigned_tasks=unassigned_tasks, teams=teams,
            team_rem_cap=team_rem_cap, w=w_val, f1_max=bounds.f1_max, f2_max=bounds.f2_max,
            current_sprint=current_sprint, skill_threshold=skill_thresh,
            w_repo=self.w_repo, w_mod=self.w_mod, w_skill=self.w_skill
        )

        # Phase 4: Super-Node Block-Level Open-TSP (Bitmask DP)
        schedules: List[ScheduleResult] = []
        routing_traces: Dict[str, Any] = {}
        for tm in teams:
            raw_tasks = assigned_tasks_by_team[tm.team_id]
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
                "chunk_count": len(chunks),
                "chunks": [{"chunk_id": c.chunk_id, "repo": c.repository, "module": c.asset_module, "skill": c.skill, "effort": c.total_effort, "task_ids": [t.id for t in c.tasks]} for c in chunks]
            },
            "phase2": {"packing_steps": packing_trace, "rem_cap_after_packing": {tm.team_id: team_rem_cap[tm.team_id] for tm in teams}},
            "phase3": {"accepted_backfills": accepted_backfill, "blocked_guardrail": blocked_backfill, "final_rem_cap": {tm.team_id: team_rem_cap[tm.team_id] for tm in teams}},
            "phase4": {"team_routes": routing_traces}
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
