# V2 B5: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B5`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B5. UI/UX INTERACTION SPEC — THEO MÀN HÌNH VÀ TRẠNG THÁI

### B5.1 Web route implementation matrix (TARGET, cần map với App Router appendix A)

| Screen / route mới dự kiến | Primary user | Mục tiêu | Thành phần bắt buộc | QA states |
|---|---|---|---|---|
| `/explore/urns` | public | tìm 9 đỉnh/162 relief | urn grid, filter, search, source badge | loading/empty/offline/error/unknown |
| `/explore/urns/[urn]` | public | duyệt từng đỉnh | 18 relief grid, vị trí, 2D/3D capability | rights-withdrawn, low-bandwidth |
| `/explore/reliefs/[id]` | public/student | học một hiện vật | image, provenance, claims, sources, uncertainties | conflicting source, AI-draft hidden |
| `/explore/reliefs/[id]/3d` | public | quan sát cấu trúc | model viewer, hotspots mapped, controls, fallback | WebGL fail, no mesh, revoked rights |
| `/learn/ellos/[id]` | student | inquiry 6 bước | observation panel, source drawer, answer editor, feedback | auto-save, conflict, resubmit |
| `/learn/assignments/[id]` | student | bài giao lớp | deadline, accessible route, progress, rubric | expired, access denied, offline |
| `/teacher/ellos/new` | teacher | soạn ELLO | wizard, claim picker, source validator, rubric | unsaved changes, invalid lesson |
| `/teacher/ellos/[id]/review` | teacher/editor | xem tình trạng | release preview, source diff, approval | stale source, request changes |
| `/teacher/classes/[id]/grading` | teacher | phản hồi tự luận | blinded option, rubric, evidence side panel | multi-rater, save conflict |
| `/curator/reliefs` | curator | xử lý 162 | 9x18 coverage board, validation errors | filter review-state, no role |
| `/curator/claims/[id]` | curator/expert | duyệt claim | original text, locator, contradiction, audit history | reject, withdraw, annotate |
| `/curator/assets/[id]` | rights manager | quản trị giấy phép | grant proof, expiry, derivative chain | revoke/expired/unknown |
| `/research/studies/[id]` | research_admin | snapshot khảo sát | schema, item dictionary, anonymized import QA | invalid CSV, missingness, duplicate |
| `/research/studies/[id]/exports` | research_admin | xuất bảng cho paper | version lock, aggregates, hashes | suppressed small cells, unauthorized |
| `/rbpc/experiences/[slug]` | visitor | gửi inquiry | consent, availability, disclaimer, accessible contact | backend-down fail, duplicate submit |
| `/rbpc/partner/inquiries` | partner | xử lý inquiry | scoped inbox, status machine, notes audit | cross-partner denial, consent withdrawn |

### B5.2 Component design contracts

**`SourceCitationCard`**: hiển thị tác giả, nhan đề, ấn bản, locator, status kiểm chứng và source type; nếu chỉ có URL chung nhưng không có locator thì hiển thị cảnh báo và chặn dùng làm evidence assessed. Nút “Mở nguồn” phải dùng URL được quyền chia sẻ; bản quyền nguồn không tự cho phép sao chép toàn bộ PDF.

**`HistoricalClaimBadge`**: chỉ ra `documented / interpretation / traditional_account / disputed / unknown`; hover giải thích nguồn và mức độ chắc chắn; color không phải kênh duy nhất (text + icon). Không hiển thị “UNESCO verified” cho từng diễn giải chỉ vì bộ sưu tập được ghi danh UNESCO.

**`UrnModelViewer`**: trước khi tải WebGL kiểm quyền và performance hints; 2D default nếu reduced motion/data saver/no WebGL; hotspot click có keyboard equivalent; công khai model là đo đạc, photogrammetry hay illustrative. Model không thể tải thì giữ nguyên nhiệm vụ học tập qua 2D.

**`EvidenceComposer`**: cột trái observation, cột phải source excerpts, vùng viết thesis, hỗ trợ gắn citation bằng stable locator ID; highlight câu không gắn chứng cứ chỉ là gợi ý, không tự động chấm sai; nguồn giáo viên cung cấp và nguồn ngoài có nhãn phân biệt.

**`RubricFeedbackPanel`**: cho học sinh thấy tiêu chí và lời phản hồi cụ thể; điểm AI gợi ý không hiển thị như điểm giáo viên; cho phép xem version cũ và xác định thay đổi nào cải thiện chứng cứ.

**`RightsDisclosure`**: tên tác giả/đơn vị, phép hiển thị cho phép, ngày kiểm và nguồn chứng thực; status unknown => không serve underlying unauthorized file; lỗi không hiển thị logo “verified”.

### B5.3 State và thông báo chuẩn

| Trạng thái | UX yêu cầu | Điều tuyệt đối tránh |
|---|---|---|
| Loading > 1s | skeleton + task context | spinner vô thời hạn |
| Không có 3D | ảnh 2D + thông báo lý do | gắn nhãn lỗi học sinh thiếu năng lực |
| Nội dung chưa duyệt | “Chưa có thông tin đã thẩm định để công bố” | hiển thị AI-draft như sự thật |
| Nguồn còn tranh luận | phân nhóm các lập luận/căn cứ và mức chắc chắn | ép một kết luận đơn nhất |
| Source update during lesson | giữ release đang học, thông báo phiên bản mới | âm thầm đổi đáp án chuẩn |
| Offline draft | “Đã lưu trên thiết bị, chưa gửi lên hệ thống” | success toast “đã nộp” |
| Submit succeeds | receipt server + timestamp | chỉ căn cứ toast client |
| Submit fails | lỗi rõ, retry giữ idempotency key | tạo điểm/số hồ sơ giả |
| Rights withdrawn | placeholder và fallback có quyền | sử dụng cache cũ bất chấp thu hồi |
| AI insufficient evidence | câu trả lời từ chối suy diễn + nguồn gợi ý | dựng citation tưởng tượng |

### B5.4 Accessibility acceptance WCAG-oriented (TARGET)

Keyboard toàn bộ flow, focus order hợp lý, visible focus, labels form rõ, alt text phân biệt observation vs interpretation, captions cho video/audio, không phụ thuộc màu, screen reader announcement cho step changes, có tùy chọn giảm motion, contrast đạt ngưỡng WCAG 2.2 AA khi phù hợp, viewport 320px không mất thông tin. 3D hotspots có danh sách text đồng bộ, AR có fallback hình 2D với nhiệm vụ tương đương; đánh giá task completion trong các trường hợp không thiết bị hỗ trợ.

### B5.5 Mobile Flutter parity contract

Không bắt Flutter có toàn bộ editor/admin feature. Student mobile tối thiểu phải xem hồ sơ di sản có dẫn nguồn, 2D fallback, nhận assignment, lưu nháp an toàn, nộp khi kết nối, nhận feedback. Parity matrix có trạng thái `web-only`, `mobile-supported`, `mobile-deferred` cho từng route, không dùng cùng tên tính năng để che thiếu chức năng. Store draft bảo vệ thiết bị và clear khi logout; migrate schema offline theo app version; conflict banner khi bài học được cập nhật.

---

