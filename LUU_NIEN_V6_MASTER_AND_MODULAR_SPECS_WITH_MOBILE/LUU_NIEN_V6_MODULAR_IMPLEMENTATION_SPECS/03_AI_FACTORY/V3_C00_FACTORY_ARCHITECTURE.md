# V3.C0: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C0`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C0. Ràng buộc hệ thống, bất biến và nguồn gốc code

### C0.1. Điểm neo hiện trạng trong repository (đã đọc ZIP)

| Nguồn trong branch | Trạng thái | Ranh giới tích hợp V3 |
|---|---|---|
| `backend/history_models.py`: `HistoricalEntity`, `HistoricalSource`, `HistoricalClaim`, `HistoricalClaimSource`, `HistoricalAsset`, `HistoricalContentAuditLog`, `HistoryStory` | `[CODE]` | Reuse primary keys và claim–source relations; **mở rộng additive migrations**, không viết đè bảng đã có một cách phá tương thích. |
| `backend/services/history_tutor.py`: nguồn từ `HistoricalClaim` và `HistoricalSource`, nhãn `expert_verified`/`editor_reviewed` | `[CODE]` | Chỉ tạo retrieval release từ nội dung phê duyệt; tách **AI research ingestion** khỏi **public tutor**. |
| `backend/routers/history.py`: quản lý entity/source/claim, linking/review | `[CODE]` | Chỉ dùng business service và phân quyền hiện hành; tạo admin `research_factory` router riêng cho pipeline. |
| `backend/routers/ai.py` và `backend/routers/admin.py` có `is_ai_generated` cho lesson | `[CODE]` | Phân biệt `ai_draft` / `human_edited` / `expert_approved`, ghi process provenance theo version nội dung. |
| `backend/services/heritage_import.py`, `data/heritage-hue/*.yaml` | `[CODE/DATA]` | Không đồng nhất nguồn Cửu Đỉnh với hạng mục thành phần di sản khác; tuân thủ content scope và media rights. |
| 162 bản ghi JSON và 162 ảnh được kiểm trong V2; `is_ai_generated` trên JSON | `[DATA/STATIC-VERIFIED]` | Chỉ dùng seed cũ làm inventory/candidate, không coi toàn bộ mô tả seed là sự kiện đã chứng minh. |
| `backend-rust` gateway và `frontend` Next.js | `[CODE]` | Orchestrator chạy nội bộ Python worker; Rust chỉ proxy route đã kiểm soát; frontend chỉ admin console riêng. |

### C0.2. Mười hai quy tắc bất biến không được phá

1. **Source-first:** Một kết luận sử học không được xuất ra công khai nếu không có tối thiểu một `source_snapshot_id` hợp lệ và `locator` xác minh được, trừ khi hiển thị nguyên văn nhãn `unverified hypothesis` trong khu vực nội bộ.
2. **Quote-first & non-fabrication:** Trích đoạn được giữ nguyên có phiên bản, vị trí và checksum; AI không tự tạo quote, DOI, trang sách, chữ Hán, bản dịch hoặc tên hiện vật.
3. **Evidence diversity:** Hai bài sao chép một nguồn gốc không tính là hai nguồn độc lập; ghi `derives_from`/citation lineage để đánh giá độc lập.
4. **Adversarial separation:** Agent biên soạn không được phê duyệt nội dung nó tạo; review agents có prompt/model release độc lập nếu khả thi; người thật có quyền phủ quyết.
5. **Immutable lineage:** Từ câu công khai luôn truy ngược được `published_block → draft_revision → claim_revision → excerpt/locator → source_snapshot → acquisition_event`.
6. **Rights-aware:** Phát hiện tài liệu không có nghĩa có quyền tải, OCR, lưu toàn văn, huấn luyện mô hình hoặc công bố trích đoạn; phân biệt các quyền này theo từng nguồn.
7. **Hán–Nôm human gate:** OCR/AI transcription, phiên âm, dịch nghĩa chỉ ở trạng thái gợi ý khi chưa được người có chuyên môn đối chiếu với ảnh/ấn bản.
8. **No hallucinated certainty:** Không gộp quan sát trực tiếp với giải thích biểu tượng; mỗi mệnh đề có risk/confidence/support status; nguồn mâu thuẫn phải được bảo tồn trong hồ sơ.
9. **Never silently overwrite:** Nội dung gốc, bản được người duyệt, phiên bản hiện hành và bản AI mới tách riêng; một rerun không được ghi đè bài đã xuất bản.
10. **Least privilege:** Agent không có quyền trực tiếp `publish`, thay đổi quyền, sửa consent hoặc đọc dữ liệu học sinh; chỉ tạo artefact draft/quarantine trong phạm vi nhiệm vụ.
11. **Fail closed:** Quota provider, lỗi mạng, trích dẫn không tìm thấy, giấy phép chưa rõ hoặc mất một worker quan trọng đều ngăn release; không tự động thay bằng dữ liệu mô phỏng.
12. **Research honesty:** Chất lượng nội dung AI, độ chính xác sử liệu, kết quả survey và learning outcomes là các biến khác nhau; không suy từ 1.502 phản hồi cảm nhận sang mức tăng học tập hay độ chính xác AI.

### C0.3. Định nghĩa đầu ra bắt buộc cho *mỗi* bản đúc nổi

`ReliefResearchBundle` gồm (a) identity 9×18 + alias, (b) ảnh hiện vật/crop đã kiểm quyền, (c) ấn bản/nguồn và phiên bản, (d) passage có locator, (e) claims atomic kèm mức chắc chắn, (f) đối chiếu và bất đồng, (g) bản giới thiệu ngắn/dài tiếng Việt, (h) bản song ngữ tiếng Anh đã kiểm tra bản dịch, (i) ghi chú chữ Hán–Nôm nếu có nguồn đúng, (j) nội dung thuyết minh, timeline/map phù hợp, (k) nguồn tham khảo người dùng xem được, (l) câu hỏi ELLO/LMS/rubric, (m) phần 2D/3D/AR phụ trợ nếu có tài sản đã duyệt, (n) trắc nghiệm + đáp án/chứng cứ, (o) trạng thái rights/review/version, (p) machine-readable provenance và export. **Không ép sinh đủ mục khi thiếu nguồn**: trường chưa đủ thông tin phải hiển thị `MISSING_EVIDENCE` và có nhiệm vụ bổ sung.

### C0.4. Semantic distinction: tự động soạn nội dung != tự động tạo sự thật

- `AUTO_DISCOVER`: tìm candidate có metadata; nguồn chưa được xem nội dung.
- `AUTO_EXTRACT`: trích đoạn máy đọc từ snapshot hợp pháp; phải kiểm quality/locator.
- `AUTO_INFER_DRAFT`: AI đề nghị claim/synthesis; không mặc định đúng.
- `AUTO_WRITE_DRAFT`: AI viết đủ các section của hồ sơ; **chỉ nội bộ**.
- `HUMAN_VERIFIED`: reviewer đã kiểm nguồn–câu–bản dịch và quyền, lưu chữ ký.
- `PUBLISHED`: release immutable chỉ chứa section đủ điều kiện.
- `REVOKED`: quyền hoặc bằng chứng rút lại, ảnh hưởng toàn bộ claims/docs/retrieval index.

---
