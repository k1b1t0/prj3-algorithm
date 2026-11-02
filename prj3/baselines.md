# Danh Sách Các Thuật Toán Đối Chuẩn (Baselines)

Tài liệu này tổng hợp 3 thuật toán đối chuẩn (Baselines) đại diện cho 3 góc độ khác nhau để so sánh với thuật toán đề xuất **Proposed H-CSM**.

---

## 1. Tổng Quan 3 Baselines

| Thuật toán | Đại diện cho nhóm nào? | Vai trò trong bài toán |
| :--- | :--- | :--- |
| **1. Greedy-CVSS** | Thực tế doanh nghiệp (Jira/Scrum) | Thước đo cơ sở thực tế (chạy siêu nhanh nhưng mù ngữ cảnh). |
| **2. OR-Tools CP-SAT** | Nghiệm tối ưu toán học (Exact Bound) | Chuẩn vàng lý thuyết (để đo khoảng cách tới tối ưu - Optimality Gap). |
| **3. OR-Tools Routing (GLS)** | Metaheuristic công nghiệp đỉnh cao | Đối thủ thực chiến mạnh nhất (tìm kiếm cục bộ có hướng dẫn). |

---

## 2. Chi Tiết Từng Thuật Toán

### 2.1. Baseline 1: Greedy-CVSS (Thực tế công nghiệp hiện nay)
* **Cách hoạt động**:
  1. Sắp xếp toàn bộ task trong Backlog theo mật độ lợi ích $\rho_i = u_i / e_i$ giảm dần (hoặc theo điểm CVSS gốc).
  2. Duyệt từ trên xuống dưới: task nào nhét vừa dung lượng của team và team đủ điểm kỹ năng ($\ge 0.5$) thì gán ngay cho team đó.
  3. Thứ tự làm việc trong từng team giữ nguyên theo thứ tự bốc việc.
* **Ưu điểm**: Cực kỳ nhanh ($< 1\text{ ms}$), đơn giản, phản ánh đúng cách các đội kỹ thuật bốc việc thủ công trên Jira hiện nay.
* **Nhược điểm**: **Hoàn toàn mù ngữ cảnh**. Vì chỉ chăm chăm bốc task CVSS cao, lập trình viên sẽ phải liên tục nhảy qua lại giữa nhiều repo/module khác nhau trong sprint, gây phân mảnh tư duy nghiêm trọng.
* **Ý nghĩa đối sánh**: Dùng làm mốc cơ sở để chứng minh thuật toán đề xuất giúp giảm mạnh chi phí đổi ngữ cảnh ($f_2$) mà lợi ích an ninh ($f_1$) không bị sụt giảm.

---

### 2.2. Baseline 2: Google OR-Tools CP-SAT (Chuẩn vàng lý thuyết)
* **Cách hoạt động**:
  - Dùng bộ giải Constraint Programming kết hợp SAT hiện đại nhất của Google để giải trực tiếp mô hình toán học hình thức MO-MILP.
  - Sử dụng toàn bộ hệ thống biến nhị phân phân bổ $x_{it}$, biến chuỗi chuyển tiếp $z_{u,v,t}$ và ràng buộc vị trí MTZ ($pos_{it}$).
* **Ưu điểm**: Định nghĩa chuẩn mực toán học chính xác (Exact Formulation) không thỏa hiệp.
* **Nhược điểm**: **Bùng nổ đối xứng giai thừa và tổ hợp biến khi kích thước tăng**.
  - Trên $N=40$, CP-SAT tìm được nghiệm khả thi chất lượng cao ($Z=0.397$ tại 15s, $Z=0.431$ tại 60s), nhưng do hiện tượng đối xứng nội cụm $\prod(N_b!) \approx 10^{23}$ hoán vị cùng $f_2=0$ và nới lỏng LP yếu của ràng buộc MTZ, solver không thể nâng cận dưới để chứng minh tối ưu tuyệt đối (đóng GAP) trong 60s.
  - Trên $N=100, 500$, solver sinh ra hàng chục nghìn đến hàng triệu biến chuỗi $z_{ijt}$, dẫn đến tràn bộ nhớ hoặc timeout không ra nghiệm.
* **Ý nghĩa đối sánh**: Cung cấp **Mốc đối chuẩn khả thi chất lượng cao** trên các kịch bản nhỏ ($N=40$) để đo chính xác khoảng cách tiếp cận của thuật toán đề xuất.

---

### 2.3. Baseline 3: Google OR-Tools Routing GLS (Heuristic công nghiệp)
* **Cách hoạt động**:
  - Xem bài toán như bài toán Định tuyến xe có dung lượng và có điểm thưởng (Capacitated Team Orienteering Problem).
  - **Pha 1 (Khởi tạo)**: Dùng chiến lược chèn tham lam chi phí thấp (`PARALLEL_CHEAPEST_INSERTION`) để tạo lịch trình ban đầu.
  - **Pha 2 (Tối ưu)**: Dùng thuật toán **Guided Local Search (GLS)** liên tục hoán đổi task giữa các team (`Relocate`, `Exchange`) và đảo chuỗi nội bộ (`2-Opt`) để giảm dần chi phí đổi ngữ cảnh.
* **Ưu điểm**: Giải được ở mọi quy mô ($N=40, 100, 500$), không bị timeout như CP-SAT, chất lượng nghiệm ban đầu khá tốt.
* **Nhược điểm**: Là thuật toán định tuyến tổng quát (General-purpose), không có cơ chế 1D Knapsack DP để chọn tập con task tối ưu trong từng cụm mã nguồn (Repo $\to$ Module $\to$ Skill). Khi cố nhồi task để tăng $f_1$, GLS làm vỡ cấu trúc chuỗi $f_2$ và dễ mắc kẹt trong cực tiểu địa phương.
* **Ý nghĩa đối sánh**: Đây là **đối thủ cạnh tranh thực tế mạnh nhất** để chứng minh thuật toán đề xuất H-CSM chạy nhanh hơn hàng chục đến hàng trăm lần mà chất lượng Pareto vượt trội (+21.2% đến +21.8%).

---

## 3. Tóm Tắt So Sánh Nhanh

| Tiêu chí | Greedy-CVSS | OR-Tools CP-SAT | OR-Tools Routing (GLS) | **Proposed H-CSM** |
| :--- | :---: | :---: | :---: | :---: |
| **Bản chất** | Tham lam 1 chiều | Bộ giải chính xác (Exact) | Metaheuristic công nghiệp | Quotient-DP Matheuristic (3 pha) |
| **Chất lượng nghiệm** | Kém (chỉ tối ưu $f_1$) | Mốc đối chuẩn trên $N=40$ | Khá tốt (bị kẹt cực tiểu địa phương) | **Tiệm cận CP-SAT 60s, vượt GLS +21.8%** |
| **Kiểm soát ngữ cảnh ($f_2$)** | Kém (Mù ngữ cảnh, $f_2$ rất cao) | Tối ưu hóa chuỗi toàn cục | Khá tốt (Local Search 2-Opt) | **Vượt trội (Quotient DP & Cheapest Path)** |
| **Thời gian chạy ($N=500$)** | $< 4\text{ ms}$ | **Timeout / Tràn RAM (>60s)** | $\approx 5.1\text{ giây}$ | **$\approx 340\text{ ms}$ (nhanh hơn $15\times$)** |
| **Quét đa điểm Pareto** | Kém (sụp đổ ở $w=0.25$) | Cực chậm / Timeout | Chậm (phải chạy lại từng điểm) | **Siêu nhanh (chỉ vài giây quét toàn bộ)** |
