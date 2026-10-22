"""
Proposed Metaheuristic: Memetic NSGA-II (Non-dominated Sorting Genetic Algorithm II).
Thiết kế theo draft-nsga.md:
- Mã hóa 2 phần: Topo Priority List & Team Assignment Vector.
- Giải mã Topo đảm bảo 100% khả thi và không vi phạm DAG.
- Tinh chỉnh chuỗi nội bộ từng team bằng Bitmask DP (Memetic Local Search).
- Khảo sát toàn diện Mặt cong Pareto (Pareto Frontier) và chỉ số Hypervolume (HV).
"""
import copy
import random
import time
from typing import List, Dict, Tuple, Optional

from models import Task, Team, ScheduleResult, SprintPlan
from metrics import compute_hypervolume, extract_pareto_front, evaluate_sprint_plan
from solvers.base import BaseSolver
from solvers.proposed_nsga2.chromosome import Chromosome
from solvers.proposed_nsga2.decoder import decode_chromosome
from solvers.proposed_nsga2.operators import (
    create_initial_population,
    order_crossover,
    crossover_assignment,
    mutate_chromosome,
    fast_non_dominated_sort,
    calculate_crowding_distance,
    tournament_select
)


class ProposedNSGA2Solver(BaseSolver):
    def __init__(
        self,
        name: str = "Proposed-NSGA-II",
        pop_size: int = 40,
        generations: int = 30,
        crossover_prob: float = 0.85,
        mutation_prob: float = 0.2,
        skill_threshold: float = 0.5,
        lambda_switch: float = 1.0,
        random_seed: int = 42
    ):
        super().__init__(name=name)
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.skill_threshold = skill_threshold
        self.lambda_switch = lambda_switch
        self.random_seed = random_seed

    def solve(
        self,
        tasks: List[Task],
        teams: List[Team],
        current_sprint: int = 4,
        **kwargs
    ) -> SprintPlan:
        t0 = time.perf_counter()
        pop_sz = kwargs.get("pop_size", self.pop_size)
        n_gens = kwargs.get("generations", self.generations)
        cx_prob = kwargs.get("crossover_prob", self.crossover_prob)
        mut_prob = kwargs.get("mutation_prob", self.mutation_prob)
        skill_thresh = kwargs.get("skill_threshold", self.skill_threshold)
        lambda_val = kwargs.get("lambda_switch", self.lambda_switch)
        seed = kwargs.get("random_seed", self.random_seed)

        rng = random.Random(seed)
        teams_dict = {tm.team_id: tm for tm in teams}

        if not tasks:
            empty_schedules = [
                ScheduleResult(team_id=tm.team_id, assigned_tasks=[], total_effort=0, context_switch_cost=0.0)
                for tm in teams
            ]
            return evaluate_sprint_plan(tasks, empty_schedules, teams_dict, current_sprint=current_sprint)

        # 1. Khởi tạo quần thể ban đầu P_0
        population = create_initial_population(
            tasks=tasks,
            teams=teams,
            pop_size=pop_sz,
            rng=rng,
            skill_threshold=skill_thresh
        )

        # Đánh giá quần thể P_0
        for chrom in population:
            decode_chromosome(
                chrom=chrom,
                tasks=tasks,
                teams=teams,
                current_sprint=current_sprint,
                skill_threshold=skill_thresh,
                apply_memetic_dp=False  # Đánh giá nhanh trong quần thể đầu
            )

        fronts = fast_non_dominated_sort(population)
        for front in fronts:
            calculate_crowding_distance(front)

        # 2. Vòng lặp tiến hóa qua các thế hệ
        for gen in range(n_gens):
            offspring: List[Chromosome] = []

            while len(offspring) < pop_sz:
                p1 = tournament_select(population, rng)
                p2 = tournament_select(population, rng)

                if rng.random() < cx_prob:
                    c1_p, c2_p = order_crossover(p1.priority, p2.priority, tasks, rng)
                    c1_a, c2_a = crossover_assignment(p1.assignment, p2.assignment, rng)
                else:
                    c1_p, c1_a = list(p1.priority), dict(p1.assignment)
                    c2_p, c2_a = list(p2.priority), dict(p2.assignment)

                c1 = Chromosome(priority=c1_p, assignment=c1_a)
                c2 = Chromosome(priority=c2_p, assignment=c2_a)

                mutate_chromosome(c1, tasks, teams, rng, mut_prob, skill_thresh)
                mutate_chromosome(c2, tasks, teams, rng, mut_prob, skill_thresh)

                # Giải mã con
                decode_chromosome(c1, tasks, teams, current_sprint, skill_thresh, apply_memetic_dp=False)
                decode_chromosome(c2, tasks, teams, current_sprint, skill_thresh, apply_memetic_dp=False)

                offspring.append(c1)
                if len(offspring) < pop_sz:
                    offspring.append(c2)

            # Kết hợp R_t = P_t + Q_t
            combined = population + offspring
            fronts = fast_non_dominated_sort(combined)

            # Chọn lọc thế hệ kế tiếp P_{t+1}
            new_pop: List[Chromosome] = []
            for front in fronts:
                calculate_crowding_distance(front)
                if len(new_pop) + len(front) <= pop_sz:
                    new_pop.extend(front)
                else:
                    # Lấy thêm các cá thể có khoảng cách tập trung lớn nhất
                    remaining_slots = pop_sz - len(new_pop)
                    front.sort(key=lambda ind: ind.crowding_dist, reverse=True)
                    new_pop.extend(front[:remaining_slots])
                    break

            population = new_pop

        # 3. Trích xuất Mặt Pareto cuối cùng (Front 0)
        final_fronts = fast_non_dominated_sort(population)
        pareto_chromosomes = final_fronts[0]

        # Áp dụng Memetic Local Search hoàn chỉnh cho các cá thể trên Pareto Front
        for chrom in pareto_chromosomes:
            decode_chromosome(
                chrom=chrom,
                tasks=tasks,
                teams=teams,
                current_sprint=current_sprint,
                skill_threshold=skill_thresh,
                apply_memetic_dp=True  # Bật Bitmask DP để tinh chỉnh chuỗi
            )

        # Lọc lại tập nghiệm không bị thống trị sau khi làm mịn bằng DP
        raw_pareto_points = [chrom.objectives for chrom in pareto_chromosomes]
        pareto_front = extract_pareto_front(raw_pareto_points)

        # Tính toán Hypervolume (HV) với Reference Point chuẩn hóa
        ref_point = kwargs.get("ref_point", (0.0, 15.0))
        hv = compute_hypervolume(pareto_front, ref_point=ref_point)

        # Chọn nghiệm đại diện (Compromise Solution) tối đa hóa Z = f1 - lambda * f2
        best_chrom = max(
            pareto_chromosomes,
            key=lambda c: c.objectives[0] - lambda_val * c.objectives[1]
        )
        plan = best_chrom.decoded_plan
        assert plan is not None

        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        plan.solver_name = self.name
        plan.execution_time_ms = exec_time_ms

        # Gắn kèm metadata Pareto & Hypervolume vào SprintPlan
        setattr(plan, "pareto_front", pareto_front)
        setattr(plan, "hypervolume", hv)
        setattr(plan, "ref_point", ref_point)

        return plan


def solve_nsga2(
    tasks: List[Task],
    teams: List[Team],
    pop_size: int = 40,
    generations: int = 30,
    skill_threshold: float = 0.5,
    lambda_switch: float = 1.0,
    current_sprint: int = 4,
    random_seed: int = 42
) -> SprintPlan:
    """Wrapper function cho Memetic NSGA-II solver."""
    solver = ProposedNSGA2Solver(
        pop_size=pop_size,
        generations=generations,
        skill_threshold=skill_threshold,
        lambda_switch=lambda_switch,
        random_seed=random_seed
    )
    return solver.solve(tasks, teams, current_sprint=current_sprint)
