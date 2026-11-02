# Giải Thích Chi Tiết Thuật Toán NSGA-II, Pareto Front & Chỉ Số Hypervolume — Project 3

> **Tài liệu nghiên cứu**: Hướng dẫn toàn diện về Thuật toán Tiến hóa Đa Mục tiêu (NSGA-II), Cơ chế Lai ghép/Đột biến, Khái niệm Mặt Pareto và Chỉ số Hypervolume (HV).

---

## 1. Thuật Toán NSGA-II Hoạt Động Như Thế Nào Trong Project 3?

NSGA-II (Non-dominated Sorting Genetic Algorithm II) là thuật toán tiến hóa đa mục tiêu nổi tiếng nhất trong giới khoa học (Deb et al., IEEE TEVC 2002). Trong Project 3, thay vì chỉ tìm 1 phương án duy nhất, NSGA-II nuôi dưỡng một **quần thể gồm P phương án xếp lịch** và cho chúng "tiến hóa" qua G thế hệ để tìm ra những phương án tốt nhất.

### 1.1. Biểu Diễn Một Phương Án Xếp Lịch (Nhiễm Sắc Thể — Chromosome)
Để vừa chọn việc, vừa gán team, vừa giữ thứ tự topo, mỗi cá thể được mã hóa thành **2 chuỗi số nguyên**:
- **Phần 1: Chuỗi ưu tiên Topo (Topological Priority List)**: Một hoán vị của toàn bộ N task trong backlog, luôn thỏa mãn thứ tự topo của đồ thị DAG (task cha luôn đứng trước task con).  
  *Ví dụ N = 6*: `[Task 1, Task 2, Task 3, Task 4, Task 5, Task 6]` (với Task 1 là cha của Task 4).
- **Phần 2: Vector chỉ định Team (Team Assignment Vector)**: Mỗi phần tử là một số nguyên từ `1` đến `M` chỉ định team nào phụ trách task đó, hoặc `0` nghĩa là hoãn sang sprint sau.  
  *Ví dụ M = 2 teams*: `[Team 1, Team 1, Team 2, Team 1, Team 2, 0]`

### 1.2. Bộ Giải Mã Topo (Topological Decoder — Bí Quyết Để Không Bị Lỗi)
Nếu lai ghép ngẫu nhiên thì phương án sinh ra rất dễ bị lỗi (quá dung lượng team hoặc vi phạm cha-con). Do đó, thuật toán sử dụng một **Bộ giải mã thông minh**:
- Thuật toán duyệt lần lượt từng task theo thứ tự trong Chuỗi ưu tiên.
- Khi xét task `v` được gán cho Team `t`:
  1. Kiểm tra: Team `t` có điểm kỹ năng với task `v` đạt >= 0.5 không?
  2. Kiểm tra: Dung lượng còn lại của Team `t` có đủ `e_v` Story Points không?
  3. Kiểm tra ràng buộc cha-con: Toàn bộ task cha của `v` đã được Team `t` nhận trong sprint này chưa?
- **Nếu thỏa mãn cả 3**: Nhận task `v` vào lịch của Team `t` và trừ dung lượng.
- **Nếu vi phạm bất kỳ điều nào**: Bỏ qua task `v` (để sang backlog sprint sau).  
-> **Kết quả**: 100% phương án sinh ra bởi NSGA-II đều **hợp lệ tuyệt đối**, không bao giờ bị lỗi toán học!

### 1.3. Cơ Chế Lai Ghép (Crossover) Hoạt Động Thế Nào?
Lai ghép là việc kết hợp ưu điểm của Lịch Bố và Lịch Mẹ để tạo ra Lịch Con:
- Dùng giải thuật **Order Crossover (OX)** trên Chuỗi ưu tiên:
  - Chọn 1 đoạn ngẫu nhiên từ Lịch Bố và sao chép y nguyên sang Lịch Con.
  - Các vị trí còn lại điền theo thứ tự xuất hiện của các task trong Lịch Mẹ (bỏ qua những task đã có).
  - *Ví dụ*: Bố = `[1, 2, 3, 4, 5]`, Mẹ = `[3, 5, 2, 1, 4]`. Cắt đoạn `[2, 3]` từ Bố. Phần còn lại điền từ Mẹ sẽ ra Con = `[5, 2, 3, 1, 4]`.
  - Không bao giờ sinh ra task bị trùng lặp hay thiếu sót.
- Vector gán Team được lai ghép theo kiểu cắt điểm đơn (Single-point crossover).

