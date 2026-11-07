# LƯU NIÊN — Customer Discovery Experiments & Research Protocols

**Document ID:** `DOC-RBPC-DISCOVERY-001`  
**Version:** 1.1.0 Final  
**Date:** 2026-11-05  
**Topic:** Customer Discovery Experiments, Standardized Usability Tasks, Anonymized Feedback Store & Pre-Registered Falsification Thresholds  
**Scope:** RBPC 2026 Cultural Bridge & EdTech Tracks  
**Controlling Documents:** `DOC-RBPC-VAL-001` (Validation Register), `DOC-RBPC-METRICS-001` (Customer Value Metrics), `DOC-RBPC-EVID-001` (Market Claims Evidence Register)

---

## 1. Executive Summary & Epistemic Framework

Customer discovery in LƯU NIÊN is governed by pre-registered evaluation thresholds, standardized interview protocols, and privacy-preserving feedback stores. To prevent founder confirmation bias, all experiments are pre-registered with quantitative falsification criteria prior to data collection.

### 1.1 Non-Representativeness Disclaimer Requirement (Negative Abuse Invariant)

**METHODOLOGICAL MANDATE:**
> **All self-selected cohorts, voluntary survey respondents, interview participants, and usability testers represent non-probability convenience samples.**
> Under no circumstances may self-selected responses be claimed or reported as *representative of the general population* of cultural tourists or Vietnamese educators without an explicit methodology disclaimer stating:
> 1. **Sampling methodology:** Convenience / self-selected / purposive opt-in (non-probability sample).
> 2. **Selection bias boundaries:** Early adopters, technologically fluent, cultural enthusiasts.
> 3. **Extrapolation prohibition:** Express prohibition on extrapolating population-level market adoption without randomized stratified sampling.

Violation of this invariant (e.g., claiming "Huế tourists prefer X" or "Vietnamese schools demand Y" based on 10–20 interviews or self-selected questionnaires) triggers an immediate audit rejection.

#### Canonical Bilingual Disclaimers

**English Canonical Disclaimer:**
> *"Methodology Disclaimer: Participants in this discovery experiment were recruited via voluntary opt-in and convenience sampling (non-probability sample). The findings reflect selection bias toward technologically fluent cultural enthusiasts and early adopters, and cannot be extrapolated as statistically representative of the general population without randomized stratified sampling."*

**Vietnamese Canonical Disclaimer:**
> *"Tuyên bố Phương pháp luận: Người tham gia thử nghiệm khám phá khách hàng được tuyển chọn thông qua hình thức tự nguyện đăng ký và lấy mẫu thuận tiện (mẫu phi xác suất). Kết quả phản ánh độ lệch chọn mẫu hướng tới nhóm người đam mê văn hóa và thành thạo công nghệ, và không thể suy rộng thành đại diện thống kê cho toàn thể dân số nếu không có phương pháp lấy mẫu phân tầng ngẫu nhiên."*

---

## 2. Standardized Discovery Interview Scripts

### 2.1 Script A: Artisan Guild Lineage Masters & Studio Leads (`ART-DISC`)
- **Target Cohort:** 4–8 Master artisans and family workshop coordinators across Huế (Pháp Lam, Bronze casting, Trúc Chỉ, Imperial embroidery).
- **Purpose:** Map workshop lead times, unannounced visitor friction, intermediary exploitation, and take-rate viability.
- **Structured Questions:**
  1. `ART-Q01` (*Current Acquisition*):
     - **VI:** Hiện nay du khách tự túc tìm đến xưởng của bác qua những kênh nào khi không đi theo tour du lịch lớn?
     - **EN:** How do independent travelers currently discover your atelier without tour buses?
     - **Objective:** Identify organic vs fragmented discovery channels and middleman commissions.
  2. `ART-Q02` (*Operational Friction*):
     - **VI:** Khi khách đến đột xuất mà xưởng chưa chuẩn bị nguyên liệu (đun đồng, ngâm giang tre), bác xử lý thế nào?
     - **EN:** What happens when guests arrive unannounced or expect instant crafting sessions?
     - **Objective:** Validate urgency of 24h inquiry lead time.
  3. `ART-Q03` (*Dignity & Pricing*):
     - **VI:** Bác đã từng bị các hướng dẫn viên bên ngoài ép giá hoặc giới thiệu sai lịch sử gia tộc chưa?
     - **EN:** Have third-party tour guides ever dictated prices or misrepresented historical lineages?
     - **Objective:** Establish artisan dignity safeguards and anti-misrepresentation protections.
  4. `ART-Q04` (*Inquiry Lead Time*):
     - **VI:** Thời gian tối thiểu bác cần để chuẩn bị chu đáo cho một buổi trải nghiệm 2-4 khách là bao lâu?
     - **EN:** What is the absolute minimum lead time required to prep materials for 2-4 guests?
     - **Objective:** Confirm SLA parameters for inquiry intake engine.
  5. `ART-Q05` (*Take-Rate Acceptance*):
     - **VI:** Nếu nền tảng chỉ thu 10% phí dịch vụ khi khách đã đến và hoàn tất trải nghiệm (không thu phí trước), bác thấy thế nào?
     - **EN:** Would an incremental 10% fee on completed verified visits be acceptable if zero upfront fees are charged?
     - **Objective:** Validate unit economics take-rate hypothesis without upfront financial risk.

