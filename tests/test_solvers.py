import unittest
import sys
from pathlib import Path

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task, Team
from solvers.base import BaseSolver
from solvers.greedy_cvss import GreedyCVSSSolver
from solvers.cpsat_exact import CPSATExactSolver
from solvers.proposed_4phase.solver import Proposed4PhaseSolver
from metrics import compute_mitigation_utility, compute_context_distance, compute_hypervolume, extract_pareto_front


class TestSolvers(unittest.TestCase):
    def setUp(self):
        self.teams = [
            Team(
                team_id="t1",
                name="Team Alpha",
                capacity_sp=15,
                skills={"SKILL_A01": 0.9, "SKILL_A02": 0.8}
            ),
            Team(
                team_id="t2",
                name="Team Beta",
                capacity_sp=15,
                skills={"SKILL_A01": 0.6, "SKILL_A02": 0.9}
            )
        ]
        self.tasks = [
            Task(id=1, title="T1", repository="repo1", asset_module="auth", r_i=8.0, e_i=4, skill="SKILL_A01", earliest_sprint=1, deadline_sprint=4),
            Task(id=2, title="T2", repository="repo1", asset_module="auth", r_i=7.0, e_i=4, skill="SKILL_A01", earliest_sprint=2, deadline_sprint=3, predecessors=[1]),
            Task(id=3, title="T3", repository="repo2", asset_module="pay", r_i=9.0, e_i=5, skill="SKILL_A02", earliest_sprint=1, deadline_sprint=4),
            Task(id=4, title="T4", repository="repo2", asset_module="pay", r_i=6.0, e_i=3, skill="SKILL_A02", earliest_sprint=3, deadline_sprint=5)
        ]

    def test_mitigation_utility_formula(self):
        # tau = 4
        # T1: disc=1, dead=4 -> persistence=3, overdue=1 (tau>=4) -> 8.0 + 0.5*3 + 50.0 = 59.5
        u1 = compute_mitigation_utility(self.tasks[0], current_sprint=4)
        self.assertEqual(u1, 59.5)

        # T4: disc=3, dead=5 -> persistence=1, overdue=0 (4 < 5) -> 6.0 + 0.5*1 + 0 = 6.5
        u4 = compute_mitigation_utility(self.tasks[3], current_sprint=4)
        self.assertEqual(u4, 6.5)

    def test_context_distance_weights(self):
        # T1 (repo1, auth, A01) vs T2 (repo1, auth, A01) -> same -> 0.0
        self.assertEqual(compute_context_distance(self.tasks[0], self.tasks[1]), 0.0)

        # T1 (repo1, auth, A01) vs T3 (repo2, pay, A02) -> diff repo (0.5), diff mod (0.3), diff skill (0.2) -> 1.0
        self.assertEqual(compute_context_distance(self.tasks[0], self.tasks[2]), 1.0)

    def test_greedy_solver(self):
        solver = GreedyCVSSSolver()
        self.assertIsInstance(solver, BaseSolver)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertEqual(plan.dag_violations, 0)
        self.assertGreater(plan.total_utility_resolved, 0.0)

    def test_cpsat_solver(self):
        solver = CPSATExactSolver(time_limit_sec=5.0)
        self.assertIsInstance(solver, BaseSolver)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertEqual(plan.dag_violations, 0)
        self.assertGreater(plan.total_utility_resolved, 0.0)

    def test_proposed_4phase_solver(self):
        solver = Proposed4PhaseSolver()
        self.assertIsInstance(solver, BaseSolver)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertEqual(plan.dag_violations, 0)
        self.assertGreater(plan.total_utility_resolved, 0.0)

    def test_nsga2_solver(self):
        from solvers.proposed_nsga2.solver import ProposedNSGA2Solver
        solver = ProposedNSGA2Solver(pop_size=10, generations=5, random_seed=42)
        self.assertIsInstance(solver, BaseSolver)
        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertEqual(plan.dag_violations, 0)
        self.assertGreater(plan.total_utility_resolved, 0.0)
        self.assertTrue(hasattr(plan, "pareto_front"))
        self.assertTrue(hasattr(plan, "hypervolume"))

    def test_hypervolume(self):
        pts = [(60.0, 3.0), (80.0, 6.0), (95.0, 10.0)]
        front = extract_pareto_front(pts)
        self.assertEqual(len(front), 3)
        hv = compute_hypervolume(front, ref_point=(0.0, 12.0))
        self.assertGreater(hv, 0.0)


if __name__ == "__main__":
    unittest.main()
