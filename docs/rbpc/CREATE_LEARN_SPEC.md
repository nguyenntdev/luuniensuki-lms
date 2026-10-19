# LƯU NIÊN — The Living Heritage Platform
## RBPC 2026: CREATE, LEARN & COMMERCIAL INQUIRY SPECIFICATION
### Comprehensive Wireframes, Component Architecture, TypeScript Contracts & Inquiry State Machine

**Document ID:** `DOC-RBPC-SPEC-007`  
**Version:** 1.0.0 Final  
**Date:** 18 October 2026  
**Status:** APPROVED / READY FOR IMPLEMENTATION (Phase 1)  
**Controlling Specification:** Master Execution Goal V2 (§4.2, §4.4, §5.3, §5.4, §V2-A, §V2-F)  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687`  
**Branch:** `feat/rbpc-cultural-bridge-2026`  
**Target Content Scope:** `RBPC_HUE`  
**Author:** AGENT 07 — Frontend Create & Learn Engineer  
**Supervision:** Student Founders (S1 Integrator, S2 Engineering Lead, S4 Creative Lead)  

---

## 1. Executive Summary & Architecture Foundation

The **LƯU NIÊN** platform (competing under the RMIT Business Plan Competition 2026 theme *"AI and Humanity: Building What's Next"*) serves as a source-grounded cultural bridge connecting imperial historical discoveries with living traditional craft practitioners in Thừa Thiên Huế.

While the *Explore* branch focuses on authoritative, source-grounded historical narratives and 3D artifacts, the **Create** and **Learn** branches represent the commercial and educational core of the venture:
1. **Create Branch (Commercial MVP Slice):** Enables culturally curious visitors to discover consenting master artisans (`/people/[slug]`), review authentic craft experiences (`/experiences/[slug]`), and initiate an honest, transparent availability inquiry (`/rbpc/inquiries`).
2. **Inquiry State Machine & Partner Inbox:** Provides craft workshops with a secure, auth-gated management portal (`/rbpc/partner`) to review inquiries, execute state transitions (`new` $\rightarrow$ `contacted` $\rightarrow$ `confirmed` | `declined` $\rightarrow$ `closed`), and maintain guest communications without predatory instant-booking automation or commission-gouging.
3. **Learn Pathway (`/learn`):** Constructs a modest, connected educational bridge linking 1835 imperial bronze metallurgical history (the Nine Dynastic Urns / *Cửu Đỉnh*) with modern living traditions, mapping existing repository learning capabilities to a three-year accredited curriculum roadmap.

### 1.1 Core Principles of the Create & Learn Interfaces
- **Epistemic Honesty:** The platform strictly enforces transparency. An inquiry is an *availability request*, never an instant confirmed booking. Pricing displays are indicative and agreed upon with practitioners.
- **Dignity & Informed Consent:** Artisans are presented as master practitioners, not tourist spectacles. Every profile displays an audited consent verification badge and acknowledges oral history recordings. If consent is revoked, public interfaces immediately fail closed.
- **Privacy by Design:** Public status endpoints return zero Personally Identifiable Information (PII). Inquiries are tracked via high-entropy opaque tokens and non-sequential reference codes (e.g. `INQ-7F89-A23C`).
- **Idempotency & Double-Submit Protection:** Every inquiry form generates a client UUID v4 idempotency key upon component mounting, preventing duplicate notifications or database spam on erratic mobile connections.

---

## 2. Design System Tokens & Layout Framework

All Create, Learn, and Partner interfaces strictly adhere to the Hue-inspired contemporary editorial visual token system defined in Master Spec §4.3 and implemented in `frontend/src/styles/rbpc.css`.

### 2.1 CSS Custom Properties & Color Semantics
```css
:root {
  /* Surface & Background */
  --rbpc-bg: #F7F4EE;            /* Warm unbleached paper background */
  --rbpc-surface: #FFFCF7;       /* Card and modal elevated paper surface */
  --rbpc-surface-subtle: #EFECE4;/* Muted background for metadata chips */
  
  /* Ink & Typography */
  --rbpc-ink: #242C2B;           /* Deep slate ink for high-contrast text */
  --rbpc-ink-muted: #66706B;     /* Secondary metadata, captions, timestamps */
  --rbpc-ink-subtle: #8A948F;    /* Disabled states, placeholders */
  
  /* Brand Accents */
  --rbpc-primary: #325B52;       /* Imperial Huế deep pine green (Primary CTA) */
  --rbpc-primary-hover: #25453E; /* Darkened pine green on hover/focus */
  --rbpc-highlight: #A66A45;     /* Warm terracotta/copper artisan accent */
  --rbpc-highlight-soft: #F4ECE6;/* Light terracotta tint for badge surfaces */
  
  /* Borders & Dividers */
  --rbpc-divider: #D8D7CE;       /* Understated 1px borders */
  --rbpc-focus: #1E675A;         /* High-contrast WCAG 2.2 AA focus outline */
  
  /* Semantic Status Indicators */
  --rbpc-status-new: #2B6CB0;       /* Blue for new incoming inquiries */
  --rbpc-status-contacted: #C05621; /* Ochre for partner follow-up */
  --rbpc-status-confirmed: #22543D; /* Forest green for confirmed experiences */
  --rbpc-status-declined: #742A2A;  /* Deep burgundy for declined requests */
  --rbpc-status-closed: #4A5568;    /* Muted charcoal for archived/closed */
  --rbpc-error: #A33A35;            /* Form field validation error red */
}
```

### 2.2 Responsive Grid Architecture
- **Desktop (1440px viewport):** 12-column grid, 80px column width, 24px gutters, max-width `1180px`, section vertical rhythm `80px` / `104px`.
- **Tablet (768px viewport):** 8-column grid, 16px gutters, max-width `720px`, section vertical rhythm `64px`.
- **Mobile (360px–390px viewport):** 4-column grid, 12px gutters, 100% fluid with 16px screen margins, section vertical rhythm `40px` / `56px`. All touch targets $\ge 44 \times 44$ CSS px.

---

## 3. Creator Profile Specification (`/people/[slug]`)

### 3.1 Overview & Functional Objectives
The Creator Profile presents a documentary-grade biography of a living cultural master (e.g., Master Bronze Caster of Phường Đúc, Thanh Tiên Paper Flower Master, or Traditional Imperial Lacquerer). It establishes historical lineage, displays audited consent, allows playback of oral history audio, and routes users to authentic workshops.

### 3.2 Desktop Wireframe (1440px Viewport — 12-Column Grid)

```text
+--------------------------------------------------------------------------------------------------+
| [HEADER] LƯU NIÊN   Khám phá (Discover)  Nghệ nhân (Makers)  Trải nghiệm (Experiences)  [EN | VI]|
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  BREADCRUMB: Trang chủ / Nghệ nhân / Nghệ nhân Nguyễn Văn Cửu (Phường Đúc)                       |
|                                                                                                  |
|  +-------------------------------------------+  +---------------------------------------------+  |
|  | [PORTRAIT HERO (1:1 / 4:5 Aspect Ratio)]  |  | [CREATOR BIOGRAPHY & VERIFICATION]          |  |
|  |                                           |  |                                             |  |
|  |  [High-Resolution Documentary Photo]      |  |  CRAFTSMANSHIP LINEAGE                      |  |
|  |  Captured at Phường Đúc foundry, Huế     |  |  Đúc đồng truyền thống Huế • Đời thứ 5       |  |
|  |                                           |  |                                             |  |
|  |  (Photo: Lưu Niên Archive / Nguyễn Đức)   |  |  <h1>Nghệ nhân Nguyễn Văn Cửu</h1>          |  |
|  |                                           |  |                                             |  |
|  |  +-------------------------------------+  |  |  [VERIFICATION BADGE]                       |  |
|  |  | [x] Giấy xác nhận đồng thuận ký tay  |  |  |  (i) Đã xác minh văn bản đồng thuận 2026    |  |
|  |  |     Mã lưu trữ: CONSENT-PD-001      |  |  |      Hồ sơ cấp quyền lưu trữ số 08/2026/LN   |  |
|  |  +-------------------------------------+  |  |                                             |  |
|  |                                           |  |  "Hơn 45 năm gắn bó với lò than đỏ lửa,     |  |
|  |  Năm sinh: 1958 • Thâm niên: 48 năm nghề  |  |   tiếng búa gõ lên khuôn đất sét là hồn     |  |
|  |  Địa bàn: Phường Đúc, TP. Huế             |  |   cốt đời người Phường Đúc..."              |  |
|  +-------------------------------------------+  |                                             |  |
|                                                 |  [APPROVED BIOGRAPHICAL SUMMARY]            |  |
|                                                 |  Kế thừa kỹ nghệ rót đồng và pha hợp kim    |  |
|                                                 |  từ các hiệp thợ cung đình thời Tự Đức...   |  |
|                                                 +---------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | [ORAL HISTORY RECORDING & TRANSCRIPT PLAYER]                                               |  |
|  |                                                                                            |  |
|  |  [Play Button]  03:42 / 18:20  ══════════════●════════════════════════════  [Volume] [Transcript]
|  |  Ghi âm tại tư gia: "Ký ức tiếng chuông đồng chùa Thiên Mụ và bí quyết khuôn đất sông Hương" |  |
|  |                                                                                            |  |
|  |  +-- [TRANSCRIPT ACCORDION: EXPANDED] ---------------------------------------------------+ |  |
|  |  | [00:15] Người phỏng vấn: Thưa chú, bí quyết giữ âm thanh ngân vang của đồng Huế nằm ở đâu?| |  |
|  |  | [00:42] Nghệ nhân: Đất làm khuôn phải lấy từ bãi bồi ven sông Hương lúc cạn nước,      | |  |
|  |  |        nhào với trấu đốt thành than non để giữ độ xốp khi rót đồng sôi nghìn độ...     | |  |
|  |  +---------------------------------------------------------------------------------------+ |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | [LINKED EXPERIENCES HOSTED BY THIS MASTER ARTISAN]                                         |  |
|  |                                                                                            |  |
|  |  +----------------------------------------+  +------------------------------------------+  |  |
|  |  | [EXPERIENCE CARD 1]                    |  | [EXPERIENCE CARD 2]                      |  |  |
|  |  | Image: Cầm vồ gõ chuông thử tiếng đồng |  | Image: Tạo mẫu khuôn đất sáp ong         |  |  |
|  |  |                                        |  |                                          |  |  |
|  |  | Kỹ nghệ thẩm âm & Rót đồng truyền thống|  | Đúc tượng nhỏ & Chạm khắc hoa văn Huế     |  |  |
|  |  | Thời lượng: 150 phút • Phường Đúc      |  | Thời lượng: 120 phút • Phường Đúc        |  |  |
|  |  | Giá chỉ dẫn: Từ 450.000 VNĐ / khách    |  | Giá chỉ dẫn: Từ 350.000 VNĐ / khách      |  |  |
|  |  |                                        |  |                                          |  |  |
|  |  | [CTA: Gửi yêu cầu lịch trải nghiệm ->] |  | [CTA: Gửi yêu cầu lịch trải nghiệm ->]   |  |  |
|  |  +----------------------------------------+  +------------------------------------------+  |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | [RIGHTS & CITATION FOOTER]                                                                 |  |
|  | Hồ sơ được bảo vệ bản quyền nhân thân theo Luật Sở hữu trí tuệ Việt Nam. Mọi nội dung chia   |  |
|  | sẻ đã được nghệ nhân Nguyễn Văn Cửu phê duyệt ngày 12/08/2026. [Xem chính sách bản quyền]  |  |
|  +--------------------------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------------------------+
```

### 3.3 Mobile Wireframe (390px Viewport — 4-Column Layout)

```text
+---------------------------------------+
| [=] LƯU NIÊN                   [VI|EN]|
+---------------------------------------+
| < Quay lại danh sách nghệ nhân        |
|                                       |
| +-----------------------------------+ |
| | [PORTRAIT: 1:1 Aspect]            | |
| |                                   | |
| |  Doc Photo of Artisan Cửu         | |
| |                                   | |
| +-----------------------------------+ |
|                                       |
| Đúc đồng truyền thống • Đời thứ 5     |
| <h1>Nghệ nhân Nguyễn Văn Cửu</h1>     |
|                                       |
| [✓] Đã xác minh văn bản đồng thuận    |
| Phường Đúc, TP. Huế • 48 năm nghề     |
|                                       |
| "Hơn 45 năm gắn bó với lò than đỏ     |
| lửa, tiếng búa gõ lên khuôn đất sét   |
| là hồn cốt đời người Phường Đúc..."   |
|                                       |
| +-----------------------------------+ |
| | [AUDIO PLAYER]                    | |
| | [>] 03:42 / 18:20 ═════●═════════ | |
| | Ghi âm: Ký ức chuông chùa Thiên Mụ| |
| | [v] Xem trích đoạn ghi âm         | |
| +-----------------------------------+ |
|                                       |
| TRẢI NGHIỆM GẮN LIỀN (2)              |
|                                       |
| +-----------------------------------+ |
| | [CARD] Kỹ nghệ thẩm âm & Rót đồng | |
| | 150 phút • Phường Đúc, Huế        | |
| | Giá chỉ dẫn: Từ 450.000 VNĐ       | |
| | [Gửi yêu cầu lịch ->]             | |
| +-----------------------------------+ |
|                                       |
| +-----------------------------------+ |
| | [CARD] Đúc tượng & Chạm hoa văn   | |
| | 120 phút • Phường Đúc, Huế        | |
| | Giá chỉ dẫn: Từ 350.000 VNĐ       | |
| | [Gửi yêu cầu lịch ->]             | |
| +-----------------------------------+ |
|                                       |
| [i] Nội dung đã được nghệ nhân ký     |
| biên bản đồng thuận ngày 12/08/2026.  |
+---------------------------------------+
```

### 3.4 Interactive States & Component Hierarchy
1. **Documentary Portrait (`approved_portrait_url`):** Renders with `altText` in Vietnamese and English, high-resolution WebP format with graceful blur-up placeholder.
2. **Verification Badge (`VerificationBadge`):** Green pill badge (`#22543D` text on `#F4ECE6` surface). Tooltip disclosure explains verification date, document reference number, and legal basis.
3. **Oral History Recording Player (`OralHistoryRecording`):** Native HTML5 `<audio>` wrapper with custom accessible controls, visual scrubber, and an accessible `<details>` transcript accordion with timestamp anchors.
4. **Fail-Closed Fallback (Consent Revoked):** If `consent_status === "revoked"`, the route immediately renders a culturally respectful notice: *"Hồ sơ này tạm thời đóng theo yêu cầu bảo vệ quyền riêng tư của nghệ nhân"* and withholds all personal contact information, portrait photographs, and audio recordings.

