# Mô Hình Toán Học Hình Thức (Formal Mathematical Model) — No-DAG Formulation

> **Tài liệu tham chiếu**: Ánh xạ từ mô tả nghiệp vụ tại [`problem_definition.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/no-dag/problem_definition.md).  
> **Dạng bài toán**: Quy hoạch nguyên tuyến tính đa mục tiêu (Bi-Objective Mixed-Integer Linear Programming — MO-MILP) kết hợp giữa Lựa chọn Knapsack đa đội (Multiple Knapsack Problem with Skill Constraints) và Định tuyến chuỗi công việc (Intra-Team Task Sequencing / Open-mTSP).

---

## 1. Tập Hợp & Chỉ Số (Sets & Indices)

- $\mathcal{V} = \{1, 2, \dots, N\}$: Tập hợp $N$ công việc vá lỗ hổng trong Backlog.
- $S = 0$: Nút ảo đại diện cho trạng thái **Bắt đầu Sprint** của mỗi team.
- $E = N + 1$: Nút ảo đại diện cho trạng thái **Kết thúc Sprint** của mỗi team.
- $\mathcal{V}^+ = \mathcal{V} \cup \{S, E\}$: Tập các nút mở rộng phục vụ việc định tuyến chuỗi.
- $T = \{1, 2, \dots, M\}$: Tập hợp $M$ đội kỹ thuật (Teams) tham gia Sprint.
- $\mathcal{S}_{\text{OWASP}} = \{1, 2, \dots, 10\}$: Tập hợp 10 nhóm kỹ năng an toàn thông tin chuẩn OWASP Top 10.
- $\tau \in \mathbb{Z}^+$: Chỉ số của chu kỳ Sprint hiện tại đang xét.

---

## 2. Thuộc Tính & Tham Số Đầu Vào (Attributes & Parameters)

### 2.1. Thuộc tính của Task $i \in \mathcal{V}$
- $r_i \in [0, 10]$: Điểm rủi ro kỹ thuật gốc theo chuẩn CVSS.
- $e_i \in \mathbb{Z}^+$: Ước lượng công sức thực hiện (Story Points).
- $\text{repo}_i$: Kho chứa mã nguồn của task $i$.
- $\text{mod}_i$: Phân hệ / microservice cụ thể của task $i$.
- $\text{skill}_i \in \mathcal{S}_{\text{OWASP}}$: Nhóm kỹ năng chuyên môn cần thiết.
- $\text{disc}_i \in \mathbb{Z}^+$: Sprint phát hiện lỗ hổng ($\text{disc}_i \le \tau$).
- $\text{dead}_i \in \mathbb{Z}^+$: Sprint hạn chót SLA bắt buộc phải khắc phục xong.

### 2.2. Thuộc tính của Team $t \in T$
- $\text{cap}_t \in \mathbb{Z}^+$: Dung lượng Story Points tối đa của team $t$ trong Sprint $\tau$.
- $k_{t, s} \in [0.0, 1.0]$: Điểm số thành thạo của team $t$ đối với nhóm kỹ năng $s \in \mathcal{S}_{\text{OWASP}}$.

### 2.3. Các Chỉ Số Tính Toán Dẫn Xuất (Derived Metrics)

#### 1. Điểm Lợi Ích Giảm Nhẹ Rủi Ro (Mitigation Utility — $u_i$)
$$u_i = r_i + \alpha \cdot (\tau - \text{disc}_i) + \beta \cdot \max(0, \tau - \text{dead}_i + 1)$$
Trong đó:
- $(\tau - \text{disc}_i) \ge 0$: Tuổi thọ tồn lưu (Persistence).
- $\max(0, \tau - \text{dead}_i + 1)$: Độ khẩn cấp hạn chót (Deadline Urgency).
- $\alpha > 0, \beta > 0$: Hệ số trọng số chính sách tổ chức.

#### 2. Chi Phí Chuyển Đổi Ngữ Cảnh Liên Tiếp (Context Switch Distance — $C_{ij}$)
$$C_{ij} = w_{\text{repo}} \cdot \mathbb{I}(\text{repo}_i \neq \text{repo}_j) + w_{\text{mod}} \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + w_{\text{skill}} \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j)$$
Trong đó:
- $\mathbb{I}(\cdot)$ là hàm chỉ thị.
- $w_{\text{repo}} = 0.5 > w_{\text{mod}} = 0.3 > w_{\text{skill}} = 0.2 > 0$.
- Quy ước với nút ảo: $C_{S, i} = 0, \; C_{i, E} = 0, \; C_{S, E} = 0, \; \forall i \in \mathcal{V}$.

---

## 3. Biến Quyết Định (Decision Variables)

1. **Biến Phân Bổ (Assignment Variable)**:
   $$x_{it} \in \{0, 1\}, \quad \forall i \in \mathcal{V}, \forall t \in T$$
   $$x_{it} = 1 \text{ nếu task } i \text{ được giao cho team } t \text{ trong Sprint } \tau; \text{ bằng } 0 \text{ nếu ngược lại.}$$

2. **Biến Định Tuyến Chuỗi Thứ Tự (Sequencing Variable)**:
   $$z_{ijt} \in \{0, 1\}, \quad \forall i, j \in \mathcal{V}^+, i \neq j, \forall t \in T$$
   $$z_{ijt} = 1 \text{ nếu team } t \text{ thực hiện task } i \text{ ngay trước task } j; \text{ bằng } 0 \text{ nếu ngược lại.}$$

3. **Biến Thứ Tự Vị Trí (Position Variables — MTZ Subtour Elimination)**:
   $$pos_{it} \in [0, N], \quad \forall i \in \mathcal{V}, \forall t \in T$$
   Biểu diễn số thứ tự thực hiện của task $i$ trong chuỗi công việc của team $t$.

---

## 4. Hệ Thống Ràng Buộc Toán Học (Constraints)

### 4.1. Ràng Buộc Phân Bổ & Dung Lượng (Assignment & Capacity)

1. **Gán đơn nhất & Cho phép tồn đọng backlog**:
   $$\sum_{t \in T} x_{it} \le 1, \quad \forall i \in \mathcal{V}$$

2. **Trần dung lượng Sprint của từng team (Story Point Knapsack)**:
   $$\sum_{i \in \mathcal{V}} e_i \cdot x_{it} \le \text{cap}_t, \quad \forall t \in T$$

3. **Ngưỡng năng lực kỹ năng tối thiểu (Skill Threshold $\ge 0.5$)**:
   $$x_{it} \le \mathbb{I}(k_{t, \text{skill}_i} \ge 0.5), \quad \forall i \in \mathcal{V}, \forall t \in T$$
   *(Nếu $k_{t, \text{skill}_i} < 0.5$, cố định $x_{it} = 0$ ngay từ bước tiền xử lý).*

---

### 4.2. Ràng Buộc Bảo Toàn Luồng Chuỗi (Flow Conservation)

Đảm bảo tập các task giao cho team $t$ tạo thành một đường đi đơn nhất bắt đầu từ $S$ và kết thúc tại $E$:

4. **Luồng xuất phát từ nút $S$**:
   $$\sum_{j \in \mathcal{V}} z_{Sjt} + z_{SEt} = 1, \quad \forall t \in T$$

5. **Luồng kết thúc tại nút $E$**:
   $$\sum_{i \in \mathcal{V}} z_{iEt} + z_{SEt} = 1, \quad \forall t \in T$$

6. **Bảo toàn luồng tại mỗi task $i \in \mathcal{V}$**:
   Một task $i$ nếu được giao cho team $t$ ($x_{it} = 1$) thì phải có đúng 1 cung đi vào và đúng 1 cung đi ra:
   $$\sum_{j \in \mathcal{V}^+, j \neq i} z_{jit} = x_{it}, \quad \forall i \in \mathcal{V}, \forall t \in T$$
   $$\sum_{j \in \mathcal{V}^+, j \neq i} z_{ijt} = x_{it}, \quad \forall i \in \mathcal{V}, \forall t \in T$$

---

### 4.3. Ràng Buộc Khử Chu Trình Con (Subtour Elimination — MTZ Formulation)

7. **Ràng buộc vị trí Miller-Tucker-Zemlin (MTZ)**:
   $$pos_{it} - pos_{jt} + N \cdot z_{ijt} \le N - 1, \quad \forall i, j \in \mathcal{V}, i \neq j, \forall t \in T$$
8. **Chặn vị trí tương thích với việc gán**:
   $$1 \le pos_{it} \le N \cdot x_{it}, \quad \forall i \in \mathcal{V}, \forall t \in T$$

---

## 5. Hàm Mục Tiêu Kép (Bi-Objective Functions)

### Mục Tiêu 1: Cực Đại Hóa Tổng Lợi Ích Rủi Ro Được Triệt Tiêu ($f_1$)
$$\max f_1(x) = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i \cdot x_{it}$$

### Mục Tiêu 2: Cực Tiểu Hóa Tổng Chi Phí Chuyển Đổi Ngữ Cảnh ($f_2$)
$$\min f_2(z) = \sum_{t \in T} \sum_{i \in \mathcal{V}^+} \sum_{j \in \mathcal{V}^+, j \neq i} C_{ij} \cdot z_{ijt}$$

---

## 6. Dạng Tối Ưu Hóa Đơn Trị Hóa (Scalarization via Weighted Sum)

Để tìm tập nghiệm biên Pareto hoặc nghiệm dung hòa theo chính sách của tổ chức, hàm mục tiêu tổng hợp được xác định qua tham số chuẩn hóa trọng số $\lambda \in [0, 1]$:
$$\max F_{\text{scalar}}(x, z) = f_1(x) - \lambda \cdot f_2(z)$$
Thuật toán tìm kiếm Pareto (hoặc exact solver qua $\epsilon$-constraint) sẽ quét qua các giá trị $\lambda$ khác nhau để dựng nên mặt cong Pareto chuẩn mực.
