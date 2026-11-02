## 1. Kiến Trúc Mô Hình Hóa 

Hàm mục tiêu vô hướng hóa $Z(w)$ được chuyển đổi tương đương về hàm chi phí định tuyến:
$$\max Z(w) = w \cdot \frac{f_1}{\Delta f_1} - (1 - w) \cdot \frac{f_2}{\Delta f_2} \iff \max \left( f_1 - \lambda_{\text{effective}} \cdot f_2 \right)$$
với hệ số phạt tương đương $\lambda_{\text{effective}}$:
$$\lambda_{\text{effective}} = \frac{1 - w}{w} \cdot \frac{f_1^{\max} - f_1^{\min}}{f_2^{\max} - f_2^{\min}}$$

| Khái niệm SecOps | Ánh xạ OR-Tools Routing |
| :--- | :--- |
| $M$ đội kỹ thuật | $M$ xe (Vehicles) |
| Dung lượng Sprint (30 SP) | Trần tải trọng (Capacity) |
| Effort task ($e_i$) | Tải trọng tại điểm (Demand) |
| Chi phí đổi ngữ cảnh ($C_{ij}$) | Chi phí di chuyển (Arc Cost) |
| Lợi ích an ninh ($u_i$) | Phạt khi bỏ lỡ task (Penalty) |
| Ngưỡng kỹ năng ($\ge 0.5$) | Xe được phép ghé thăm |
| Hành trình hở (Open Route) | 2 depot ảo: Start ($N$), End ($N+1$) |

---

## 2. Quy Trình Thực Thi Mô Hình

- **Tạo đỉnh ảo**: Tạo 2 depot ảo Start ($N$) và End ($N+1$), cả $M$ đội xuất phát từ $N$ và kết thúc tại $N+1$ với chi phí nối đỉnh ảo bằng 0.
- **Chi phí cung đường**: $\text{Cost}(i, j) = \text{round}(C_{ij} \cdot \lambda_{\text{effective}} \cdot \text{SCALE})$.
- **Kiểm soát dung lượng**: Giới hạn tổng Story Points của mỗi đội không vượt quá trần dung lượng $\text{cap}_t = 30\text{ SP}$.
- **Cơ chế phạt**: Bỏ lỡ task $i$ bị phạt bằng $u_i \cdot \text{SCALE}$, tương đương toán học với việc tối đa hóa lợi ích $f_1$.
- **Chiến lược tìm kiếm 2 pha**:
  - Khởi tạo tham lam: Dùng Parallel Cheapest Insertion chèn việc song song để tạo nghiệm ban đầu hợp lệ trong vài mili-giây.
  - Tinh chỉnh GLS: Dùng Guided Local Search với các toán tử 2-opt, Relocate, Exchange; tự động phạt các cung chi phí cao để thoát cực tiểu cục bộ trong thời gian giới hạn.
- **Trích xuất nghiệm**: Lần theo chuỗi chỉ mục từng xe để đóng gói thành `SprintPlan`, sau đó gọi `evaluate_sprint_plan()` tính lại các chỉ số thực $f_1, f_2, Z(w)$.

---

## 3. Điểm Yếu Của GLS

- **Chỉ thao tác đơn task**: Các toán tử láng giềng chỉ hoán đổi từng task riêng lẻ, không thể di chuyển hay hoán đổi cả khối công việc cùng module.
- **Bão hòa không gian tìm kiếm**: Dễ rơi vào vùng bình nguyên cục bộ khi quy mô bài toán tăng lên.
