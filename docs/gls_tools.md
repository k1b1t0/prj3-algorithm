# Cơ Sở Lý Thuyết & Cơ Chế Hoạt Động Của Guided Local Search (GLS) & OR-Tools Routing

> **Mục đích**: Tài liệu hóa nền tảng toán học, cơ chế hoạt động tầng thấp và kiến trúc giải thuật của metaheuristic **Guided Local Search (GLS)** cùng thư viện **Google OR-Tools Routing Library**.  
> **Tài liệu cài đặt mã nguồn**: Tham khảo [`gls_implementation.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/gls_implementation.md) và mã nguồn tại [`src/solvers/ortools_routing.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/ortools_routing.py).

---

## 1. Tổng Quan Về Local Search & Vấn Đề Cực Tiểu Cục Bộ

Trong tối ưu hóa tổ hợp (Combinatorial Optimization), các phương pháp tìm kiếm cục bộ (*Local Search - LS*) bắt đầu từ một nghiệm khởi tạo $s \in \mathcal{S}$ và liên tục di chuyển sang một nghiệm láng giềng $s' \in \mathcal{N}(s)$ có chất lượng tốt hơn:
$$s \leftarrow \arg\min_{s' \in \mathcal{N}(s)} g(s')$$

```
  Hàm mục tiêu g(s)
       ▲
       │        Local Minimum 1
       │          (Bẫy cực tiểu)
       │              ▼           Global Optimum
       │            \   /            (Cực trị toàn cục)
       │             \_/                  ▼
       │      \     /   \                \     /
       │       \___/     \________________\___/
       └──────────────────────────────────────────► Không gian nghiệm S
```

### Điểm nghẽn Cực tiểu cục bộ (Local Minima Trap)
Khi thuật toán đạt tới trạng thái mà **mọi nghiệm láng giềng $s' \in \mathcal{N}(s)$ đều có chi phí cao hơn hoặc bằng $s$** ($g(s') \ge g(s)$), phương pháp Hill-Climbing đơn thuần sẽ bị kẹt cứng và không thể di chuyển tiếp.

### So sánh các hướng tiếp cận Metaheuristic thoát bẫy
Để vượt qua điểm nghẽn này, các trường phái metaheuristic kinh điển sử dụng các chiến lược khác nhau:

| Metaheuristic | Chiến lược thoát bẫy | Cơ chế cốt lõi |
| :--- | :--- | :--- |
| **Simulated Annealing (SA)** | Chấp nhận bước đi tồi hơn có điều kiện | Xác suất Boltzmann $P = e^{-\Delta g / T}$ (nhiệt độ giảm dần $T \to 0$). |
| **Tabu Search (TS)** | Cấm quay lại vết cũ | Sử dụng danh sách cấm (*Tabu List*) để khóa các toán tử hoặc trạng thái vừa đi qua trong $k$ bước. |
| **Guided Local Search (GLS)** | **Thay đổi cảnh quan hàm mục tiêu** | Phạt (*Penalize*) các đặc trưng xấu có trong nghiệm hiện tại, biến cực tiểu cục bộ thành đỉnh đồi để đẩy bộ tìm kiếm đi tiếp. |

---

## 2. Nguyên Lý Toán Học Của Guided Local Search (GLS)

Được đề xuất bởi Christos Voudouris và Edward Tsang (1999), **Guided Local Search** là một metaheuristic thông minh nằm ở tầng trên (*higher-level meta-algorithm*), điều khiển một thuật toán Local Search cơ sở ở tầng dưới.

### 2.1. Đặc trưng của lời giải (Solution Features)
Một bài toán được phân rã thành tập hợp các đặc trưng tiềm năng $\{f_1, f_2, \dots, f_M\}$.
- Trong bài toán định tuyến (VRP/TSP), một đặc trưng $f_i$ thường đại diện cho một **cung đường chuyển tiếp** giữa hai điểm: $(u \to v)$.
- Hàm chỉ thị đặc trưng:
  $$I_i(s) = \begin{cases} 1 & \text{nếu đặc trưng } f_i \text{ xuất hiện trong nghiệm } s \\ 0 & \text{ngược lại} \end{cases}$$
- Mỗi đặc trưng có một chi phí gốc $c_i$ (ví dụ: độ dài hoặc chi phí chuyển đổi giữa hai đỉnh $u$ và $v$).

### 2.2. Hàm mục tiêu tăng cường (Augmented Objective Function)
Thay vì tìm kiếm trên hàm mục tiêu gốc $g(s)$, GLS biến đổi bề mặt không gian tìm kiếm bằng cách bổ sung một số hạng phạt (*Penalty term*):
$$h(s) = g(s) + \lambda \sum_{i=1}^M p_i \cdot I_i(s)$$

Trong đó:
- $g(s)$: Hàm mục tiêu chi phí gốc cần tối thiểu hóa.
- $p_i$: Số lần phạt tích lũy (*Penalty count*) của đặc trưng $f_i$ (khởi tạo bằng $0$).
- $\lambda$: Hệ số phạt tổng quát (tham số cân bằng giữa mục tiêu gốc và áp lực thoát bẫy).

