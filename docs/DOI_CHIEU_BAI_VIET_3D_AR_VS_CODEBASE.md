# Đối chiếu bài viết "Số hóa Cửu Đỉnh bằng LiDAR & AR" với codebase thực tế

> Tài liệu rà soát mức độ khớp giữa **nội dung bài viết học thuật** (giải pháp số hóa Cửu Đỉnh bằng scan 3D LiDAR + tối ưu hiển thị qua AR) và **dự án `luuniensuki-lms` thực tế** trong repo này.
> Mục tiêu: chỉ rõ điểm chưa phù hợp, mức độ nghiêm trọng, và hướng xử lý (sửa bài viết cho khớp thực tế, hoặc bổ sung code cho khớp bài viết).

Ngày rà soát: 2026-06-11

---

## 0. Cách đối chiếu

Tôi đã đọc trực tiếp các phần code/cấu hình liên quan đến 3D, model, và phân phối asset:

- Web (Next.js + React Three Fiber / three.js):
  - `frontend/src/components/live/HeritageStage3D.tsx`
  - `frontend/src/components/UrnViewer.tsx`
  - `frontend/src/components/viewer/Example.tsx`, `frontend/src/components/live2/AiAvatar.tsx`
  - `frontend/src/app/tools/annotate/page.jsx`
- Backend / dữ liệu:
  - `models.py`, `schemas.py`, `main.py` (trường `model_url`)
  - `seed.py` (`URN_MODEL_FILENAMES`, dữ liệu motif)
- Mobile (Flutter):
  - `mobile/...` (dùng Google `<model-viewer>` qua WebView)
- Hạ tầng:
  - `nginx-lms.conf`, `nginx-lms-histolab.conf`, `scripts/deployment/deploy-cors*.sh`

Quy ước mức độ:

- 🔴 **Phải sửa** — sai lệch lớn về sự thật kỹ thuật, công nghệ mô tả trong bài KHÔNG tồn tại trong dự án.
- 🟠 **Cần sửa** — số liệu/chi tiết không có căn cứ trong repo hoặc mâu thuẫn với code.
- 🟡 **Nên làm rõ** — đúng một phần, nhưng cách diễn đạt gây hiểu nhầm về phạm vi.
- 🟢 **Khớp** — bài viết phản ánh đúng dự án.

---

## 1. Bảng tổng hợp

| # | Nội dung bài viết | Thực tế trong codebase | Mức độ |
|---|-------------------|------------------------|--------|
| 1 | Tích hợp **Vuforia SDK** + Unity 3D để chạy AR, quét Tracker dán bàn học | Không có Vuforia, không có Unity, không có bất kỳ chế độ AR nào | 🔴 |
| 2 | Hiển thị mô hình trên **Sketchfab WebGL** | Không dùng Sketchfab; tự host GLB + render bằng three.js/R3F và Google model-viewer | 🔴 |
| 3 | Số hóa **cả 9** Cửu Đỉnh | Chỉ **6/9** đỉnh có file GLB; 3 đỉnh (Nhân, Anh, Dụ) bị comment "not yet available" | 🔴 |
| 4 | Mô hình tối ưu **18–56 MB**, gốc **280–345 MB** | Tài liệu mobile ghi kích thước thật ~**65–78 MB**; không có model 280–345 MB nào trong repo | 🟠 |
| 5 | Đạt **60 FPS** sau tối ưu, gốc 10–12 FPS; làm **Visual Turing Test** | Không có số liệu benchmark, không có test FPS hay Visual Turing Test trong repo | 🟠 |
| 6 | Pipeline LiDAR + Polycam + SOR + Poisson + Retopology + bake **Normal Map** + **PBR** | Repo chỉ **tiêu thụ** GLB hoàn chỉnh; không có bước/cấu hình pipeline nào, không có bake normal map | 🟠 |
| 7 | Tối ưu để chạy mượt nhờ nén hình học | Web loader dùng `useGLTF`/`GLTFLoader` **thuần**, không có DRACO/KTX2/meshopt | 🟠 |
| 8 | Học sinh vùng sâu xem được (ngụ ý offline/nhẹ) | Model load **từ server từ xa**, bắt buộc có internet + CORS; mobile đã bỏ asset bundle local | 🟡 |
| 9 | Cao Đỉnh có **17** họa tiết, tổng **153** bức chạm nổi | Số motif là dữ liệu động seed từ file toạ độ; con số 17/153 chưa có căn cứ trong repo | 🟡 |
| 10 | Hiển thị 3D xoay 360°, zoom, tương tác chọn họa tiết | Có thật: `OrbitControls`, click mesh → mở lesson theo `mesh_name` | 🟢 |
| 11 | Đối tượng là Cửu Đỉnh đặt trước Thế Miếu, đồng, patina, di sản | Khớp chủ đề dự án (urns/đỉnh, motif, lesson) | 🟢 |

