"""
Ve do thi Pareto Frontier da muc tieu (Plan A: Static Benchmark).
Bieu dien duong danh doi giua f1 (Loi ich giam thieu) va f2 (Chi phi chuyen doi).
Tinh toan gia tri trung binh kem do lech chuan qua cac trong so w.
"""
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np
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
        sc_runs = [r for r in static_records if r["scenario"] == sc and r.get("status") != "TIMEOUT"]
        if not sc_runs:
            continue
        fig, ax = plt.subplots(figsize=(9.0, 6.0), dpi=300)

        # Gom nhom theo solver va theo weight w
        solver_weight_data: Dict[str, Dict[float, List[Tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
        for r in sc_runs:
            sol = r["solver"]
            w = float(r["weight_w"])
            solver_weight_data[sol][w].append((r["f1_utility"], r["f2_switch_cost"]))

        for solver_name, style in SOLVER_STYLES.items():
            if solver_name not in solver_weight_data:
                continue
            w_dict = solver_weight_data[solver_name]
            weights = sorted(w_dict.keys())
            if not weights:
                continue

            pareto_pts = []
            for w in weights:
                pts = w_dict[w]
                f1_vals = [p[0] for p in pts]
                f2_vals = [p[1] for p in pts]
                m_f1, s_f1 = float(np.mean(f1_vals)), float(np.std(f1_vals))
                m_f2, s_f2 = float(np.mean(f2_vals)), float(np.std(f2_vals))
                pareto_pts.append({
                    "w": w, "m_f1": m_f1, "s_f1": s_f1,
                    "m_f2": m_f2, "s_f2": s_f2, "raw_f1": f1_vals, "raw_f2": f2_vals
                })

            # Sap xep theo f1 tang dan de ve duong bien Pareto chuan
            pareto_pts.sort(key=lambda p: p["m_f1"])
            f1_means = [p["m_f1"] for p in pareto_pts]
            f2_means = [p["m_f2"] for p in pareto_pts]
            f1_errs = [p["s_f1"] for p in pareto_pts]
            f2_errs = [p["s_f2"] for p in pareto_pts]

            # 1. Ve cac diem thuc nghiem thô (translucent raw points)
            for p in pareto_pts:
                ax.scatter(p["raw_f1"], p["raw_f2"], color=style["color"],
                           alpha=0.18, s=28, marker=style["marker"], edgecolors="none")

            # 2. Ve duong noi Pareto Frontier trung binh
            if len(f1_means) > 1 and solver_name != "Greedy-CVSS":
                ax.plot(f1_means, f2_means, color=style["color"], linestyle=style["linestyle"],
                        linewidth=style["linewidth"], alpha=0.9, zorder=style["zorder"])

            # 3. Ve cac diem trung binh kem error bar (Mean +/- Std)
            ax.errorbar(
                f1_means, f2_means, xerr=f1_errs, yerr=f2_errs,
                fmt=style["marker"], color=style["color"], ecolor=style["color"],
                elinewidth=1.2, capsize=3.5, capthick=1.2, markersize=8,
                label=f"{style['label']} (Pareto)", zorder=style["zorder"] + 1, alpha=0.95
            )

            # 4. Chu thich trong so w tren tung diem cua H-CSM
            if solver_name == "Proposed H-CSM":
                for p in pareto_pts:
                    ax.annotate(
                        f"w={p['w']:.2f}", (p["m_f1"], p["m_f2"]),
                        textcoords="offset points", xytext=(8, -6),
                        fontsize=8.5, fontweight="bold", color=style["color"]
                    )

        ax.set_title(f"Pareto Frontier: Security Utility ($f_1$) vs Context Switch Cost ($f_2$)\n[Scenario: {sc} | Mean $\\pm$ Std across Instances]", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("Mitigated Security Utility $f_1$ (Higher is better $\\rightarrow$)", fontsize=10.5, fontweight="semibold")
        ax.set_ylabel("Context Switch Cost $f_2$ (Lower is better $\\leftarrow$)", fontsize=10.5, fontweight="semibold")
        ax.grid(True, linestyle="--", alpha=0.55)
        ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", framealpha=0.95, fontsize=9.0)
        fig.tight_layout()
        fig.savefig(figures_dir / f"pareto_{sc}.png")
        plt.close(fig)
