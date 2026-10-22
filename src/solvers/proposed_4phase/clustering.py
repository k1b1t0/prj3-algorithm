import numpy as np
from sklearn.cluster import SpectralClustering
from typing import List, Dict
from models import Task
from solvers.proposed_4phase.affinity import build_affinity_matrix


def cluster_tasks(
    tasks: List[Task],
    n_clusters: int,
    random_state: int = 42,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> List[List[Task]]:
    """
    Gom cụm lỗ hổng bằng Spectral Clustering dựa trên ma trận tương đồng A_ij có xét DAG boost.
    Gom thành n_clusters cụm (tương ứng với số lượng teams).
    """
    if n_clusters <= 1 or len(tasks) <= n_clusters:
        return [tasks] if n_clusters <= 1 else [[t] for t in tasks]

    A = build_affinity_matrix(tasks, w_repo=w_repo, w_mod=w_mod, w_skill=w_skill)
    sc = SpectralClustering(
        n_clusters=n_clusters,
        affinity="precomputed",
        assign_labels="kmeans",
        random_state=random_state
    )
    labels = sc.fit_predict(A)

    clusters: Dict[int, List[Task]] = {c: [] for c in range(n_clusters)}
    for task, label in zip(tasks, labels):
        clusters[label].append(task)

    return [clusters[c] for c in range(n_clusters)]
