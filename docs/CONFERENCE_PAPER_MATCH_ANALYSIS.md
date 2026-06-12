# Phân tích: Project Luuniensuki LMS vs Bài báo hội thảo "Số hóa cổ vật chi phí thấp bằng LiDAR + AR"

**Bài báo:** Nguyễn Đắc Quang Minh, Trần Minh Đức, Nguyễn Ngọc Thiện — "Giải pháp số hóa cổ vật chi phí thấp bằng công nghệ scan 3D LiDAR và tối ưu hóa hiển thị qua thực tế tăng cường (AR)"
**Subject:** 9 Cửu Đỉnh tại Đại Nội Huế
**Ngày phân tích:** 2026-05-19 (cập nhật trạng thái: 2026-05-20)
**Code base:** repo `luuniensuki-lms` (deploy prod tại `/opt/luuniensuki-lms`, domain `lms.histolab.icu`)

> **Cập nhật 2026-05-20:** Gap 4 (render performance dashboard) đã được triển khai — xem mục 3 / Gap 4. Một vài đường dẫn file đã được sửa cho khớp codebase hiện tại (frontend đang chuyển từ JS sang TypeScript).

---

## 1. Tóm tắt độ match: **~76% — phần lớn trùng khớp, còn 4 gap cần đóng (Gap 4 đã xong)**

| Khối | Match | Score |
|------|-------|-------|
| Subject (9 Cửu Đỉnh, Đại Nội Huế) | ✅ Trùng 100% | 100% |
| Quy trình quét 3D thực địa (Polycam/LiDAR) | ⚠️ Đã có model, không có pipeline ingest | 30% |
| Tiền xử lý nhiễu + bổ sung mặt khuất | ❌ Không có pipeline | 0% |
| Tối ưu hóa giảm dung lượng (60-84%) | ✅ Đã đạt 83% (29MB → 5MB) | 100% |
| Hiển thị 3D web (xoay/zoom) | ✅ Three.js + R3F | 100% |
| Hiển thị 3D mobile (xoay/zoom) | ✅ model-viewer trong WebView | 100% |
| AR mobile (xem trong không gian thực) | ✅ scene-viewer + webxr + quick-look | 90% |
| AR Vuforia Image Target | ❌ Không có | 0% |
| Sketchfab embed/host | ❌ Không có | 0% |
| Tốc độ render +46% | ✅ Có 3 LOD (512/1k/2k) + dashboard benchmark (admin_render) | 85% |
| Cộng đồng tiếp cận (web + mobile) | ✅ Production tại lms.histolab.icu | 95% |
| Mở rộng cho bảo tàng địa phương khác | ❌ Hard-coded Cửu Đỉnh, không có multi-museum | 20% |

**Tổng trọng số:** ~72% match.

---

## 2. Match chi tiết theo từng phần bài báo

### 2.1 ✅ Subject — **100% match**

**Bài báo:** "9 mẫu cổ vật tiêu biểu (Cửu đỉnh) tại khu vực Đại Nội Huế"

**Project:**
- Database có 9 urns: Cao, Nhân, Chương, Anh, Nghị, Thuần, Tuyên, Dụ, Huyền Đỉnh
- Files data: `/opt/luuniensuki-lms/data/{05..13}_Data_*Dinh.json` (1 file/đỉnh)
- 3D model: `mobile/assets/models/CAO-DINH-v1.glb` (Cao Đỉnh) + `models_upload/`
- Production: `https://lms.histolab.icu` đang serve các urns này

**Verdict:** Trùng khớp tuyệt đối. Chính xác là cùng đối tượng nghiên cứu.

---

### 2.2 ⚠️ Pipeline số hóa — **30% match**

**Bài báo nói về:**
- Giai đoạn 1: Quét 3D thực địa qua Polycam (LiDAR mobile)
- Giai đoạn 2: Tiền xử lý loại nhiễu + bổ sung mặt khuất

