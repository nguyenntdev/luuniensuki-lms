# LƯU NIÊN — RBPC 2026: EXPLORE INFORMATION ARCHITECTURE & WIREFRAME SPECIFICATION

**Document Version:** 1.0 (Phase 1 Engineering Specification)  
**Date:** 18 October 2026  
**Status:** APPROVED FOR IMPLEMENTATION (Gate G1)  
**Author:** AGENT 06 — Frontend Explore Engineer  
**Scope:** Public Rebrand, Single-Header Navigation, `/explore` Catalogue, `/heritage/[slug]` Place Detail, Epistemic Source Rails, 3D Sketchfab Decision Gate, and Cultural Bridge AI Panel.  
**Repository Branch:** `feat/rbpc-cultural-bridge-2026`  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687`  

---

## 1. Executive Summary & Brand Transformation Architecture

### 1.1 From Monograph to Living Heritage Platform
The legacy platform operated as *Lưu Niên Sử Kí*, an edtech Learning Management System strictly centered on the Nine Dynastic Urns (*Cửu Đỉnh*) and its 162 bronze relief motifs. For the RMIT Business Plan Competition 2026 (RBPC 2026) under the theme **AI and Humanity: Building What's Next**, the product transitions into:

> **LƯU NIÊN — The Living Heritage Platform** (*Lưu Niên — Di sản sống*)  
> **Core Working Strapline:** *"Discover the story. Meet the people. Keep heritage alive."*  
> **Core Mechanism:** `Verified Cultural Context → Meaningful Human Connection → Experience Inquiry → Traceable Partner Value`

### 1.2 Information Architecture Domain Model
The product architecture standardizes on three integrated branches, with **Explore** and **Create** forming the P0 commercial MVP slice for the competition:

| Branch | Public Route | Purpose & Scope | MVP Status |
|---|---|---|---|
| **Explore** | `/explore`, `/heritage/[slug]` | Huế-wide heritage knowledge catalogue, primary source citations, 2D/3D viewers, and Cultural Bridge AI | **P0 (Must Demo)** |
| **Create** | `/people/[slug]`, `/experiences/[slug]` | Consented artisan profiles, craft lineages, workshop inquiries, and partner value tracking | **P0 (Thin Slice)** |
| **Learn** | `/learn` | Source-grounded historical pedagogy and lesson modules (reused from legacy core) | **P2 (Roadmap Context)** |

### 1.3 Strict Boundary Preservations
1. **Historic Cửu Đỉnh Preservation:** The Nine Dynastic Urns are preserved as an authentic historic collection card inside `/explore?collection=cuu-dinh` and deep routes (`/cuu-dinh/*`, `/atlas/*`). Factual historical texts retain proper nouns.
2. **STTTNNĐ Strict Isolation:** The aerial-map project and dataset located at `/dai-noi` are strictly quarantined. No RBPC routing, rebrand asset, or navigation change touches or redirects `/dai-noi`.
3. **Honest Epistemics:** All claims are bounded by verified primary sources. No 3D model is displayed without copyright clearance, and no simulated instant checkout or fake booking metric is presented.

### 1.4 Scoped Design Tokens & Cultural Editorial Palette

```
/* Contemporary Huế Cultural Editorial Design Tokens */
--color-ink:        #23282C;  /* Deep typography, high contrast WCAG AAA */
--color-rice:       #F7F3EA;  /* Warm ivory background, textured paper feel */
--color-plum:       #633B49;  /* Regal Hue imperial plum, primary accent */
--color-clay:       #A46452;  /* Terracotta / brick of Hue citadel & tombs */
--color-patina:     #5C756E;  /* Oxidized bronze & moss, secondary accent */
--color-line:       #D9D0C4;  /* Muted hairline borders and structural dividers */
--color-surface:    #FFFFFF;  /* Elevated card background */
--color-surface-dim:#EFEBE1;  /* Subtle container fills */
--color-error:      #9E3535;  /* Accessible alert / disputed state */
--color-success:    #2D6949;  /* Verified / cleared status */

/* Typography */
--font-display:     "Playfair Display", "Merriweather", "Noto Serif", Georgia, serif;
--font-body:        "Be Vietnam Pro", "Inter", -apple-system, sans-serif;
```

---

## 2. Unified Single-Header Navigation Architecture

### 2.1 The Problem in Legacy Navigation
Audit of `frontend/src/components/shell/GlobalHeader.tsx` and `MobileDrawer.tsx` revealed duplicate navigation structures:
- Desktop mounted both `HeritageMegaMenu` (with nested Cửu Đỉnh jargon) and `PRIMARY_NAV`.
- Mobile mounted `MobileNavigation` bottom bar alongside an extensive 396-line `MobileDrawer` containing 18+ links.
- Login buttons appeared with identical accessible names ("Đăng nhập"), triggering Playwright strict-mode violations in CI.

### 2.2 The Unified 5-Link Navigation Model
The unified header condenses all user journeys into exactly 5 top-level destinations, shared symmetrically across desktop and mobile disclosures:

```
[1] Khám phá (Explore)    -> /explore     (Huế-wide places, monuments, craft villages, map)
[2] Nghệ nhân (Makers)    -> /people      (Consented living artisans & cultural keepers)
[3] Trải nghiệm (Experience)-> /experiences (Curated cultural workshops & inquiry visits)
[4] Học tập (Learn)       -> /learn       (Source-grounded educational trails & modules)
[5] Về dự án (About)      -> /about       (Methodology, sources, RMIT 2026 team, ethics)
```

### 2.3 Desktop Header Layout (≥1024px)

```
+---------------------------------------------------------------------------------------------------+
|  [LN] LƯU NIÊN     Khám phá    Nghệ nhân    Trải nghiệm    Học tập    Về dự án    [Q Tìm kiếm (Ctrl+K)] [VI/EN] [Tài khoản] |
+---------------------------------------------------------------------------------------------------+
```

- **Height:** 56px (`h-14`), sticky `top-0`, z-index `40`, `border-b border-border/70 bg-background/90 backdrop-blur-xl`.
- **Brand Monogram:** 36x36px badge with `LN` in imperial plum/patina border + wordmark `LƯU NIÊN` with subtitle `DI SẢN SỐNG`.
- **Active Route Indicator:** Bottom border highlight `border-b-2 border-plum` with text `text-plum font-semibold`.
- **Search Trigger:** Semantic search button invoking the accessible `GlobalSearch` command palette (`⌘K` / `Ctrl+K`).
- **Language Switch:** Minimal toggle `VI | EN` persisting preference to cookie `NEXT_LOCALE`.

### 2.4 Mobile Header & Sheet Drawer (<1024px)

```
Top Bar (390px):
+--------------------------------------------------------------------+
|  [LN] LƯU NIÊN              [🔍 Tìm kiếm]  [🌙 Theme]  [☰ Menu]   |
+--------------------------------------------------------------------+