### 1.4. Cơ Chế Đột Biến (Mutation) Hoạt Động Thế Nào?
Đột biến giúp thuật toán thoát khỏi bẫy cực trị cục bộ (tránh bị tắc nghẽn ở các phương án tầm thường):
1. **Đột biến Đổi Team (Team Mutation)**: Chọn ngẫu nhiên một task và đổi sang cho một team khác có đủ kỹ năng.
2. **Đột biến Đổi Chỗ (Swap Mutation)**: Chọn 2 task độc lập trong DAG (không có quan hệ cha-con) và đổi chỗ thứ tự ưu tiên của chúng.

---

## 2. Tại Sao Cần "Random Seeds", "Mean", "Std" và "Bốc 5 Tập Task (Instances)"?

Trong nghiên cứu khoa học, một thuật toán không thể chỉ chạy 1 lần rồi tuyên bố "tôi giỏi nhất". Bạn cần chứng minh tính ổn định và tính khách quan qua 2 cấp độ:

### 2.1. Tại Sao Phải Bốc 5 Tập Task Khác Nhau (5 Instances)?
- Trong kho dữ liệu thực tế, bạn có **2.103 task** rải rác trên 76 module và 6 repo.
- Nếu bạn chỉ bốc đúng 1 tập 40 task để test: Rất có thể tình cờ tập 40 task đó toàn nằm trong cùng 1 module (bài toán quá dễ) hoặc toàn nằm rải rác 40 repo khác nhau (bài toán quá khó).
- Vì vậy, ta phải bốc ngẫu nhiên **5 tập task độc lập (5 instances)**:
  - Instance 1: Nhiều task cùng module Auth.
  - Instance 2: Nhiều task nằm ở tầng Gateway và Payment.
  - Instance 3, 4, 5: Phân bổ ngẫu nhiên khác nhau.
- Mục đích: Chứng minh thuật toán chạy tốt trên **mọi thể loại dự án**, không phụ thuộc vào may rủi dữ liệu.

### 2.2. Tại Sao Cần "Random Seed", "Mean" và "Std Dev"?
- Thuật toán tiến hóa NSGA-II có dùng hàm ngẫu nhiên (`random()` khi khởi tạo, lai ghép, đột biến).
- Nếu chạy 1 lần: Có thể lần đó thuật toán "may mắn" vớ được phương án ngon ngay từ đầu.
- Do đó, với mỗi instance, ta chạy lặp lại **5 lần với 5 Random Seed khác nhau** (seed = 42, 100, 2024, 999, 1234).
- Kết quả thu được 5 con số, ta tính:
  - **Giá trị trung bình (Mean)**: Thể hiện năng lực thực tế trung bình của thuật toán.
  - **Độ lệch chuẩn (Standard Deviation — Std)**: Thể hiện độ ổn định. Ví dụ: `Mean = 85, Std = 1.2` nghĩa là thuật toán chạy cực kỳ ổn định, lần nào cũng ra kết quả quanh mốc 85 điểm, không bị trồi sụt thất thường.

---

## 3. Bản Chất Mặt Pareto & Chỉ Số Hypervolume (HV)

Đây là phần trả lời trực tiếp cho khúc mắc của bạn: *"Tại sao mỗi thuật toán có 1 đường Pareto khác nhau rồi, nhìn vào là thấy, thì cần gì chỉ số Hypervolume (HV) nữa?"*

### 3.1. Mặt Pareto (Pareto Front) Trên Đồ Thị 2 Chiều
Mỗi phương án xếp lịch là 1 điểm trên hệ trục tọa độ 2 chiều:
- Trục X: Tổng Lợi ích Rủi ro giải quyết (`f1`, càng sang PHẢI càng tốt).
- Trục Y: Tổng Chi phí Đổi ngữ cảnh (`f2`, càng xuống DƯỚI càng tốt).

Góc **DƯỚI - PHẢI** là góc "Thiên đường" (Vừa diệt tối đa rủi ro, vừa tốn ít chi phí chuyển đổi nhất).

```text
Chi phí đổi ngữ cảnh (f2 - Càng thấp càng tốt)
  ▲
  │  [Bị thống trị]
  │       x
  │
10│       ● (Nghiệm A: f1=60, f2=10)
  │        \
 6│         ● (Nghiệm B: f1=80, f2=6)
  │          \
 3│           ● (Nghiệm C: f1=95, f2=3)  <-- ĐƯỜNG PARETO FRONT
  │
 0└────────────────────────────────────────► Lợi ích rủi ro (f1 - Càng cao càng tốt)
  0       60       80       95
```

