"""
Bien the V3: w/o Path-Awareness (Phan bo mu ngu canh).
O Pha 2, triet tieu so hang chi phi chen duong di (Delta C = 0) trong ham tinh eta.
Thuat toan chi toi uu loi ich an ninh f1 ma khong quan tam den viec cum duoc gan co lam tang f2 hay khong.
Kiem chung tac dung kiem che f2 va chong phan manh cong viec cua co che chen duong di re nhat.
"""
from typing import List, Dict, Tuple, Optional
from models import Task, Team
from bounds import ObjectiveBounds
from solvers.proposed_cas.solver import ProposedCASSolver
from solvers.proposed_cas.clustering_dp import Cluster


def allocate_clusters_no_path_aware(
    clusters: List[Cluster],
    teams: List[Team],
    w: float,
    f1_max: float,
    skill_threshold: float = 0.5,
    current_sprint: int = 4
) -> Dict[str, List[Task]]:
    """Phan bo cum cho doi bo qua chi phi duong di (Delta C = 0, khong co tie-breaker repo/module)."""
    team_tasks: Dict[str, List[Task]] = {t.team_id: [] for t in teams}
    team_rem_cap: Dict[str, int] = {t.team_id: t.capacity_sp for t in teams}

    max_team_cap = max(t.capacity_sp for t in teams) if teams else 30
    safe_f1 = max(1e-4, f1_max)

    while True:
        best_candidate: Optional[Tuple[Cluster, int, str, List[Task]]] = None
        best_eta = 0.0

        for tm in teams:
            rem = team_rem_cap[tm.team_id]
            if rem <= 0:
                continue

            for cl in clusters:
                if not cl.tasks or tm.get_skill_score(cl.skill) < skill_threshold:
                    continue

                max_c = min(cl.total_effort, rem)
                if max_c <= 0:
                    continue

                for c in range(max_c, 0, -1):
                    if c not in cl.dp_profile:
                        continue
                    util, subset = cl.dp_profile[c]
                    if not subset or util <= 0.0:
                        continue

                    # V3: Delta C = 0, khong tinh chi phi duong di
                    gain = w * (util / safe_f1)
                    eta = gain / c

                    if eta > best_eta:
                        best_eta = eta
                        best_candidate = (cl, c, tm.team_id, subset)

        if best_candidate is None or best_eta <= 0.0:
            break

        cl_star, c_star, t_star, subset_star = best_candidate

        actual_effort = sum(t.e_i for t in subset_star)
        team_tasks[t_star].extend(subset_star)
        team_rem_cap[t_star] -= actual_effort

        cl_star.remove_tasks(subset_star, max_cap=max_team_cap, current_sprint=current_sprint)

    return team_tasks


class V3NoPathAwareSolver(ProposedCASSolver):
    """Bien the V3: Dat Delta C = 0 trong Pha 2 (khong tinh chi phi chen duong di)."""

    def __init__(self, name: str = "V3", **kwargs):
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
        """Pha 2: Phan bo cum khong quan tam chi phi duong di."""
        return allocate_clusters_no_path_aware(
            clusters=clusters,
            teams=teams,
            w=w,
            f1_max=bounds.f1_max,
            skill_threshold=skill_thresh,
            current_sprint=current_sprint
        )
