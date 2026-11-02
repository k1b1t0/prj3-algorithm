# Thiết Kế & Cài Đặt Thuật Toán Đề Xuất H-CSM

> **Mục tiêu**: Hiện thực hóa thuật toán đề xuất H-CSM (Hierarchical Cluster-Simulate-Match) theo kiến trúc điều phối 3 pha độc lập, đạt tốc độ thực thi siêu tốc (< 25ms) và chất lượng tiệm cận nghiệm chính xác.  
> **Thư mục mã nguồn**: `prj3-algorithm/src/solvers/proposed_hcsm/`

---

## 1. Cấu Trúc Các Module Triển Khai

Tất cả các module con được thiết kế theo nguyên tắc **Pure Functions** (chỉ tiếp nhận input và trả output, tuyệt đối không chứa cờ thí nghiệm hay logic logging rườm rà). Toàn bộ logic kết nối do lớp điều phối `ProposedHCSMSolver` trong `solver.py` quản lý.

| Pha trong thuật toán | File code | Hàm cốt lõi | Input dữ liệu | Output trả về | Vai trò & Trách nhiệm chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Điều phối chung** | `solver.py` | `ProposedHCSMSolver.solve()` | `tasks: List[Task]`<br>`teams: List[Team]`<br>`w: float` | `SprintPlan` | Điều phối tuần tự qua 4 methods của 3 pha, đóng gói nghiệm hoàn chỉnh |
| **Pha 1: Phân cụm & 1D DP** | `clustering_dp.py` | `partition_clusters()` | `tasks: List[Task]`<br>`max_cap: int` (30 SP) | `List[Cluster]` | Gom nhóm task có $C_{ij}=0$, giải 1D Knapsack DP tính trước tập task tối ưu cho mọi $c \in [0, \text{cap}_{\max}]$ |
| **Pha 2: Phân bổ cụm** | `allocation.py`<br>`path_insertion.py` | `allocate_clusters_to_teams()` | `clusters: List[Cluster]`<br>`teams: List[Team]`<br>`w: float`, bounds $(f_1^{\max}, f_2^{\max})$ | `team_paths: Dict[str, List[Cluster]]`<br>`team_tasks: Dict[str, List[Task]]`<br>`team_rem_cap: Dict[str, int]` | Quét bộ $(b, c, t)$ có $\eta$ lớn nhất, tự động chèn đường đi rẻ nhất $\Delta C$, phân bổ task cho từng đội |
| **Pha 3.1: Hoán đổi liên đội** | `inter_team_swap.py` | `swap_inter_team_clusters()` | `team_tasks: Dict[str, List[Task]]`<br>`teams: List[Team]` | `team_tasks: Dict[str, List[Task]]` | Thử 1-0 Relocate và 1-1 Block Swap giữa các cặp đội để gom gọn các cụm chung repo về 1 đội |
| **Pha 3.2: Định tuyến chuỗi** | `task_sequencing.py` | `sequence_team_tasks()` | `tasks: List[Task]` (của 1 đội) | `ordered_tasks: List[Task]` | Giải Bitmask DP tìm thứ tự tối ưu tuyệt đối giữa các cụm ($K \le 12$), xếp task nội bộ cụm theo $u_i / e_i$ |

---

## 2. Chi Tiết Triển Khai Kỹ Thuật Từng Pha

### 2.1. Pha 1: Gom Cụm $C_{ij}=0$ & Lập Bảng DP (`clustering_dp.py`)
- **Gom nhóm**: Duyệt toàn bộ task trong backlog, băm theo khóa tuple `(repository, asset_module, skill)`. Các task cùng khóa được gom vào đối tượng `Cluster`.
- **Hàm `Cluster.compute_dp(max_cap)`**:
  - Dùng mảng 1D `dp[w] = (utility, [tasks])` kích thước `max_cap + 1` (31 phần tử).
  - Duyệt qua từng task trong cụm, cập nhật `dp[w]` từ trên xuống dưới (`range(limit, eff - 1, -1)`).
  - Ép tính đơn điệu: $\Phi(c) \ge \Phi(c - 1)$, đảm bảo dung lượng tăng thì utility không giảm.
- **Hàm `remove_tasks(subset)`**: Khi các task đã được phân bổ cho 1 đội, cụm lập tức xóa bỏ các task này và chạy lại `compute_dp` trên các task còn lại để phục vụ bước tiếp theo.

