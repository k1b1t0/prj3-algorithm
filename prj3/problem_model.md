# Mô Hình Toán Học Hình Thức: MO-MILP Lập Lịch SecOps Đa Mục Tiêu

> **Bản chất bài toán**: Quy hoạch nguyên số hỗn hợp đa mục tiêu (**Multi-Objective Mixed-Integer Linear Programming — MO-MILP**).  
> **Cấu trúc bài toán**: Tích hợp đồng thời bài toán Đóng gói ba lô đa dung lượng (**Multiple Knapsack Problem**) với bài toán Người du lịch hành trình hở (**Open Traveling Salesperson Problem — Open-TSP**) trên không gian chi phí chuyển đổi ngữ cảnh phân cấp.

---

### Bảng Ký Hiệu Toán Học (Nomenclature)

| Nhóm | Ký hiệu | Miền giá trị / Đơn vị | Ý nghĩa tóm tắt |
| :--- | :--- | :--- | :--- |
| **Chỉ số & Tập hợp** | $i, j \in \mathcal{V}$ | $1, \dots, N$ | Tập các lỗ hổng an ninh trong Backlog |
| | $t \in T$ | $1, \dots, M$ | Tập các đội kỹ thuật Scrum |
| | $S, E$ | Dummy | Đỉnh ảo bắt đầu ($S$) và kết thúc ($E$) của hành trình hở |
| **Tham số đầu vào** | $e_i$ | $\mathbb{Z}^+$ (Story Points) | Công sức ước lượng của task $i$ |
| | $\text{cap}_t$ | $\mathbb{Z}^+$ (Story Points) | Hạn mức năng lực của Đội $t$ trong Sprint |
| | $u_i(\tau)$ | $(0.0, 1.0]$ | Điểm ưu tiên giảm nhẹ rủi ro (Mitigation Utility) |
| | $C_{ij}$ | $[0.0, 1.0]$ | Chi phí chuyển đổi ngữ cảnh từ task $i$ sang $j$ |
| | $w$ | $[0.0, 1.0]$ | Trọng số cân bằng hàm vô hướng hóa $Z(w)$ |
| **Biến quyết định** | $x_{it}$ | $\{0, 1\}$ | $= 1$ nếu giao task $i$ cho Đội $t$ |
| | $z_{u, v, t}$ | $\{0, 1\}$ | $= 1$ nếu Đội $t$ làm tiếp task $v$ ngay sau $u$ |
| | $pos_{it}$ | $[0, N]$ | Thứ tự vị trí thực thi của task $i$ (triệt tiêu chu trình MTZ) |

---

## 1. Không Gian Biến Quyết Định (Decision Variables)

Cho tập backlog $N$ lỗ hổng $\mathcal{V} = \{1, 2, \dots, N\}$ và $M$ đội kỹ thuật $T = \{1, 2, \dots, M\}$.

Bổ sung cặp đỉnh ảo $\{S, E\}$ (bắt đầu và kết thúc) với chi phí chuyển đổi bằng 0: $C_{S, i} = C_{i, E} = C_{S, E} = 0$.

1. **Biến phân bổ (Assignment Variable)**:
   $$x_{it} \in \{0, 1\} \quad \forall i \in \mathcal{V}, \forall t \in T$$
   - $x_{it} = 1$: Task $i$ được giao cho Đội $t$ thực hiện trong Sprint (ngược lại bằng 0).

2. **Biến thứ tự chuyển tiếp công việc (Transition Variable)**:
   $$z_{u, v, t} \in \{0, 1\} \quad \forall u, v \in \mathcal{V} \cup \{S, E\}, \forall t \in T$$
   - $z_{u, v, t} = 1$: Đội $t$ làm xong task $u$ thì chuyển tiếp ngay sang làm task $v$ (hoặc từ điểm bắt đầu $S \to i$, hay từ task cuối $i \to E$).

3. **Biến thứ tự vị trí (MTZ Ordering Variable)**:
   $$pos_{it} \ge 0 \quad \forall i \in \mathcal{V}, \forall t \in T$$
   - Xác định số thứ tự thực thi của task $i$ trong chuỗi công việc của Đội $t$, dùng để triệt tiêu chu trình con cô lập (Subtour Elimination).

---

## 2. Các Chỉ Số Tính Toán (Computed Metrics)

### 2.1. Điểm Ưu Tiên Giảm Nhẹ Rủi Ro (Mitigation Utility — $u_i(\tau)$)
Điểm ưu tiên của task $i$ tại Sprint $\tau$ (tham khảo công thức từ VULCON) kết hợp giữa mức độ nghiêm trọng an ninh và áp lực thời gian SLA:
$$u_i(\tau) = \alpha \cdot \hat{r}_i + (1 - \alpha) \cdot \hat{p}_i(\tau) \in (0.0, 1.0]$$

