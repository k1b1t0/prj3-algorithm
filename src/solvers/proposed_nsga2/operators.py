import random
from typing import List, Dict, Tuple
from collections import defaultdict
from models import Task, Team
from solvers.proposed_nsga2.chromosome import Chromosome


def topological_repair(order: List[int], tasks: List[Task]) -> List[int]:
    """
    Ham giu lai cho backward-compatibility.
    Trong bai toan No-DAG, moi hoan vi deu hop le.
    """
    return list(order)


def generate_random_topological_sort(tasks: List[Task], rng: random.Random) -> List[int]:
    """Sinh ngau nhien mot hoan vi thu tu uu tien cua cac task."""
    order = [t.id for t in tasks]
    rng.shuffle(order)
    return order


def create_initial_population(
    tasks: List[Task],
    teams: List[Team],
    pop_size: int,
    rng: random.Random,
    skill_threshold: float = 0.5
) -> List[Chromosome]:
    """Khoi tao quan the ban dau voi da dang nghiem."""
    population = []

    for _ in range(pop_size):
        priority = generate_random_topological_sort(tasks, rng)
        assignment = {}
        for t in tasks:
            # Tim danh sach cac team du ky nang
            capable = [i + 1 for i, tm in enumerate(teams) if tm.get_skill_score(t.skill) >= skill_threshold]
            if capable and rng.random() < 0.85:
                # 85% kha nang gan cho 1 team du ky nang
                assignment[t.id] = rng.choice(capable)
            else:
                # 15% kha nang gan cho 0 (hoan sang sprint sau)
                assignment[t.id] = 0

        population.append(Chromosome(priority=priority, assignment=assignment))

    return population


def order_crossover(
    p1: List[int],
    p2: List[int],
    tasks: List[Task],
    rng: random.Random
) -> Tuple[List[int], List[int]]:
    """Toan tu Lai ghep Thu tu (Order Crossover - OX)."""
    size = len(p1)
    if size <= 2:
        return list(p1), list(p2)

    cx1 = rng.randint(0, size - 2)
    cx2 = rng.randint(cx1 + 1, size - 1)

    def ox(parent_a, parent_b):
        child = [None] * size
        child[cx1:cx2 + 1] = parent_a[cx1:cx2 + 1]
        copied_set = set(parent_a[cx1:cx2 + 1])

        # Dien cac vi tri con lai tu parent_b
        fill_vals = [item for item in parent_b if item not in copied_set]
        fill_idx = 0
        for i in range(size):
            if child[i] is None:
                if fill_idx < len(fill_vals):
                    child[i] = fill_vals[fill_idx]
                    fill_idx += 1
                else:
                    child[i] = parent_a[i]
        return child

    c1 = ox(p1, p2)
    c2 = ox(p2, p1)
    return c1, c2


def crossover_assignment(
    a1: Dict[int, int],
    a2: Dict[int, int],
    rng: random.Random
) -> Tuple[Dict[int, int], Dict[int, int]]:
    """Lai ghep dong deu (Uniform Crossover) tren vector chi dinh team."""
    c1, c2 = {}, {}
    for k in a1.keys():
        if rng.random() < 0.5:
            c1[k] = a1[k]
            c2[k] = a2.get(k, 0)
        else:
            c1[k] = a2.get(k, 0)
            c2[k] = a1[k]
    return c1, c2


def mutate_chromosome(
    chrom: Chromosome,
    tasks: List[Task],
    teams: List[Team],
    rng: random.Random,
    mutation_rate: float = 0.2,
    skill_threshold: float = 0.5
):
    """Toan tu Dot bien Thich ung (Adaptive Mutation): Doi Team va Hoan doi thu tu."""
    # 1. Dot bien Doi Team
    for t in tasks:
        if rng.random() < mutation_rate:
            capable = [i + 1 for i, tm in enumerate(teams) if tm.get_skill_score(t.skill) >= skill_threshold]
            if capable and rng.random() < 0.7:
                chrom.assignment[t.id] = rng.choice(capable)
            else:
                chrom.assignment[t.id] = 0

    # 2. Dot bien Hoan doi thu tu (Swap Mutation)
    if len(chrom.priority) > 2 and rng.random() < mutation_rate:
        idx1 = rng.randrange(len(chrom.priority))
        idx2 = rng.randrange(len(chrom.priority))
        chrom.priority[idx1], chrom.priority[idx2] = chrom.priority[idx2], chrom.priority[idx1]


def fast_non_dominated_sort(population: List[Chromosome]) -> List[List[Chromosome]]:
    """Thuat toan Sap xep Khong bi thong tri nhanh (Fast Non-dominated Sort cua Deb et al.)."""
    front_indices: List[List[int]] = [[]]
    S: Dict[int, List[int]] = defaultdict(list)
    n = [0] * len(population)

    for p_idx, p in enumerate(population):
        for q_idx, q in enumerate(population):
            if p.dominates(q):
                S[p_idx].append(q_idx)
            elif q.dominates(p):
                n[p_idx] += 1

        if n[p_idx] == 0:
            p.rank = 0
            front_indices[0].append(p_idx)

    curr_idx = 0
    while curr_idx < len(front_indices) and front_indices[curr_idx]:
        next_front: List[int] = []
        for p_idx in front_indices[curr_idx]:
            for q_idx in S[p_idx]:
                n[q_idx] -= 1
                if n[q_idx] == 0:
                    population[q_idx].rank = curr_idx + 1
                    next_front.append(q_idx)
        curr_idx += 1
        if next_front:
            front_indices.append(next_front)
        else:
            break

    return [[population[i] for i in front] for front in front_indices if front]


def calculate_crowding_distance(front: List[Chromosome]):
    """Gan khoang cach tap trung (Crowding Distance) cho cac ca the trong cung mot Front."""
    l = len(front)
    if l == 0:
        return
    for ind in front:
        ind.crowding_dist = 0.0

    if l <= 2:
        for ind in front:
            ind.crowding_dist = float("inf")
        return

    # Muc tieu 1: f1 (Utility - Maximize)
    front.sort(key=lambda ind: ind.objectives[0])
    front[0].crowding_dist = float("inf")
    front[-1].crowding_dist = float("inf")
    f1_min = front[0].objectives[0]
    f1_max = front[-1].objectives[0]
    f1_range = f1_max - f1_min if f1_max > f1_min else 1.0

    for i in range(1, l - 1):
        front[i].crowding_dist += (front[i + 1].objectives[0] - front[i - 1].objectives[0]) / f1_range

    # Muc tieu 2: f2 (Switch Cost - Minimize)
    front.sort(key=lambda ind: ind.objectives[1])
    front[0].crowding_dist = float("inf")
    front[-1].crowding_dist = float("inf")
    f2_min = front[0].objectives[1]
    f2_max = front[-1].objectives[1]
    f2_range = f2_max - f2_min if f2_max > f2_min else 1.0

    for i in range(1, l - 1):
        front[i].crowding_dist += (front[i + 1].objectives[1] - front[i - 1].objectives[1]) / f2_range


def tournament_select(population: List[Chromosome], rng: random.Random) -> Chromosome:
    """Chon loc Tournament nhi phan dua tren (Rank, Crowding Distance)."""
    cand1 = rng.choice(population)
    cand2 = rng.choice(population)

    if cand1.rank < cand2.rank:
        return cand1
    elif cand2.rank < cand1.rank:
        return cand2
    else:
        return cand1 if cand1.crowding_dist >= cand2.crowding_dist else cand2
