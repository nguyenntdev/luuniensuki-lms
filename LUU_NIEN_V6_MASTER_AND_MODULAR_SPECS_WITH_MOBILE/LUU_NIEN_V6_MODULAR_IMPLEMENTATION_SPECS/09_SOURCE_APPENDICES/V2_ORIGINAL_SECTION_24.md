# V2 original archival technical chapter — SECTION_24

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 24. THAM CHIẾU NỘI BỘ CHO ĐỘI TRIỂN KHAI

- Core: `README.md`, `docs/ARCHITECTURE.md`, `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`, `docs/specs/HISTORY_FIRST_EXECUTION.md`, `docs/CURRENT_SYSTEM_STATE.md`.
- RBPC: `docs/rbpc/BASELINE.md`, `API_CONTRACTS.md`, `DATABASE_CONTRACTS.md`, `AI_EVAL.md`, `CONTENT_RIGHTS.md`, `HERITAGE_FACT_CHECK_LEDGER.md`, `CREATOR_CONSENT_AUDIT.md`, `RELEASE_CHECKLIST.md`, `FINAL_HANDOFF_REPORT.md`.
- Code: `frontend/src/app`, `frontend/src/components`, `frontend/src/lib/rbpc`, `backend/main.py`, `backend/routers`, `backend/services`, `backend/models_rbpc.py`, `backend/history_models.py`, `backend-rust/src`, `mobile/lib`, `migrations/versions`, `data`, `ban-duc-noi`, `.github/workflows`.
- Research: Q2 English/Vietnamese paper (6-step framework, 1.502 aggregate) + extended 17-page design manuscript (ELLO, audit anomalies, experimental protocol) + HCMUS 2026 submitted abstract. Những bản nghiên cứu này là **claim register**, không thay thế kiểm chứng sản phẩm và dữ liệu.
- ZIP snapshot SHA-256 nêu ở đầu tài liệu; mọi issue paths dưới đây là relative từ thư mục repo gốc trong ZIP.

**END — PHẦN CHÍNH.** Phụ lục tự động kiểm kê các file, route và checkpoint tĩnh được nối ở cuối tài liệu để đội dev có thể định vị mã cụ thể.


---

# PHỤ LỤC A — INVENTORY CÓ THỂ KIỂM TRA TỪ SOURCE SNAPSHOT

**Phương pháp:** trích từ tệp hiện diện; không phải kết quả query production. Các thống kê và tên tệp bên dưới dành để map công việc kiểm chứng; không đồng nghĩa dữ liệu đúng về mặt lịch sử.

- `backend`: **339 files**; extensions: `.jpg` 162, `.py` 140, `.mp3` 16, `.pyc` 12, `.glb` 4, `.txt` 2.
- `backend-rust/src`: **100 files**; extensions: `.rs` 100.
- `frontend/src`: **405 files**; extensions: `.tsx` 233, `.ts` 102, `.jsx` 55, `.json` 6, `.md` 4, `.js` 3.
- `mobile/lib`: **228 files**; extensions: `.dart` 228.
- `tests`: **58 files**; extensions: `.py` 56, `.json` 1, `.pyc` 1.
- `migrations/versions`: **71 files**; extensions: `.py` 71.
- `data`: **42 files**; extensions: `.json` 36, `.yaml` 6.
- `ban-duc-noi`: **164 files**; extensions: `.jpg` 162, `.png` 2.
- `docs/rbpc`: **40 files**; extensions: `.md` 40.

