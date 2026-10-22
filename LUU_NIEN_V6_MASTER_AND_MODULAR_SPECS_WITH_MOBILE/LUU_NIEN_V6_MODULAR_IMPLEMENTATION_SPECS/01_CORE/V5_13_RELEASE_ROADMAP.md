# V5.13 — RELEASE_ROADMAP

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.13`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.13 — DỰ TOÁN TRIỂN KHAI VÀ QUY TẮC ƯU TIÊN

Không có đủ dữ liệu team velocity để cam kết ngày hoàn tất. Dùng **relative effort** thay vì thời hạn cố định: XS = <0.5 day, S = 1–2 days, M = 3–5 days, L = 1–2 weeks, XL = >2 weeks cho **một kỹ sư có hiểu biết repo**; chỉ là planning heuristic, nhiều ticket phụ thuộc giáo viên/curator/đối tác không nằm trong năng lực engineer. `T-Shirt` cần cập nhật sau spike + estimation thực.

### 13.1. Critical path

`Truth baseline W00` → `Inquiry+tenant W01` + `Source editorial W02` → `LMS server W03` + `Media W04` → `Mobile W05` + `AI tutor W06` → `Research factory W07` → `Security+SRE W08` → `School B2B W09` & `Market features W10` → `Business measurement W11` → `Release W12`.

Parallel lanes allowed **only** if file ownership is isolated, migration sequenced and data assumptions stable. E.g. education rubric UI can progress while source licensing reviewed, but cannot publish unsupported lessons. Marketplace demo can be built in sandbox but cannot count a fake success.

### 13.2. Three coherent release trains

- **R1 Source-True Foundation:** production truth + verified subset of Cửu Đỉnh + real accounts/roles + production 2D + basic source lookup + no fake operation.
- **R2 Classroom & Cultural Pilot:** teacher real assignments, grades, 3D/AR accessible, partner inquiry reliable, admin content review, privacy.
- **R3 Startup Product:** Passport, museum QR, partner calendar, analytics cohorts, paid pilot/contracts if ready, AI advanced with evaluation.

A feature is not `DONE` because its UI route renders. Require backend state, durability, failures, observability, privacy, accessibility, infra and user signoff.

