# Kế Hoạch Triển Khai & Tái Cấu Trúc Toàn Diện (Implementation Plan)
## Dự Án: `prj3-algo-no-dag`

Tài liệu này quy định chi tiết toàn bộ kiến trúc mã nguồn, quy chuẩn refactor, hệ thống log chi tiết và lộ trình triển khai thuật toán đề xuất **H-CSM** cùng các baselines đối chuẩn theo kế hoạch nghiên cứu đã chốt.

---

## 1. Mục Tiêu & Nguyên Tắc Tái Cấu Trúc Toàn Bộ (Refactoring Scope)

### 1.1. Các Nguyên Tắc Bắt Buộc (Strict Coding Standards)
1. **Thông điệp & Log (Messages & Logs)**: 100% bằng **Tiếng Anh (English)**. In ấn tối giản, ngắn gọn, chuẩn format, không spam terminal.
2. **Chú thích mã nguồn (Comments)**: Tối giản, chỉ chú thích tại các đoạn thuật toán phức tạp, sử dụng **Tiếng Việt không dấu** (hoặc Tiếng Anh).
3. **Bảo toàn dữ liệu (FROZEN Dataset)**: Tuyệt đối không can thiệp, không sửa đổi dữ liệu gốc trong `dataset/*`.
4. **Không làm chậm thuật toán (Zero-Overhead Logging)**: Hệ thống log chi tiết từng pha (phase logging) được điều khiển qua cờ `verbose: bool = False`, tách biệt hoàn toàn khỏi logic tính toán cốt lõi.

### 1.2. Danh Sách Các File Cũ Bị Xóa Bỏ Hoàn Toàn (Dead Code Removal)
Xóa bỏ các file trùng lặp, file nháp thử nghiệm và các thuật toán không còn sử dụng:
* **Thư mục trùng lặp**:
  - `src/proposed/` (toàn bộ thư mục — bị thay thế hoàn toàn bởi `src/solvers/proposed_hcsm/`).
  - `src/baselines/` (toàn bộ thư mục — bị thay thế bởi `src/solvers/`).
* **Thuật toán cũ không dùng**:
  - `src/solvers/proposed_4phase/` (thuật toán 4 pha bản cũ dùng greedy trimmer).
  - `src/solvers/proposed_nsga2/` (thuật toán di truyền cũ).
* **Các file script solo / tạm bợ trong `scripts/`**:
  - `scripts/benchmark_normalization.py`
  - `scripts/run_greedy_solo.py`
  - `scripts/solo_hcsm_vs_cpsat.py`
  - `scripts/solo_with_ortools_heuristic.py`
  - `scripts/test_ortools_routing.py`
  - `scripts/run_exact.py`
  - `scripts/run_proposed.py`
  - `scripts/run_benchmark.py`
  - `scripts/generate_visualizer.py`
  - `scripts/render_dashboard.py`

