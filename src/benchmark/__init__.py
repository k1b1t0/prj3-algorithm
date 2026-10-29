"""
Benchmark Suite Module: Static & Rolling Benchmark Experiments.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

from benchmark.static import run_benchmark_static
from benchmark.rolling import run_benchmark_rolling
from benchmark.plot_rolling import plot_rolling_line_charts
from benchmark.plot_pareto import plot_pareto_fronts_from_data
from benchmark.config import PROJECT_ROOT


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records


def plot_all_benchmarks(figures_dir: Path):
    r_file = PROJECT_ROOT / "outputs" / "rolling" / "rolling_runs.jsonl"
    s_file = PROJECT_ROOT / "outputs" / "static" / "raw_runs.jsonl"
    plot_rolling_line_charts(load_jsonl(r_file), figures_dir)
    plot_pareto_fronts_from_data(load_jsonl(s_file), figures_dir)


__all__ = [
    "run_benchmark_static",
    "run_benchmark_rolling",
    "plot_rolling_line_charts",
    "plot_pareto_fronts_from_data",
    "plot_all_benchmarks"
]