Mobile Sheet Drawer (Right Slide-over, role="dialog", aria-modal="true"):
+--------------------------------------------------+
|  [LN] LƯU NIÊN                 [✕ Đóng]          |
|  Di sản sống Cố đô Huế                           |
+--------------------------------------------------+
|  ĐIỀU HƯỚNG CHÍNH                                |
|  🧭 Khám phá di sản Huế            /explore      |
|  🪡 Nghệ nhân & Làng nghề         /people       |
|  🏮 Trải nghiệm văn hóa           /experiences  |
|  📚 Góc học tập di sản            /learn        |
|  🏛️ Về dự án & Nguồn sử liệu      /about        |
+--------------------------------------------------+
|  BỘ SƯU TẬP ĐẶC BIỆT                             |
|  🏺 Cửu Đỉnh & 162 Phù điêu       /cuu-dinh     |
|  🗺️ Bản đồ danh thắng Huế        /explore?view=map |
+--------------------------------------------------+
|  TIỆN ÍCH                                        |
|  🌐 Ngôn ngữ: [Tiếng Việt] [English]             |
|  [ Đăng nhập tài khoản ] (role="button")         |
+--------------------------------------------------+
```

---

## 3. Homepage Architecture & Wireframes

### 3.1 Content Structure & Hierarchy
The new homepage transitions from a technical relief explorer into an editorial cultural landing page:
1. **Hero Section:** Rights-cleared editorial visual of Huế, primary value proposition, and twin CTAs.
2. **Core 3-Step Value Mechanism:** `01 Khám phá bối cảnh` → `02 Gặp gỡ nghệ nhân` → `03 Trải nghiệm thực tế`.
3. **Heritage Ecosystem Facet Cards:** 4 entry gates (Imperial Architecture, Royal Tombs, Crafts, Music).
4. **Featured Curated Story:** Deep narrative journey highlighting the bridge between historic place and modern craft.
5. **Consented Artisan Spotlight:** Verified profile card with written consent badge and transparent inquiry link.
6. **Provenance & Trust Framework:** "Tại sao tin cậy LƯU NIÊN?" explaining the 5-layer academic citation gate.
7. **Footer:** Structural links, UNESCO WHC reference IDs, ethical disclosures, and RMIT competition acknowledgment.

### 3.2 Mobile Homepage Wireframe (390px Viewport)

```
+--------------------------------------------------+
| [LN] LƯU NIÊN              [🔍]  [🌙]  [☰ Menu]  |
+--------------------------------------------------+
| [HERO BANNER]                                    |
|  Eyebrow: LƯU NIÊN · DI SẢN SỐNG                 |
|  Headline:                                       |
|  Khám phá Huế qua                                |
|  những câu chuyện và con người.                  |
|                                                  |
|  Subline:                                        |
|  Tìm hiểu di sản với tư liệu có nguồn, rồi gặp   |
|  những người đang tiếp nối giá trị ấy.           |
|                                                  |
|  [ Khám phá di sản Huế ]  (Primary CTA)          |
|  [ Gặp người làm nghề ]   (Secondary CTA)        |
|                                                  |
|  +--------------------------------------------+  |
|  | [Ảnh tư liệu Sông Hương / Cố Đô Huế]       |  |
|  | Nguồn: Trung tâm BTDT Cố đô Huế (Trích dẫn) |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
| [CƠ CHẾ HOẠT ĐỘNG: 3 BƯỚC]                       |
|                                                  |
|  01. KHÁM PHÁ (EXPLORE)                          |
|  Tìm hiểu 14 cấu phần di sản UNESCO và các công  |
|  trình với sử liệu chính thống, không bịa đặt.   |
|                                                  |
|  02. KẾT NỐI (CONNECT)                           |
|  Lắng nghe câu chuyện từ nghệ nhân đang gìn giữ  |
|  nghề đúc đồng, pháp lam, hoa giấy, nhã nhạc.   |
|                                                  |
|  03. TRẢI NGHIỆM (EXPERIENCE)                    |
|  Gửi yêu cầu tham gia workshop thực tế.          |
|  Minh bạch: Đối tác sẽ liên hệ xác nhận lịch.    |
+--------------------------------------------------+
| [DANH MỤC TRỌNG TÂM]                             |
|  +---------------------+  +--------------------+ |
|  | 🏛️ Hoàng thành Huế  |  | 👑 Lăng tẩm triều  | |
|  | 14 cấu phần UNESCO  |  | Nguyễn (Tự Đức...) | |
|  +---------------------+  +--------------------+ |
|  +---------------------+  +--------------------+ |
|  | 🪡 Làng nghề truyền |  | 🎶 Nhã nhạc & Diễn | |
|  | thống (Đúc đồng...) |  | xướng Cung đình    | |
|  +---------------------+  +--------------------+ |
+--------------------------------------------------+
| [CÂU CHUYỆN TIÊU BIỂU]                           |
|  "Từ Vạc đồng Cung đình đến Ngọn lửa Phường Đúc"|
|  +--------------------------------------------+  |
|  | [Ảnh: Chi tiết đúc đồng & Lò rèn Phường Đúc]|  |
|  +--------------------------------------------+  |
|  Chứng cứ sử liệu: Đại Nam Thực Lục, Đệ nhị kỷ  |
|  Nghệ nhân đồng hành: Nghệ nhân Ưu tú N.V.S       |
|  [ Đọc câu chuyện đầy đủ -> ]                     |
+--------------------------------------------------+
| [CAM KẾT MINH BẠCH & TƯ LIỆU]                    |
|  ✓ 100% Nội dung khảo cứu có số trang & thư tịch |
|  ✓ Mô hình 3D ghi rõ cấp độ chính xác đo đạc     |
|  ✓ Nghệ nhân đồng thuận bằng văn bản             |
|  ✓ Không mô phỏng giao dịch thanh toán ảo        |
+--------------------------------------------------+
| [FOOTER]                                         |
|  LƯU NIÊN — Nền tảng Di sản Sống                 |
|  Dự án tham dự RMIT Business Plan Competition    |
|  © 2026 Nhóm tác giả học sinh LƯU NIÊN.          |
+--------------------------------------------------+
```

### 3.3 Desktop Homepage Wireframe (1440px Viewport)

```
+---------------------------------------------------------------------------------------------------+
|  [LN] LƯU NIÊN     Khám phá    Nghệ nhân    Trải nghiệm    Học tập    Về dự án    [Q Tìm kiếm (Ctrl+K)] [VI/EN] [Tài khoản] |
+---------------------------------------------------------------------------------------------------+
| [HERO SECTION]                                                                                    |
|  LEFT (55%):                                            RIGHT (45%):                              |
|  Eyebrow: [ LƯU NIÊN · DI SẢN SỐNG ]                    +---------------------------------------+ |
|  Headline:                                              | [High-Resolution Editorial Photograph]| |
|  Khám phá Huế qua                                       | Cửa Ngọ Môn & Kỳ Đài buổi sớm mai     | |
|  những câu chuyện và con người.                         |                                       | |
|                                                         | Photo: Bản quyền lưu trữ tư liệu      | |
|  Subline:                                               | CC BY-SA 4.0 Attribution              | |
|  Tìm hiểu di sản với sử liệu có trích dẫn nguồn,        +---------------------------------------+ |
|  rồi gặp gỡ những nghệ nhân đang tiếp nối giá trị ấy.   [ Thẻ nổi: 14 Cấu phần UNESCO chính thức] |
|                                                                                                   |
|  [ Khám phá di sản Huế -> ]   [ Gặp người làm nghề ]   [ Cách thức hoạt động ]                    |
+---------------------------------------------------------------------------------------------------+
| [3-STEP CORE VALUE FLOW]                                                                          |
|  +---------------------------+  +---------------------------+  +--------------------------------+ |
|  | 01. KHÁM PHÁ CÓ CĂN CỨ     |  | 02. KẾT NỐI CON NGƯỜI      |  | 03. TRẢI NGHIỆM THỰC TẾ        | |
|  | Tiếp cận 14 cấu phần di   |  | Gặp gỡ nghệ nhân làng nghề |  | Gửi yêu cầu workshop trực tiếp.| |
|  | sản thế giới với trích dẫn|  | đang kế thừa kỹ nghệ truyền|  | Minh bạch: Nhà cung cấp phản   | |
|  | Đại Nam Thực Lục & Hội Điển|  | thống có sự đồng thuận.    |  | hồi theo lịch thực tế.         | |
|  +---------------------------+  +---------------------------+  +--------------------------------+ |
+---------------------------------------------------------------------------------------------------+
| [HƯỚNG KHÁM PHÁ THEO KHÔNG GIAN VĂN HÓA]                                                          |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
|  | 🏛️ Cung đình Huế   |  | 👑 Lăng tẩm Hoàng  |  | 🪡 Làng nghề Huế   |  | 🎶 Nghệ thuật diễn |   |
|  | Kinh thành, Ngọ Môn|  | Lăng Tự Đức, Minh  |  | Đúc đồng, Pháp lam,|  | Nhã nhạc Cung đình,|   |
|  | Điện Thái Hòa...   |  | Mạng, Khải Định... |  | Tranh Làng Sình... |  | Ca Huế trên sông...|   |
|  | (18 địa điểm)      |  | (8 lăng tẩm lớn)   |  | (6 làng nghề sống) |  | (4 loại hình diễn) |   |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
+---------------------------------------------------------------------------------------------------+
| [CÂU CHUYỆN TIÊU BIỂU: CẦU NỐI VĂN HÓA]                                                           |
|  +-----------------------------------------+  +-------------------------------------------------+ |
|  | [Ảnh tư liệu: Vạc đồng Cung điện &     |  | CÂU CHUYỆN KHẢO CHỨNG SỐ 01                     | |
|  |  Xưởng đúc Phường Đúc hôm nay]          |  | "Từ Vạc đồng Cửu Đỉnh đến Ngọn lửa Phường Đúc"  | |
|  |                                         |  |                                                 | |
|  | Trạng thái: Đã kiểm chứng sử học         |  | Suốt hơn 200 năm, tiếng búa và mùi than củi ven | |
|  | Bản quyền: Giấy phép tư liệu mở         |  | bờ sông Hương vẫn chưa từng tắt...              | |
|  +-----------------------------------------+  | [ Xem tư liệu sử học ]  [ Gặp nghệ nhân ]       | |
+---------------------------------------------------------------------------------------------------+
| [TRỤ CỘT MINH BẠCH & ĐẠO ĐỨC DỮ LIỆU]                                                             |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
|  | 📚 Sử liệu có nguồn|  | 🔍 3D phân loại rõ |  | ✍️ Đồng thuận thật |  | 💳 Không thanh toán|   |
|  | Trích dẫn chính xác|  | Phân biệt scan đo  |  | Nghệ nhân ký văn   |  | giả lập. Quy trình |   |
|  | sách, tập, số trang|  | đạc vs minh họa mỹ |  | bản đồng ý xuất bản|  | yêu cầu khảo sát   |   |
|  | lưu trữ chính thức.|  | thuật rõ ràng.     |  | thông tin và ảnh.  |  | nhu cầu trung thực.|   |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. `/explore` Catalogue Architecture & Wireframes

