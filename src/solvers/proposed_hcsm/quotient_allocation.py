"""
Unified Multiple-Choice Quotient Allocation with Path Insertion (Phase 2).
Selects (cluster, budget, team) maximizing marginal efficiency rate eta:
eta = [ w * (Delta Phi / F1_max) - (1 - w) * (Delta C / F2_max) ] / c
Strictly no DAG logic, line limit < 200 lines.
"""
from typing import List, Dict, Tuple, Optional
from models import Task, Team
from .quotient_dp import QuotientCluster
from .cheapest_insertion import compute_cheapest_insertion


def allocate_quotient_clusters(
    clusters: List[QuotientCluster],
    teams: List[Team],
    w: float,
    f1_max: float,
    f2_max: float,
    skill_threshold: float = 0.5,
    current_sprint: int = 4
) -> Tuple[Dict[str, List[QuotientCluster]], Dict[str, List[Task]], Dict[str, int]]:
    """
    Allocate quotient clusters to teams using scale-amortized marginal rate.
    Returns:
    - team_paths: team_id -> list of QuotientCluster
    - team_tasks: team_id -> list of Task
    - team_rem_cap: team_id -> remaining SP
    """
    team_paths: Dict[str, List[QuotientCluster]] = {t.team_id: [] for t in teams}
    team_tasks: Dict[str, List[Task]] = {t.team_id: [] for t in teams}
    team_rem_cap: Dict[str, int] = {t.team_id: t.capacity_sp for t in teams}
    team_map = {t.team_id: t for t in teams}

    max_team_cap = max(t.capacity_sp for t in teams) if teams else 30
    safe_f1 = max(1e-4, f1_max)
    safe_f2 = max(1e-4, f2_max)

    while True:
        best_candidate: Optional[Tuple[QuotientCluster, int, str, float, int, List[Task]]] = None
        best_eta = 0.0

        for tm in teams:
            rem = team_rem_cap[tm.team_id]
            if rem <= 0:
                continue

            current_path = team_paths[tm.team_id]
            # Track repos and modules currently handled by this team
            existing_repos = {c.repository for c in current_path}
            existing_mods = {c.asset_module for c in current_path}

            for cl in clusters:
                if not cl.tasks or tm.get_skill_score(cl.skill) < skill_threshold:
                    continue

                delta_c, best_pos = compute_cheapest_insertion(cl, current_path)
                max_c = min(cl.total_effort, rem)
                if max_c <= 0:
                    continue

                # Evaluate feasible capacity levels in cluster DP profile
                # Check top capacity levels down to 1
                for c in range(max_c, 0, -1):
                    if c not in cl.dp_profile:
                        continue
                    util, subset = cl.dp_profile[c]
                    if not subset or util <= 0.0:
                        continue

                    # Marginal objective gain per unit effort
                    gain = w * (util / safe_f1) - (1.0 - w) * (delta_c / safe_f2)
                    eta = gain / c

                    # Tie-breaking bonus for domain affinity
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

        # Commit assignment
        actual_effort = sum(t.e_i for t in subset_star)
        team_tasks[t_star].extend(subset_star)
        team_rem_cap[t_star] -= actual_effort

        # Insert cluster into path if not already visited
        path = team_paths[t_star]
        if not any(c.cluster_id == cl_star.cluster_id for c in path):
            path.insert(pos_star, cl_star)

        # Remove tasks from cluster and re-run DP on residual tasks
        cl_star.remove_tasks(subset_star, max_cap=max_team_cap, current_sprint=current_sprint)

    return team_paths, team_tasks, team_rem_cap