---

## 4. Experience Listing Specification (`/experiences/[slug]`)

### 4.1 Overview & Transparency Mandate
The Experience Listing showcases an authentic, real-world cultural workshop or masterclass. In strict adherence to ADR 06, this interface **NEVER** displays fake immediate checkout buttons (`"Book Now"`, `"Pay 500,000 VND"`). The primary CTA is explicitly branded: **`Gửi yêu cầu lịch trống (Request availability)`**.

### 4.2 Desktop Wireframe (1440px Viewport — 12-Column Grid with Sticky Inquiry Rail)

```text
+--------------------------------------------------------------------------------------------------+
| [HEADER] LƯU NIÊN   Khám phá  Nghệ nhân  Trải nghiệm  Tìm hiểu  Tác động                 [VI | EN]|
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  BREADCRUMB: Trang chủ / Trải nghiệm / Kỹ nghệ thẩm âm & Rót đồng truyền thống                   |
|                                                                                                  |
|  +---------------------------------------------------+  +-------------------------------------+  |
|  | [LEFT CONTENT COLUMN - 8 COLUMNS]                 |  | [STICKY INQUIRY RAIL - 4 COLUMNS]   |  |
|  |                                                   |  |                                     |  |
|  |  CRAFT MASTERCLASS • HUẾ METALLURGY               |  |  +-------------------------------+  |  |
|  |  <h1>Kỹ nghệ thẩm âm & Rót đồng truyền thống</h1> |  |  | [INQUIRY SUMMARY CARD]         |  |  |
|  |  Host: Nghệ nhân Nguyễn Văn Cửu (Phường Đúc)      |  |  |                               |  |  |
|  |                                                   |  |  | GIÁ CHỈ DẪN (INDICATIVE PRICE)|  |  |
|  |  [HERO IMAGE: Workshop foundry scene]             |  |  | <span class="price">          |  |  |
|  |                                                   |  |  |   Từ 450.000 VNĐ / khách       |  |  |
|  |  +---------------------------------------------+  |  |  | </span>                       |  |  |
|  |  | [METADATA CHIP BAR]                         |  |  |  | Nhóm tối đa: 8 khách          |  |  |
|  |  | (o) 150 phút   [x] Tối đa 8 người   [v] Tiếng|  |  |  | Thời lượng: 2.5 giờ           |  |  |
|  |  |     Việt & Hỗ trợ tiếng Anh                 |  |  |  | Địa điểm: Phường Đúc, TP. Huế |  |  |
|  |  +---------------------------------------------+  |  |  |                               |  |  |
|  |                                                   |  |  | [TRANSPARENCY NOTICE]         |  |  |
|  |  TỔNG QUAN TRẢI NGHIỆM                            |  |  | (i) Đây là bước liên hệ xác    |  |  |
|  |  Bước vào xưởng đúc đồng có lịch sử hơn 150 năm...|  |  |     nhận lịch rảnh với nghệ    |  |  |
|  |                                                   |  |  |     nhân. KHÔNG thu phí thẻ tức|  |  |
|  |  GIÁO TRÌNH XƯỞNG THỰC HÀNH (WORKSHOP SYLLABUS)   |  |  |     thì trên trang web.        |  |  |
|  |                                                   |  |  |                               |  |  |
|  |  [1] 00:00 - 00:30 • Chuyện đất & Chuyện lò than   |  |  | [PRIMARY CTA BUTTON]          |  |  |
|  |      Tìm hiểu kỹ thuật chọn đất sét sông Hương... |  |  | [ Gửi yêu cầu lịch trống ]    |  |  |
|  |                                                   |  |  |                               |  |  |
|  |  [2] 00:30 - 01:15 • Bí quyết nghe tiếng đồng chín|  |  | [GUARANTEE BADGE]             |  |  |
|  |      Thực hành gõ búa thử âm thanh phôi đồng...   |  |  | [✓] Nghệ nhân nhận 100% học phí|  |  |
|  |                                                   |  |  |     trực tiếp tại xưởng.       |  |  |
|  |  [3] 01:15 - 02:30 • Chạm hoa văn & Đúc chuông nhỏ|  |  |                               |  |  |
|  |      Tự tay hoàn thiện chiếc chuông gió bằng đồng |  |  | [v] Hỏi trợ lý AI về kỹ nghệ  |  |  |
|  |                                                   |  |  +-------------------------------+  |  |
|  |  ĐỊA ĐIỂM & ĐƯỜNG ĐI                              |  |                                     |  |
|  |  Xưởng đúc Cửu Long, Kiệt 123 Bùi Thị Xuân, Huế...|  |                                     |  |
|  |                                                   |  |                                     |  |
|  |  LƯU Ý AN TOÀN & TRANG PHỤC                       |  |                                     |  |
|  |  • Trang phục cotton dài tay, đi giày kín mũi.    |  |                                     |  |
|  |  • Trẻ em dưới 12 tuổi cần người lớn kèm cặp.     |  |                                     |  |
|  +---------------------------------------------------+  +-------------------------------------+  |
+--------------------------------------------------------------------------------------------------+
```