### 4.1 Filter and Facet Model
The `/explore` catalogue allows browsing across all of Huế with rich, verifiable taxonomy filters:

1. **Keyword Search (`q`):** Accent-tolerant Vietnamese search (`Ngo Mon` matches `Ngọ Môn`), searching across `name_vi`, `name_en`, `official_reference_id`, and summaries.
2. **Category Facets (`category`):**
   - `Tất cả` (All)
   - `Kiến trúc Cung đình` (`imperial_architecture`)
   - `Lăng tẩm Hoàng gia` (`royal_tomb`)
   - `Làng nghề thủ công` (`craft_living_culture`)
   - `Âm nhạc & Diễn xướng` (`music_performance`)
   - `Danh thắng & Cảnh quan` (`landscape_nature`)
   - `Tín ngưỡng & Tôn giáo` (`religious_spiritual`)
3. **Filter Pills & Toggles:**
   - `UNESCO 14 Cấu phần`: Filters specifically for UNESCO property IDs `678-001` through `678-014`.
   - `Có mô hình 3D`: Only displays assets with rights-cleared, verified 3D embeds or models.
   - `Trạng thái`: Open (`open`), Restoration (`undergoing_restoration`), Restricted (`restricted`).
4. **View Toggle:** `[Dạng lưới / Grid]` vs `[Bản đồ / Map]`.
5. **Sort Options (`sort`):** Relevance, Name (A-Z), Historical Era, Newest.

