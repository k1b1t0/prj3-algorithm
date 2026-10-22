"""
Baseline 2 (Gurobi): Gurobi Optimizer Exact MIP Solver.
Mô hình hóa quy hoạch nguyên tuyến tính đa mục tiêu (MO-MILP) theo problem_model.md:
- Biến quyết định: x_{it}, z_{ijt}, pos_{it}
- Ràng buộc: Dung lượng, Ngưỡng skill, Phụ thuộc DAG (Intra-team x_{vt} <= x_{ut}), Luồng luân chuyển S-E, MTZ.
- Hàm mục tiêu vô hướng hóa: Maximize Z(lambda) = f1 - lambda * f2.
"""
import time
from typing import List, Dict, Set, Optional

from models import Task, Team, ScheduleResult, SprintPlan
from metrics import compute_context_distance, evaluate_sprint_plan
from solvers.base import BaseSolver

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False


class GurobiExactSolver(BaseSolver):
    def __init__(
        self,
        name: str = "Gurobi Optimizer",
        time_limit_sec: float = 30.0,
        skill_threshold: float = 0.5,
        lambda_switch: float = 1.0,
        threads: int = 8
    ):
        super().__init__(name=name)
        self.time_limit_sec = time_limit_sec
        self.skill_threshold = skill_threshold
        self.lambda_switch = lambda_switch
        self.threads = threads

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        teams_dict = {tm.team_id: tm for tm in teams}
        time_limit = kwargs.get("time_limit_sec", self.time_limit_sec)
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        lambda_val = kwargs.get("lambda_switch", self.lambda_switch)
        threads = kwargs.get("threads", self.threads)

        if not GUROBI_AVAILABLE:
            raise RuntimeError("gurobipy is not installed or available.")

        N = len(tasks)
        M = len(teams)

        if N == 0:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            return evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)

        id_to_idx = {t.id: i for i, t in enumerate(tasks)}

        # Tính toán ma trận C_ij
        c_dist = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(N):
                if i != j:
                    c_dist[i][j] = compute_context_distance(tasks[i], tasks[j])

        # Phụ thuộc DAG
        preds_map = {}
        for i, t in enumerate(tasks):
            preds_map[i] = [id_to_idx[p] for p in t.predecessors if p in id_to_idx]

        descendants: Dict[int, Set[int]] = {i: set() for i in range(N)}
        for i, t in enumerate(tasks):
            for p_id in t.predecessors:
                if p_id in id_to_idx:
                    descendants[id_to_idx[p_id]].add(i)

        changed = True
        while changed:
            changed = False
            for i in range(N):
                curr_desc = set(descendants[i])
                for d in curr_desc:
                    for dd in descendants[d]:
                        if dd not in descendants[i]:
                            descendants[i].add(dd)
                            changed = True

        try:
            model = gp.Model("SecOps_MIP")
            model.Params.OutputFlag = 0
            model.Params.TimeLimit = float(time_limit)
            model.Params.Threads = int(threads)

            # 1. Biến gán x[i, t]
            x = {}
            for i in range(N):
                for t in range(M):
                    x[i, t] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{t}")

            # 2. Biến vị trí pos[i, t]
            pos = {}
            for i in range(N):
                for t in range(M):
                    pos[i, t] = model.addVar(lb=0.0, ub=float(N), vtype=GRB.CONTINUOUS, name=f"pos_{i}_{t}")

            # 3. Biến cung định tuyến chuỗi z[i, j, t]
            z = {}
            for t in range(M):
                z["S", "E", t] = model.addVar(vtype=GRB.BINARY, name=f"z_S_E_{t}")
                for i in range(N):
                    z["S", i, t] = model.addVar(vtype=GRB.BINARY, name=f"z_S_{i}_{t}")
                    z[i, "E", t] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_E_{t}")
                    for j in range(N):
                        if i != j and i not in descendants[j]:
                            z[i, j, t] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{j}_{t}")

            model.update()

            # Ràng buộc kỹ năng
            for i in range(N):
                for t in range(M):
                    if teams[t].get_skill_score(tasks[i].skill) < skill_thresh:
                        model.addConstr(x[i, t] == 0)

            # Ràng buộc gán đơn nhất
            for i in range(N):
                model.addConstr(gp.quicksum(x[i, t] for t in range(M)) <= 1)

            # Ràng buộc dung lượng Story Points
            for t in range(M):
                model.addConstr(gp.quicksum(tasks[i].e_i * x[i, t] for i in range(N)) <= teams[t].capacity_sp)

            # Ràng buộc phụ thuộc DAG & Intra-team Execution (x_{vt} <= x_{ut})
            for i in range(N):
                for p in preds_map[i]:
                    for t in range(M):
                        model.addConstr(x[i, t] <= x[p, t])

            # Ràng buộc luồng S-E và bảo toàn tại từng task
            for t in range(M):
                # Luồng từ S
                model.addConstr(gp.quicksum(z["S", i, t] for i in range(N)) + z["S", "E", t] == 1)
                # Luồng tới E
                model.addConstr(gp.quicksum(z[i, "E", t] for i in range(N)) + z["S", "E", t] == 1)

                for i in range(N):
                    # Khớp pos với x
                    model.addConstr(pos[i, t] >= x[i, t])
                    model.addConstr(pos[i, t] <= N * x[i, t])

                    in_arcs = [z[j, i, t] for j in range(N) if (j, i, t) in z] + [z["S", i, t]]
                    model.addConstr(gp.quicksum(in_arcs) == x[i, t])

                    out_arcs = [z[i, j, t] for j in range(N) if (i, j, t) in z] + [z[i, "E", t]]
                    model.addConstr(gp.quicksum(out_arcs) == x[i, t])

                    # MTZ subtour elimination
                    for j in range(N):
                        if (i, j, t) in z:
                            model.addConstr(pos[j, t] >= pos[i, t] + 1 - N * (1 - z[i, j, t]))

                    # Quan hệ topo nội bộ team
                    for p in preds_map[i]:
                        model.addConstr(pos[p, t] <= pos[i, t] - 1 + N * (2 - x[p, t] - x[i, t]))

            # Hàm mục tiêu vô hướng hóa Maximize Z = f1 - lambda * f2
            f1_terms = []
            for i in range(N):
                u_i = tasks[i].compute_utility(current_sprint=current_sprint)
                for t in range(M):
                    f1_terms.append(u_i * x[i, t])

            f2_terms = []
            for t in range(M):
                for i in range(N):
                    for j in range(N):
                        if (i, j, t) in z:
                            f2_terms.append(c_dist[i][j] * z[i, j, t])

            model.setObjective(
                gp.quicksum(f1_terms) - lambda_val * gp.quicksum(f2_terms),
                GRB.MAXIMIZE
            )

            model.optimize()

            status_name = "FEASIBLE"
            if model.Status == GRB.OPTIMAL:
                status_name = "OPTIMAL"
            elif model.Status == GRB.TIME_LIMIT:
                status_name = "TIME_LIMIT"
            elif model.Status == GRB.INFEASIBLE:
                status_name = "INFEASIBLE"

            # Trích xuất nghiệm
            schedules: List[ScheduleResult] = []
            for t in range(M):
                team = teams[t]
                assigned_indices = [i for i in range(N) if x[i, t].X > 0.5] if model.SolCount > 0 else []

                curr = "S"
                visited = set()
                seq = []
                while True:
                    next_node = None
                    for j in range(N):
                        if (curr, j, t) in z and z[curr, j, t].X > 0.5 and j not in visited:
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
                        key=lambda t_obj: pos[id_to_idx[t_obj.id], t].X
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
            if model.SolCount > 0:
                setattr(plan, "raw_objective", round(model.ObjVal, 4))
                setattr(plan, "best_bound", round(model.ObjBound, 4))

            return plan

        except gp.GurobiError as e:
            # Xử lý trường hợp giới hạn kích thước license hoặc lỗi cấu hình
            exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            plan = evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)
            plan.solver_name = f"{self.name} (LICENSE/SIZE LIMIT: {str(e)[:30]})"
            plan.execution_time_ms = exec_time_ms
            setattr(plan, "solver_status", "LICENSE_LIMITED")
            return plan


def solve_gurobi_exact(
    tasks: List[Task],
    teams: List[Team],
    time_limit_sec: float = 30.0,
    skill_threshold: float = 0.5,
    lambda_switch: float = 1.0,
    current_sprint: int = 4
) -> SprintPlan:
    """Wrapper function cho Gurobi solver."""
    solver = GurobiExactSolver(
        time_limit_sec=time_limit_sec,
        skill_threshold=skill_threshold,
        lambda_switch=lambda_switch
    )
    return solver.solve(tasks, teams, current_sprint=current_sprint)
