# V5.10 — STARTUP_GTM_BUSINESS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.10`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.10 — STARTUP: MÔ HÌNH KINH DOANH, VALIDATION VÀ PITCH CÓ BẰNG CHỨNG

### 10.1. Định vị và beachhead

**Định vị đề xuất:** “LƯU NIÊN giúp người học và khách tham quan khám phá di sản Việt Nam bằng nội dung có nguồn kiểm chứng, học tập tương tác và kết nối với nghệ nhân thật.” Không hứa mọi di sản toàn quốc trong MVP. Beachhead: Huế/Cửu Đỉnh + 2–3 đối tác trải nghiệm được đồng thuận + 2–3 giáo viên/trường triển khai thí điểm. Mở rộng thêm di sản khi content & rights pipeline chứng minh được chất lượng.

**Value proposition kiểm chứng được:**
- Trường học: tài liệu có nguồn và bài tập chấm được, tiết kiệm thời gian chuẩn bị bài (chỉ claim sau đo teacher baseline).
- Nghệ nhân: inquiry khách phù hợp, lịch rõ, quyền thông tin tự quyết; không hứa 4.5h tiết kiệm nếu chưa có phép đo.
- Khách: khám phá chân thực, hiểu ý nghĩa và đặt yêu cầu trải nghiệm dễ, không bị dẫn tới booking giả.
- Nhà quản lý di sản: provenance và quyền media, audit/rollback, giảm nguồn diễn giải thiếu kiểm soát.

### 10.2. Business Model Canvas 2-track

| Hạng mục | EdTech track | Experience track |
|---|---|---|
| Buyer | trường, bảo tàng, đơn vị hoạt động giáo dục | khách trả phí trải nghiệm; đối tác trả commission theo hợp đồng |
| User | giáo viên, học sinh | khách du lịch, nghệ nhân |
| Pain | thiếu nguồn tin cậy và worksheet tương tác, thời gian soạn bài | khó tìm trải nghiệm uy tín; nhiều inquiry rời rạc |
| Solution | lesson studio + source graph + 2D/3D + rubric | verified stories + creator profile + request/confirmation |
| Revenue assumption | annual school SaaS + onboarding/training; cần discovery willingness-to-pay | % completed verified experience hoặc fixed partner subscription; phải ký điều khoản |
| Key costs | historical review, hosting/media, support, AI calls, teacher onboarding | partner support, source licensing, customer service, dispute, marketing |
| Main risk | school adoption/consent/data minors | disintermediation, fake bookings, limited inventory, seasonality |
| Moat hypothesis | evidence provenance + teacher workflows + licensed content | verified artisan network + consent + story-to-experience data |

### 10.3. Không dùng số dự báo làm thực tế

`docs/rbpc/FINANCIAL_ASSUMPTIONS.md` nêu 1.100 trải nghiệm hoàn tất/năm, 10% commission, giá tham khảo. Đây là **TARGET/ASSUMPTION** cho đến khi có recorded completed bookings và financial reconciliation. Tương tự 4.5h/tuần tiết kiệm, 15% conversion là **hypothesis** cần kiểm định. Người làm pitch phải gắn nhãn cạnh số liệu: `OBSERVED`, `VALIDATED_PARTNER`, `PILOT`, `FORECAST`, `ILLUSTRATIVE`. Các quan sát thị trường bên ngoài cần nguồn và năm thống kê.

### 10.4. North Star Metrics và KPI tree

**EdTech North Star:** `weekly source-grounded learning tasks completed with rubric/evidence` chứ không phải clicks/XP.  
**Experience North Star:** `verified completed cultural experiences with partner & visitor evidence` chứ không phải inquiry form opens.  
**Platform Quality:** `published_claims_with_valid_source_locator / published_claims`, `consent_coverage`, `rights_coverage`, `citation_failure_rate`, `availability_SLO`.

| Funnel stage | Definition | Dedup method | Legitimate numerator/denominator |
|---|---|---|---|
| Exposure | unique eligible sessions opted-in | anonymous session with 24h TTL | sessions with story view / eligible sessions |
| Engagement | open source, dwell under privacy | server/client event dedup | sessions with ≥1 meaningful action / story viewers |
| Inquiry | server-committed inquiry | inquiry_id | inquiries / eligible experience page sessions |
| Confirm | partner-approved inquiry | state event unique | confirmed inquiries / real inquiries |
| Complete | attested actually occurred | completion evidence | completed verified / confirmed |
| Revenue | fee actually invoiced/collected | reconciliation id | real cash receipts, not website conversions |
| Education activation | first actual class assignment | teacher+school+week | active teachers / eligible onboarded teachers |
| Education retention | teacher repeats lesson after week 4 | cohort by first class | retained / eligible school teachers |

