# V5.2 — CODEBASE_BASELINE

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.2`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.2 — CODEBASE BASELINE VÀ GIỚI HẠN AUDIT

**Những điểm đã quan sát trong ZIP:** `backend/` FastAPI active; `backend-rust/` gateway Axum; `frontend/` Next.js; `mobile/` Flutter; `migrations/` Alembic; `data/` chín file dữ liệu cho Cửu Đỉnh; `public/models/`; `docs/rbpc/` bộ startup/consent/business plan; CI `ci.yml` và `deploy.yml`.

**Kiểm tra đã thực hiện trong phiên audit V5:** `python -m compileall -q backend` PASS trong môi trường hiện tại; parse 9 file JSON `*Data*Dinh.json` PASS; tổng 162 bản ghi, 162 `is_ai_generated=true`, 162 bản ghi không có field citation/source trực tiếp theo tập field kiểm tra, 162 `3d_mesh_id`. Đây **không** chứng minh 162 model 3D tương ứng tồn tại hoặc nội dung đã được kiểm duyệt. `frontend/node_modules` không có trong snapshot và `.git` không có; chưa thể tự xác minh frontend build, full migration, Rust tests hoặc production traffic. Nhiều tài liệu `docs/rbpc/` tự ghi `PASS`, số liệu thương mại và cấu hình hạ tầng; phải xác minh bằng log và giấy tờ độc lập, không được nhầm một tuyên bố trong hồ sơ pitch thành production evidence.

### 2.1. Hệ thống API hiện có phải tái sử dụng

- `backend/routers/rbpc.py`: endpoint stories/creators/experiences/inquiries/inquiry status/partner inbox/status; **không xây lại một backend marketplace song song** khi endpoint cũ có thể harden.
- `backend/models_rbpc.py`: các model thị trường nghệ nhân; mở rộng bằng migration, không tạo shadow tables.
- `backend/history_models.py`, `backend/routers/history_learning.py`, `backend/routers/history_tutor.py`, `backend/services/history_tutor.py`: lớp nguồn–claim–learning cần mở rộng.
- `backend/services/heritage_import.py`: pipeline seed/import hiện có; phải thay `verified` mặc định bằng validation+editorial evidence gate.
- `frontend/src/lib/rbpc/inquiries.ts`, `frontend/src/app/rbpc/partner/page.tsx`: client API cho inquiry/partner.
- `frontend/src/lib/imperial/map-api.ts`: map/annotation mutation cần strict result.
- `frontend/src/lib/imperial/submissions-api.ts`: fake student submissions cần thay bằng lớp API và quyền giáo viên.
- `mobile/lib/routing/app_router.dart`: một số route quests vẫn trỏ placeholder; kiểm tra referenced routes để phân biệt placeholder dead code và route đang dùng.
- `backend-rust/config/route-modes.toml`: thay đổi route phải đồng bộ chính sách native/gateway và tests, không mặc định Rust có handler mới.

### 2.2. Nguyên tắc kiểm toán

`docs/rbpc/*` là bằng chứng **ý định/thiết kế/claim trong dossier**, không thay test. `AGENTS.md` ghi rõ file root-level monolith đã obsolete. Không sửa `main.py`, `models.py`, `schemas.py`, root `versions/`. Có công cụ GitNexus thì chạy impact/detect changes; không có thì ghi `INDEX_UNAVAILABLE` và làm call-graph thủ công. Không xử lý trực tiếp thông tin học sinh trong LLM prompt/log hoặc commit.

