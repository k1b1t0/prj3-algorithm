# Thuật Toán Đề Xuất: H-CSM (Hierarchical Cluster-Simulate-Match)

> **Mục tiêu**: Lập lịch phân bổ và định tuyến chuỗi xử lý lỗ hổng bảo mật cho nhiều đội kỹ thuật trong Sprint Agile, tối ưu hóa đồng thời Lợi ích an ninh ($f_1$) và Chi phí chuyển đổi ngữ cảnh ($f_2$).  
> **Nguyên lý cốt lõi**: Phân cụm nguyên tử dựa trên quan hệ $C_{ij} = 0$, kết hợp Quy hoạch động 1 chiều nội cụm (Exact 1D Knapsack DP), Phân bổ đa lựa chọn khấu hao chi phí chèn đường đi (Cheapest Path Insertion), và Định tuyến chuỗi cụm bằng Bitmask DP.

---

## 1. Kiến Trúc 3 Pha Tổng Quát

Thuật toán H-CSM vận hành qua 3 pha nối tiếp:
- **Pha 1 (Phân cụm & Quy hoạch động nội cụm)**: Gom các task cùng Repo, Module, Skill thành các cụm nguyên tử ($C_{ij} = 0$), sau đó dùng 1D Knapsack DP lập trước bảng giá trị tối ưu $\Phi_b(c)$ cho từng mức dung lượng $c \in [1, \text{cap}_{\max}]$.
- **Pha 2 (Phân bổ đa lựa chọn & Chèn đường đi)**: Lần lượt chọn cụm, mức dung lượng và đội $(b, c, t)$ có hiệu suất biên $\eta$ cao nhất, tự động khấu hao chi phí chuyển đổi đường đi.
- **Pha 3 (Hoán đổi liên đội & Định tuyến Bitmask DP)**: Tinh chỉnh hoán đổi cụm giữa các đội để gom gọn repo, sau đó giải chính xác thứ tự thực thi Open-TSP trong từng đội bằng Bitmask DP.

---

## 2. Chi Tiết Logic Toán Học Từng Pha

### Pha 1: Phân Cụm Ngữ Cảnh & Quy Hoạch Động Nội Cụm (Clustering & 1D DP Profiling)

1. **Phân cụm nguyên tử (Atomic Clustering)**:
   Các task có $C_{ij} = 0$ (cùng Repo, Module, Skill) được gom thành $B$ cụm $\mathcal{G} = \{G_1, G_2, \dots, G_B\}$ ($B \ll N$). Chi phí chuyển đổi giữa các task bên trong cùng một cụm luôn bằng $0$.
2. **Quy hoạch động 1 chiều nội cụm (Exact 1D Knapsack DP)**:
   Với mỗi cụm $G_b$ và mỗi mức dung lượng $c \in \{1, \dots, \text{cap}_{\max}\}$, ta dùng thuật toán Quy hoạch động 1 chiều (1D DP) để tìm tập con task tối ưu $S^*_b(c) \subseteq G_b$ mang lại tổng điểm ưu tiên lớn nhất:
   $$\Phi_b(c) = \max_{S \subseteq G_b} \left\{ \sum_{i \in S} u_i \;\middle\vert{}\; \sum_{i \in S} e_i \le c \right\}$$
   - *Ý nghĩa*: $\Phi_b(c)$ là tổng điểm utility lớn nhất của tập task con nhặt được từ cụm $G_b$ với giới hạn dung lượng $c$. Bảng DP này được tính sẵn trong $O(|G_b| \cdot \text{cap}_{\max})$, chỉ tốn $\approx 0.1\text{ ms}$ cho toàn bộ backlog.

---

### Pha 2: Phân Bổ Cụm Task Cho Từng Đội (Cluster-to-Team Allocation)

Mỗi đội $t$ duy trì một chuỗi các cụm hiện tại $\pi_t = (b_1, b_2, \dots, b_k)$.

