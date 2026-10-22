# prj3-algo-no-dag: Bi-Objective Agile SecOps Vulnerability Scheduling (Decoupled Precedence Architecture)

Hệ sinh thái thuật toán tối ưu hóa điều độ và phân bổ công việc khắc phục lỗ hổng an ninh mạng đa mục tiêu trong chu kỳ Sprint Agile (**Bi-Objective Agile SecOps Scheduling**), được hiện thực hóa theo kiến trúc phi phụ thuộc tác vụ (No-DAG Task-Level Decoupling).

Dự án này là biến thể độc lập của `prj3-algorithm/`, được xây dựng để đối chiếu thực nghiệm trực tiếp giữa hai trường phái mô hình hóa trong DevSecOps:
1. **Mô hình có phụ thuộc DAG (prj3-algorithm)**: Ép buộc ràng buộc thứ tự cứng cha-con và cư trú cùng đội (Intra-team execution), phản ánh bài toán Next Release Problem (NRP) cổ điển nhưng chịu nghẽn năng lực (capacity starvation).
2. **Mô hình phi phụ thuộc DAG (prj3-algo-no-dag)**: Tách rời phụ thuộc tác vụ giả định, chuyển hóa bài toán sang Đa ba-lô đa kỹ năng (Multi-Team Multi-Skill Knapsack) kết hợp Định tuyến tối ưu giảm chi phí đổi ngữ cảnh (Context-Switch Routing). Bài toán kế thừa và phát triển từ nền tảng VULCON (ICSE 2020), giải quyết bài toán phân công đa đội thực tế.

---

## 1. Mô Hình Toán Học Hình Thức (Formal Mathematical Model)

### 1.1. Các Chỉ Số Cốt Lõi
1. **Điểm Lợi Ích Khắc Phục Lỗ Hổng (Mitigation Utility — u_i)**:
   - Công thức: `u_i = r_i + alpha * (tau - disc_i) + M_penalty * I(tau >= dead_i)`
   - `r_i in [0, 10]`: Điểm rủi ro kỹ thuật CVSS gốc.
   - `alpha = 0.5`: Trọng số tích lũy rủi ro theo thời gian tồn lưu qua các sprint chưa vá.
   - `M_penalty = 50.0`: Mức phạt leo thang khi sprint hiện tại `tau` đã chạm hoặc vượt quá hạn chót SLA `dead_i`.

2. **Khoảng Cách Ngữ Cảnh Tác Vụ (Context Switch Distance — C_ij)**:
   - Công thức: `C_ij = w_repo * I(repo_i != repo_j) + w_mod * I(mod_i != mod_j) + w_skill * I(skill_i != skill_j)`
   - `w_repo = 0.5`: Chi phí chuyển đổi kho chứa mã nguồn / repository (IDE context reload).
   - `w_mod = 0.3`: Chi phí chuyển đổi phân hệ / microservice module.
   - `w_skill = 0.2`: Chi phí chuyển đổi nhóm kỹ năng an toàn OWASP Top-10.
   - Tổng trọng số: `0.5 + 0.3 + 0.2 = 1.0`. `C_ij = 0` khi và chỉ khi hai tác vụ cùng kho, cùng phân hệ và cùng nhóm kỹ năng.

### 1.2. Hàm Mục Tiêu Kép (Bi-Objective Criteria)
- **Mục tiêu 1 (Cực đại hóa Lợi ích Khắc phục Lỗ hổng)**:
  `max f1 = sum_{t in T} sum_{i in V} u_i * x_{it}`
- **Mục tiêu 2 (Cực tiểu hóa Tổng Chi phí Chuyển đổi Ngữ cảnh)**:
  `min f2 = sum_{t in T} sum_{k=1}^{|pi_t|-1} C_{pi_t(k), pi_t(k+1)}`
- **Hàm vô hướng hóa (Scalarized Objective)**:
  `max Z(lambda) = f1 - lambda * f2` với `lambda >= 0`.

### 1.3. Ràng Buộc Kỹ Thuật (Hard Constraints)
1. **Trần dung lượng Sprint (Knapsack Capacity)**:
   `sum_{i in V} e_i * x_{it} <= cap_t, forall t in T` (Chuẩn Scrum 30 Story Points / đội).
2. **Ngưỡng năng lực kỹ năng chuyên môn (Skill Threshold)**:
   `x_{it} <= I(k_{t, skill_i} >= 0.5), forall i in V, forall t in T`.
3. **Phân bổ đơn nhất (Single Assignment)**:
   `sum_{t in T} x_{it} <= 1, forall i in V`.