- Các điểm `A, B, C` nối lại thành **Mặt Pareto (Pareto Front)**. 
- Nghiệm `x` nằm thụt lùi vào trong bị gọi là "nghiệm bị thống trị" (vì cùng tốn chi phí đó mà diệt ít rủi ro hơn, hoặc cùng mức rủi ro đó mà tốn nhiều chi phí hơn).

---

### 3.2. Tại Sao Cần Chỉ Số Hypervolume (HV) Mà Không Thể Chỉ Nhìn Bằng Mắt?

Giả sử bạn chạy 2 thuật toán: **Thuật toán Đề Xuất** (Đường Xanh) và **Thuật toán Đối Sánh** (Đường Đỏ). Khi vẽ lên đồ thị, bạn sẽ gặp tình huống sau:

```text
Chi phí f2
  ▲
  │        Đường Đỏ (Đối sánh)
  │          \   \
  │           \   ●─────● (Đỏ cắt Xanh)
  │            \ /
  │             X
  │            / \
  │           ●───●  Đường Xanh (Đề xuất)
  │
  └────────────────────────────────► Rủi ro f1
```

#### Tình huống thực tế trong nghiên cứu:
1. **Hai đường Pareto CẮT NHAU**: Ở đoạn rủi ro thấp thì thuật toán Đỏ tốt hơn một chút, nhưng ở đoạn rủi ro cao thì thuật toán Xanh lại vượt trội hơn hẳn. Nhìn bằng mắt **không thể kết luận thuật toán nào tổng thể xịn hơn**!
2. **Không thể in hình vẽ vào bảng so sánh tổng hợp**: Khi bạn làm bảng so sánh trên 15 kịch bản khác nhau, bạn không thể nhét 15 cái hình vẽ vào bảng được. Bạn bắt buộc phải có **một con số định lượng duy nhất** để kết luận: *"Thuật toán của tôi vượt trội hơn đối thủ 18.5%"*.

#### Chỉ số Hypervolume (HV) Làm Nhiệm Vụ Gì?
Hypervolume chọn một **Điểm tồi tệ nhất làm chuẩn (Reference Point - Ref)**, ví dụ điểm `Ref = (f1_min, f2_max)`.

**Hypervolume chính là DIỆN TÍCH (hoặc Thể tích) của vùng không gian nằm giữa Mặt Pareto và Điểm chuẩn Ref:**

```text
Chi phí f2
  ▲
  │   Ref ┌────────────────────────┐
  │       │////////////////////////│  <--- DIỆN TÍCH HYPERVOLUME (HV)
  │       │/////// VÙNG ĐƯỢC //////│       Được bao phủ bởi Mặt Pareto
  │       │/////// BAO PHỦ ////////│
  │       │////////////////●───────┤ (Nghiệm 1)
  │       │////////////////│       │
  │       │////////////////●───────┤ (Nghiệm 2)
  │       │////////////////////////│
  └───────┴────────────────────────┴────────► Rủi ro f1
```

#### Ý nghĩa khoa học của Hypervolume (HV):
1. **Đo độ hội tụ (Convergence)**: Nếu mặt Pareto của bạn càng tiến sát về góc "Thiên đường" (vừa giải quyết nhiều rủi ro, vừa ít đổi ngữ cảnh), vùng diện tích `HV` sẽ **càng phình to ra**.
2. **Đo độ bao phủ đa dạng (Diversity)**: Nếu mặt Pareto của bạn trải dài, cho người dùng nhiều sự lựa chọn từ an ninh tối đa đến năng suất tối đa, diện tích `HV` cũng sẽ **to hơn**.
3. **Kết luận khoa học bằng 1 con số**: 
   - Nếu `HV của NSGA-II = 0.82`
   - Trong khi `HV của Đối sánh = 0.65`
   - Bạn chứng minh được bằng toán học: **Thuật toán NSGA-II vượt trội hơn đối thủ 26.1% về chất lượng giải pháp đa mục tiêu toàn diện!**

---

## 4. Tóm Tắt Khung Thực Nghiệm Của Đồ Án

1. **Dữ liệu**: Bốc 5 tập task (instances) cho mỗi kịch bản (40 task, 100 task, 500 task) từ kho 2.103 task thực tế.
2. **Chạy test**: Mỗi instance chạy 5 seed ngẫu nhiên cho NSGA-II.
3. **So sánh**:
   - So sánh đơn mục tiêu: Điểm rủi ro `f1`, Chi phí chuyển đổi `f2`, Tỷ lệ giảm chi phí `%`, Thời gian chạy `ms`.
   - So sánh đa mục tiêu toàn diện: Dùng **Chỉ số Hypervolume (HV)** để khẳng định thuật toán nào tạo ra Mặt Pareto xịn hơn.
