"""
Pha 2: Phan bo cum nguyen tu vao cac doi va xac dinh vi tri chen duong di (Path Insertion).
Chon bo ba (cum b, muc dung luong c, doi t) co mat do tang dong gop eta lon nhat:
eta = [ w * (Delta Phi / F1_max) - (1 - w) * (Delta C / F2_max) ] / c
"""
from typing import List, Dict, Tuple, Optional
from models import Task, Team
from .clustering_dp import Cluster
from .path_insertion import compute_path_insertion_cost


def allocate_clusters_to_teams(
    clusters: List[Cluster],
    teams: List[Team],
    w: float,
    f1_max: float,
    f2_max: float,
    skill_threshold: float = 0.5,
    current_sprint: int = 4
) -> Tuple[Dict[str, List[Cluster]], Dict[str, List[Task]], Dict[str, int]]:
    """Phan bo cac cum nguyen tu cho doi dua tren mat do tang dong gop eta."""
    team_paths: Dict[str, List[Cluster]] = {t.team_id: [] for t in teams}
    team_tasks: Dict[str, List[Task]] = {t.team_id: [] for t in teams}
    team_rem_cap: Dict[str, int] = {t.team_id: t.capacity_sp for t in teams}

    max_team_cap = max(t.capacity_sp for t in teams) if teams else 30
    safe_f1 = max(1e-4, f1_max)
    safe_f2 = max(1e-4, f2_max)

    while True:
        best_candidate: Optional[Tuple[Cluster, int, str, float, int, List[Task]]] = None
        best_eta = 0.0

        for tm in teams:
            rem = team_rem_cap[tm.team_id]
            if rem <= 0:
                continue

            current_path = team_paths[tm.team_id]
            existing_repos = {c.repository for c in current_path}
            existing_mods = {c.asset_module for c in current_path}

            for cl in clusters:
                if not cl.tasks or tm.get_skill_score(cl.skill) < skill_threshold:
                    continue

                delta_c, best_pos = compute_path_insertion_cost(cl, current_path)
                max_c = min(cl.total_effort, rem)
                if max_c <= 0:
                    continue

                for c in range(max_c, 0, -1):
                    if c not in cl.dp_profile:
                        continue
                    util, subset = cl.dp_profile[c]
                    if not subset or util <= 0.0:
                        continue

                    gain = w * (util / safe_f1) - (1.0 - w) * (delta_c / safe_f2)
                    eta = gain / c

                    if cl.repository in existing_repos:
                        eta += 1e-4
                    if cl.asset_module in existing_mods:
                        eta += 1e-4

                    if eta > best_eta:
                        best_eta = eta
                        best_candidate = (cl, c, tm.team_id, delta_c, best_pos, subset)

        if best_candidate is None or best_eta <= 0.0:
            break

        cl_star, c_star, t_star, delta_c_star, pos_star, subset_star = best_candidate

        actual_effort = sum(t.e_i for t in subset_star)
        team_tasks[t_star].extend(subset_star)
        team_rem_cap[t_star] -= actual_effort

        path = team_paths[t_star]
        if not any(c.cluster_id == cl_star.cluster_id for c in path):
            path.insert(pos_star, cl_star)

        cl_star.remove_tasks(subset_star, max_cap=max_team_cap, current_sprint=current_sprint)

    return team_paths, team_tasks, team_rem_cap