4. **Bảo toàn luồng định tuyến (Miller-Tucker-Zemlin Subtour Elimination)**:
   Loại bỏ chu trình con và xác định thứ tự thực thi tối ưu `pi_t` nội bộ cho từng đội nhằm cực tiểu hóa `f2`.
5. **Phi phụ thuộc thứ tự tác vụ (No-DAG Decoupling)**:
   Ràng buộc `x_{vt} <= x_{ut}` được gỡ bỏ. Sự gom cụm kiến trúc (architectural colocation) được điều tiết tự nhiên thông qua hàm mục tiêu `f2` thay vì áp đặt cứng nhắc.

---

## 2. So Sánh Với Mô Hình VULCON (ICSE 2020)

| Tiêu Chí | VULCON (Nguyen et al., ICSE 2020) | prj3-algo-no-dag (Proposed Framework) |
| :--- | :--- | :--- |
| **Cơ cấu tổ chức** | 1 Knapsack tổng duy nhất cho toàn tổ chức | **Đa đội Agile (Multi-Team Knapsack)** với các năng lực chuyên môn riêng biệt |
| **Đơn vị nỗ lực** | Giờ công kỹ sư `h_i` dưới tổng ngân sách `H` (hours) | **Story Points chuẩn Scrum `e_i`** theo trần sprint `cap_t = 30 SP` |
| **Kỹ năng chuyên môn** | Bỏ qua (mọi kỹ sư giả định có thể sửa mọi CVE) | **Ma trận kỹ năng OWASP Top-10** (`k_{t, skill} >= 0.5`) |
| **Chi phí chuyển ngữ cảnh** | Không xét (coi các bản vá là độc lập hoàn toàn) | **Hàm mục tiêu thứ hai `f2`** đo lường khoảng cách Repo - Module - Skill |
| **Thứ tự thực thi** | Không xét thứ tự nội bộ | **Định tuyến chuỗi tối ưu (Intra-team sequencing)** giải bài toán Open TSP |
| **Không gian Pareto** | Tối ưu đơn mục tiêu (MILP) | **Tối ưu hóa đa mục tiêu thực thụ (Bi-Objective MOCO)** |

---

## 3. Kiến Trúc 3 Tầng Tách Biệt (Decoupled 3-Tier Architecture)

Toàn bộ hệ thống tuân thủ kiến trúc phân tầng chuẩn mực nghiên cứu:

```text
+------------------------------------------------------------------------+
|            KIẾN TRÚC 3 TẦNG TÁCH BIỆT (DECOUPLED PIPELINE)            |
+------------------------------------------------------------------------+
| TẦNG 1: CORE THUẬT TOÁN (src/solvers/)                                |
| - Chuẩn hóa qua Interface BaseSolver.solve(tasks, teams, **kwargs)     |
| - Không phụ thuộc code logging hay hiển thị                           |
| - greedy_cvss.py: Baseline thực tế doanh nghiệp                       |
| - cpsat_exact.py: Nghiệm tối ưu toàn cục Google OR-Tools CP-SAT       |
| - proposed_4phase/: Matheuristic Cluster-Simulate-Match (CSM No-DAG)  |
| - proposed_nsga2/: Metaheuristic Memetic NSGA-II                      |
+-----------------------------------+------------------------------------+
| TẦNG 2: RUNNER & LOGGER           | TẦNG 3: BÁO CÁO & VISUALIZER       |
| (scripts/run_experiments.py)      | (Các script độc lập)               |
| - Điều phối 3 kịch bản chuẩn      | - render_dashboard.py: Xuất HTML   |
| - 5 instances x 5 seeds ngẫu nhiên|   Dashboard Glassmorphism trực quan|
| - Ghi log thô: outputs/raw_runs   | - plot_pareto.py: Xuất biểu đồ     |
| - Xuất CSV: summary_metrics.csv   |   Pareto Frontier & Hypervolume PNG|
+-----------------------------------+------------------------------------+
```

### Các Giải Thuật Cốt Lõi:
1. **`Greedy-CVSS (Industry Standard Practice)`**:
   - Sắp xếp Backlog giảm dần theo `u_i`.
   - Gán tuần tự cho đội đầu tiên thỏa mãn kỹ năng chuyên môn (`k >= 0.5`) và còn đủ dung lượng Story Points.
2. **`OR-Tools CP-SAT (Exact Global Optimum)`**:
   - Hiện thực hóa mô hình MO-MILP vô hướng hóa trên bộ giải CP-SAT của Google, cung cấp chặn trên toán học (Exact Bound).
