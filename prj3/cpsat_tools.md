# Cơ Sở Lý Thuyết & Kiến Trúc Bộ Giải Google OR-Tools CP-SAT

> **Mục đích**: Tài liệu hóa nền tảng toán học, cơ chế hoạt động tầng thấp (*under the hood*) và kiến trúc giải thuật của **Google OR-Tools CP-SAT Solver** (Constraint Programming - Boolean Satisfiability).  
> **Tài liệu cài đặt mã nguồn**: Tham khảo [`cpsat_implementation.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/cpsat_implementation.md) và mã nguồn tại [`src/solvers/cpsat_exact.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/cpsat_exact.py).

---

## 1. Tổng Quan & Lịch Sử Hình Thành

**CP-SAT** là bộ giải tối ưu hóa tổ hợp hiện đại của Google OR-Tools, được phát triển bởi đội ngũ do Laurent Perron dẫn dắt. Bộ giải này đánh dấu sự kết hợp đột phá giữa hai trường phái tính toán lớn:

1. **Constraint Programming (CP truyền thống)**:
   - *Thế mạnh*: Khả năng mô hình hóa tự nhiên và phong phú thông qua các ràng buộc cấp cao chuyên biệt (*Global Constraints* như `AllDifferent`, `Cumulative`, `Circuit`, `NoOverlap`).
   - *Điểm yếu*: Thuật toán tìm kiếm nhánh-cận (Branch-and-Bound) kết hợp Chronological Backtracking truyền thống dễ bị "lạc" trong không gian tìm kiếm khổng lồ và lặp lại các chuỗi sai lầm tương tự.
2. **Boolean Satisfiability (SAT)**:
   - *Thế mạnh*: Khả năng suy diễn logic cực nhanh với cơ chế **Conflict-Driven Clause Learning (CDCL)** và Non-chronological Backtracking (Backjumping).
   - *Điểm yếu*: Chỉ xử lý trực tiếp các biến nhị phân $\{0, 1\}$ và các mệnh đề logic dạng hội (CNF). Việc chuyển đổi bài toán số nguyên lớn sang SAT thuần túy (*Eager SAT Encoding*) làm bùng nổ cấp số nhân số lượng mệnh đề Boolean.

**Bước đột phá LCG (Lazy Clause Generation)**:
Dựa trên các nghiên cứu tiên phong của GS. Peter Stuckey và cộng sự (Ohrimenko et al., 2009), CP-SAT kết hợp CP và SAT thông qua kỹ thuật **Lazy Clause Generation**: Duy trì các bộ lan truyền miền giá trị số nguyên của CP, nhưng liên kết chúng với một SAT engine bên dưới để chỉ sinh ra các mệnh đề Boolean giải thích khi cần thiết.

---

## 2. Kiến Trúc Hoạt Động Tầng Thấp (Under the Hood)

Sơ đồ kiến trúc bên trong của CP-SAT Solver:

```
                      ┌────────────────────────────────────────┐
                      │             Presolve Engine            │
                      │  (Probing, Domain Reduction, Dual Red) │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │       Shared Portfolio Search          │
                      │ ┌──────────────┐      ┌──────────────┐ │
                      │ │ Worker 1..K  │ ◄──► │ Worker K+1..M│ │
                      │ │ (LNS, VSIDS) │      │ (LP Dual Bnd)│ │
                      │ └──────────────┘      └──────────────┘ │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                     Core Engine Loop                        │
        │                                                             │
        │   ┌─────────────────────┐       LCG       ┌──────────────┐  │
        │   │    CP Propagators   │ ──────────────► │  SAT Engine  │  │
        │   │ (Linear, Intervals) │ ◄────────────── │ (Unit Prop,  │  │
        │   └─────────────────────┘   Explanations  │    CDCL)     │  │
        │              ▲                                   │          │
        │              └──────────── Conflict ─────────────┘          │
        └─────────────────────────────────────────────────────────────┘
```

### 2.1. Cơ Chế Mã Hóa Biến Nguyên (Order Encoding)
CP-SAT là một bộ giải số nguyên thuần túy (*pure integer engine*). Mỗi biến nguyên $x$ có miền giá trị $D(x) = [l, u]$ được liên kết với một họ các biến mệnh đề Boolean theo phương pháp **Order Encoding**:
$$B(x, v) \iff [x \ge v] \quad \forall v \in \{l+1, \dots, u\}$$