- $\hat{r}_i = \frac{r_i}{10.0} \in [0.0, 1.0]$: Mức độ nghiêm trọng kỹ thuật chuẩn hóa từ điểm CVSS Base Score $r_i$.
- $\hat{p}_i(\tau) = \min\left(1.0, \max\left(0.0, \frac{\tau - \text{disc}_i}{\text{dead}_i - \text{disc}_i}\right)^\gamma\right) \in [0.0, 1.0]$: Tỷ lệ tiệm cận hạn chót SLA.
- $\alpha \in [0.0, 1.0]$: Trọng số cân bằng giữa kỹ thuật và thời gian (mặc định $\alpha = 0.6$).
- $\gamma \ge 1.0$: Hệ số lũy thừa gia tốc áp lực SLA (mặc định $\gamma = 1.5$).
- *Đặc tính*: Toàn bộ $u_i \in (0.0, 1.0]$ đồng nhất thang đo với chi phí chuyển đổi ngữ cảnh $C_{ij} \in [0.0, 1.0]$, loại bỏ hoàn toàn các hằng số phạt nhảy bậc.

### 2.2. Chi Phí Chuyển Đổi Ngữ Cảnh Phân Cấp (Context-Switching Cost — $C_{ij}$)
Khi một đội chuyển tiếp từ task $i$ sang task $j$, chi phí hao tổn tư duy và setup môi trường được mô hình hóa theo cấu trúc 3 cấp:
$$C_{ij} = w_{\text{repo}} \cdot \mathbb{I}(\text{repo}_i \neq \text{repo}_j) + w_{\text{mod}} \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + w_{\text{skill}} \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j)$$

- Trọng số chuẩn hóa: $w_{\text{repo}} + w_{\text{mod}} + w_{\text{skill}} = 1.0$ (với $w_{\text{repo}}, w_{\text{mod}}, w_{\text{skill}} \ge 0$).
  - Giá trị mặc định: $w_{\text{repo}} = 0.5$, $w_{\text{mod}} = 0.3$, $w_{\text{skill}} = 0.2$. Cặp task cùng repo, cùng module, cùng skill có $C_{ij} = 0.0$.

---

## 3. Hàm Mục Tiêu Tối Ưu Hóa (Bi-Objective Criteria)

1. **Mục tiêu 1: Cực đại hóa Lợi ích Giảm nhẹ Rủi ro ($f_1$ - Mitigation Utility)**
   $$\max f_1 = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i(\tau) \cdot x_{it}$$

2. **Mục tiêu 2: Cực tiểu hóa Chi phí Chuyển đổi Ngữ cảnh ($f_2$ - Context-Switching Cost)**
   $$\min f_2 = \sum_{t \in T} \sum_{i \in \mathcal{V}} \sum_{j \in \mathcal{V}, j \neq i} C_{ij} \cdot z_{ijt}$$

3. **Hàm vô hướng hóa chuẩn hóa (Normalized Weighted Sum)**:
   Chuẩn hóa giá trị hai hàm mục tiêu về cùng đoạn $[0.0, 1.0]$ để loại bỏ chênh lệch thang đo:
   $$\hat{f}_1 = \frac{f_1 - f_1^{\min}}{f_1^{\max} - f_1^{\min}}, \quad \hat{f}_2 = \frac{f_2 - f_2^{\min}}{f_2^{\max} - f_2^{\min}}$$
   $$\max Z(w) = w \cdot \hat{f}_1 - (1 - w) \cdot \hat{f}_2 \quad (w \in [0.0, 1.0])$$
   *Bộ cận tĩnh (Static Bounds)*:
   - $f_1^{\min} = 0$, $f_1^{\max}$: Nghiệm Fractional Knapsack với tổng dung lượng $\sum \text{cap}_t$.
   - $f_2^{\min} = 0$, $f_2^{\max} = K_{\max} - M$ (số task tối đa nhặt được theo greedy effort nhỏ nhất trừ đi số đội $M$).

---

## 4. Ràng Buộc (Formal Constraints)

### 4.1. Ràng Buộc Nghiệp Vụ & Năng Lực (Assignment & Capacity)

1. **Gán đơn nhất (Single Assignment)**:
   $$\sum_{t \in T} x_{it} \le 1 \quad \forall i \in \mathcal{V}$$
   Mỗi lỗ hổng chỉ được gán tối đa cho một đội hoặc lưu lại backlog.

2. **Trần dung lượng Sprint (Knapsack Capacity Limit)**:
   $$\sum_{i \in \mathcal{V}} e_i \cdot x_{it} \le \text{cap}_t \quad \forall t \in T$$
   Tổng Story Points các task được giao cho Đội $t$ không được vượt quá hạn mức Sprint.