### 4.3 Mobile Wireframe (390px Viewport — Sticky Bottom Action Bar)

```text
+---------------------------------------+
| [<] Chi tiết trải nghiệm       [VI|EN]|
+---------------------------------------+
| [HERO IMAGE: Workshop scene]          |
|                                       |
| ĐÚC ĐỒNG PHƯỜNG ĐÚC                   |
| <h2>Kỹ nghệ thẩm âm & Rót đồng</h2>   |
| Host: Nghệ nhân Nguyễn Văn Cửu        |
|                                       |
| [150 phút] [Tối đa 8 khách] [Huế]     |
|                                       |
| GIÁ CHỈ DẪN                           |
| Từ 450.000 VNĐ / khách                |
|                                       |
| [!] Minh bạch: Không thanh toán tức   |
| thì. Nghệ nhân sẽ phản hồi lịch rảnh. |
|                                       |
| NỘI DUNG BUỔI HỌC (3 PHẦN)            |
|                                       |
| [1] Chuyện đất sét & than củi (30p)   |
| [2] Kỹ nghệ thẩm âm phôi đồng (45p)   |
| [3] Tự tay chạm chuông gió nhỏ (75p)  |
|                                       |
| LƯU Ý AN TOÀN                         |
| Đi giày kín mũi, trang phục cotton.   |
|                                       |
| +-----------------------------------+ |
| | [STICKY BOTTOM ACTION BAR (44px)] | |
| | Từ 450.000 VNĐ                      | |
| | [ Gửi yêu cầu lịch trống -> ]     | |
| +-----------------------------------+ |
+---------------------------------------+
```

