# Mô Tả Bài Toán Bằng Lời (Problem Definition) — Project 3

> **Tên đề tài**: Tối ưu hóa điều độ và phân bổ công việc vá lỗ hổng an ninh mạng đa mục tiêu trong chu kỳ Sprint Agile (Bi-Objective Agile SecOps Scheduling).  
> **Mục đích tài liệu**: Trình bày toàn bộ bối cảnh nghiệp vụ, các khái niệm, quy tắc vận hành và tư duy thiết kế bài toán dưới dạng ngôn ngữ tự nhiên (không lồng ghép các công thức ma trận trừu tượng).

---

## 1. Bối Cảnh Thực Tế & Động Lực Nghiên Cứu

Trong các tổ chức phát triển phần mềm hiện đại vận hành theo mô hình **Agile / DevSecOps**, các công cụ quét mã nguồn tự động (SAST/DAST/SCA như Snyk, SonarQube, GitHub Dependabot) liên tục phát hiện ra hàng chục đến hàng trăm lỗ hổng bảo mật (CVE/CWE) mỗi tuần. Toàn bộ các cảnh báo này được đổ dồn vào **Product Backlog**.

Tuy nhiên, đội ngũ kỹ thuật luôn phải đối mặt với **sự khan hiếm về nguồn lực**:
1. **Dung lượng Sprint có hạn**: Mỗi Sprint thường kéo dài cố định 2 tuần (time-boxed). Mỗi đội phát triển (Team) chỉ có một mức dung lượng tối đa (Capacity) tính bằng Story Points (SP). Họ không thể làm hết toàn bộ tồn đọng trong một sprint mà bắt buộc phải **chọn lọc**.
2. **Chi phí chuyển đổi ngữ cảnh (Context Switching Overhead)**: Khi một lập trình viên đang sửa lỗi ở repository/module này mà phải chuyển sang một repository hoàn toàn khác, hoặc phải chuyển từ dạng lỗi logic phân quyền sang lỗi mã hóa, họ mất rất nhiều thời gian "làm nóng" (context switching: clone repo, đọc lại kiến trúc module, cài đặt môi trường, chạy test nội bộ). Nếu lịch làm việc chắp vá, nhảy cóc liên tục thì năng suất sẽ giảm sút nghiêm trọng.
3. **Mối quan hệ phụ thuộc kỹ thuật (Precedence Dependencies)**: Có những lỗ hổng không thể sửa độc lập. Ví dụ: Lỗi ở module lõi (Core/Authentication) phải được khắc phục và đóng gói trước thì các lỗi phụ thuộc ở module giao diện (API/Frontend) mới có thể sửa và kiểm thử được.
4. **Áp lực thời hạn tuân thủ (SLA / Deadline)**: Theo các tiêu chuẩn an ninh như NIST hay PCI DSS, các lỗ hổng có thời hạn khắc phục nghiêm ngặt (ví dụ: lỗi Critical phải sửa trong vòng 30 ngày). Những lỗi bị hoãn (defer) qua nhiều sprint sẽ tích lũy phơi nhiễm rủi ro và cần được tự động tăng mức độ ưu tiên.

---

## 2. Các Thực Thể & Thuộc Tính Cốt Lõi

Bài toán xem xét trong phạm vi **1 chu kỳ Sprint duy nhất** (ví dụ: Sprint hiện tại $\tau$).

### 2.1. Backlog Lỗ Hổng An Ninh (Vulnerability Tasks)
Tập hợp gồm $N$ công việc vá lỗ hổng đang tồn đọng trong Backlog. Mỗi công việc $v_i$ mang các thông tin thực tế:
- **`id`**: Định danh duy nhất của task trong hệ thống quản lý (Jira/GitHub Issues).
- **`cwe`**: Mã phân loại lỗ hổng an ninh (ví dụ: CWE-89 cho SQL Injection, CWE-79 cho XSS). Đóng vai trò là thông tin nghiệp vụ/metadata.
- **`repo`**: Tên kho chứa mã nguồn (Code Repository) chứa file bị lỗi.
- **`asset-module`**: Thư mục gốc hoặc phân hệ/microservice cụ thể bên trong repo (ví dụ: `services/auth`, `core/network`).
- **`r_i` (Base Risk)**: Điểm rủi ro kỹ thuật gốc của lỗ hổng, chuẩn hóa theo điểm CVSS v3/v4 cơ bản (thang điểm $[0, 10]$).
- **`e_i` (Effort)**: Ước lượng độ phức tạp và công sức cần thiết để sửa chữa, đo bằng Story Points (SP, số nguyên dương).
- **`skill`**: Nhóm kỹ năng chuyên môn cần thiết để sửa lỗi, ánh xạ theo 10 danh mục bảo mật chuẩn OWASP Top 10 (ví dụ: Injection, Broken Access Control, Cryptographic Failures...).
- **`sprint_discovered`**: Sprint mà lỗ hổng bắt đầu được phát hiện và ghi nhận vào Backlog.
- **`sprint_deadline`**: Sprint hạn chót bắt buộc phải hoàn thành việc vá lỗi theo chính sách SLA của tổ chức.
- **`predecessors`**: Danh sách các task cha mà task này phụ thuộc vào. Nếu task cha chưa hoàn thành thì task này chưa thể bắt đầu.