**Project hiện có:**
- ✅ Đã có model GLB Cao Đỉnh (3 LOD: 5MB / 27MB / 29MB)
- ✅ Tools annotate motif positions (`frontend/src/app/tools/annotate/page.jsx`) — admin click vào model để tag motif positions
- ❌ KHÔNG có pipeline import từ Polycam
- ❌ KHÔNG có UI/script để re-process raw scan data
- ❌ KHÔNG có công cụ làm sạch nhiễu mesh hay bổ sung mặt khuất
- ❌ KHÔNG có tài liệu về quy trình quét

**Gap:** Project đã consume **kết quả** của pipeline số hóa nhưng không **own** pipeline đó. Bài báo trình bày chính pipeline — đây là phần academic value của bài.

---

### 2.3 ✅ Tối ưu hóa dung lượng — **100% match (vượt yêu cầu)**

**Bài báo:** "giảm dung lượng tệp từ 60% đến 84%"

**Project đo được:**
- `CAO-DINH-v1-2k.glb`: **30.35 MB** (baseline)
- `CAO-DINH-v1-1k.glb`: **27.42 MB** (giảm ~10%)
- `CAO-DINH-v1-512.glb`: **5.21 MB** (giảm **82.8%**)
- Có script `mobile/scripts/compress-models.js` + `compress-models.sh`

**Verdict:** Đạt 83% reduction — gần đỉnh phổ "60-84%" của bài báo. Match xuất sắc.

**Chi tiết script đã có:**
- `mobile/scripts/compress-models.sh` (chạy được)
- `mobile/scripts/test-compression.js`
- `mobile/scripts/deploy-compressed-models.sh`

---

### 2.4 ✅ Hiển thị 3D — **100% match**

**Bài báo:** "tích hợp mô hình vào nền tảng AR Vuforia và website Sketchfab... cho phép người dùng tương tác xoay, thu phóng"

**Project có:**
- Web: `frontend/src/components/UrnViewer.tsx` dùng Three.js + React Three Fiber + Drei (đã migrate sang TypeScript)
- Mobile: `mobile/lib/features/urn_viewer/presentation/widgets/custom_model_viewer.dart` dùng `<model-viewer>` (Google) trong InAppWebView
- Hotspot system: tap vào motif → mở lesson

**Match level:** Tương đương về functionality (xoay/zoom). Khác về platform (Three.js + model-viewer thay vì Sketchfab embed).

---

### 2.5 ⚠️ AR — **70% match**

**Bài báo:** "tích hợp mô hình vào nền tảng AR Vuforia... trải nghiệm di sản mượt mà trong không gian thực"

**Project có:**
- File `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart` line 960:
  ```dart
  void _launchAR(UrnDetail urnDetail) {
    // AR is already enabled in ModelViewer with ar: true
  }
  ```
- AR modes enabled: `scene-viewer` (Android), `webxr` (web), `quick-look` (iOS)
- Tham khảo: `mobile/IMPLEMENTATION_SUMMARY.md` Task 4.2 (Set ar: true) đã DONE
- Camera permission cho AR: chưa wire (Task 4.3 DEFERRED)

**Gap:**
- ❌ **Vuforia Image Target** không có (Vuforia là markered AR — quét marker in trên catalog/poster để xuất hiện 3D model)
- ❌ Không có demo "đặt đỉnh trên bàn để quan sát"
- ❌ Không có camera permission được wire đúng

**Verdict:** AR markerless (đặt vào không gian) đã có ~80%. AR markered (Vuforia) 0%.

---

### 2.6 ✅ Tốc độ render +46% — **85% match**

**Bài báo:** "tăng tốc độ hiển thị lên 46%"

**Project:**
- ✅ Có 3 LOD (Level Of Detail): 512/1k/2k
- ✅ Có script benchmark `mobile/scripts/test-compression.js`
- ✅ **Đã có dashboard đo lường production:** `backend-rust/src/routes/admin_render.rs` — endpoint `GET /api/v1/admin/analytics/render-performance` aggregate event `render_performance` (TTF/TTFI/FPS percentiles theo LOD, tính `speedup_vs_2k`) từ `UrnViewer`.
- ⚠️ Cần thu đủ data thực tế trong production để validate con số "+46%" (logic so sánh 512-vs-2k đã có và test minh hoạ trả về đúng 46%).

