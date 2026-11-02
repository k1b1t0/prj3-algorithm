"""
Bien the V4: w/o Effort Amortization (Bo khau hao dung luong mau so c).
O Pha 2, khong chia cho dung luong c trong cong thuc eta:
eta = w * (util / f1_max) - (1 - w) * (delta_c / f2_max)
Vi utility la ham dong bien theo c, neu khong chia cho c, thuat toan se luon chon
khoi dung luong lon nhat co the (c = min(rem_t, E(G_b))), nuot ca cac task mat do thap o day cum.
Kiem chung vai tro cua phep chia c trong viec tim Diem uon toi uu (Optimal Knee Point).
"""
from typing import List, Dict, Tuple, Optional
from models import Task, Team
from bounds import ObjectiveBounds
from solvers.proposed_hcsm.solver import ProposedHCSMSolver
from solvers.proposed_hcsm.clustering_dp import Cluster
from solvers.proposed_hcsm.path_insertion import compute_path_insertion_cost


def allocate_clusters_no_amortization(
    clusters: List[Cluster],
    teams: List[Team],
    w: float,
    f1_max: float,
    f2_max: float,
    skill_threshold: float = 0.5,
    current_sprint: int = 4
) -> Dict[str, List[Task]]:
    """Phan bo cum voi cong thuc eta khong chia cho dung luong c (eta = gain)."""
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
                    # V4: Bo chia cho dung luong c (khong khau hao theo chi phi/effort)
                    eta = gain

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

    return team_tasks


class V4NoAmortizationSolver(ProposedHCSMSolver):
    """Bien the V4: Bo chia cho dung luong c trong cong thuc eta (eta = gain)."""

    def __init__(self, name: str = "V4", **kwargs):
        super().__init__(name=name, **kwargs)

    def run_phase2(
        self,
        clusters: List[Cluster],
        teams: List[Team],
        w: float,
        bounds: ObjectiveBounds,
        skill_thresh: float,
        current_sprint: int
    ) -> Dict[str, List[Task]]:
        """Pha 2: Phan bo cum voi eta = gain (khong chia cho c)."""
        return allocate_clusters_no_amortization(
            clusters=clusters,
            teams=teams,
            w=w,
            f1_max=bounds.f1_max,
            f2_max=bounds.f2_max,
            skill_threshold=skill_thresh,
            current_sprint=current_sprint
        )
