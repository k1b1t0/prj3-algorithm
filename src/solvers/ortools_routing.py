"""
Solver su dung Google OR-Tools Routing Library (Heuristics & Metaheuristics).
Giai bai toan Capacitated Team Orienteering Problem (CTOP):
- Tuyen xe tuong ung voi Team (co dung luong cap_t).
- Cac node tuong ung voi Task (co effort e_i).
- Chi phi di chuyen giua 2 node la lambda * C_ij.
- Bo qua node bi phat bang Utility u_i (AddDisjunction).
- Heuristics: PARALLEL_CHEAPEST_INSERTION + GUIDED_LOCAL_SEARCH.
"""
import time
from typing import List, Dict, Tuple, Optional
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from models import Task, Team, SprintPlan, ScheduleResult
from metrics import evaluate_sprint_plan, compute_context_distance
from solvers.base import BaseSolver


class ORToolsRoutingHeuristicSolver(BaseSolver):
    def __init__(
        self,
        name: str = "OR-Tools Routing (GLS)",
        time_limit_sec: float = 10.0,
        skill_threshold: float = 0.5,
        scale: int = 1000
    ):
        super().__init__(name=name)
        self.time_limit_sec = time_limit_sec
        self.skill_threshold = skill_threshold
        self.scale = scale

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        lambda_switch: float = 0.5,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        N = len(tasks)
        M = len(teams)
        time_limit = kwargs.get("time_limit_sec", self.time_limit_sec)
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        lambda_val = kwargs.get("lambda_switch", lambda_switch)
        w_val = kwargs.get("w", None)
        bounds = kwargs.get("bounds", None)

        if w_val is not None:
            if bounds is None:
                from bounds import compute_static_bounds
                bounds = compute_static_bounds(tasks, teams, current_sprint=current_sprint)
            lambda_val = bounds.get_effective_lambda(w_val)

        teams_dict = {tm.team_id: tm for tm in teams}

        if N == 0 or M == 0:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            return evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)

        # Tao start depot va end depot cho Open-TSP
        start_depot = N
        end_depot = N + 1
        num_nodes = N + 2

        starts = [start_depot] * M
        ends = [end_depot] * M

        manager = pywrapcp.RoutingIndexManager(num_nodes, M, starts, ends)
        routing = pywrapcp.RoutingModel(manager)

        # Tinh utility u_i cho tung task
        task_utilities = [t.compute_utility(current_sprint=current_sprint) for t in tasks]

        # Ma tran khoang cach C_ij
        dist_matrix = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(i + 1, N):
                d = compute_context_distance(tasks[i], tasks[j])
                dist_matrix[i][j] = d
                dist_matrix[j][i] = d

        def transit_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            if from_node >= N or to_node >= N:
                return 0
            return int(round(self.scale * lambda_val * dist_matrix[from_node][to_node]))

        transit_callback_index = routing.RegisterTransitCallback(transit_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Dung luong Story Points
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node >= N:
                return 0
            return tasks[from_node].e_i

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        vehicle_capacities = [tm.capacity_sp for tm in teams]
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            vehicle_capacities,
            True,
            "Capacity"
        )

        # Disjunction (Phan thuong u_i duoi dang phat neu bo qua task)
        for i in range(N):
            node_idx = manager.NodeToIndex(i)
            penalty = int(round(self.scale * task_utilities[i]))
            routing.AddDisjunction([node_idx], penalty)

        # Rang buoc ky nang
        for i in range(N):
            node_idx = manager.NodeToIndex(i)
            allowed_vehicles = []
            for v_idx, tm in enumerate(teams):
                if tm.skills.get(tasks[i].skill, 0.0) >= skill_thresh:
                    allowed_vehicles.append(v_idx)
            routing.VehicleVar(node_idx).SetValues([-1] + allowed_vehicles)

        # Search Parameters: Parallel Cheapest Insertion + Guided Local Search
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = int(max(1, round(time_limit)))

        solution = routing.SolveWithParameters(search_parameters)
        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        schedules: List[ScheduleResult] = []
        if solution:
            for v_idx, tm in enumerate(teams):
                index = routing.Start(v_idx)
                route_tasks: List[Task] = []
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    if node < N:
                        route_tasks.append(tasks[node])
                    index = solution.Value(routing.NextVar(index))

                effort = sum(t.e_i for t in route_tasks)
                cost = 0.0
                for k in range(len(route_tasks) - 1):
                    cost += compute_context_distance(route_tasks[k], route_tasks[k + 1])

                schedules.append(ScheduleResult(
                    team_id=tm.team_id,
                    assigned_tasks=route_tasks,
                    total_effort=effort,
                    context_switch_cost=round(cost, 4)
                ))
        else:
            schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]

        status_name = "FEASIBLE" if solution else "NO_SOLUTION"
        plan = evaluate_sprint_plan(
            all_backlog_tasks=tasks,
            schedules=schedules,
            teams_dict=teams_dict,
            current_sprint=current_sprint,
            solver_name=f"{self.name} ({status_name})",
            execution_time_ms=exec_time_ms
        )
        setattr(plan, "solver_status", status_name)
        return plan


ORToolsRoutingSolver = ORToolsRoutingHeuristicSolver
