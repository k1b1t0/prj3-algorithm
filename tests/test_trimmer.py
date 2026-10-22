import unittest
import sys
from pathlib import Path

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task, Team
from proposed.trimmer import trim_cluster_for_team
from metrics import check_dag_violations


class TestTrimmer(unittest.TestCase):
    def setUp(self):
        self.team = Team(
            team_id="t1",
            name="Alpha Team",
            capacity_sp=10,
            skills={"SKILL_A01": 0.9, "SKILL_A02": 0.3}
        )

    def test_skill_filtering(self):
        # Task 1 matches skill (0.9 >= 0.5), Task 2 does not (0.3 < 0.5)
        tasks = [
            Task(id=1, title="T1", repository="r1", asset_module="m1", r_i=8.0, e_i=4, skill="SKILL_A01"),
            Task(id=2, title="T2", repository="r1", asset_module="m1", r_i=9.0, e_i=4, skill="SKILL_A02")
        ]
        retained, deferred = trim_cluster_for_team(tasks, self.team)
        self.assertEqual([t.id for t in retained], [1])
        self.assertEqual([t.id for t in deferred], [2])

    def test_independent_skill_filtering(self):
        # T1 (unskilled: 0.3) is dropped. T2 (skilled: 0.9) is independently retained
        tasks = [
            Task(id=1, title="T1", repository="r1", asset_module="m1", r_i=8.0, e_i=3, skill="SKILL_A02"),
            Task(id=2, title="T2", repository="r1", asset_module="m1", r_i=9.0, e_i=3, skill="SKILL_A01")
        ]
        retained, deferred = trim_cluster_for_team(tasks, self.team)
        self.assertEqual([t.id for t in retained], [2])
        self.assertEqual([t.id for t in deferred], [1])

    def test_leaf_pruning_capacity(self):
        # Total effort: 4 + 4 + 4 = 12 > capacity 10
        # DAG: 1 -> 2 -> 3
        # Task 3 has lowest r/e ratio (1.0 vs 2.0 vs 2.0) and is a leaf (out-degree 0)
        tasks = [
            Task(id=1, title="T1", repository="r1", asset_module="m1", r_i=8.0, e_i=4, skill="SKILL_A01"),
            Task(id=2, title="T2", repository="r1", asset_module="m1", r_i=8.0, e_i=4, skill="SKILL_A01", predecessors=[1]),
            Task(id=3, title="T3", repository="r1", asset_module="m1", r_i=4.0, e_i=4, skill="SKILL_A01", predecessors=[2])
        ]
        retained, deferred = trim_cluster_for_team(tasks, self.team)
        self.assertEqual([t.id for t in retained], [1, 2])
        self.assertEqual([t.id for t in deferred], [3])
        self.assertEqual(sum(t.e_i for t in retained), 8)
        self.assertLessEqual(sum(t.e_i for t in retained), self.team.capacity_sp)
        self.assertEqual(check_dag_violations(retained), 0)


if __name__ == "__main__":
    unittest.main()
