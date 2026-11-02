# Thiết Kế & Cài Đặt OR-Tools Routing GLS (Baseline 3: Metaheuristic)

> **Mục tiêu**: Mô hình hóa bài toán SecOps thành bài toán Định tuyến đội có dung lượng và có điểm thưởng (Capacitated Team Orienteering Problem — CTOP), giải bằng Guided Local Search (GLS).  
> **File mã nguồn**: [`src/solvers/ortools_routing.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/ortools_routing.py)

---

## 1. Tổng Quan Kiến Trúc Mô Hình Hóa (Mapping CTOP)

Hàm mục tiêu vô hướng hóa $Z(w)$ được chuyển đổi tương đương về hàm chi phí định tuyến:
$$\max Z(w) = w \cdot \frac{f_1}{\Delta f_1} - (1 - w) \cdot \frac{f_2}{\Delta f_2} \iff \max \left( f_1 - \lambda_{\text{effective}} \cdot f_2 \right)$$
với hệ số phạt tương đương $\lambda_{\text{effective}}$:
$$\lambda_{\text{effective}} = \frac{1 - w}{w} \cdot \frac{f_1^{\max} - f_1^{\min}}{f_2^{\max} - f_2^{\min}}$$

| Khái niệm trong SecOps | Ánh xạ sang OR-Tools Routing | Hàm / Cơ chế thư viện |
| :--- | :--- | :--- |
| **$M$ Đội kỹ thuật** | **$M$ Chiếc xe (Vehicles)** | `RoutingIndexManager(num_nodes, M, starts, ends)` |
| **Dung lượng Sprint (30 SP)** | **Trần tải trọng (Capacity)** | `routing.AddDimensionWithVehicleCapacity(...)` |
| **Effort task ($e_i$)** | **Tải trọng tại điểm (Demand)** | `demand_callback` qua Story Points của task |
| **Chi phí đổi ngữ cảnh ($C_{ij}$)** | **Chi phí di chuyển (Arc Cost)** | `transit_callback` = $\text{round}(C_{ij} \times \lambda_{\text{effective}} \times \text{SCALE})$ |
| **Lợi ích an ninh ($u_i$)** | **Phạt khi bỏ lỡ task (Penalty)** | `routing.AddDisjunction([node_i], scale * u_i)` |
| **Ngưỡng kỹ năng ($\ge 0.5$)** | **Xe được phép ghé thăm** | `routing.VehicleVar(node_i).SetValues([-1] + allowed)` |
| **Hành trình hở (Open Route)** | **2 Depot ảo: Start ($N$), End ($N+1$)** | Cung nối đỉnh ảo có chi phí bằng $0$ |

---

## 2. Các Giai Đoạn Mô Hình Hóa Chi Tiết

### 2.1. Hành trình hở với 2 Depot ảo (Open-TSP)
- Tạo đúng 2 đỉnh ảo: `start_depot = N` và `end_depot = N + 1` (tổng đồ thị có $N + 2$ đỉnh).
- Cả $M$ đội xuất phát từ $N$ và kết thúc tại $N+1$. Chi phí từ/về đỉnh ảo bằng $0$ (`if from_node >= N or to_node >= N: return 0`).

### 2.2. Chi phí cung đường (Arc Cost)
- Chi phí giữa 2 task thực tế $i \to j$: $\text{Cost}(i, j) = \text{round}(C_{ij} \times \lambda_{\text{effective}} \times \text{SCALE})$.
- Đăng ký qua `routing.RegisterTransitCallback` và `routing.SetArcCostEvaluatorOfAllVehicles`.

### 2.3. Kiểm soát dung lượng Sprint (Capacity Dimension)
- Tự động cộng dồn Story Points $e_i$ của các task trên hành trình thông qua `routing.AddDimensionWithVehicleCapacity(...)`.
- Nếu bước đi láng giềng làm tổng Story Points vượt quá trần tải trọng (30 SP), solver sẽ lập tức loại bỏ.

### 2.4. Điểm thưởng an ninh qua cơ chế phạt (Disjunctions)
- Thay vì bắt buộc ghé thăm tất cả các task, sử dụng `routing.AddDisjunction([node_idx], penalty = scale * u_i)`.
- Không làm task $i$ thì bị phạt đúng bằng điểm ưu tiên $u_i$. Solver tối thiểu hóa tiền phạt tương đương toán học với tối đa hóa tổng lợi ích an ninh $f_1$.

### 2.5. Khóa quyền phục vụ theo kỹ năng (VehicleVar)
- Trong OR-Tools Routing, mỗi node có một biến quyết định `VehicleVar(node_idx)` lưu ID của xe (đội) được phép ghé thăm nó.
- Ta giới hạn miền giá trị: `routing.VehicleVar(node_idx).SetValues([-1] + allowed_vehicles)`, trong đó:
  - `allowed_vehicles`: Danh sách các đội có điểm kỹ năng $\ge 0.5$ với task này (đội không đủ kỹ năng bị loại bỏ, không thể nhận task).
  - `-1`: Giá trị đặc biệt trong OR-Tools biểu thị task này bị bỏ qua (không đội nào làm).

### 2.6. Chiến lược tìm kiếm 2 pha (Parallel Insertion + GLS)
- **Pha 1**: `PARALLEL_CHEAPEST_INSERTION` — chèn việc tham lam song song tạo nghiệm ban đầu hợp lệ trong vài mili-giây.
- **Pha 2**: `GUIDED_LOCAL_SEARCH` — tìm kiếm cục bộ có hướng dẫn bằng các toán tử `2-opt`, `Relocate`, `Exchange`. Khi kẹt ở cực tiểu cục bộ, GLS tự động phạt các cung chi phí cao để thoát bẫy trong thời gian `time_limit`.

### 2.7. Trích xuất nghiệm & Đóng gói SprintPlan
- Lần theo chuỗi con trỏ `solution.Value(routing.NextVar(index))` từ `routing.Start(v_idx)` của từng đội (bỏ qua các node ảo $\ge N$).
- Đánh giá lại toàn bộ kế hoạch bằng hàm số thực `evaluate_sprint_plan(...)` để tính chuẩn xác $f_1, f_2, Z(w)$.

---

## 3. Điểm Yếu Của GLS

1. **Thao tác láng giềng chỉ xử lý đơn task (Single-task moves)**:
   - Các toán tử định tuyến của OR-Tools (`2-opt`, `Relocate`, `Exchange`) chỉ hoán đổi từng task riêng lẻ hoặc đảo đoạn giữa hai vị trí.
   - Khi xe đã đầy dung lượng (30 SP), GLS không thể thực hiện các bước chuyển phức hợp nhiều task cùng lúc (như loại bỏ 1 task lớn để nhặt đồng thời cụm nhiều task nhỏ có cùng ngữ cảnh), làm hạn chế khả năng tối ưu hóa việc chọn tập task.

2. **Hiện tượng bão hòa không gian tìm kiếm (Search Plateau)**:
   - Khi tăng thời gian tìm kiếm của GLS (từ $3\text{s}$ lên $10\text{s}$ trên $N=100$), chất lượng nghiệm hầu như đi ngang và không cải thiện thêm.
   - GLS nhanh chóng rơi vào vùng bình nguyên (search plateau), việc kéo dài thêm thời gian tính toán không mang lại lợi thế về chất lượng nghiệm.