"""
Baseline 2: Google OR-Tools CP-SAT (Constraint Programming - SAT).
Mo hinh toan hoc No-DAG:
- Bien quyet dinh: x_{it}, z_{ijt}, pos_{it}
- Rang buoc: Knapsack dung luong, Nguong skill, Gan don nhat, Bao toan luong S-E, MTZ subtour elimination.
- Ham muc tieu vo huong hoa: Maximize Z(lambda) = f1 - lambda * f2.
"""
import time
from typing import List, Dict, Set, Optional
from ortools.sat.python import cp_model

from models import Task, Team, ScheduleResult, SprintPlan
from metrics import compute_context_distance, evaluate_sprint_plan
from solvers.base import BaseSolver


class CPSATExactSolver(BaseSolver):
    def __init__(
        self,
        name: str = "OR-Tools CP-SAT",
        time_limit_sec: float = 30.0,
        skill_threshold: float = 0.5,
        lambda_switch: float = 1.0,
        num_workers: int = 8
    ):
        super().__init__(name=name)
        self.time_limit_sec = time_limit_sec
        self.skill_threshold = skill_threshold
        self.lambda_switch = lambda_switch
        self.num_workers = num_workers

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        N = len(tasks)
        M = len(teams)
        time_limit = kwargs.get("time_limit_sec", self.time_limit_sec)
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        lambda_val = kwargs.get("lambda_switch", self.lambda_switch)
        num_workers = kwargs.get("num_workers", self.num_workers)

        teams_dict = {tm.team_id: tm for tm in teams}

        # Neu tap task rong
        if N == 0:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            return evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)

        model = cp_model.CpModel()
        id_to_idx = {t.id: i for i, t in enumerate(tasks)}

        # 1. Ma tran chi phi chuyen doi ngu canh C_ij
        c_dist = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(N):
                if i != j:
                    c_dist[i][j] = compute_context_distance(tasks[i], tasks[j])

        # 2. Bien phan bo task: x[i, t] in {0, 1}
        x = {}
        for i in range(N):
            for t in range(M):
                x[i, t] = model.NewBoolVar(f"x_{i}_{t}")

        # Rang buoc nguong ky nang: x[i, t] = 0 neu score < skill_threshold
        for i in range(N):
            for t in range(M):
                if teams[t].get_skill_score(tasks[i].skill) < skill_thresh:
                    model.Add(x[i, t] == 0)

        # Rang buoc gan don nhat: moi task gan toi da 1 team
        for i in range(N):
            model.Add(sum(x[i, t] for t in range(M)) <= 1)

        # Rang buoc dung luong knapsack: sum(e_i * x_it) <= cap_t
        for t in range(M):
            model.Add(sum(tasks[i].e_i * x[i, t] for i in range(N)) <= teams[t].capacity_sp)

        # 3. Bien thu tu va dinh tuyen chuoi theo tung team (Miller-Tucker-Zemlin flow)
        z = {}
        pos = {}

        for t in range(M):
            # pos[i, t] in [0, N]: 0 neu khong duoc gan cho team t, 1..N neu duoc gan
            for i in range(N):
                pos[i, t] = model.NewIntVar(0, N, f"pos_{i}_{t}")
                model.Add(pos[i, t] == 0).OnlyEnforceIf(x[i, t].Not())
                model.Add(pos[i, t] >= 1).OnlyEnforceIf(x[i, t])

            # Cung xuat phat tu Start S va ket thuc tai End E
            z["S", "E", t] = model.NewBoolVar(f"z_S_E_{t}")
            for i in range(N):
                z["S", i, t] = model.NewBoolVar(f"z_S_{i}_{t}")
                z[i, "E", t] = model.NewBoolVar(f"z_{i}_E_{t}")
                model.Add(pos[i, t] == 1).OnlyEnforceIf(z["S", i, t])

            # Cung giua cac task i -> j
            for i in range(N):
                for j in range(N):
                    if i != j:
                        z[i, j, t] = model.NewBoolVar(f"z_{i}_{j}_{t}")
                        # MTZ: pos[j] >= pos[i] + 1 neu z_{ijt} = 1
                        model.Add(pos[j, t] >= pos[i, t] + 1).OnlyEnforceIf(z[i, j, t])

            # Bao toan luong tai S va E
            model.Add(sum(z["S", i, t] for i in range(N)) + z["S", "E", t] == 1)
            model.Add(sum(z[i, "E", t] for i in range(N)) + z["S", "E", t] == 1)

            # Bao toan luong tai tung task i
            for i in range(N):
                in_arcs = [z[j, i, t] for j in range(N) if (j, i, t) in z] + [z["S", i, t]]
                model.Add(sum(in_arcs) == x[i, t])

                out_arcs = [z[i, j, t] for j in range(N) if (i, j, t) in z] + [z[i, "E", t]]
                model.Add(sum(out_arcs) == x[i, t])

        # 4. Ham muc tieu vo huong hoa Z(lambda) = f1 - lambda * f2 (Scale = 1000)
        SCALE = 1000
        obj_terms = []

        for i in range(N):
            u_i = tasks[i].compute_utility(current_sprint=current_sprint)
            u_scaled = int(round(u_i * SCALE))
            for t in range(M):
                obj_terms.append(u_scaled * x[i, t])

        for t in range(M):
            for i in range(N):
                for j in range(N):
                    if (i, j, t) in z:
                        cost_scaled = int(round(c_dist[i][j] * lambda_val * SCALE))
                        obj_terms.append(-cost_scaled * z[i, j, t])

        model.Maximize(sum(obj_terms))

        # 5. Cau hinh Solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit)
        solver.parameters.num_workers = int(num_workers)

        status = solver.Solve(model)
        status_name = solver.StatusName(status)

        # 6. Trich xuat nghiem
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            plan = evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)
            plan.solver_name = f"{self.name} ({status_name})"
            plan.execution_time_ms = exec_time_ms
            setattr(plan, "solver_status", status_name)
            setattr(plan, "raw_objective", 0.0)
            setattr(plan, "best_bound", 0.0)
            return plan

        schedules: List[ScheduleResult] = []
        for t in range(M):
            team = teams[t]
            assigned_indices = [i for i in range(N) if solver.Value(x[i, t]) == 1]

            # Truy vet chuoi tu S
            curr = "S"
            visited = set()
            seq = []
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

            # Fallback theo thu tu pos neu chuoi bi dut
            if len(seq) != len(assigned_indices):
                seq = sorted(
                    [tasks[i] for i in assigned_indices],
                    key=lambda t_obj: solver.Value(pos[id_to_idx[t_obj.id], t])
                )

            effort = sum(task.e_i for task in seq)
            cost = 0.0
            for k in range(len(seq) - 1):
                cost += compute_context_distance(seq[k], seq[k + 1])

            schedules.append(ScheduleResult(
                team_id=team.team_id,
                assigned_tasks=seq,
                total_effort=effort,
                context_switch_cost=round(cost, 4)
            ))

        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        plan = evaluate_sprint_plan(
            all_backlog_tasks=tasks,
            schedules=schedules,
            teams_dict=teams_dict,
            current_sprint=current_sprint,
            solver_name=f"{self.name} ({status_name})",
            execution_time_ms=exec_time_ms
        )

        setattr(plan, "solver_status", status_name)
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            setattr(plan, "raw_objective", round(solver.ObjectiveValue() / SCALE, 4))
            setattr(plan, "best_bound", round(solver.BestObjectiveBound() / SCALE, 4))
        else:
            setattr(plan, "raw_objective", 0.0)
            setattr(plan, "best_bound", 0.0)

        return plan


def solve_cpsat_exact(
    tasks: List[Task],
    teams: List[Team],
    time_limit_sec: float = 30.0,
    skill_threshold: float = 0.5,
    lambda_switch: float = 1.0,
    current_sprint: int = 4
) -> SprintPlan:
    """Wrapper function cho backward compatibility."""
    solver = CPSATExactSolver(
        time_limit_sec=time_limit_sec,
        skill_threshold=skill_threshold,
        lambda_switch=lambda_switch
    )
    return solver.solve(tasks, teams, current_sprint=current_sprint)
