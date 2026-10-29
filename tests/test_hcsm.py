"""
Unit tests for ProposedHCSMSolver.
Tests:
1. Atomic Coarsening (C_ij = 0) and Capacitated Chunking (E_chunk).
2. Skill filtering and Multi-Cluster Packing.
3. Hard Guardrail backfill mechanism (S > 0).
4. Super-Node Block-Level Open-TSP Bitmask DP.
5. End-to-end ProposedHCSMSolver and Pareto sweep.
"""
import unittest
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import compute_static_bounds
from metrics import compute_context_distance, evaluate_schedule_switch_cost
from solvers.base import BaseSolver
from solvers.proposed_hcsm.coarsening import create_atomic_chunks, TaskChunk
from solvers.proposed_hcsm.packing import pack_chunks_to_teams, compute_chunk_distance
from solvers.proposed_hcsm.backfill import backfill_residual_tasks
from solvers.proposed_hcsm.block_tsp import sequence_team_tasks_block_tsp
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
            # Group 1: repo1, auth, SKILL_A01 (4 tasks, total effort = 12)
            Task(id=1, title="T1", repository="repo1", asset_module="auth", r_i=8.0, e_i=3, skill="SKILL_A01", earliest_sprint=1, deadline_sprint=4),
            Task(id=2, title="T2", repository="repo1", asset_module="auth", r_i=7.0, e_i=3, skill="SKILL_A01", earliest_sprint=2, deadline_sprint=4),
            Task(id=3, title="T3", repository="repo1", asset_module="auth", r_i=6.0, e_i=3, skill="SKILL_A01", earliest_sprint=3, deadline_sprint=4),
            Task(id=4, title="T4", repository="repo1", asset_module="auth", r_i=5.0, e_i=3, skill="SKILL_A01", earliest_sprint=3, deadline_sprint=5),

            # Group 2: repo2, pay, SKILL_A02 (2 tasks, total effort = 6)
            Task(id=5, title="T5", repository="repo2", asset_module="pay", r_i=9.0, e_i=3, skill="SKILL_A02", earliest_sprint=1, deadline_sprint=4),
            Task(id=6, title="T6", repository="repo2", asset_module="pay", r_i=8.0, e_i=3, skill="SKILL_A02", earliest_sprint=2, deadline_sprint=4),

            # Group 3: repo3, db, SKILL_A03 (2 tasks, total effort = 6)
            Task(id=7, title="T7", repository="repo3", asset_module="db", r_i=9.0, e_i=3, skill="SKILL_A03", earliest_sprint=1, deadline_sprint=4),
            Task(id=8, title="T8", repository="repo3", asset_module="db", r_i=6.0, e_i=3, skill="SKILL_A03", earliest_sprint=2, deadline_sprint=4),
        ]

    def test_coarsening_and_chunking(self):
        chunks, max_u = create_atomic_chunks(self.tasks, self.teams, current_sprint=4)
        self.assertGreater(len(chunks), 0)
        self.assertGreater(max_u, 0.0)

        # Context distance inside any chunk is 0.0
        for ch in chunks:
            for t1 in ch.tasks:
                for t2 in ch.tasks:
                    dist = compute_context_distance(t1, t2)
                    self.assertEqual(dist, 0.0)

        # Group 1 has effort 12 > E_chunk (10), must be sliced into at least 2 chunks
        group1_chunks = [ch for ch in chunks if ch.repository == "repo1" and ch.asset_module == "auth"]
        self.assertGreaterEqual(len(group1_chunks), 2)
        total_effort = sum(ch.total_effort for ch in group1_chunks)
        self.assertEqual(total_effort, 12)

    def test_skill_filtering_and_multi_cluster_packing(self):
        chunks, max_u = create_atomic_chunks(self.tasks, self.teams, current_sprint=4)
        bounds = compute_static_bounds(self.tasks, self.teams, current_sprint=4)
        team_chunks, team_rem_cap, unassigned, packing_trace = pack_chunks_to_teams(
            chunks=chunks,
            teams=self.teams,
            w=0.5,
            f1_max=bounds.f1_max,
            f2_max=bounds.f2_max,
            skill_threshold=0.5
        )

        # Team t1 has skill A03 = 0.2 < 0.5 -> must not receive SKILL_A03 chunk
        for ch in team_chunks["t1"]:
            self.assertNotEqual(ch.skill, "SKILL_A03")
            self.assertGreaterEqual(self.teams[0].get_skill_score(ch.skill), 0.5)

        # Team t2 has skill A01 = 0.3 < 0.5 -> must not receive SKILL_A01 chunk
        for ch in team_chunks["t2"]:
            self.assertNotEqual(ch.skill, "SKILL_A01")
            self.assertGreaterEqual(self.teams[1].get_skill_score(ch.skill), 0.5)

        # Capacity never exceeded
        for tm in self.teams:
            self.assertGreaterEqual(team_rem_cap[tm.team_id], 0)
            assigned_effort = sum(ch.total_effort for ch in team_chunks[tm.team_id])
            self.assertLessEqual(assigned_effort, tm.capacity_sp)

    def test_hard_guardrail_backfill(self):
        assigned_tasks = {
            "t1": [self.tasks[0], self.tasks[1]],
            "t2": [self.tasks[4]]
        }
        rem_cap = {"t1": 10, "t2": 10}

        # Low utility, completely unfamiliar repo/mod task
        low_val_task = Task(
            id=99,
            title="Low Value",
            repository="repo_remote",
            asset_module="mod_remote",
            r_i=0.01,
            e_i=5,
            skill="SKILL_A01",
            earliest_sprint=4,
            deadline_sprint=10
        )
        unassigned = [low_val_task]

        # With w = 0.1 (strong focus on switch cost), delta_c = 1.0 causes S < 0
        updated_assigned, updated_rem, rem_unassigned, accepted, blocked = backfill_residual_tasks(
            assigned_tasks_by_team=assigned_tasks,
            unassigned_tasks=unassigned,
            teams=self.teams,
            team_rem_cap=rem_cap,
            w=0.1,
            f1_max=100.0,
            f2_max=10.0,
            current_sprint=4,
            skill_threshold=0.5
        )

        # Hard Guardrail must block this task
        self.assertIn(low_val_task, rem_unassigned)
        self.assertNotIn(low_val_task, updated_assigned["t1"])
        self.assertEqual(updated_rem["t1"], 10)
        self.assertGreaterEqual(len(blocked), 1)

    def test_block_level_open_tsp(self):
        mixed_tasks = [self.tasks[0], self.tasks[4], self.tasks[1], self.tasks[5]]
        ordered, route_info = sequence_team_tasks_block_tsp(mixed_tasks, current_sprint=4)

        # Optimal route groups same-block tasks together: cost must be 1.0
        cost = evaluate_schedule_switch_cost(ordered)
        self.assertEqual(cost, 1.0)
        self.assertEqual(len(ordered), 4)

        first_two = {ordered[0].id, ordered[1].id}
        last_two = {ordered[2].id, ordered[3].id}
        self.assertTrue(
            (first_two == {1, 2} and last_two == {5, 6}) or
            (first_two == {5, 6} and last_two == {1, 2})
        )
        self.assertEqual(route_info["method"], "Bitmask DP (Exact)")

    def test_solver_full_pipeline(self):
        solver = ProposedHCSMSolver(skill_threshold=0.5, default_w=0.5)
        self.assertIsInstance(solver, BaseSolver)

        plan = solver.solve(self.tasks, self.teams, current_sprint=4)
        self.assertGreater(plan.total_utility_resolved, 0.0)
        self.assertGreaterEqual(plan.total_switch_cost, 0.0)
        self.assertIn("phase1", plan.trace_details)

        for sch in plan.schedules:
            tm = next(t for t in self.teams if t.team_id == sch.team_id)
            self.assertLessEqual(sch.total_effort, tm.capacity_sp)

    def test_solve_pareto_and_hypervolume(self):
        solver = ProposedHCSMSolver(skill_threshold=0.5)
        plans, pareto_front, hv = solver.solve_pareto(
            tasks=self.tasks,
            teams=self.teams,
            current_sprint=4,
            n_points=11,
            ref_point=(0.0, 15.0)
        )
        self.assertGreater(len(plans), 0)
        self.assertGreater(len(pareto_front), 0)
        self.assertGreater(hv, 0.0)


if __name__ == "__main__":
    unittest.main()
