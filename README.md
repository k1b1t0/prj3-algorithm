# prj3-algorithm: Bi-Objective SecOps Vulnerability Scheduling

Hệ sinh thái thuật toán tối ưu hóa điều độ và phân bổ công việc vá lỗ hổng an ninh mạng đa mục tiêu trong chu kỳ Sprint Agile (**Bi-Objective Agile SecOps Scheduling**).

---

## 1. Mô Hình Toán Học Hình Thức (Formal Mathematical Model)

Mô hình ánh xạ 1-1 từ nghiên cứu lý thuyết tại `research/reports/prj3/problem_model.md`:

### 1.1. Các Chỉ Số Tính Toán Cốt Lõi
1. **Điểm Lợi Ích Giảm Nhẹ Rủi Ro (Mitigation Utility — $u_i$)**:
   $$u_i = r_i + \alpha \cdot (\tau - \text{disc}_i) + M_{\text{penalty}} \cdot \mathbb{I}(\tau \ge \text{dead}_i)$$
   - $r_i \in [0, 10]$: Điểm rủi ro kỹ thuật CVSS gốc.
   - $\alpha = 0.5$: Hệ số tồn lưu qua các sprint chưa vá.
   - $M_{\text{penalty}} = 50.0$: Phạt tăng vọt khi sprint hiện tại $\tau$ đã chạm hoặc vượt quá hạn chót SLA $\text{dead}_i$.

2. **Chi Phí Chuyển Đổi Ngữ Cảnh Phân Cấp (Context Switch Distance — $C_{ij}$)**:
   $$C_{ij} = w_{\text{repo}} \cdot \mathbb{I}(\text{repo}_i \neq \text{repo}_j) + w_{\text{mod}} \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + w_{\text{skill}} \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j)$$
   - $w_{\text{repo}} = 0.5$: Phạt nặng nhất do đổi kho chứa mã nguồn, chuyển môi trường IDE.
   - $w_{\text{mod}} = 0.3$: Phạt vừa do đổi phân hệ microservice.
   - $w_{\text{skill}} = 0.2$: Phạt nhẹ do đổi nhóm kỹ năng OWASP ($0.5 + 0.3 + 0.2 = 1.0$).
   - $C_{ij} = 0 \iff$ Cùng Repo, cùng Module và cùng nhóm Skill.

### 1.2. Hàm Mục Tiêu Kép (Bi-Objective Criteria)
- **Mục tiêu 1 (Cực đại hóa Lợi ích Rủi ro Giảm nhẹ)**:
  $$\max f_1 = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i \cdot x_{it}$$
- **Mục tiêu 2 (Cực tiểu hóa Tổng Chi phí Chuyển đổi Ngữ cảnh)**:
  $$\min f_2 = \sum_{t \in T} \sum_{k=1}^{|\pi_t|-1} C_{\pi_t(k), \pi_t(k+1)}$$
- **Hàm vô hướng hóa**: $\max Z(\lambda) = f_1 - \lambda \cdot f_2$ với $\lambda \ge 0$.

### 1.3. Ràng Buộc Cứng (Hard Constraints)
1. **Dung lượng Sprint (Knapsack)**: $\sum_{i \in \mathcal{V}} e_i \cdot x_{it} \le \text{cap}_t, \forall t \in T$ (Chuẩn 30 SP / team).
2. **Ngưỡng năng lực kỹ năng**: $x_{it} \le \mathbb{I}(k_{t, \text{skill}_i} \ge 0.5), \forall i, t$.
3. **Ràng buộc phụ thuộc kỹ thuật DAG & Intra-team Execution**:
   $$x_{vt} \le x_{ut}, \quad \forall (u, v) \in \mathcal{E}, \forall t \in T$$
   *(Nếu task con $v$ được chọn, task cha $u$ bắt buộc phải được chọn và giao cho CÙNG MỘT TEAM)*.
4. **Bảo toàn luồng chuỗi & Thứ tự Topo (MTZ Subtour Elimination)**: Đảm bảo thứ tự topo $u \prec v$ trong chuỗi nội bộ của team.

