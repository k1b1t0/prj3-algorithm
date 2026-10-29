"""
Baseline 2: Google OR-Tools CP-SAT (Constraint Programming - SAT).
Solves MO-MILP formulation:
- Variables: x_{it}, z_{uvt}, pos_{it}
- Constraints: Knapsack capacity, Skill threshold, Single assignment, Flow conservation (S-E), MTZ subtour elimination.
- Objective: Maximize Z(w) = w * norm(f1) - (1 - w) * norm(f2).
"""
import time
from typing import List, Dict, Set, Optional, Tuple
from ortools.sat.python import cp_model

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import compute_static_bounds
from metrics import compute_context_distance, evaluate_sprint_plan
from solvers.base import BaseSolver


def _extract_schedules(solver, tasks, teams, x, z, pos, id_to_idx, N, M) -> List[ScheduleResult]:
    """Helper to reconstruct execution sequences from CP-SAT solution."""
    schedules: List[ScheduleResult] = []
    for t in range(M):
        team = teams[t]
        assigned_indices = [i for i in range(N) if solver.Value(x[i, t]) == 1]
        curr = "S"
        visited: Set[int] = set()
        seq: List[Task] = []
        while True:
            next_node = None
            for j in range(N):
                if (curr, j, t) in z and solver.Value(z[curr, j, t]) == 1 and j not in visited:
                    next_node = j
                    break
            if next_node is not None:
                seq.append(tasks[next_node])
                visited.add(next_node)
                curr = next_node
            else:
                break

        if len(seq) != len(assigned_indices):
            seq = sorted(
                [tasks[i] for i in assigned_indices],
                key=lambda t_obj: solver.Value(pos[id_to_idx[t_obj.id], t])
            )

        effort = sum(task.e_i for task in seq)
        cost = sum(compute_context_distance(seq[k], seq[k + 1]) for k in range(len(seq) - 1))
        schedules.append(ScheduleResult(
            team_id=team.team_id, assigned_tasks=seq,
            total_effort=effort, context_switch_cost=round(cost, 4)
        ))
    return schedules


class CPSATExactSolver(BaseSolver):
    def __init__(
        self,
        name: str = "OR-Tools CP-SAT",
        time_limit_sec: float = 30.0,
        skill_threshold: float = 0.5,
        num_workers: int = 8
    ):
        super().__init__(name=name)
        self.time_limit_sec = time_limit_sec
        self.skill_threshold = skill_threshold
        self.num_workers = num_workers

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        N, M = len(tasks), len(teams)
        time_limit = kwargs.get("time_limit_sec", self.time_limit_sec)
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        w_val = kwargs.get("w", 0.5)
        bounds = kwargs.get("bounds") or compute_static_bounds(tasks, teams, current_sprint)
        teams_dict = {tm.team_id: tm for tm in teams}

        if N == 0:
            empty = [ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0) for tm in teams]
            return evaluate_sprint_plan(tasks, empty, teams_dict, current_sprint=current_sprint)

        model = cp_model.CpModel()
        id_to_idx = {t.id: i for i, t in enumerate(tasks)}
        c_dist = [[compute_context_distance(tasks[i], tasks[j]) if i != j else 0.0 for j in range(N)] for i in range(N)]

        # 1. Assignment Variables x[i, t]
        x = {}
        for i in range(N):
            for t in range(M):
                x[i, t] = model.NewBoolVar(f"x_{i}_{t}")
                if teams[t].get_skill_score(tasks[i].skill) < skill_thresh:
                    model.Add(x[i, t] == 0)

        for i in range(N):
            model.Add(sum(x[i, t] for t in range(M)) <= 1)

        for t in range(M):
            model.Add(sum(tasks[i].e_i * x[i, t] for i in range(N)) <= teams[t].capacity_sp)

        # 2. MTZ Routing Variables z[u, v, t], pos[i, t]
        z, pos = {}, {}
        for t in range(M):
            for i in range(N):
                pos[i, t] = model.NewIntVar(0, N, f"pos_{i}_{t}")
                model.Add(pos[i, t] == 0).OnlyEnforceIf(x[i, t].Not())
                model.Add(pos[i, t] >= 1).OnlyEnforceIf(x[i, t])

            z["S", "E", t] = model.NewBoolVar(f"z_S_E_{t}")
            for i in range(N):
                z["S", i, t] = model.NewBoolVar(f"z_S_{i}_{t}")
                z[i, "E", t] = model.NewBoolVar(f"z_{i}_E_{t}")
                model.Add(pos[i, t] == 1).OnlyEnforceIf(z["S", i, t])

            for i in range(N):
                for j in range(N):
                    if i != j:
                        z[i, j, t] = model.NewBoolVar(f"z_{i}_{j}_{t}")
                        model.Add(pos[j, t] >= pos[i, t] + 1).OnlyEnforceIf(z[i, j, t])

            model.Add(sum(z["S", i, t] for i in range(N)) + z["S", "E", t] == 1)
            model.Add(sum(z[i, "E", t] for i in range(N)) + z["S", "E", t] == 1)

            for i in range(N):
                in_arcs = [z[j, i, t] for j in range(N) if (j, i, t) in z] + [z["S", i, t]]
                model.Add(sum(in_arcs) == x[i, t])
                out_arcs = [z[i, j, t] for j in range(N) if (i, j, t) in z] + [z[i, "E", t]]
                model.Add(sum(out_arcs) == x[i, t])

        # 3. Normalized Objective Function Z(w)
        SCALE = 100_000
        f1_span = max(1e-6, bounds.f1_max - bounds.f1_min)
        f2_span = max(1e-6, bounds.f2_max - bounds.f2_min)
        coeff_u = (w_val / f1_span) * SCALE
        coeff_c = ((1.0 - w_val) / f2_span) * SCALE

        obj_terms = []
        for i in range(N):
            u_i = tasks[i].compute_utility(current_sprint=current_sprint)
            u_scaled = int(round(u_i * coeff_u))
            for t in range(M):
                obj_terms.append(u_scaled * x[i, t])

        for t in range(M):
            for i in range(N):
                for j in range(N):
                    if (i, j, t) in z:
                        cost_scaled = int(round(c_dist[i][j] * coeff_c))
                        obj_terms.append(-cost_scaled * z[i, j, t])

        model.Maximize(sum(obj_terms))

        # 4. Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit)
        solver.parameters.num_workers = int(kwargs.get("num_workers", self.num_workers))

        status = solver.Solve(model)
        status_name = solver.StatusName(status)
        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            empty = [ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0) for tm in teams]
            plan = evaluate_sprint_plan(tasks, empty, teams_dict, current_sprint=current_sprint)
            plan.solver_name = f"{self.name} ({status_name})"
            plan.execution_time_ms = exec_time_ms
            setattr(plan, "solver_status", status_name)
            return plan

        schedules = _extract_schedules(solver, tasks, teams, x, z, pos, id_to_idx, N, M)
        plan = evaluate_sprint_plan(
            all_backlog_tasks=tasks, schedules=schedules, teams_dict=teams_dict,
            current_sprint=current_sprint, solver_name=f"{self.name} ({status_name})",
            execution_time_ms=exec_time_ms
        )
        setattr(plan, "solver_status", status_name)
        return plan


def solve_cpsat_exact(tasks: List[Task], teams: List[Team], **kwargs) -> SprintPlan:
    return CPSATExactSolver(**kwargs).solve(tasks, teams)
