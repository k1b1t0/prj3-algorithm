"""
Scorecard and reporting utilities for Plan B: Multi-Sprint Rolling Benchmark.
"""
import csv
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from metrics import compute_wilcoxon_pvalue


def aggregate_rolling_scorecard(
    solver_seed_results: Dict[str, List[Dict[str, Any]]],
    output_path: Path
) -> List[Dict[str, Any]]:
    gls_runs = solver_seed_results.get("Routing GLS", [])
    gls_auc = [r["auc_tve"] for r in gls_runs if r["completed"]]
    hcsm_runs = solver_seed_results.get("Proposed H-CSM", [])
    hcsm_auc = [r["auc_tve"] for r in hcsm_runs if r["completed"]]

    p_val_auc_str = "—"
    if hcsm_auc and gls_auc and len(hcsm_auc) == len(gls_auc):
        p_val = compute_wilcoxon_pvalue(hcsm_auc, gls_auc, alternative="less")
        p_val_auc_str = f"{p_val:.4f}{'*' if p_val < 0.05 else ''}"

    display_order = [
        ("Proposed H-CSM", "Rank 1"),
        ("Routing GLS", "Rank 2 (Baseline)"),
        ("Greedy-CVSS", "Rank 3"),
        ("OR-Tools CP-SAT", "Incomplete (Timeout)")
    ]

    scorecard_rows: List[Dict[str, Any]] = []
    for sol_name, rank_desc in display_order:
        runs = solver_seed_results.get(sol_name, [])
        if not runs:
            continue
        completed = [r for r in runs if r["completed"]]
        if not completed:
            to_sprints = [r["timeout_sprint"] for r in runs if r.get("timeout_sprint")]
            first_to = min(to_sprints) if to_sprints else 1
            row = {
                "Solver": sol_name, "AUC_TVE": f"N/A (Timeout Sprint {first_to})",
                "Total_Breaches": "N/A", "Total_f2": "N/A", "Total_Z_0.5": "N/A",
                "p_value_vs_GLS": "—", "Rank": rank_desc
            }
        else:
            aucs = [r["auc_tve"] for r in completed]
            breaches = [r["total_breaches"] for r in completed]
            f2s = [r["total_f2"] for r in completed]
            zs = [r["total_z"] for r in completed]
            p_val_str = p_val_auc_str if sol_name == "Proposed H-CSM" else ("Baseline" if sol_name == "Routing GLS" else "—")
            row = {
                "Solver": sol_name,
                "AUC_TVE": f"{np.mean(aucs):.1f} +/- {np.std(aucs):.1f}",
                "Total_Breaches": f"{np.mean(breaches):.1f} +/- {np.std(breaches):.1f}",
                "Total_f2": f"{np.mean(f2s):.2f} +/- {np.std(f2s):.2f}",
                "Total_Z_0.5": f"{np.mean(zs):.2f} +/- {np.std(zs):.2f}",
                "p_value_vs_GLS": p_val_str, "Rank": rank_desc
            }
        scorecard_rows.append(row)

    if scorecard_rows:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(scorecard_rows[0].keys()))
            writer.writeheader()
            writer.writerows(scorecard_rows)

    return scorecard_rows


def print_rolling_scorecard(scorecard_rows: List[Dict[str, Any]]):
    print("\n" + "=" * 115)
    print(f"{'PLAN B: FINAL EVALUATION SCORECARD (Mean +/- Std across 5 Independent Seeds)':^115}")
    print("=" * 115)
    print(f"{'Solver':<22} | {'AUC-TVE (v)':<20} | {'Total Breaches':<16} | {'Total f2':<15} | {'Total Z(0.5)':<15} | {'p-val vs GLS':<12} | {'Rank'}")
    print("-" * 115)
    for r in scorecard_rows:
        print(f"{r['Solver']:<22} | {r['AUC_TVE']:<20} | {r['Total_Breaches']:<16} | {r['Total_f2']:<15} | {r['Total_Z_0.5']:<15} | {r['p_value_vs_GLS']:<12} | {r['Rank']}")
    print("=" * 115)
    print("(*) Indicates statistically significant superiority vs Baseline via Wilcoxon Signed-Rank Test (p < 0.05).")

