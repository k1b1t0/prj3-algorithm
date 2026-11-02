"""
Ve do thi Pareto Frontier da muc tieu (Plan A: Static Benchmark).
Bieu dien duong danh doi giua f1 (Loi ich giam thieu) va f2 (Chi phi chuyen doi).
Quet 11 trong so w in [0.0, 1.0] moi buoc 0.1.
- Proposed H-CSM: Duong net lien (11 diem)
- Routing GLS: Duong net dut (11 diem)
- OR-Tools CP-SAT: Duong net cham gach (11 diem)
- Greedy-CVSS: 1 diem don le duy nhat (marker X)
"""
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Bang mau va style chuan cho 4 solvers
SOLVER_PLOT_STYLES = {
    "Proposed H-CSM": {
        "color": "#1d4ed8", "marker": "o", "linestyle": "-", "linewidth": 2.2,
        "label": "Proposed H-CSM", "zorder": 5, "markersize": 7
    },
    "Routing GLS": {
        "color": "#ea580c", "marker": "s", "linestyle": "--", "linewidth": 2.0,
        "label": "OR-Tools Routing (GLS)", "zorder": 4, "markersize": 6
    },
    "OR-Tools CP-SAT": {
        "color": "#7c3aed", "marker": "d", "linestyle": "-.", "linewidth": 2.0,
        "label": "OR-Tools CP-SAT (Exact)", "zorder": 6, "markersize": 7
    },
    "Greedy-CVSS": {
        "color": "#dc2626", "marker": "X", "linestyle": "", "linewidth": 0,
        "label": "Greedy-CVSS (Single point)", "zorder": 7, "markersize": 11
    }
}


def plot_pareto_fronts_from_data(static_records: List[Dict[str, Any]], figures_dir: Path):
    """Ve bieu do Pareto cho tung kich ban tu du lieu raw_runs.jsonl."""
    if not static_records:
        return
    figures_dir.mkdir(parents=True, exist_ok=True)
    scenarios = sorted(list(set(r["scenario"] for r in static_records)))

    for sc in scenarios:
        sc_runs = [r for r in static_records if r["scenario"] == sc and r.get("status") not in ["TIMEOUT", "ERROR", "UNKNOWN"]]
        if not sc_runs:
            continue

        fig, ax = plt.subplots(figsize=(8.5, 6.0), dpi=300)

        # Gom nhom theo solver va theo weight w
        solver_weight_data: Dict[str, Dict[float, List[Tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
        for r in sc_runs:
            sol = r["solver"]
            w = round(float(r["weight_w"]), 2)
            solver_weight_data[sol][w].append((r["f1_utility"], r["f2_switch_cost"]))

        # 1. Ve cac duong Pareto cho 3 thuat toan co quet trong so w
        for solver_name in ["Proposed H-CSM", "Routing GLS", "OR-Tools CP-SAT"]:
            if solver_name not in solver_weight_data:
                continue
            w_dict = solver_weight_data[solver_name]
            weights = sorted(w_dict.keys())
            if not weights:
                continue

            style = SOLVER_PLOT_STYLES[solver_name]
            f1_means, f2_means = [], []

            for w in weights:
                pts = w_dict[w]
                f1_means.append(float(np.mean([p[0] for p in pts])))
                f2_means.append(float(np.mean([p[1] for p in pts])))

            # Noi thang cac diem theo thu tu w tang dan
            ax.plot(
                f1_means, f2_means,
                linestyle=style["linestyle"],
                color=style["color"],
                linewidth=style["linewidth"],
                marker=style["marker"],
                markersize=style["markersize"],
                label=style["label"],
                zorder=style["zorder"],
                alpha=0.95
            )

        # 2. Ve 1 diem don le cho Greedy-CVSS (khong co duong noi vi khong phu thuoc w)
        if "Greedy-CVSS" in solver_weight_data:
            style = SOLVER_PLOT_STYLES["Greedy-CVSS"]
            greedy_pts = []
            for pts in solver_weight_data["Greedy-CVSS"].values():
                greedy_pts.extend(pts)
            if greedy_pts:
                m_f1 = float(np.mean([p[0] for p in greedy_pts]))
                m_f2 = float(np.mean([p[1] for p in greedy_pts]))
                ax.scatter(
                    [m_f1], [m_f2],
                    color=style["color"],
                    marker=style["marker"],
                    s=style["markersize"] ** 2,
                    label=style["label"],
                    zorder=style["zorder"],
                    edgecolors="#7f1d1d",
                    linewidths=1.2
                )

        ax.set_title(f"Bi-Objective Pareto Frontier — Scenario: {sc.upper()}", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Mitigated Utility ($f_1$) — Higher is Better $\\rightarrow$", fontsize=10.5, fontweight="semibold")
        ax.set_ylabel("Context Switch Cost ($f_2$) — Lower is Better $\\leftarrow$", fontsize=10.5, fontweight="semibold")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(frameon=True, facecolor="white", edgecolor="#cbd5e1", framealpha=0.95, fontsize=9.5, loc="best")

        fig.tight_layout()
        out_path = figures_dir / f"pareto_{sc}.png"
        fig.savefig(out_path)
        plt.close(fig)
