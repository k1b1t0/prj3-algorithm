import numpy as np
from typing import List
from models import Task
from metrics import compute_context_distance


def build_affinity_matrix(tasks: List[Task], sigma: float = 0.5, dag_boost: float = 1.0) -> np.ndarray:
    # Xay dung ma tran tuong dong A_ij giua cac task:
    # A_ij = exp(-C_ij^2 / (2 * sigma^2))
    # Neu u va v co quan he DAG (u -> v hoac v -> u), tang manh affinity bang dag_boost
    n = len(tasks)
    A = np.zeros((n, n), dtype=float)
    id_to_idx = {t.id: i for i, t in enumerate(tasks)}

    for i in range(n):
        for j in range(i, n):
            if i == j:
                A[i, j] = 1.0
                continue
            dist = compute_context_distance(tasks[i], tasks[j])
            sim = np.exp(-(dist ** 2) / (2 * (sigma ** 2)))

            # Kiem tra neu co quan he DAG phu thuoc truc tiep
            ti = tasks[i]
            tj = tasks[j]
            has_dag = (tj.id in ti.predecessors) or (ti.id in tj.predecessors)
            if has_dag:
                sim = max(sim, dag_boost)

            A[i, j] = sim
            A[j, i] = sim

    return A