### 2.2 Script B: Cultural Independent Travelers & Museum Visitors (`FIT-DISC`)
- **Target Cohort:** 15–30 Domestic & International cultural travelers in Huế.
- **Purpose:** Assess travel discovery friction, trust in heritage narratives, inquiry UX expectations, and willingness to pay.
- **Structured Questions:**
  1. `FIT-Q01` (*Search Frustration*):
     - **VI:** Khi tìm kiếm các trải nghiệm nghề thủ công đích thực tại Huế, bạn thường gặp khó khăn gì trên mạng?
     - **EN:** When seeking authentic local craft experiences, where do online searches fail?
     - **Objective:** Discover information fragmentation and commercial noise.
  2. `FIT-Q02` (*Trust in Heritage Claims*):
     - **VI:** Làm thế nào bạn biết một làng nghề là truyền thống thật hay là điểm mua sắm công nghiệp cho tour?
     - **EN:** How do you verify whether a marketed 'traditional village' is genuine or a commercial tourist trap?
     - **Objective:** Determine the value of archival proof and historical citations.
  3. `FIT-Q03` (*Inquiry vs Instant Booking*):
     - **VI:** Việc gửi yêu cầu hẹn trước và chờ nghệ nhân xác nhận trong 24h làm bạn tăng hay giảm độ tin cậy so với đặt phòng tức thì?
     - **EN:** Does requesting an appointment and waiting up to 24h for artisan confirmation increase or decrease your trust?
     - **Objective:** Test inquiry vs instant checkout perception.
  4. `FIT-Q04` (*Citations & AI*):
     - **VI:** Nếu trợ lý AI giải thích tích xưa trên Cửu Đỉnh có dẫn chú thích thư tịch gốc (Đại Nam Thực Lục), bạn thấy tin tưởng hơn không?
     - **EN:** If an AI explains an imperial motif, does seeing primary historical footnotes make you trust the content?
     - **Objective:** Validate AI citation faithfulness value proposition.
  5. `FIT-Q05` (*Willingness to Pay*):
     - **VI:** Mức giá nào bạn cảm thấy xứng đáng cho một buổi học nghề 2 giờ trực tiếp cùng nghệ nhân ưu tú (500k - 850k VND)?
     - **EN:** What price range would you consider reasonable for a 2-hour master-guided workshop?
     - **Objective:** Gauge willingness to pay (WTP) distribution.

### 2.3 Script C: Secondary School Heritage Educators (`EDU-DISC`)
- **Target Cohort:** 8–15 History & Civic Education teachers (Grades 10–12).
- **Purpose:** Identify curriculum obstacles, worksheet preparation time, and 2D printable fallback necessity.
- **Structured Questions:**
  1. `EDU-Q01` (*Curriculum Pain Points*):
     - **VI:** Trở ngại lớn nhất của thầy/cô khi giảng dạy phần lịch sử địa phương và di sản triều Nguyễn là gì?
     - **EN:** What are the primary obstacles in teaching the 2018 General Education Program local heritage modules?
     - **Objective:** Map curriculum compliance and source scarcity pain points.
  2. `EDU-Q02` (*Worksheet Prep Time*):
     - **VI:** Mỗi tuần thầy/cô mất bao nhiêu giờ để tìm tài liệu, bản dập sắc nét và chú thích lịch sử cho tiết học?
     - **EN:** How many hours per week are spent finding high-resolution rubbings and cited historical sources?
     - **Objective:** Measure baseline prep time burden.
  3. `EDU-Q03` (*3D vs 2D Accessibility*):
     - **VI:** Trong điều kiện phòng học wifi yếu hoặc học sinh không có điện thoại, tài liệu in bản dập 2D quan trọng thế nào?
     - **EN:** If classrooms have weak Wi-Fi or lack phones, how essential are printable rubbings and 2D fallbacks?
     - **Objective:** Verify offline accessibility and Universal Design for Learning (UDL) requirement.
  4. `EDU-Q04` (*Assessment Burden*):
     - **VI:** Làm thế nào thầy/cô chấm điểm lập luận lịch sử theo mô hình Luận điểm - Dẫn chứng - Diễn giải (M-E-E)?
     - **EN:** How do you evaluate historical reasoning (M-E-E evidence framework) without subjective grading bias?
     - **Objective:** Confirm rubric utility and assessment standardization.
  5. `EDU-Q05` (*Institutional Adoption*):
     - **VI:** Quy trình phê duyệt ngân sách hoặc thủ tục thí điểm nào nhà trường yêu cầu trước khi triển khai phần mềm?
     - **EN:** What budget approvals or pilot proofs are required before school administrators greenlight EdTech tools?
     - **Objective:** Understand B2B school sales cycle and pilot requirements.

