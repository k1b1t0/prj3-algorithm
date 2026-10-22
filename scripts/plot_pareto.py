"""
Tầng 3: Pareto Frontier & Hypervolume Visualizer (scripts/plot_pareto.py).
Đọc dữ liệu từ outputs/raw_runs.jsonl và xuất biểu đồ Pareto PNG độ phân giải cao:
- Biểu đồ Mặt cong Pareto (f1: Utility vs f2: Switch Cost) kèm vùng tô Hypervolume.
- Điểm đánh dấu đối sánh giữa NSGA-II, Proposed 4-Phase, Greedy-CVSS và CP-SAT Exact.
- Biểu đồ thanh so sánh đa tiêu chí và thời gian thực thi (Runtime ms).
"""
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_raw_runs(jsonl_path: Path) -> List[Dict[str, Any]]:
    runs = []
    if not jsonl_path.exists():
        print(f"[Error] Raw runs file not found: {jsonl_path}")
        return runs
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                runs.append(json.loads(line))
    return runs


def plot_pareto_fronts(raw_runs: List[Dict[str, Any]], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Nhóm runs theo scenario
    scenarios = sorted(list(set(r["scenario"] for r in raw_runs)))

    for sc in scenarios:
        sc_runs = [r for r in raw_runs if r["scenario"] == sc]

        # Lọc các giải thuật
        nsga_runs = [r for r in sc_runs if "nsga" in r["solver"].lower()]
        greedy_runs = [r for r in sc_runs if "greedy" in r["solver"].lower()]
        prop_runs = [r for r in sc_runs if "4phase" in r["solver"].lower() or "proposed" in r["solver"].lower() and "nsga" not in r["solver"].lower()]
        exact_runs = [r for r in sc_runs if "cp-sat" in r["solver"].lower() or "exact" in r["solver"].lower()]

        plt.figure(figsize=(10, 6.5), dpi=300)
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        # 1. Vẽ vùng Hypervolume và đường Pareto của NSGA-II
        if nsga_runs:
            # Lấy pareto_front của lần chạy có Hypervolume cao nhất hoặc instance đầu
            best_nsga = max(nsga_runs, key=lambda r: r.get("hypervolume") or 0.0)
            p_front = best_nsga.get("pareto_front")
            if p_front and len(p_front) > 0:
                p_front_sorted = sorted(p_front, key=lambda p: p[0])
                f1_pts = [p[0] for p in p_front_sorted]
                f2_pts = [p[1] for p in p_front_sorted]

                # Reference point
                ref_y = max(f2_pts) * 1.3 + 2.0
                ref_x = 0.0

                # Tô vùng Hypervolume dạng bậc thang
                hv_x = [ref_x] + f1_pts + [f1_pts[-1], ref_x]
                hv_y = [ref_y] + f2_pts + [ref_y, ref_y]
                plt.fill_between(
                    f1_pts, f2_pts, ref_y,
                    step="post", alpha=0.18, color="#3b82f6",
                    label=f"NSGA-II Hypervolume (HV={best_nsga.get('hypervolume', 0.0):.1f})"
                )

                # Vẽ đường Pareto
                plt.step(
                    f1_pts, f2_pts, where="post", color="#2563eb",
                    linewidth=2.5, linestyle="--", alpha=0.85
                )
                plt.scatter(
                    f1_pts, f2_pts, color="#1d4ed8", s=60, zorder=5,
                    edgecolor="white", linewidth=1.2, label=f"Proposed NSGA-II Front ({len(f1_pts)} solutions)"
                )

        # 2. Vẽ điểm Proposed 4-Phase
        if prop_runs:
            p_f1 = np.mean([r["f1_utility"] for r in prop_runs])
            p_f2 = np.mean([r["f2_switch_cost"] for r in prop_runs])
            plt.scatter(
                [p_f1], [p_f2], color="#10b981", s=180, marker="*",
                zorder=6, edgecolor="#064e3b", linewidth=1.5,
                label=f"Proposed 4-Phase Matheuristic ({p_f1:.1f}, {p_f2:.2f})"
            )
            plt.annotate(
                "Proposed 4-Phase",
                (p_f1, p_f2), textcoords="offset points", xytext=(10, -5),
                fontweight="bold", color="#047857", fontsize=9
            )

        # 3. Vẽ điểm Baseline Greedy-CVSS
        if greedy_runs:
            g_f1 = np.mean([r["f1_utility"] for r in greedy_runs])
            g_f2 = np.mean([r["f2_switch_cost"] for r in greedy_runs])
            plt.scatter(
                [g_f1], [g_f2], color="#ef4444", s=140, marker="X",
                zorder=6, edgecolor="#7f1d1d", linewidth=1.5,
                label=f"Greedy-CVSS Industry Standard ({g_f1:.1f}, {g_f2:.2f})"
            )
            plt.annotate(
                "Greedy-CVSS (Industry)",
                (g_f1, g_f2), textcoords="offset points", xytext=(-120, 10),
                fontweight="bold", color="#b91c1c", fontsize=9
            )

        # 4. Vẽ điểm Exact Baseline (CP-SAT)
        if exact_runs:
            valid_exact = [r for r in exact_runs if r["f1_utility"] > 0]
            if valid_exact:
                e_f1 = np.mean([r["f1_utility"] for r in valid_exact])
                e_f2 = np.mean([r["f2_switch_cost"] for r in valid_exact])
                plt.scatter(
                    [e_f1], [e_f2], color="#8b5cf6", s=150, marker="D",
                    zorder=6, edgecolor="#4c1d95", linewidth=1.5,
                    label=f"OR-Tools CP-SAT Exact ({e_f1:.1f}, {e_f2:.2f})"
                )
                plt.annotate(
                    "CP-SAT Exact",
                    (e_f1, e_f2), textcoords="offset points", xytext=(10, 10),
                    fontweight="bold", color="#6d28d9", fontsize=9
                )

        plt.title(f"Bi-Objective Pareto Frontier — Scenario: {sc.upper()}", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Mitigated Utility (f1) — Higher is Better →", fontsize=11, fontweight="semibold")
        plt.ylabel("Context Switch Cost (f2) — Lower is Better ←", fontsize=11, fontweight="semibold")
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(loc="upper right", frameon=True, framealpha=0.9, facecolor="white")

        plot_path = output_dir / f"pareto_frontier_{sc}.png"
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()
        print(f"[+] Saved Pareto plot: {plot_path}")


def plot_summary_bars(raw_runs: List[Dict[str, Any]], output_dir: Path):
    """Vẽ biểu đồ so sánh chi phí chuyển đổi f2 và thời gian thực thi."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scenarios = sorted(list(set(r["scenario"] for r in raw_runs)))

    for sc in scenarios:
        sc_runs = [r for r in raw_runs if r["scenario"] == sc]
        solvers = sorted(list(set(r["solver"] for r in sc_runs)))

        costs = []
        runtimes = []
        labels = []

        for slv in solvers:
            matching = [r for r in sc_runs if r["solver"] == slv]
            if not matching or all(r["f1_utility"] == 0 for r in matching):
                continue
            labels.append(slv.replace("Proposed-", "").replace("Optimizer", "").strip())
            costs.append(np.mean([r["f2_switch_cost"] for r in matching]))
            runtimes.append(np.mean([r["execution_time_ms"] for r in matching]))

        if not labels:
            continue

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=300)

        # Bar 1: Switch Cost
        colors = ["#ef4444" if "greedy" in l.lower() else "#10b981" if "4phase" in l.lower() else "#3b82f6" for l in labels]
        bars1 = ax1.bar(labels, costs, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
        ax1.set_title(f"Context Switch Cost (f2) — {sc.upper()}", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Switch Cost (Lower is Better)")
        ax1.grid(axis="y", linestyle="--", alpha=0.6)
        for bar in bars1:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.1, f"{h:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

        # Bar 2: Execution Time (Log scale if needed)
        bars2 = ax2.bar(labels, runtimes, color="#6366f1", width=0.55, edgecolor="black", linewidth=0.8)
        ax2.set_title(f"Execution Time (ms) — {sc.upper()}", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Time (ms)")
        ax2.set_yscale("log")
        ax2.grid(axis="y", linestyle="--", alpha=0.6)
        for bar in bars2:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, h * 1.15, f"{h:.1f}ms", ha="center", va="bottom", fontsize=8)

        plt.tight_layout()
        bar_path = output_dir / f"metrics_comparison_{sc}.png"
        plt.savefig(bar_path)
        plt.close()
        print(f"[+] Saved comparison bar plot: {bar_path}")


def main():
    parser = argparse.ArgumentParser(description="Plot Pareto Frontiers and Performance Charts from raw_runs.jsonl")
    parser.add_argument("--input", default="outputs/raw_runs.jsonl", help="Input raw_runs.jsonl file")
    parser.add_argument("--output-dir", default="outputs/pareto_plots", help="Output directory for PNG charts")
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input
    out_dir = PROJECT_ROOT / args.output_dir

    raw_runs = load_raw_runs(input_path)
    if not raw_runs:
        print("[!] No runs found to plot.")
        return

    plot_pareto_fronts(raw_runs, out_dir)
    plot_summary_bars(raw_runs, out_dir)


if __name__ == "__main__":
    main()
