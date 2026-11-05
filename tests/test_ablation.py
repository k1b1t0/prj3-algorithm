"""
Unit tests cho 6 bien the cua Ablation Study (V1 - V6).
"""
import unittest
import sys
from pathlib import Path

# Add src and dataset to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataset.benchmark_loader import generate_scenario_instance
from bounds import compute_static_bounds
from solvers.proposed_cas.solver import ProposedCASSolver
from ablation import (
    V1NoClusteringSolver,
    V2NoDPSolver,
    V3NoPathAwareSolver,
    V4NoAmortizationSolver,
    V5NoSwapSolver,
    V6TwoPhaseOnlySolver
)


class TestAblationVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks, cls.teams = generate_scenario_instance("small_40", 40, 2, 1, seed=42)
        cls.bounds = compute_static_bounds(cls.tasks, cls.teams, current_sprint=4)

    def test_all_variants_produce_valid_plans(self):
        solvers = [
            ProposedCASSolver(),
            V1NoClusteringSolver(),
            V2NoDPSolver(),
            V3NoPathAwareSolver(),
            V4NoAmortizationSolver(),
            V5NoSwapSolver(),
            V6TwoPhaseOnlySolver(),
        ]
        for solver in solvers:
            plan = solver.solve(self.tasks, self.teams, current_sprint=4, w=0.5, bounds=self.bounds)
            self.assertIsNotNone(plan, f"{solver.name} returned None")
            self.assertEqual(len(plan.schedules), 2, f"{solver.name} wrong schedule count")
            self.assertGreater(plan.total_utility_resolved, 0.0, f"{solver.name} utility should be > 0")
            self.assertGreaterEqual(plan.total_switch_cost, 0.0, f"{solver.name} switch cost should be >= 0")
            for sched in plan.schedules:
                self.assertLessEqual(sched.total_effort, 30, f"{solver.name} exceeded team capacity")


if __name__ == "__main__":
    unittest.main()

