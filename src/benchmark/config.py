"""
Cau hinh tap trung toan bo tham so he thong va thuc nghiem benchmark.
Moi tham so deu co the dieu chinh linh hoat tai day.
"""
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 1. Tham so dieu khien toan cuc
DEFAULT_NUM_INSTANCES: int = 10
DEFAULT_SCENARIOS: List[str] = ["small_40", "medium_100", "large_500"]
DEFAULT_WEIGHTS: List[float] = [0.25, 0.50, 0.75]
DEFAULT_SOLVERS: List[str] = ["hcsm", "gls", "cpsat", "greedy"]

# 2. Tham so mo phong chuoi nhieu Sprint (Plan B)
DEFAULT_ROLLING_SEEDS: List[int] = [42, 100, 2024, 777, 999, 101, 202, 303, 404, 505]
DEFAULT_NUM_SPRINTS: int = 8
DEFAULT_TASKS_PER_SPRINT: int = 25

# 3. Gioi han thoi gian va cau hinh da luong
DEFAULT_NUM_WORKERS: int = 8
DEFAULT_TIME_LIMIT_CPSAT: float = 60.0

SCENARIO_CONFIGS: Dict[str, Dict[str, Any]] = {
    "small_40": {
        "n_tasks": 40,
        "n_teams": 2,
        "time_limit_cpsat": 60.0,
        "time_limit_gls": 1.0
    },
    "medium_100": {
        "n_tasks": 100,
        "n_teams": 4,
        "time_limit_cpsat": 60.0,
        "time_limit_gls": 3.0
    },
    "large_500": {
        "n_tasks": 500,
        "n_teams": 8,
        "time_limit_cpsat": 60.0,
        "time_limit_gls": 5.0
    },
}

# 4. Dinh dang do hoa publication-ready
SOLVER_STYLES: Dict[str, Dict[str, Any]] = {
    "Proposed H-CSM": {
        "color": "#1d4ed8", "marker": "s", "linestyle": "-", "linewidth": 2.5,
        "label": "Proposed H-CSM", "alpha_fill": 0.15, "zorder": 5
    },
    "Routing GLS": {
        "color": "#059669", "marker": "o", "linestyle": "--", "linewidth": 2.0,
        "label": "Routing GLS (Baseline)", "alpha_fill": 0.12, "zorder": 4
    },
    "Greedy-CVSS": {
        "color": "#dc2626", "marker": "^", "linestyle": "-.", "linewidth": 1.8,
        "label": "Greedy-CVSS", "alpha_fill": 0.10, "zorder": 3
    },
    "OR-Tools CP-SAT": {
        "color": "#7c3aed", "marker": "d", "linestyle": ":", "linewidth": 2.0,
        "label": "OR-Tools CP-SAT (Exact)", "alpha_fill": 0.15, "zorder": 6
    }
}
