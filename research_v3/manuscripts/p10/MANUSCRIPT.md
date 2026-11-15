# P10 — Thiết kế tiến trình học liệu số xoắn ốc liên thông lớp 10–12 trong giáo dục di sản địa phương

**Manuscript skeleton (P10-T17). Status: DRAFT_SKELETON — PEDAGOGICAL_VALIDATION_REQUIRED.**
Venue orientation: Tạp chí Giáo dục (HĐGSNN). Every numeric claim below is bound to an
evidence ID in the frozen run artifact (`research_artifacts_v3/runs/p10/p10_run_*.json`,
`payload_sha256`-pinned). No number may be pasted from anywhere else (P10-T15).

---

## Abstract (skeleton; numbers auto-inserted from run manifest by render step)

- **Context:** Lớp học liệu di sản Cửu Đỉnh (9 đỉnh, 162 họa tiết, đúc 1835–1837) chưa được
  xếp thành tiến trình xoắn ốc liên thông lớp 10–12 theo CTGDPT 2018.
- **Objective:** Thiết kế và kiểm chứng máy (design-gate) một chuỗi xoắn ốc 3 lớp
  (Nhận diện → Đối chiếu → Đánh giá) với 4 bất biến: phi chu kỳ DAG, đơn điệu khối lớp,
  leo thang Bloom, neo chương trình có truy nguyên.
- **Evidence IDs:** [EVID-P10-M1], [EVID-P10-M2], [EVID-P10-M3], [EVID-P10-M4].

## 1. Introduction

- RQ (đóng băng theo prereg): "Tính liên tục, tăng độ sâu nhận thức và phù hợp CTGDPT của
  chuỗi học liệu di sản số theo 3 lớp được chuyên gia đánh giá như thế nào?"
- Đóng góp: (i) kiến trúc xoắn ốc 3 lớp trên corpus có thật; (ii) registry neo chương trình
  **phân tách trung thực** documented / needs_expert_review; (iii) bộ gate máy kiểm được
  trước khi mời chuyên gia.
- **Collision boundaries:** P02 (tối ưu thuật toán) — P10 là thiết kế sư phạm; P11 (rubric
  chấm) — P10 không phát minh rubric; P12 (xác thực sử liệu) — P10 không tuyên bố chân lý
  lịch sử của họa tiết.

## 2. Related work

- **Bruner spiral** — Bruner (1960), *The Process of Education*: cấu trúc cùng một được
  ghé lại nhiều lần với độ phức tạp tăng dần. P10 hiện thực hóa bằng 3 lớp Bloom băng cố định.
- **Constructive alignment** — Biggs (1996): mục tiêu–hoạt động–đánh giá phải thẳng hàng;
  P10 mã hóa bằng anchor → layer → bloom band (P10-LOCAL, chờ chuyên gia).
- **GDPT 2018** — Thông tư 32/2018/TT-BGDĐT; Chuyên đề 10.2 "Bảo tồn và phát huy giá trị
  di sản văn hóa" (Lịch sử 10) là neo documented chính [EVID-P10-ANCHOR-REG].
- **Predecessor:** LN-01 (V2) gates xoắn ốc tổng quát; khác biệt được ghi ở
  `research_v3/methods/p10/METHOD.md` §5 (P10 thêm lớp/cầu/registry truy nguyên).
- Nearest-work matrix: **chưa ký** — P10-T20 human-only, BLOCKED.

## 3. Method

- Xem `research_v3/methods/p10/METHOD.md` (đóng băng trước khi viết engine).
- 4 bất biến + thứ tự fail-closed; C0/C1/proposed; A1–A4; độ phức tạp O(V+E), CPU.
- **Tách bộ thiết kế / bộ đánh giá:** gate máy (bộ thiết kế, repo này) ≠ hội đồng giáo viên
  (bộ đánh giá, BLOCKED); hội đồng chấm mù tên phương pháp (packet §2).

## 4. Results (design-gate only; human phase pending)

Bảng chính — mọi ô tính từ run manifest, không nhập tay:

| Metric | Value | Evidence ID |
|---|---|---|
| M1 sequence_validity_rate (C0/C1/proposed) | auto | [EVID-P10-M1] |
| M2 anchor coverage (documented objects / 162) | auto | [EVID-P10-M2] |
| M3 needs_expert_review rate (objects / 162) | auto | [EVID-P10-M3] |
| M4 bloom-leap flag rate (edges / 71) | auto | [EVID-P10-M4] |
| Anchor registry: documented vs pending | 3 vs 27 | [EVID-P10-ANCHOR-REG] |

Kết quả đắc lực từ ablation: A3 chứng minh khi **bỏ** gate neo, mã năng lực bịa
(`NH10-FABRICATED-COMPETENCY`) lọt vào chuỗi [EVID-P10-A3] — cơ chế mà proposed chặn.

## 5. Threats to Validity

- **Curriculum mapping not expert-validated (main threat):** 27/30 neo và 71/162 đối tượng
  đang ở trạng thái `needs_expert_review`; kết quả M1–M4 chỉ là **gate kỹ thuật**, không
  phải chứng cứ sư phạm. Không CVI, không rubric, không inter-rater trong bản chạy máy.
- **Construct:** Bloom band hóa theo lớp là quyết định thiết kế prereg, không phải chuẩn
  bộ GDPT; cần đối chiếu yêu cầu đạt của CTGDPT từng lớp.
- **External validity:** một bộ di sản (Cửu Đỉnh); tổng quát hóa ngoài Huế chưa kiểm chứng
  (single-collection limitation, công bố thẳng).
- **Data provenance:** 162/162 mô tả motif là AI-generated trong repo; tiến trình tham chiếu
  danh tính đối tượng, không tuyên bố độ chính xác sử liệu (việc của P12).
- **Rights:** không có quyền lưu trữ Huế; dataset card `hue-heritage-corpus` giữ BLOCKED.

## 6. Failure review (P10-T16)

- C0 thất bại gate đơn điệu khối lớp (playlist xuyên biên giới lớp) — **báo cáo, không bịa
  thành đạt**; đây là negative control có chủ đích.
- A4 random: 51 nghịch đảo khối lớp ở seed 42 — failure family như prereg.
- Không có run nào bị xóa; certificate reason_codes đầy đủ trong run JSON.

## 7. Ethics & compliance

- Không dữ liệu người học; không tuyển người; không liên hệ trường.
- Phase chuyên gia (P10-T19) phải có duyệt đạo đức + form đồng ý trước khi thu rating;
  hiện **BLOCKED**, không mô phỏng chữ ký.

## 8. Reproduction (P10-T18)

```bash
# from a clean clone at the recorded commit
pytest tests/research_v3/method/test_p10_invariants.py \
       tests/research_v3/method/test_p10_builders.py \
       tests/research_v3/method/test_p10_ablations.py \
       tests/research_v3/method/test_p10_provenance.py \
       tests/research_v3/method/test_p10_experiment.py
python -m research_v3.methods.p10.cli run      # freezes research_artifacts_v3/runs/p10/p10_run_*.json
python -m research_v3.methods.p10.cli verify   # byte-identical determinism check
```

## Appendix A — Anchor registry dump

Rendered from `build_anchor_registry()` at build time; every row carries
`anchor_code, grade, competency_ref, source_citation, confidence_status`. 27 dòng
needs_expert_review được in nguyên trạng — không ẩn, không gộp vào documented.