### 4.2 Mobile `/explore` Wireframe (390px Viewport)

```
+--------------------------------------------------+
| [LN] LƯU NIÊN              [🔍]  [🌙]  [☰ Menu]  |
+--------------------------------------------------+
| Khám phá di sản Huế                              |
| 14 cấu phần UNESCO & các di tích gắn liền        |
|                                                  |
| +----------------------------------------------+ |
| | 🔍 Tìm kiếm di tích, lăng tẩm, làng nghề...  | |
| +----------------------------------------------+ |
|                                                  |
| [Tất cả] [🏛️ Cung đình] [👑 Lăng tẩm] [🪡 Nghề]  | (Horizontal scrollable pill tabs)
|                                                  |
| [⚡ Bộ lọc nâng cao (2)]   [Chế độ: Lưới | Bản đồ]|
|                                                  |
| Đang hiển thị 14 địa điểm đã kiểm chứng          |
+--------------------------------------------------+
| [CARD 1: Lăng Tự Đức]                            |
| +----------------------------------------------+ |
| | [Thumbnail Image: Khiêm Lăng]                | |
| | [UNESCO 678-007]           [Có mô hình 3D]   | |
| +----------------------------------------------+ |
| Lăng Tự Đức (Khiêm Lăng)                         |
| Tomb of Emperor Tu Duc                           |
| Triều Tự Đức (1864–1867) • Thủy Xuân, Huế        |
| Quần thể lăng tẩm đỉnh cao của kiến trúc cảnh    |
| quan triều Nguyễn với hồ Lưu Khiêm và Khiêm Cung.|
| 2 nguồn sử học xác thực • 1 mô hình 3D đo đạc    |
| [ Chi tiết di sản -> ]                           |
+--------------------------------------------------+
| [CARD 2: Ngọ Môn]                                |
| +----------------------------------------------+ |
| | [Thumbnail Image: Cổng Ngọ Môn]              | |
| | [UNESCO 678-001]           [Có mô hình 3D]   | |
| +----------------------------------------------+ |
| Ngọ Môn — Đại Nội Huế                            |
| Meridian Gate, Hue Imperial City                 |
| Triều Minh Mạng (1833) • Đại Nội, Huế            |
| Cổng chính phía Nam của Hoàng thành Huế, nơi     |
| diễn ra lễ Truyền Lô và sự kiện thoái vị 1945.   |
| 3 nguồn sử học xác thực • Lầu Ngũ Phụng          |
| [ Chi tiết di sản -> ]                           |
+--------------------------------------------------+
| [CARD 3: Làng Đúc đồng Phường Đúc]               |
| +----------------------------------------------+ |
| | [Thumbnail Image: Nghệ nhân rót đồng]        | |
| | [Làng nghề truyền thống]  [Có nghệ nhân]     | |
| +----------------------------------------------+ |
| Làng Đúc đồng Phường Đúc                         |
| Phuong Duc Bronze Casting Heritage               |
| Thế kỷ XVII đến nay • Phường Đúc, Huế            |
| Cái nôi đúc nên Cửu Đỉnh, Vạc đồng và Chuông Đại|
| Hồng Chung Thiên Mụ. 1 nghệ nhân đồng thuận.     |
| [ Chi tiết di sản -> ]                           |
+--------------------------------------------------+
| [ Nút: Tải thêm kết quả (Trang 1/2) ]            |
+--------------------------------------------------+
```

### 4.3 Desktop `/explore` Wireframe (1440px Viewport)

```
+---------------------------------------------------------------------------------------------------+
|  [LN] LƯU NIÊN     Khám phá    Nghệ nhân    Trải nghiệm    Học tập    Về dự án    [Q Tìm kiếm (Ctrl+K)] [VI/EN] [Tài khoản] |
+---------------------------------------------------------------------------------------------------+
| Trang chủ > Khám phá di sản Huế                                                                   |
|                                                                                                   |
| KHÁM PHÁ DI SẢN CỐ ĐÔ HUẾ                                                                         |
| Khảo cứu 14 cấu phần Quần thể Di tích Huế (UNESCO 678) cùng các thực thể lịch sử và làng nghề    |
|                                                                                                   |
| +-----------------------------------------------------------------------------+ +---------------+ |
| | 🔍 Nhập tên di tích, nhân vật lịch sử, bảo vật hoặc làng nghề truyền thống... | | [Sắp xếp: ...]v| |
| +-----------------------------------------------------------------------------+ +---------------+ |
|                                                                                                   |
| [Tất cả danh mục] [🏛️ Cung đình] [👑 Lăng tẩm] [🪡 Làng nghề] [🎶 Diễn xướng] [🌊 Danh thắng]   |
|                                                                                                   |
| [ ] Chỉ hiện 14 cấu phần UNESCO   [ ] Có mô hình 3D tương tác   [ Chế độ: [■ Lưới] [🗺️ Bản đồ] ]   |
+---------------------------------------------------------------------------------------------------+
| Đang hiển thị 14 kết quả được khảo chứng thư tịch                                                 |
|                                                                                                   |
| +---------------------------+ +---------------------------+ +-----------------------------------+ |
| | [Ảnh: Lăng Tự Đức]        | | [Ảnh: Ngọ Môn]            | | [Ảnh: Chùa Thiên Mụ]              | |
| | [UNESCO 678-007] [3D Scan]| | [UNESCO 678-001] [3D Scan]| | [UNESCO 678-002] [Tư liệu 2D]     | |
| |                           | |                           | |                                   | |
| | LĂNG TỰ ĐỨC (KHIÊM LĂNG)  | | NGỌ MÔN — ĐẠI NỘI HUẾ     | | CHÙA THIÊN MỤ (LINH MỤ)           | |
| | Tomb of Emperor Tu Duc    | | Meridian Gate, Hue City   | | Thien Mu Pagoda                   | |
| | 1864–1867 • Triều Tự Đức  | | 1833 • Triều Minh Mạng    | | Khởi lập 1601 • Chúa Tiên         | |
| | Quần thể kiến trúc cảnh   | | Cổng chính Nam Hoàng thành| | Ngôi quốc tự cổ kính bên bờ sông  | |
| | quan soi bóng hồ Lưu Khiêm| | lầu Ngũ Phụng 9 nóc.      | | Hương, nơi lưu giữ Đại Hồng Chung.| |
| | 2 trích dẫn • 1 mô hình 3D| | 3 trích dẫn • 1 mô hình 3D| | 4 trích dẫn • Tư liệu chuông 1710 | |
| | [ Chi tiết di sản -> ]    | | [ Chi tiết di sản -> ]    | | [ Chi tiết di sản -> ]            | |
| +---------------------------+ +---------------------------+ +-----------------------------------+ |
|                                                                                                   |
| +---------------------------+ +---------------------------+ +-----------------------------------+ |
| | [Ảnh: Làng Đúc đồng]      | | [Ảnh: Cung An Định]       | | [Ảnh: Điện Thái Hòa]              | |
| | [Làng nghề] [Có Workshop] | | [Di tích lịch sử] [3D Scan| | [UNESCO 678-001] [Khung gỗ 3D]    | |
| |                           | |                           | |                                   | |
| | ĐÚC ĐỒNG PHƯỜNG ĐÚC       | | CUNG AN ĐỊNH              | | ĐIỆN THÁI HÒA                     | |
| | Bronze Casting Community  | | An Dinh Palace            | | Palace of Supreme Harmony         | |
| | Thế kỷ XVII – Hiện nay    | | 1917–1918 • Khải Định     | | 1805–1833 • Gia Long, Minh Mạng   | |
| | Kỹ nghệ đúc đồng truyền   | | Tuyệt tác giao thoa kiến  | | Trung tâm quyền lực triều Nguyễn, | |
| | thống nuôi dưỡng Cửu Đỉnh | | trúc Cung đình & Tân cổ   | | nơi diễn ra các đại lễ đăng quang.| |
| | 1 Nghệ nhân • 1 Trải nghiệm| | điển Pháp. 2 nguồn kiểm tra| | 3 trích dẫn • Khảo cứu trùng tu   | |
| | [ Chi tiết di sản -> ]    | | [ Chi tiết di sản -> ]    | | [ Chi tiết di sản -> ]            | |
| +---------------------------+ +---------------------------+ +-----------------------------------+ |
|                                                                                                   |
|                      [ << Trang trước ]   [ 1 ]   [ 2 ]   [ Trang sau >> ]                        |
+---------------------------------------------------------------------------------------------------+
```

