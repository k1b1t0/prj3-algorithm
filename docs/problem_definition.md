# Mô Tả Bài Toán: Lập Lịch Vá Lỗ Hổng An Ninh Mạng Đa Đội Đa Kỹ Năng

> **Tên bài toán**: Lập kế hoạch phân bổ và tối ưu hóa chuỗi công việc vá lỗ hổng an ninh mạng đa mục tiêu trong chu kỳ Sprint Agile (**Bi-Objective Agile SecOps Scheduling**).  
> **Định hướng**: Mô hình tác vụ độc lập (Independent Tasks / Decoupled SecOps) — phản ánh trực tiếp thực tế vận hành DevSecOps hiện đại.  
> **Cơ sở học thuật**: Kế thừa và mở rộng từ mô hình phân bổ rủi ro VULCON (*Farris et al., ACM TOPS 2018*), bài toán Knapsack đa năng lực (*Tian et al., C&IE 2022*) và chi phí chuyển đổi ngữ cảnh lập trình viên (*Golfarelli et al., DKE 2013*).

---

## 1. Bối Cảnh Thực Tế

Trong các doanh nghiệp phần mềm phát triển theo mô hình Microservices và Agile:
1. **Sự độc lập của các bản vá an ninh (Atomic Patches)**:
   - Các công cụ quét mã tự động (SAST/DAST/SCA) quét ra hàng trăm lỗ hổng (CVE/CWE) đổ về Backlog.
   - Khác với phát triển tính năng mới (cần thiết kế luồng phụ thuộc), các lỗi an ninh thường là **các bản vá độc lập (atomic patches)**. Do đó không xép đến luồng phụ thuộc giữa các lỗ hổng.
2. **Gom cụm tự nhiên bằng Chi phí Chuyển đổi Ngữ Cảnh ($C_{ij}$)**:
   - Cãng lỗ hổng trong cùng repo, model, hoặc cùng skill sẽ có chi phí chuyển đổi thấp.
   - Mục tiêu giảm thiểu $f_2$ sẽ tự động gom các lỗi liên quan về cho cùng một đội giải quyết liền mạch, tránh phân mảnh tư duy (cognitive fatigue).

---

## 2. Các Thực Thể & Tham Số

Xét trong phạm vi **1 chu kỳ Sprint cố định** ($\tau$, thông thường 2 tuần làm việc).

| Nhóm Thực thể | Ký hiệu | Thuộc tính & Tham số chính | Ý nghĩa trong Sprint |
| :--- | :--- | :--- | :--- |
| **Backlog Lỗ hổng** | $\mathcal{V} = \{1, \dots, N\}$ | • $u_i \in (0, 1]$: Utility rủi ro động<br>• $e_i \in \mathbb{Z}^+$: Effort (Story Points)<br>• $\text{repo}_i, \text{mod}_i, \text{skill}_i$: Ngữ cảnh mã & kỹ năng<br>• $\text{disc}_i, \text{dead}_i$: Sprint phát hiện & hạn chót SLA | Tập các tác vụ vá lỗi cần lập lịch khắc phục hoặc hoãn |
| **Đội ngũ Kỹ thuật** | $T = \{1, \dots, M\}$ | • $\text{cap}_t$: Trần năng lực Sprint (VD: 30 SP)<br>• $\mathbf{k}_t = [k_{t, s}] \in [0, 1]$: Năng lực chuyên môn an ninh | Nguồn lực song song thực thi các tác vụ được giao |

### 2.1. Backlog Lỗ Hổng An Ninh ($\mathcal{V} = \{1, 2, \dots, N\}$)
Mỗi công việc vá lỗ hổng $i \in \mathcal{V}$ mang các thuộc tính:
- $\text{repo}_i$: Kho mã nguồn chứa lỗi.
- $\text{mod}_i$: Module hoặc Microservice bị ảnh hưởng.
- $\text{skill}_i$: Nhóm kỹ năng chuyên môn cần thiết (chuẩn hóa theo 10 phân loại OWASP Top 10).
- $e_i \in \mathbb{Z}^+$: Điểm công sức ước lượng (Story Points).
- $r_i \in [0.0, 10.0]$: Điểm rủi ro kỹ thuật gốc theo thang CVSS Base Score.
- $\text{disc}_i$: Sprint phát hiện lỗ hổng.
- $\text{dead}_i$: Hạn chót cam kết SLA phải khắc phục.

