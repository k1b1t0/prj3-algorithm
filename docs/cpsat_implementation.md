# Thiết Kế & Cài Đặt OR-Tools CP-SAT (Baseline 2: Exact Solver)

> **Mục tiêu**: Giải chính xác mô hình quy hoạch nguyên đa mục tiêu (MO-MILP) kết hợp định tuyến (Open-TSP) để thiết lập cận chuẩn vàng (Exact Reference Bound) trên kịch bản nhỏ ($N=40$).  
> **File mã nguồn**: [`src/solvers/ortools_cpsat.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/ortools_cpsat.py)

---

## 1. Pipeline Năm Giai Đoạn

- **Giai đoạn 1 (Tiền xử lý)**: Lọc trước các task bất khả thi ($k_{t, \text{skill}} < 0.5$) để giảm số biến.
- **Giai đoạn 2 (Biến quyết định)**: Khởi tạo biến nhị phân phân bổ $x_{it}$, biến hành trình $z_{u,v,t}$ và biến vị trí MTZ $pos_{it}$.
- **Giai đoạn 3 (Thiết lập ràng buộc)**: Gán đơn nhất, trần dung lượng Sprint, bảo toàn luồng và triệt tiêu chu trình MTZ.
- **Giai đoạn 4 (Nguyên hóa hàm mục tiêu)**: Nhân phóng đại `SCALE = 100,000` đưa hàm mục tiêu vô hướng hóa $Z(w)$ về số nguyên.
- **Giai đoạn 5 (Giải & Đánh giá độc lập)**: Chạy 8 luồng CPU, trích xuất chuỗi và chấm điểm lại bằng hàm số thực `evaluate_sprint_plan`.

---

## 2. Giai Đoạn 1: Tiền Lọc Không Gian Biến

Lọc bớt theo ngưỡng kỹ năng để giảm bớt số biến nhị phân:

```python
eligible_tasks = {
    t: [i for i in range(N) if teams[t].get_skill_score(tasks[i].skill) >= skill_thresh]
    for t in range(M)
}
```

---

## 3. Giai Đoạn 2: Không Gian Biến Quyết Định

1. **Biến phân bổ công việc ($x_{it} \in \{0, 1\}$)**:
   ```python
   x[i, t] = model.NewBoolVar(f"x_{i}_{t}")
   ```
2. **Biến hành trình chuyển tiếp ($z_{u, v, t} \in \{0, 1\}$)**:
   Thêm cặp đỉnh ảo $S$ (bắt đầu) và $E$ (kết thúc) cho hành trình hở:
   ```python
   z[i, j, t]   = model.NewBoolVar(f"z_{i}_{j}_{t}") # Task i sang Task j
   z["S", i, t] = model.NewBoolVar(f"z_S_{i}_{t}")   # Task dau tien cua doi t
   z[i, "E", t] = model.NewBoolVar(f"z_{i}_E_{t}")   # Task cuoi cung cua doi t
   z["S", "E", t] = model.NewBoolVar(f"z_S_E_{t}")   # Doi t rong (khong nhan task nao)
   ```
3. **Biến thứ tự vị trí ($pos_{it} \ge 0$)**:
   ```python
   pos[i, t] = model.NewIntVar(0, k_tasks, f"pos_{i}_{t}")
   ```

---

## 4. Giai Đoạn 3: Hệ Thống Ràng Buộc

Sử dụng ràng buộc đại số `model.Add(...)` kết hợp mệnh đề logic điều kiện `.OnlyEnforceIf(...)`:

### 4.1. Gán đơn nhất (Single Assignment)
Mỗi task chỉ được giao tối đa cho 1 đội:
```python
for i in range(N):
    cand = [x[i, t] for t in range(M) if (i, t) in x]
    if cand:
        model.Add(sum(cand) <= 1)
```

### 4.2. Dung lượng Sprint (Knapsack Capacity)
Tổng Story Points của các task giao cho đội $t$ không vượt quá trần dung lượng:
```python
for t in range(M):
    cand = [tasks[i].e_i * x[i, t] for i in eligible_tasks[t]]
    model.Add(sum(cand) <= teams[t].capacity_sp)
```

### 4.3. Kích hoạt vị trí thứ tự
Task có làm ($x_{it}=1$) thì vị trí $pos \ge 1$; không làm ($x_{it}=0$) thì $pos = 0$:
```python
for i in eligible_tasks[t]:
    model.Add(pos[i, t] == 0).OnlyEnforceIf(x[i, t].Not())
    model.Add(pos[i, t] >= 1).OnlyEnforceIf(x[i, t])
```

### 4.4. Bảo toàn luồng ảo
Mỗi đội luôn có đúng 1 luồng rời khỏi $S$ và 1 luồng đi vào $E$:
```python
model.Add(sum(z["S", i, t] for i in t_tasks) + z["S", "E", t] == 1)
model.Add(sum(z[i, "E", t] for i in t_tasks) + z["S", "E", t] == 1)
```

### 4.5. Bảo toàn luồng tại từng Task
Nếu task $i$ được chọn làm ($x_{it}=1$), phải có đúng 1 cung đi vào và 1 cung đi ra:
```python
for i in t_tasks:
    in_arcs = [z[j, i, t] for j in t_tasks if (j, i, t) in z] + [z["S", i, t]]
    model.Add(sum(in_arcs) == x[i, t])

    out_arcs = [z[i, j, t] for j in t_tasks if (i, j, t) in z] + [z[i, "E", t]]
    model.Add(sum(out_arcs) == x[i, t])
```

### 4.6. Triệt tiêu chu trình con MTZ (Subtour Elimination)
Neo task đầu tiên có $pos=1$, và mỗi bước chuyển tiếp $i \to j$ làm tăng thứ tự vị trí:
```python
model.Add(pos[i, t] == 1).OnlyEnforceIf(z["S", i, t])

for i in t_tasks:
    for j in t_tasks:
        if i != j:
            model.Add(pos[j, t] >= pos[i, t] + 1).OnlyEnforceIf(z[i, j, t])
```

---

## 5. Giai Đoạn 4: Nguyên Hóa Hàm Mục Tiêu

Vì CP-SAT chỉ tối ưu hóa trên số nguyên, toàn bộ hệ số của hàm mục tiêu vô hướng hóa $Z(w)$ được nhân với `SCALE = 100,000` rồi làm tròn nguyên:

```python
SCALE = 100_000
coeff_u = (w_val / f1_span) * SCALE
coeff_c = ((1.0 - w_val) / f2_span) * SCALE

obj_terms = []
for (i, t), var in x.items():
    u_i = tasks[i].compute_utility(current_sprint=current_sprint)
    obj_terms.append(int(round(u_i * coeff_u)) * var)

for (u, v, t), var in z.items():
    if u != "S" and v != "E":
        obj_terms.append(-int(round(c_dist[u][v] * coeff_c)) * var)

model.Maximize(sum(obj_terms))
```

---

## 6. Giai Đoạn 5: Cấu Hình Bộ Giải & Đánh Giá Độc Lập

```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0  # Gioi han thoi gian
solver.parameters.num_workers = 8             # 8 luong tim kiem song song
status = solver.Solve(model)
```

1. Trích xuất thứ tự công việc thực tế $\pi_t$ từ các biến $z_{u,v,t} == 1$.
2. Đánh giá lại bằng hàm số thực `evaluate_sprint_plan(...)` để đảm bảo tính chuẩn xác và đồng nhất tuyệt đối giữa các thuật toán.

---

## 7. Phân Tích Thực Nghiệm: Cận Chuẩn Vàng & Ngưỡng Timeout

| Quy mô kịch bản | Số biến chuỗi $z_{ijt}$ | Thời gian chạy CP-SAT | Kết quả thu được |
| :--- | :--- | :--- | :--- |
| **Nhỏ ($N=40$)** | $\approx 400$ biến | **60.2 giây** | **Tìm ra nghiệm Pareto tối ưu toàn cục ($Z=0.431$)** $\to$ Đóng vai trò chuẩn vàng để đo Optimality Gap. |
| **Lớn ($N \ge 100$)** | $O(M \cdot N^2) > 80{,}000$ biến | **Timeout (60.0s)** | **Không tìm được nghiệm khả thi** $\to$ Bằng chứng khoa học khẳng định solver chính xác không thể áp dụng cho hệ thống thời gian thực. |