---

## 5. `/heritage/[slug]` Place Detail Architecture & Wireframes

### 5.1 Place Detail Sections & Content Hierarchy
The `/heritage/[slug]` place detail route provides a deep, evidence-backed showcase:

1. **Breadcrumb Bar & Designation Chips:** Hierarchy path, UNESCO inventory ID (e.g. `UNESCO 678-007`), entity type, and current conservation status.
2. **Hero Showcase (Tabs Component):**
   - **Tab 1: Hình ảnh 2D (Photos):** Curated, licensed photography with visible credits and provenance tags.
   - **Tab 2: Mô hình 3D (Sketchfab Exhibit):** User-initiated lazy iframe embed. Displays accuracy badge (`survey_grade`, `measured_photogrammetry`), original author link, CC license attribution, and "Kích hoạt mô hình 3D". Does **not** auto-play or stream without user action.
   - **Tab 3: Bản vẽ tư liệu (Archives):** Historic maps, architectural plans, and stele rubbings.
3. **Verified Historical Narrative:** 80–150 word factual synthesis cross-referenced with primary imperial records.
4. **Source Evidence Rail (Thư viện chứng cứ sử liệu):** Explicit citation cards showing book title, author, volume, page number, and original statement.
5. **Living Culture Connection (Cầu nối Di sản Sống):** Direct relational bridge card to living crafts and artisans (e.g. Phường Đúc Bronze Foundry or Pháp Lam Enamel Studio).
6. **Cultural Bridge AI Panel:** Scoped conversation drawer parameterized to `content_scope = 'RBPC_HUE'`, providing 2 modes (Quick Explanation ≤120 words, Deep Context ≤250 words) with mandatory footnote links to source citations.

### 5.2 Mobile `/heritage/[slug]` Wireframe (390px Viewport)