### 2.2. Pha 2: Phân Bổ Cụm Task Cho Từng Đội (`allocation.py`, `path_insertion.py`)
- Vòng lặp `while True`:
  - Quét qua mọi đội còn dung lượng trống $\text{rem}_t > 0$.
  - Với mỗi đội, duyệt qua các cụm $G_b$ hợp lệ theo ngưỡng kỹ năng: $k_{t, \text{skill}} \ge 0.5$.
  - Gọi `compute_path_insertion_cost(cl, current_path)` từ `path_insertion.py` để tính chi phí chèn thêm cụm vào chuỗi: $\Delta C$ và vị trí chèn tốt nhất `best_pos`.
  - Duyệt qua các mức dung lượng khả thi $c \in [1, \min(\text{effort}, \text{rem}_t)]$ trong bảng DP của cụm.
  - Tính mật độ đóng góp:
    $$\eta = \frac{w \cdot (\Phi_b(c) / f_1^{\max}) - (1 - w) \cdot (\Delta C / f_2^{\max})}{c}$$
  - Chọn bộ $(b^*, c^*, t^*)$ có $\eta > 0$ cao nhất:
    - Gán danh sách task tương ứng cho đội $t^*$, trừ dung lượng $\text{rem}_{t^*}$.
    - Chèn cụm vào chuỗi hành trình của đội $t^*$ tại vị trí `pos_star`.
    - Gọi `cl_star.remove_tasks(...)` cập nhật lại bảng DP cho phần dư.
- Dừng vòng lặp khi không còn ứng viên nào có $\eta > 0$ hoặc tất cả các đội đã hết dung lượng.

### 2.3. Pha 3.1: Hoán Đổi Cụm Giữa Hai Đội (`inter_team_swap.py`)
- Quét qua từng cặp đội $(t_1, t_2)$:
  - **1-0 Relocate**: Thử nhấc 1 cụm của $t_1$ ném sang $t_2$. Nếu $t_2$ đủ chỗ, đủ kỹ năng và tổng chi phí $\text{Cost}(t_1) + \text{Cost}(t_2)$ giảm xuống thì chấp nhận.
  - **1-1 Block Swap**: Thử đổi chéo 1 cụm của $t_1$ với 1 cụm của $t_2$. Kiểm tra điều kiện dung lượng bù trừ:
    $\text{used}_1 - \text{eff}_1 + \text{eff}_2 \le \text{cap}_1$ và $\text{used}_2 - \text{eff}_2 + \text{eff}_1 \le \text{cap}_2$.
    Nếu cả 2 đội đều đủ kỹ năng và chi phí chuyển đổi giảm $\implies$ thực hiện hoán đổi.
- Chạy lặp tối đa 3 lượt (passes < 3) hoặc dừng khi không còn nước đi cải thiện.

### 2.4. Pha 3.2: Định Tuyến Chuỗi Thực Thi (`task_sequencing.py`)
- Sau khi chốt danh sách task của đội, gom các task theo cụm và tính ma trận khoảng cách giữa các cụm.
- **Nếu số cụm $K \le 12$**:
  - Dùng thuật toán **Bitmask DP** (Quy hoạch động trạng thái bit):
    `dp[(mask, u)]` lưu chi phí nhỏ nhất để đi qua tập cụm biểu diễn bởi `mask` và kết thúc tại cụm `u`.
    Độ phức tạp $O(2^K \cdot K^2)$ chạy trong $< 0.1\text{ ms}$, cam kết đường đi Hamilton hở tối ưu tuyệt đối 100%.
- **Nếu số cụm $K > 12$**:
  - Fallback sang sắp xếp phân cấp theo repo $\to$ module $\to$ skill để đảm bảo tốc độ.
- **Bên trong từng cụm**: Sắp xếp các task thành phần theo mật độ utility $u_i / e_i$ giảm dần (vì giữa chúng $C_{ij} = 0$, thứ tự nội bộ không ảnh hưởng tới $f_2$ mà tối ưu hóa tiến độ hoàn thành rủi ro sớm nhất).

---

## 3. Kiến Trúc Điều Phối Trong `ProposedHCSMSolver` (`solver.py`)

