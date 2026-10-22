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
    Làm gọn cụm công việc cho team (No-DAG Knapsack Selection):
    1. Lọc cứng kỹ năng: Nếu điểm kỹ năng < skill_threshold, đưa sang deferred.
    2. Greedy Knapsack Selection: Sắp xếp các task đủ điều kiện theo mật độ rủi ro (u_i / e_i)
       giảm dần. Lần lượt nhặt các task có hiệu quả cao nhất vào Sprint cho đến khi chạm trần dung lượng.
    """
    deferred: List[Task] = []
    valid_tasks: List[Task] = []

    # Bước 1: Lọc theo ngưỡng kỹ năng
    for t in cluster_tasks:
        if team.get_skill_score(t.skill) >= skill_threshold:
            valid_tasks.append(t)
        else:
            deferred.append(t)

    # Bước 2: Sắp xếp theo tỷ số utility / effort giảm dần
    valid_tasks.sort(
        key=lambda t: t.compute_utility(current_sprint, alpha, m_penalty) / max(1, t.e_i),
        reverse=True
    )

    retained: List[Task] = []
    current_sp = 0
    for t in valid_tasks:
        if current_sp + t.e_i <= team.capacity_sp:
            retained.append(t)
            current_sp += t.e_i
        else:
            deferred.append(t)

    return retained, deferred
