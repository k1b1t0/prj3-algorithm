## 1. Tham Số Thực Nghiệm Cố Định

| Tham số | Giá trị | Ý nghĩa nghiệp vụ |
| :--- | :---: | :--- |
| $\alpha, 1 - \alpha$ | $0.6, 0.4$ | Trọng số mức nghiêm trọng CVSS và thời gian tiệm cận SLA. |
| $\gamma$ | $1.5$ | Bậc lũy thừa tăng tốc áp lực hạn chót. |
| $w_{\text{repo}}, w_{\text{mod}}, w_{\text{skill}}$ | $0.5, 0.3, 0.2$ | Trọng số khoảng cách ngữ cảnh ($C_{ij} \in [0.0, 1.0]$). |
| $\text{skill\_threshold}$ | $0.5$ | Ngưỡng năng lực tối thiểu để đội được nhận task. |
| $\text{cap}_t$ | $30\text{ SP}$ | Dung lượng định mức chuẩn Scrum của mỗi đội trong Sprint. |
| $w$ | $\{0.25, 0.50, 0.75\}$ | Trọng số cân bằng Pareto trong hàm $Z(w)$. |

---

## 2. Kế Hoạch A: Thực Nghiệm Đơn Sprint (Static Snapshot)

Đánh giá chất lượng lập lịch tại một Sprint cố định ($\tau = 4$).

### 2.1. Cấu Hình 3 Kịch Bản
| Kịch bản | Số Task ($N$) | Số Đội ($M$) | Tổng Dung Lượng |
| :--- | :---: | :---: | :---: |
| **`small_40`** | $40$ tasks | 2 đội | $60\text{ SP}$ |
| **`medium_100`** | $100$ tasks | 4 đội | $120\text{ SP}$ |
| **`large_500`** | $500$ tasks | 8 đội | $240\text{ SP}$ |

* **Độ lặp lại**: Mỗi kịch bản chạy 10 lần (10 random seeds), mỗi lần bốc ngẫu nhiên tập task từ kho dữ liệu để tính giá trị trung bình $\text{Mean} \pm \text{Std}$.

### 2.2. Chỉ Số Đo Lường (Metrics)
1. **Lợi ích an ninh ($f_1$)**: Tổng điểm $u_i$ của các task được chọn xử lý ($\uparrow$).
2. **Chi phí chuyển đổi ngữ cảnh ($f_2$)**: Tổng chi phí chuyển đổi repo/module/skill của các đội ($\downarrow$).
3. **Điểm mục tiêu chuẩn hóa ($Z(w)$)**: 
   $$Z(w) = w \cdot \frac{f_1}{f_1^{\max}} - (1 - w) \cdot \frac{f_2}{f_2^{\max}} \quad (\uparrow)$$
4. **Thời gian chạy (Runtime)**: Tính bằng mili-giây (ms) ($\downarrow$).
5. **Khoảng cách tối ưu (Gap/Gain)**: So với CP-SAT trên `small_40` và so với GLS trên `medium_100`, `large_500`.

### 2.3. Bảng Mẫu Báo Cáo Kế Hoạch A (Template)

| Kịch bản | Thuật toán | $f_1$ ($\uparrow$) | $f_2$ ($\downarrow$) | $Z(0.50)$ ($\uparrow$) | Runtime (ms) ($\downarrow$) | Gap / Gain vs GLS |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`small_40`** | OR-Tools CP-SAT | TBD | TBD | TBD | TBD | Mốc chuẩn (60s) |
| | Proposed H-CSM | TBD | TBD | TBD | TBD | TBD |
| | Routing GLS | TBD | TBD | TBD | TBD | Baseline |
| | Greedy-CVSS | TBD | TBD | TBD | TBD | TBD |
| **`medium_100`** | Proposed H-CSM | TBD | TBD | TBD | TBD | TBD |
| | Routing GLS | TBD | TBD | TBD | TBD | Baseline |
| | OR-Tools CP-SAT | — | — | — | Timeout (>60s) | N/A |
| | Greedy-CVSS | TBD | TBD | TBD | TBD | TBD |
| **`large_500`** | Proposed H-CSM | TBD | TBD | TBD | TBD | TBD |
| | Routing GLS | TBD | TBD | TBD | TBD | Baseline |
| | OR-Tools CP-SAT | — | — | — | Timeout / OOM | N/A |
| | Greedy-CVSS | TBD | TBD | TBD | TBD | TBD |

---

## 3. Kế Hoạch B: Thực Nghiệm Chuỗi 8 Sprint Liên Tiếp (Multi-Sprint Rolling)

Mô phỏng chu trình làm việc Agile qua 8 Sprint ($s = 1, \dots, 8$):
- Task giải quyết xong được xóa bỏ; task hoãn bị cộng dồn sang Sprint tiếp theo và tăng điểm ưu tiên do cận deadline.
- Chạy lặp lại trên 10 random seeds độc lập.

### 3.1. Các Chỉ Số Đo Lường Chính
1. **Phơi nhiễm rủi ro tích lũy ($\text{AUC-TVE}$)**: Tổng điểm rủi ro còn tồn đọng qua các Sprint ($\downarrow$).
2. **Số lượt vi phạm hạn chót ($\text{Total Breaches}$)**: Tổng số task bị quá hạn SLA ($\downarrow$).
3. **Tổng chi phí chuyển đổi ($\text{Total } f_2$)**: Tổng chi phí chuyển ngữ cảnh qua 8 Sprint ($\downarrow$).
4. **Tổng điểm đa mục tiêu ($\text{Total } Z(0.5)$)**: Tổng $Z(0.5)$ qua 8 Sprint ($\uparrow$).

### 3.2. Bảng Mẫu Báo Cáo Kế Hoạch B (Template)

| Thuật toán | $\text{AUC-TVE}$ ($\downarrow$) | $\text{Total Breaches}$ ($\downarrow$) | $\text{Total } f_2$ ($\downarrow$) | $\text{Total } Z(0.5)$ ($\uparrow$) | Xếp hạng Chung |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Proposed H-CSM** | TBD | TBD | TBD | TBD | TBD |
| **Routing GLS** | TBD | TBD | TBD | TBD | TBD |
| **Greedy-CVSS** | TBD | TBD | TBD | TBD | TBD |
| **OR-Tools CP-SAT** | N/A | N/A | N/A | N/A | Timeout |