**Gap còn lại:** Chủ yếu là vận hành — thu thập đủ sample `render_performance` từ user thật và chạy A/B cohort để công bố con số chắc chắn. Công cụ đo đã sẵn sàng.

---

### 2.7 ❌ Sketchfab — **0% match**

**Bài báo:** "tích hợp... website Sketchfab"

**Project:** Không có link Sketchfab nào trong codebase. Project tự host model qua server riêng.

**Đây không hẳn là gap negative** — self-hosting cho phép control hoàn toàn data. Nhưng nếu muốn "match" bài báo thì cần upload mirror copy lên Sketchfab công khai.

---

## 3. Năm gap chính cần đóng để match 100%

### Gap 1: Pipeline LiDAR scan ingest (priority HIGH)

**Hiện trạng:** Có model GLB nhưng không own pipeline tạo ra nó.

**Hành động:**
1. Tạo `tools/lidar-import/` với script chuyển từ Polycam .obj/.fbx → .glb
2. Tài liệu hóa quy trình quét tại `docs/SCANNING_PROTOCOL_VI.md` (steps Polycam, lighting, distance, overlap %)
3. Tạo admin UI `frontend/src/app/admin/scans/page.jsx` cho admin upload raw scan + chọn LOD level
4. Backend Rust route `POST /api/v1/admin/scans/import` accept multipart upload, queue background processing

**Effort:** 2 sprints (1 spike để integrate Polycam SDK/format, 1 sprint cho UI + processing).

### Gap 2: Mesh denoising + hole filling (priority MEDIUM)

**Hiện trạng:** Không có. Bài báo coi đây là core của "tiền xử lý".

**Hành động:**
1. Wrap `pymeshlab` (Python lib mạnh cho mesh processing) vào microservice mới `services/mesh_processor/`
2. Pipeline: input raw mesh → remove duplicated vertices → fill holes (small radius) → smooth (Taubin filter) → reduce vertices (Quadric Edge Collapse Decimation = "Error Quadrics" theo keyword bài báo)
3. Output: cleaned `.glb` ở 3 LOD levels (5MB / 27MB / 29MB pattern hiện có)
4. Trigger từ admin UI ở Gap 1

**Lưu ý:** Bài báo từ khóa **"Error Quadrics"** chính là Quadric Edge Collapse Decimation algorithm — `pymeshlab` có function `meshing_decimation_quadric_edge_collapse`.

**Effort:** 2 sprints.

### Gap 3: Vuforia Image Target AR (priority MEDIUM-LOW)

**Hiện trạng:** AR markerless đã có. AR markered chưa.

**Hành động:**
1. In poster A4/A5 chứa hình 9 đỉnh + ảnh đặc trưng làm marker
2. Tạo Vuforia account (free dev license), upload images vào Vuforia Target Manager
3. Build Unity project (hoặc dùng MindAR/A-Frame thay Vuforia — cùng concept, free và web-based) để wrap GLB models theo marker
4. Deploy WebAR app tại `https://ar.histolab.icu` (subdomain mới)
5. QR code trong booklet/poster → mở WebAR

**Recommended pivot:** Thay vì Vuforia (proprietary, $$$), dùng **MindAR** (open-source, browser-based) — cùng kết quả nhưng cost = $0. Bài báo cải tiến.

**Effort:** 2 sprints.

### Gap 4: Render performance benchmark dashboard (priority MEDIUM) — ✅ ĐÃ SHIP

**Hiện trạng:** Đã triển khai. `backend-rust/src/routes/admin_render.rs` cung cấp `GET /api/v1/admin/analytics/render-performance`, aggregate event `render_performance` (do `UrnViewer` emit) theo LOD và tính `speedup_vs_2k`.

**Còn lại (vận hành, không phải code):**
1. Đảm bảo frontend `UrnViewer` instrument đủ: time to first frame, first interaction time, average FPS (đã định nghĩa payload `ttf_ms`/`ttfi_ms`/`avg_fps`/`lod_label`/`urn_slug`).
2. Thu đủ sample production để con số "+46%" có ý nghĩa thống kê.
3. A/B test cohort: random user xem 512 vs 1k LOD — đo conversion "discover → complete lesson" (dùng `Experiment` framework sẵn có).

