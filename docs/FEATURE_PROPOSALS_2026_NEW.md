# Feature Proposals 2026 — Bổ sung cho Luuniensuki LMS

Ngày: 2026-05-19
Tác giả: Kiro (research-driven proposal)

## 1. Bối cảnh và phạm vi

Tài liệu này **bổ sung** cho các đề xuất hiện có và **không trùng lặp** với:

- `docs/EDTECH_RESEARCH_INNOVATIONS_2026.md` — 7 đề xuất AI tutor/SRL/AR-CH
- `docs/LEARNER_EXPERIENCE_IMPROVEMENTS_2026.md` — 12 cải tiến UX (mission CTA, quiz auto-save, hearts UX, AI inline, v.v.)
- `docs/RESEARCH_BREAKTHROUGH_FEATURES_2026.md` — 6 công nghệ đột phá (Realtime multimodal tutor, GraphRAG, Knowledge tracing, On-device AI, Eval pipeline)

**Trọng tâm tài liệu này:** các tính năng có thể implement trên Rust backend hiện tại, leverage 290 native routes, không phụ thuộc nặng vào AI/LLM, có ROI rõ và bằng chứng research.

**Bối cảnh hệ thống hiện tại (đã verify):**

- 290/291 routes native trên Rust (Axum + SQLx + PostgreSQL)
- Frontend Next.js + React Three Fiber cho 3D
- Mobile Flutter app với offline cache lessons
- Live AI Teacher worker (Python) cho realtime voice/chat
- Đã có: streak, hearts, badges, quests, milestones, leaderboard, classrooms
- DB: ~9 urns Cửu Đỉnh, motifs theo từng đỉnh, lesson contents, quiz questions
- Production: `https://lms.histolab.icu`

---

## 2. Bảy nhóm tính năng đề xuất

### 2.1 — Citizen Curation: cộng đồng đóng góp diễn giải di sản

**Vấn đề:** App hiện tại có nội dung do admin/teacher seed. Người học chỉ tiêu thụ, không đóng góp. Trong khi đó, nhiều người Việt có hiểu biết quý về Cửu Đỉnh (gia đình ở Huế, sinh viên Hán Nôm, nhà nghiên cứu di sản) đang không có kênh đóng góp có cấu trúc.

**Bằng chứng research:**

