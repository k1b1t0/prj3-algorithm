"""
Benchmark Visualizer CLI Shim.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark import plot_all_benchmarks
from benchmark.config import PROJECT_ROOT

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Publication Figures")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "figures"))
    args = parser.parse_args()
    plot_all_benchmarks(Path(args.output_dir))
