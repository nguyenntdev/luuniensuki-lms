# V4.2 — Novelty-first, Win-by-Evidence
**Ngày:** 2026-11-16 · **Repository evidence:** `nguyenntdev/luuniensuki-lms@331c581f540ba4a6d41618b49222a0f56fdf0042` · **State:** DESIGN ONLY.

V4.1 đề xuất nhiều thuật toán trước khi chứng minh khoảng trống. V4.2 chặn chuyện đó bằng 2 contracts độc lập: `NOVELTY_GATE` và `WIN_CONTRACT`.

**Không ai có thể bảo đảm một mô hình học máy chưa chạy chắc chắn thắng baseline trên bộ test độc lập.** Điều có thể bảo đảm là: (i) thuật toán thỏa những invariants được đặc tả và chứng minh; (ii) mọi tuyên bố thắng chỉ được phát hành khi qua kiểm định thực nghiệm công bằng, đủ mạnh, trên bộ dữ liệu độc lập. Nếu không, ghi `NOT_WON`, pivot/merge/drop. Đây không phải thất bại của công việc; đó là thực nghiệm nghiêm túc.

**V3 facts:** Runner Research V3 từng in `641 passed / 9 failed / 9 errors / 16 skipped` nhưng workflow vẫn xanh (do pipeline không fail). Trong clean CI, progress là `211 DONE / 107 BLOCKED`, trong commit `progress.json` là `218/100`. Dữ liệu, license, chuyên gia vẫn là các gates. Trước khi tìm improvement, sửa phần kiểm thử và tái tạo baseline V3.

**Nguồn:** xem `08_REFERENCES/VERIFIED_CLOSEST_WORK.md`. Tất cả so sánh novelty tại thời điểm này là **screening only**, không được tự động đánh dấu `NOVEL` hay `SOTA`.

## Luồng thực thi bắt buộc
`G0_FIX_CI -> G1_REPRODUCE_V3 -> G2_FULL_RELATED_WORK_AND_CODE -> G3_STRONG_BASELINE_CHAMPION -> G4_RESIDUAL_ERROR_AND_NONTRIVIALITY -> G5_NOVELTY_REVIEW -> G6_METHOD_MATHEMATICAL_SPEC -> G7_DEV_BUDGET -> G8_FREEZE_PREREG -> G9_ONE_SHOT_SEALED_TEST -> G10_INDEPENDENT_REPLICATION -> G11_HUMAN_SIGNOFF -> G12_CLAIM_RELEASE`.

## Cấu trúc
- `01_NOVELTY/` 14 bài novelty screening, nearest-work/PICO/exclusion/merge decisions
- `02_WIN_CONTRACT/` định nghĩa thế nào là thắng, và cái gì chứng minh được
- `03_PAPERS/` 14 detailed research-method specs
- `04_BASELINES/` danh sách đối thủ bắt buộc và dataset parity
- `05_EXECUTION/` gating architecture, CI repair, reproducibility, timelines
- `06_AGENT/GOAL.md` goal để 10 agents phối hợp
- `07_TICKETS/` 14×18 + 22 = 274 ticket, DAG & acceptance criteria
- `08_REFERENCES/` bài báo và tài liệu ban đầu có URL, chưa phải systematic review đầy đủ

**Không được** đánh dấu DONE cho human signoff, licence chưa duyệt, baseline chưa chạy hoặc CLAIM khi chưa kiểm định. Không được học lại bằng cách nhìn test set rồi đổi metric/hypothesis.