```
+--------------------------------------------------+
| [LN] LƯU NIÊN              [🔍]  [🌙]  [☰ Menu]  |
+--------------------------------------------------+
| Trang chủ > Khám phá > Lăng Tự Đức               |
|                                                  |
| [UNESCO 678-007]  [Quần thể Lăng tẩm]  [Mở cửa]   |
|                                                  |
| LĂNG TỰ ĐỨC (KHIÊM LĂNG)                         |
| Tomb of Emperor Tu Duc                           |
| Niên đại: 1864–1867 • Triều vua Tự Đức           |
| Địa điểm: Thủy Xuân, Thành phố Huế               |
+--------------------------------------------------+
| [MEDIA SHOWCASE]                                 |
|  [ Ảnh 2D (4) ]  [ Mô hình 3D (1) ]  [ Bản vẽ (2)]|
|                                                  |
|  +--------------------------------------------+  |
|  | [3D TAB ACTIVE]                            |  |
|  | Mô hình: Tomb of Tu Duc                    |  |
|  | Tác giả: matousekfoto (CyArk Dataset)      |  |
|  | Giấy phép: CC BY 4.0 (Ghi công tác giả)    |  |
|  | Cấp độ: Đo đạc ảnh thực (Photogrammetry)   |  |
|  |                                            |  |
|  |       [ ▶ KÍCH HOẠT MÔ HÌNH 3D ]           |  |
|  |   (Chỉ tải dữ liệu khi bạn nhấn nút)       |  |
|  +--------------------------------------------+  |
|  Attribution: Model based on CyArk scans under    |
|  CC BY 4.0. Opens Sketchfab viewer securely.     |
+--------------------------------------------------+
| [KHẢO CHỨNG LỊCH SỬ]                             |
| Khiêm Lăng được xây dựng từ năm 1864 đến 1867    |
| trên một thung lũng hẹp thuộc làng Dương Xuân    |
| Thượng. Không chỉ là nơi an nghỉ, đây còn là nơi |
| vua Tự Đức lui tới làm việc, làm thơ giữa cảnh   |
| quan hồ Lưu Khiêm và rừng thông u tịch...        |
| [Đọc tiếp bài khảo chứng ->]                     |
+--------------------------------------------------+
| [NGUỒN THƯ TỊCH XÁC THỰC (2 NGUỒN)]              |
|                                                  |
|  +--------------------------------------------+  |
|  | 📜 Đại Nam Thực Lục — Chính biên, Đệ tứ kỷ |  |
|  | Quốc sử quán triều Nguyễn                   |  |
|  | Quyển 30, tr. 142 • Năm Tự Đức thứ 17 (1864)|  |
|  | "Khởi công xây dựng Vạn Niên Cơ, sau đổi   |  |
|  | tên thành Khiêm Cung..."                   |  |
|  | [✓ Đã kiểm chứng trang sách]               |  |
|  +--------------------------------------------+  |
|  | 📜 Khâm Định Đại Nam Hội Điển Sự Lệ       |  |
|  | Bộ Công biên soạn • Quyển 118, tr. 89      |  |
|  | Quy chuẩn kiến trúc đình, tạ và hồ nước... |  |
|  | [✓ Đã kiểm chứng trang sách]               |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
| [CẦU NỐI DI SẢN SỐNG & NGHỆ NHÂN]                |
|  Gắn liền: Nghề khảm sành sứ & Đúc đồng Huế      |
|  Nghệ nhân tiếp nối: Nghệ nhân Ưu tú N.V.S       |
|  "Kỹ thuật cẩn xà cừ và chạm khắc gỗ Khiêm Cung  |
|  hiện vẫn được các hiệp thợ Huế trao truyền..." |
|                                                  |
|  [ Xem hồ sơ nghệ nhân & Workshop -> ]           |
+--------------------------------------------------+
| [HỎI ĐÁP CÙNG CULTURAL BRIDGE AI]                |
|  Cố vấn văn hóa ảo (Dựa trên tư liệu khảo chứng) |
|                                                  |
|  Gợi ý câu hỏi:                                  |
|  [ Vì sao Khiêm Lăng có kiến trúc như hành cung?]|
|  [ Ý nghĩa của hồ Lưu Khiêm và nhà tạ? ]        |
|                                                  |
|  +--------------------------------------------+  |
|  | Nhập câu hỏi về bối cảnh văn hóa...    [Gửi]|  |
|  +--------------------------------------------+  |
|  Lưu ý: AI chỉ phản hồi dựa trên nguồn đã kiểm tra|
+--------------------------------------------------+
| [STICKY BOTTOM BAR (Mobile)]                     |
|  Lăng Tự Đức • UNESCO 678-007                    |
|  [ Gửi yêu cầu trải nghiệm / Tham quan ]         |
+--------------------------------------------------+
```

### 5.3 Desktop `/heritage/[slug]` Wireframe (1440px Viewport)

```
+---------------------------------------------------------------------------------------------------+
|  [LN] LƯU NIÊN     Khám phá    Nghệ nhân    Trải nghiệm    Học tập    Về dự án    [Q Tìm kiếm (Ctrl+K)] [VI/EN] [Tài khoản] |
+---------------------------------------------------------------------------------------------------+
| Trang chủ > Khám phá di sản Huế > Lăng Tự Đức (Khiêm Lăng)                                        |
|                                                                                                   |
| [UNESCO 678-007]  [Quần thể Lăng tẩm Hoàng gia]  [Hiện trạng: Bảo tồn tốt]  [Mở cửa tham quan]    |
|                                                                                                   |
| LĂNG TỰ ĐỨC — KHIÊM LĂNG                                                                         |
| Tomb of Emperor Tu Duc • Quần thể kiến trúc cảnh quan đỉnh cao thời Nguyễn                       |
| Niên đại: 1864–1867 • Triều vua Tự Đức | Địa điểm: Thôn Thượng Ba, Phường Thủy Xuân, Huế         |
+---------------------------------------------------------------------------------------------------+
| MAIN CONTENT LAYOUT (GRID 70% / 30%)                                                              |
|                                                                                                   |
| LEFT COLUMN (70%):                                      RIGHT COLUMN (30%):                       |
| +-----------------------------------------------------+ +---------------------------------------+ |
| | [TABS: (1) Ảnh chụp 2D  |(2) Mô hình 3D  |(3) Bản vẽ] | | THÔNG TIN DI TÍCH                   | |
| | +-------------------------------------------------+ | |                                       | |
| | | [INTERACTIVE 3D VIEWER CONTAINER]               | | | Cấp bảo tồn: Di sản Thế giới UNESCO   | |
| | | Tên mô hình: Tomb of Tu Duc                     | | | Mã định danh: UNESCO 678-007          | |
| | | Tác giả scan: matousekfoto / OpenHeritage3D     | | | Tọa độ: 16.4332° N, 107.5658° E       | |
| | | Giấy phép: CC BY 4.0 Attribution                | | | Độ chính xác vị trí: Exact GPS        | |
| | | Cấp độ đo đạc: Measured Photogrammetry          | | | Giờ mở cửa: 07:00 – 17:30 hằng ngày   | |
| | |                                                 | | | Giá vé: Theo quy định TTBTDT Cố Đô    | |
| | |       [ ▶ BẬT MÔ HÌNH 3D TƯƠNG TÁC ]            | | +---------------------------------------+ |
| | |   (Iframe bảo mật Sketchfab lazy-load)          | | [CẦU NỐI DI SẢN SỐNG]                   | |
| | +-------------------------------------------------+ | | Nghệ nhân kế thừa truyền thống:       | |
| | Ghi công: CyArk / OpenHeritage3D dataset. Phục vụ | | | [Ảnh chân dung Nghệ nhân N.V.S]       | |
| | nghiên cứu và giáo dục di sản văn hóa.            | | | Nghệ nhân Ưu tú Nguyễn Văn S.         | |
| +-----------------------------------------------------+ | Làng nghề Đúc đồng Phường Đúc         | |
|                                                         | "Gìn giữ ngọn lửa đúc đồng hơn 40     | |
| [BÀI KHẢO CHỨNG LỊCH SỬ XÁC THỰC]                       | năm, tham gia phục chế đồ đồng thờ tự"| |
| Khiêm Lăng là một trong những công trình đẹp nhất của   | [ Gặp nghệ nhân & Đặt trải nghiệm -> ]| |
| kiến trúc cung đình thời Nguyễn. Được xây dựng khi nhà  | +---------------------------------------+ |
| vua còn tại vị, Khiêm Lăng không mang màu sắc u buồn    | [HỎI ĐÁP CÙNG AI CULTURAL BRIDGE]       | |
| của một lăng mộ thông thường mà hiện lên như một khu    | | 💬 Hỏi về bối cảnh văn hóa di tích:   | |
| lâm viên thanh nhã với gần 50 công trình lớn nhỏ...     | | [ Vì sao lăng có 50 chữ Khiêm? ]     | |
|                                                         | | [ Nghệ thuật cẩn sành sứ ở đâu? ]   | |
| [THƯ VIỆN NGUỒN & CHỨNG CỨ THƯ TỊCH]                    | | +-----------------------------------+ | |
| +-----------------------------------------------------+ | | [Nhập câu hỏi...            ] [Gửi]| | |
| | 📜 Đại Nam Thực Lục (Chính biên, Đệ tứ kỷ)          | | +-----------------------------------+ | |
| | Tác giả: Quốc sử quán triều Nguyễn                  | | Phản hồi tự động:                     | |
| | Trích yếu: Quyển 30, tờ 12b-14a (Năm Giáp Tý 1864)  | | "Mọi công trình tại lăng đều mang     | |
| | "Mùa thu tháng 8, khởi đắp Khiêm Lăng. Sai quan văn | | chữ Khiêm (khiêm tốn), thể hiện tấm   | |
| | võ đổng biện công việc, định rõ quy thức doanh tạo."| | lòng và tâm sự u uẩn của vua Tự Đức   | |
| | Trạng thái: [✓ Đã đối chiếu bản khắc Mộc bản]       | | trước vận nước biến động [Nguồn: 1]"  | |
| +-----------------------------------------------------+ +---------------------------------------+ |
| +-----------------------------------------------------+                                           |
| | 📜 Khâm Định Đại Nam Hội Điển Sự Lệ (Bộ Công)       |                                           |
| | Tác giả: Nội các triều Nguyễn biên soạn (1851–1868) |                                           |
| | Trích yếu: Quyển 118, Điều khoản Lăng tẩm           |                                           |
| | Trạng thái: [✓ Đã đối chiếu văn bản Hán-Nôm]        |                                           |
| +-----------------------------------------------------+                                           |
+---------------------------------------------------------------------------------------------------+
```

