"""
Script trich xuat va xuat bao cao ket qua benchmark tu log co san.
Doc tu outputs/static/summary_metrics.csv va outputs/rolling/rolling_scorecard.csv.
In scorecard ra terminal va xuat file Markdown dong bo vao outputs va research.
"""
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def load_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def format_static_terminal(rows: List[Dict[str, str]]) -> str:
    lines = []
    lines.append("=" * 125)
    lines.append(f"{'PLAN A: STATIC SNAPSHOT BENCHMARK SCORECARD':^125}")
    lines.append("=" * 125)
    header = f"{'Scenario':<12} | {'Solver':<20} | {'f1 (Utility)':<17} | {'f2 (Switch)':<15} | {'Z(0.50)':<17} | {'Runtime (ms)':<16} | {'Gap / Gain':<18} | {'p-val vs GLS'}"
    lines.append(header)
    lines.append("-" * 125)
    last_sc = None
    for r in rows:
        sc = r["Scenario"]
        if last_sc is not None and sc != last_sc:
            lines.append("-" * 125)
        last_sc = sc
        f1_s = f"{float(r['f1_mean']):.1f} +/- {float(r['f1_std']):.1f}"
        f2_s = f"{float(r['f2_mean']):.2f} +/- {float(r['f2_std']):.2f}"
        z05_s = f"{float(r['Z_0.50_mean']):.3f} +/- {float(r['Z_0.50_std']):.3f}"
        tm_s = f"{float(r['Runtime_ms_mean']):.1f} +/- {float(r['Runtime_ms_std']):.1f}"
        lines.append(f"{sc:<12} | {r['Solver']:<20} | {f1_s:<17} | {f2_s:<15} | {z05_s:<17} | {tm_s:<16} | {r['Gap_Gain_w0.5']:<18} | {r['p_value_vs_GLS']}")
    lines.append("=" * 125)

    lines.append("\n" + "=" * 90)
    lines.append(f"{'PLAN A: MULTI-WEIGHT PARETO SCORECARD (Mean +/- Std)':^90}")
    lines.append("=" * 90)
    lines.append(f"{'Scenario':<12} | {'Solver':<20} | {'Z(w=0.25)':<16} | {'Z(w=0.50)':<16} | {'Z(w=0.75)':<16}")
    lines.append("-" * 90)
    last_sc = None
    for r in rows:
        sc = r["Scenario"]
        if last_sc is not None and sc != last_sc:
            lines.append("-" * 90)
        last_sc = sc
        z25 = f"{float(r['Z_0.25_mean']):.3f} +/- {float(r['Z_0.25_std']):.3f}" if float(r['Z_0.25_mean']) > 0 else "—"
        z50 = f"{float(r['Z_0.50_mean']):.3f} +/- {float(r['Z_0.50_std']):.3f}" if float(r['Z_0.50_mean']) > 0 else "—"
        z75 = f"{float(r['Z_0.75_mean']):.3f} +/- {float(r['Z_0.75_std']):.3f}" if float(r['Z_0.75_mean']) > 0 else "—"
        lines.append(f"{sc:<12} | {r['Solver']:<20} | {z25:<16} | {z50:<16} | {z75:<16}")
    lines.append("=" * 90)
    return "\n".join(lines)


def format_rolling_terminal(rows: List[Dict[str, str]]) -> str:
    lines = []
    lines.append("\n" + "=" * 115)
    lines.append(f"{'PLAN B: MULTI-SPRINT ROLLING BENCHMARK SCORECARD (8 Sprints x 10 Seeds)':^115}")
    lines.append("=" * 115)
    header = f"{'Solver':<22} | {'AUC-TVE (v)':<18} | {'Total Breaches':<18} | {'Total f2':<18} | {'Total Z(0.5)':<15} | {'p-val':<10} | {'Rank'}"
    lines.append(header)
    lines.append("-" * 115)
    for r in rows:
        sol = r["Solver"]
        tve = r.get("AUC_TVE", "—")
        br = r.get("Total_Breaches", "—")
        f2 = r.get("Total_f2", "—")
        z = r.get("Total_Z_0.5", "—")
        pval = r.get("p_value_vs_GLS", "—")
        rank = r.get("Rank", "—")
        lines.append(f"{sol:<22} | {tve:<18} | {br:<18} | {f2:<18} | {z:<15} | {pval:<10} | {rank}")
    lines.append("=" * 115)
    return "\n".join(lines)