3. **Ngưỡng năng lực kỹ năng (Skill Feasibility)**:
   $$x_{it} \le \mathbb{I}(k_{t, \text{skill}_i} \ge 0.5) \quad \forall i \in \mathcal{V}, \forall t \in T$$
   Đội $t$ chỉ được nhận task $i$ nếu điểm kỹ năng trên phân loại OWASP của task đó đạt chuẩn $\ge 0.5$.

### 4.2. Ràng Buộc Cấu Trúc Chuỗi Tuyến Tính Hở (Open-TSP & Subtour Elimination)

Mỗi đội $t$ sở hữu một chuỗi thực thi tuyến tính hở $\pi_t$ bắt đầu từ đỉnh ảo $S$ và kết thúc tại đỉnh ảo $E$.

1. **Bảo toàn luồng tại các đỉnh ảo (Depot Flow Conservation)**:
   Mỗi đội $t$ luôn có đúng một luồng rời khỏi đỉnh xuất phát $S$ và đúng một luồng đi vào đỉnh kết thúc $E$:
   $$\sum_{i \in \mathcal{V}} z_{S, i, t} + z_{S, E, t} = 1 \quad \forall t \in T$$
   $$\sum_{i \in \mathcal{V}} z_{i, E, t} + z_{S, E, t} = 1 \quad \forall t \in T$$
   - Khi $z_{S, E, t} = 1$: Đội $t$ không được phân bổ bất kỳ task nào trong Sprint ($\sum_{i \in \mathcal{V}} x_{it} = 0$).

2. **Bảo toàn luồng công việc tại từng Task (Task Degree Conservation)**:
   Một task $i \in \mathcal{V}$ nếu được giao cho Đội $t$ ($x_{it} = 1$) thì bắt buộc phải có đúng một cung đi vào và đúng một cung đi ra:
   $$z_{S, i, t} + \sum_{j \in \mathcal{V}, j \neq i} z_{j, i, t} = x_{it} \quad \forall i \in \mathcal{V}, \forall t \in T$$
   $$z_{i, E, t} + \sum_{j \in \mathcal{V}, j \neq i} z_{i, j, t} = x_{it} \quad \forall i \in \mathcal{V}, \forall t \in T$$

3. **Neo thứ tự vị trí & Triệt tiêu chu trình con MTZ (MTZ Subtour Elimination)**:
   Biến vị trí $pos_{it} \ge 0$ được dùng để loại bỏ hoàn toàn các chu trình con cô lập tách rời khỏi đường đi chính:
   - Nếu $x_{it} = 0$: $pos_{it} = 0$.
   - Nếu $x_{it} = 1$: $1 \le pos_{it} \le |\mathcal{V}|$, với task đầu tiên sau $S$ được neo tại vị trí 1:
     $$pos_{it} = 1 \quad \text{nếu } z_{S, i, t} = 1$$
   - Mỗi bước chuyển tiếp giữa 2 task $i \to j$ làm tăng số thứ tự vị trí ít nhất 1 đơn vị:
     $$pos_{jt} \ge pos_{it} + 1 - |\mathcal{V}| \cdot (1 - z_{i, j, t}) \quad \forall i, j \in \mathcal{V} (i \neq j), \forall t \in T$$
     $$x_{it} \le pos_{it} \le |\mathcal{V}| \cdot x_{it} \quad \forall i \in \mathcal{V}, \forall t \in T$$

---

## 5. Phân Tích Độ Phức Tạp & Điểm Nghẽn Tính Toán

1. **Bản chất NP-hard**:
   - Bài toán là sự kết hợp của Multiple 0-1 Knapsack (chọn tập tối ưu $x_{it}$) và Open-TSP đa phương tiện (định tuyến chuỗi $z_{ijt}$).
2. **Bùng nổ tổ hợp của Bộ giải Chính xác (Exact Solvers / CP-SAT)**:
   - Số lượng biến nhị phân chuỗi chuyển tiếp: $M \times N \times (N - 1) = O(M \cdot N^2)$.
   - Với quy mô nhỏ ($N=40, M=2$): $\approx 3.120$ biến $z_{ijt}$ $\implies$ CP-SAT giải tối ưu trong $\approx 15\text{ s}$.
   - Với quy mô lớn ($N=500, M=8$): $\approx 2.000.000$ biến nhị phân $z_{ijt}$ cùng hàng triệu ràng buộc MTZ $\implies$ CP-SAT bị tràn bộ nhớ và timeout ($> 90\text{ s}$ không ra nghiệm).
3. **Động lực ra đời của Thuật toán Đề xuất H-CSM**:
   - Tách bài toán thành các pha phân cấp: Gom cụm nguyên tử $C_{ij} = 0$ để nén không gian tìm kiếm, đóng gói Pareto và giải Open-TSP trên các khối siêu đỉnh (Super-Nodes $B \le 10$) bằng Quy hoạch động Bitmask DP trong thời gian vài mili-giây.