---

## 2. Kiến Trúc 3 Tầng Tách Biệt (Decoupled 3-Tier Architecture)

Toàn bộ hệ thống được tái cấu trúc thành 3 tầng độc lập hoàn toàn theo chuẩn khoa học:

```text
┌────────────────────────────────────────────────────────────────────────┐
│            KIẾN TRÚC 3 TẦNG TÁCH BIỆT (DECOUPLED PIPELINE)            │
├────────────────────────────────────────────────────────────────────────┤
│ TẦNG 1: CORE THUẬT TOÁN (src/solvers/)                                │
│ • Chuẩn hóa qua Interface: BaseSolver.solve(tasks, teams, **kwargs)   │
│ • Thuần túy thuật toán, không nhét code logging/vis vào core.         │
│ • greedy_cvss.py, cpsat_exact.py, proposed_4phase/ (CSM),                     │
│   proposed_4phase/, proposed_nsga2/                                    │
├───────────────────────────────────┬────────────────────────────────────┤
│ TẦNG 2: RUNNER & LOGGER           │ TẦNG 3: BÁO CÁO & VISUALIZER       │
│ (scripts/run_experiments.py)      │ (Các script phụ chạy riêng)        │
│ • Đọc Scenario & cấu hình         │ • render_dashboard.py: Render HTML │
│ • Chạy 5 instances x 5 seeds      │   dashboard giao diện Glassmorphism│
│ • In bảng tóm tắt ra Terminal     │ • plot_pareto.py: Vẽ biểu đồ PNG   │
│ • Ghi RAW data: raw_runs.jsonl    │   mặt cong Pareto & Hypervolume.   │
│ • Ghi BẢNG PIVOT: summary.csv     │                                    │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 2.1. Tầng 1: Core Solvers (`src/solvers/`)
1. **`Greedy-CVSS (Industry Standard)`**:
   - Sắp xếp Backlog giảm dần theo Mitigation Utility $u_i$.
   - Duyệt tuần tự: Đảm bảo ràng buộc intra-team (cha con cùng team) và gán cho team đầu tiên thỏa mãn năng lực ($k \ge 0.5$) và đủ Story Points.
2. **`OR-Tools CP-SAT (Exact Global Optimum)`**:
   - Bộ giải Constraint Programming - SAT của Google, giải bài toán MO-MILP vô hướng hóa tìm nghiệm tối ưu toàn cục làm Ground Truth.
3. **`Gurobi Optimizer (Commercial MIP Solver)`**:
   - Bộ giải quy hoạch nguyên thương mại số 1 thế giới, tự động phát hiện và xử lý giấy phép.
4. **`Proposed 4-Phase Matheuristic (Hybrid ESSC + DP)`**:
   - **Pha 1**: Phân cụm phổ cân bằng (Spectral Clustering) có xét DAG Affinity Boost ($A_{uv} = 1.0$).
   - **Pha 2**: Ghép cặp Team - Cụm bằng Hungarian Matching tối đa hóa điểm kỹ năng.
   - **Pha 3**: Cắt tỉa PCKP Leaf Pruning tỉa các nút lá có tỷ số $u_i / e_i$ thấp nhất để đảm bảo $100\%$ tuân thủ DAG và vừa vặn dung lượng.
   - **Pha 4**: Sắp xếp thứ tự nội bộ từng team bằng Topological Bitmask DP trong $O(2^L L^2)$.
5. **`Proposed Memetic NSGA-II (Metaheuristic)`**:
   - Mã hóa 2 phần: Topo Priority List & Team Assignment Vector.
   - Bộ giải mã Topo Decoder đảm bảo $100\%$ cá thể sinh ra đều khả thi (Zero DAG violations).
   - Tinh chỉnh chuỗi cục bộ bằng Bitmask DP (Memetic component).
   - Đo lường toàn diện Mặt cong Pareto (Pareto Frontier) và diện tích Hypervolume (HV).

---

## 3. Kết Quả Thực Nghiệm Đối Sánh Đa Kịch Bản (Benchmark Results)

Bộ thực nghiệm được thực hiện trên **3 kịch bản chuẩn hóa quy mô** (Small 40, Medium 100, Large 500 tasks), mỗi kịch bản gồm **5 instances độc lập** từ kho 2.103 vulnerabilities thực tế, lặp lại **5 random seeds** cho thuật toán tiến hóa (tổng cộng 120 lượt chạy đo lường):

| Kịch Bản | Giải Thuật (Solver) | Số Lượt Chạy | Lợi Ích Rủi Ro f1 (Mean ± Std) | Tăng f1 vs Greedy (%) | Chi Phí Đổi Ngữ Cảnh f2 (Mean ± Std) | Giảm f2 vs Greedy (%) | Hypervolume (HV) (Mean ± Std) | Vi Phạm DAG | Thời Gian Chạy (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **small_40** *(2 teams)* | **Greedy-CVSS** *(Industry)* | 5 | 406.5 ± 213.5 | Baseline (0.0%) | 5.02 ± 1.19 | Baseline (0.0%) | 3,954.3 ± 1,906.3 | **0** | **0.2 ms** |
| | **OR-Tools CP-SAT** *(Exact Bound)* | 5 | **448.7 ± 197.3** | **+10.4%** | 3.64 ± 0.38 | +27.5% | 5,122.1 ± 2,342.4 | **0** | 15,174.0 ms |
| | **Proposed-CSM** *(Matheuristic)* | 5 | 410.9 ± 170.2 | +1.1% | **2.68 ± 0.65** | **+46.6%** | 5,008.4 ± 1,975.8 | **0** | **176.7 ms** |
| | **Proposed NSGA-II** *(Metaheuristic)* | 25 | 438.1 ± 197.4 | +7.8% | 4.67 ± 0.85 | +7.0% | **5,535.2 ± 2,550.3** | **0** | 2,140.4 ms |
| **medium_100** *(4 teams)* | **Greedy-CVSS** *(Industry)* | 5 | 1167.4 ± 609.2 | Baseline (0.0%) | 7.50 ± 0.87 | Baseline (0.0%) | 26,500.8 ± 14,027.7 | **0** | **0.5 ms** |
| | **OR-Tools CP-SAT** *(Exact Bound)* | 5 | 647.8 ± 395.5 | -44.5% (T.O.) | 10.16 ± 5.32 | -35.5% | 11,165.1 ± 3,853.1 | **0** | 31,812.2 ms |
| | **Proposed-CSM** *(Matheuristic)* | 5 | 1098.8 ± 571.6 | -5.9% | **3.38 ± 1.10** | **+54.9%** | **29,271.5 ± 15,789.0** | **0** | **2,372.5 ms** |
| | **Proposed NSGA-II** *(Metaheuristic)* | 25 | 1084.3 ± 497.4 | -7.1% | 11.54 ± 2.13 | -53.9% | 23,527.8 ± 10,043.0 | **0** | 4,807.5 ms |
| **large_500** *(8 teams)* | **Greedy-CVSS** *(Industry)* | 5 | **3064.6 ± 801.5** | Baseline (0.0%) | 17.18 ± 0.83 | Baseline (0.0%) | 130,758.5 ± 31,994.9 | **0** | **2.8 ms** |
| | **OR-Tools CP-SAT** *(Exact Bound)* | 5 | 0.0 ± 0.0 | N/A (Timeout) | 0.00 ± 0.00 | N/A (Timeout) | 0.0 ± 0.0 | 0 | 117,040.4 ms |
| | **Proposed-CSM** *(Matheuristic)* | 5 | 2603.9 ± 474.9 | -15.0% | **8.46 ± 1.06** | **+50.8%** | **134,027.8 ± 24,005.1** | **0** | **7,218.0 ms** |
| | **Proposed NSGA-II** *(Metaheuristic)* | 25 | 1724.2 ± 270.5 | -43.7% | 31.36 ± 4.78 | -82.5% | 63,157.4 ± 8,165.3 | **0** | 12,957.4 ms |

### Nhận Xét Khoa Học Cốt Lõi:
1. **Khả năng mở rộng vượt bậc của Proposed-CSM Matheuristic**:
   - **Triệt tiêu chi phí đổi ngữ cảnh (f2)** đồng nhất trên mọi quy mô: Giảm tới **46.6%** ở Small, **54.9%** ở Medium, và **50.8%** ở Large so với Greedy công nghiệp.
   - **Đạt Hypervolume cao nhất ở cả Medium (29,271.5) và Large (134,027.8)**, chứng minh sự ổn định vượt bậc khi bài toán phình to về số task và số team.
   - Thời gian thực thi cực nhanh: Chỉ 176ms (Small), 2.3s (Medium), và 7.2s (Large 500 tasks), giải quyết bài toán mà solver toán học CP-SAT hoàn toàn bất lực.
2. **Điểm nghẽn bùng nổ tổ hợp của Solver Toán học CP-SAT**:
   - Giải tối ưu ở Small 40 ( = 448.7$).
   - Bị nghẽn nặng ở Medium 100 do không gian 40.000 biến nhị phân, chỉ tìm được nghiệm non ( = 647.8$).
   - Hoàn toàn quá tải ở Large 500 tasks (2.000.000 biến nhị phân), mất 117s mà không tìm được bất kỳ nghiệm khả thi nào.
3. **Bài học về Metaheuristic NSGA-II trên không gian hoán vị lớn**:
   - Hoạt động xuất sắc ở quy mô nhỏ (Small 40 tasks), đạt Hypervolume cao nhất (,535.2$).
   - Khi bài toán tăng lên 500 tasks (không gian hoán vị 00!$), toán tử lai ghép toàn cục OX và đột biến phân tán khiến NSGA-II khó hội tụ trong số thế hệ hữu hạn. Đây là luận điểm khoa học mạnh mẽ để mở rộng hướng nghiên cứu tương lai sang **Adaptive Large Neighborhood Search (ALNS)**.
4. **Toàn vẹn ràng buộc toán học**:
   - 00\%$ các phương án sinh ra bởi các thuật toán khả thi đều đạt **0 DAG violations**, thỏa mãn tuyệt đối các ràng buộc dung lượng Story Points và ngưỡng năng lực >= 0.5.


---

## 4. Hướng Dẫn Cài Đặt & Sử Dụng (Quickstart Guide)

### 4.1. Cài đặt Môi trường với `uv`
```bash
# Khởi tạo và cài đặt toàn bộ dependencies tự động
uv sync
```

### 4.2. Chạy Thực Nghiệm Benchmark (Tier 2)
```bash
# Chạy toàn bộ thực nghiệm Kịch bản 1 (5 instances, 5 seeds)
uv run main.py experiments --scenarios small_40 --instances 5 --seeds 42 100 2024 777 999 --clean

# Chạy cả 3 kịch bản chuẩn (small_40, medium_100, large_500)
uv run main.py experiments --scenarios small_40 medium_100 large_500 --instances 5
```

### 4.3. Xuất Báo Cáo & Trực Quan Hóa (Tier 3)
```bash
# Xuất biểu đồ Pareto và Hypervolume dạng ảnh PNG (300 DPI)
uv run main.py pareto

# Render HTML Dashboard tương tác trực quan
uv run main.py dashboard

# All-in-one: Chạy benchmark, vẽ đồ thị Pareto và render Dashboard
uv run main.py all --scenarios small_40 --instances 5
```

File kết quả được tự động lưu tại:
- `outputs/raw_runs.jsonl`: Dữ liệu log chi tiết từng lượt chạy (Single Source of Truth).
- `outputs/summary_metrics.csv`: Bảng tổng hợp Mean ± Std cho bài báo.
- `outputs/dashboard.html`: Giao diện Dashboard HTML tương tác trực quan.
- `outputs/pareto_plots/`: Bộ ảnh biểu đồ Pareto và so sánh đa chỉ số PNG.

### 4.4. Chạy Unit Tests
```bash
uv run python -m unittest discover tests
```