Nhờ cấu trúc này:
- Nếu $[x \ge v] = \text{True}$ thì tự động suy ra $[x \ge v - 1] = \text{True}$.
- Nếu $[x \ge v] = \text{False}$ thì miền trên của $x$ lập tức bị chặn tại $x \le v - 1$.
- Phủ định logic: $\neg [x \ge v] \iff [x \le v - 1]$.

Mã hóa này cho phép SAT solver trực tiếp lập luận về các phép so sánh bất đẳng thức số nguyên mà không cần phân rã biến $x$ thành vô số biến rời rạc độc lập.

---

### 2.2. Lan Truyền Ràng Buộc & Giải Thích (Propagation & Explanations)
Trong CP truyền thống, khi một ràng buộc rút gọn miền giá trị (ví dụ: $x + y \le 10$, với $x \ge 6 \implies y \le 4$), thông tin này chỉ được cập nhật vào miền biến.

Trong CP-SAT, mỗi khi một propagator rút gọn cận, nó bắt buộc phải cung cấp một **Lời giải thích (Explanation)** dưới dạng mệnh đề Boolean:
$$\text{Antecedent} \implies \text{Consequent}$$
Ví dụ:
$$([x \ge 6]) \implies ([y \le 4]) \iff (\neg [x \ge 6] \lor [y \le 4])$$

Mệnh đề này được đưa vào SAT solver. SAT solver dùng nó để suy diễn tiếp qua thuật toán **Unit Propagation**.

---

### 2.3. Sinh Mệnh Đề Lười Biếng (Lazy Clause Generation - LCG)
- Nếu sinh toàn bộ các mệnh đề giải thích ngay từ đầu (*Eager Generation*), số lượng clauses có thể lên tới hàng triệu hoặc hàng tỷ, gây tràn bộ nhớ RAM ngay lập tức.
- **Cơ chế Lazy**: Bộ giải duy trì các ràng buộc số nguyên ở dạng gọn nhẹ. Chỉ khi nào nhánh tìm kiếm dẫn đến việc rút gọn cận hoặc dẫn tới mâu thuẫn, propagator mới sinh ra mệnh đề logic giải thích cho bước đi đó. Nhờ vậy, CP-SAT giữ được dung lượng bộ nhớ nhỏ gọn trong khi vẫn tận dụng được sức mạnh suy diễn logic của SAT.

---

### 2.4. Học Xung Đột & Quay Lui Phi Tuần Tự (CDCL & Non-Chronological Backtracking)
Khi một nhánh gán giá trị dẫn đến mâu thuẫn (Conflict — miền giá trị biến trở thành rỗng):

1. **Phân tích xung đột (Conflict Analysis)**: Bộ giải duyệt ngược đồ thị suy diễn (*Implication Graph*) từ nút mâu thuẫn về phía các quyết định nhánh ban đầu.
2. **Tìm 1UIP (First Unique Implication Point)**: Điểm nút logic duy nhất mà mọi luồng suy diễn mâu thuẫn đều phải đi qua ở tầng quyết định hiện tại.
3. **Sinh Learned Clause**: Một mệnh đề mới được suy ra: "Sự kết hợp các phép gán này là bất khả thi!".
4. **Nhảy lùi (Backjumping)**: Khác với CP truyền thống chỉ lùi về bước trước đó 1 bước ($d \to d - 1$), CDCL nhảy thẳng về tầng sâu nhất liên quan đến xung đột (có thể từ tầng 20 lùi thẳng về tầng 3).
5. **Cắt tỉa vĩnh viễn**: Mệnh đề học được này được lưu vào bộ nhớ cơ sở dữ liệu mệnh đề (*Clause DB*), đảm bảo bộ giải **không bao giờ đi vào bất kỳ nhánh tìm kiếm nào khác có cùng cấu trúc mâu thuẫn này trong tương lai**.

---

## 3. Các Thành Phần Tối Ưu Hóa Nâng Cao

### 3.1. Tiền Xử Lý (Presolve Engine)
Trước khi bước vào vòng lặp tìm kiếm chính, CP-SAT chạy một chuỗi các kỹ thuật đơn giản hóa bài toán cực kỳ mạnh mẽ:
- **Variable Elimination & Substitution**: Khử các biến phụ thuộc tuyến tính hoặc biến trung gian.
- **Linear Constraint Tightening**: Siết chặt hệ số ma trận bằng phân tích cận trên/cận dưới (GCD reduction).
- **Probing**: Thử gán tạm một biến nhị phân $x = 1$, thực hiện suy diễn lan truyền; nếu sinh mâu thuẫn thì cố định vĩnh viễn $x = 0$; nếu suy ra $y = 1$ thì bổ sung ràng buộc $x \le y$.
- **Symmetry Breaking Detection**: Phát hiện các hoán vị đối xứng trong bài toán để cố định thứ tự, giảm kích thước không gian tìm kiếm.