### 1.3. Cấu Trúc Thư Mục Mới Sau Khi Refactor
```text
prj3-algo-no-dag/
├── dataset/
│   ├── benchmark/                # 15 file JSON instances chuan (small, medium, large)
│   ├── benchmark_loader.py       # Loader du lieu benchmark chuan
│   └── generator.py              # Tool trich xuat du lieu tu raw
├── src/
│   ├── models.py                 # Task, Team, ScheduleResult, SprintPlan (chuan disc_i, dead_i)
│   ├── bounds.py                 # compute_static_bounds (f1_max, f2_max chuan toan hoc)
│   ├── metrics.py                # compute_context_distance, compute_utility, evaluate_plan, wilcoxon
│   └── solvers/
│       ├── __init__.py
│       ├── base.py               # Abstract BaseSolver
│       ├── greedy_cvss.py        # Baseline 1: Greedy-CVSS
│       ├── cpsat_exact.py        # Baseline 2: OR-Tools CP-SAT MO-MILP with MTZ
│       ├── ortools_routing.py    # Baseline 3: OR-Tools Routing GLS (rename & clean)
│       └── proposed_hcsm/        # Thuat toan de xuat H-CSM (4 Pha Chuan)
│           ├── __init__.py
│           ├── coarsening.py     # Pha 1: Atomic coarsening & chunking E_chunk = 15 SP
│           ├── packing.py        # Pha 2: Multi-cluster packing voi Delta Z(w) / Effort
│           ├── backfill.py       # Pha 3: Residual backfill & Hard Guardrail S(i, m, w) > 0
│           ├── block_tsp.py      # Pha 4: Super-node Bitmask DP (B <= 12) + Nearest Neighbor
│           └── solver.py         # Solver tong hop voi co che PhaseLogger
├── scripts/
│   ├── run_benchmark_static.py   # Ke hoach A: 5 instances x 3 scenarios x 3 weights (w=0.25, 0.5, 0.75)
│   ├── run_benchmark_rolling.py  # Ke hoach B: Mo phong 8 Sprints x 5 seeds x 4 solvers
│   └── plot_benchmarks.py        # Xuat do thi: 4 Line Charts (Ke hoach B) & Pareto Fronts (Ke hoach A)
├── outputs/
│   ├── static/                   # Ket qua Ke hoach A: raw_runs.jsonl, summary_metrics.csv
│   │   └── assignments/          # Chi tiet phan bo task, thu tu chuoi cong viec tung run
│   ├── rolling/                  # Ket qua Ke hoach B: rolling_scorecard.csv
│   │   └── traces/               # Chi tiet tung Sprint: TVE, Breaches, phan bo tung doi
│   └── figures/                  # 4 Line Charts PNG & Pareto Front PNGs
├── tests/
│   ├── test_models_metrics.py    # Test logic models, C_ij, static bounds
│   ├── test_hcsm.py              # Test 4 pha H-CSM, Guardrail, Bitmask DP
│   └── test_baselines.py         # Test CP-SAT, Routing GLS, Greedy
├── main.py                       # CLI dieu khien tap trung (run static, rolling, inspect, test)
├── pyproject.toml
└── README.md
```

---

## 2. Hệ Thống Log Thực Nghiệm & Chi Tiết Kết Quả (Execution Logging)

Nhằm phục vụ kiểm toán khoa học và xác thực thực nghiệm, hệ thống lưu trữ kết quả ở 2 cấp độ: **Số liệu tổng hợp (Metrics)** và **Dữ liệu phân bổ thực tế (Actual Assignment Trace)**.

### 2.1. Lưu Vết Dữ Liệu Thực Tế Từng Lượt Chạy (Actual Run Trace)
Mỗi lần giải một bài toán, solver không chỉ trả về điểm số $f_1, f_2, Z$, mà bắt buộc ghi lại đầy đủ đối tượng `SprintPlan` chi tiết dưới dạng JSON:
* **Tập Task đầu vào**: `task_id`, `r_i`, `e_i`, `repo`, `module`, `skill`, `sprint_discovered`, `deadline_sprint`.
* **Phân bổ từng Đội (`ScheduleResult`)**:
  - `team_id`: Đội tiếp nhận.
  - `assigned_tasks`: Danh sách ID task theo đúng **thứ tự thực thi chuỗi công việc** $\pi_m = [t_1, t_2, \dots, t_k]$.
  - `total_effort`: Tổng Story Points đã dùng (ví dụ: $29/30\text{ SP}$).
  - `context_switch_cost`: Chi phí chuyển đổi nội bộ của đội $C(\mathcal{A}_m)$.
  - `mitigated_utility`: Tổng điểm rủi ro $u_i$ đội đã giải quyết.
* **Tập Task bị hoãn (`deferred_tasks`)**: Danh sách ID các task không thể nạp vào sprint, chuyển tiếp sang backlog kỳ sau.

### 2.2. Cơ Chế Log Từng Pha Của H-CSM (Phase-by-Phase Debug Log)