### 2.2. Đội Ngũ Thực Thi (Cross-Functional Teams)
Gồm $M$ đội kỹ thuật tham gia vào Sprint. Mỗi team $t$ có:
- **`team_id`**: Định danh của đội (ví dụ: Team Alpha, Team Beta).
- **`cap_t` (Capacity)**: Tổng số Story Points tối đa mà cả đội có thể cam kết thực hiện trong Sprint này.
- **Ma trận kỹ năng `skills`**: Bảng đánh giá độ thành thạo của đội trên 10 nhóm kỹ năng OWASP, mỗi kỹ năng có điểm số thực trong khoảng $[0.0, 1.0]$.

---

## 3. Triết Lý Vận Hành & Khung Thiết Kế

1. **Khung thời gian hữu hạn (Time-boxed Snapshot)**:
   Mô hình tập trung tối ưu hóa cho **1 Sprint hiện tại**. Toàn bộ công việc được chọn phải đảm bảo vừa vặn trong dung lượng của các team để hoàn thành dứt điểm trong sprint đó.
2. **Thứ tự thực hiện (Sequencing) thay vì Thời gian liên tục (Scheduling)**:
   - Trong một Sprint 2 tuần, việc phân mảnh chi tiết đến từng giờ hay đo lường makespan liên tục là không thực tế (lập trình viên làm song song, chờ code review, merge code và release chung vào cuối sprint).
   - Mô hình **chỉ quan tâm đến thứ tự chuỗi công việc của từng team**: Ví dụ Team A làm $1 \to 2 \to 5 \to 7$. Hoàn thành 1 rồi mới chuyển sang 2. Không cần quan tâm task 1 làm vào ngày thứ mấy.
3. **Chọn lọc (Knapsack Selection)**:
   Không bắt buộc phải làm hết 100% Backlog. Những công việc vượt quá dung lượng hoặc độ ưu tiên thấp sẽ được hoãn (deferred) sang các sprint tiếp theo.

---

## 4. Hệ Thống Ràng Buộc Nghiệp Vụ

### 4.1. Ràng Buộc Cứng (Bắt buộc phải thỏa mãn 100%)
1. **Gán đơn nhất (Single Assignment)**: Mỗi task trong backlog chỉ được giao cho tối đa một team xử lý, và làm tối đa một lần trong sprint.
2. **Giới hạn dung lượng Sprint (Sprint Capacity Limit)**: Tổng Story Points ($e_i$) của các task giao cho Team $t$ không được vượt quá $\text{cap}_t$.
3. **Ngưỡng năng lực tối thiểu (Skill Threshold)**: Một team chỉ được phép nhận task nếu điểm thành thạo của team đối với nhóm kỹ năng yêu cầu của task đó đạt từ $0.5$ trở lên.
4. **Ràng buộc phụ thuộc kỹ thuật (Precedence Integrity)**:
   - **Chọn con thì phải chọn bố**: Nếu task con $v$ được chọn làm trong sprint này, thì task cha $u$ bắt buộc cũng phải được chọn làm trong sprint này.
   - **Bắt buộc cùng một team (Intra-team Execution)**: Nếu cả task cha $u$ và task con $v$ cùng được chọn trong cùng sprint, **chúng bắt buộc phải được giao cho cùng một team**. Điều này loại bỏ hoàn toàn rủi ro tắc nghẽn giao tiếp chéo (cross-team blocking).
   - **Tuân thủ thứ tự topo**: Trong chuỗi công việc nội bộ của team đó, task cha $u$ bắt buộc phải được xếp làm trước task con $v$.

