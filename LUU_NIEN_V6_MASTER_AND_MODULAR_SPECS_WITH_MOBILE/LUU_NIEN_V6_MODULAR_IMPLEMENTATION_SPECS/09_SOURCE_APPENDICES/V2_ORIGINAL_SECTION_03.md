# V2 original archival technical chapter — SECTION_03

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 3. PRODUCT VISION, ROLES, MODULES

### 3.1 Personas và quyền

| Persona | Nhiệm vụ | Quyền | Dữ liệu không được thấy |
|---|---|---|---|
| Guest | xem hiện vật, nguồn published, 2D/3D, map | read public | đáp án test chưa hoàn thành, PII, drafts |
| Student/Minor | bài học, làm bài, reflection, FSRS | assigned content + own work | điểm bạn khác, dữ liệu nghiên cứu cá nhân, thông tin đối tác |
| Parent/Guardian | consent / xem dữ liệu hợp pháp nếu cấu hình | scoped child records theo pháp luật/quy trình | thông tin trẻ khác |
| Teacher | tạo lớp/lesson, chấm rubric, feedback | lớp được giao | lớp không được phân công |
| Heritage Editor | chỉnh claim/media/citation, gửi duyệt | content scope được gán | cấp chứng thực cuối nếu không đúng role |
| Historian/Subject Specialist | review lịch sử, reject/approve evidence | domain assigned | PII học sinh |
| Language Expert | duyệt transliteration, CALL task | language fields | thương mại bí mật |
| Media Rights Officer | rights/consent/license | asset rights | PII nghiên cứu không cần |
| Artisan/Partner | profile consent, inbox inquiry thuộc mình | provider-scoped | inquiry của provider khác |
| Research Analyst | dataset aggregate/ẩn danh được cấp quyền | research project scoped | tên/email/raw IP mặc định |
| System Admin | operation/security/config | break-glass có audit | nguyên tắc tối thiểu quyền vẫn áp dụng |

### 3.2 Domain boundaries

Các bounded contexts: `Identity`, `Historical Knowledge`, `Heritage Catalog`, `Media/3D`, `Instruction`, `Assessment`, `Learner Progress`, `Research`, `AI`, `Living Heritage`, `Experience Inquiry`, `Rights & Consent`, `Telemetry`, `Governance`, `Operations`. Không cho domain phụ tự tạo bản sao thực thể/sources không đồng bộ.

### 3.3 Quality attributes có tiêu chí

- Correctness: 100% published factual claims phải có ít nhất một binding đến source có locator; claim gây tranh luận phải có trạng thái và ghi chú.
- Availability: công khai 2D hoạt động khi 3D/AI/WebRTC lỗi; mục tiêu uptime tự đặt và đo, không tuyên bố đạt sẵn.
- Accessibility: WCAG 2.2 AA target; điều hướng bàn phím, transcript, captions, non-AR route, low-bandwidth mode.
- Performance: p95 API browse < 600ms khi warmed cache; p95 static article load < 2.5s trên cấu hình mục tiêu định nghĩa; asset budgets phải được đo thật trước claim.
- Security: auth/tenant test required; nhánh research mặc định cấm public; 0 secrets in repo; public API có rate limiting và observability.
- Research: deterministic export from versioned raw files; replicate all published counts; query and denominator traceability.
- Sustainability: không lấy quyền của nghệ nhân hoặc mô hình 3D khi giấy phép không cho phép; rollback/withdrawal thực thi thực tế.

---

