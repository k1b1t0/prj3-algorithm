"""
Pha 1: Pure Atomic Coarsening va Capacitated Chunking.
- 1A: Gom cac task cung (repo, asset_module, skill) -> C_ij = 0 tuyet doi.
  Sap xep task theo mat do loi ich rho_i = u_i / e_i giam dan.
- 1B: Chia nho cum neu tong effort > E_chunk = 0.5 * min(cap_m).
  Tao ra K cum nho vua van dung luong (K > M).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from models import Task, Team


@dataclass
class TaskChunk:
    """Dai dien cho mot micro-cluster / chunk gom cac task dong nhat ngu canh."""
    chunk_id: int
    repository: str
    asset_module: str
    skill: str
    tasks: List[Task] = field(default_factory=list)
    total_effort: int = 0
    total_utility: float = 0.0
    normalized_utility: float = 0.0


def create_atomic_chunks(
    tasks: List[Task],
    teams: List[Team],
    current_sprint: int = 4,
    alpha: float = 0.5,
    m_penalty: float = 50.0
) -> Tuple[List[TaskChunk], float]:
    """
    Pha 1A & 1B: Gom cum nguyen tu va phan manh dung luong E_chunk.
    Tra ve danh sach cac TaskChunk va max_u de chuan hoa.
    """
    if not tasks:
        return [], 1.0

    # Tinh utility cho tung task va tim max_u
    task_utilities: Dict[int, float] = {}
    max_u = 0.0
    for t in tasks:
        u = t.compute_utility(current_sprint=current_sprint, alpha=alpha, m_penalty=m_penalty)
        task_utilities[t.id] = u
        if u > max_u:
            max_u = u

    if max_u <= 0.0:
        max_u = 1.0

    # Pha 1A: Gom cum nguyen tu cung (repo, asset_module, skill)
    groups: Dict[Tuple[str, str, str], List[Task]] = {}
    for t in tasks:
        key = (t.repository, t.asset_module, t.skill)
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    # Sap xep task trong moi cum nguyen tu theo rho_i = u_i / e_i giam dan
    for key in groups:
        groups[key].sort(
            key=lambda t: (task_utilities[t.id] / max(1, t.e_i), task_utilities[t.id]),
            reverse=True
        )

    # Pha 1B: Capacitated Chunking theo E_chunk = 0.5 * min(cap_m)
    min_cap = min(tm.capacity_sp for tm in teams) if teams else 30
    e_chunk = max(1, int(round(0.5 * min_cap)))

    chunks: List[TaskChunk] = []
    chunk_counter = 0

    for (repo, mod, skill), group_tasks in groups.items():
        total_group_effort = sum(t.e_i for t in group_tasks)

        if total_group_effort <= e_chunk:
            # Cum nho: giu nguyen 1 chunk doc lap
            c_util = sum(task_utilities[t.id] for t in group_tasks)
            norm_util = sum(task_utilities[t.id] / max_u for t in group_tasks)
            chunks.append(TaskChunk(
                chunk_id=chunk_counter,
                repository=repo,
                asset_module=mod,
                skill=skill,
                tasks=list(group_tasks),
                total_effort=total_group_effort,
                total_utility=round(c_util, 4),
                normalized_utility=round(norm_util, 6)
            ))
            chunk_counter += 1
        else:
            # Cum to: phan manh thanh cac chunk vua van ~ E_chunk
            curr_chunk_tasks: List[Task] = []
            curr_chunk_effort = 0

            for t in group_tasks:
                # Neu them t lam vuot e_chunk va chunk da co it nhat 1 task -> dong chunk
                if curr_chunk_tasks and (curr_chunk_effort + t.e_i > e_chunk):
                    c_util = sum(task_utilities[item.id] for item in curr_chunk_tasks)
                    norm_util = sum(task_utilities[item.id] / max_u for item in curr_chunk_tasks)
                    chunks.append(TaskChunk(
                        chunk_id=chunk_counter,
                        repository=repo,
                        asset_module=mod,
                        skill=skill,
                        tasks=list(curr_chunk_tasks),
                        total_effort=curr_chunk_effort,
                        total_utility=round(c_util, 4),
                        normalized_utility=round(norm_util, 6)
                    ))
                    chunk_counter += 1
                    curr_chunk_tasks = [t]
                    curr_chunk_effort = t.e_i
                else:
                    curr_chunk_tasks.append(t)
                    curr_chunk_effort += t.e_i

            if curr_chunk_tasks:
                c_util = sum(task_utilities[item.id] for item in curr_chunk_tasks)
                norm_util = sum(task_utilities[item.id] / max_u for item in curr_chunk_tasks)
                chunks.append(TaskChunk(
                    chunk_id=chunk_counter,
                    repository=repo,
                    asset_module=mod,
                    skill=skill,
                    tasks=list(curr_chunk_tasks),
                    total_effort=curr_chunk_effort,
                    total_utility=round(c_util, 4),
                    normalized_utility=round(norm_util, 6)
                ))
                chunk_counter += 1

    return chunks, max_u