---

## 5. Inquiry Form Wireframe & State Machine Flow (`/rbpc/inquiries`)

### 5.1 Minimalist Fields & Privacy Guarantees
To maximize conversion, respect user privacy, and avoid unnecessary data retention:
1. **Name:** Visitor public name or moniker (2–100 chars).
2. **Contact Channel (Segmented Control):** `Email` | `Điện thoại (Phone)` | `Zalo`.
3. **Contact Value:** Validated RFC 5322 email or Vietnamese/international 8–15 digit phone.
4. **Preferred Date (Optional):** Native date picker constrained to `date >= today()`.
5. **Party Size:** Stepper input bounded between 1 and 10 (or provider limit).
6. **Message (Optional):** Plain text notes, special requests (max 2000 chars, sanitized).
7. **Explicit Consent Checkbox:** **Unchecked by default**. User must explicitly tick:
   *"Tôi đồng ý chia sẻ thông tin liên lạc này với [Tên nghệ nhân/nhà cung cấp] để trao đổi xác nhận lịch trải nghiệm."*
8. **Client-Generated Idempotency Key:** Automatically generated via `crypto.randomUUID()` when the form initializes. If user double-clicks or re-submits within 60s, backend returns the original reference without duplicate record creation.

### 5.2 Modal & Form Wireframe