- Dự án EU SPICE (Social cohesion, Participation, Inclusion through Cultural Engagement) chứng minh citizen curation tăng community engagement và quality of metadata cho di sản.
  Nguồn: [SPICE H2020](https://spice-h2020.eu/) — content rephrased for compliance with licensing restrictions
- Nature 2025 RCT về VR/AR cultural heritage games (N=80) cho thấy: knowledge gain tương quan với exploratory density và group interaction.
  Nguồn: [npj Heritage Science 2025](https://www.nature.com/articles/s40494-025-02247-z) — content rephrased for compliance with licensing restrictions

**Thiết kế tính năng:**

1. **Motif notes** — Người dùng có quyền `learner` đã pass quiz một motif có thể submit "ghi chú diễn giải" (text + optional image). Note có 4 trạng thái: `draft → pending → approved → featured`.
2. **Community translation layer** — Người dùng đóng góp dịch nội dung từ tiếng Việt sang tiếng Anh/Pháp/Nhật. Mỗi đoạn dịch được rate bởi 3 user khác trước khi auto-approve (nếu trung bình >= 4/5).
3. **Heritage Source Library** — Người dùng có quyền `teacher` upload tài liệu nguồn (sách, báo, ảnh) để bind với motif. Admin moderate trước khi public. Tích hợp với RAG sources cho AI tutor.
4. **Reputation system** — Mỗi đóng góp được approved: +5 XP + 1 reputation point. Tier: `Newcomer (0)` → `Contributor (50)` → `Curator (200)` → `Expert (500)` → `Heritage Steward (2000)`. Tier cao mở quyền moderate.

**Implement vào Rust backend:**

- New tables: `motif_notes`, `motif_note_votes`, `heritage_sources`, `user_translations`, `user_reputation`
- Routes mới (~12 routes): `POST /api/v1/motifs/:id/notes`, `GET /api/v1/motifs/:id/notes`, `POST /api/v1/notes/:id/vote`, `GET /api/v1/users/me/reputation`, `POST /api/v1/admin/notes/:id/moderate`, etc.
- Tận dụng auth/badge/XP infrastructure đã native.

**KPI đo lường:**

- % users tạo ít nhất 1 note trong 30 ngày đầu (target ≥ 8%)
- Notes approved per week (target ≥ 50 sau 3 tháng)
- Quiz score của motifs có ≥3 community notes vs không có (kỳ vọng nhóm có notes cao hơn ≥ 5 điểm tuyệt đối)

**Effort:** 3-4 sprints. Risk: moderation overhead — cần admin tooling tốt.

---

### 2.2 — Heritage Trail Mode: hành trình du lịch số

**Vấn đề:** App hiện tại tổ chức nội dung theo "urns / motifs / lessons" — cấu trúc kiến thức. Nhưng heritage learning hiệu quả nhất khi có **narrative arc** kiểu hành trình (chứng cứ: Heritage-based Video Games research 2025 chỉ ra "narrative-driven gameplay" và "open-world exploration" tăng retention so với task-based learning).

**Bằng chứng research:**

- ResearchGate 2025: Heritage-based games có "narrative-driven gameplay, task-driven learning, open-world exploration" tăng meaningfulness so với non-narrative formats.
  Nguồn: [Digital Game-Based Heritage Education](https://www.researchgate.net/publication/379750538) — content rephrased for compliance with licensing restrictions
- Vietnamnet 2025 báo cáo Vietnam Cultural Heritage Conservation Fund + TikTok ký hợp tác để phát triển #DiSanVietNam hashtag challenge — chứng minh demand cho narrative heritage content trong giới trẻ Việt.
  Nguồn: [Vietnamnet 2025](https://vietnamnet.vn/en/bringing-vietnam-s-heritage-to-life-through-games-and-social-media-2386143.html) — content rephrased for compliance with licensing restrictions

**Thiết kế tính năng:**

1. **Trails** — Một trail là chuỗi 5-15 motifs có chủ đề rõ (ví dụ: "Linh vật Cao Đỉnh", "Hình tượng vua Minh Mạng qua 9 đỉnh", "Họa tiết hoa cỏ trong văn hóa cung đình"). Có narrator script đầu/cuối.
2. **Story checkpoints** — Mỗi 2-3 motifs có một "checkpoint" — 1 câu hỏi reflection ngắn ("Bạn đã thấy 3 motif này có chung điểm gì?"). Trả lời lưu lại như learning journal.
3. **Trail pace** — User chọn pace: `1 trail / week`, `2 trails / week`, hoặc `daily`. Hệ thống nhắc theo pace đã chọn (tích hợp với streak hiện có).
4. **Trail completion certificate** — Hoàn thành trail → cấp certificate PDF có tên user, ngày, mô tả trail, hash để verify trên `/api/v1/certificates/:hash/verify`.
5. **Curator-built trails** — `teacher` role có thể tạo trails private cho lớp học của mình, sau đó submit để admin promote thành public.

**Implement:**

- New tables: `trails`, `trail_motifs` (many-to-many), `trail_checkpoints`, `user_trail_progress`, `trail_certificates`
- Routes (~8): `GET /api/v1/trails`, `GET /api/v1/trails/:slug`, `POST /api/v1/trails/:slug/start`, `POST /api/v1/trails/:slug/checkpoint/:idx`, `GET /api/v1/users/me/trails`, `POST /api/v1/teacher/trails`, etc.
- Reuse existing `lesson_caches` table cho offline trail support.

**KPI:**

- % users start ít nhất 1 trail trong 14 ngày đầu (target ≥ 30%)
- Trail completion rate (target ≥ 40% — benchmark Coursera khóa MOOC ngắn ~30%)
- Avg lessons completed/user/week tăng ≥ 25% so với baseline

**Effort:** 4-5 sprints. Có thể release MVP với 2-3 trails admin-seeded trước khi mở curator-built.

---

### 2.3 — FSRS Spaced Repetition: thay thế SM-2 hiện tại

**Vấn đề:** App hiện đã có spaced repetition (`backend/services/spaced_repetition.py`) nhưng dùng thuật toán cổ điển kiểu SM-2 (Anki). Algorithm này có 2 vấn đề chứng minh được: (1) over-review easy cards, (2) under-review hard cards. FSRS (2024) là state-of-the-art mới, MIT licensed, có Rust crate sẵn.

**Bằng chứng research:**

- FSRS-4-Anki (open-spaced-repetition GitHub, 3.2k stars) là algorithm dựa trên DSR model (Difficulty, Stability, Retrievability) chính xác hơn SM-2.
  Nguồn: [FSRS GitHub](https://github.com/open-spaced-repetition/fsrs4anki) — content rephrased for compliance with licensing restrictions
- Bench published trong wiki: FSRS đạt log-loss thấp hơn ~30% so với SM-2 trên dataset 700M reviews.
  Nguồn: [FSRS Algorithm wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm) — content rephrased for compliance with licensing restrictions

**Thiết kế tính năng:**

1. **FSRS scheduler trong Rust** — Có sẵn crate `rs-fsrs`. Tích hợp vào `backend-rust/src/services/spaced_repetition_service.rs`.
2. **Per-user parameter optimization** — Sau mỗi 50 reviews của user, retrain w0..w16 parameters (job nền). Dùng Cohort thay thế nếu user có < 50 reviews.
3. **Optimal retention slider** — User chọn target retention rate (75% ↔ 95%). Retention thấp = ít review hơn, retention cao = nhớ chắc hơn.
4. **Card states** — `New → Learning → Review → Relearning`. Mỗi quiz attempt sinh `Rating ∈ {Again, Hard, Good, Easy}`.
5. **Migrate from SM-2** — Một-time migration job: set initial Stability dựa trên `quiz_best_score`, set Difficulty default 5.

**Implement:**

- Add `rs-fsrs = "=1.5.0"` (pinned) vào `Cargo.toml`
- Modify `quiz_questions` schema: thêm columns `fsrs_difficulty`, `fsrs_stability`, `fsrs_due_date`, `fsrs_last_review`, `fsrs_state`
- Routes mới: `GET /api/v1/reviews/due`, `POST /api/v1/reviews/:card_id/rate`, `GET /api/v1/users/me/review-stats`, `POST /api/v1/admin/fsrs/retrain`
- A/B test: 50% users dùng FSRS, 50% giữ SM-2 (tận dụng `Experiment` table sẵn có)

**KPI:**

- 7-day retention rate (target ≥ 90% trong nhóm FSRS vs ~75% trong SM-2)
- Daily review time per user giảm ≥ 20% (do skip easy cards)
- Quiz pass rate sau 14 ngày từ lần đầu học motif (target +10pp)

**Effort:** 2-3 sprints. Risk: parameter retraining cần background worker — có thể delay đến v2.

---

### 2.4 — Heritage Time-Lapse: trục thời gian tương tác

**Vấn đề:** Cửu Đỉnh được đúc từ 1835-1837 dưới thời vua Minh Mạng. Mỗi đỉnh đại diện một vị vua. Hiện tại app trình bày 9 đỉnh đồng thời, không có dimension lịch sử. Người học mất context "đỉnh nào ra đời trước/sau", "vị vua nào tương ứng", "bối cảnh chính trị".

**Bằng chứng research:**

- MDPI 2025: "Three-Dimensional Modeling and AI-Assisted Contextual Narratives in Digital Heritage Education" cho thấy timeline + contextual narrative tăng comprehension score so với spatial-only views.
  Nguồn: [MDPI Heritage](https://www.mdpi.com/2571-9408/8/7/280) — content rephrased for compliance with licensing restrictions
- Hanoi Temple of Literature "Việt Nam Diệu Sử" AR project (2025) đã chứng minh thị giác hóa lịch sử trong không gian thực giúp visitors absorb thông tin nhanh hơn.
  Nguồn: [hanoi.gov.vn](https://sovhtt.hanoi.gov.vn/en/experiencing-digital-heritage-viet-nam-dieu-su-at-the-temple-of-literature/) — content rephrased for compliance with licensing restrictions

**Thiết kế tính năng:**

1. **Timeline view** — Trang `/timeline` hiển thị 9 đỉnh trên trục thời gian 1835-1837 + năm trị vì 9 vua Nguyễn (Gia Long → Bảo Đại). Click vào sự kiện mở detail panel.
2. **Era filter** — Filter motifs theo "thời kỳ đầu Nguyễn", "thời Pháp thuộc", "hậu hiện đại". Mỗi motif gắn `era_tags` array.
3. **Compare panel** — Chọn 2 motifs cùng category (ví dụ: 2 hình rồng từ 2 đỉnh khác nhau) → side-by-side comparison: thời kỳ, tinh xảo, ý nghĩa biểu trưng.
4. **Historical events overlay** — Trên timeline overlay các sự kiện lịch sử ngoài (Hiệp ước Patenôtre, đảo Hoàng Sa-Trường Sa, nhà Nguyễn cáo chung) để học sinh thấy bối cảnh.

**Implement:**

- New tables: `historical_events`, `motif_eras` (many-to-many)
- Routes: `GET /api/v1/timeline/events`, `GET /api/v1/timeline/motifs?era=`, `GET /api/v1/motifs/compare?ids=`
- Frontend: trang timeline mới + compare modal
- Reuse existing motif schema, chỉ thêm `era_tags` (Postgres array) và backfill data từ existing content

**KPI:**

- Timeline page views/user/week (target ≥ 1.2)
- Compare modal opens (target ≥ 2k/month)
- Quiz score motifs liên quan đến historical events tăng ≥ 5pp

**Effort:** 2-3 sprints. Cần work với content team để seed historical events đúng.

---

### 2.5 — Streak Repair Economy: hệ thống "cứu chuỗi" thông minh

**Vấn đề:** Hiện tại có `streak_freezes` cho phép "đông cứng" streak trong 1 ngày bỏ học. Nhưng (a) user không biết khi nào nên dùng, (b) chỉ có 1 cơ chế cứng, (c) không có sự an toàn khi server outage.

**Bằng chứng research:**

- Duolingo Blog 2024: streak system with freezes + repair mechanics + Big Red Button (BRB) cho server outages giảm churn từ 47% xuống 28% trong major markets.
  Nguồn: [Duolingo Streak Article](https://blog.duolingo.com/protecting-streaks-from-site-issues/) — content rephrased for compliance with licensing restrictions
- StriveCloud 2025: gamification triggers (streak, leaderboard) đẩy DAU lên 36% YoY ở Duolingo.
  Nguồn: [StriveCloud](https://www.strivecloud.io/blog/blog-gamification-examples-boost-user-retention-duolingo) — content rephrased for compliance with licensing restrictions

**Thiết kế tính năng:**

1. **Streak Freeze (đã có)** — giữ nguyên: 2 freezes/month, auto-apply.
2. **Streak Repair** — User mất streak có thể "repair" trong 48h sau khi mất, cost: 50 hearts hoặc 200 XP. Chỉ được repair tối đa 1 lần/tháng.
3. **Streak Insurance** — Subscription feature ($1.99/month): unlimited freezes + 3 repairs/month + "Server outage protection" auto-claim.
4. **Big Red Button (BRB)** — Internal admin endpoint: khi server có incident > 5min, admin click BRB → mọi user có active streak sẽ được "frozen" tự động, không mất streak. Log lại vào `streak_protection_events` table.
5. **Friend streak** — 2 user follow nhau và cả 2 cùng study trong 1 ngày → tăng 1 friend-streak. Hiện thị vào leaderboard. Xã hội hóa motivation.
6. **Streak comeback** — User mất streak 30+ ngày, sau đó quay lại + active 3 ngày liên tiếp → unlock "Phoenix" badge và double XP cho week tiếp theo.

**Implement:**

- New tables: `streak_repair_events`, `streak_protection_events`, `friend_streaks`, `streak_subscriptions`
- Routes (~6): `POST /api/v1/users/me/streak/repair`, `GET /api/v1/users/me/streak/repair-options`, `POST /api/v1/admin/streak/big-red-button`, `GET /api/v1/users/:id/friend-streak`
- Tích hợp với hearts service hiện tại

**KPI:**

- 30-day retention rate (target +8pp)
- Streak repair conversion (% users mất streak chọn repair) — target ≥ 25%
- Subscription uptake — target ≥ 2% MAU sau 3 tháng

**Effort:** 2 sprints. Subscription cần payment provider (Stripe/MoMo) — defer đến v2.

---

### 2.6 — Offline-First Mobile: học trên đường, không cần mạng

**Vấn đề:** Mobile app (Flutter) đã có lesson cache nhưng (a) không có offline quiz submission, (b) sync chỉ một chiều, (c) progress sync không có conflict resolution. Việt Nam có ~4G coverage tốt nhưng vẫn nhiều khu vực vùng sâu (Tây Nguyên, miền núi phía Bắc) có connectivity yếu.

**Bằng chứng research:**

- UNESCO Distance Learning Report: ~56 million learners toàn cầu sống ở khu vực không có mobile network. Offline-first design là trụ cột digital equity.
  Nguồn: [UNESCO Distance Learning](https://www.unesco.org/en/articles/startling-digital-divides-distance-learning-emerge) — content rephrased for compliance with licensing restrictions
- UNESCO Eneza Education case: SMS-based lessons trên feature phone (không internet) đạt scale ở rural Africa — mô hình tham khảo cho VN rural.
  Nguồn: [UNESCO Eneza](https://www.unesco.org/en/dtc-financing-toolkit/eneza-education) — content rephrased for compliance with licensing restrictions

**Thiết kế tính năng:**

1. **Full offline learning loop** — User download trail (5-15 lessons) → học offline → quiz offline → progress lưu local → sync khi online. Lesson + quiz contents được pre-cached ở client.
2. **Offline event queue** — Mọi user actions (quiz submit, lesson complete, heart spent, XP gain) lưu vào local SQLite queue với timestamp. Khi online: PUT bulk lên `POST /api/v1/sync/bulk-events`.
3. **Conflict resolution** — Server resolve conflicts theo rules:
   - XP/streak: lấy max
   - Hearts: server-authoritative (nếu local > server, drop local)
   - Quiz best_score: lấy max
   - Last activity: lấy timestamp mới nhất
4. **Offline-aware UI** — Hiển thị badge "Offline mode" + indicator pending events count. Khi sync: progress bar + summary "Đã đồng bộ X bài học, Y quiz."
5. **Selective download** — User chọn quality: `Light (~5MB/trail, no audio)`, `Standard (~30MB)`, `HQ (~80MB with audio narration)`. Mặc định Standard.

**Implement:**

- Flutter SQLite + sync queue logic
- Rust backend: `POST /api/v1/sync/bulk-events` accept array of events, return per-event status (`accepted | rejected | conflict_resolved`). Idempotent qua client-generated `event_id`.
- New tables: `sync_events_log`, `client_sync_state`
- Existing `lesson_caches` table extended với `cached_quality` column
- Mobile: upgrade flutter cache from CRUD-based to event-sourcing model

**KPI:**

- DAU trong khu vực connectivity yếu (đo qua IP geolocation) tăng ≥ 30%
- Conflict resolution rate (target < 0.5% events have conflicts)
- Avg sync latency p95 < 2s

**Effort:** 4-5 sprints (mobile + backend). Risk: conflict logic phức tạp — cần property-based tests kỹ.

---

### 2.7 — Heritage Map: bản đồ tương tác Việt Nam

**Vấn đề:** Cửu Đỉnh đặt ở Thế Tổ Miếu, Đại Nội Huế. Nhưng các motif trên đỉnh tham chiếu đến địa danh khắp Việt Nam (núi Tản Viên, sông Hương, biển Đông). Hiện tại không có cách nào nhìn ra connection địa lý.

**Bằng chứng research:**

- ACM 2025 CompARe project: gamified AR learning environment cho cultural heritage sites — học sinh đóng vai art historians qua các "digital hotspots" có vị trí địa lý.
  Nguồn: [ACM Digital Library](https://dl.acm.org/doi/10.1145/3703917) — content rephrased for compliance with licensing restrictions
- Geographic context tăng meaningfulness và personal connection trong heritage learning (research consensus across multiple meta-analyses).

**Thiết kế tính năng:**

1. **Vietnam map view** — Trang `/map` hiển thị bản đồ Việt Nam với pins các địa danh được mention trên 9 đỉnh. Click pin → list motifs liên quan đến địa danh đó.
2. **Geographic motif tags** — Mỗi motif (nếu có địa danh) bind với `geo_locations` (lat/lng + name + region).
3. **Region quests** — Quest mới "Thuần hành Bắc Bộ" (học hết motif về Bắc Bộ), "Khám phá Trung Trung Bộ" (motif về Huế-Quảng Nam-Đà Nẵng), v.v. 3 region quests.
4. **Local context** — Khi user mở app, GPS detect → suggest motifs near user. "Bạn đang ở Hà Nội? Đây là 5 motif liên quan đến vùng Bắc Bộ." (chỉ với consent location).
5. **Pilgrimage mode** — User đến các di sản thực ở VN (Hoàng thành Huế, đền Hùng, vịnh Hạ Long) → check-in qua GPS → unlock special "pilgrim" badges + nội dung độc quyền theo địa điểm.

**Implement:**

- New tables: `geo_locations`, `motif_locations` (many-to-many), `pilgrim_checkins`
- Routes (~6): `GET /api/v1/map/locations`, `GET /api/v1/map/motifs?lat=&lng=&radius=`, `POST /api/v1/pilgrim/checkin`, `GET /api/v1/users/me/pilgrim-progress`
- Frontend: Mapbox/Leaflet integration cho web, native maps cho Flutter
- Privacy: location data chỉ stored với user consent, opt-out anytime

**KPI:**

- Map page weekly views (target ≥ 5k/month sau 2 tháng)
- Pilgrim check-ins (target 500/month — niche metric, ai sống gần Huế)
- Region quest completion rate ≥ 30%

**Effort:** 3-4 sprints. Mapbox cost: ~$50/month tier free đủ cho start.

---

## 3. Bảng tổng hợp ưu tiên

| # | Feature | Effort (sprints) | Expected Impact | Risk | Phụ thuộc |
|---|---------|-----------------|----------------|------|-----------|
| 2.5 | Streak Repair Economy | 2 | 30-day retention +8pp | Low | None — leverage hearts/streak hiện có |
| 2.3 | FSRS Spaced Repetition | 2-3 | Review time -20%, quiz pass +10pp | Low | None — Rust crate sẵn |
| 2.4 | Heritage Time-Lapse | 2-3 | Comprehension score tăng | Low | Cần content team seed events |
| 2.2 | Heritage Trail Mode | 4-5 | Retention +25% lessons/week | Medium | Cần curator UI cho teacher |
| 2.6 | Offline-First Mobile | 4-5 | DAU rural +30% | Medium | Mobile team capacity |
| 2.1 | Citizen Curation | 3-4 | Community engagement | Medium | Moderation overhead |
| 2.7 | Heritage Map | 3-4 | New use case | Low | Mapbox integration |

**Recommendation thứ tự release:**

1. **Sprint 1-2:** Streak Repair Economy (quick win, leverage existing infra)
2. **Sprint 3-5:** FSRS Spaced Repetition + Heritage Time-Lapse (parallel)
3. **Sprint 6-10:** Heritage Trail Mode (large but high-impact)
4. **Sprint 11-15:** Offline-First Mobile + Heritage Map (parallel)
5. **Sprint 16-19:** Citizen Curation (cần community đủ lớn để có người curate)

---

## 4. Cross-cutting concerns

### 4.1 Đo lường (đã có infrastructure)

App có sẵn `Experiment` + `ExperimentEvent` tables → mọi tính năng mới phải:

- Có experiment_key (ví dụ `feat_streak_repair_v1`)
- Có giả thuyết H0/H1 viết rõ trước khi ship
- A/B test ≥ 2 tuần với power analysis (sample size đạt p < 0.05 cho effect size kỳ vọng)
- Stop rule: nếu primary metric giảm > 5% với p < 0.1, kill feature

### 4.2 Accessibility (WCAG 2.1 AA)

Mọi feature mới phải:

- Keyboard navigation cho mọi interaction
- Color contrast ≥ 4.5:1 cho text
- Screen reader labels (ARIA) cho 3D/map components
- Captions cho audio narration
- Font scalable đến 200% không vỡ layout

### 4.3 Privacy & Data minimization

- Geolocation: explicit consent, opt-out anytime, không lưu lịch sử position
- Citizen curation: option ẩn danh username trên public notes
- Friend streak: opt-in, không default
- Tuân thủ Luật An ninh mạng VN + GDPR cho user EU

### 4.4 Tận dụng Rust backend

Tất cả features đều có thể làm thuần native Rust (không cần fallback Python):

- Reuse `auth` module cho mọi endpoint mới
- Reuse `gateway` cho legacy endpoint nếu cần backward compat
- Add SQL migrations qua existing Alembic pipeline
- Mỗi feature → 1 mới `routes/`, `services/`, `models/` module

---

## 5. Câu hỏi research mở (cho nhóm)

1. **Citizen curation moderation:** Có thể dùng LLM-as-judge để pre-filter notes trước human moderation không? Hiệu quả bao nhiêu so với chỉ human?
2. **FSRS personalization:** Per-user param có thực sự cần không, hay cohort-level (ví dụ: theo age group, theo skill level) là đủ?
3. **Heritage Trail length:** 5 lessons/trail vs 15/trail — đâu là sweet spot cho completion rate? Cần A/B test sớm.
4. **Pilgrimage mode adoption:** Có bao nhiêu user thực sự đến Huế? Cần survey hoặc soft-launch để estimate trước khi đầu tư GPS feature.
5. **Vietnamese-specific gamification:** Có pattern gamification riêng cho người Việt không? (ví dụ: lễ Tết, rằm tháng giêng → special quests theo lịch âm)

---

## 6. Kết luận

Bảy nhóm tính năng trên được chọn vì:

- **Không trùng** với 3 docs research hiện có
- **Tận dụng** 290 native routes Rust và schema PostgreSQL hiện tại
- **Có bằng chứng research** từ 2024-2026 (UNESCO, MDPI, Nature, ACM, FSRS, Duolingo)
- **Có path implement rõ** với effort ước tính 2-5 sprints/feature
- **Có KPI đo lường được** qua infrastructure A/B test sẵn có

Ưu tiên triển khai theo thứ tự ROI/effort: Streak Repair → FSRS → Time-Lapse → Trails → Offline → Curation → Map.

---

## Phụ lục: Nguồn tham khảo

Tất cả nguồn được rephrased for compliance với licensing restrictions:

- **Cultural Heritage Tech (Vietnam):**
  - [Vietnamnet — heritage games and social media](https://vietnamnet.vn/en/bringing-vietnam-s-heritage-to-life-through-games-and-social-media-2386143.html)
  - [VOV — Reviving Vietnam heritage digital innovation](https://english.vov.vn/en/culture/reviving-vietnams-cultural-heritage-through-digital-innovation-post1287219.vov)
  - [Hanoi Department — Việt Nam Diệu Sử AR](https://sovhtt.hanoi.gov.vn/en/experiencing-digital-heritage-viet-nam-dieu-su-at-the-temple-of-literature/)

- **Heritage Education Research:**
  - [MDPI Heritage 2025 — 3D + AI Contextual Narratives](https://www.mdpi.com/2571-9408/8/7/280)
  - [Nature 2025 — VR/AR Cultural Heritage Serious Games](https://www.nature.com/articles/s40494-025-02247-z)
  - [ACM 2025 — CompARe Gamified AR](https://dl.acm.org/doi/10.1145/3703917)
  - [arxiv 2506.04090 — Reference Architecture Gamified Cultural Heritage AI/AR](https://arxiv.org/html/2506.04090v1)
  - [SPICE H2020 — Citizen Curation](https://spice-h2020.eu/)

- **Gamification & Retention:**
  - [Duolingo Blog — Streak habit research](https://blog.duolingo.com/how-duolingo-streak-builds-habit/)
  - [Duolingo Blog — Big Red Button server protection](https://blog.duolingo.com/protecting-streaks-from-site-issues/)
  - [StriveCloud 2025 — Duolingo gamification 36% DAU YoY](https://www.strivecloud.io/blog/blog-gamification-examples-boost-user-retention-duolingo)

- **Spaced Repetition:**
  - [FSRS-4-Anki GitHub](https://github.com/open-spaced-repetition/fsrs4anki)
  - [FSRS Algorithm wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)
  - [FSRS Optimal Retention](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Optimal-Retention)

- **Accessibility & Equity:**
  - [UNESCO — Charter Preservation Digital Heritage](https://www.unesco.org/en/legal-affairs/charter-preservation-digital-heritage)
  - [UNESCO — Distance Learning Digital Divides](https://www.unesco.org/en/articles/startling-digital-divides-distance-learning-emerge)
  - [UNESCO — Eneza Education case study](https://www.unesco.org/en/dtc-financing-toolkit/eneza-education)