3. **`Proposed-CSM Matheuristic (Cluster-Simulate-Match No-DAG)`**:
   - **Bước 1**: Tiền lọc tập ứng viên ưu tiên cao (Candidate Pool Pre-Filtering) theo hàm hữu dụng khi backlog vượt quá 2 lần tổng dung lượng.
   - **Bước 2**: Phân cụm phổ cân bằng (Spectral Clustering) theo ma trận khoảng cách ngữ cảnh RBF Gaussian (`A_ij = exp(-gamma * C_ij)`).
   - **Bước 3**: Giả lập đánh giá ma trận cặp (Đội i, Cụm j) kết hợp knapsack chọn lọc theo mật độ `u_i / e_i` và ước tính chi phí ngữ cảnh nhóm nhanh.
   - **Bước 4**: Ghép cặp tối ưu toàn cục (Global Hungarian Matching) tối đa hóa lợi ích thu được.
   - **Bước 5**: Bổ sung dung lượng còn thừa (Residual capacity fill) ưu tiên các tác vụ cùng repo/module.
   - **Bước 6**: Định tuyến chuỗi tối ưu cục bộ bằng Bitmask DP cho các cặp đội thắng giải trong thời gian dưới 1 giây.
4. **`Proposed Memetic NSGA-II (Metaheuristic)`**:
   - Biểu diễn nhiễm sắc thể kép: Priority Vector (hoán vị tác vụ) và Team Assignment Vector.
   - Toán tử lai ghép OX cải tiến bảo toàn tính đơn nhất của tập tác vụ.
   - Tối ưu hóa chuỗi cục bộ bằng Bitmask DP cho các cá thể thuộc Mặt cong Pareto (Front 0).

---

## 4. Kết Quả Thực Nghiệm Đối Sánh Đa Kịch Bản (Benchmark Results)

Bộ thực nghiệm đo lường đầy đủ **120 lượt chạy thực nghiệm độc lập** trên 3 kịch bản chuẩn hóa quy mô từ kho dữ liệu 2.103 lỗ hổng bảo mật thực tế:

