# Thiết Kế Kế Hoạch Thực Nghiệm Bóc Tách (Ablation Study Plan)

> **Mục tiêu**: Đề xuất kế hoạch thực nghiệm bóc tách nhằm đánh giá vai trò và đóng góp độc lập của từng thành phần trong thuật toán đề xuất H-CSM.  
> **Nguyên tắc**: Giữ nguyên thuật toán chính (Full H-CSM), xây dựng 4 biến thể cắt giảm (*Ablation Variants*) thông qua các cờ tham số để chạy đối sánh thực nghiệm.  
> **Tài liệu thuật toán gốc**: Tham khảo [`proposed_algorithm.md`](file:///home/kibito/Desktop/repos/project3/research/reports/prj3/proposed_algorithm.md) và mã nguồn tại [`src/solvers/proposed_hcsm/solver.py`](file:///home/kibito/Desktop/repos/project3/prj3-algorithm/src/solvers/proposed_hcsm/solver.py).

---

## 1. Mục Đích Nghiên Cứu & Câu Hỏi Khoa Học

Kế hoạch Ablation Study nhằm trả lời 4 câu hỏi cốt lõi:
1. *Quy hoạch động (Knapsack DP) ở Phase 1 có ưu thế gì so với việc nhặt tham lam theo tỷ số $u_i / e_i$?*
2. *Việc tính đến chi phí chèn đường đi $\Delta C$ trong Phase 2 đóng góp thế nào vào việc kiểm soát chi phí nhảy ngữ cảnh?*
3. *Bước hoán đổi liên đội (Phase 3.1) cải thiện việc phân mảnh công việc ra sao?*
4. *Việc giải Open-TSP bằng Bitmask DP ở Phase 3.2 cải thiện thứ tự thực thi như thế nào so với thứ tự chèn ban đầu?*

---

## 2. Bốn Biến Thể Bóc Tách (Ablation Variants)

```
Full H-CSM (Chuẩn) ──┬──► V1: w/o DP (Thay Knapsack DP bằng Greedy u_i/e_i)
                     ├──► V2: w/o Path-aware (Phân bổ không xét chi phí đường đi)
                     ├──► V3: w/o Inter-Swap (Bỏ bước hoán đổi liên đội)
                     └──► V4: w/o Bitmask DP (Giữ nguyên thứ tự chèn ban đầu)
```

### 2.1. Biến thể 1: w/o DP (Không dùng Knapsack DP)
- **Thao tác**: Ở Phase 1, không chạy bảng 1D Knapsack DP $\Phi_b(c)$. Thay vào đó, sắp xếp các task trong cụm theo mật độ $u_i / e_i$ giảm dần và nhặt tham lam đến khi hết dung lượng $c$.
- **Mục đích kiểm chứng**: Đo lường tác động của việc giải chính xác bài toán ba lô nội cụm lên chỉ số $f_1$.

### 2.2. Biến thể 2: w/o Path-aware (Không tích hợp chi phí đường đi)
- **Thao tác**: Ở Phase 2, triệt tiêu số hạng chi phí đường đi $\Delta C$, chỉ phân bổ dựa trên mật độ lợi ích:
  $$\eta'(b, c, t) = \frac{w \cdot \Phi_b(c) / f_1^{\max}}{c}$$
- **Mục đích kiểm chứng**: Đo lường mức độ kiểm soát chi phí nhảy ngữ cảnh ($f_2$) của cơ chế khấu hao đường đi.

### 2.3. Biến thể 3: w/o Inter-Swap (Bỏ bước hoán đổi liên đội)
- **Thao tác**: Bỏ qua hàm `consolidate_inter_team_quotients` (Phase 3.1), chuyển thẳng từ kết quả phân bổ của Phase 2 sang Phase 3.2.
- **Mục đích kiểm chứng**: Đánh giá vai trò của việc gom gọn cụm giữa các đội đối với $f_2$.

### 2.4. Biến thể 4: w/o Bitmask DP (Bỏ bước giải chính xác Open-TSP)
- **Thao tác**: Ở Phase 3.2, bỏ thuật toán Bitmask DP, giữ nguyên thứ tự xuất hiện của các cụm theo kết quả chèn từ Phase 2.
- **Mục đích kiểm chứng**: Xác định mức cải thiện thứ tự chuỗi hành trình khi giải tối ưu bằng Bitmask DP.

---

## 3. Cơ Chế Tham Số Hóa Trong Mã Nguồn

Để phục vụ chạy thử nghiệm bóc tách, `ProposedHCSMSolver` hỗ trợ 4 cờ điều khiển:

```python
class ProposedHCSMSolver(BaseSolver):
    def __init__(
        self,
        name: str = "Proposed-H-CSM",
        use_dp: bool = True,                 # Tắt -> Biến thể V1 (w/o DP)
        path_aware: bool = True,             # Tắt -> Biến thể V2 (w/o Path-aware)
        enable_inter_team_swap: bool = True, # Tắt -> Biến thể V3 (w/o Inter-Swap)
        use_bitmask_tsp: bool = True,        # Tắt -> Biến thể V4 (w/o Bitmask DP)
        ...
    ):
```

---

## 4. Mẫu Bảng Báo Cáo Thực Nghiệm Đối Sánh

Bảng tổng hợp kết quả thực nghiệm sau khi chạy benchmark trên các kịch bản:

| Cấu hình thuật toán | $f_1$ (Lợi ích an ninh $\uparrow$) | $f_2$ (Chi phí ngữ cảnh $\downarrow$) | Điểm tổng hợp $Z(w) \uparrow$ | Runtime ($ms$) | Đánh giá / Ghi chú |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Full H-CSM** | TBD | TBD | TBD | TBD | Cấu hình đầy đủ 3 pha chuẩn |
| *V1 (w/o DP)* | TBD | TBD | TBD | TBD | Đánh giá vai trò của Knapsack DP |
| *V2 (w/o Path-aware)* | TBD | TBD | TBD | TBD | Đánh giá vai trò của cơ chế chèn đường đi |
| *V3 (w/o Inter-Swap)* | TBD | TBD | TBD | TBD | Đánh giá vai trò của hoán đổi liên đội |
| *V4 (w/o Bitmask DP)* | TBD | TBD | TBD | TBD | Đánh giá vai trò của Bitmask DP |