Để hỗ trợ kiểm tra chi tiết "từng cụm gồm những task nào, gán vào đâu", hệ thống cung cấp 2 chế độ hiển thị linh hoạt:

1. **Chế độ Tóm tắt (`--verbose`)**: Tóm tắt nhanh số lượng, dung lượng và chỉ số từng pha (như mẫu bên dưới).
2. **Chế độ Chi tiết (`--detailed` hoặc `--inspect`)**: Bung chi tiết toàn bộ danh sách Task ID ($v_i$) của từng cụm, từng quyết định gán và chuỗi thứ tự:
   * **Pha 1**: Liệt kê từng Cụm / Chunk: `Chunk B1 [repo: auth, mod: jwt, skill: A02] (14 SP) -> Tasks: [v12, v15, v18]`.
   * **Pha 2**: Liệt kê các Chunk giao cho từng Team: `Team t1 <- Chunks [B1, B3, B7] (28 SP) -> Tasks: [v12, v15, v18, v31, ...]`.
   * **Pha 3**: Liệt kê từng Task lẻ được nhận hoặc bị chặn:
     - `Accepted: Task v45 (2 SP) -> Team t1 (Gain: +0.015, S > 0)`
     - `Guardrail Blocked: Task v52 (3 SP) -> Team t2 (S = -0.008 <= 0, diff_repo=1)`
   * **Pha 4**: Liệt kê chuỗi thứ tự thực thi chi tiết của từng Team:
     - `Team t1 route: [v12 -> v15 -> v18] -> [v31 -> v35] -> [v45] (Cost f2: 1.8)`.

```text
========================================================================================
[H-CSM Detailed Trace] Scenario: small_40_inst1 | Weight w: 0.50 | Target: 2 Teams
----------------------------------------------------------------------------------------
[Phase 1: Coarsening & Chunking]
  • Input: 40 tasks | 9 Atomic Clusters -> 11 Chunks (E_chunk = 15 SP)
  • Chunk Details:
    - B0 [repo: core, mod: auth, skill: A02] (14 SP): Tasks [v101, v105, v108]
    - B1 [repo: core, mod: user, skill: A01] (12 SP): Tasks [v112, v115]
    - B2 [repo: pay,  mod: bill, skill: A04] (15 SP): Tasks [v120, v121, v125]
    - ...
[Phase 2: Multi-Cluster Packing]
  • Bounds: f1_max = 285.0, f2_max = 14.0 | Metric: Delta Z(w) / Effort
  • Packing Decisions:
    - Team t1 <- Chunks [B0, B1] (Total: 26 SP, Rem: 4 SP) | Tasks: [v101, v105, v108, v112, v115]
    - Team t2 <- Chunks [B2, B4] (Total: 27 SP, Rem: 3 SP) | Tasks: [v120, v121, v125, v130]
[Phase 3: Residual Backfill & Hard Guardrail]
  • Unassigned Tasks Pool: 15 tasks
  • Backfill Decisions:
    - ACCEPTED: Task v109 (2 SP) -> Team t1 | Delta Z: +0.012 (S = 0.0060 > 0)
    - ACCEPTED: Task v132 (2 SP) -> Team t2 | Delta Z: +0.010 (S = 0.0050 > 0)
    - BLOCKED:  Task v140 (3 SP) -> Team t1 | Delta Z: -0.008 (S <= 0, Reason: diff_repo=1)
  • Rem. Capacity: Team t1: 28/30 SP (Rem: 2 SP) | Team t2: 29/30 SP (Rem: 1 SP)
[Phase 4: Super-Node Block-Level Open-TSP]
  • Team t1 (3 blocks) -> Bitmask DP optimal route:
    Chain: [B0: v101 -> v105 -> v108] -> [v109] -> [B1: v112 -> v115] | Cost: 1.3
  • Team t2 (3 blocks) -> Bitmask DP optimal route:
    Chain: [B2: v120 -> v121 -> v125] -> [v132] -> [B4: v130] | Cost: 1.5
----------------------------------------------------------------------------------------
[H-CSM Final Result] Assigned: 12 tasks (57 SP) | f1: 278.4 | f2: 2.8 | Z(0.5): 0.388 | Time: 2.1 ms
========================================================================================
```