| Kịch Bản | Giải Thuật (Solver) | Số Lượt Chạy | Lợi Ích Lỗ Hổng f1 (Mean ± Std) | Tăng f1 vs Greedy (%) | Chi Phí Chuyển Đổi f2 (Mean ± Std) | Giảm f2 vs Greedy (%) | Hypervolume (HV) (Mean ± Std) | Thời Gian Chạy (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **small_40** *(2 đội, 40 tasks)* | **Greedy-CVSS** *(Industry)* | 5 | 406.0 ± 212.5 | Baseline (0.0%) | 4.72 ± 0.93 | Baseline (0.0%) | 4,115.1 ± 2,034.5 | **0.1 ms** |
| | **OR-Tools CP-SAT** *(Exact)* | 5 | **453.5 ± 199.1** | **+11.7%** | 3.98 ± 0.83 | +15.7% | 4,956.2 ± 2,147.0 | 15,107.7 ms |
| | **Proposed-CSM** *(Matheuristic)* | 5 | 420.3 ± 180.6 | +3.5% | **3.18 ± 1.08** | **+32.6%** | 4,863.9 ± 1,953.7 | **278.7 ms** |
| | **Proposed-NSGA-II** *(Meta)* | 25 | 441.1 ± 196.6 | +8.7% | 5.32 ± 0.78 | -12.8% | **5,382.7 ± 2,451.1** | 2,247.8 ms |
| **medium_100** *(4 đội, 100 tasks)* | **Greedy-CVSS** *(Industry)* | 5 | 1,163.9 ± 611.8 | Baseline (0.0%) | 6.92 ± 0.92 | Baseline (0.0%) | 26,718.0 ± 13,959.2 | **0.2 ms** |
| | **OR-Tools CP-SAT** *(Exact)* | 5 | 1,097.6 ± 560.7 | -5.7% | 20.26 ± 6.49 | -192.8% | 8,398.6 ± 5,157.6 | 31,368.6 ms |
| | **Proposed-CSM** *(Matheuristic)* | 5 | **1,176.4 ± 581.9** | **+1.1%** | **4.68 ± 1.53** | **+32.4%** | **29,271.5 ± 13,879.8** | **575.5 ms** |
| | **Proposed-NSGA-II** *(Meta)* | 25 | 1,045.4 ± 468.0 | -10.2% | 12.34 ± 1.43 | -78.3% | 22,151.3 ± 9,390.1 | 3,264.6 ms |
| **large_500** *(8 đội, 500 tasks)* | **Greedy-CVSS** *(Industry)* | 5 | **3,449.9 ± 836.9** | Baseline (0.0%) | 14.28 ± 2.85 | Baseline (0.0%) | 157,466.0 ± 37,456.3 | **0.7 ms** |
| | **OR-Tools CP-SAT** *(Exact)* | 5 | 0.0 ± 0.0 | T.O. (2M vars) | 0.00 ± 0.00 | N/A | 0.0 ± 0.0 | 75,617.1 ms |
| | **Proposed-CSM** *(Matheuristic)* | 5 | 3,333.5 ± 747.7 | -3.4% | **9.18 ± 1.68** | **+35.7%** | **169,733.5 ± 38,902.0** | **707.1 ms** |
| | **Proposed-NSGA-II** *(Meta)* | 25 | 1,775.1 ± 215.2 | -48.5% | 32.15 ± 4.40 | -125.2% | 64,181.0 ± 8,199.6 | 3,375.8 ms |

---

## 5. Những Phát Hiện Khoa Học Cốt Lõi (Key Scientific Findings)

1. **Hiệu Ứng Vượt Trội Của CSM So Với Greedy Ở Cả Hai Mục Tiêu Trong Quy Mô Trung Bình**:
   - Ở kịch bản `medium_100`, **Proposed-CSM thống trị hoàn toàn Greedy-CVSS** trên cả 2 mục tiêu: tăng lợi ích khắc phục rủi ro `+1.1%` (1,176.4 vs 1,163.9) và đồng thời **cắt giảm chi phí chuyển đổi ngữ cảnh đến 32.4%** (4.68 vs 6.92).
   - Chỉ số Hypervolume của Proposed-CSM đạt **29,271.5**, cao nhất trong toàn bộ các giải thuật thử nghiệm (vượt trội hơn cả Greedy và NSGA-II).

2. **Khả Năng Mở Rộng Dưới 1 Giây Cho Quy Mô Lớn (Sub-Second Scalability)**:
   - Trong khi bài toán quy hoạch nguyên chính xác OR-Tools CP-SAT hoàn toàn bất khả thi khi mở rộng lên 500 tác vụ (hơn 2.000.000 biến nhị phân gây cạn kiệt bộ nhớ và hết thời gian chạy 75 giây với nghiệm rỗng), **Proposed-CSM giải quyết trọn vẹn 500 tác vụ chỉ trong 707.1 ms**.
   - Proposed-CSM ở quy mô 500 tác vụ giúp **cắt giảm 35.7% chi phí chuyển đổi ngữ cảnh** so với thực hành công nghiệp và đạt Hypervolume **169,733.5** (cao hơn Greedy-CVSS +7.8%).

3. **Ý Nghĩa Thực Tiễn So Với Bản Có DAG (prj3-algorithm)**:
   - Khi loại bỏ phụ thuộc tác vụ giả định, các đội không còn bị hiện tượng bỏ rơi tác vụ do nghẽn dung lượng (capacity-induced starvation).
   - Sự gắn kết tự nhiên giữa các tác vụ cùng module được đảm bảo trọn vẹn thông qua tối ưu hóa `f2` (khoảng cách ngữ cảnh phân cấp), loại bỏ nhu cầu cưỡng chế một đội phải ôm trọn cả nhánh cây phụ thuộc.

---

## 6. Hướng Dẫn Sử Dụng & Tái Lập Thực Nghiệm

Toàn bộ dự án được quản lý qua `uv`:

```bash
# 1. Cài đặt môi trường
uv sync

# 2. Chạy bộ kiểm thử tự động
uv run python -m unittest discover tests

# 3. Tái lập toàn bộ 120 lượt chạy thực nghiệm
uv run python scripts/run_experiments.py --scenarios small_40 medium_100 large_500 --instances 5 --seeds 42 100 2024 777 999 --solvers greedy cpsat proposed_4phase proposed_nsga2 --clean

# 4. Xuất đồ thị Pareto độ phân giải cao
uv run python scripts/plot_pareto.py

# 5. Kết xuất Dashboard Glassmorphism tương tác
uv run python scripts/render_dashboard.py
```

File báo cáo trực quan có thể xem tại: `outputs/dashboard.html`.
Các đồ thị đối sánh Pareto được lưu tại: `outputs/pareto_plots/`.
Bảng chỉ số thống kê tổng hợp được lưu tại: `outputs/summary_metrics.csv`.
