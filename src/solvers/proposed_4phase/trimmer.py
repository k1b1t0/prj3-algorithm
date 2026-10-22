from typing import List, Tuple, Set
from models import Task, Team


def trim_cluster_for_team(
    cluster_tasks: List[Task],
    team: Team,
    skill_threshold: float = 0.5,
    current_sprint: int = 4,
    alpha: float = 0.5,
    m_penalty: float = 50.0
) -> Tuple[List[Task], List[Task]]:
    """
    Làm gọn cụm công việc cho team:
    1. Lọc cứng kỹ năng: Nếu điểm kỹ năng < skill_threshold, loại sang deferred.
    2. Đảm bảo toàn vẹn DAG (cascade): Nếu cha bị loại, con bắt buộc phải loại theo.
    3. Leaf Pruning Heuristic cho PCKP: Nếu tổng effort > capacity_sp, tỉa dần các task lá
       có tỷ số u_i / e_i thấp nhất để đảm bảo 100% không bao giờ vi phạm DAG.
    """
    deferred: List[Task] = []
    retained_map = {}

    # Bước 1: Lọc theo ngưỡng kỹ năng
    for t in cluster_tasks:
        if team.get_skill_score(t.skill) >= skill_threshold:
            retained_map[t.id] = t
        else:
            deferred.append(t)

    # Đảm bảo không có task con mồ côi (nếu cha trong cluster gốc bị loại)
    changed = True
    while changed:
        changed = False
        to_remove = []
        for tid, t in retained_map.items():
            for p in t.predecessors:
                if p not in retained_map:
                    to_remove.append(tid)
                    break
        for tid in to_remove:
            deferred.append(retained_map.pop(tid))
            changed = True

    # Bước 2: Leaf Pruning theo Dung lượng
    while sum(t.e_i for t in retained_map.values()) > team.capacity_sp and retained_map:
        current_ids = set(retained_map.keys())
        parent_ids: Set[int] = set()
        for t in retained_map.values():
            for p in t.predecessors:
                if p in current_ids:
                    parent_ids.add(p)

        leaf_candidates = [t for tid, t in retained_map.items() if tid not in parent_ids]
        if not leaf_candidates:
            leaf_candidates = list(retained_map.values())

        # Sắp xếp các nút lá theo tỷ số utility / effort tăng dần (tỉa task kém hiệu quả nhất)
        # Giữ lại các task đã chạm/quá hạn SLA (u_i sẽ rất cao nhờ M_penalty)
        leaf_candidates.sort(
            key=lambda t: t.compute_utility(current_sprint, alpha, m_penalty) / max(1, t.e_i)
        )
        victim = leaf_candidates[0]
        deferred.append(retained_map.pop(victim.id))

    return list(retained_map.values()), deferred