Publish only cohort sizes meeting privacy minima; avoid group-level re-identification for minors. Analytics must separate beta/test traffic from real customers.

### 10.5. Unit Economics and pricing tests (giả thuyết, không phải dữ liệu quan sát)

For an illustrative workshop price `P`, agreed take rate `r`, completed bookings `B`, refund/dispute fees `F`, variable operation costs `C`, estimated revenue = `B*P*r - F`, contribution = revenue - C. Example `P=500,000 VND`, `r=10%`, `B=20` yields gross platform fee `1,000,000 VND` **in this hypothetical scenario only**; not actual traction or income. Bookings must be verified completed. Track payment channel, taxes, provider payouts and refunds separately. School SaaS pricing must be validated through interviews/LOI and pilot renewal, not invented numbers presented as accepted prices.

### 10.6. Go-to-market experiments (pre-register)

| Experiment | Target sample | Method | Success decision rule | Risk |
|---|---|---|---|---|
| Discovery schools | 8–15 teachers (pilot assumption) | structured interviews about lesson prep and budgets | ≥ target percent show repeated use, not just praise | convenience bias |
| Lesson pilot | ≥2 classes if approved | real assignment, teacher rubric, class observation | high successful completion without technical intervention | student consent and confounding |
| Artisan ops pilot | 2–3 consented workshops | onboard real profiles + inquiry inbox | partner acknowledges real leads and chooses continuation | no guarantee customers arrive |
| Visitor usability | 10–20 eligible adults | 2D/3D navigate to true inquiry | observed task completion and meaningful comprehension | sample not representative |
| AI trust test | blind human gold set | historical claim verification and source support | threshold fixed before evaluation | expert time and licensing |
| Paid B2B pilot | verified decision makers | paid LOI / small paid proof-of-concept | at least one fully documented pilot contract (target) | procurement timelines |

**Không sử dụng khảo sát 1.502 học sinh để tính TAM/SAM/SOM**. Dataset này đo nhận biết/sở thích/cảm nhận đối với tài liệu, không phải willingness-to-pay, bookings, causal learning gains.

### 10.7. Startup competition evidence room

Required folders (target artifact manifests, avoid public PII): `evidence/product` (real screen+functional tests), `evidence/heritage` (verified citations/rights), `evidence/market` (dated independent sources), `evidence/customers` (opt-in interviews, anonymized), `evidence/partners` (LOIs/consent, controlled access), `evidence/finance` (scenario vs actual), `evidence/operations` (SLO/backup/security), `evidence/impact` (measured not invented), `evidence/legal` (ownership, terms, data policy), `evidence/team` (roles/contributions). Pitch claims link to evidence id, source locator, verification date and reviewer.

### 10.8. 10-slide pitch narrative (không tạo slide trong ticket này)

1. Problem in Huế education + cultural experience (sourced). 2. Two user journeys with real pain. 3. Live demo of heritage claim → verifiable source. 4. Teacher workflow & class task. 5. Artisan-consented story → real inquiry. 6. Differentiation: knowledge trust + rights + 2D access. 7. Market thesis with assumptions visibly separated. 8. Validation/traction with evidence links (if zero revenue, show honest pilot). 9. Go-to-market + unit economics hypotheses. 10. Team, requested support, 6–12 month milestones and risks. No AI-generated testimonials, no claims of UNESCO endorsing product, no “Q2 accepted” without decision.

### 10.9. IP, brand, permissions and governance

Clarify ownership of code/assets, contributor agreements (including student founders), rights on historical photos and photogrammetry, permissions from schools, artisans and contributors. UNESCO designation concerns specific heritage material, **not endorsement of LƯU NIÊN**. Startup legal structure, taxes, consumer terms, payment obligations, minors' data and consent must be reviewed with competent local counsel before selling. No claiming specific statute compliance without legal review. Use least-privilege data and retention schedules.

