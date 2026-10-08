import numpy as np
from sklearn.cluster import SpectralClustering
from typing import List, Dict
from ..models import Task
from .affinity import build_affinity_matrix


def cluster_tasks(tasks: List[Task], n_clusters: int, random_state: int = 42) -> List[List[Task]]:
    # Gom cum lo hong bang Spectral Clustering dua tren ma tran tuong dong A_ij
    # Gom thanh n_clusters cum (tuong ung voi so luong teams)
    if n_clusters <= 1 or len(tasks) <= n_clusters:
        return [tasks]

    A = build_affinity_matrix(tasks)
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

    # Chuyen thanh list cac cum task
    return [clusters[c] for c in range(n_clusters)]
