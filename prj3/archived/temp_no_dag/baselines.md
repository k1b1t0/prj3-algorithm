# Danh Sách Các Thuật Toán Đối Chuẩn (Baselines Summary — No-DAG Formulation)

> **Mục tiêu**: Định nghĩa và phân loại hệ thống các giải thuật đối chuẩn (Baselines) dùng trong thực nghiệm so sánh với giải thuật đề xuất **H-CSM** cho bài toán No-DAG DevSecOps Sprint Scheduling.

---

## 1. Khung Phân Loại Các Thuật Toán Đối Sánh

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          HỆ THỐNG THUẬT TOÁN ĐỐI SÁNH (BENCHMARK)                      │
├──────────────────────────┬─────────────────────────────────────┬───────────────────────┤
│ Phân Nhóm                │ Tên Thuật Toán                      │ Bản Chất / Cơ Chế     │
├──────────────────────────┼─────────────────────────────────────┼───────────────────────┤
│ 1. Thực tế Công nghiệp   │ Greedy-CVSS                         │ Tham lam ưu tiên CVSS │
├──────────────────────────┼─────────────────────────────────────┼───────────────────────┤
│ 2. Giải thuật Chính xác  │ OR-Tools CP-SAT                     │ Exact MIP / CP Solver │
├──────────────────────────┼─────────────────────────────────────┼───────────────────────┤
│ 3. Heuristic Công nghiệp │ OR-Tools Routing (GLS)              │ Guided Local Search   │
├──────────────────────────┼─────────────────────────────────────┼───────────────────────┤
│ 4. Tiền thân Nghiên cứu  │ CSM Cũ (Spectral + Hungarian)       │ Phân cụm phổ ma trận  │
├──────────────────────────┼─────────────────────────────────────┼───────────────────────┤
│ 5. Metaheuristic Đa MT   │ Proposed NSGA-II                    │ Tiến hóa Pareto       │
├──────────────────────────┼─────────────────────────────────────┼───────────────────────┤
│ 6. Giải thuật Đề xuất    │ Proposed H-CSM                      │ Phân cấp 4 Pha        │
└──────────────────────────┴─────────────────────────────────────┴───────────────────────┘
```

---

## 2. Chi Tiết Từng Giải Thuật Baseline

### 2.1. Baseline 1: Greedy-CVSS (Tiêu Chuẩn Thực Tế Công Nghiệp — Jira Default)
- **Bản chất**: Heuristic tham lam một chiều dựa trên độ nghiêm trọng gốc của lỗ hổng.
- **Quy trình thực hiện**:
  1. Sắp xếp toàn bộ backlog theo thứ tự $u_i / e_i$ (hoặc CVSS gốc $r_i$) giảm dần.
  2. Lần lượt duyệt từng task: gán cho team đầu tiên thỏa mãn đồng thời hai điều kiện:
     - Kỹ năng đạt chuẩn: $k_{t, \text{skill}} \ge 0.5$.
     - Dung lượng còn đủ: $\text{rem}_t \ge e_i$.
  3. Thứ tự thực thi nội bộ trong team được giữ nguyên theo thứ tự bốc việc (FIFO).
- **Ưu điểm**: Thời gian chạy cực nhanh ($< 1\text{ ms}$ cho 500 tasks), dễ cài đặt và phản ánh cách phân việc thủ công hiện nay trên Jira/GitHub Issues.
- **Điểm yếu**: Hoàn toàn "mù ngữ cảnh" (Context-blind). Gây phân mảnh context nghiêm trọng, khiến lập trình viên phải nhảy qua lại giữa nhiều repository/module khác nhau liên tục.
- **Vai trò trong nghiên cứu**: Chứng minh giải thuật đề xuất khắc phục được sự lãng phí chi phí chuyển đổi ngữ cảnh trong thực tế công nghiệp (giảm $50\% - 70\%$ chi phí $f_2$).

---

### 2.2. Baseline 2: Google OR-Tools CP-SAT (Bộ Giải Toán Học Chính Xác — Exact Ground Truth)
- **Bản chất**: Constraint Programming Solver kết hợp Boolean Satisfiability (SAT), Lazy Clause Generation và Branch-and-Bound.
- **Mô hình hóa**:
  - Giải trực tiếp mô hình toán hình thức MO-MILP:
    $$\max Z(\lambda) = f_1 - \lambda \cdot f_2$$
  - Biến quyết định nhị phân: $x_{it} \in \{0, 1\}$ (gán task cho team), $z_{ijt} \in \{0, 1\}$ (thứ tự chuyển tiếp $i \to j$) và biến MTZ $pos_{it}$ để loại trừ chu trình con.
- **Ưu điểm**: Đảm bảo nghiệm tìm được là **tối ưu toàn cục 100% (Absolute Mathematical Optimum)** nếu hội tụ trước giới hạn thời gian.
- **Điểm yếu**: Bị bùng nổ tổ hợp (Combinatorial Explosion). Với bài toán $N=500$ tasks, số biến nhị phân $z_{ijt}$ lên tới gần $2$ triệu biến, gây tràn RAM và timeout ($> 120\text{ s}$) mà không thể tìm được nghiệm khả thi.
- **Vai trò trong nghiên cứu**: Làm **Ground Truth (chuẩn tham chiếu vàng)** để đo lường khoảng cách tối ưu (Optimality Gap) của H-CSM ở quy mô vừa và nhỏ ($N \le 40$ tasks).

---

### 2.3. Baseline 3: Google OR-Tools Routing Library — Guided Local Search (Industrial Heuristic Baseline)
- **Bản chất**: Framework Heuristics & Metaheuristics chuẩn công nghiệp của Google chuyên trị bài toán VRP và Team Orienteering Problem (TOP).
- **Mô hình hóa (Capacitated Team Orienteering Problem - CTOP)**:
  - Mỗi Team $\equiv$ 1 Phương tiện (Vehicle) có trần dung lượng $\text{cap}_t$.
  - Mỗi Task $\equiv$ 1 Điểm đến (Node) có nhu cầu $\text{demand} = e_i$.
  - Chi phí cung đường (Arc Cost) = $\lambda \cdot C_{ij}$.
  - Cơ chế nhả điểm phạt (Disjunction Penalty): Nếu bỏ qua không ghé thăm task $i$, thuật toán chịu phạt đúng bằng điểm rủi ro $u_i$ $\implies$ Tương đương tối đa hóa $\sum u_i - \lambda \cdot C_{ij}$.
  - Ràng buộc kỹ năng: `routing.VehicleVar(node).SetValues([-1] + allowed_teams)`.
- **Cơ chế giải thuật**:
  - *Khởi tạo ban đầu*: `PARALLEL_CHEAPEST_INSERTION` (chèn task tham lam song song vào các team).
  - *Cải tiến nghiệm*: `GUIDED_LOCAL_SEARCH` (GLS — tìm kiếm cục bộ có hàm phạt định hướng thoát khỏi cực tiểu địa phương).
- **Ưu điểm**: Giải được quy mô lớn ($500$ tasks) trong vài giây mà không bị tràn bộ nhớ như CP-SAT. Là đối thủ metaheuristic chuẩn công nghiệp uy tín nhất.
- **Điểm yếu**: Xem các task như các tọa độ độc lập trên đồ thị mở, không nhận biết được cấu trúc nhóm cụm nguyên tử có chi phí bằng $0$ ($C_{\text{internal}} = 0$) của ngành công nghệ phần mềm, dẫn đến nghiệm dễ bị phân tán.
- **Vai trò trong nghiên cứu**: Đối sánh trực tiếp 1-1 với H-CSM ở quy mô lớn để chứng minh ưu thế của giải thuật chuyên biệt theo ngữ cảnh phần mềm (Domain-specific Matheuristic).

---

### 2.4. Baseline 4: Thuật Toán CSM Cũ (Spectral Clustering + Hungarian Matching)
- **Bản chất**: Giải thuật lai ghép phân cụm phổ đồ thị và quy hoạch gán việc.
- **Quy trình**:
  1. Chiếu ma trận khoảng cách $C_{ij}$ qua hàm nhân Gauss RBF $A_{ij} = \exp(-C_{ij}^2 / 2\sigma^2)$.
  2. Phân cụm phổ (Spectral Clustering) chia backlog thành đúng $K = M$ cụm lớn.
  3. Mô phỏng ma trận chi phí $M \times M$ và dùng giải thuật Hungarian ($O(M^3)$) để ghép cụm cho team.
  4. Cắt tỉa tham lam bên trong cụm theo dung lượng team $\text{cap}_t$.
- **Điểm nghẽn**:
  - *Mù dung lượng*: Cụm tạo ra quá to ($> 200\text{ SP}$), khi cắt tỉa làm phá vỡ hoàn toàn cấu trúc gắn kết của cụm.
  - *Ép cứng $K = M$*: Không phản ánh thực tế số lượng module phần mềm luôn nhiều hơn số đội.
  - *Sụt giảm Utility*: Bị sụt giảm tới $-26.1\%$ điểm utility so với tiềm năng tối ưu.
- **Vai trò trong nghiên cứu**: Chứng minh sự cần thiết và tính ưu việt của giải thuật đề xuất H-CSM (thay thế Spectral bằng Pure Atomic Coarsening).

---

### 2.5. Baseline 5: Proposed NSGA-II (Tiến Hóa Pareto Đa Mục Tiêu)
- **Bản chất**: Thuật toán di truyền đa mục tiêu kinh điển (Non-dominated Sorting Genetic Algorithm II).
- **Mã hóa**: Nhiễm sắc thể 2 đoạn (Đoạn 1: Team Assignment vector; Đoạn 2: Priority/Order permutation).
- **Đặc điểm**: Tự động tiến hóa qua các thế hệ để tìm tập nghiệm Pareto bao phủ đồng thời cả $f_1$ và $f_2$.
- **Điểm yếu**: Thời gian hội tụ chậm ($2 - 4\text{ giây}$ cho 100 thế hệ), nghiệm phụ thuộc vào đột biến ngẫu nhiên nên độ ổn định không cao bằng giải thuật tất định.

---

## 3. Tổng Hợp Ma Trận So Sánh Các Giải Thuật

| Tiêu chí | Greedy-CVSS | OR-Tools CP-SAT | OR-Tools Routing (GLS) | CSM Cũ (Spectral) | Proposed NSGA-II | **Proposed H-CSM** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Loại hình giải thuật** | Heuristic | Exact Solver | Metaheuristic | Matheuristic | Metaheuristic | **Matheuristic** |
| **Bảo đảm tối ưu** | Không | Tối ưu toàn cục (khi hội tụ) | Cận tối ưu (GLS) | Không | Tập nghiệm Pareto | **Cận tối ưu 97.5% CP-SAT** |
| **Tốc độ ($N=500$)** | $< 1\text{ ms}$ | Timeout ($> 120\text{ s}$) | $5 - 10\text{ s}$ | $\sim 450\text{ ms}$ | $3.4\text{ s}$ | **$39\text{ ms}$** |
| **Khảo sát Mặt Pareto** | Không (1 điểm) | Quét scalarization (rất chậm) | Quét scalarization ($> 60\text{ s}$) | Kém | Tự nhiên theo quần thể | **Quét 21 điểm trong 1.2s** |
| **Nhận biết cấu trúc Code** | Không | Không (Mô hình hóa phẳng) | Không (Coi như điểm VRP) | Bị mờ bởi Gauss RBF | Không | **Nhận biết tuyệt đối $C_{ij}=0$** |