def export_markdown_report(static_rows: List[Dict[str, str]], rolling_rows: List[Dict[str, str]], out_md: Path):
    md = []
    md.append("# Báo Cáo Thực Nghiệm Đối Chuẩn Thuật Toán (Automated Benchmark Report)\n")
    md.append("Báo cáo được trích xuất tự động từ log thực nghiệm độc lập trong hệ thống.\n")

    md.append("## 1. Kế Hoạch A: Thực Nghiệm Đơn Sprint (Static Snapshot Benchmark)\n")
    md.append("| Kịch bản | Thuật toán | $f_1$ (Utility $\\uparrow$) | $f_2$ (Switch $\\downarrow$) | $Z(0.50)$ (Chuẩn) | Runtime (ms) | Gap / Gain | $p$-value vs GLS |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in static_rows:
        f1_s = f"{float(r['f1_mean']):.1f} $\\pm$ {float(r['f1_std']):.1f}"
        f2_s = f"{float(r['f2_mean']):.2f} $\\pm$ {float(r['f2_std']):.2f}"
        z05_s = f"{float(r['Z_0.50_mean']):.3f} $\\pm$ {float(r['Z_0.50_std']):.3f}"
        tm_s = f"{float(r['Runtime_ms_mean']):.1f} $\\pm$ {float(r['Runtime_ms_std']):.1f}"
        md.append(f"| **`{r['Scenario']}`** | **{r['Solver']}** | {f1_s} | {f2_s} | **{z05_s}** | {tm_s} | {r['Gap_Gain_w0.5']} | {r['p_value_vs_GLS']} |")

    md.append("\n### Đánh Đổi Đa Trọng Số Pareto ($w \\in \\{0.25, 0.50, 0.75\\}$)\n")
    md.append("| Kịch bản | Thuật toán | $Z(w=0.25)$ (Thấp $f_2$) | $Z(w=0.50)$ (Cân bằng) | $Z(w=0.75)$ (Cao $f_1$) |")
    md.append("| :--- | :--- | :---: | :---: | :---: |")
    for r in static_rows:
        z25 = f"{float(r['Z_0.25_mean']):.3f} $\\pm$ {float(r['Z_0.25_std']):.3f}" if float(r['Z_0.25_mean']) > 0 else "—"
        z50 = f"{float(r['Z_0.50_mean']):.3f} $\\pm$ {float(r['Z_0.50_std']):.3f}" if float(r['Z_0.50_mean']) > 0 else "—"
        z75 = f"{float(r['Z_0.75_mean']):.3f} $\\pm$ {float(r['Z_0.75_std']):.3f}" if float(r['Z_0.75_mean']) > 0 else "—"
        md.append(f"| **`{r['Scenario']}`** | **{r['Solver']}** | {z25} | {z50} | {z75} |")

    md.append("\n## 2. Kế Hoạch B: Thực Nghiệm Chuỗi 8 Sprint Liên Tiếp (Multi-Sprint Rolling Simulation)\n")
    md.append("| Thuật toán | $\\text{AUC-TVE}$ ($\\downarrow$) | $\\text{Total Breaches}$ ($\\downarrow$) | $\\text{Total } f_2$ ($\\downarrow$) | $\\text{Total } Z(0.50)$ ($\\uparrow$) | $p$-value vs GLS | Xếp hạng |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in rolling_rows:
        sol = r["Solver"]
        tve = r.get("AUC_TVE", "—").replace("+/-", "$\\pm$")
        br = r.get("Total_Breaches", "—").replace("+/-", "$\\pm$")
        f2 = r.get("Total_f2", "—").replace("+/-", "$\\pm$")
        z = r.get("Total_Z_0.5", "—").replace("+/-", "$\\pm$")
        pval = r.get("p_value_vs_GLS", "—")
        rank = r.get("Rank", "—")
        md.append(f"| **{sol}** | {tve} | {br} | {f2} | **{z}** | {pval} | **{rank}** |")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"\n[OK] Exported Markdown report to: {out_md}")


def main():
    static_csv = PROJECT_ROOT / "outputs" / "static" / "summary_metrics.csv"
    rolling_csv = PROJECT_ROOT / "outputs" / "rolling" / "rolling_scorecard.csv"
    static_rows = load_csv_rows(static_csv)
    rolling_rows = load_csv_rows(rolling_csv)

    if not static_rows and not rolling_rows:
        print("[!] No benchmark logs found. Run benchmarks first via 'python main.py static' and 'python main.py rolling'.")
        return

    if static_rows:
        print(format_static_terminal(static_rows))
    if rolling_rows:
        print(format_rolling_terminal(rolling_rows))

    # Xuat ra file Markdown tai ca outputs va research
    out_outputs_md = PROJECT_ROOT / "outputs" / "BENCHMARK_REPORT.md"
    export_markdown_report(static_rows, rolling_rows, out_outputs_md)
    out_research_md = PROJECT_ROOT.parent / "research" / "reports" / "prj3" / "benchmark_results.md"
    export_markdown_report(static_rows, rolling_rows, out_research_md)


if __name__ == "__main__":
    main()
