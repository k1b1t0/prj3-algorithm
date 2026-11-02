# Mô Hình Toán Học Hình Thức (Formal Mathematical Model) — Project 3

> **Tài liệu tham chiếu**: Ánh xạ 1-1 từ mô tả nghiệp vụ tại [`problem_definition.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/problem_definition.md).  
> **Dạng bài toán**: Quy hoạch nguyên tuyến tính đa mục tiêu (Bi-Objective Mixed-Integer Linear Programming — MO-MILP) kết hợp giữa Lựa chọn Knapsack (Multiple Knapsack Problem) và Định tuyến chuỗi công việc (Task Sequencing with Precedence Constraints).

---

## 1. Tập Hợp & Chỉ Số (Sets & Indices)

- $\mathcal{V} = \{1, 2, \dots, N\}$: Tập hợp $N$ công việc vá lỗ hổng trong Backlog.
- $S = 0$: Nút ảo đại diện cho trạng thái **Bắt đầu Sprint** của mỗi team.
- $E = N + 1$: Nút ảo đại diện cho trạng thái **Kết thúc Sprint** của mỗi team.
- $\mathcal{V}^+ = \mathcal{V} \cup \{S, E\}$: Tập các nút mở rộng phục vụ việc định tuyến chuỗi.
- $T = \{1, 2, \dots, M\}$: Tập hợp $M$ đội kỹ thuật (Teams) tham gia Sprint.
- $\mathcal{E} \subset \mathcal{V} \times \mathcal{V}$: Tập hợp các cung phụ thuộc tiên quyết trong đồ thị có hướng không chu trình (DAG) $G = (\mathcal{V}, \mathcal{E})$.  
  Cặp $(u, v) \in \mathcal{E}$ thể hiện task $u$ là điều kiện tiên quyết của task $v$ ($u \prec v$).
- $\mathcal{S}_{\text{OWASP}} = \{1, 2, \dots, 10\}$: Tập hợp 10 nhóm kỹ năng bảo mật chuẩn OWASP Top 10.
- $\tau \in \mathbb{Z}^+$: Chỉ số của chu kỳ Sprint hiện tại đang xét.

---

## 2. Thuộc Tính & Tham Số Đầu Vào (Attributes & Parameters)

### 2.1. Thuộc tính của Task $i \in \mathcal{V}$
- $r_i \in [0, 10]$: Điểm rủi ro an ninh kỹ thuật gốc theo chuẩn CVSS.
- $e_i \in \mathbb{Z}^+$: Ước lượng công sức thực hiện (đo bằng Story Points).
- $\text{repo}_i$: Định danh repository chứa mã nguồn của task $i$.
- $\text{mod}_i$: Định danh phân hệ / module mã nguồn cụ thể của task $i$.
- $\text{skill}_i \in \mathcal{S}_{\text{OWASP}}$: Nhóm kỹ năng chuyên môn cần thiết để sửa task $i$.
- $\text{disc}_i \in \mathbb{Z}^+$: Sprint phát hiện lỗ hổng ($\text{disc}_i \le \tau$).
- $\text{dead}_i \in \mathbb{Z}^+$: Sprint hạn chót SLA bắt buộc phải khắc phục xong.

### 2.2. Thuộc tính của Team $t \in T$
- $\text{cap}_t \in \mathbb{Z}^+$: Tổng dung lượng Story Points tối đa mà team $t$ có thể cam kết trong Sprint $\tau$.
- $k_{t, s} \in [0.0, 1.0]$: Điểm số thành thạo của team $t$ đối với nhóm kỹ năng $s \in \mathcal{S}_{\text{OWASP}}$.

### 2.3. Các Chỉ Số Tính Toán Dẫn Xuất (Derived Metrics)

#### 1. Điểm Lợi Ích Giảm Nhẹ Rủi Ro (Mitigation Utility — $u_i$)
Điểm ưu tiên rủi ro của task $i$ tại Sprint $\tau$ được tính bằng tổng của điểm CVSS gốc và hai thành phần khuếch đại theo thời gian:
$$u_i = r_i + \alpha \cdot (\tau - \text{disc}_i) + \beta \cdot \max(0, \tau - \text{dead}_i + 1)$$
Trong đó:
- $(\tau - \text{disc}_i) \ge 0$: Tuổi thọ tồn lưu (Persistence), đo bằng số sprint lỗ hổng đã tồn đọng trong backlog mà chưa được xử lý.
- $\max(0, \tau - \text{dead}_i + 1)$: Độ khẩn cấp thời hạn (Deadline Urgency), tự động kích hoạt phạt tăng vọt khi sprint hiện tại đã chạm hoặc vượt quá hạn chót $\text{dead}_i$.
- $\alpha > 0, \beta > 0$: Các hệ số điều chỉnh chính sách ưu tiên do tổ chức thiết lập.

#### 2. Chi Phí Chuyển Đổi Ngữ Cảnh Liên Tiếp (Context Switch Distance — $C_{ij}$)
Chi phí phát sinh khi một team hoàn thành task $i$ và chuyển sang thực hiện ngay task $j$ ($i, j \in \mathcal{V}, i \neq j$):
$$C_{ij} = w_{\text{repo}} \cdot \mathbb{I}(\text{repo}_i \neq \text{repo}_j) + w_{\text{mod}} \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + w_{\text{skill}} \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j)$$
Trong đó:
- $\mathbb{I}(\cdot)$ là hàm chỉ thị: bằng $1$ nếu điều kiện đúng, bằng $0$ nếu sai.
- $w_{\text{repo}} > w_{\text{mod}} \ge w_{\text{skill}} > 0$: Hệ số phạt phân cấp theo 3 mức độ (Đổi Repo > Đổi Module > Đổi Skill).
- $C_{ij} = 0$ khi và chỉ khi hai task cùng chung Repo, cùng Module và cùng nhóm Skill.
- Quy ước với nút ảo: $C_{S, i} = 0, \; C_{i, E} = 0, \; C_{S, E} = 0, \; \forall i \in \mathcal{V}$.

---

## 3. Biến Quyết Định (Decision Variables)

1. **Biến Phân Bổ (Assignment Variable)**:
   $$x_{it} \in \{0, 1\}, \quad \forall i \in \mathcal{V}, \forall t \in T$$
   $$x_{it} = \begin{cases} 1 & \text{nếu task } i \text{ được giao cho team } t \text{ thực hiện trong Sprint } \tau \\ 0 & \text{ngược lại} \end{cases}$$

2. **Biến Định Tuyến Chuỗi Thứ Tự (Sequencing / Routing Variable)**:
   $$z_{ijt} \in \{0, 1\}, \quad \forall i, j \in \mathcal{V}^+, i \neq j, \forall t \in T$$
   $$z_{ijt} = \begin{cases} 1 & \text{nếu team } t \text{ thực hiện task } i \text{ ngay trước task } j \\ 0 & \text{ngược lại} \end{cases}$$
   *(Lưu ý: $z_{SEt} = 1$ biểu thị trường hợp team $t$ không nhận bất kỳ task nào trong sprint).*

3. **Biến Vị Trí Thứ Tự Trong Chuỗi (Position Variables — MTZ Formulation)**:
   $$pos_{it} \in [0, N], \quad \forall i \in \mathcal{V}, \forall t \in T$$
   $pos_{it}$ là biến nguyên biểu diễn số thứ tự thực hiện của task $i$ trong chuỗi công việc của team $t$. Nếu $x_{it} = 0$ thì $pos_{it} = 0$.

---

## 4. Hệ Thống Ràng Buộc Toán Học (Constraints)

### 4.1. Ràng Buộc Phân Bổ & Năng Lực (Assignment & Capacity)

1. **Gán đơn nhất & Cho phép tồn đọng backlog**:
   Mỗi task $i$ chỉ được giao cho tối đa 1 team xử lý trong sprint (những task không được giao sẽ hoãn sang sprint sau):
   $$\sum_{t \in T} x_{it} \le 1, \quad \forall i \in \mathcal{V}$$

2. **Trần dung lượng Sprint của từng team (Story Point Knapsack)**:
   Tổng điểm Story Points của các task giao cho team $t$ không được vượt quá dung lượng $\text{cap}_t$:
   $$\sum_{i \in \mathcal{V}} e_i \cdot x_{it} \le \text{cap}_t, \quad \forall t \in T$$

3. **Ngưỡng năng lực kỹ năng tối thiểu (Skill Threshold $\ge 0.5$)**:
   Team $t$ chỉ được phép nhận task $i$ nếu điểm thành thạo kỹ năng tương ứng đạt từ $0.5$ trở lên:
   $$x_{it} \le \mathbb{I}(k_{t, \text{skill}_i} \ge 0.5), \quad \forall i \in \mathcal{V}, \forall t \in T$$
   *(Trong mô hình MIP, nếu $k_{t, \text{skill}_i} < 0.5$, ta cố định $x_{it} = 0$ ngay từ khâu tiền xử lý).*

---

### 4.2. Ràng Buộc Phụ Thuộc Kỹ Thuật (Precedence Constraints)

Với mọi cặp phụ thuộc $(u, v) \in \mathcal{E}$ ($u$ là cha, $v$ là con):

4. **Kéo theo khi chọn lọc (Chọn con bắt buộc phải chọn cha)**:
   Không thể sửa lỗ hổng con $v$ nếu lỗ hổng cha $u$ chưa được giải quyết:
   $$\sum_{t \in T} x_{vt} \le \sum_{t \in T} x_{ut}, \quad \forall (u, v) \in \mathcal{E}$$

5. **Bắt buộc cùng một team (Intra-team Execution)**:
   Nếu cả $u$ và $v$ cùng được chọn làm trong sprint này, chúng bắt buộc phải thuộc về cùng một team để triệt tiêu hoàn toàn tắc nghẽn cross-team:
   $$x_{vt} \le x_{ut}, \quad \forall t \in T, \forall (u, v) \in \mathcal{E}$$
   *(Bất đẳng thức này phát biểu: Nếu team $t$ nhận task con $v$ ($x_{vt} = 1$), thì team $t$ bắt buộc phải nhận task cha $u$ ($x_{ut} = 1$))*.

---

### 4.3. Ràng Buộc Bảo Toàn Luồng Chuỗi (Flow Conservation)

Đảm bảo tập các task được giao cho mỗi team $t$ tạo thành một đường đi đơn nhất bắt đầu từ $S$ và kết thúc tại $E$:

6. **Luồng xuất phát từ nút $S$**:
   $$\sum_{j \in \mathcal{V}} z_{Sjt} + z_{SEt} = 1, \quad \forall t \in T$$

7. **Luồng kết thúc tại nút $E$**:
   $$\sum_{i \in \mathcal{V}} z_{iEt} + z_{SEt} = 1, \quad \forall t \in T$$

8. **Bảo toàn luồng tại mỗi task $i \in \mathcal{V}$**:
   Một task $i$ nếu được giao cho team $t$ ($x_{it} = 1$) thì phải có đúng 1 cung đi vào và đúng 1 cung đi ra:
   $$\sum_{j \in \mathcal{V} \cup \{S\}, j \neq i} z_{jit} = x_{it}, \quad \forall i \in \mathcal{V}, \forall t \in T$$
   $$\sum_{j \in \mathcal{V} \cup \{E\}, j \neq i} z_{ijt} = x_{it}, \quad \forall i \in \mathcal{V}, \forall t \in T$$

---

### 4.4. Ràng Buộc Khử Chu Trình Con & Thứ Tự Topo (Subtour Elimination & Ordering)

9. **Liên kết biến vị trí $pos_{it}$ với biến gán $x_{it}$**:
   $$x_{it} \le pos_{it} \le N \cdot x_{it}, \quad \forall i \in \mathcal{V}, \forall t \in T$$
   *(Nếu $x_{it} = 1 \implies 1 \le pos_{it} \le N$; nếu $x_{it} = 0 \implies pos_{it} = 0$)*.

10. **Khử chu trình con theo chuẩn Miller-Tucker-Zemlin (MTZ)**:
    Nếu team $t$ thực hiện $i$ ngay trước $j$ ($z_{ijt} = 1$), thì thứ tự vị trí của $j$ phải lớn hơn ít nhất 1 đơn vị so với $i$:
    $$pos_{jt} \ge pos_{it} + 1 - N \cdot (1 - z_{ijt}), \quad \forall i, j \in \mathcal{V}, i \neq j, \forall t \in T$$

11. **Thứ tự topo bắt buộc nội bộ team**:
    Nếu cả cha $u$ và con $v$ cùng được giao cho team $t$ ($x_{ut} = x_{vt} = 1$), thì $u$ phải được làm trước $v$ ($pos_{ut} < pos_{vt}$):
    $$pos_{ut} \le pos_{vt} - 1 + N \cdot (2 - x_{ut} - x_{vt}), \quad \forall (u, v) \in \mathcal{E}, \forall t \in T$$
    *(Khi $x_{ut} = x_{vt} = 1$, số hạng $N \cdot (2 - 2) = 0$, phương trình trở thành $pos_{ut} \le pos_{vt} - 1 \implies pos_{ut} < pos_{vt}$)*.

---

## 5. Hàm Mục Tiêu Kép (Bi-Objective Optimization)

Mô hình tìm kiếm phương án phân bổ $\mathbf{X}$ và định tuyến chuỗi $\mathbf{Z}$ tối ưu đồng thời 2 mục tiêu:

$$\text{Optimize } \mathbf{F} = \Big( \max f_1, \; \min f_2 \Big)$$

### 5.1. Hàm $f_1$ — Cực Đại Hóa Lợi Ích Giảm Nhẹ Rủi Ro (Mitigated Utility)
Tổng điểm Mitigation Utility ($u_i$) của toàn bộ các lỗ hổng được các teams hoàn thành trong sprint:
$$f_1 = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i \cdot x_{it}$$

### 5.2. Hàm $f_2$ — Cực Tiểu Hóa Tổng Chi Phí Chuyển Đổi Ngữ Cảnh (Context Switch Cost)
Tổng chi phí chuyển đổi ngữ cảnh phát sinh qua các bước chuyển việc liên tiếp của tất cả các team:
$$f_2 = \sum_{t \in T} \sum_{i \in \mathcal{V}} \sum_{j \in \mathcal{V}, j \neq i} C_{ij} \cdot z_{ijt}$$

---

## 6. Phương Pháp Vô Hướng Hóa & Dò Quét Pareto (Scalarization)

Để giải tìm tập nghiệm thỏa hiệp (Pareto Frontier) hoặc nghiệm theo yêu cầu của Product Owner, ta áp dụng phương pháp vô hướng hóa có trọng số (Weighted-Sum Scalarization):

$$\max Z(\lambda) = f_1 - \lambda \cdot f_2 = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i \cdot x_{it} - \lambda \cdot \sum_{t \in T} \sum_{i \in \mathcal{V}} \sum_{j \in \mathcal{V}, j \neq i} C_{ij} \cdot z_{ijt}$$

- $\lambda \ge 0$: Hệ số đánh đổi (Trade-off weight) do người quản trị thiết lập:
  - $\lambda \to 0$: Ưu tiên tối đa giải quyết rủi ro bảo mật (chấp nhận dev đổi ngữ cảnh nhiều).
  - $\lambda$ lớn: Ưu tiên bảo vệ năng suất lập trình viên, chỉ chấp nhận vá lỗi nếu các task nằm cùng repo/module.
- Bằng cách quét tham số $\lambda \in [0, \lambda_{\max}]$, mô hình chính xác (như OR-Tools CP-SAT) có thể vạch ra toàn bộ **Đường cong Pareto tối ưu (Exact Pareto Frontier)** để làm chuẩn đối sánh (benchmark) cho các giải thuật Heuristic/Metaheuristic.
