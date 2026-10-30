"""
Inter-Team Quotient Consolidation (Phase 3.1).
Consolidates split super-nodes between teams via 1-0 Relocate and 1-1 Block Swap.
Strictly no DAG logic, line limit < 200 lines.
"""
from typing import List, Dict, Tuple, Optional
from models import Task, Team
from metrics import evaluate_schedule_switch_cost
from .block_tsp import sequence_team_tasks_block_tsp


def _eval_team_cost(
    tasks: List[Task],
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """Tinh chi phi chuyen doi ngu canh toi uu cua 1 doi tren cac khoi sieu dinh."""
    if len(tasks) <= 1:
        return 0.0
    ordered, _ = sequence_team_tasks_block_tsp(
        tasks, w_repo=w_repo, w_mod=w_mod, w_skill=w_skill
    )
    return evaluate_schedule_switch_cost(
        ordered, w_repo=w_repo, w_mod=w_mod, w_skill=w_skill
    )


def consolidate_inter_team_quotients(
    team_tasks: Dict[str, List[Task]],
    teams: List[Team],
    skill_threshold: float = 0.5,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> Dict[str, List[Task]]:
    """
    Tinh chinh lien doi bang 1-0 Relocate va 1-1 Block Swap de giam f2
    ma khong lam suy giam f1 hay vi pham dung luong, ky nang.
    """
    team_map = {t.team_id: t for t in teams}
    team_ids = [t.team_id for t in teams]

    improved = True
    passes = 0
    while improved and passes < 3:
        improved = False
        passes += 1
        best_delta = -1e-4
        best_move: Optional[Tuple[str, str, List[Task], List[Task]]] = None

        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                t1_id, t2_id = team_ids[i], team_ids[j]
                tm1, tm2 = team_map[t1_id], team_map[t2_id]
                tasks1, tasks2 = team_tasks[t1_id], team_tasks[t2_id]
                if not tasks1 or not tasks2:
                    continue

                curr_cost = (
                    _eval_team_cost(tasks1, w_repo, w_mod, w_skill)
                    + _eval_team_cost(tasks2, w_repo, w_mod, w_skill)
                )

                # Gom cac task cua moi doi theo khoi sieu dinh (repo, mod, skill)
                g1: Dict[Tuple[str, str, str], List[Task]] = {}
                for t in tasks1:
                    g1.setdefault((t.repository, t.asset_module, t.skill), []).append(t)

                g2: Dict[Tuple[str, str, str], List[Task]] = {}
                for t in tasks2:
                    g2.setdefault((t.repository, t.asset_module, t.skill), []).append(t)

                used1 = sum(t.e_i for t in tasks1)
                used2 = sum(t.e_i for t in tasks2)

                # 1. Thu Relocate 1-0: Chuyen khoi u tu t1 sang t2 (hoac nguoc lai)
                for k1, sub1 in g1.items():
                    eff1 = sum(t.e_i for t in sub1)
                    if used2 + eff1 <= tm2.capacity_sp and all(
                        tm2.get_skill_score(t.skill) >= skill_threshold for t in sub1
                    ):
                        cand1 = [t for t in tasks1 if t not in sub1]
                        cand2 = tasks2 + sub1
                        d = (
                            _eval_team_cost(cand1, w_repo, w_mod, w_skill)
                            + _eval_team_cost(cand2, w_repo, w_mod, w_skill)
                        ) - curr_cost
                        if d < best_delta:
                            best_delta = d
                            best_move = (t1_id, t2_id, cand1, cand2)

                for k2, sub2 in g2.items():
                    eff2 = sum(t.e_i for t in sub2)
                    if used1 + eff2 <= tm1.capacity_sp and all(
                        tm1.get_skill_score(t.skill) >= skill_threshold for t in sub2
                    ):
                        cand1 = tasks1 + sub2
                        cand2 = [t for t in tasks2 if t not in sub2]
                        d = (
                            _eval_team_cost(cand1, w_repo, w_mod, w_skill)
                            + _eval_team_cost(cand2, w_repo, w_mod, w_skill)
                        ) - curr_cost
                        if d < best_delta:
                            best_delta = d
                            best_move = (t1_id, t2_id, cand1, cand2)

                # 2. Thu Swap 1-1: Trao doi khoi u cua t1 voi khoi v cua t2
                for k1, sub1 in g1.items():
                    eff1 = sum(t.e_i for t in sub1)
                    for k2, sub2 in g2.items():
                        if k1 == k2:
                            continue
                        eff2 = sum(t.e_i for t in sub2)
                        # Kiem tra dung luong bu tru ca 2 doi
                        if (
                            used1 - eff1 + eff2 > tm1.capacity_sp
                            or used2 - eff2 + eff1 > tm2.capacity_sp
                        ):
                            continue
                        # Kiem tra ky nang ca 2 doi
                        if not all(
                            tm1.get_skill_score(t.skill) >= skill_threshold for t in sub2
                        ):
                            continue
                        if not all(
                            tm2.get_skill_score(t.skill) >= skill_threshold for t in sub1
                        ):
                            continue

                        cand1 = [t for t in tasks1 if t not in sub1] + sub2
                        cand2 = [t for t in tasks2 if t not in sub2] + sub1
                        d = (
                            _eval_team_cost(cand1, w_repo, w_mod, w_skill)
                            + _eval_team_cost(cand2, w_repo, w_mod, w_skill)
                        ) - curr_cost
                        if d < best_delta:
                            best_delta = d
                            best_move = (t1_id, t2_id, cand1, cand2)

        if best_move is not None:
            t1_id, t2_id, c1, c2 = best_move
            team_tasks[t1_id] = c1
            team_tasks[t2_id] = c2
            improved = True

    return team_tasks