---

## 2. Chi tiết từng điểm & hướng sửa

### 🔴 #1 — Vuforia AR không tồn tại trong dự án

**Bài viết (Mục 5.2, 6):** "tích hợp **Vuforia SDK**", "quét chỉ báo **Tracker** nằm dán sẵn bàn học", "Unity 3D Engine", mô hình "mọc kiêu hãnh… ngay giữa nền phòng".

**Thực tế:**
- Tìm toàn repo: **không có** chuỗi `Vuforia`, `Unity`, `WebXR`, `scene-viewer`, `quick-look`, `usdz`, `ar-modes`.
- Web hiển thị 3D trong `<Canvas>` của React Three Fiber (`HeritageStage3D.tsx`, `UrnViewer.tsx`) — đây là **3D trên màn hình**, không phải AR đặt vật thể vào không gian thực.
- Mobile dùng Google `<model-viewer>` nhúng trong WebView (`mobile/CUSTOM_MODEL_VIEWER_INTEGRATION.md`, `ARCHITECTURE_DIAGRAM.md`). `<model-viewer>` *có* thuộc tính `ar` nhưng **không hề được bật/cấu hình** ở đây (không có `ar`, `ar-modes`, không có file `.usdz` cho iOS Quick Look).

**Hướng sửa — chọn 1 trong 2:**
- **(Khuyến nghị) Sửa bài viết:** bỏ toàn bộ phần Vuforia/Unity/Tracker. Mô tả đúng: "hiển thị 3D tương tác trên web (three.js/R3F) và mobile (Google model-viewer)". Nếu muốn giữ chữ "AR", chỉ được nói ở dạng *định hướng tương lai*, không phải đã triển khai.
- **(Nếu muốn code khớp bài):** bật AR bằng chính `<model-viewer>` đang có — thêm `ar ar-modes="webxr scene-viewer quick-look"` và cung cấp bản `.usdz` cho iOS. **Không cần Vuforia/Unity.** Đây là cách rẻ và đúng với stack hiện tại.

---

### 🔴 #2 — Không dùng Sketchfab

**Bài viết (Mục 4.1, 5.1):** "Trang WebGL **Sketchfab** tải nhanh hơn 46%", "khi nạp mô hình… lên trang học **Sketchfab WebGL**".

**Thực tế:**
- Không có embed Sketchfab, không có domain `sketchfab.com` trong repo.
- Mô hình được **tự host** trên hạ tầng riêng: `seed.py` build `model_url` từ `store.histolab.icu`, phục vụ qua Nginx tại `https://lms.histolab.icu/assets/models/*.glb` (xem `nginx-lms.conf` block `location ^~ /assets/`, và `scripts/deployment/deploy-cors-auto.sh`).
- Render bằng three.js/R3F (web) hoặc model-viewer (mobile), không phải iframe Sketchfab.

