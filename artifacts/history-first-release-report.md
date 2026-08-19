# Báo Cáo Phát Hành — History-First Release Report

**Ngày cập nhật:** `2026-08-19 11:20:00 UTC`  
**Trạng thái phát hành:** `SẴN SÀNG KHỞI CHẠY (RELEASE READY)`  

---

## 1. Tổng Quan Kiến Trúc & Route Đã Triển Khai (Shipped Routes)

Đã hoàn tất chuyển đổi kiến trúc Lịch sử (History-First Domain), đồng bộ hệ thống định tuyến giữa Next.js Frontend, Rust Gateway & FastAPI Backend.

### Các tuyến đường đã hoạt động (100% Dynamic Sitemap & Metadata):
- `/ (Trang chủ / Discovery)`
- `/cuu-dinh (Tổng quan Cửu Đỉnh)`
- `/cuu-dinh/[urnSlug] (9 Đỉnh chi tiết)`
- `/atlas (Atlas 162 họa tiết & phù điêu)`
- `/atlas/[urnSlug]/[reliefSlug] (153 tuyến Phù điêu chi tiết)`
- `/map (Bản đồ di sản & fallback dạng bảng WCAG)`
- `/timeline (Dòng thời gian lịch sử)`
- `/stories (Câu chuyện di sản dạng khối - Block-based History Stories)`
- `/collections (Tuyển tập tuyển chọn - Curated Historical Collections)`
- `/sources (Thư viện nguồn & bằng chứng)`
- `/api/v1/history/* (Hệ thống REST API Lịch sử & Strangler-Fig Rust Gateway)`

- **Tổng số Route Sitemap:** `170` routes (`/`, `/cuu-dinh`, 9 đỉnh, `/atlas`, 153 phù điêu, `/map`, `/timeline`, `/stories`, `/collections`, `/sources`).

---

## 2. Kiểm Trực Dữ Liệu & Toàn Vẹn Nội Dung (Content Validation)

- **Alembic Migrations:** `66` bản cập nhật schema đã được áp dụng.
- **Lỗi vi phạm toàn vẹn (Errors):** `0`
- **Cảnh báo rà soát (Warnings):** `0`
- **Kết quả Kiểm tra Dữ liệu:** `ĐẠT (PASS)`

### Thống kê Kiểm chứng (Verification Counts):
- **Phù điêu đã định danh & chuẩn hóa chữ Hán:** `153/153 (100%)` phù điêu thuộc 9 Đỉnh có đầy đủ chữ Hán-Nôm chuẩn xác.
- **Đỉnh đồng đã kiểm chứng:** `9/9 (100%)` đỉnh có đầy đủ miếu hiệu, kích thước, khối lượng và liên kết án thờ.
- **Thực thể lịch sử & Địa danh:** `250+` thực thể có tọa độ và độ chính xác WGS84 (`exact`, `approximate`, `region`).
- **Nguồn thư tịch chính thống:** `5` bộ chính sử (Đại Nam Thực Lục, Khâm Định Đại Nam Hội Điển Sự Lệ, Đại Nam Nhất Thống Chí, UNESCO MOWCAP Cửu Đỉnh Dossier, Đồng Khánh Địa Dư Chí).
- **Câu chuyện & Tuyển tập tuyển chọn:** Đã biên soạn và xuất bản các câu chuyện lịch sử khối và bộ sưu tập chuyên đề.

---

## 3. Khả Năng Truy Cập (Accessibility - WCAG 2.2 AA) & SEO

1. **Fallback Văn bản cho 3D Viewer (`UrnAccessibleFallback.tsx`):**
   - Đã tích hợp chế độ đọc văn bản thay thế cho Trình xem 3D Cửu Đỉnh.
   - Hiển thị đầy đủ thông số kích thước, triều đại, biểu tượng và bảng 17 phù điêu dạng văn bản có thể truy cập bằng screen-reader.
2. **Fallback Dạng Bảng cho Bản Đồ (`/map?view=list`):**
   - Hỗ trợ chế độ hiển thị bảng semantic HTML (`<table role="table">`, `<caption>`, `<thead>`, `<tbody>`, `scope="col/row"`).
   - Tối ưu cho người dùng không sử dụng được bản đồ tương tác Leaflet/Canvas.
3. **Nhãn Kiểm Chứng Không Dùng Màu Đơn Thuần (`EpistemicLabel.tsx`):**
   - Toàn bộ nhãn mức độ tin cậy được trang bị biểu tượng riêng biệt (`ShieldCheck`, `BookOpen`, `ScrollText`, `HelpCircle`, `AlertTriangle`, `Clock`) đi kèm văn bản trạng thái.
4. **Metadata & Structured Data (JSON-LD):**
   - Đã nhúng `schema.org/VisualArtwork` & `schema.org/HistoricalObject` trên toàn bộ 153 trang chi tiết phù điêu.
   - Cấu hình thẻ OpenGraph, Twitter Card & Canonical URL chính xác.

---

## 4. Báo Cáo Kiểm Thử & Kiểm Soát Chất Lượng (Test Results)

- **Rust Gateway (`cargo test`):** `PASSED` (Tất cả contract tests & health check parity đạt 100%).
- **Python Backend History Tests (`pytest tests/backend/test_history*.py`):** `76/76 PASSED (100%)`.
- **Legacy Migration Invariant Tests (`test_history_migration.py`):** `8/8 PASSED (100%)`.
- **Frontend Type-check (`tsc --noEmit`):** `PASSED` (Không có lỗi TypeScript).
- **Frontend Lint (`npm run lint:ci`):** `PASSED` (0 warnings/errors).

---

## 5. Kết Luận Release Readiness

Hệ thống **History-First LMS (Lưu Niên Sử Kí - Cửu Đỉnh)** đã đáp ứng đầy đủ các tiêu chuẩn về Dữ liệu Lịch sử, Khả năng truy cập (WCAG 2.2 AA), Chuẩn SEO Metadata, Tốc độ truyền tải và Tính toàn vẹn của mô hình phân tầng. Cho phép tiến hành phát hành bản thương mại/chính thức.
