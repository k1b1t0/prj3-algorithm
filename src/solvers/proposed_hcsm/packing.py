"""
Phase 2: Multi-Cluster Packing using Global Objective Delta Z(w).
- Bridge distance: Delta C(B_k, A_m) = min C(B_k, B_q) (if A_m is empty, Delta C = 0).
- Global Marginal Gain: Gain(B_k, m, w) = w * (U(B_k) / f1_max) - (1 - w) * (Delta C(B_k, A_m) / f2_max).
- Packing Density: Density = Gain / E_k.
- Greedy assignment maximizing Density, satisfying skill capability and team capacity.
"""
from typing import List, Dict, Tuple, Set, Any
from models import Team
from solvers.proposed_hcsm.coarsening import TaskChunk


def compute_chunk_distance(
    chunk_a: TaskChunk,
    chunk_b: TaskChunk,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> float:
    """Compute context distance between two TaskChunks."""
    if chunk_a.chunk_id == chunk_b.chunk_id:
        return 0.0
    d_repo = 1.0 if chunk_a.repository != chunk_b.repository else 0.0
    d_mod = 1.0 if chunk_a.asset_module != chunk_b.asset_module else 0.0
    d_skill = 1.0 if chunk_a.skill != chunk_b.skill else 0.0
    return round(w_repo * d_repo + w_mod * d_mod + w_skill * d_skill, 4)


def pack_chunks_to_teams(
    chunks: List[TaskChunk],
    teams: List[Team],
    w: float = 0.5,
    f1_max: float = 1.0,
    f2_max: float = 1.0,
    skill_threshold: float = 0.5,
    w_repo: float = 0.5,
    w_mod: float = 0.3,
    w_skill: float = 0.2
) -> Tuple[Dict[str, List[TaskChunk]], Dict[str, int], List[TaskChunk], List[Dict[str, Any]]]:
    """
    Phase 2: Greedy Multi-Cluster Packing.
    Returns:
    - team_chunks: Dict mapping team_id -> list of assigned TaskChunks
    - team_rem_cap: Dict mapping team_id -> remaining SP capacity
    - unassigned_chunks: List of unassigned TaskChunks
    - packing_trace: List of assignment step logs
    """
    team_chunks: Dict[str, List[TaskChunk]] = {tm.team_id: [] for tm in teams}
    team_rem_cap: Dict[str, int] = {tm.team_id: tm.capacity_sp for tm in teams}
    assigned_chunk_ids: Set[int] = set()
    packing_trace: List[Dict[str, Any]] = []

    if not chunks or not teams:
        return team_chunks, team_rem_cap, list(chunks), packing_trace

    safe_f1_max = max(1e-6, f1_max)
    safe_f2_max = max(1e-6, f2_max)

    # Precompute pairwise chunk distances
    n_chunks = len(chunks)
    dist_matrix: Dict[Tuple[int, int], float] = {}
    for i in range(n_chunks):
        for j in range(i, n_chunks):
            d = compute_chunk_distance(chunks[i], chunks[j], w_repo, w_mod, w_skill)
            dist_matrix[(chunks[i].chunk_id, chunks[j].chunk_id)] = d
            dist_matrix[(chunks[j].chunk_id, chunks[i].chunk_id)] = d

    while True:
        best_cand = None
        best_density = -float("inf")
        best_gain = -float("inf")
        best_delta_c = 0.0

        for chunk in chunks:
            if chunk.chunk_id in assigned_chunk_ids:
                continue

            for tm in teams:
                # 1. Skill check
                if tm.get_skill_score(chunk.skill) < skill_threshold:
                    continue

                # 2. Capacity check
                rem = team_rem_cap[tm.team_id]
                if chunk.total_effort > rem:
                    continue

                # 3. Bridge context cost Delta C(B_k, A_m)
                assigned_to_tm = team_chunks[tm.team_id]
                if not assigned_to_tm:
                    delta_c = 0.0
                else:
                    delta_c = min(
                        dist_matrix[(chunk.chunk_id, q.chunk_id)]
                        for q in assigned_to_tm
                    )

                # 4. Global Objective Delta Z(w) Gain & Density
                gain = w * (chunk.total_utility / safe_f1_max) - (1.0 - w) * (delta_c / safe_f2_max)
                density = gain / max(1, chunk.total_effort)

                if (density > best_density) or (density == best_density and gain > best_gain):
                    best_density = density
                    best_gain = gain
                    best_delta_c = delta_c
                    best_cand = (chunk, tm)

        if best_cand is None:
            break

        chosen_chunk, chosen_team = best_cand
        assigned_chunk_ids.add(chosen_chunk.chunk_id)
        team_chunks[chosen_team.team_id].append(chosen_chunk)
        team_rem_cap[chosen_team.team_id] -= chosen_chunk.total_effort

        packing_trace.append({
            "chunk_id": chosen_chunk.chunk_id,
            "team_id": chosen_team.team_id,
            "effort": chosen_chunk.total_effort,
            "utility": round(chosen_chunk.total_utility, 2),
            "delta_c": round(best_delta_c, 3),
            "gain": round(best_gain, 4),
            "density": round(best_density, 5),
            "rem_cap_after": team_rem_cap[chosen_team.team_id],
            "task_ids": [t.id for t in chosen_chunk.tasks],
        })

    unassigned_chunks = [c for c in chunks if c.chunk_id not in assigned_chunk_ids]
    return team_chunks, team_rem_cap, unassigned_chunks, packing_trace