---

## 6. End-to-End Visitor User Journey Matrix

### 6.1 Step-by-Step Flow

```
[ BƯỚC 1: TIẾP CẬN ] 
     │   Người dùng truy cập trang chủ LƯU NIÊN (Desktop hoặc Mobile)
     ▼
[ BƯỚC 2: KHÁM PHÁ DANH MỤC ]
     │   Chọn "Khám phá di sản Huế" -> Vào `/explore`
     │   Lọc theo "Lăng tẩm Hoàng gia" hoặc tìm kiếm "Lăng Tự Đức"
     ▼
[ BƯỚC 3: CHI TIẾT DI TÍCH ]
     │   Mở `/heritage/lang-tu-duc`
     │   Đọc bài khảo chứng lịch sử 120 từ, kiểm tra nguồn Đại Nam Thực Lục
     ▼
[ BƯỚC 4: TƯƠNG TÁC ĐA PHƯƠNG TIỆN ]
     │   Nhấn tab "Mô hình 3D" -> Xem mô hình Sketchfab đã kiểm duyệt bản quyền
     │   Hỏi AI Cultural Bridge: "Ai là người trực tiếp tham gia xây dựng lăng?"
     ▼
[ BƯỚC 5: CẦU NỐI VĂN HÓA SỐNG ]
     │   Thấy Thẻ liên kết: "Nghệ nhân Đúc đồng & Khảm sành sứ Phường Đúc"
     │   Nhấn "Xem hồ sơ nghệ nhân" -> Chuyển sang `/people/nghe-nhan-phuong-duc`
     ▼
[ BƯỚC 6: GỬI YÊU CẦU TRẢI NGHIỆM ]
     │   Nhấn "Gửi yêu cầu trải nghiệm" (Inquiry request form)
     │   Nhận thông báo minh bạch: "Đã ghi nhận yêu cầu. Nghệ nhân sẽ liên hệ nếu có lịch phù hợp."
```

### 6.2 Epistemic Rights Decision Gate for 3D Assets

Before displaying any 3D asset in Tab 2, the frontend evaluates the asset metadata against the Rights Decision Gate:

```
                  [ 3D Model Candidate ]
                            │
              Có URL và UUID chính xác không?
                      /           \
                   Có              Không ──> [ Chuyển sang ảnh 2D & Ghi chú ]
                   │
           Mô hình có vi phạm SF-020 (Bịa đặt)?
                      /           \
                 Không             Có ────> [ CHẶN HOÀN TOÀN (Negative Guardrail) ]
                   │
            Giấy phép là CC BY hay CC0?
                      /           \
                   Có              Không ──> [ CC BY-NC-SA / NoAI: Chỉ nghiên cứu, ]
                   │                         [ KHÔNG dùng cho thương mại/AI        ]
     Tác giả cho phép Embed Iframe hợp lệ?
                      /           \
                   Có              Không ──> [ Liên hệ tác giả xin phép bằng văn bản]
                   │
        [ HIỂN THỊ NÚT KÍCH HOẠT 3D ]
        - Lazy load iframe khi click
        - Hiển thị nhãn Accuracy Grade
        - Dẫn link ghi công tác giả & Sketchfab
```

---

## 7. System State Wireframes: Loading, Empty, and Error Handling

### 7.1 Loading State Wireframes (Skeleton UI)

#### 7.1.1 Mobile Loading State (`/explore`)
```
+--------------------------------------------------+
| [LN] LƯU NIÊN              [🔍]  [🌙]  [☰ Menu]  |
+--------------------------------------------------+
| [████████████████]       (Skeleton title)        |
| [██████████████████████] (Skeleton subtitle)     |
|                                                  |
| +----------------------------------------------+ |
| | [██████████████████████████████████████████] | |
| +----------------------------------------------+ |
|                                                  |
| [████] [██████] [██████] [████] (Skeleton pills) |
|                                                  |
| +----------------------------------------------+ |
| | [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  | | (Pulsing image placeholder)
| | [██████████]             [██████]            | |
| |                                              | |
| | [██████████████████████]                     | |
| | [████████████████████████████████████]       | |
| | [████████████████████]                       | |
| +----------------------------------------------+ |
| +----------------------------------------------+ |
| | [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  | |
| | [██████████]             [██████]            | |
| |                                              | |
| | [██████████████████████]                     | |
| +----------------------------------------------+ |
+--------------------------------------------------+
```

