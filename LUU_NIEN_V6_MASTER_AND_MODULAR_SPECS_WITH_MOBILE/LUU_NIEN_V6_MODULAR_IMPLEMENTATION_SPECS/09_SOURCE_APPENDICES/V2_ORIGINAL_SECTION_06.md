# V2 original archival technical chapter — SECTION_06

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 6. SOURCE-LINKED LEARNING OBJECT — ELLO v1 (CORE PAPER)

### 6.1 Cấu trúc bắt buộc

`ELLO = identifiable_object + question + provisional_claim + media_representation + source_packet + inquiry_sequence + student_artifact + feedback_rubric + accessibility_route + version_manifest`.

Một ELLO được tái dùng theo lớp/khối/giáo viên; mỗi publication tạo `ello_version` immutable. Dùng chính Historical Entity/Claim/Source, không copy đoạn văn tự do vào bài mà không có identity; override của giáo viên phải có version lineage và không ảnh hưởng authority record.

### 6.2 Sáu bước của bài Q2 được chuyển thành chức năng

| Step | UX phải có | Data/API | Learning artifact | Acceptance |
|---|---|---|---|---|
| 1 Identify Object | ảnh, ID, vị trí, tên Hán/VI, trạng thái kiểm chứng | `GET /learning-objects/{id}` | `observation_draft` | chỉ item publish; 2D accessible |
| 2 Formulate Claim | ô giả thuyết ban đầu; nhãn “suy luận” | `POST /inquiry-attempts/{id}/claim` | claim bản 0 | phân biệt observation/inference |
| 3 Consult Source | source drawer, citation locator, competing interpretations | `GET /source-packets/{id}` | source annotations | điểm nguồn hợp lệ khi link đúng |
| 4 Representation | 2D/zoom/3D/AR theo mục tiêu | `GET /media/variants` | media log tối thiểu | không khóa chỉ AR, giảm tải |
| 5 Inquiry Task | so sánh, lập luận, trích chứng cứ | `POST /responses` | CER answer + selected citations | trả về rubric-ready |
| 6 Feedback/Revise | nhận phản hồi giáo viên/AI limited, sửa bài | `POST /revisions` | revision history | không overwrite version cũ |

Các bước thể hiện **logic thiết kế**; học sinh có thể quay lại nguồn/nhận định nhiều lần. UI không được cưỡng ép một tuyến một chiều thiếu quyền sửa; tất cả nhánh có thể được giáo viên cấu hình.

### 6.3 Authoring workflow

`DRAFT → SOURCE_CHECK → PEDAGOGICAL_REVIEW → ACCESSIBILITY_CHECK → TEACHER_PILOT → APPROVED → PUBLISHED → ARCHIVED`.

- author chọn motif và mục tiêu chương trình;
- hệ thống kiểm cited claims và bản quyền;
- teacher viết objectives theo hành động quan sát/so sánh/lập luận;
- subject reviewer xác nhận không có historical overclaim;
- lesson preview bằng thiết bị yếu và screen reader;
- test rubric trước khi chấm;
- đóng gói version manifest cho nghiên cứu.

### 6.4 Rubric trực tiếp đo historical reasoning

| Tiêu chí | Điểm | 0 | Trung bình | Mức tốt |
|---|---:|---|---|---|
| Nhận biết hiện vật | 0–2 | không xác định | đúng tên nhưng thiếu vị trí | đúng ID/vị trí và bối cảnh |
| Quan sát đối tượng | 0–2 | không có chi tiết | 1 chi tiết thiếu cụ thể | ≥2 chi tiết mô tả trực tiếp |
| Đối chiếu nguồn | 0–3 | không nguồn | nguồn có nhưng liên hệ yếu | nguồn có locator và phù hợp |
| Lập luận | 0–3 | kết luận vô căn cứ | nêu claim + evidence nhưng thiếu warrant | giải thích quan hệ + giới hạn |
| **Tổng** | **0–10** |  |  |  |

Rubric **chưa được chuẩn hóa tâm trắc**; đây là thiết kế cho pilot. Chấm mù điều kiện khi nghiên cứu, ít nhất hai người chấm một mẫu bài đủ lớn; lập thỏa thuận mã hóa và đo inter-rater reliability thích hợp. `self_assessment` là trường riêng, không chấm là `historical_reasoning_score`.

### 6.5 Bài học mẫu 45 phút (mẫu chưa xác minh claim lịch sử)

- 0–5': kích hoạt câu hỏi về bản đúc nổi chọn từ kho được duyệt; nêu quan sát chưa diễn giải.
- 5–12': 2D ảnh + xác định chi tiết; tải 3D tùy chọn nếu mục tiêu cần góc nhìn/quan hệ không gian.
- 12–20': mở hai nguồn có citation locator, phân loại nguồn gốc và điểm có thể kiểm chứng.
- 20–30': học sinh lập CER (`claim`, `evidence`, `reasoning`) từ câu hỏi cụ thể.
- 30–40': đối chiếu phản hồi, sửa câu trả lời; giáo viên nêu uncertainty và quan điểm khác.
- 40–45': exit ticket và lưu bản chấm/rubric + self-report tách rời.

Không dùng bài mẫu này trong phần Method của bài hiện tại như một giờ dạy đã thực nghiệm nếu chưa triển khai đúng giao thức.

---