### 3.2. Đa Luồng Song Song (Portfolio Search Architecture)
Khi kích hoạt chế độ đa luồng (`num_workers = 8` hoặc `16`), CP-SAT phân bổ các worker chạy nhiều chiến lược hoàn toàn khác nhau nhưng cùng đọc/ghi vào một bộ nhớ chia sẻ (*Shared Memory*):

| Nhóm Worker | Chiến lược tìm kiếm | Vai trò trong hệ thống |
| :--- | :--- | :--- |
| **Worker 1 - 2** | CDCL / SAT Search với heuristics VSIDS / LRB | Tìm nghiệm khả thi nhanh và chứng minh tính bất khả thi ở các nhánh con. |
| **Worker 3 - 4** | **LNS (Large Neighborhood Search)** | Nhận nghiệm tốt nhất hiện có, "đóng băng" 80% biến, giải bài toán con trên 20% biến còn lại để cải thiện hàm mục tiêu cục bộ. |
| **Worker 5 - 6** | LP Relaxation (Linear Programming Simplex) | Thả lỏng bài toán nguyên về bài toán liên tục để tính toán cận dưới/cận trên lý thuyết (*Dual Bounds*). |
| **Worker 7 - 8** | Randomized Search & Frequent Restarts | Đột phá khỏi các thung lũng cục bộ bằng cách gieo seed ngẫu nhiên và khởi động lại chu kỳ tìm kiếm. |

### 3.3. Tối Ưu Hóa Hàm Mục Tiêu (Objective Optimization)
Để tối ưu hóa hàm mục tiêu $\min \sum c_i x_i$:
- **Core-guided Search (MaxSAT)**: Tìm tập xung đột tối thiểu (*Unsatisfiable Core*), nới lỏng dần các ràng buộc mềm để nâng dần cận dưới (*lower bound*).
- **Branch-and-Bound với Dynamic Cutoff**: Mỗi khi tìm được nghiệm khả thi với giá trị mục tiêu $Z^*$, bộ giải tự động nạp thêm ràng buộc:
  $$\sum c_i x_i < Z^*$$
  và tiếp tục giải bài toán SAT tìm kiếm nghiệm tốt hơn.

---

## 4. Điểm Mạnh, Hạn Chế & Phạm Vi Ứng Dụng

### 4.1. Điểm mạnh
- **Độ tin cậy toán học tuyệt đối**: Khi CP-SAT trả về trạng thái `OPTIMAL`, đó là nghiệm tối ưu toàn cục được chứng minh bằng toán học (không tồn tại nghiệm nào tốt hơn).
- **Cực kỳ mạnh với bài toán logic rời rạc**: Vượt trội hơn hẳn các bộ giải MIP truyền thống (như SCIP, CBC) trong các bài toán xếp lịch (Scheduling), chuỗi thời gian (Routing/Sequencing) và bài toán đóng gói (Packing).

### 4.2. Hạn chế cấu trúc
- **Chỉ nhận hệ số nguyên (Pure Integer Requirement)**: Tất cả biến và hệ số mục tiêu/ràng buộc đều phải là số nguyên ($32\text{-bit}$ hoặc $64\text{-bit}$). Mọi số thực (float) phải được chuẩn hóa qua hệ số phóng đại ($\text{SCALE}$).
- **Bùng nổ tổ hợp biến chuỗi (Combinatorial Explosion)**: Trong các bài toán định tuyến hay chuỗi công việc, số lượng biến chuyển tiếp nhị phân $z_{ijt}$ tăng theo $O(M \cdot N^2)$. Khi $N \ge 100$, số biến vượt ngưỡng hàng chục nghìn khiến bộ giải rơi vào trạng thái bão hòa bộ nhớ hoặc hết thời gian (Timeout).

---

## 5. Tham Chiếu

1. Ohrimenko, P., Stuckey, P. J., & Codish, M. (2009). *Propagation via lazy clause generation*. Constraints, 14(3), 357-391.
2. Perron, L., & Furnon, V. *OR-Tools CP-SAT Solver*. Google LLC.
3. Van Hentenryck, P. *Discrete Optimization Course* (Coursera / University of Melbourne).
4. Cài đặt chi tiết mô hình hóa cho bài toán SecOps: [`cpsat_implementation.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/cpsat_implementation.md).