```text
+--------------------------------------------------------------------------------------------------+
|  [X Đóng]                                                                                        |
|  <h2>Gửi yêu cầu lịch trải nghiệm</h2>                                                           |
|  <p class="subtitle">Trải nghiệm: Kỹ nghệ thẩm âm & Rót đồng truyền thống (Nghệ nhân Cửu)</p>   |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | Họ và tên của bạn (*)                                                                      |  |
|  | [ Nguyễn An Nhiên                                                                        ] |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  Phương thức liên hệ ưu tiên (*)                                                                 |
|  ( ) Email          (*) Số điện thoại / Zalo          ( ) WhatsApp                               |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | Số điện thoại / Zalo (*)                                                                   |  |
|  | [ 0912 345 678                                                                           ] |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +------------------------------------------+  +----------------------------------------------+  |
|  | Ngày dự kiến (Không bắt buộc)            |  | Số lượng khách (*)                           |  |
|  | [ 2026-11-05                 [Lịch v] ]  |  | [ - ]   2 người   [ + ]  (Tối đa: 8 khách)   |  |
|  +------------------------------------------+  +----------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | Lời nhắn gửi nghệ nhân (Yêu cầu khung giờ, ngoại ngữ hỗ trợ, v.v.)                         |  |
|  | [ Chúng tôi là 2 bạn trẻ muốn tìm hiểu kỹ nghệ đúc chuông để nghiên cứu văn hóa Huế...   ] |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | [ ] (*) Tôi đồng ý chia sẻ thông tin này với Xưởng đúc Cửu Long để phối hợp lịch trống.   |  |
|  |         Thông tin được lưu trữ tạm thời và bảo vệ theo Chính sách riêng tư Lưu Niên.       |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  [ HỦY BỎ ]                                          [ GỬI YÊU CẦU XÁC NHẬN (SUBMIT) -> ]        |
+--------------------------------------------------------------------------------------------------+
```

### 5.3 Request Acknowledgment Screen Wireframe (`/request/[requestId]`)

```text
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  [✓ CHECKMARK ICON - EMERALD 500]                                                                |
|  <h1>Yêu cầu trải nghiệm đã được gửi thành công!</h1>                                            |
|  <p>Mã tham chiếu hồ sơ của bạn: <strong class="badge">INQ-7F89-A23C</strong></p>               |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | [LƯU Ý QUAN TRỌNG VỀ TÍNH KHẢ DỤNG]                                                        |  |
|  | Đây là bước yêu cầu lịch rảnh, CHƯA PHẢI xác nhận đặt chỗ cuối cùng.                       |  |
|  | Xưởng đúc Cửu Long sẽ liên hệ với bạn qua Số điện thoại / Zalo trong vòng 24 giờ.         |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | TÓM TẮT THÔNG TIN YÊU CẦU                                                                  |  |
|  | • Trải nghiệm: Kỹ nghệ thẩm âm & Rót đồng truyền thống                                      |  |
|  | • Nghệ nhân chủ trì: Nghệ nhân Nguyễn Văn Cửu                                             |  |
|  | • Ngày dự kiến: 05/11/2026                                                                 |  |
|  | • Số khách: 2 người                                                                        |  |
|  | • Trạng thái hiện tại: [ Mới tiếp nhận (New) ]                                             |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  [ Tra cứu tiến độ yêu cầu ]                         [ Quay lại câu chuyện di sản ]              |
+--------------------------------------------------------------------------------------------------+
```

