# Mô Tả Bài Toán Lập Lịch Vá Lỗ Hổng Bảo Mật Đa Đội Đa Kỹ Năng (No-DAG Formulation)

> **Tên bài toán**: Lập kế hoạch phân bổ và tối ưu hóa chuỗi công việc vá lỗ hổng an ninh mạng đa mục tiêu trong chu kỳ Sprint Agile (Bi-Objective Agile SecOps Scheduling with Context-Switch Minimization).  
> **Phiên bản**: No-DAG (Precedence-Free / Decoupled Task Formulation).  
> **Cơ sở học thuật**: Kế thừa và mở rộng toàn diện từ VULCON (Farris et al., ACM TOPS 2018), Tian et al. (C&IE 2022) và Golfarelli et al. (DKE 2013).

---

## 1. Bối Cảnh Thực Tế & Động Lực Thiết Kế

Trong các tổ chức phần mềm vận hành theo mô hình **Agile / DevSecOps**, các công cụ quét tự động (SAST, DAST, SCA) liên tục phát hiện hàng trăm lỗ hổng bảo mật (CVE/CWE) đổ về Product Backlog.

Trong thực tế phát triển phần mềm hiện đại:
1. **Tính độc lập của các bản vá an ninh (Atomic Patches)**: Khác với việc phát triển tính năng mới từ đầu, các lỗi bảo mật (như SQL Injection, XSS, Deserialization, nâng cấp thư viện phụ thuộc) chủ yếu là các bản vá mang tính cục bộ (localized atomic fixes). Lập trình viên làm việc trên các Git feature branches riêng biệt, sử dụng kỹ thuật Mocking/Stubbing và merge độc lập qua Pull Request.
2. **Bản chất của Sprint 2 tuần (Time-boxed Capacity Planning)**: Ở cấp độ lập kế hoạch Sprint, ban quản lý cần quyết định: **Chọn những lỗ hổng nào để vá trong 2 tuần tới, giao cho đội nào, và sắp xếp thứ tự làm việc ra sao để lập trình viên không bị phân mảnh tư duy (cognitive context switching)**.
3. **Sự gắn kết tự nhiên theo Module (Organic Architectural Colocation)**: Các lỗ hổng nằm trong cùng một microservice hoặc repository vốn dĩ có độ liên quan mật thiết. Không cần phải dùng dây xích phụ thuộc (DAG) gượng ép, chính **mục tiêu giảm thiểu chi phí chuyển đổi ngữ cảnh ($f_2$)** sẽ tự động gom các lỗ hổng cùng module về cho cùng một đội giải quyết liên tục.

---

## 2. Các Thực Thể & Thuộc Tính Cốt Lõi

Xét trong phạm vi **1 chu kỳ Sprint cố định** (Sprint $\tau$ kéo dài 2 tuần).

### 2.1. Backlog Lỗ Hổng An Ninh (Vulnerability Tasks)
Tập hợp $N$ công việc vá lỗ hổng đang tồn đọng $\mathcal{V} = \{1, 2, \dots, N\}$. Mỗi công việc mang các thuộc tính:
- **`id`**: Định danh duy nhất của task trong hệ thống issue tracking.
- **`repo`**: Kho chứa mã nguồn (Repository) của task.
- **`asset_module`**: Phân hệ / Microservice cụ thể trong repo.
- **`r_i` (Base Risk)**: Điểm rủi ro kỹ thuật gốc theo chuẩn CVSS (thang điểm $[0.0, 10.0]$).
- **`e_i` (Effort)**: Ước lượng công sức thực hiện, đo bằng Story Points (SP, số nguyên dương).
- **`skill`**: Nhóm kỹ năng chuyên môn cần thiết, ánh xạ theo 10 danh mục chuẩn OWASP Top 10.
- **`earliest_sprint`**: Sprint phát hiện lỗ hổng.
- **`deadline_sprint`**: Hạn chót SLA bắt buộc phải khắc phục xong.

### 2.2. Đội Ngũ Kỹ Thuật (Cross-Functional Teams)
Tập hợp $M$ đội kỹ thuật tham gia Sprint $T = \{1, 2, \dots, M\}$. Mỗi đội $t$ có:
- **`team_id`**: Định danh của đội.
- **`cap_t` (Sprint Capacity)**: Tổng Story Points tối đa mà đội có thể cam kết trong Sprint (ví dụ: chuẩn Scrum 30 SP / team).
- **`skills`**: Điểm số thành thạo của đội trên 10 nhóm kỹ năng OWASP, giá trị trong đoạn $[0.0, 1.0]$.

---

