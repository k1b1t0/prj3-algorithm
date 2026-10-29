"""
Inter-Team Quotient Consolidation (Phase 3.1).
Consolidates split super-nodes of same repo/module between teams via 2-exchange.
Strictly no DAG logic, line limit < 200 lines.
"""
from typing import List, Dict, Tuple
from models import Task, Team
from metrics import evaluate_schedule_switch_cost


def consolidate_inter_team_quotients(
    team_tasks: Dict[str, List[Task]],
    teams: List[Team],
    skill_threshold: float = 0.5
) -> Dict[str, List[Task]]:
    """
    Consolidate tasks of matching (repo, module) across teams if capacity allows
    and context switch cost decreases without losing utility.
    """
    team_map = {t.team_id: t for t in teams}
    team_ids = [t.team_id for t in teams]

    improved = True
    passes = 0
    while improved and passes < 3:
        improved = False
        passes += 1

        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                t1_id = team_ids[i]
                t2_id = team_ids[j]
                tm1 = team_map[t1_id]
                tm2 = team_map[t2_id]

                tasks1 = team_tasks[t1_id]
                tasks2 = team_tasks[t2_id]
                if not tasks1 or not tasks2:
                    continue

                # Group tasks by (repo, module) in team 1
                group1: Dict[Tuple[str, str], List[Task]] = {}
                for t in tasks1:
                    group1.setdefault((t.repository, t.asset_module), []).append(t)

                # Group tasks by (repo, module) in team 2
                group2: Dict[Tuple[str, str], List[Task]] = {}
                for t in tasks2:
                    group2.setdefault((t.repository, t.asset_module), []).append(t)

                # Look for common (repo, module) split between t1 and t2
                common_keys = set(group1.keys()).intersection(set(group2.keys()))
                for key in common_keys:
                    sub1 = group1[key]
                    eff1 = sum(t.e_i for t in sub1)
                    # Try moving sub1 from t1 to t2 if t2 has capacity & skills
                    rem2 = tm2.capacity_sp - sum(t.e_i for t in tasks2)
                    skill_ok2 = all(tm2.get_skill_score(t.skill) >= skill_threshold for t in sub1)

                    if rem2 >= eff1 and skill_ok2:
                        old_cost = evaluate_schedule_switch_cost(tasks1) + evaluate_schedule_switch_cost(tasks2)
                        cand1 = [t for t in tasks1 if t not in sub1]
                        cand2 = tasks2 + sub1
                        new_cost = evaluate_schedule_switch_cost(cand1) + evaluate_schedule_switch_cost(cand2)

                        if new_cost < old_cost - 1e-4:
                            team_tasks[t1_id] = cand1
                            team_tasks[t2_id] = cand2
                            improved = True
                            break

                    # Alternatively, try symmetric move: sub2 from t2 to t1
                    sub2 = group2[key]
                    eff2 = sum(t.e_i for t in sub2)
                    rem1 = tm1.capacity_sp - sum(t.e_i for t in tasks1)
                    skill_ok1 = all(tm1.get_skill_score(t.skill) >= skill_threshold for t in sub2)

                    if rem1 >= eff2 and skill_ok1:
                        old_cost = evaluate_schedule_switch_cost(tasks1) + evaluate_schedule_switch_cost(tasks2)
                        cand1 = tasks1 + sub2
                        cand2 = [t for t in tasks2 if t not in sub2]
                        new_cost = evaluate_schedule_switch_cost(cand1) + evaluate_schedule_switch_cost(cand2)

                        if new_cost < old_cost - 1e-4:
                            team_tasks[t1_id] = cand1
                            team_tasks[t2_id] = cand2
                            improved = True
                            break

                if improved:
                    break

    return team_tasks

