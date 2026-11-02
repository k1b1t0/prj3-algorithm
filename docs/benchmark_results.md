# Báo Cáo Thực Nghiệm Đối Chuẩn Thuật Toán (Automated Benchmark Report)

Báo cáo được trích xuất tự động từ log thực nghiệm độc lập trong hệ thống.

## 1. Kế Hoạch A: Thực Nghiệm Đơn Sprint (Static Snapshot Benchmark)

| Kịch bản | Thuật toán | $f_1$ (Utility $\uparrow$) | $f_2$ (Switch $\downarrow$) | $Z(0.50)$ (Chuẩn) | Runtime (ms) | Gap / Gain | $p$-value vs GLS |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`small_40`** | **OR-Tools CP-SAT** | 10.5 $\pm$ 2.4 | 2.21 $\pm$ 0.59 | **0.431 $\pm$ 0.017** | 60227.2 $\pm$ 235.3 | Feasible (60s) | Reference |
| **`small_40`** | **Proposed H-CSM** | 10.5 $\pm$ 2.4 | 2.33 $\pm$ 0.54 | **0.427 $\pm$ 0.013** | 28.2 $\pm$ 64.9 | Gap = 1.0% | 0.0010* |
| **`small_40`** | **Routing GLS** | 8.8 $\pm$ 2.7 | 1.80 $\pm$ 0.61 | **0.356 $\pm$ 0.040** | 1004.0 $\pm$ 1.9 | Baseline (0.0%) | Baseline |
| **`small_40`** | **Greedy-CVSS** | 10.9 $\pm$ 2.5 | 6.55 $\pm$ 1.83 | **0.353 $\pm$ 0.044** | 0.7 $\pm$ 0.4 | Gap = 18.1% | 0.5566 (p>=0.05) |
| **`medium_100`** | **OR-Tools CP-SAT** | 0.0 $\pm$ 0.0 | 0.00 $\pm$ 0.00 | **0.000 $\pm$ 0.000** | 60000.0 $\pm$ 0.0 | N/A (Timeout) | — |
| **`medium_100`** | **Proposed H-CSM** | 23.8 $\pm$ 5.2 | 3.60 $\pm$ 1.03 | **0.441 $\pm$ 0.013** | 215.6 $\pm$ 400.7 | +22.1% vs GLS | 0.0020* |
| **`medium_100`** | **Routing GLS** | 19.9 $\pm$ 6.1 | 2.97 $\pm$ 1.04 | **0.361 $\pm$ 0.049** | 3012.6 $\pm$ 2.7 | Baseline (0.0%) | Baseline |
| **`medium_100`** | **Greedy-CVSS** | 24.8 $\pm$ 5.6 | 11.57 $\pm$ 2.89 | **0.376 $\pm$ 0.031** | 1.3 $\pm$ 0.3 | +4.0% vs GLS | 0.7695 (p>=0.05) |
| **`large_500`** | **OR-Tools CP-SAT** | 0.0 $\pm$ 0.0 | 0.00 $\pm$ 0.00 | **0.000 $\pm$ 0.000** | 60000.0 $\pm$ 0.0 | N/A (Timeout) | — |
| **`large_500`** | **Proposed H-CSM** | 65.0 $\pm$ 6.1 | 6.76 $\pm$ 1.14 | **0.459 $\pm$ 0.009** | 749.2 $\pm$ 705.0 | +22.5% vs GLS | 0.0010* |
| **`large_500`** | **Routing GLS** | 53.5 $\pm$ 5.8 | 6.38 $\pm$ 1.61 | **0.374 $\pm$ 0.027** | 5221.4 $\pm$ 76.7 | Baseline (0.0%) | Baseline |
| **`large_500`** | **Greedy-CVSS** | 66.8 $\pm$ 6.2 | 27.46 $\pm$ 5.19 | **0.388 $\pm$ 0.021** | 6.4 $\pm$ 2.1 | +3.7% vs GLS | 0.4922 (p>=0.05) |

### Đánh Đổi Đa Trọng Số Pareto ($w \in \{0.25, 0.50, 0.75\}$)

| Kịch bản | Thuật toán | $Z(w=0.25)$ (Thấp $f_2$) | $Z(w=0.50)$ (Cân bằng) | $Z(w=0.75)$ (Cao $f_1$) |
| :--- | :--- | :---: | :---: | :---: |
| **`small_40`** | **OR-Tools CP-SAT** | 0.182 $\pm$ 0.016 | 0.431 $\pm$ 0.017 | 0.710 $\pm$ 0.010 |
| **`small_40`** | **Proposed H-CSM** | 0.171 $\pm$ 0.018 | 0.427 $\pm$ 0.013 | 0.703 $\pm$ 0.013 |
| **`small_40`** | **Routing GLS** | 0.153 $\pm$ 0.023 | 0.356 $\pm$ 0.040 | 0.552 $\pm$ 0.075 |
| **`small_40`** | **Greedy-CVSS** | 0.032 $\pm$ 0.064 | 0.353 $\pm$ 0.044 | 0.674 $\pm$ 0.025 |
| **`medium_100`** | **OR-Tools CP-SAT** | — | — | — |
| **`medium_100`** | **Proposed H-CSM** | 0.192 $\pm$ 0.013 | 0.441 $\pm$ 0.013 | 0.713 $\pm$ 0.007 |
| **`medium_100`** | **Routing GLS** | 0.163 $\pm$ 0.025 | 0.361 $\pm$ 0.049 | 0.561 $\pm$ 0.073 |
| **`medium_100`** | **Greedy-CVSS** | 0.066 $\pm$ 0.046 | 0.376 $\pm$ 0.031 | 0.685 $\pm$ 0.016 |
| **`large_500`** | **OR-Tools CP-SAT** | — | — | — |
| **`large_500`** | **Proposed H-CSM** | 0.204 $\pm$ 0.008 | 0.459 $\pm$ 0.009 | 0.724 $\pm$ 0.006 |
| **`large_500`** | **Routing GLS** | 0.155 $\pm$ 0.021 | 0.374 $\pm$ 0.027 | 0.583 $\pm$ 0.039 |
| **`large_500`** | **Greedy-CVSS** | 0.083 $\pm$ 0.032 | 0.388 $\pm$ 0.021 | 0.694 $\pm$ 0.010 |

## 2. Kế Hoạch B: Thực Nghiệm Chuỗi 8 Sprint Liên Tiếp (Multi-Sprint Rolling Simulation)

| Thuật toán | $\text{AUC-TVE}$ ($\downarrow$) | $\text{Total Breaches}$ ($\downarrow$) | $\text{Total } f_2$ ($\downarrow$) | $\text{Total } Z(0.50)$ ($\uparrow$) | $p$-value vs GLS | Xếp hạng |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Proposed H-CSM** | 61.9 $\pm$ 8.1 | 49.5 $\pm$ 5.2 | 24.81 $\pm$ 2.46 | **3.11 $\pm$ 0.05** | 0.0010* | **Rank 1** |
| **Routing GLS** | 69.6 $\pm$ 10.5 | 51.9 $\pm$ 5.6 | 24.05 $\pm$ 3.12 | **2.93 $\pm$ 0.06** | Baseline | **Rank 2 (Baseline)** |
| **Greedy-CVSS** | 54.3 $\pm$ 8.5 | 46.3 $\pm$ 5.6 | 73.70 $\pm$ 5.66 | **2.07 $\pm$ 0.14** | 0.0010* (GLS wins) | **Rank 3** |
| **OR-Tools CP-SAT** | N/A (Timeout Sprint 1) | N/A | N/A | **N/A** | — | **Incomplete (Timeout)** |
