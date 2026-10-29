"""
Plotting utilities for Plan B: Multi-Sprint Rolling Benchmark Line Charts.
"""
from pathlib import Path
from typing import Dict, List, Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from benchmark.config import SOLVER_STYLES

METRIC_CONFIGS = [
    ("tve", "Total Vulnerability Exposure (TVE)", "TVE Score", "rolling_tve.png"),
    ("breaches", "Active SLA Breaches", "Number of Overdue Tasks", "rolling_breaches.png"),
    ("f2", "Context Switch Cost (f2)", "Switch Cost (Normalized Arcs)", "rolling_switch_cost.png"),
    ("z_w", "Multi-Objective Quality Z(0.50)", "Normalized Utility Score", "rolling_utility_z.png")
]


def _collect_curve(records, solver_name, metric_key, sprints):
    means, stds, valid = [], [], []
    has_timeout = False
    for s in sprints:
        matching = [r[metric_key] for r in records if r["solver"] == solver_name and r["sprint"] == s and r.get("status") == "COMPLETED"]
        if matching:
            valid.append(s)
            means.append(float(np.mean(matching)))
            stds.append(float(np.std(matching)))
        else:
            if any(r["solver"] == solver_name and r["sprint"] == s and r.get("status") == "TIMEOUT" for r in records):
                has_timeout = True
                break
    return np.array(means), np.array(stds), np.array(valid), has_timeout


def plot_rolling_line_charts(records: List[Dict[str, Any]], figures_dir: Path):
    if not records:
        return
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    sprints = sorted(list(set(r["sprint"] for r in records)))

    # 1. Individual figures
    for metric_key, title, ylabel, fname in METRIC_CONFIGS:
        fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)
        for s_name, style in SOLVER_STYLES.items():
            means, stds, valid, to_flag = _collect_curve(records, s_name, metric_key, sprints)
            if len(valid) > 0:
                ax.plot(valid, means, label=style["label"], color=style["color"],
                        linestyle=style["linestyle"], linewidth=style["linewidth"],
                        marker=style["marker"], markersize=6.5, zorder=style["zorder"])
                ax.fill_between(valid, means - stds, means + stds, color=style["color"],
                                alpha=style["alpha_fill"], zorder=style["zorder"] - 1)
                if to_flag:
                    ax.scatter([valid[-1]], [means[-1]], color="#b91c1c", s=130, marker="X", zorder=10)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Sprint Iteration (s)", fontsize=11, fontweight="semibold")
        ax.set_ylabel(ylabel, fontsize=11, fontweight="semibold")
        ax.set_xticks(sprints)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(frameon=True, facecolor="white", framealpha=0.9, fontsize=10)
        fig.tight_layout()
        fig.savefig(figures_dir / fname)
        plt.close(fig)

    # 2. 4-Panel Overview Dashboard
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    for idx, (metric_key, title, ylabel, _) in enumerate(METRIC_CONFIGS):
        ax = axes.flatten()[idx]
        for s_name, style in SOLVER_STYLES.items():
            means, stds, valid, to_flag = _collect_curve(records, s_name, metric_key, sprints)
            if len(valid) > 0:
                ax.plot(valid, means, label=style["label"], color=style["color"],
                        linestyle=style["linestyle"], linewidth=style["linewidth"],
                        marker=style["marker"], markersize=5.5, zorder=style["zorder"])
                ax.fill_between(valid, means - stds, means + stds, color=style["color"], alpha=style["alpha_fill"])
                if to_flag:
                    ax.scatter([valid[-1]], [means[-1]], color="#b91c1c", s=110, marker="X", zorder=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Sprint Iteration", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_xticks(sprints)
        ax.grid(True, linestyle="--", alpha=0.6)
        if idx == 0:
            ax.legend(frameon=True, facecolor="white", framealpha=0.9, fontsize=9)

    fig.suptitle("Plan B: Multi-Sprint Rolling Simulation (8 Sprints x 5 Random Seeds)", fontsize=15, fontweight="bold", y=0.99)
    fig.tight_layout()
    fig.savefig(figures_dir / "rolling_overview_4panel.png")
    plt.close(fig)

