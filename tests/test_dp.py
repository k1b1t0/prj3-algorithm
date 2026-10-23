import unittest
import sys
from pathlib import Path

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task
from solvers.proposed_4phase.dp_sequencing import sequence_tasks_dp
from metrics import check_dag_violations, evaluate_schedule_switch_cost


class TestDPSequencing(unittest.TestCase):
    def test_single_task(self):
        tasks = [
            Task(id=1, title="T1", repository="r1", asset_module="m1", r_i=5.0, e_i=3, skill="SKILL_A01")
        ]
        res = sequence_tasks_dp(tasks)
        self.assertEqual([t.id for t in res], [1])
        self.assertEqual(check_dag_violations(res), 0)

    def test_switch_cost_minimization(self):
        # 4 tasks:
        # Tasks 1 & 3 share module 'm2' and skill 's2' (C_13 = 0.0)
        # Tasks 2 & 4 share module 'm1' and skill 's1' (C_24 = 0.0)
        # Optimal sequence groups {1, 3} together and {2, 4} together to achieve cost = 0.5
        tasks = [
            Task(id=4, title="T4", repository="r1", asset_module="m1", r_i=10.0, e_i=3, skill="SKILL_A01"),
            Task(id=2, title="T2", repository="r1", asset_module="m1", r_i=10.0, e_i=3, skill="SKILL_A01"),
            Task(id=3, title="T3", repository="r1", asset_module="m2", r_i=10.0, e_i=3, skill="SKILL_A02"),
            Task(id=1, title="T1", repository="r1", asset_module="m2", r_i=10.0, e_i=3, skill="SKILL_A02")
        ]
        res = sequence_tasks_dp(tasks)
        self.assertEqual(check_dag_violations(res), 0)
        cost = evaluate_schedule_switch_cost(res)
        # Minimized switch cost must be exactly 0.5 (only 1 context switch between the two modules)
        self.assertEqual(cost, 0.5)
        # Verify clustering: {res[0], res[1]} must be one cluster, {res[2], res[3]} must be the other
        first_group = {res[0].id, res[1].id}
        second_group = {res[2].id, res[3].id}
        self.assertTrue(
            (first_group == {1, 3} and second_group == {2, 4}) or
            (first_group == {2, 4} and second_group == {1, 3})
        )


if __name__ == "__main__":
    unittest.main()
