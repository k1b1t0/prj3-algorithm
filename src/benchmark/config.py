"""
Benchmark configurations, scenario parameters, and styling.
"""
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCENARIO_CONFIGS: Dict[str, Dict[str, Any]] = {
    "small_40": {"n_tasks": 40, "n_teams": 2, "time_limit_cpsat": 3.0, "time_limit_gls": 1.0},
    "medium_100": {"n_tasks": 100, "n_teams": 4, "time_limit_cpsat": 10.0, "time_limit_gls": 3.0},
    "large_500": {"n_tasks": 500, "n_teams": 8, "time_limit_cpsat": 15.0, "time_limit_gls": 5.0},
}

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

