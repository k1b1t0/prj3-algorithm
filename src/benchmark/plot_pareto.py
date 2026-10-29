"""
Plotting utilities for Plan A: Static Benchmark Pareto Frontiers.
"""
from pathlib import Path
from typing import Dict, List, Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from benchmark.config import SOLVER_STYLES


def plot_pareto_fronts_from_data(static_records: List[Dict[str, Any]], figures_dir: Path):
    if not static_records:
        return
    figures_dir.mkdir(parents=True, exist_ok=True)
    scenarios = sorted(list(set(r["scenario"] for r in static_records)))

    for sc in scenarios:
        sc_runs = [r for r in static_records if r["scenario"] == sc]
        fig, ax = plt.subplots(figsize=(8.5, 5.8), dpi=300)

        for solver_name, style in SOLVER_STYLES.items():
            matching = [r for r in sc_runs if r["solver"] == solver_name and r.get("status") != "TIMEOUT"]
            if not matching:
                continue
            pts = sorted(list(set((r["f1_utility"], r["f2_switch_cost"]) for r in matching)), key=lambda p: p[0])
            if not pts:
                continue
            f1s, f2s = [p[0] for p in pts], [p[1] for p in pts]
            if len(f1s) > 1 and solver_name in ["Proposed H-CSM", "Routing GLS", "OR-Tools CP-SAT"]:
                ax.step(f1s, f2s, where="post", color=style["color"], linestyle=style["linestyle"],
                        linewidth=style["linewidth"], alpha=0.85)

            ax.scatter(f1s, f2s, label=f"{style['label']} ({len(pts)} pts)", color=style["color"],
                       marker=style["marker"], s=80, edgecolor="white", linewidth=1.2, zorder=style["zorder"])

        ax.set_title(f"Pareto Frontier: Security Utility (f1) vs Switch Cost (f2) [{sc}]", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Mitigated Security Utility f1 (Higher is better)", fontsize=11, fontweight="semibold")
        ax.set_ylabel("Context Switch Cost f2 (Lower is better)", fontsize=11, fontweight="semibold")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(frameon=True, facecolor="white", framealpha=0.9, fontsize=9.5)
        fig.tight_layout()
        fig.savefig(figures_dir / f"pareto_{sc}.png")
        plt.close(fig)