### 5.4 Inquiry Lifecycle State Machine

```
      Visitor Submits Form
               │
               ▼
        ┌─────────────┐
        │     NEW     │ ── (Created in DB, idempotency verified, provider notified)
        └─────────────┘
               │
      Partner opens & contacts
      guest via Phone/Zalo/Email
               │
               ▼
        ┌─────────────┐
        │  CONTACTED  │ ── (Partner actively coordinating dates/fees with guest)
        └─────────────┘
          │         │
Guest & Partner    Partner or Guest
agree on slot      cannot accommodate
          │         │
          ▼         ▼
    ┌───────────┐ ┌───────────┐
    │ CONFIRMED │ │ DECLINED  │ ── (Reason logged: schedule conflict, overcapacity)
    └───────────┘ └───────────┘
          │         │
Workshop completed  Record archived
or slot passed      after 30 days
          │         │
          ▼         ▼
        ┌─────────────┐
        │   CLOSED    │ ── (Terminal retention state; PII purged per policy)
        └─────────────┘
```

#### State Transition Rules Table
| Current State | Permitted Target State | Triggering Actor | Invariant / Security Rule |
|---|---|---|---|
| *(none)* | `new` | Anonymous Visitor | Requires valid `idempotency_key`, `accepted === true`, future date. |
| `new` | `contacted` | Workshop Partner / Admin | Updates `last_contacted_at`, partner must own the experience. |
| `new` | `declined` | Workshop Partner / Admin | Requires cancellation reason note. |
| `contacted` | `confirmed` | Workshop Partner / Admin | Requires partner confirmation note; triggers confirmation alert. |
| `contacted` | `declined` | Workshop Partner / Admin | Rejection reason recorded; guest notified. |
| `confirmed` | `closed` | Workshop Partner / System | Automatically transitions after workshop date passes. |
| `declined` | `closed` | System Auto-archiver | Archived 30 days post-creation. |

---

## 6. Partner Inbox Specification (`/rbpc/partner`)

### 6.1 Authentication & Provider Scoping Invariant
1. **Access Gate:** Restricted to authenticated users with `role: "partner"` or `role: "admin"`. Guest tokens receive `HTTP 401 Unauthorized` or redirect to `/login`.
2. **Strict Server-Side Isolation:** The query `GET /api/v1/rbpc/partner/inquiries` enforces `WHERE provider_id = current_user.provider_id`. A partner can never see, filter, or infer inquiries belonging to another craft workshop.
3. **Audit Trail:** Every state change logs timestamp, actor UUID, previous state, and new state.

### 6.2 Desktop Wireframe (1440px Viewport — Management Inbox Table & Action Drawer)

```text
+--------------------------------------------------------------------------------------------------+
| [PARTNER CONSOLE] LƯU NIÊN   Hộp thư đối tác: Xưởng đúc Cửu Long (Phường Đúc)     [Tài khoản v] |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  BỘ LỌC TRẠNG THÁI:                                                                              |
|  [ Tất cả (14) ]  [ Mới tiếp nhận (3) ]*  [ Đang liên hệ (5) ]  [ Đã xác nhận (4) ]  [ Đã hủy (2)]|
|                                                                                                  |
|  +-------------------------------------------------------------------+  +---------------------+  |
|  | [DANH SÁCH YÊU CẦU (INQUIRY TABLE)]                               |  | [CHI TIẾT & XỬ LÝ]  |  |
|  |                                                                   |  |                     |  |
|  | Mã hồ sơ   Khách hàng     Liên hệ       Ngày hẹn    Số khách  Status|  | Mã: INQ-7F89-A23C   |  |
|  | ───────────────────────────────────────────────────────────────── |  |                     |  |
|  | INQ-7F89   Nguyễn An Nhiên 0912345678    05/11/2026  2         NEW  |  | Khách: An Nhiên     |  |
|  | INQ-6E21   David Miller    d.m@gmail.com 02/11/2026  4   CONTACTED |  | Zalo: 0912345678    |  |
|  | INQ-5B10   Trần Bảo Ngọc   0988112233    28/10/2026  1   CONFIRMED |  | Trải nghiệm:        |  |
|  | INQ-4A02   Jean Dupont     j.d@laposte.fr 24/10/2026 2    DECLINED |  | Kỹ nghệ thẩm âm     |  |
|  |                                                                   |  | Ngày: 05/11/2026    |  |
|  | [<< Trang 1 / 3 >>]                                               |  |                     |  |
|  |                                                                   |  | Lời nhắn:           |  |
|  |                                                                   |  | "Chúng tôi là 2 bạn |  |
|  |                                                                   |  | trẻ muốn tìm hiểu..."
|  |                                                                   |  |                     |  |
|  |                                                                   |  | GHI CHÚ NỘI BỘ:     |  |
|  |                                                                   |  | [ Đã gọi lần 1 lúc  |  |
|  |                                                                   |  |   14:20 chưa nghe...|  |
|  |                                                                   |  |                     |  |
|  |                                                                   |  | CHUYỂN TRẠNG THÁI:  |  |
|  |                                                                   |  | [ Đã liên hệ ]      |  |
|  |                                                                   |  | [ Xác nhận lịch ]   |  |
|  |                                                                   |  | [ Từ chối yêu cầu ] |  |
|  +-------------------------------------------------------------------+  +---------------------+  |
+--------------------------------------------------------------------------------------------------+
```

