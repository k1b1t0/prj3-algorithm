"""
Unit tests for Baseline solvers:
1. GreedyCVSSSolver
2. CPSATExactSolver
3. ORToolsRoutingSolver
"""
import unittest
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task, Team
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.cpsat_exact import CPSATExactSolver
from solvers.ortools_routing import ORToolsRoutingSolver


class TestBaselines(unittest.TestCase):
    def setUp(self):
        self.teams = [
            Team(team_id="t1", name="Alpha", capacity_sp=20, skills={"SKILL_A01": 0.9, "SKILL_A02": 0.3}),
            Team(team_id="t2", name="Beta", capacity_sp=20, skills={"SKILL_A01": 0.3, "SKILL_A02": 0.9})
        ]

        self.tasks = [
            Task(id=1, title="T1", repository="repo1", asset_module="auth", r_i=8.0, e_i=5, skill="SKILL_A01", earliest_sprint=1, deadline_sprint=4),
            Task(id=2, title="T2", repository="repo1", asset_module="auth", r_i=7.0, e_i=5, skill="SKILL_A01", earliest_sprint=2, deadline_sprint=4),
            Task(id=3, title="T3", repository="repo2", asset_module="pay", r_i=9.0, e_i=5, skill="SKILL_A02", earliest_sprint=1, deadline_sprint=4),
            Task(id=4, title="T4", repository="repo2", asset_module="pay", r_i=6.0, e_i=5, skill="SKILL_A02", earliest_sprint=2, deadline_sprint=4),
        ]

    def test_greedy_solver(self):
        solver = GreedyCVSSSolver(skill_threshold=0.5)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertGreater(plan.total_utility_resolved, 0.0)
        self.assertLessEqual(sum(s.total_effort for s in plan.schedules), 40)

    def test_cpsat_solver(self):
        solver = CPSATExactSolver(time_limit_sec=5.0, skill_threshold=0.5)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4, w=0.5)
        self.assertGreater(plan.total_utility_resolved, 0.0)
        self.assertLessEqual(sum(s.total_effort for s in plan.schedules), 40)

    def test_routing_solver(self):
        solver = ORToolsRoutingSolver(time_limit_sec=3.0, skill_threshold=0.5)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4, w=0.5)
        self.assertGreater(plan.total_utility_resolved, 0.0)
        self.assertLessEqual(sum(s.total_effort for s in plan.schedules), 40)


if __name__ == "__main__":
    unittest.main()