1. **Chi phí chèn đường đi rẻ nhất (Cheapest Open-Path Insertion)**:
   Khi chèn cụm $G_b$ vào đội $t$, chi phí chuyển đổi ngữ cảnh tăng thêm $\Delta C(b, \pi_t)$ được tính bằng vị trí chèn rẻ nhất vào chuỗi:
   $$\Delta C(b, \pi_t) = \begin{cases} 0 & \text{nếu } b \in \pi_t \text{ hoặc } \pi_t = \emptyset \\ \min_{0 \le r \le |\pi_t|} \big( C_{\pi_t(r), b} + C_{b, \pi_t(r+1)} - C_{\pi_t(r), \pi_t(r+1)} \big) & \text{nếu } b \notin \pi_t \end{cases}$$
2. **Mật độ đóng góp cho hàm mục tiêu ($\eta$)**:
   $$\eta(b, c, t) = \frac{w \cdot \frac{\Phi_b(c)}{f_1^{\max}} - (1 - w) \cdot \frac{\Delta C(b, \pi_t)}{f_2^{\max}}}{c}$$
   - Đại lượng $\eta$ đo lường mức đóng góp vào hàm mục tiêu $Z(w)$ trên mỗi Story Point tiêu tốn.
   - Nếu đội $t$ nhận thêm task từ cụm đã có sẵn trong chuỗi ($b \in \pi_t$), $\Delta C = 0$.
3. **Lựa chọn tối ưu từng bước**:
   Tại mỗi bước, thuật toán quét tìm trường hợp $(b^*, c^*, t^*)$ có $\eta > 0$ cao nhất $\to$ gán tập task con cho đội $t^* \to$ cập nhật lại bảng DP cho các task còn lại của cụm $G_{b^*}$.

---

### Pha 3: Tinh Chỉnh Thứ Tự & Định Tuyến Chuỗi (Refinement & Sequencing)

1. **Thử hoán đổi cụm giữa hai đội (Inter-Team Exchange)**:
   Giải thuật lần lượt thử 2 phép biến đổi để giảm $f_2$ mà vẫn giữ nguyên $f_1$ (không vi phạm dung lượng và kỹ năng):
   - *Di chuyển một chiều (1-0 Relocate)*: Chuyển 1 cụm từ Team 1 sang Team 2 nếu Team 2 còn đủ chỗ và có cùng repo.
   - *Đổi chéo hai chiều (1-1 Block Swap)*: Đổi chéo 1 cụm giữa Team 1 và Team 2 để gom chung repo về cùng một đội.
2. **Định tuyến chuỗi thực thi (Task Sequencing)**:
   - *Giữa các cụm*: Giải chính xác đường đi hở ngắn nhất giữa $K$ cụm ($K \le 10$) bằng Quy hoạch động Bitmask DP $O(2^K \cdot K^2)$.
   - *Bên trong từng cụm*: Sắp xếp các task theo mật độ $u_i / e_i$ giảm dần.

---

## 3. Phân Tích Độ Phức Tạp & Hiệu Năng

| Thành Phần Thuật Toán | Độ Phức Tạp Lý Thuyết | Thời Gian Thực Tế ($N=500, M=8$) |
| :--- | :---: | :---: |
| **Pha 1 (Phân cụm & 1D DP)** | $O(N \cdot \text{cap}_{\max})$ | $\approx 0.5\text{ ms}$ |
| **Pha 2 (Phân bổ chèn đường đi)** | $O(B \cdot \text{cap}_{\max} \cdot M)$ | $\approx 15\text{ ms}$ |
| **Pha 3 (Hoán đổi & Bitmask DP TSP)** | $O(M \cdot 2^K \cdot K^2)$ ($K \le 10$) | $\approx 2.5\text{ ms}$ |
| **Tổng thể 1 lượt chạy H-CSM ($w$ cố định)** | **$O(N \cdot \text{cap}_{\max} + B \cdot \text{cap}_{\max} \cdot M + M \cdot 2^K \cdot K^2)$** | **$< 25\text{ ms}$** |
| **Quét toàn bộ mặt cong Pareto (21 giá trị $w$)** | **$21 \times \text{Runtime}$** | **$< 0.5\text{ giây}$** |