---

## 7. Learn Pathway Specification (`/learn`)

### 7.1 Educational Philosophy & Continuity Bridge
The Learn Pathway connects the 1835 imperial bronze legacy of the Nine Dynastic Urns (*Cửu Đỉnh*) with living craft practitioners and the future accredited curriculum roadmap. It serves as concrete proof of technical capability without bloating the commercial MVP.

```
+─────────────────────────────────────────────────────────────────────────────+
|                          LƯU NIÊN LEARN PATHWAY                             |
+─────────────────────────────────────────────────────────────────────────────+
|                                                                             |
|   PHASE 1: FOUNDATION           PHASE 2: 3D ARTEFACT       PHASE 3: LIVING  |
|   Source-Grounded History       Interactive Metallurgy     Masterclass &    |
|   (Khâm Định Hội Điển...)        (162 Relief Digital Twin)  Workshop Action |
|                                                                             |
|   ┌─────────────────────┐       ┌──────────────────────┐  ┌───────────────┐ |
|   │ 1. Ký ức đồng thau  │       │ 2. Giải mã Cửu Đỉnh  │  │ 3. Nhập môn   │ |
|   │    Huế thời Nguyễn  │ ────> │    & Bản đúc nổi     │─>│    thẩm âm    │ |
|   │ [Sách sử & Khảo cứu]│       │ [Mô hình 3D & Hotspot│  │    Phường Đúc │ |
|   └─────────────────────┘       └──────────────────────┘  └───────────────┘ |
|                                                                    │        |
|                                                                    ▼        |
|                                                           ┌───────────────┐ |
|                                                           │ 4. Lộ trình   │ |
|                                                           │    học tập    │ |
|                                                           │    chứng chỉ  │ |
|                                                           │  (2027-2028)  │ |
|                                                           └───────────────┘ |
+─────────────────────────────────────────────────────────────────────────────+
```

### 7.2 Desktop Wireframe (1440px Viewport — 12-Column Grid)

```text
+--------------------------------------------------------------------------------------------------+
| [HEADER] LƯU NIÊN   Khám phá  Nghệ nhân  Trải nghiệm  Lộ trình học tập (Learn)           [VI | EN]|
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  LỘ TRÌNH KẾT NỐI GIÁO DỤC DI SẢN (EDUCATIONAL PATHWAY)                                         |
|  <h1>Từ Ký ức Lịch sử Hoàng triều đến Đôi bàn tay Người thợ hôm nay</h1>                         |
|  <p class="summary">Khám phá chuỗi bài học tương tác kết hợp tư liệu lịch sử chính thống,       |
|     mô hình 3D giải phẫu bản đúc và trải nghiệm xưởng nghề thực tế.</p>                          |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | CHẶNG 1: NỀN TẢNG THƯ TỊCH HOÀNG GIA (PHASE 1 - HISTORICAL FOUNDATION)                     |  |
|  |                                                                                            |  |
|  |  +-------------------------------------+  +---------------------------------------------+  |  |
|  |  | [MODULE CARD 01]                    |  | [MODULE CARD 02]                            |  |  |
|  |  | Tư liệu: Khâm Định Đại Nam Hội Điển  |  | Địa bạ Phường Đúc & Lệnh lập Vụ Đúc (1835)   |  |  |
|  |  | 4 chương • 30 phút • 8 nguồn dẫn     |  | 3 chương • 20 phút • 5 nguồn dẫn            |  |  |
|  |  | [ Trạng thái: Có sẵn trong hệ thống]|  | [ Trạng thái: Có sẵn trong hệ thống ]      |  |  |
|  |  +-------------------------------------+  +---------------------------------------------+  |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | CHẶNG 2: TƯƠNG TÁC 3D & GIẢI MÃ BẢN ĐÚC NỔI (PHASE 2 - 3D DISCOVERY)                       |  |
|  |                                                                                            |  |
|  |  +-------------------------------------+  +---------------------------------------------+  |  |
|  |  | [MODULE CARD 03]                    |  | [MODULE CARD 04]                            |  |  |
|  |  | Khám phá 18 bản đúc Cao Đỉnh        |  | Kỹ thuật tạo khuôn đất sáp ong hoàng cung   |  |  |
|  |  | Tích hợp 3D WebGL / R3F Viewer      |  | Mô hình so sánh phôi đúc xưa và nay         |  |  |
|  |  | [ Khám phá chi tiết 3D -> ]         |  | [ Xem mô hình giải phẫu -> ]                |  |  |
|  |  +-------------------------------------+  +---------------------------------------------+  |  |
|  +--------------------------------------------------------------------------------------------+  |
|                                                                                                  |
|  +--------------------------------------------------------------------------------------------+  |
|  | CHẶNG 3: TRẢI NGHIỆM THỰC ĐỊA & NGHỆ NHÂN (PHASE 3 - MASTERCLASS)                          |  |
|  |                                                                                            |  |
|  |  +-------------------------------------+  +---------------------------------------------+  |  |
|  |  | [MODULE CARD 05]                    |  | [ROADMAP 2027-2028: CHỨNG CHỈ HỌC TẬP]      |  |  |
|  |  | Thực hành thẩm âm chuông Phường Đúc |  | Khung chứng chỉ số liên kết trường học      |  |  |
|  |  | Học trực tiếp cùng Nghệ nhân Cửu    |  | Dự kiến triển khai sau giai đoạn thử nghiệm |  |  |
|  |  | [ Đăng ký yêu cầu tham gia -> ]     |  | [ Xem đề án nghiên cứu giáo dục ]           |  |  |
|  |  +-------------------------------------+  +---------------------------------------------+  |  |
|  +--------------------------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------------------------+
```

