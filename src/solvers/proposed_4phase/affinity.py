import numpy as np
from typing import List
from models import Task
from metrics import compute_context_distance


def build_affinity_matrix(
    tasks: List[Task],
    sigma: float = 0.5,
    dag_boost: float = 1.0,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> np.ndarray:
    """
    Xây dựng ma trận tương đồng A_ij giữa các task:
    A_ij = exp(-C_ij^2 / (2 * sigma^2))
    Nếu u và v có quan hệ DAG phụ thuộc trực tiếp (u -> v hoặc v -> u),
    tăng mạnh độ tương đồng bằng dag_boost để ép vào cùng 1 cụm.
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

            # Quan hệ DAG trực tiếp
            ti = tasks[i]
            tj = tasks[j]
            has_dag = (tj.id in ti.predecessors) or (ti.id in tj.predecessors)
            if has_dag:
                sim = max(sim, dag_boost)

            A[i, j] = sim
            A[j, i] = sim

    return A