### 2.3. Tiện ích phạt (Penalty Utility)
Khi Local Search cơ sở bị kẹt tại một cực tiểu cục bộ $s^*$, GLS sẽ kích hoạt cơ chế can thiệp. Thay vì phạt ngẫu nhiên, GLS tính toán **Độ tiện ích của việc phạt** cho từng đặc trưng đang có mặt trong nghiệm $s^*$:
$$\text{util}(s^*, f_i) = I_i(s^*) \cdot \frac{c_i}{1 + p_i}$$

**Ý nghĩa toán học**:
- **Tập trung vào chi phí cao ($c_i$ lớn)**: Các cung đường quá dài hoặc các bước chuyển đổi quá tốn kém sẽ có độ tiện ích cao, cần bị phạt ưu tiên.
- **Tránh phạt lặp lại quá mức ($1 + p_i$ ở mẫu số)**: Ngăn chặn việc một đặc trưng bị phạt liên tục vô hạn lần, giúp giải phóng các đặc trưng khác và tạo ra sự đa dạng hóa (*Diversification*) cho không gian tìm kiếm.

### 2.4. Chu trình điều khiển GLS (Algorithmic Loop)
1. **Khởi tạo**: Đặt $p_i = 0 \quad \forall i$. Khởi tạo nghiệm ban đầu $s_0$.
2. **Local Search cơ sở**: Thực hiện tìm kiếm láng giềng tối ưu hóa hàm tăng cường $h(s)$ cho đến khi đạt cực tiểu cục bộ $s^*$.
3. **Phạt đặc trưng**:
   - Tính $\text{util}(s^*, f_i)$ cho tất cả các đặc trưng trong $s^*$.
   - Tìm đặc trưng có tiện ích cao nhất:
     $$f^* = \arg\max_{f_i} \text{util}(s^*, f_i)$$
   - Tăng mức phạt: $p_{f^*} \leftarrow p_{f^*} + 1$.
4. **Cập nhật hàm mục tiêu**: Hàm $h(s)$ được cập nhật giá trị mới. Điểm $s^*$ lúc này không còn là cực tiểu của $h(s)$ nữa vì chi phí của nó đã bị đội lên $\lambda$.
5. **Tiếp tục Local Search**: Bộ giải tiếp tục lặp lại từ bước 2 cho đến khi hết thời gian chạy (*Time Limit*).

---

## 3. Kiến Trúc Bộ Giải OR-Tools Routing Library

Google OR-Tools Routing Engine được xây dựng chuyên biệt trên nền tảng **Constraint-Based Local Search (CBLS)**.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                 OR-TOOLS ROUTING PIPELINE                   │
       │                                                             │
       │  ┌───────────────────────────────────────────────────────┐  │
       │  │ Phase 1: First Solution Strategy (Khởi tạo)           │  │
       │  │ (Parallel Cheapest Insertion, Clarke-Wright Savings)  │  │
       │  └──────────────────────────┬────────────────────────────┘  │
       │                             │ s_0                           │
       │                             ▼                               │
       │  ┌───────────────────────────────────────────────────────┐  │
       │  │ Phase 2: Local Search Metaheuristic (GLS Engine)      │  │
       │  │ ┌─────────────────────────┐ ┌───────────────────────┐ │  │
       │  │ │ Neighborhood Operators  │ │ Penalty Management    │ │  │
       │  │ │ (2-opt, Relocate, Exch) │ │ (Augmented Cost h(s)) │ │  │
       │  │ └─────────────────────────┘ └───────────────────────┘ │  │
       │  └───────────────────────────────────────────────────────┘  │
       └─────────────────────────────────────────────────────────────┘
