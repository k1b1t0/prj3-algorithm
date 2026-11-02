"""
Bo tong hop va xuat bao cao thuc nghiem boc tach Ablation Study.
Xuat ra 3 dinh dang tai outputs/ablation/:
1. raw_runs.jsonl: Log chi tiet tung luot chay doc lap.
2. ablation_summary.csv: Bang so lieu tong hop Mean +/- Std.
3. ABLATION_REPORT.md: Bao cao Markdown chuan dinh dang de doc hoac dua vao bai bao.
"""
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import numpy as np


def generate_ablation_reports(raw_runs: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    """Tong hop so lieu va xuat toan bo file bao cao tai output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ghi raw_runs.jsonl
    raw_path = output_dir / "raw_runs.jsonl"
    with open(raw_path, "w", encoding="utf-8") as f:
        for r in raw_runs:
            f.write(json.dumps(r) + "\n")

    # 2. Tinh toan Mean +/- Std theo (scenario, variant_name)
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in raw_runs:
        grouped[r["scenario"]][r["variant"]].append(r)

    scenarios = sorted(grouped.keys())
    summary_rows: List[Dict[str, Any]] = []
    variant_order = ["Full H-CSM", "V1", "V2", "V3", "V4", "V5", "V6"]

    for sc in scenarios:
        for v_name in variant_order:
            if v_name not in grouped[sc]:
                continue
            items = grouped[sc][v_name]
            f1_vals = [it["f1_utility"] for it in items]
            f2_vals = [it["f2_switch_cost"] for it in items]
            z_vals = [it["z_w"] for it in items]
            time_vals = [it["execution_time_ms"] for it in items]

            row = {
                "scenario": sc,
                "variant": v_name,
                "instances_count": len(items),
                "f1_mean": round(float(np.mean(f1_vals)), 2),
                "f1_std": round(float(np.std(f1_vals)), 2),
                "f2_mean": round(float(np.mean(f2_vals)), 3),
                "f2_std": round(float(np.std(f2_vals)), 3),
                "z_mean": round(float(np.mean(z_vals)), 4),
                "z_std": round(float(np.std(z_vals)), 4),
                "time_mean_ms": round(float(np.mean(time_vals)), 1),
                "time_std_ms": round(float(np.std(time_vals)), 1),
            }
            summary_rows.append(row)

    # 3. Ghi ablation_summary.csv
    csv_path = output_dir / "ablation_summary.csv"
    if summary_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    # 4. Sinh bao cao Markdown ABLATION_REPORT.md
    md_path = output_dir / "ABLATION_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Báo Cáo Thực Nghiệm Bóc Tách (Ablation Study Report)\n\n")
        f.write("> **Trọng số**: $w = 0.50$ | 10 instances/kịch bản. **Quy ước**: **In đậm** = Hạng 1 (tốt nhất), <u>Gạch chân</u> = Hạng 2.\n\n")

        def rank_format(val: float, val_str: str, u_vals: List[float]) -> str:
            if not u_vals:
                return val_str
            if abs(val - u_vals[0]) < 1e-6:
                return f"**{val_str}**"
            if len(u_vals) > 1 and abs(val - u_vals[1]) < 1e-6:
                return f"<u>{val_str}</u>"
            return val_str

        for sc in scenarios:
            f.write(f"### Kịch Bản: `{sc}`\n\n")
            f.write("| Cấu hình thuật toán | $f_1$ (Lợi ích $\\uparrow$) | $f_2$ (Ngữ cảnh $\\downarrow$) | Điểm $Z(0.50)$ ($\\uparrow$) | Runtime (ms) ($\\downarrow$) |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: |\n")
            sc_rows = [r for r in summary_rows if r["scenario"] == sc]
            if not sc_rows:
                continue

            f1_ranked = sorted(list({r["f1_mean"] for r in sc_rows}), reverse=True)
            f2_ranked = sorted(list({r["f2_mean"] for r in sc_rows}))
            z_ranked = sorted(list({r["z_mean"] for r in sc_rows}), reverse=True)
            t_ranked = sorted(list({r["time_mean_ms"] for r in sc_rows}))

            for r in sc_rows:
                f1_str = rank_format(r["f1_mean"], f"{r['f1_mean']} ± {r['f1_std']}", f1_ranked)
                f2_str = rank_format(r["f2_mean"], f"{r['f2_mean']} ± {r['f2_std']}", f2_ranked)
                z_str = rank_format(r["z_mean"], f"{r['z_mean']} ± {r['z_std']}", z_ranked)
                t_str = rank_format(r["time_mean_ms"], f"{r['time_mean_ms']} ± {r['time_std_ms']}", t_ranked)

                v_label = f"**{r['variant']}**" if r["variant"] == "Full H-CSM" else r["variant"]
                f.write(f"| {v_label} | {f1_str} | {f2_str} | {z_str} | {t_str} |\n")
            f.write("\n---\n\n")

    # In ra man hinh console
    print("\n" + "=" * 115)
    print(f"{'ABLATION STUDY SUMMARY REPORT (w=0.50)':^115}")
    print("=" * 115)
    print(f"{'Scenario':<12} | {'Variant':<34} | {'f1 (Utility)':<15} | {'f2 (Switch)':<16} | {'Z(0.50)':<16} | {'Time (ms)':<14}")
    print("-" * 115)
    for r in summary_rows:
        f1_str = f"{r['f1_mean']} ± {r['f1_std']}"
        f2_str = f"{r['f2_mean']} ± {r['f2_std']}"
        z_str = f"{r['z_mean']} ± {r['z_std']}"
        t_str = f"{r['time_mean_ms']} ± {r['time_std_ms']}"
        print(f"{r['scenario']:<12} | {r['variant']:<34} | {f1_str:<15} | {f2_str:<16} | {z_str:<16} | {t_str:<14}")
    print("=" * 115)

    return summary_rows