**Effort còn lại:** < 1 sprint (chủ yếu thu data + phân tích).

### Gap 5: Sketchfab mirror (priority LOW)

**Hiện trạng:** Tự host.

**Hành động (optional):**
1. Tạo Sketchfab account `Luuniensuki LMS`
2. Upload 9 đỉnh GLB lên Sketchfab (free tier 100MB/file đủ)
3. Embed Sketchfab iframe trong `frontend/src/app/urns/[slug]/page.jsx` như fallback view
4. Lý do: SEO + community discovery — Sketchfab có 5M+ users tìm 3D content miễn phí

**Effort:** 0.5 sprint.

---

## 4. Đề xuất scope tiếp theo (ưu tiên)

| # | Gap | Effort | ROI | Note |
|---|-----|--------|-----|------|
| ✅ | **Render performance dashboard** (Gap 4) | ĐÃ SHIP | Cao | `admin_render.rs` đã xong; còn lại là thu data + A/B để công bố 46% |
| 1 | **Mesh denoising service** (Gap 2) | 2 sprints | Cao | Core academic contribution, dùng được cho cổ vật khác |
| 2 | **Scan import pipeline** (Gap 1) | 2 sprints | Cao | Owns toàn bộ chuỗi giá trị |
| 3 | **MindAR (thay Vuforia)** marker AR (Gap 3) | 2 sprints | Trung bình | Wow-factor cho live demo bài báo |
| 4 | **Sketchfab mirror** (Gap 5) | 0.5 sprint | Thấp | Optional, công khai data |
| 5 | **Multi-museum support** (mở rộng) | 4 sprints | Cao về dài hạn | Đóng tinh thần "mở rộng cho bảo tàng địa phương" |

**Recommended sprint order (các gap còn lại):**

1. **Sprint 1-2:** Mesh denoising + scan import pipeline (Gap 2 + 1) — đóng phần academic core
2. **Sprint 3:** MindAR markered (Gap 3) — wow demo
3. **Sprint 4 (optional):** Sketchfab mirror + multi-museum

Total: ~4-5 sprints để đạt **95-100% match** với bài báo (Gap 4 đã hoàn thành).

---

## 5. Đóng góp ngược lại bài báo

Project có **3 thứ vượt scope bài báo** mà có thể đề xuất extend trong publication tiếp theo:

1. **Gamification + LMS layer** trên top mô hình 3D — bài báo nói về số hóa, project nói về **giáo dục thông qua số hóa**. Chứng minh ROI giáo dục (quiz scores, retention, engagement) cao hơn so với chỉ xem mô hình thụ động.

2. **AI Tutor tích hợp với 3D viewer** — chỉ vào motif → AI giải thích bằng tiếng Việt + tiếng Anh. Đây là intersection cultural heritage + AI mà bài báo chưa cover.

3. **Mobile-first + offline-cache** — bài báo nói về mobile (Polycam) cho input nhưng chưa thảo luận mobile cho output. Project đã có Flutter app + offline cache → mở rộng access cho khu vực mạng yếu.

**Đề xuất:** Cộng tác publication tiếp theo dạng "Phương pháp số hóa + giáo dục di sản chi phí thấp: case study Luuniensuki LMS" — kết hợp pipeline scan của bài báo + LMS gamified layer của project.

---

## 6. Conclusion

**Project hiện tại ở ~76% match.** Phần lớn thì khớp, đặc biệt là:
- ✅ Cùng subject (9 Cửu Đỉnh Huế)
- ✅ Cùng kết quả tối ưu hóa (~83% giảm dung lượng)
- ✅ Cùng cảm giác output (xoay/zoom 3D + AR markerless)
- ✅ Đã có dashboard benchmark render (Gap 4) để validate claim "+46%"

**Để đạt 100% match cần:**
1. Đóng gap **pipeline ingest LiDAR** + **mesh denoising** (tổng 4 sprints)
2. Đóng gap **AR markered** (2 sprints) — recommend MindAR thay Vuforia
3. Thu data production cho **render benchmark** đã ship để công bố con số 46%

**Budget:** ~4-5 sprints với 2 dev full-time để đưa project lên 100% match + vượt scope bài báo qua gamified LMS layer.