```

### 3.1. Pha 1: Heuristics Khởi Tạo Nghiệm Ban Đầu (First Solution Strategy)
Trước khi chạy GLS, OR-Tools cần một nghiệm xuất phát khả thi $s_0$:
- **`PARALLEL_CHEAPEST_INSERTION`**: Duyệt song song tất cả các xe (đội thợ). Tại mỗi bước, tìm đỉnh chưa ghé thăm có chi phí chèn thêm vào hành trình là nhỏ nhất và chèn vào xe tương ứng.
- **`PATH_CHEAPEST_INSERTION`**: Xây dựng tuần tự từng hành trình một cho đến khi đầy tải rồi mới chuyển sang xe tiếp theo.
- **`SAVINGS` (Clarke-Wright)**: Tính toán lượng chi phí tiết kiệm được khi ghép hai hành trình đơn lẻ $(0 \to i \to 0)$ và $(0 \to j \to 0)$ thành hành trình chung $(0 \to i \to j \to 0)$.

### 3.2. Hệ Thống Toán Tử Láng Giềng VRP Chuyên Biệt (Neighborhood Operators)
Để khám phá không gian nghiệm, bộ giải thực hiện các phép biến đổi hình học trên các chuỗi cung đường:

1. **Toán tử nội bộ hành trình (Intra-route Operators)**:
   - **`2-opt`**: Cắt bỏ hai cung không liền kề và đảo ngược đoạn đường con ở giữa để triệt tiêu các đoạn đường bắt chéo.
   - **`Or-opt`**: Cắt một chuỗi liên tiếp gồm 1, 2 hoặc 3 đỉnh và chèn sang một vị trí khác trên cùng hành trình.
2. **Toán tử liên hành trình (Inter-route Operators)**:
   - **`Relocate`**: Rút 1 đỉnh từ lộ trình của xe $A$ và chèn vào vị trí tối ưu trên lộ trình của xe $B$.
   - **`Exchange`**: Hoán đổi vị trí của 1 đỉnh thuộc xe $A$ với 1 đỉnh thuộc xe $B$.
   - **`Cross-Exchange`**: Cắt hai phân đoạn con từ hai xe khác nhau và hoán đổi vị trí cho nhau.

### 3.3. Quản Lý Ràng Buộc Bằng Đại Lượng Kích Thước (Dimensions)
Để kiểm soát các ràng buộc tích lũy dọc theo hành trình (sức chứa, thời gian, cửa sổ thời gian):
- **`RoutingDimension`**: Tự động duy trì các biến trạng thái tích lũy tại mỗi nút:
  $$\text{CumulVar}(j) \ge \text{CumulVar}(i) + \text{TransitValue}(i, j)$$
- **Disjunctions (Prize-Collecting / Optional Nodes)**:
  Với bài toán Orienteering hoặc Knapsack, không phải đỉnh nào cũng bắt buộc ghé thăm. OR-Tools hỗ trợ `AddDisjunction([node], penalty)`:
  - Nếu xe ghé thăm `node`: Hệ thống tính chi phí di chuyển cung đường.
  - Nếu `node` bị bỏ qua (*dropped*): Hệ thống cộng thêm một khoản phạt `penalty` vào hàm mục tiêu.

---

## 4. Điểm Mạnh, Hạn Chế & Hiện Tượng "Bẫy Knapsack"

### 4.1. Điểm mạnh
- **Tốc độ thực thi cực nhanh trên bài toán định tuyến**: Tìm kiếm cục bộ có định hướng giúp giải quyết các bài toán VRP thực tế từ hàng trăm đến hàng nghìn điểm dừng chỉ trong vài giây.
- **Duy trì chuỗi hành trình mượt mà**: Rất mạnh trong việc giảm thiểu tổng chi phí di chuyển hoặc chi phí chuyển đổi ngữ cảnh ($f_2$).

### 4.2. Hạn chế cấu trúc: Hiện tượng "Bẫy Knapsack" (Knapsack Trap)
Khi giải bài toán **Capacitated Team Orienteering Problem (CTOP)** — bài toán kết hợp đồng thời giữa:
1. **Bài toán Ba lô (Knapsack Problem)**: Quyết định chọn tập con các task nào để đưa vào Sprint sao cho tối đa hóa tổng giá trị $f_1$.
2. **Bài toán Định tuyến (TSP/Routing Problem)**: Sắp xếp thứ tự các task đã chọn sao cho tối thiểu hóa chi phí chuyển đổi $f_2$.

GLS bộc lộ điểm yếu cố hữu:
- **Thiếu toán tử tổ hợp đa phần tử (*Multi-item swap operator*)**: Các toán tử VRP cổ điển (`Relocate`, `Exchange`, `2-opt`) được thiết kế để di chuyển hoặc hoán đổi 1-1 giữa các đỉnh.
- **Kẹt cứng khi đầy tải**: Khi các xe đã đầy tải trọng (ví dụ đầy 30 SP), toán tử `Relocate` không thể chèn thêm task mới. Để đưa được 3 task nhỏ (mỗi task 1 SP) vào xe, hệ thống bắt buộc phải loại bỏ đồng thời 1 task to (3 SP). Các toán tử láng giềng VRP đơn lẻ không thể thực hiện bước chuyển phức hợp này trong một bước đi, khiến thuật toán **bị kẹt vĩnh viễn trong cấu trúc tập task ban đầu** do bộ khởi tạo chọn ra.

---

## 5. Tham Chiếu

1. Voudouris, C., & Tsang, E. (1999). *Guided local search and its application to the traveling salesman problem*. European Journal of Operational Research, 113(2), 469-499.
2. Kilby, P., Prosser, P., & Shaw, P. (1999). *Guided local search for the vehicle routing problem with time windows*. Meta-heuristics: Advances and trends in local search paradigms for optimization, 473-486.
3. Perron, L., & Furnon, V. *OR-Tools Routing Library*. Google LLC.
4. Cài đặt chi tiết mô hình hóa cho bài toán SecOps: [`gls_implementation.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/gls_implementation.md).

