# V5.9 — NEW_FEATURE_ROADMAP

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.9`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.9 — NEW FEATURES: TÍNH NĂNG CẠNH TRANH KHỞI NGHIỆP CÓ ƯU TIÊN

**Tính mới cần tạo ra giá trị thực** cho 3 nhóm: trường học, khách trải nghiệm, nghệ nhân/bảo tàng. Không biến LƯU NIÊN thành “superapp” không có PMF. Feature launch order = tiếp tục production fixes + thử nghiệm sản phẩm mới có metrics. Tất cả đề xuất là `[TARGET]`, KHÔNG đánh dấu đã tồn tại hoặc đã đo hiệu quả.

### 9.1. Ma trận Value × Feasibility × Evidence

| Feature | Người dùng | Khác biệt có thể kiểm chứng | Minimum shippable product | Dependency | Priority |
|---|---|---|---|---|---|
| **Verified Heritage Passport** | học sinh/khách | 9 urns × 162 objects journey với bằng chứng; không đánh tráo chứng nhận học thuật | QR trail, nguồn, check-in có consent, badge ghi `experience` không ghi `mastery` | published corpus, identity, QR integrity | S1 |
| **Evidence Coach / Historical Thinking Tutor** | trường | phản hồi theo claim–evidence–reasoning, không chỉ giải đáp | hint-first, link nguồn, teacher-review, rubric trace | evidence graph, lesson API | S1 |
| **Teacher Class Studio** | trường | giáo viên cấu hình bài học 2D/3D và nguồn; gradebook thật | class, assignment, student submission, rubric export | authentication, LMS backend | S1 |
| **Artisan Experience Inbox** | nghệ nhân | từ câu chuyện có nguồn đến inquiry thực, quyền chủ thể | consented listing, inquiry, scoped inbox, confirmation, support | marketplace integrity | S1 |
| **Offline Heritage Kit** | trường nghèo thiết bị | 2D/low-bandwidth continuity, a11y | licensed offline bundle, teacher projection, sync queue | media rights, data manifests | S1 |
| **Expert Review Workbench** | curator | sửa sử liệu có claim-by-claim source proof | compare excerpts, conflict view, reviewer signature, audit | source factory | S1 |
| **Museum/Site QR Trails** | bảo tàng/du khách | contextual learning at physical object | QR label -> verified object -> audio/2D -> source | rights, location permissions | S2 |
| **Multilingual Cultural Bridge** | khách quốc tế | VI/EN contextual storytelling grounded in scholarly sources | translate metadata only after review; bilingual consent & privacy | claim graph, translation QA | S2 |
| **Adaptive Quest Engine** | học sinh | chuyển từ XP trò chơi sang mastery có nguồn | FSRS + evidence tasks + achievement audit | real grade/progress | S2 |
| **Partner Inventory & Availability Calendar** | nghệ nhân | giảm double-booking/cold inquiry | staff-only slots, capacity, expiry/confirm | inquiry integrity | S2 |
| **Ethical Commerce & Settlement Ledger** | nghệ nhân/đơn vị vận hành | minh bạch phí và số tiền thực nhận | agreed fee, completion evidence, export monthly | legal/payment contracts | S2 |
| **School Evidence Dashboard** | trường/B2B | năng lực sử dụng chứng cứ theo rubric có version | class aggregates, consent, export, no unsupported causal claim | gradebook, privacy | S2 |
| **Story-to-Experience Recommendations** | khách | gợi ý lịch trải nghiệm có liên quan di sản, không gán nghệ nhân thành hiện vật | rule-based verified links, no fake personalization | real partner & object graph | S2 |
| **Community Oral History with Consent** | nghệ nhân/bảo tàng | di sản sống có chủ sở hữu câu chuyện | upload audio, transcript, permission, editorial review | rights, storage, removal | S3 |
| **Collaborative Source Debate** | lớp học | nhóm học sinh so sánh nguồn trái chiều | small groups, source evidence board, teacher evaluation | LMS real | S3 |
| **CALL Heritage Language Module** | học ngôn ngữ | đọc chú giải Việt–Anh/Hán–Nôm có mục tiêu ngôn ngữ | glossary, translations reviewed, language task rubric | scholars + teachers + pilot | S3 |
| **3D Precision Hotspot Studio** | curator | nối vùng mesh với atomic claim và perspective | persisted position, versioned model, preview + 2D | 3D real assets, editor API | S3 |
| **AI Research Factory as B2B Service** | bảo tàng/nhà nghiên cứu | chuẩn hóa và kiểm tra dữ liệu catalog dưới kiểm duyệt | batch import + evidence review + controlled export | source rights, multi tenancy, SRE | S4 |
| **Open Scholarly Interchange API** | viện/bảo tàng | interoperable metadata and verified citations | versioned JSON-LD/CSV, license badges, rate limits | published graph | S4 |
| **Verified Marketplace Ratings** | khách/nghệ nhân | đánh giá chỉ từ chuyến đã hoàn tất | completion-linked reviews, moderation/disputes | real bookings, fraud checks | S4 |

`S1` = ship for real first; `S2` = pilot traction; `S3` = differentiation after data real; `S4` = ecosystem scale. Nếu nguồn lực ít, tập trung đúng **Teacher Class Studio + Evidence Coach + Artisan Inquiry** thay vì mở mọi trục cùng lúc.

### 9.2. Journey-level feature specs

**Passport** — Role: guest/registered student. QR codes generated for approved heritage objects; record check-ins only with consent; offline pending state; stop location tracking by default; teacher may issue pedagogical completion certificates only after rubric grade; passport stamp merely indicates a visit/interaction. Anti-cheat: server check-in nonce, rate limit, QR signed, avoid hard requirement GPS (privacy/accessibility). Acceptance: 9 urns gallery works 2D, no fabricated completion, teacher can revoke badge issued in error.

**Evidence Coach** — Role: learner. Select observation and claim, cite supporting page, receive hints. Backend scores only according to transparent rubric and holds teacher review for high-stakes grade. Model must not generate source reference not retrieved. Acceptance: on false premise asks for source, missing source abstains, score pending until teacher; test sample 30 prompts with explicit support check.

**Teacher Class Studio** — Class onboarding, roster import only with authorization, reusable ELLO templates, 45-minute activity wizard, assignments, submissions, grading and PDF/CSV export under role policy. Child privacy: no public leaderboard with names; teacher dashboard pseudonymous; deletion/retention workflows. Acceptance: teacher A cannot access School B, rubric locked at grading, live updates reflected across devices.

**Museum QR Trails** — Metadata registry for QR anchors, license for physical signage, verified source page, multilingual narration, AR optional. Visitors can continue offline; support accessibility (captions, text alternatives). Acceptance: low-bandwidth loads 2D within agreed budget; revoked asset/creator hidden; experience analytics omit precise GPS without consent.

**Partner Calendar** — Listing availability, versioned slot inventory, capacity, hold expiration, timeout, human confirmation; no automatic purchase until consent/contract. Acceptance: 2 simultaneous requests for 1 seat cannot both be confirmed; race test serializable compare-and-swap.

**Ratings & Referral** — Only after verified completed experience, moderation, appeal, anti-spam; do not incentivize positive reviews specifically, no fake reviews. Referral rewards only if legal/ethical and opt-in. Acceptance: unverified guest cannot rate; partner cannot alter independent rating silently; dispute workflow supports correction.

**CALL** — Only if genuine language-learning objective and measurable language task exists; test vocabulary/translation/reading comprehension before claiming CALL research. Historical source evaluation alone is not CALL.