Ví dụ:
```json
{
  "id": 34916,
  "title": "java.spring.security.audit.spring-csrf-disabled",
  "repository": "train-ticket",
  "asset_module": "ts-order-service",
  "skill": "SKILL_A07",
  "r_i": 6.5,
  "e_i": 8,
  "earliest_sprint": 3,
  "deadline_sprint": 6
}
```

### 2.2. Đội Ngũ Lập Trình Viên Đa Kỹ Năng ($T = \{1, 2, \dots, M\}$)
Mỗi đội kỹ thuật $t \in T$ có:
- $\text{cap}_t$: Tổng năng lực xử lý trong Sprint (chuẩn Scrum: 30 Story Points / đội).
- $\mathbf{k}_t = [k_{t, s}]_{s=1}^{S_{\text{max}}}$: Vector điểm kỹ năng trên các mảng an ninh ($k_{t, s} \in [0.0, 1.0]$).

Ví dụ:
```json
{
  "team_id": "t1",
  "name": "Team 1 (Core & Backend)",
  "capacity_sp": 30,
  "skills": {
    "SKILL_A01": 0.9,
    "SKILL_A02": 0.5,
    "SKILL_A03": 0.5,
    "SKILL_A04": 0.7,
    "SKILL_A05": 0.6,
    "SKILL_A06": 0.4,
    "SKILL_A07": 0.95,
    "SKILL_A08": 0.6,
    "SKILL_A09": 0.5,
    "SKILL_A10": 0.4
  }
}
```

---

## 3. Các Chỉ Số Tính Toán

### 3.1. Điểm Ưu Tiên Giảm Nhẹ Rủi Ro (Mitigation Utility — $u_i(\tau)$)
Điểm ưu tiên của task $i$ tại Sprint $\tau$ (tham khảo công thức từ VULCON) kết hợp giữa mức độ nghiêm trọng an ninh và áp lực thời gian SLA:
$$u_i(\tau) = \alpha \cdot \hat{r}_i + (1 - \alpha) \cdot \hat{p}_i(\tau) \in (0.0, 1.0]$$

- $\hat{r}_i = \frac{r_i}{10.0} \in [0.0, 1.0]$: Chuẩn hóa từ $r_i$.
- $\hat{p}_i(\tau) = \min\left(1.0, \max\left(0.0, \frac{\tau - \text{disc}_i}{\text{dead}_i - \text{disc}_i}\right)^\gamma\right) \in [0.0, 1.0]$: Tỷ lệ tiệm cận hạn chót SLA.
- $\alpha \in [0.0, 1.0]$: Trọng số cân bằng giữa kỹ thuật và thời gian (mặc định $\alpha = 0.6$). Càng gần 1 thì hệ thống càng ưu tiên lỗ hổng rủi ro cao (CVSS), càng gần 0 thì càng ưu tiên các task sắp hết hạn cam kết SLA.
- $\gamma \ge 1.0$: Hệ số lũy thừa gia tốc áp lực SLA (mặc định $\gamma = 1.5$). $\gamma$ càng tăng thì mức độ ưu tiên càng tăng vọt phi tuyến khi task tiệm cận sát deadline $\text{dead}_i$.

### 3.2. Chi Phí Chuyển Đổi Ngữ Cảnh Phân Cấp (Context-Switching Cost — $C_{ij}$)
Khi một đội chuyển tiếp từ task $i$ sang task $j$, chi phí hao tổn tư duy và setup môi trường được mô hình hóa theo cấu trúc 3 cấp:
$$C_{ij} = w_{\text{repo}} \cdot \mathbb{I}(\text{repo}_i \neq \text{repo}_j) + w_{\text{mod}} \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + w_{\text{skill}} \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j)$$