*(Lưu ý: Toàn bộ thông tin chi tiết từng task $v_i$ này cũng được tự động serialize và lưu vào file JSON `outputs/static/assignments/` để tra cứu bất kỳ lúc nào mà không cần chạy lại solver).*

---

## 3. Kế Hoạch Triển Khai Kỹ Thuật Chi Tiết (Step-by-Step Implementation)

### Bước 1: Dọn Dẹp Code Cũ & Đồng Bộ Models / Metrics
1. **Dọn rác**: Xóa các file `scripts/solo_*.py`, `src/proposed/`, `src/baselines/`, `src/solvers/proposed_4phase/`, `src/solvers/proposed_nsga2/`.
2. **Đồng bộ `src/models.py`**:
   - Sử dụng chính thức trường `sprint_discovered` và `deadline_sprint`.
   - Bổ sung hàm xuất `to_dict()` cho `SprintPlan` để phục vụ serialize ra file JSON assignment trace.
3. **Chuẩn hóa `src/metrics.py`**:
   - Tích hợp kiểm định thống kê `scipy.stats.wilcoxon(alternative='greater')` để tính $p$-value đối đầu trực tiếp với GLS.
   - Hàm đánh giá kế hoạch `evaluate_sprint_plan` tính toán đầy đủ $f_1, f_2, Z(w)$.

### Bước 2: Hoàn Thiện Thuật Toán Đề Xuất `src/solvers/proposed_hcsm/`
1. **`coarsening.py`**: Gom cụm $C_{ij} = 0$, cắt chunk $E_{\text{chunk}} = 15\text{ SP}$ theo mật độ $\rho_i = u_i / e_i$ giảm dần.
2. **`packing.py`**: Tính Gain theo đúng độ biến thiên mục tiêu toàn cục $\Delta Z(w)$:
   $$\text{Gain}(B_k, m, w) = w \cdot \frac{U(B_k)}{f_1^{\max}} - (1 - w) \cdot \frac{\Delta C(B_k, \mathcal{A}_m)}{f_2^{\max}}$$
3. **`backfill.py`**: Lập hàng rào chặn cứng $S(i, m, w) > 0$. Kiên quyết từ chối nạp task nếu $S \le 0$ để bảo vệ ngữ cảnh dev.
4. **`block_tsp.py`**: Giải Open-TSP giữa các super-nodes bằng Bitmask DP cho $B \le 12$ ($O(2^B \cdot B^2)$), fallback Nearest Neighbor khi $B > 12$.
5. **`solver.py`**: Điều phối 4 pha, tích hợp `PhaseLogger` kích hoạt khi `verbose=True`.

### Bước 3: Chuẩn Hóa 3 Baselines Trong `src/solvers/`
1. **`greedy_cvss.py`**: Sắp xếp theo $\rho_i = u_i / e_i$, bốc việc tuần tự theo dung lượng và skill, giữ nguyên thứ tự thực thi.
2. **`cpsat_exact.py`**: Giải MO-MILP với đỉnh ảo $S, E$ và MTZ subtour elimination. Quản lý timeout $30\text{ s}$, nếu timeout trả về nghiệm khả thi tốt nhất tìm được hoặc rỗng.
3. **`ortools_routing.py`**: Guided Local Search (GLS) với `PARALLEL_CHEAPEST_INSERTION`, time limit $30\text{ s}$.

