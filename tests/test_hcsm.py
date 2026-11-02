"""
Unit tests for ProposedHCSMSolver theo kien truc 3 pha H-CSM:
1. Phase 1: Phan cum nguyen tu C_ij = 0 va lap bang 1D Knapsack DP profiling (clustering_dp.py).
2. Phase 2: Phan bo da lua chon tich hop chen duong di re nhat (allocation.py, path_insertion.py).
3. Phase 3: Hoan doi cum lien doi (inter_team_swap.py) va Dinh tuyen Bitmask DP Open-TSP (task_sequencing.py).
4. End-to-end Solver va quet nghiem Pareto (solve_pareto & hypervolume).
5. Kiem tra kha nang ke thua de mo phong Ablation Study (override tung pha).
"""
import unittest
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import compute_static_bounds
from metrics import evaluate_schedule_switch_cost
from solvers.base import BaseSolver
from solvers.proposed_hcsm.clustering_dp import partition_clusters, Cluster
from solvers.proposed_hcsm.allocation import allocate_clusters_to_teams
from solvers.proposed_hcsm.task_sequencing import sequence_team_tasks
from solvers.proposed_hcsm.solver import ProposedHCSMSolver, solve_hcsm


class TestHCSM(unittest.TestCase):
    def setUp(self):
        self.teams = [
            Team(
                team_id="t1",
                name="Team Alpha",
                capacity_sp=20,
                skills={"SKILL_A01": 0.9, "SKILL_A02": 0.8, "SKILL_A03": 0.2}
            ),
            Team(
                team_id="t2",
                name="Team Beta",
                capacity_sp=20,
                skills={"SKILL_A01": 0.3, "SKILL_A02": 0.9, "SKILL_A03": 0.9}
            )
        ]

        self.tasks = [
            # Nhom 1: repo1, auth, SKILL_A01 (4 tasks, tong effort = 12)
            Task(id=1, title="T1", repository="repo1", asset_module="auth", r_i=8.0, e_i=3, skill="SKILL_A01", earliest_sprint=1, deadline_sprint=4),
            Task(id=2, title="T2", repository="repo1", asset_module="auth", r_i=7.0, e_i=3, skill="SKILL_A01", earliest_sprint=2, deadline_sprint=4),
            Task(id=3, title="T3", repository="repo1", asset_module="auth", r_i=6.0, e_i=3, skill="SKILL_A01", earliest_sprint=3, deadline_sprint=4),
            Task(id=4, title="T4", repository="repo1", asset_module="auth", r_i=5.0, e_i=3, skill="SKILL_A01", earliest_sprint=3, deadline_sprint=5),

            # Nhom 2: repo2, pay, SKILL_A02 (2 tasks, tong effort = 6)
            Task(id=5, title="T5", repository="repo2", asset_module="pay", r_i=9.0, e_i=3, skill="SKILL_A02", earliest_sprint=1, deadline_sprint=4),
            Task(id=6, title="T6", repository="repo2", asset_module="pay", r_i=8.0, e_i=3, skill="SKILL_A02", earliest_sprint=2, deadline_sprint=4),

            # Nhom 3: repo3, db, SKILL_A03 (2 tasks, tong effort = 6)
            Task(id=7, title="T7", repository="repo3", asset_module="db", r_i=9.0, e_i=3, skill="SKILL_A03", earliest_sprint=1, deadline_sprint=4),
            Task(id=8, title="T8", repository="repo3", asset_module="db", r_i=6.0, e_i=3, skill="SKILL_A03", earliest_sprint=2, deadline_sprint=4),
        ]

    def test_phase1_clustering_dp_partition(self):
        """Kiem tra Pha 1: Gom cum C_ij = 0 va tinh bang DP."""
        clusters = partition_clusters(self.tasks, max_cap=20, current_sprint=4)
        self.assertEqual(len(clusters), 3)

        c1 = next(c for c in clusters if c.repository == "repo1")
        self.assertEqual(c1.total_effort, 12)
        best_u, subset_6 = c1.get_best_subset(6)
        self.assertEqual(len(subset_6), 2)
        self.assertEqual({t.id for t in subset_6}, {1, 2})

    def test_phase2_cluster_allocation(self):
        """Kiem tra Pha 2: Phan bo da lua chon theo mat do tang dong gop eta."""
        clusters = partition_clusters(self.tasks, max_cap=20, current_sprint=4)
        bounds = compute_static_bounds(self.tasks, self.teams, current_sprint=4)

        team_paths, team_tasks, team_rem_cap = allocate_clusters_to_teams(
            clusters=clusters,
            teams=self.teams,
            w=0.5,
            f1_max=bounds.f1_max,
            f2_max=bounds.f2_max,
            skill_threshold=0.5,
            current_sprint=4
        )

        self.assertFalse(any(t.repository == "repo3" for t in team_tasks["t1"]))
        self.assertGreaterEqual(team_rem_cap["t1"], 0)
        self.assertGreaterEqual(team_rem_cap["t2"], 0)

    def test_phase3_task_sequencing_open_tsp(self):
        """Kiem tra Pha 3: Dinh tuyen Open-TSP bang Bitmask DP."""
        mixed_tasks = [self.tasks[0], self.tasks[4], self.tasks[1], self.tasks[5]]
        ordered = sequence_team_tasks(mixed_tasks, current_sprint=4)

        cost = evaluate_schedule_switch_cost(ordered)
        self.assertEqual(cost, 1.0)
        self.assertEqual(len(ordered), 4)

        first_two = {ordered[0].id, ordered[1].id}
        last_two = {ordered[2].id, ordered[3].id}
        self.assertTrue(
            (first_two == {1, 2} and last_two == {5, 6}) or
            (first_two == {5, 6} and last_two == {1, 2})
        )

    def test_solver_full_pipeline(self):
        """Kiem tra toan bo luong ProposedHCSMSolver."""
        solver = ProposedHCSMSolver(skill_threshold=0.5, default_w=0.5)
        self.assertIsInstance(solver, BaseSolver)

        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertGreater(plan.total_utility_resolved, 0.0)
        self.assertGreaterEqual(plan.total_switch_cost, 0.0)

        for sch in plan.schedules:
            tm = next(t for t in self.teams if t.team_id == sch.team_id)
            self.assertLessEqual(sch.total_effort, tm.capacity_sp)

    def test_solve_hcsm_wrapper_and_sweep_w(self):
        """Kiem tra goi solve_hcsm nhieu lan voi cac gia tri w khac nhau."""
        for w_val in [0.2, 0.5, 1.0]:
            plan = solve_hcsm(self.tasks, self.teams, current_sprint=4, w=w_val)
            self.assertGreater(plan.total_utility_resolved, 0.0)
            self.assertGreaterEqual(plan.total_switch_cost, 0.0)

    def test_ablation_subclass_override(self):
        """Kiem tra viec tao class con ke thua ProposedHCSMSolver de lam ablation study."""
        # Class con bo qua buoc hoan doi lien doi (Pha 3.1)
        class NoSwapSolver(ProposedHCSMSolver):
            def run_phase3_swap(self, team_tasks, teams, skill_thresh):
                return team_tasks  # Khong lam gi ca

        ablation_solver = NoSwapSolver()
        plan = ablation_solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertGreater(plan.total_utility_resolved, 0.0)


if __name__ == "__main__":
    unittest.main()
