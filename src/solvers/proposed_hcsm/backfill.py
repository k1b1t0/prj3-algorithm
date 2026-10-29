"""
Phase 3: Residual Backfill & Hard Guardrail.
- Evaluates unassigned individual tasks against remaining capacity of teams.
- Marginal context cost: Delta C_{i -> m} = min_{j in Team_m} C_{ij} (0 if team empty).
- Marginal Knapsack Efficiency: S(i, m, w) = [w * (u_i / f1_max) - (1 - w) * (Delta C / f2_max)] / e_i.
- Hard Guardrail: Only assign task if S(i, m, w) > 0. Rejects task if S <= 0 to protect developer focus.
"""
from typing import List, Dict, Tuple, Set, Any
from models import Task, Team
from metrics import compute_context_distance


def backfill_residual_tasks(
    assigned_tasks_by_team: Dict[str, List[Task]],
    unassigned_tasks: List[Task],
    teams: List[Team],
    team_rem_cap: Dict[str, int],
    w: float = 0.5,
    f1_max: float = 1.0,
    f2_max: float = 1.0,
    current_sprint: int = 4,
    skill_threshold: float = 0.5,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> Tuple[Dict[str, List[Task]], Dict[str, int], List[Task], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Phase 3: Residual Backfill with Hard Guardrail.
    Returns:
    - assigned_tasks_by_team: Dict mapping team_id -> tasks including backfilled ones
    - team_rem_cap: Dict mapping team_id -> final remaining capacity
    - remaining_unassigned: List of still unassigned tasks
    - accepted_trace: List of accepted task decision details
    - blocked_trace: List of tasks blocked by Hard Guardrail
    """
    accepted_trace: List[Dict[str, Any]] = []
    blocked_trace: List[Dict[str, Any]] = []

    if not unassigned_tasks or not teams:
        return assigned_tasks_by_team, team_rem_cap, list(unassigned_tasks), accepted_trace, blocked_trace

    safe_f1_max = max(1e-6, f1_max)
    safe_f2_max = max(1e-6, f2_max)

    # Pre-aggregate unique contexts (repo, mod, skill) per team for fast lookups
    team_contexts: Dict[str, Set[Tuple[str, str, str]]] = {}
    for tm in teams:
        team_contexts[tm.team_id] = {
            (t.repository, t.asset_module, t.skill)
            for t in assigned_tasks_by_team.get(tm.team_id, [])
        }

    task_utilities: Dict[int, float] = {
        t.id: t.compute_utility(current_sprint=current_sprint)
        for t in unassigned_tasks
    }

    candidates = list(unassigned_tasks)

    while candidates:
        best_cand = None
        best_score = 0.0  # Hard Guardrail: strictly requires S > 0
        best_delta_z = 0.0
        best_delta_c = 0.0

        for t in candidates:
            u_i = task_utilities[t.id]

            for tm in teams:
                # 1. Skill check
                if tm.get_skill_score(t.skill) < skill_threshold:
                    continue

                # 2. Capacity check
                rem = team_rem_cap[tm.team_id]
                if t.e_i > rem:
                    continue

                # 3. Context insertion cost Delta C_{i -> m}
                contexts = team_contexts[tm.team_id]
                if not contexts:
                    delta_c = 0.0
                else:
                    min_d = 1.0
                    for r, m, s in contexts:
                        d_r = 1.0 if t.repository != r else 0.0
                        d_m = 1.0 if t.asset_module != m else 0.0
                        d_s = 1.0 if t.skill != s else 0.0
                        d = round(w_repo * d_r + w_mod * d_m + w_skill * d_s, 4)
                        if d < min_d:
                            min_d = d
                            if min_d == 0.0:
                                break
                    delta_c = min_d

                # 4. Global Objective Delta Z and Efficiency score S
                delta_z = w * (u_i / safe_f1_max) - (1.0 - w) * (delta_c / safe_f2_max)
                score = delta_z / max(1, t.e_i)

                # Hard Guardrail Check
                if score <= 0.0:
                    blocked_trace.append({
                        "task_id": t.id,
                        "team_id": tm.team_id,
                        "effort": t.e_i,
                        "delta_c": round(delta_c, 3),
                        "score_s": round(score, 5),
                        "reason": f"S <= 0 (Context loss exceeds security gain, Delta C={delta_c})"
                    })
                    continue

                if score > best_score:
                    best_score = score
                    best_delta_z = delta_z
                    best_delta_c = delta_c
                    best_cand = (t, tm)

        if best_cand is None:
            # No eligible task satisfies capacity and S > 0
            break

        chosen_task, chosen_team = best_cand
        candidates.remove(chosen_task)
        assigned_tasks_by_team[chosen_team.team_id].append(chosen_task)
        team_rem_cap[chosen_team.team_id] -= chosen_task.e_i
        team_contexts[chosen_team.team_id].add(
            (chosen_task.repository, chosen_task.asset_module, chosen_task.skill)
        )

        accepted_trace.append({
            "task_id": chosen_task.id,
            "team_id": chosen_team.team_id,
            "effort": chosen_task.e_i,
            "utility": round(task_utilities[chosen_task.id], 2),
            "delta_c": round(best_delta_c, 3),
            "delta_z": round(best_delta_z, 5),
            "score_s": round(best_score, 5),
            "rem_cap_after": team_rem_cap[chosen_team.team_id],
        })

    remaining_unassigned = candidates
    return assigned_tasks_by_team, team_rem_cap, remaining_unassigned, accepted_trace, blocked_trace
