import unittest
import sys
from pathlib import Path

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task
from proposed.dp_sequencing import sequence_tasks_dp
from metrics import check_dag_violations, evaluate_schedule_switch_cost


class TestDPSequencing(unittest.TestCase):
    def test_single_task(self):
        tasks = [
            Task(id=1, title="T1", repository="r1", asset_module="m1", r_i=5.0, e_i=3, skill="SKILL_A01")
        ]
        res = sequence_tasks_dp(tasks)
        self.assertEqual([t.id for t in res], [1])
        self.assertEqual(check_dag_violations(res), 0)

    def test_linear_dag_precedence(self):
        # 1 -> 2 -> 3
        tasks = [
            Task(id=3, title="T3", repository="r1", asset_module="m1", r_i=5.0, e_i=3, skill="SKILL_A01", predecessors=[2]),
            Task(id=1, title="T1", repository="r1", asset_module="m1", r_i=5.0, e_i=3, skill="SKILL_A01"),
            Task(id=2, title="T2", repository="r1", asset_module="m1", r_i=5.0, e_i=3, skill="SKILL_A01", predecessors=[1])
        ]
        res = sequence_tasks_dp(tasks)
        self.assertEqual([t.id for t in res], [1, 2, 3])
        self.assertEqual(check_dag_violations(res), 0)

    def test_diamond_dag_switch_cost_optimization(self):
        # DAG: 1 -> 2, 1 -> 3, 2 -> 4, 3 -> 4
        # Tasks 1 & 3 share module 'm2' and skill 's2' (C_13 = 0.0)
        # Tasks 2 & 4 share module 'm1' and skill 's1' (C_24 = 0.0)
        # Optimal sequence groups 1, 3 then 2, 4 (or 1, then branches) to minimize C_ij
        tasks = [
            Task(id=4, title="T4", repository="r1", asset_module="m1", r_i=10.0, e_i=3, skill="SKILL_A01", predecessors=[2, 3]),
            Task(id=2, title="T2", repository="r1", asset_module="m1", r_i=10.0, e_i=3, skill="SKILL_A01", predecessors=[1]),
            Task(id=3, title="T3", repository="r1", asset_module="m2", r_i=10.0, e_i=3, skill="SKILL_A02", predecessors=[1]),
            Task(id=1, title="T1", repository="r1", asset_module="m2", r_i=10.0, e_i=3, skill="SKILL_A02")
        ]
        res = sequence_tasks_dp(tasks)
        self.assertEqual(check_dag_violations(res), 0)
        cost = evaluate_schedule_switch_cost(res)
        # Optimal order is [1, 3, 2, 4]: cost = C(1,3)=0.0 + C(3,2)=1.0 + C(2,4)=0.0 = 1.0
        self.assertEqual(cost, 1.0)
        self.assertEqual([t.id for t in res], [1, 3, 2, 4])


if __name__ == "__main__":
    unittest.main()