### 7.2 Empty State Wireframes

#### 7.2.1 No Search Results (`/explore?q=XYZ`)
```
+---------------------------------------------------------------------------------------------------+
|  [LN] LƯU NIÊN     Khám phá    Nghệ nhân    Trải nghiệm    Học tập    Về dự án    [Q Tìm kiếm (Ctrl+K)] [VI/EN] [Tài khoản] |
+---------------------------------------------------------------------------------------------------+
| Trang chủ > Khám phá di sản Huế                                                                   |
|                                                                                                   |
| +-----------------------------------------------------------------------------+ +---------------+ |
| | 🔍 Tháp Chăm Cổ Đại Huế                                                      | | [Sắp xếp: ...]v| |
| +-----------------------------------------------------------------------------+ +---------------+ |
|                                                                                                   |
|                                   +-------------------------+                                     |
|                                   |        [ 🔍 ✕ ]         |                                     |
|                                   |  Không tìm thấy kết quả |                                     |
|                                   +-------------------------+                                     |
|                                                                                                   |
|                         Không có di sản nào khớp với từ khóa "Tháp Chăm Cổ Đại Huế".              |
|                     Hệ thống chỉ lưu trữ và hiển thị các di tích và làng nghề đã qua              |
|                                  khảo chứng thư tịch lịch sử chính thức.                          |
|                                                                                                   |
|                          Gợi ý tìm kiếm:                                                          |
|                          • Thử tìm: "Ngọ Môn", "Lăng Tự Đức", "Đúc đồng", "Thiên Mụ"              |
|                          • Kiểm tra lại lỗi chính tả hoặc bỏ bớt các bộ lọc đang chọn             |
|                                                                                                   |
|                                     [ Xóa toàn bộ bộ lọc ]                                        |
+---------------------------------------------------------------------------------------------------+
```

### 7.3 Error State Wireframes

#### 7.3.1 Service / Network Error State (HTTP 500 / Offline)
```
+---------------------------------------------------------------------------------------------------+
|  [LN] LƯU NIÊN     Khám phá    Nghệ nhân    Trải nghiệm    Học tập    Về dự án    [Q Tìm kiếm (Ctrl+K)] [VI/EN] [Tài khoản] |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                                   +-------------------------+                                     |
|                                   |        [ ⚠️ ! ]         |                                     |
|                                   |   Không thể tải dữ liệu |                                     |
|                                   +-------------------------+                                     |
|                                                                                                   |
|                                Mã lỗi: ERR_HERITAGE_FETCH_FAILED (HTTP 500)                       |
|                          Máy chủ khảo cứu tạm thời không thể xử lý truy vấn.                      |
|                  Hệ thống bảo vệ fail-closed không hiển thị dữ liệu chưa được xác thực.           |
|                                                                                                   |
|                                [ Thử tải lại trang ]   [ Về trang chủ ]                           |
|                                                                                                   |
|                    Nếu sự cố vẫn tiếp diễn, vui lòng liên hệ: contact@histolab.icu                |
+---------------------------------------------------------------------------------------------------+
```

#### 7.3.2 3D Viewer Fallback (WebGL Not Supported / Iframe Blocked)
```
+-------------------------------------------------------------------+
| [!] Không thể hiển thị mô hình 3D tương tác                      |
|                                                                   |
| Trình duyệt của bạn không hỗ trợ WebGL hoặc kết nối đến Sketchfab |
| đã bị chặn bởi tiện ích bảo vệ quyền riêng tư.                    |
|                                                                   |
| Phương án thay thế:                                               |
| • Xem ảnh chụp tư liệu độ phân giải cao tại Tab "Ảnh chụp 2D"     |
| • Hoặc mở mô hình trực tiếp trên Sketchfab:                       |
|   [ Mở mô hình "Tomb of Tu Duc" trên Sketchfab ↗ (matousekfoto) ] |
+-------------------------------------------------------------------+
```

---

## 8. Technical Contract Alignment & Frontend Implementation Roadmap

### 8.1 TypeScript Contract Alignment
All wireframe entities directly bind to the TypeScript definitions created in `frontend/src/types/heritage.ts`:

```typescript
// Mapping wireframe elements to contracts:
HeritagePlace           -> Explore catalogue cards, Search hits, Map markers
HeritagePlaceDetail     -> Place detail page `/heritage/[slug]`
HeritageCategory        -> Facet filter pills and category badges
HeritageEntityType      -> Structural taxonomy chips (site, monument, building...)
EditorialStatus         -> Publication lifecycle indicators
HeritageRelation        -> Parent/child structural graph and living culture bridges
HeritageSourceEvidence  -> Source citation cards with volume & page numbers
HeritageMediaAsset      -> 2D photo gallery and Sketchfab 3D embed containers
LicensingStatus         -> Epistemic decision gate & attribution disclosures
HeritageSearchFilters   -> Query params for catalogue search, filters, and cursor
```

### 8.2 Frontend Component File Inventory (Phase 2 Roadmap)
To be built in Phase 2 in strict accordance with this specification:

1. `frontend/src/components/shell/GlobalHeader.tsx` (Refactor to single 5-link model)
2. `frontend/src/components/shell/MobileDrawer.tsx` (Consolidate into single accessible sheet)
3. `frontend/src/app/explore/page.tsx` (Full rewrite to Huế-wide catalogue)
4. `frontend/src/components/explore/HeritageCard.tsx` (Summary card with badges)
5. `frontend/src/components/explore/HeritageFilters.tsx` (Facet pills & advanced drawer)
6. `frontend/src/components/explore/HeritageMap.tsx` (Leaflet map with category pins)
7. `frontend/src/app/heritage/[slug]/page.tsx` (Deep place detail layout)
8. `frontend/src/components/heritage/HeritageMediaTabs.tsx` (Photo/3D/Archival tabs)
9. `frontend/src/components/heritage/SketchfabExhibit.tsx` (Lazy-loaded safe iframe)
10. `frontend/src/components/heritage/SourceEvidenceRail.tsx` (Citation cards)
11. `frontend/src/components/heritage/LivingBridgeCard.tsx` (Maker & experience CTA)
12. `frontend/src/components/heritage/CulturalBridgeAIPanel.tsx` (Scoped RAG chat)

---

**End of Specification.**  
*Signed off by AGENT 06 (Frontend Explore Engineer) — Ready for Phase 2 Component Implementation.*
