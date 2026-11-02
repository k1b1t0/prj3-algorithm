## 1. Pipeline Năm Giai Đoạn

- **Giai đoạn 1 (Tiền xử lý)**: Lọc trước các task bất khả thi ($k_{t, \text{skill}} < 0.5$) để giảm số biến.
- **Giai đoạn 2 (Biến quyết định)**: Khởi tạo biến nhị phân phân bổ $x_{it}$, biến hành trình $z_{u,v,t}$ và biến vị trí MTZ $pos_{it}$.
- **Giai đoạn 3 (Thiết lập ràng buộc)**: Gán đơn nhất, trần dung lượng Sprint, bảo toàn luồng và triệt tiêu chu trình MTZ.
- **Giai đoạn 4 (Nguyên hóa hàm mục tiêu)**: Nhân phóng đại `SCALE = 100,000` đưa hàm mục tiêu vô hướng hóa $Z(w)$ về số nguyên.
- **Giai đoạn 5 (Giải & Đánh giá độc lập)**: Chạy 8 luồng CPU, trích xuất chuỗi và chấm điểm lại bằng hàm số thực `evaluate_sprint_plan`.