**Hướng sửa:**
- **Sửa bài viết:** thay "Sketchfab WebGL" bằng mô tả đúng — "trình xem WebGL tự xây bằng three.js / React Three Fiber, model GLB tự host trên Nginx (`lms.histolab.icu/assets/models/`)". Con số "nhanh hơn 46%" cũng phải gắn vào đúng ngữ cảnh này (xem #5).

---

### 🔴 #3 — Mới có 6/9 đỉnh, không phải đủ 9

**Bài viết (Mục 4, 5.3):** "tạo ra bản sao số của **cả chín** chiếc Cửu Đỉnh", "sự tụ hội bản sao số học chín đỉnh đồng".

**Thực tế (`seed.py`, `URN_MODEL_FILENAMES`):**
```python
URN_MODEL_FILENAMES = {
    "cao-dinh":  "CAO-DINH-v1.glb",
    "chuong-dinh":"CHUONG-DINH-v1.glb",
    "huyen-dinh":"HUYEN-DINH-v1.glb",
    "nghi-dinh": "NGHI-DINH-v1.glb",
    "thuan-dinh":"THUAN-DINH-v1.glb",
    "tuyen-dinh":"TUYEN-DINH-v1.glb",
    # Models not yet available on store.histolab.icu:
    # "nhan-dinh": "NHAN-DINH-v1.glb",
    # "anh-dinh":  "ANH-DINH-v1.glb",
    # "du-dinh":   "DU-DINH-v1.glb",
}
```
- Chỉ **6** đỉnh có model: Cao, Chương, Huyền, Nghị, Thuần, Tuyên.
- **3 đỉnh thiếu**: Nhân, Anh, Dụ (bị comment).
- `mobile/FIX_3D_VIEWER_BLACK_SCREEN.md` còn ghi rõ tình trạng từng chỉ có 1 model local (`CAO-DINH-v1.glb`).

**Hướng sửa:**
- **Sửa bài viết:** nêu đúng "đã số hóa 6/9 đỉnh, đang hoàn thiện 3 đỉnh còn lại (Nhân, Anh, Dụ)".
- **Hoặc sửa code/asset:** bổ sung 3 file GLB còn thiếu lên `store.histolab.icu` rồi bỏ comment trong `URN_MODEL_FILENAMES` thì bài viết mới đúng.

---

### 🟠 #4 — Số liệu dung lượng không khớp

**Bài viết (Mục 4.1):** mô hình gốc **280–345 MB**, tối ưu **18–56 MB**.

**Thực tế:** Tài liệu mobile (`mobile/MODEL_DOWNLOAD_DIAGRAMS.md`) ghi kích thước file thật trong cache:
```
~78.5 MB, ~65.2 MB, ~72.1 MB
```
- Đây là các file GLB **đang dùng**, nằm trong khoảng ~65–78 MB — **lớn hơn** mức "18–56 MB" mà bài viết gọi là "đã tối ưu", và **không có** file 280–345 MB nào trong repo.

**Hướng sửa:**
- **Sửa bài viết:** dùng đúng dải kích thước thực tế (~65–78 MB) hoặc đo lại và trích nguồn cụ thể. Nếu muốn giữ con số "18–56 MB" thì phải thực sự tối ưu lại model (xem #7) và cập nhật file lên server.

---

### 🟠 #5 — FPS 60 và "Visual Turing Test" chưa có bằng chứng trong repo

**Bài viết (Mục 4, 5.1):** "đạt **60 FPS**", "gốc 10–12 FPS", "nhanh hơn **46%**", và bài kiểm tra **Visual Turing Test** với chuyên gia.

**Thực tế:**
- Không tìm thấy bất kỳ script benchmark, log đo FPS, hay tài liệu Visual Turing Test nào trong repo.
- `mobile/MODERN_BACKGROUND_TESTING.md` chỉ có **checklist FPS để trống** (`FPS: _____ / 60`) — tức là khung test chưa điền số, không phải kết quả đã đo.

**Hướng sửa:**
- **Sửa bài viết:** hoặc dẫn nguồn báo cáo đo đạc thật (đính kèm dữ liệu), hoặc hạ giọng thành "mục tiêu/kỳ vọng" thay vì kết quả đã kiểm chứng.
- **Hoặc bổ sung thật:** thêm trang đo FPS (ví dụ `stats.js` trong R3F) + biên bản Visual Turing Test rồi lưu kết quả vào `docs/`.

---

### 🟠 #6 — Pipeline LiDAR/Polycam/SOR/Poisson/Retopology/Normal-map nằm ngoài codebase

**Bài viết (Mục 3):** quy trình quét LiDAR bằng Polycam → lọc SOR → vá lỗ Poisson → Retopology → bake Normal Map → PBR.

**Thực tế:**
- Đây là **pipeline sản xuất asset ngoại tuyến** (offline content production). Repo này là **ứng dụng tiêu thụ** model: nó chỉ nhận file `.glb` đã hoàn chỉnh và hiển thị.
- Trong repo **không có** bất kỳ artifact nào của pipeline: không file Polycam, không cấu hình SOR/Poisson, không file bake normal map, không tài liệu thông số chụp (400–600 ảnh, overlap 80–85%…).

**Hướng sửa:**
- **Làm rõ trong bài viết** ranh giới: "Mục 3 mô tả quy trình tạo asset (ngoài repo phần mềm); repo `luuniensuki-lms` là tầng phân phối & hiển thị." Như vậy bài viết vẫn hợp lệ, chỉ cần nói rõ phần này không thuộc source code.
- **(Tùy chọn)** Lưu lại các asset trung gian / tài liệu pipeline vào một thư mục (vd `docs/pipeline/`) để có truy vết.

---

### 🟠 #7 — Web loader không hề nén hình học (không khớp tinh thần "tối ưu")

**Bài viết:** nhấn mạnh tối ưu hình học để chạy nhẹ.

**Thực tế:**
- `frontend/src/components/UrnViewer.tsx`, `live2/AiAvatar.tsx`, `app/tools/annotate/page.jsx` đều dùng `useGLTF(url)` **thuần**; `HeritageStage3D.tsx` dùng `new GLTFLoader()` **không** gắn `DRACOLoader`, `KTX2Loader`, hay `MeshoptDecoder`.
- Nghĩa là model tải về dạng GLB không nén → với file ~65–78 MB (#4) thì luận điểm "nhẹ, mượt trên điện thoại bình dân" của bài viết **chưa được code hậu thuẫn**.

**Hướng sửa (nếu muốn đạt đúng như bài):**
- Nén model bằng **Draco** (hình học) + **KTX2/Basis** (texture) hoặc **meshopt**, rồi gắn loader tương ứng:
  - R3F: cấu hình `useGLTF` với `draco`/`meshopt`; hoặc `GLTFLoader.setDRACOLoader(...)`, `setKTX2Loader(...)`, `setMeshoptDecoder(...)`.
- Sau khi nén thật, kích thước mới có thể chạm dải "18–56 MB" và số liệu trong bài mới đúng.

---

### 🟡 #8 — "Học sinh vùng sâu xem được" mâu thuẫn với cơ chế tải từ xa

**Bài viết (Mục 4.2, 5.3):** học sinh vùng sâu, vùng xa, hải đảo xem/xoay được mô hình.

**Thực tế:**
- Model load **từ server từ xa** (`lms.histolab.icu/assets/models/`), bắt buộc có internet và CORS đúng (`scripts/deployment/deploy-cors*.sh`).
- Mobile đã **bỏ bundle asset local**, chuyển hẳn sang remote URL (`mobile/FIX_3D_VIEWER_BLACK_SCREEN.md`, `mobile/assets/models/README.md`: "models are now loaded directly from remote URLs").
- Với file ~65–78 MB chưa nén, trải nghiệm ở mạng yếu sẽ không "mượt" như bài mô tả.

**Hướng sửa:**
- **Làm rõ trong bài:** cần kết nối internet; hoặc
- **Bổ sung code:** caching offline (mobile đã có `model_cache/` theo hash URL — xem `mobile/MODEL_DOWNLOAD_DIAGRAMS.md`), kết hợp nén ở #7 để đúng tinh thần "vùng sâu vẫn xem được".

---

### 🟡 #9 — Con số họa tiết (17 / 153) chưa truy được trong repo

**Bài viết:** Cao Đỉnh "17 họa tiết", và "153 bức chạm nổi" tổng.

**Thực tế:**
- Motif được seed động từ các file toạ độ `motif-coordinates-*.json` và dữ liệu seed (`seed.py`: `upsert_motif`, `mesh_name`, `3d_mesh_id`). Số lượng phụ thuộc dữ liệu thực tế nạp vào, không hard-code 17/153.
- Không tìm thấy hằng số/đếm "153" hay "17" trong code.

**Hướng sửa:**
- Đối chiếu lại con số bằng cách đếm motif thực tế sau seed (query bảng `motifs`), rồi điền số đúng vào bài. Nếu repo mới có 6/9 đỉnh thì tổng motif khả dụng cũng chưa thể là 153.

---

### 🟢 #10, #11 — Những điểm bài viết nói đúng

- **Hiển thị 3D tương tác** là có thật: `OrbitControls` cho xoay/zoom (`HeritageStage3D.tsx`, `UrnViewer.tsx`), tự động fit khung nhìn bằng `Box3`, click vào mesh → tra cứu motif theo `mesh_name` → mở nội dung bài học (mô tả trong `docs/implementation/04_Frontend_3D_Logic.md`).
- **Chủ đề & đối tượng** đúng: dự án xoay quanh Cửu Đỉnh/đỉnh đồng, họa tiết (motif), bài học di sản — khớp với mô tả Mục 1–2 của bài.
- **Định dạng GLB + tự host qua Nginx** là cách dự án đang dùng để phân phối model.

---

## 3. Việc cần làm (gợi ý ưu tiên)

**Nhóm A — Sửa bài viết cho khớp thực tế (nhanh, rủi ro thấp):**
1. Bỏ Vuforia/Unity/Tracker; mô tả đúng three.js/R3F + model-viewer (#1).
2. Bỏ Sketchfab; ghi "tự host GLB + WebGL viewer riêng" (#2).
3. Ghi đúng "6/9 đỉnh đã số hóa" (#3).
4. Cập nhật dải dung lượng thật (~65–78 MB) hoặc gắn nguồn đo (#4).
5. Hạ giọng FPS/Visual Turing Test thành mục tiêu, hoặc đính kèm dữ liệu (#5).
6. Tách rõ "pipeline tạo asset" vs "repo phần mềm" (#6, #9).

**Nhóm B — Bổ sung code để dự án tiệm cận bài viết (nếu muốn giữ nguyên claim):**
1. Bật AR bằng `<model-viewer>` (`ar ar-modes="webxr scene-viewer quick-look"` + `.usdz`) — không cần Vuforia (#1).
2. Nén model Draco/KTX2/meshopt + gắn loader trong R3F để đạt dải 18–56 MB (#4, #7).
3. Bổ sung 3 GLB còn thiếu (Nhân, Anh, Dụ) và mở comment trong `seed.py` (#3).
4. Thêm đo FPS (`stats.js`) + biên bản test, lưu vào `docs/` (#5).
5. Bổ sung cache offline để hỗ trợ mạng yếu (#8).

---

## 4. Phụ lục — dẫn chứng file

| Khẳng định | File dẫn chứng |
|------------|----------------|
| Render 3D web bằng R3F/three.js, OrbitControls, GLTFLoader thuần | `frontend/src/components/live/HeritageStage3D.tsx` |
| `useGLTF` không nén, click mesh → motif | `frontend/src/components/UrnViewer.tsx`, `frontend/src/app/tools/annotate/page.jsx` |
| Mobile dùng Google model-viewer qua WebView (không Vuforia) | `mobile/CUSTOM_MODEL_VIEWER_INTEGRATION.md`, `mobile/ARCHITECTURE_DIAGRAM.md` |
| Model load remote, bỏ asset local | `mobile/FIX_3D_VIEWER_BLACK_SCREEN.md`, `mobile/assets/models/README.md` |
| Chỉ 6/9 đỉnh có GLB | `seed.py` → `URN_MODEL_FILENAMES` |
| Kích thước model thật ~65–78 MB | `mobile/MODEL_DOWNLOAD_DIAGRAMS.md` |
| Tự host GLB + CORS qua Nginx (không Sketchfab) | `nginx-lms.conf`, `scripts/deployment/deploy-cors-auto.sh` |
| Trường `model_url` trong API/DB | `models.py`, `schemas.py`, `main.py` |
| Motif seed động theo `mesh_name`/toạ độ | `seed.py` → `upsert_motif`, `motif-coordinates-*.json` |
