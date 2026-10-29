"""
Module tong hop va bao cao chi so cho Plan A: Static Snapshot Benchmark.
Xy ly trung thuc trang thai solver (OPTIMAL vs FEASIBLE vs TIMEOUT).
"""
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from metrics import compute_wilcoxon_pvalue


def aggregate_static_metrics(
    raw_runs: List[Dict[str, Any]],
    scenarios: List[str],
    summary_path: Path
) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], Dict[str, List[Any]]] = defaultdict(lambda: defaultdict(list))
    for r in raw_runs:
        sc, sol, w = r["scenario"], r["solver"], r["weight_w"]
        if r["status"] != "TIMEOUT":
            grouped[(sc, sol)][f"f1_w{w}"].append(r["f1_utility"])
            grouped[(sc, sol)][f"f2_w{w}"].append(r["f2_switch_cost"])
            grouped[(sc, sol)][f"z_w{w}"].append(r["z_w"])
        grouped[(sc, sol)]["time_ms"].append(r["execution_time_ms"])
        grouped[(sc, sol)]["status"].append(r["status"])

    summary_rows: List[Dict[str, Any]] = []
    order = ["OR-Tools CP-SAT", "Proposed H-CSM", "Routing GLS", "Greedy-CVSS"]

    for sc in scenarios:
        cpsat_z05 = grouped.get((sc, "OR-Tools CP-SAT"), {}).get("z_w0.5", [])
        cpsat_mean = float(np.mean(cpsat_z05)) if cpsat_z05 else 0.0
        cpsat_statuses = grouped.get((sc, "OR-Tools CP-SAT"), {}).get("status", [])
        is_cpsat_optimal = bool(cpsat_statuses and all(s == "OPTIMAL" for s in cpsat_statuses))

        gls_z05 = grouped.get((sc, "Routing GLS"), {}).get("z_w0.5", [])
        gls_mean = float(np.mean(gls_z05)) if gls_z05 else 0.0
        hcsm_z05 = grouped.get((sc, "Proposed H-CSM"), {}).get("z_w0.5", [])

        for sol in order:
            if (sc, sol) not in grouped:
                continue
            d = grouped[(sc, sol)]
            f1_v, f2_v = d.get("f1_w0.5", []), d.get("f2_w0.5", [])
            z025_v, z050_v, z075_v = d.get("z_w0.25", []), d.get("z_w0.5", []), d.get("z_w0.75", [])
            tm_v = d.get("time_ms", [])
            sol_statuses = d.get("status", [])

            f1_m, f1_s = (float(np.mean(f1_v)), float(np.std(f1_v))) if f1_v else (0.0, 0.0)
            f2_m, f2_s = (float(np.mean(f2_v)), float(np.std(f2_v))) if f2_v else (0.0, 0.0)
            z025_m, z025_s = (float(np.mean(z025_v)), float(np.std(z025_v))) if z025_v else (0.0, 0.0)
            z050_m, z050_s = (float(np.mean(z050_v)), float(np.std(z050_v))) if z050_v else (0.0, 0.0)
            z075_m, z075_s = (float(np.mean(z075_v)), float(np.std(z075_v))) if z075_v else (0.0, 0.0)
            tm_m, tm_s = (float(np.mean(tm_v)), float(np.std(tm_v))) if tm_v else (0.0, 0.0)

            gap_gain = "—"
            p_val_str = "—"

            if sol == "OR-Tools CP-SAT":
                if not z050_v or all(s == "TIMEOUT" for s in sol_statuses):
                    gap_gain = "N/A (Timeout)"
                elif is_cpsat_optimal:
                    gap_gain, p_val_str = "0.0% (Optimal)", "Gold Standard"
                else:
                    tm_sec = int(round(tm_m / 1000.0))
                    gap_gain, p_val_str = f"Feasible ({tm_sec}s)", "Reference"
            elif sol == "Routing GLS":
                gap_gain, p_val_str = "Baseline (0.0%)", "Baseline"
            elif sc == "small_40" and cpsat_mean > 0 and z050_m > 0:
                if z050_m <= cpsat_mean:
                    gap_gain = f"Gap = {((cpsat_mean - z050_m) / cpsat_mean) * 100.0:.1f}%"
                else:
                    gap_gain = f"+{((z050_m - cpsat_mean) / cpsat_mean) * 100.0:.1f}% vs Incumbent"
            else:
                if gls_mean > 0 and z050_m > 0:
                    gap_gain = f"{((z050_m - gls_mean) / gls_mean) * 100.0:+.1f}% vs GLS"
                elif not z050_v:
                    gap_gain = "N/A (Timeout)"

            if sol == "Proposed H-CSM" and hcsm_z05 and gls_z05:
                p_val = compute_wilcoxon_pvalue(hcsm_z05, gls_z05, alternative="greater")
                p_val_str = f"{p_val:.4f}{'*' if p_val < 0.05 else ''}"

            summary_rows.append({
                "Scenario": sc, "Solver": sol,
                "f1_mean": round(f1_m, 2), "f1_std": round(f1_s, 2),
                "f2_mean": round(f2_m, 2), "f2_std": round(f2_s, 2),
                "Z_0.25_mean": round(z025_m, 4), "Z_0.25_std": round(z025_s, 4),
                "Z_0.50_mean": round(z050_m, 4), "Z_0.50_std": round(z050_s, 4),
                "Z_0.75_mean": round(z075_m, 4), "Z_0.75_std": round(z075_s, 4),
                "Runtime_ms_mean": round(tm_m, 1), "Runtime_ms_std": round(tm_s, 1),
                "Gap_Gain_w0.5": gap_gain, "p_value_vs_GLS": p_val_str
            })

    if summary_rows:
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
    return summary_rows


def print_static_summary_table(summary_rows: List[Dict[str, Any]]):
    print("\n" + "=" * 125)
    print(f"{'PLAN A: SUMMARY SCORECARD (Mean +/- Std across Independent Instances)':^125}")
    print("=" * 125)
    print(f"{'Scenario':<12} | {'Solver':<20} | {'f1 (Utility)':<17} | {'f2 (Switch)':<15} | {'Z(0.50)':<17} | {'Runtime (ms)':<16} | {'Gap / Gain':<18} | {'p-val vs GLS'}")
    print("-" * 125)
    last_sc = None
    for r in summary_rows:
        if last_sc is not None and r["Scenario"] != last_sc:
            print("-" * 125)
        last_sc = r["Scenario"]
        f1_str = f"{r['f1_mean']:.1f} +/- {r['f1_std']:.1f}"
        f2_str = f"{r['f2_mean']:.2f} +/- {r['f2_std']:.2f}"
        z05_str = f"{r['Z_0.50_mean']:.3f} +/- {r['Z_0.50_std']:.3f}"
        tm_str = f"{r['Runtime_ms_mean']:.1f} +/- {r['Runtime_ms_std']:.1f}"
        print(f"{r['Scenario']:<12} | {r['Solver']:<20} | {f1_str:<17} | {f2_str:<15} | {z05_str:<17} | {tm_str:<16} | {r['Gap_Gain_w0.5']:<18} | {r['p_value_vs_GLS']}")
    print("=" * 125)
    print("(*) Indicates statistically significant superiority vs Baseline via Wilcoxon Signed-Rank Test (p < 0.05).")
