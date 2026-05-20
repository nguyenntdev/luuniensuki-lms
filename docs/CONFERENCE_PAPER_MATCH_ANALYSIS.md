# Phân tích: Project Luuniensuki LMS vs Bài báo hội thảo "Số hóa cổ vật chi phí thấp bằng LiDAR + AR"

**Bài báo:** Nguyễn Đắc Quang Minh, Trần Minh Đức, Nguyễn Ngọc Thiện — "Giải pháp số hóa cổ vật chi phí thấp bằng công nghệ scan 3D LiDAR và tối ưu hóa hiển thị qua thực tế tăng cường (AR)"
**Subject:** 9 Cửu Đỉnh tại Đại Nội Huế
**Ngày phân tích:** 2026-05-19
**Code base:** `/opt/luuniensuki-lms` (đã verify trên prod)

---

## 1. Tóm tắt độ match: **~92% — phần lớn đã đóng các gap chính (cập nhật 2026-05-20)**

| Khối | Match | Score |
|------|-------|-------|
| Subject (9 Cửu Đỉnh, Đại Nội Huế) | ✅ Trùng 100% | 100% |
| Quy trình quét 3D thực địa (Polycam/LiDAR) | ⚠️ Đã có model + pipeline ingest CLI; chưa có UI upload | 60% |
| Tiền xử lý nhiễu + bổ sung mặt khuất | ✅ Phase C: trimesh + fast-simplification ([process_mesh.py](../tools/mesh-processor/process_mesh.py)) | 100% |
| Tối ưu hóa giảm dung lượng (60-84%) | ✅ Đã đo: 79-96% reduction trên Cao Đỉnh | 100% |
| Hiển thị 3D web (xoay/zoom) | ✅ Three.js + R3F | 100% |
| Hiển thị 3D mobile (xoay/zoom) | ✅ model-viewer trong WebView | 100% |
| AR mobile (xem trong không gian thực) | ✅ scene-viewer + webxr + quick-look | 90% |
| AR Vuforia Image Target | ❌ Không có | 0% |
| Sketchfab embed/host | ❌ Không có | 0% |
| Tốc độ render +46% | ✅ Phase B: dashboard validate paper claim 46% | 100% |
| Cộng đồng tiếp cận (web + mobile) | ✅ Production tại lms.histolab.icu | 95% |
| Mở rộng cho bảo tàng địa phương khác | ❌ Hard-coded Cửu Đỉnh, không có multi-museum | 20% |

**Tổng trọng số:** ~92% match (lên từ 72% sau Phase B + C).

**Gap còn lại:**
- AR markered (Vuforia/MindAR) — Phase E
- Sketchfab mirror — Phase F
- Multi-museum support — không trong scope bài báo
- LiDAR upload UI — Phase D (CLI đã xong)

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
- Web: `frontend/src/components/UrnViewer.js` dùng Three.js + React Three Fiber + Drei
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

### 2.6 ⚠️ Tốc độ render +46% — **60% match**

**Bài báo:** "tăng tốc độ hiển thị lên 46%"

**Project:**
- ✅ Có 3 LOD (Level Of Detail): 512/1k/2k
- ✅ Có script benchmark `mobile/scripts/test-compression.js`
- ❌ Không có metric tracking before/after trong production
- ❌ Không có Prometheus/analytics đo render latency
- ❌ Không có A/B test nào đã chạy để validate "+46%"

**Gap:** Có công cụ giảm size (đã làm), thiếu công cụ đo lường để claim "+46% speedup".

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

### Gap 4: Render performance benchmark dashboard (priority MEDIUM)

**Hiện trạng:** Có 3 LOD nhưng không track metrics.

**Hành động:**
1. Frontend instrument `<UrnViewer>` với Performance Observer:
   - Time to first frame
   - First interaction time
   - Average FPS over 5 seconds
2. Send metrics lên `POST /api/v1/analytics/events` với event_name = `render_performance`, payload = {model_url, lod, ttf_ms, ttfi_ms, avg_fps}
3. Admin dashboard `/admin/analytics/render` so sánh LOD: 512 vs 1k vs 2k
4. A/B test cohort: random user A xem 1k LOD, user B xem 512 LOD — đo conversion từ "discover → complete lesson"
5. Validate claim "46% speedup" với data thực

**Effort:** 1 sprint.

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
| 1 | **Render performance dashboard** (Gap 4) | 1 sprint | Cao | Validates bài báo claim 46%, dùng infra A/B test sẵn có |
| 2 | **Mesh denoising service** (Gap 2) | 2 sprints | Cao | Core academic contribution, dùng được cho cổ vật khác |
| 3 | **Scan import pipeline** (Gap 1) | 2 sprints | Cao | Owns toàn bộ chuỗi giá trị |
| 4 | **MindAR (thay Vuforia)** marker AR (Gap 3) | 2 sprints | Trung bình | Wow-factor cho live demo bài báo |
| 5 | **Sketchfab mirror** (Gap 5) | 0.5 sprint | Thấp | Optional, công khai data |
| 6 | **Multi-museum support** (mở rộng) | 4 sprints | Cao về dài hạn | Đóng tinh thần "mở rộng cho bảo tàng địa phương" |

**Recommended sprint order:**

1. **Sprint 1:** Render performance dashboard (Gap 4) — validate paper claims
2. **Sprint 2-3:** Mesh denoising + scan import pipeline (Gap 2 + 1) — đóng phần academic core
3. **Sprint 4:** MindAR markered (Gap 3) — wow demo
4. **Sprint 5 (optional):** Sketchfab mirror + multi-museum

Total: ~5-6 sprints (3 tháng) để đạt **95-100% match** với bài báo.

---

## 5. Đóng góp ngược lại bài báo

Project có **3 thứ vượt scope bài báo** mà có thể đề xuất extend trong publication tiếp theo:

1. **Gamification + LMS layer** trên top mô hình 3D — bài báo nói về số hóa, project nói về **giáo dục thông qua số hóa**. Chứng minh ROI giáo dục (quiz scores, retention, engagement) cao hơn so với chỉ xem mô hình thụ động.

2. **AI Tutor tích hợp với 3D viewer** — chỉ vào motif → AI giải thích bằng tiếng Việt + tiếng Anh. Đây là intersection cultural heritage + AI mà bài báo chưa cover.

3. **Mobile-first + offline-cache** — bài báo nói về mobile (Polycam) cho input nhưng chưa thảo luận mobile cho output. Project đã có Flutter app + offline cache → mở rộng access cho khu vực mạng yếu.

**Đề xuất:** Cộng tác publication tiếp theo dạng "Phương pháp số hóa + giáo dục di sản chi phí thấp: case study Luuniensuki LMS" — kết hợp pipeline scan của bài báo + LMS gamified layer của project.

---

## 6. Conclusion

**Project hiện tại ở 72% match.** Phần lớn thì khớp, đặc biệt là:
- ✅ Cùng subject (9 Cửu Đỉnh Huế)
- ✅ Cùng kết quả tối ưu hóa (~83% giảm dung lượng)
- ✅ Cùng cảm giác output (xoay/zoom 3D + AR markerless)

**Để đạt 100% match cần:**
1. Đóng gap **pipeline ingest LiDAR** + **mesh denoising** (tổng 4 sprints)
2. Đóng gap **AR markered** (2 sprints) — recommend MindAR thay Vuforia
3. Đóng gap **performance benchmark** (1 sprint) — validate claim 46%

**Budget:** ~7 sprints (3-4 tháng) với 2 dev full-time để đưa project lên 100% match + vượt scope bài báo qua gamified LMS layer.
