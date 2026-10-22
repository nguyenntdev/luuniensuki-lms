# V2 B8: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B8`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B8. TRUSTWORTHY AI + CALL (ĐIỀU KIỆN), KHÔNG LẤY DEMO LÀM BẰNG CHỨNG

### B8.1 Retrieval/evidence provenance

Index only claim revisions approved for relevant audience+scope. Chunk contains `source_id`, locator, claim_id, claim_version, reviewer status, source language, timestamp, rights, content hash. Use retrieval filters before vector ranking; no private notes or student responses in embedding corpus without documented basis. A claim revoked triggers index invalidation; retrieval release hash ties to AI evaluation run.

### B8.2 Evaluation dataset composition

Gold set cần bao gồm: câu hỏi đơn nguồn; nhiều nguồn tương thích; nguồn mâu thuẫn; câu hỏi không có chứng cứ; sai tên đỉnh; yêu cầu phiên dịch chữ Hán chưa duyệt; prompt injection embedded in source; multi-turn context shift; query ngoài collection; hỏi về quyền/giấy phép; câu chứa dữ liệu cá nhân; hỏi nội dung liên quan người chưa thành niên. Người gán nhãn lịch sử đối chiếu từng câu trả lời với locator, không dùng AI tự chấm hoàn toàn. Nếu dùng LLM-as-judge, phải kiểm calibration với gold human labels.

### B8.3 AI metrics và release thresholds (TARGET; chỉ được claim sau đo)

| Metric | Định nghĩa | Target pilot đề xuất | Khi fail |
|---|---|---|---|
| Citation validity | câu trích tồn tại đúng source locator/version | >= 99% trên curated eval | chặn phát hành feature |
| Unsupported assertion rate | mệnh đề thực chứng không đủ nguồn / tổng mệnh đề | <= 2% trên gold evaluation | strengthen abstain/context |
| Correct abstention | không đủ nguồn -> không bịa | >= 95% trên no-evidence cases | disable answer, suggest sources |
| Scope violation | trích tài liệu ngoài content scope | 0 trong security suite | P0 fix |
| Prompt injection obedience | thực thi lệnh trong tài liệu không tin | 0 trong red-team fixtures | P0 fix |
| Median/95p latency | request end-to-end on target infra | target by deployment budget | optimize/reduce payload |
| Human dispute reconciliation | tỷ lệ disagreements adjudicated | 100% trước freeze paper | chưa báo cáo chính thức |

**Cẩn trọng:** ngưỡng là tiêu chí kỹ thuật đề xuất, không là số đã đạt hoặc bằng chứng zero hallucination ngoài phân bố kiểm thử.

### B8.4 Teacher AI assistant

Cho phép AI đề xuất câu hỏi, nguồn cần đọc, rubric draft và chú giải 2D/3D; mọi gợi ý có nhãn `AI_DRAFT`, đi qua review trước publish. Không cho phép AI tự duyệt hoặc tự chấm tổng kết mà không có protocol/validation. Human-in-the-loop audit log ghi prompt template version, retrieved sources, teacher accept/edit/reject (không lưu PII không cần thiết).

### B8.5 CALL Extension: không biến đọc sử liệu thành bài báo dạy ngoại ngữ một cách danh nghĩa

Cần xác định **đối tượng ngôn ngữ**: đọc hiểu tiếng Anh, thuật ngữ văn hóa, hoặc Hán–Nôm có chuyên gia (không xem chữ Hán là tiếng Anh). Thiết kế objective measurable theo CEFR hoặc framework phù hợp, task theo năng lực, feedback ngôn ngữ và assessment. Nếu chỉ trình diễn technology showcase, gọi rõ case demo, không claim học ngôn ngữ tốt hơn nếu chưa đánh giá.

**Mẫu lesson CALL (đề xuất mới, chưa triển khai):** nguồn đoạn giới thiệu di sản tiếng Anh đã duyệt -> học từ vựng lịch sử -> nhiệm vụ đọc hiểu infer meaning from context -> chọn evidence phrase -> phản hồi bằng rúbric language comprehension. Phần Hán–Nôm cần image crop, original transcription, phiên âm, dịch, rater chuyên môn; tuyệt đối không hiển thị ký tự seed AI chưa duyệt làm bản chữ gốc.

**CALL-specific metrics:** pre/post reading item score nếu có nghiên cứu; productive vocabulary accuracy; comprehension transfer; pronunciation chỉ khi hệ thống có chức năng phù hợp; completion/engagement là phụ trợ. Không lấy 94% mong muốn xem 3D để suy ra thành tích ngoại ngữ.

---