### Bước 4: Viết Scripts Benchmark Theo Chuẩn Mới
1. **`scripts/run_benchmark_static.py` (Kế hoạch A)**:
   - Chạy 3 kịch bản (`small_40`, `medium_100`, `large_500`) $\times$ 5 instances $\times$ 4 thuật toán.
   - Đánh giá trên 3 trọng số $w \in \{0.25, 0.50, 0.75\}$.
   - Lưu kết quả số liệu vào `outputs/static/summary_metrics.csv` và `raw_runs.jsonl`.
   - Lưu chi tiết phân bổ từng task vào `outputs/static/assignments/{scenario}_{solver}_inst{idx}.json`.
2. **`scripts/run_benchmark_rolling.py` (Kế hoạch B)**:
   - Mô phỏng chuỗi 8 Sprint liên tiếp $\times$ 5 seeds $\times$ 4 thuật toán.
   - Áp dụng cơ chế Backlog động $\text{Backlog}^{(s)} = \text{Deferred}^{(s-1)} \cup \{i \mid \text{disc}_i = s\}$.
   - Ghi nhận trạng thái Timeout cho CP-SAT nếu vượt quá $30\text{ s}$.
   - Tính toán $\text{AUC-TVE}$, $\text{Total Breaches}$, $\text{Total } f_2$, $\text{Total } Z(0.5)$ và $p$-value vs GLS.
   - Lưu kết quả vào `outputs/rolling/scorecard.csv` và chi tiết từng sprint vào `outputs/rolling/traces/`.
3. **`scripts/plot_benchmarks.py`**:
   - Quét 11 điểm $w \in \{0.0, 0.1, \dots, 1.0\}$ để vẽ đường cong Pareto Front mượt mà (Kế hoạch A).
   - Vẽ 4 Biểu đồ đường (Line Charts) qua 8 Sprint cho 4 chỉ số (Kế hoạch B) kèm sai số mờ $\text{Std}$.

### Bước 5: Cập Nhật CLI `main.py` & Kiểm Thử Toàn Diện `tests/`
1. **CLI `main.py`**:
   - `python main.py static`: Chạy Kế hoạch A.
   - `python main.py rolling`: Chạy Kế hoạch B.
   - `python main.py inspect --scenario small_40 --instance 1 --solver proposed`: Chạy 1 instance có bật Phase Logger chi tiết để kiểm toán từng bước.
   - `python main.py plot`: Xuất toàn bộ biểu đồ.
2. **Kiểm thử Unit Tests**:
   - Viết các test suite chặt chẽ trong `tests/` kiểm tra: tính đúng của static bounds, không vi phạm dung lượng, không gán trùng task, điều kiện chặn cứng Guardrail $S > 0$, tính tối ưu của Bitmask DP.
   - Chạy kiểm thử: `python -m unittest discover tests`.

---

## 4. Bảng Kiểm Tra Tiến Độ & Tiêu Chí Nghiệm Thu (Acceptance Criteria)

| Thành phần | Tiêu chí nghiệm thu | Trạng thái |
| :--- | :--- | :---: |
| **Dọn dẹp mã nguồn** | Xóa sạch 100% file solo và duplicate, cấu trúc thư mục sạch đẹp | [x] |
| **H-CSM Solver** | Khớp công thức Gain $\Delta Z(w)$, Guardrail $S > 0$, Bitmask DP $B \le 12$ | [x] |
| **Phase Logger** | In log 4 pha rõ ràng khi bật cờ `--inspect`, không làm chậm benchmark | [x] |
| **Assignment Trace** | Xuất đầy đủ file JSON chi tiết task assignment cho từng run | [x] |
| **Kế hoạch A Script** | Chạy trơn tru 5 instances $\times$ 3 kịch bản $\times$ 3 trọng số $w$ | [x] |
| **Kế hoạch B Script** | Mô phỏng trọn vẹn 8 Sprints $\times$ 5 seeds, xử lý timeout CP-SAT chuẩn | [x] |
| **Visualizer Script** | Xuất đủ đồ thị Pareto Front (11 điểm $w$) và 4 Line Charts qua 8 Sprint | [x] |
| **Unit Test Suite** | 100% unit tests PASS với thư viện chuẩn `unittest` | [x] |