Toàn bộ luồng xử lý được tách thành 4 methods chuyên biệt:
```python
class ProposedHCSMSolver(BaseSolver):
    def run_phase1(self, tasks, max_cap, current_sprint) -> List[Cluster]:
        return partition_clusters(tasks, max_cap, current_sprint)

    def run_phase2(self, clusters, teams, w, bounds, skill_thresh, current_sprint) -> Dict[str, List[Task]]:
        _, team_tasks, _ = allocate_clusters_to_teams(clusters, teams, w, bounds.f1_max, bounds.f2_max, skill_thresh, current_sprint)
        return team_tasks

    def run_phase3_swap(self, team_tasks, teams, skill_thresh) -> Dict[str, List[Task]]:
        return swap_inter_team_clusters(team_tasks, teams, skill_thresh, self.w_repo, self.w_mod, self.w_skill)

    def run_phase3_sequencing(self, tasks, current_sprint) -> List[Task]:
        return sequence_team_tasks(tasks, current_sprint, self.w_repo, self.w_mod, self.w_skill)

    def solve(self, tasks, teams, current_sprint=4, w=None, bounds=None, **kwargs) -> SprintPlan:
        # 1. Tinh bounds static
        # 2. clusters = self.run_phase1(...)
        # 3. team_tasks = self.run_phase2(...)
        # 4. team_tasks = self.run_phase3_swap(...)
        # 5. ordered_tasks = self.run_phase3_sequencing(...) cho tung doi
        # 6. return evaluate_sprint_plan(...)
```

---

## 4. Cơ Chế Thử Nghiệm Bóc Tách (Ablation Study) Chuẩn OOP

Nhờ kiến trúc module hóa sạch sẽ trên, việc bóc tách hay thử nghiệm từng pha không cần phải thêm cờ (`flag`) hay chèn log vào code lõi:

### Cách 1: Tạo Lớp Con (Subclass) Để Override Bất Kỳ Pha Nào
Khi muốn kiểm tra hiệu quả khi **loại bỏ** hoặc **thay thế** một pha:

```python
# Ví dụ 1: Thử nghiệm bỏ qua Pha 3.1 (không hoán đổi cụm giữa các đội)
class NoSwapSolver(ProposedHCSMSolver):
    def run_phase3_swap(self, team_tasks, teams, skill_thresh):
        return team_tasks  # Giữ nguyên phân bổ từ Pha 2, không swap

# Ví dụ 2: Thử nghiệm bỏ qua Bitmask DP ở Pha 3.2 (không định tuyến tối ưu)
class NoRoutingSolver(ProposedHCSMSolver):
    def run_phase3_sequencing(self, tasks, current_sprint):
        return tasks  # Giữ nguyên thứ tự ban đầu
```

### Cách 2: Gọi Trực Tiếp Từng Pha Để Kiểm Tra Input / Output Độc Lập
Nếu muốn lấy trực tiếp dữ liệu sau từng bước:
```python
solver = ProposedHCSMSolver()

# 1. Lấy kết quả phân cụm sau Pha 1
clusters = solver.run_phase1(tasks, max_cap=30, current_sprint=4)

# 2. Lấy kết quả phân bổ sau Pha 2
team_tasks = solver.run_phase2(clusters, teams, w=0.5, bounds=bounds, skill_thresh=0.5, current_sprint=4)

# 3. Lấy kết quả hoán đổi sau Pha 3.1
team_tasks_swapped = solver.run_phase3_swap(team_tasks, teams, skill_thresh=0.5)

# 4. Lấy kết quả sắp xếp chuỗi sau Pha 3.2
ordered_tasks = solver.run_phase3_sequencing(team_tasks_swapped["team_1"], current_sprint=4)
```

---

## 5. Lộ Trình Đọc & Kiểm Tra Code Chi Tiết (Code Review Checklist)

Để nắm bắt toàn diện thuật toán một cách trực quan nhất, nên kiểm tra code theo lộ trình tuần tự:

1. **[`solver.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/solver.py)**: Xem cách lớp `ProposedHCSMSolver` nhận input, định nghĩa 4 methods tương ứng với các pha và ghép thành luồng hoàn chỉnh trong `solve()`.
2. **[`clustering_dp.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/clustering_dp.py)**: Xem cấu trúc đối tượng `Cluster` và thuật toán 1D 0-1 Knapsack DP giải trước $\Phi_b(c)$ cho từng cụm.
3. **[`path_insertion.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/path_insertion.py)**: Xem cách tính khoảng cách ngữ cảnh giữa 2 cụm và thuật toán tìm vị trí chèn tốt nhất vào chuỗi hành trình.
4. **[`allocation.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/allocation.py)**: Xem vòng lặp tham lam chọn bộ $(b, c, t)$ có mật độ đóng góp $\eta$ lớn nhất để phân bổ task cho các đội.
5. **[`inter_team_swap.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/inter_team_swap.py)**: Xem cơ chế 1-0 Relocate và 1-1 Block Swap nhằm giảm $f_2$ mà giữ nguyên $f_1$.
6. **[`task_sequencing.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/task_sequencing.py)**: Xem thuật toán Bitmask DP Open-TSP sắp xếp chuỗi cụm và logic sắp xếp nội bộ task theo $u_i / e_i$.
