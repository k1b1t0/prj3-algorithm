from typing import List, Tuple, Set
from ..models import Task, Team


def trim_cluster_for_team(
    cluster_tasks: List[Task],
    team: Team,
    skill_threshold: float = 0.5
) -> Tuple[List[Task], List[Task]]:
    # Lam gon cum cong viec cho team:
    # 1. Loc cung ky nang: Neu diem ky nang < skill_threshold, loai sang deferred
    # 2. Leaf Pruning Heuristic cho PCKP: Neu tong effort > capacity, tia dan cac task la co r_i / e_i thap nhat
    deferred: List[Task] = []
    retained_map = {}

    # Buoc 1: Loc theo nguong ky nang
    for t in cluster_tasks:
        if team.get_skill_score(t.skill) >= skill_threshold:
            retained_map[t.id] = t
        else:
            deferred.append(t)

    # Neu cha bi loai bo vi ky nang ma con van con thi con cung phai bi loai
    # Lap lai cho den khi khong con task con mo coi
    changed = True
    while changed:
        changed = False
        to_remove = []
        for tid, t in retained_map.items():
            for p in t.predecessors:
                # Neu cha co trong cluster goc nhung khong co trong retained_map
                # thi phai loai task con
                if p not in retained_map:
                    # Kiem tra xem cha co tung thuoc ve cluster goc khong
                    if any(orig.id == p for orig in cluster_tasks):
                        to_remove.append(tid)
                        break
        for tid in to_remove:
            deferred.append(retained_map.pop(tid))
            changed = True

    # Buoc 2: Leaf Pruning theo Capacity
    # Trong khi tong effort > capacity_sp, tia bo task la (out-degree == 0 trong tap hien tai)
    while sum(t.e_i for t in retained_map.values()) > team.capacity_sp and retained_map:
        # Xac dinh cac task la: khong co task nao khac trong retained_map coi no la cha
        current_ids = set(retained_map.keys())
        parent_ids: Set[int] = set()
        for t in retained_map.values():
            for p in t.predecessors:
                if p in current_ids:
                    parent_ids.add(p)

        leaf_candidates = [t for tid, t in retained_map.items() if tid not in parent_ids]

        if not leaf_candidates:
            # Phong truong hop do thi co van de bat thuong, lay task bat ky
            leaf_candidates = list(retained_map.values())

        # Chon task la co ty so r_i / e_i thap nhat de tia bo
        # (uu tien giu lai task co han chot deadline_sprint == 1)
        leaf_candidates.sort(key=lambda t: (1 if t.deadline_sprint == 1 else 0, t.r_i / t.e_i))
        victim = leaf_candidates[0]

        deferred.append(retained_map.pop(victim.id))

    return list(retained_map.values()), deferred
