import numpy as np
from typing import List
from models import Task
from metrics import compute_context_distance


def build_affinity_matrix(
    tasks: List[Task],
    sigma: float = 0.5,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> np.ndarray:
    """
    Xay dung ma tran tuong dong A_ij dua tren khoang cach ngu canh C_ij:
    A_ij = exp(-C_ij^2 / (2 * sigma^2))
    """
    n = len(tasks)
    A = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(i, n):
            if i == j:
                A[i, j] = 1.0
                continue
            dist = compute_context_distance(tasks[i], tasks[j], w_repo, w_mod, w_skill)
            sim = np.exp(-(dist ** 2) / (2 * (sigma ** 2)))

            A[i, j] = sim
            A[j, i] = sim

    return A