- Trọng số chuẩn hóa: $w_{\text{repo}} + w_{\text{mod}} + w_{\text{skill}} = 1.0$ (với $w_{\text{repo}}, w_{\text{mod}}, w_{\text{skill}} \ge 0$).
  - Giá trị mặc định: $w_{\text{repo}} = 0.5$, $w_{\text{mod}} = 0.3$, $w_{\text{skill}} = 0.2$.

---

## 4. Hệ Thống Ràng Buộc Nghiệp Vụ

1. **Gán đơn nhất (Single Assignment)**: Mỗi task chỉ được giao cho tối đa 1 đội xử lý trong sprint hiện tại. Task không được chọn sẽ lưu lại backlog.
2. **Trần dung lượng Sprint (Knapsack Capacity)**: Tổng Story Points các task gán cho đội $t$ không vượt quá $\text{cap}_t$.
3. **Ngưỡng năng lực kỹ năng (Skill Feasibility)**: Đội $t$ chỉ được nhận task $i$ nếu điểm kỹ năng tương ứng đạt ngưỡng tối thiểu: $k_{t, \text{skill}_i} \ge 0.5$.

---

## 5. Hai Mục Tiêu Tối Ưu Hóa (Bi-Objective Criteria)

Mô hình hướng tới cân bằng giữa an ninh bảo mật và hiệu suất phát triển phần mềm:

1. **Mục tiêu 1: Cực đại hóa Lợi ích Giảm nhẹ Rủi ro ($f_1$ - Mitigation Utility)**
   $$\max f_1 = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i \cdot x_{it}$$

2. **Mục tiêu 2: Cực tiểu hóa Chi phí Chuyển đổi Ngữ cảnh ($f_2$ - Context-Switching Cost)**
   $$\min f_2 = \sum_{t \in T} \sum_{k=1}^{|\pi_t|-1} C_{\pi_t(k), \pi_t(k+1)}$$

3. **Hàm vô hướng hóa chuẩn hóa (Normalized Weighted Sum)**:
   Chuẩn hóa giá trị hai hàm mục tiêu về cùng đoạn $[0.0, 1.0]$ để loại bỏ chênh lệch thang đo:
   $$\hat{f}_1 = \frac{f_1 - f_1^{\min}}{f_1^{\max} - f_1^{\min}}, \quad \hat{f}_2 = \frac{f_2 - f_2^{\min}}{f_2^{\max} - f_2^{\min}}$$
   Hàm mục tiêu vô hướng hóa với trọng số $w \in [0.0, 1.0]$:
   $$\max Z(w) = w \cdot \hat{f}_1 - (1 - w) \cdot \hat{f}_2$$
   - Trọng số $w$ phản ánh mức độ ưu tiên giữa giảm thiểu rủi ro an ninh ($w \to 1$) và giữ độ tập trung ngữ cảnh cho lập trình viên ($w \to 0$).

---

## 6. Cơ Chế Xác Định Cận Chuẩn Hóa Tĩnh (Static Bounds)

Các giá trị cận $(f^{\min}, f^{\max})$ được tính toán như một thuộc tính tĩnh của bài toán (Instance Property), hoàn toàn độc lập với thuật toán giải:

1. **Đối với $f_1$ (Mitigation Utility)**:
   - $f_1^{\min} = 0$: Không hoàn thành task nào.
   - $f_1^{\max}$: Nghiệm của bài toán Fractional Knapsack với tổng dung lượng $\sum_{t \in T} \text{cap}_t$.
2. **Đối với $f_2$ (Context Switch Cost)**:
   - $f_2^{\min} = 0$: Trường hợp lý tưởng nhất (không phát sinh chi phí chuyển đổi).
   - $f_2^{\max}$: Cận trên số bước chuyển đổi vật lý ($K_{\max} - M$, với $K_{\max}$ là số lượng task tối đa nhặt được theo greedy effort nhỏ nhất chạm trần $\sum \text{cap}_t$, mỗi bước chuyển đổi có chi phí tối đa là $1.0$):
     $$f_2^{\max} = K_{\max} - M$$



