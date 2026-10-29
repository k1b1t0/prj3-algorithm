import unittest
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Task, Team, ScheduleResult, SprintPlan
from bounds import compute_static_bounds, ObjectiveBounds
from metrics import (
    compute_context_distance,
    compute_mitigation_utility,
    evaluate_schedule_switch_cost,
    compute_wilcoxon_pvalue
)


class TestModelsAndMetrics(unittest.TestCase):
    def setUp(self):
        self.team1 = Team(team_id="t1", name="Alpha", capacity_sp=30, skills={"SKILL_A01": 0.9, "SKILL_A02": 0.4})
        self.task1 = Task(id=1, title="SQLi", repository="repo_core", asset_module="auth", r_i=8.0, e_i=3, skill="SKILL_A01", earliest_sprint=1, deadline_sprint=4)
        self.task2 = Task(id=2, title="XSS", repository="repo_core", asset_module="auth", r_i=6.0, e_i=5, skill="SKILL_A01", earliest_sprint=2, deadline_sprint=4)
        self.task3 = Task(id=3, title="CSRF", repository="repo_pay", asset_module="bill", r_i=7.0, e_i=4, skill="SKILL_A02", earliest_sprint=1, deadline_sprint=4)

    def test_context_distance(self):
        # Same repo, same mod, same skill -> 0.0
        d_same = compute_context_distance(self.task1, self.task2)
        self.assertEqual(d_same, 0.0)

        # Diff repo, diff mod, diff skill -> 0.5 + 0.3 + 0.2 = 1.0
        d_diff = compute_context_distance(self.task1, self.task3)
        self.assertEqual(d_diff, 1.0)

    def test_mitigation_utility(self):
        # Current sprint = 4 (at deadline): u = 8.0 + 0.5 * (4 - 1) + 50.0 = 59.5
        u = self.task1.compute_utility(current_sprint=4, alpha=0.5, m_penalty=50.0)
        self.assertEqual(u, 59.5)

        # Current sprint = 2 (before deadline): u = 8.0 + 0.5 * (2 - 1) + 0.0 = 8.5
        u_early = self.task1.compute_utility(current_sprint=2, alpha=0.5, m_penalty=50.0)
        self.assertEqual(u_early, 8.5)

    def test_static_bounds(self):
        tasks = [self.task1, self.task2, self.task3]
        teams = [self.team1]
        bounds = compute_static_bounds(tasks, teams, current_sprint=4)
        self.assertGreater(bounds.f1_max, 0.0)
        self.assertGreater(bounds.f2_max, 0.0)

    def test_wilcoxon_pvalue(self):
        scores_hcsm = [0.40, 0.42, 0.39, 0.41, 0.43]
        scores_gls = [0.35, 0.36, 0.34, 0.35, 0.36]
        p_val = compute_wilcoxon_pvalue(scores_hcsm, scores_gls, alternative="greater")
        self.assertLess(p_val, 0.05)


if __name__ == "__main__":
    unittest.main()