## 3. Hệ Thống Ràng Buộc Nghiệp Vụ

### 3.1. Ràng Buộc Cứng (Hard Constraints)
1. **Gán đơn nhất (Single Assignment)**: Mỗi task trong backlog chỉ được giao cho tối đa một team xử lý, và làm tối đa một lần trong sprint (các task chưa làm sẽ lưu lại backlog cho sprint sau).
2. **Trần dung lượng Sprint (Story Point Capacity Limit)**: Tổng Story Points ($e_i$) của các task giao cho Team $t$ không được vượt quá $\text{cap}_t$.
3. **Ngưỡng năng lực kỹ năng tối thiểu (Skill Threshold $\ge 0.5$)**: Team $t$ chỉ được phép nhận task nếu điểm thành thạo của team đối với nhóm kỹ năng yêu cầu của task đó đạt từ $0.5$ trở lên.

### 3.2. Không Ép Buộc Ràng Buộc Phụ Thuộc Cứng (No Hard DAG Precedence)
- Các task được xem xét độc lập trong quá trình chọn lọc.
- Mọi quan hệ gắn kết kiến trúc giữa các lỗ hổng trong cùng một hệ thống được điều tiết thông qua **Hàm mục tiêu chi phí chuyển đổi ngữ cảnh ($f_2$)**.

---

## 4. Hai Mục Tiêu Tối Ưu Hóa (Bi-Objective Criteria)

### Mục Tiêu 1: Cực Đại Hóa Lợi Ích Giảm Thiểu Rủi Ro (Maximize Mitigation Utility — $f_1$)
Kế thừa triết lý từ VULCON (Farris et al., 2018), điểm lợi ích $u_i$ của từng task phản ánh tính động của rủi ro theo thời gian:
$$u_i = r_i + \alpha \cdot (\tau - \text{earliest\_sprint}_i) + \beta \cdot \max(0, \tau - \text{deadline\_sprint}_i + 1)$$
- Điểm CVSS gốc ($r_i$).
- Điểm thưởng tuổi thọ tồn lưu (Persistence): lỗi tồn tại càng lâu trong backlog càng được ưu tiên xử lý.
- Điểm phạt vi phạm hạn chót (Deadline Urgency): tự động nhảy vọt khi sprint hiện tại chạm hoặc vượt hạn SLA.

$$\max f_1 = \sum_{t \in T} \sum_{i \in \mathcal{V}} u_i \cdot x_{it}$$

### Mục Tiêu 2: Cực Tiểu Hóa Chi Phí Chuyển Đổi Ngữ Cảnh (Minimize Context Switch Cost — $f_2$)
Kế thừa triết lý từ Tian et al. (C&IE 2022) về chi phí chuyển đổi kỹ năng (Skill Switches) và Golfarelli et al. (2013) về Task Affinity. Mỗi khi một team hoàn thành task $i$ và chuyển sang thực hiện task $j$ kế tiếp trong chuỗi công việc, họ chịu chi phí chuyển đổi $C_{ij}$:
$$C_{ij} = w_{\text{repo}} \cdot \mathbb{I}(\text{repo}_i \neq \text{repo}_j) + w_{\text{mod}} \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + w_{\text{skill}} \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j)$$
- Phân cấp chi phí: $w_{\text{repo}} = 0.5 > w_{\text{mod}} = 0.3 > w_{\text{skill}} = 0.2$.
- $C_{ij} = 0$ khi và chỉ khi 2 task kế tiếp cùng Repo, cùng Module và cùng nhóm Skill.

$$\min f_2 = \sum_{t \in T} \sum_{i \in \mathcal{V}^+} \sum_{j \in \mathcal{V}^+} C_{ij} \cdot z_{ijt}$$

---

## 5. Ý Nghĩa Của Việc Bỏ DAG Đối Với Bài Toán

1. **Thanh thoát và sạch sẽ về mặt toán học**: Không còn hiện tượng "nghẽn năng lực" (capacity-induced starvation), khi một cụm DAG 180 SP làm tê liệt các đội khác.
2. **Không xung đột với trục thời gian**: Tránh được câu hỏi chất vấn của các nhà khoa học: *"Team 2 chờ Team 1 ở ngày thứ mấy trong Sprint nếu không có biểu đồ Gantt?"*.
3. **Độ phức tạp vẫn là NP-hard**: Bài toán thuộc lớp **Skill-Constrained Multiple Knapsack Problem kết hợp với Open Multiple Traveling Salesperson Problem (MS-MKP-mTSP)**, vượt trội hoàn toàn so với mô hình Knapsack 0-1 đơn giản của VULCON.
