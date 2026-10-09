# prj3-algorithm: Thuật Toán Điều Độ Lỗ Hổng Bảo Mật (1 Sprint)

---

## 1. Kết Quả Thực Nghiệm Đối Chứng (Benchmark Summary)

Chạy thực nghiệm so sánh phương pháp đề xuất (**Proposed: ESSC+DP**) với 2 giải thuật đối chứng (**Greedy-CVSS** và **Knapsack-Topo**) trên 3 bộ kịch bản:

| Kịch bản | Quy mô | Chỉ số | Proposed (ESSC+DP) | Baseline 1 (Greedy-CVSS) | Baseline 2 (Knapsack-Topo) | Nhận xét cải tiến |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **demo-1** | $N=20$<br>$\|T\|=2$ | **Switch Cost** ($F_{\text{Switch}}$)<br>Risk Resolved ($F_{\text{Risk}}$)<br>Skill Match (SMS)<br>DAG Violations | **0.80**<br>88.0<br>0.697<br>**0** | 5.00<br>**91.0**<br>0.731<br>**0** | 3.00<br>88.0<br>0.713<br>**0** | **Giảm 73.3%** chi phí chuyển ngữ cảnh so với baseline tốt nhất. |
| **demo-2** | $N=40$<br>$\|T\|=3$ | **Switch Cost** ($F_{\text{Switch}}$)<br>Risk Resolved ($F_{\text{Risk}}$)<br>Skill Match (SMS)<br>DAG Violations | **1.20**<br>139.5<br>0.666<br>**0** | 5.20<br>127.5<br>0.707<br>**0** | 5.60<br>**145.5**<br>0.663<br>**0** | **Giảm 76.9%** chi phí chuyển ngữ cảnh; giữ vững 0 vi phạm DAG khi cắt tỉa quá tải. |
| **demo-3** | $N=60$<br>$\|T\|=4$ | **Switch Cost** ($F_{\text{Switch}}$)<br>Risk Resolved ($F_{\text{Risk}}$)<br>Skill Match (SMS)<br>DAG Violations | **3.20**<br>**226.5**<br>0.731<br>**0** | 8.00<br>191.0<br>0.752<br>**0** | 12.20<br>198.0<br>0.691<br>**0** | **Giảm 60.0% - 73.8%** chi phí chuyển ngữ cảnh; **xử lý được nhiều rủi ro hơn** cả 2 baseline. |

---

## 2. Hướng Dẫn Vận Hành

### Sử dụng CLI chính (`main.py`):
```bash
# Cài đặt môi trường
uv sync

# Chạy thuật toán đề xuất (lưu kết quả vào outputs/proposed_results.json)
uv run main.py proposed

# Chạy benchmark so sánh đối chứng (lưu vào outputs/benchmark_summary.json)
uv run main.py benchmark

# Sinh báo cáo trực quan Dashboard HTML
uv run main.py visualizer

# Chạy trọn gói (Benchmark + Visualizer)
uv run main.py all
```

### Hoặc chạy trực tiếp từng script riêng biệt trong `scripts/`:
```bash
uv run scripts/run_proposed.py
uv run scripts/run_benchmark.py
uv run scripts/generate_visualizer.py
uv run python -m unittest discover tests
```

---

## 3. Kiến Trúc 4 Giai Đoạn (Proposed Pipeline)

```text
               [Backlog Tasks (demo-X.json)]
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Giai đoạn 1: Gom Cụm Ngữ Cảnh (Spectral Clustering)     │
  │ - Ma trận khoảng cách C_ij (Module: 0.6, Skill: 0.4).   │
  │ - DAG Affinity Boost: kéo gần các cặp phụ thuộc u -> v. │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Giai đoạn 2: Phân Công Đội Nhóm (Hungarian Matching)    │
  │ - Tối đa hóa độ tương thích kỹ năng k_{t, skill}        │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Giai đoạn 3: Làm Gọn Dung Lượng (PCKP Leaf Pruning)     │
  │ - Lọc kỹ năng yếu (< 0.5) và tỉa các con mồ côi.        │
  │ - Tỉa dần các task lá có r_i / e_i thấp nhất            │
  │   đảm bảo 100% không làm đứt gãy DAG.                   │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Giai đoạn 4: Lập Lịch Thứ Tự Nội Bộ (Intra-Team DP)     │
  │ - Topological Bitmask DP tìm hoán vị tối thiểu          │
  │   tổng Context Switch Cost trong O(2^L * L) (< 0.02s).   │
  └──────────────────────────┬──────────────────────────────┘
```

---

## 4. Các Thuật Toán Đối Chứng (Baselines)

- **Baseline 1 (`Greedy-CVSS`)**: Đại diện cho thực tiễn phổ biến trong doanh nghiệp — ưu tiên gán các task có rủi ro $r_i$ cao nhất cho đội nhóm phù hợp còn trống dung lượng. Giữ nguyên thứ tự gán làm chuỗi thực hiện, dẫn đến chi phí chuyển đổi ngữ cảnh ($F_{\text{Switch}}$) rất cao do nhảy module liên tục.
- **Baseline 2 (`Knapsack-Topo`)**: Tối đa hóa rủi ro bằng Knapsack tham lam theo tỷ số $\frac{r_i}{e_i}$. Sắp xếp thứ tự thực thi bằng thuật toán Kahn Topological Sort cơ bản, hoàn toàn không tối ưu hóa hàm chi phí chuyển đổi ngữ cảnh $C_{ij}$.

