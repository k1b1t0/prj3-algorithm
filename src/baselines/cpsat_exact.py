"""
Exact Baseline Solver using Google OR-Tools CP-SAT (Constraint Programming - Satisfiability).
Mô hình hóa bài toán quy hoạch nguyên tuyến tính tối ưu hóa toàn cục:
- Ràng buộc: Dung lượng Sprint <= cap_t, Ngưỡng skill >= skill_threshold, Phụ thuộc DAG (selection & ordering), MTZ.
- Hàm mục tiêu: Tối đa hóa Z = sum(r_i * x_it) - lambda * sum(C_ij * z_ijt) + mu * sum(skill * x_it).
"""
import time
from typing import List, Dict, Tuple, Set, Optional
from ortools.sat.python import cp_model

from models import Task, Team, ScheduleResult, SprintPlan
from metrics import compute_context_distance, evaluate_sprint_plan


def solve_cpsat_exact(
    tasks: List[Task],
    teams: List[Team],
    time_limit_sec: float = 60.0,
    skill_threshold: float = 0.5,
    relative_gap_limit: float = 0.02,
    lambda_switch: float = 1.0,
    mu_skill: float = 1.0
) -> SprintPlan:
    """
    Giai toan bo phuong an lap lich sprint bang Google OR-Tools CP-SAT.
    Tra ve SprintPlan tuong thich 100% voi he thong danh gia benchmark.
    """
    N = len(tasks)
    M = len(teams)

    # Neu tap task rong
    if N == 0:
        teams_dict = {tm.team_id: tm for tm in teams}
        empty_schedules = [
            ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
            for tm in teams
        ]
        return evaluate_sprint_plan(tasks, empty_schedules, teams_dict)

    t0 = time.time()
    model = cp_model.CpModel()
    id_to_idx = {t.id: i for i, t in enumerate(tasks)}

    # 1. Lan truyen do thi DAG de tim quan he reachability (descendants)
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

    preds_map = {}
    for i, t in enumerate(tasks):
        preds_map[i] = [id_to_idx[p] for p in t.predecessors if p in id_to_idx]

    # 2. Ma tran khoang cach chuyen ngu canh C_ij
    c_dist = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i != j:
                c_dist[i][j] = compute_context_distance(tasks[i], tasks[j])

    # 3. Bien quyet dinh gan task: x[i, t] in {0, 1}
    x = {}
    for i in range(N):
        for t in range(M):
            x[i, t] = model.NewBoolVar(f"x_{i}_{t}")

    # Rang buoc nguong ky nang: x[i, t] = 0 neu score < skill_threshold
    for i in range(N):
        for t in range(M):
            if teams[t].get_skill_score(tasks[i].skill) < skill_threshold:
                model.Add(x[i, t] == 0)

    # Rang buoc gan duy nhat: Moi task gan cho toi da 1 team
    for i in range(N):
        model.Add(sum(x[i, t] for t in range(M)) <= 1)

    # Rang buoc tran dung luong: sum(e_i * x_it) <= cap_t
    for t in range(M):
        model.Add(sum(tasks[i].e_i * x[i, t] for i in range(N)) <= teams[t].capacity_sp)

    # Rang buoc lua chon phu thuoc DAG: Neu con duoc chon, cha bat buoc phai duoc chon
    for i in range(N):
        for p in preds_map[i]:
            model.Add(sum(x[i, t] for t in range(M)) <= sum(x[p, t] for t in range(M)))

    # 4. Bien thu tu va cung noi bo theo team (Miller-Tucker-Zemlin flow)
    z = {}
    pos = {}

    for t in range(M):
        # pos[i, t] in [0, N]: 0 neu khong duoc gan cho team t, 1..N neu duoc gan
        for i in range(N):
            pos[i, t] = model.NewIntVar(0, N, f"pos_{i}_{t}")
            model.Add(pos[i, t] == 0).OnlyEnforceIf(x[i, t].Not())
            model.Add(pos[i, t] >= 1).OnlyEnforceIf(x[i, t])

        # Cung tu Start S va den End E
        z["S", "E", t] = model.NewBoolVar(f"z_S_E_{t}")
        for i in range(N):
            z["S", i, t] = model.NewBoolVar(f"z_S_{i}_{t}")
            z[i, "E", t] = model.NewBoolVar(f"z_{i}_E_{t}")
            # Neu S -> i thi task i la task dau tien (pos = 1)
            model.Add(pos[i, t] == 1).OnlyEnforceIf(z["S", i, t])

        # Cung giua cac task i -> j
        for i in range(N):
            for j in range(N):
                if i != j:
                    # Neu i la hau due cua j trong DAG thi i khong the di truoc j
                    if i in descendants[j]:
                        continue
                    z[i, j, t] = model.NewBoolVar(f"z_{i}_{j}_{t}")
                    # Rang buoc MTZ: neu i di ngay truoc j thi pos[j] >= pos[i] + 1
                    model.Add(pos[j, t] >= pos[i, t] + 1).OnlyEnforceIf(z[i, j, t])

        # Luu luong bao toan tai S va E
        model.Add(sum(z["S", i, t] for i in range(N)) + z["S", "E", t] == 1)
        model.Add(sum(z[i, "E", t] for i in range(N)) + z["S", "E", t] == 1)

        # Luu luong bao toan tai tung task i
        for i in range(N):
            in_arcs = [z[j, i, t] for j in range(N) if (j, i, t) in z] + [z["S", i, t]]
            model.Add(sum(in_arcs) == x[i, t])

            out_arcs = [z[i, j, t] for j in range(N) if (i, j, t) in z] + [z[i, "E", t]]
            model.Add(sum(out_arcs) == x[i, t])

        # Thu tu topo tren cung 1 team: neu ca cha p va con i cung duoc gan cho team t
        for i in range(N):
            for p in preds_map[i]:
                model.Add(pos[p, t] < pos[i, t]).OnlyEnforceIf([x[p, t], x[i, t]])

    # 5. Thiet lap ham muc tieu so nguyen co ty le hoa (Scale = 1000)
    SCALE = 1000
    obj_terms = []

    for t in range(M):
        for i in range(N):
            risk_scaled = int(round(tasks[i].r_i * SCALE))
            skill_scaled = int(round(teams[t].get_skill_score(tasks[i].skill) * mu_skill * SCALE))
            obj_terms.append((risk_scaled + skill_scaled) * x[i, t])

            for j in range(N):
                if (i, j, t) in z:
                    cost_scaled = int(round(c_dist[i][j] * lambda_switch * SCALE))
                    obj_terms.append(-cost_scaled * z[i, j, t])

    model.Maximize(sum(obj_terms))

    # 6. Cau hinh bo giai CP-SAT
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_sec)
    solver.parameters.num_workers = 8
    if relative_gap_limit > 0:
        solver.parameters.relative_gap_limit = float(relative_gap_limit)

    status = solver.Solve(model)
    solve_duration = time.time() - t0
    status_name = solver.StatusName(status)

    # 7. Trich xuat nghiem va tao ScheduleResult cho tung team
    teams_dict = {tm.team_id: tm for tm in teams}
    schedules: List[ScheduleResult] = []

    for t in range(M):
        team = teams[t]
        assigned_indices = [i for i in range(N) if solver.Value(x[i, t]) == 1]

        # Truy vet chuoi thu tu cong viec tu cung S
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

        # Co che du phong phong ve: sap xep theo gia tri pos neu co giat doan cung
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

    # 8. Tong hop va danh gia SprintPlan
    plan = evaluate_sprint_plan(tasks, schedules, teams_dict)
    
    # Gan them cac metadata phu tro phuc vu bao cao benchmark
    setattr(plan, "solver_status", status_name)
    setattr(plan, "solve_duration", round(solve_duration, 4))
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        setattr(plan, "raw_objective", round(solver.ObjectiveValue() / SCALE, 4))
        setattr(plan, "best_bound", round(solver.BestObjectiveBound() / SCALE, 4))
    else:
        setattr(plan, "raw_objective", 0.0)
        setattr(plan, "best_bound", 0.0)

    return plan