### 4.2. Ràng Buộc Tự Do (Tối ưu hóa thuần túy)
- **Tự do phân bổ tải (Pure Knapsack)**: Không áp đặt chặn dưới về mức độ sử dụng dung lượng của các team (không bắt buộc mỗi team phải làm tối thiểu bao nhiêu SP). Thuật toán có toàn quyền dồn việc sao cho đạt lợi ích rủi ro cao nhất và chi phí chuyển đổi thấp nhất.

---

## 5. Hai Mục Tiêu Tối Ưu Hóa (Bi-Objective Criteria)

Bài toán tìm kiếm phương án phân bổ và lập chuỗi công việc nhằm tối ưu hóa đồng thời 2 mục tiêu có tính chất đánh đổi (trade-off):

### Mục Tiêu 1: Cực Đại Hóa Lợi Ích Giảm Thiểu Rủi Ro (Maximize Mitigated Utility — MU)
Không chỉ đơn thuần cộng điểm CVSS gốc, hệ thống tính toán điểm **Lợi ích Giảm nhẹ (Mitigation Utility — $u_i$)** cho từng task để phản ánh tính động của rủi ro theo thời gian (kế thừa triết lý VULCON):
- Điểm $u_i$ bắt đầu từ điểm rủi ro gốc $r_i$ (CVSS).
- Được cộng thêm điểm thưởng tuổi thọ tích lũy (**Persistence**): task tồn tại càng nhiều sprint trong backlog mà chưa được sửa thì điểm càng tăng.
- Được cộng thêm điểm phạt khẩn cấp (**Deadline Urgency**): task càng sát hạn chót hoặc đã quá hạn SLA theo quy định thì điểm ưu tiên càng tăng vọt.
$$\max f_1 = \sum_{\text{các task được chọn trong Sprint}} u_i$$

### Mục Tiêu 2: Cực Tiểu Hóa Chi Phí Chuyển Đổi Ngữ Cảnh (Minimize Context Switch Cost)
Mỗi khi một team hoàn thành task $i$ và chuyển sang thực hiện task $j$ kế tiếp, họ chịu một chi phí chuyển đổi ngữ cảnh ($C_{ij}$). Chi phí này được **phân cấp theo 3 mức độ thực tế**:
1. **Khác Repository ($w_{\text{repo}}$)**: Phạt nặng nhất vì dev phải mở dự án mới, chuyển đổi môi trường và công cụ.
2. **Khác Module ($w_{\text{mod}}$)**: Cùng repo nhưng khác thư mục/phân hệ mã nguồn, phạt mức vừa vì phải đọc lại ngữ cảnh kiến trúc module mới.
3. **Khác Skill ($w_{\text{skill}}$)**: Khác nhóm lỗi bảo mật, phạt phụ do chuyển đổi tư duy kỹ thuật.
- *Nếu hai task kế tiếp có cùng repo, cùng module và cùng nhóm skill thì chi phí chuyển đổi bằng 0 ($C_{ij} = 0$).*
$$\min f_2 = \sum_{\text{các team}} \sum_{\text{các bước chuyển } i \to j} C_{ij}$$

---

## 6. Mối Quan Hệ Đa Mục Tiêu & Bản Đồ Nghiệm (Pareto Frontier)

Hai mục tiêu trên có sự xung đột tự nhiên:
- Muốn giải quyết được rủi ro cao nhất ($f_1$ max), các team có thể phải "chữa cháy" khắp nơi, nhảy qua nhiều repo và module khác nhau, làm chi phí chuyển đổi ($f_2$) tăng vọt.
- Ngược lại, muốn chi phí chuyển đổi thấp nhất ($f_2$ min), các team có xu hướng chỉ làm các task cùng repo/module, vô tình bỏ qua các lỗi nghiêm trọng nằm rải rác ở các module khác.

Do đó, bài toán được định nghĩa ở dạng **Đa mục tiêu thuần túy (Bi-Objective Pareto)** nhằm cung cấp một **Tập nghiệm Pareto** (hoặc nghiệm dung hòa theo trọng số $\lambda$ do Product Owner lựa chọn), giúp doanh nghiệp linh hoạt cân bằng giữa **An ninh hệ thống (Security)** và **Năng suất lập trình (Productivity)**.