---

## 8. TypeScript Contract Reference (`frontend/src/types/rbpc.ts`)

The frontend implementation is governed by the strictly typed contracts in `frontend/src/types/rbpc.ts`.

### 8.1 Key Type Signatures Summary
```typescript
// Core Inquiry Status
export type InquiryStatus = 'new' | 'contacted' | 'confirmed' | 'declined' | 'closed';

// Polymorphic Story Blocks
export type StoryBlock =
  | TextStoryBlock
  | ImageStoryBlock
  | QuoteStoryBlock
  | SourceExcerptStoryBlock
  | CulturalContextStoryBlock
  | Model3DStoryBlock
  | ArtisanBridgeStoryBlock   // Connects story to artisan
  | ComparisonStoryBlock
  | CalloutStoryBlock
  | ReflectionPromptStoryBlock
  | AudioRecordingStoryBlock
  | VideoClipStoryBlock;

// Artisan Profile
export interface RbpcCreator {
  id: string;
  slug: string;
  publicName: string;
  craftTradition: LocalizedField;
  approvedBio: LocalizedField;
  approvedPortraitUrl?: string;
  publicRegion: string;
  consentStatus: ConsentStatus;
  verificationBadge?: VerificationBadge;
  oralHistory?: OralHistoryRecording;
  approvedStorySlugs: string[];
  experienceSlugs: string[];
}

// Experience Offering
export interface RbpcExperience {
  id: string;
  slug: string;
  creatorSlug: string;
  title: LocalizedField;
  description: LocalizedField;
  syllabus: WorkshopSyllabusStep[];
  areaPublic: string;
  durationMinutes: number;
  pricing: PricingDisplay;
  availabilityMode: 'inquiry_only' | 'disabled';
  maxPartySize: number;
  notice: string;
}

// Inquiry Form Values
export interface InquiryFormValues {
  experienceSlug: string;
  name: string;
  contactMethod: 'email' | 'phone' | 'zalo';
  contactValue: string;
  preferredDate?: string;
  partySize: number;
  message?: string;
  consentAccepted: boolean;
  privacyAccepted: boolean;
  consentVersion: string;
  idempotencyKey: string;
}
```

---

## 9. Accessibility (WCAG 2.2 AA) & Error Acceptance Matrix

| Criterion | Requirement & Implementation | Gate |
|---|---|---|
| **Keyboard Trapping** | When Inquiry Modal opens, focus is trapped inside modal. `Esc` key cancels and restores focus to triggering CTA. | P0 |
| **Visible Focus Indicator** | All inputs, buttons, and radio toggles feature a 2px solid `--rbpc-focus` (`#1E675A`) outline with 2px offset. | P0 |
| **Contrast Ratio** | Body text meets $\ge 4.5:1$ against `--rbpc-bg` (`#F7F4EE`). Button labels meet $\ge 4.5:1$ against `--rbpc-primary`. | P0 |
| **Explicit Consent** | Checkbox is **never pre-checked**. Form submission with unchecked consent displays inline error: *"Vui lòng xác nhận đồng thuận chia sẻ thông tin."* | P0 |
| **Double-Submit Prevention** | Client UUID v4 idempotency key disables submit button upon first click and prevents duplicate POST calls. | P0 |
| **Screen Reader Announcement** | Form errors and successful submission status use `aria-live="polite"` containers. | P0 |
| **Reduced Motion** | Modal transitions respect `prefers-reduced-motion: reduce` by disabling sliding/zoom animations. | P0 |
| **Fail-Closed Privacy** | Revoked consent completely strips oral history audio and contact channels from the client bundle. | P0 |

---

## 10. Traceability & Ownership

- **Controlling Document:** `docs/rbpc/CREATE_LEARN_SPEC.md`
- **TypeScript Type Definitions:** `frontend/src/types/rbpc.ts`
- **Bilingual Copy Dictionary:** `frontend/src/lib/rbpc/copy.ts`
- **Backend API Schemas:** `backend/apischemas/rbpc.py`
- **Assigned Engineering Owner:** AGENT 07 (Phase 1 Frontend Create & Learn Engineer)