---

## 3. Structured Usability Evaluation Tasks

The platform implements 4 standardized usability tasks with objective pass/fail completion metrics:

| Task ID | Target Cohort | Scenario & Objective | Max Dwell | Success Criterion | Zero Upfront Check |
|---|---|---|---|---|---|
| `TASK-01` | Cultural Visitor | Explore "Đại Triều Nghi" story, click source citation [^1], inspect archive locator, and submit booking inquiry with preferred date ≥24h in advance. | 180s | Complete submission without validation error; verify 0 upfront charge notice seen. | ✅ YES |
| `TASK-02` | Museum Visitor | Scan QR token for Bronze Urn, navigate 2D rubbing fallback when WebGL disabled, and inspect Hán-Nôm inscription translation. | 120s | Successful navigation to rubbing view and reading translation without UI lockup. | — |
| `TASK-03` | Craft Partner | Receive inquiry notification, review visitor party size and date, and confirm availability via partner dashboard. | 90s | State transition from `new` -> `confirmed` executed in ≤2 clicks. | — |
| `TASK-04` | History Teacher | Access Lesson Wizard, select Cửu Đỉnh motif, filter by Grade 10 competency, and export printable low-bandwidth worksheet. | 150s | PDF/Printable generated with verified source citations and zero unreviewed claims. | — |

---

## 4. Pre-Registered Experiment Hypotheses & Falsification Thresholds

All experiments pre-register explicit quantitative success thresholds prior to field execution. Failure to achieve the target threshold or crossing the falsification trigger falsifies the product hypothesis and triggers a documented pivot.

| Exp ID | Hypothesis | Metric & Formula | Target Threshold | Falsification Trigger | Pre-Reg Status | Target N |
|---|---|---|---|---|---|---|
| `EXP-01` | Transparent inquiry copy ("Send Booking Request", 0 VND upfront) produces higher completion than instant checkout. | Form Completion Rate = `Completed Submissions / Form Starts` | ≥ 65.0% | Completion < 45.0% | `PRE_REGISTERED` | 30 |
| `EXP-02` | Primary source footnote drawer increases perceived trustworthiness among cultural travelers. | Trust Rating (% rating 4 or 5 on 5-point Likert scale) | ≥ 80.0% | Trust rating < 60.0% | `PRE_REGISTERED` | 25 |
| `EXP-03` | 24-hour advance lead-time constraint eliminates artisan scheduling friction and last-minute cancellation stress. | Partner Scheduling Conflict Rate | ≤ 5.0% | Conflict rate > 15.0% | `PRE_REGISTERED` | 10 |
| `EXP-04` | Teacher lesson wizard reduces lesson planning time from 3 hours to under 45 minutes. | Task Completion Time (minutes) | ≤ 45 min | Median time > 60 min | `PRE_REGISTERED` | 12 |
| `EXP-05` | Printable 2D rubbing kit delivers pedagogical equivalence in bandwidth-constrained classrooms. | Task Feasibility & Comprehension Score | ≥ 85.0% | Comprehension < 70.0% | `PRE_REGISTERED` | 40 |

---

## 5. Anonymized Feedback Store Architecture

Feedback data is stored with cryptographic zero-PII guarantees:
- **Participant Identity:** Pseudo-anonymized subject tokens matching `^[A-Z]{2,4}-[A-Z0-9]{4,8}$` (e.g., `FIT-8A2F`, `ART-1042`, `EDU-77X1`).
- **PII Scrubbing:** Names, emails, IP addresses, and phone numbers are automatically sanitized before persistence.
- **Consent Version Tracking:** Explicit capture of consent agreement (`consent_accepted=True`) and policy version (`rbpc-discovery-v1`).
- **Data Integrity:** Likert ratings strictly constrained to integer range `1..5`; dwell time in seconds tracked accurately.
- **Methodology Disclaimers:** Every report or export automatically bundles the mandatory non-representativeness notice.

---

## 6. Implementation References & Cross-Language Architecture

- **Backend Python Service:** `backend/services/rbpc_discovery.py` (`CustomerDiscoveryRegister`, `validate_methodology_disclaimer`, `scrub_pii`)
- **Frontend Core Library:** `frontend/src/lib/rbpc/discoveryExperiments.ts`
- **Frontend Usability Modal:** `frontend/src/components/rbpc/DiscoveryFeedbackModal.tsx`
- **Test Automation Suite:** `tests/v5/test_v5_t114.py` (Pytest) & `frontend/src/components/rbpc/discoveryExperiments.test.ts` (Vitest)
