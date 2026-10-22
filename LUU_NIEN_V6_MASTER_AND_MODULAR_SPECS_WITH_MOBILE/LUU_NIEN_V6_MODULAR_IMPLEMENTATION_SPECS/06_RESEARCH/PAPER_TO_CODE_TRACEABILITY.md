# Paper-to-code scientific evidence traceability

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.E`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

# PHỤ LỤC V4.E — PAPER-TO-CODE EVIDENCE TRACEABILITY

## Q2-EN/VI: source-based history
- Required feature: Approved 162 relief registry and source-linked inquiry.
- Proof artifact: 162 index + one inspected per-sentence claim chain; version lock.
- Prohibited inference: No claim of increased historical thinking from surveys.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.

## Q2-EN/VI: participant survey
- Required feature: Google Forms analysis pipeline + private deidentified data.
- Proof artifact: CSV/codebook mappings reproduce 1,502 aggregations and missingness.
- Prohibited inference: No fabrication of raw data.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.

## HCMUS poster
- Required feature: Demonstrable 3D/AR/LMS routes where actual.
- Proof artifact: Screenshots from running build + dataset provenance + release commit.
- Prohibited inference: No performance claims from product screenshots.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.

## ICTIM heritage tourism
- Required feature: Visitor/story/rights and tourism-related content only if evidence.
- Proof artifact: Real source-informed cultural interpretation and visitor-specific test if claimed.
- Prohibited inference: School survey not visitor survey.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.

## GLoCALL CALL
- Required feature: Language objectives and assessment items.
- Proof artifact: Pilot language task, rubric and measured language outcomes if claiming gains.
- Prohibited inference: Han-Nom not automatically CALL.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.

## ICETAI AI
- Required feature: Grounded agent corpus, model pin, adversarial benchmarks.
- Proof artifact: Precision/abstention/false citation evaluation with frozen test sets.
- Prohibited inference: No guaranteed zero hallucination.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.

## EAUT architecture
- Required feature: Database API CI migrations rights and scale.
- Proof artifact: Test logs on versioned staging; verified schema and deployment evidence.
- Prohibited inference: Unrun pipeline cannot be called production proven.
- Gate: paper claim cites artifact SHA and version; external reviewers can reproduce aggregate / service tests without access to children's raw PII.


---

# PHẦN NỀN V3 (GIỮ LẠI NGUYÊN VĂN PHẦN AUDIT VÀ 120 ROLES)

# [V3 ARCHIVED SPEC] LƯU NIÊN — CODEBASE AUDIT & FULL-SYSTEM BUILD SPECIFICATION

**Tài liệu duy nhất | Audit + Architecture Decision + Product Requirements + Data Contracts + Research Traceability + Implementation Backlog + Acceptance Criteria**  
**Phiên bản tài liệu:** 3.0 (V1 + V2 + Phụ lục C — AI Research Factory) | **Ngày lập:** 21/10/2026 | **Ngôn ngữ:** tiếng Việt (tên schema/API bằng tiếng Anh)  
**Repository:** `nguyenntdev/luuniensuki-lms` | **Branch ZIP được cung cấp:** `feat/rbpc-cultural-bridge-2026`  
**Định danh ZIP nguồn SHA-256:** `6afbae524382bebfa9675f22a0ea86187a9596ecd5d35bc4727d3a8a80600e31`  
**Commit SHA:** các tài liệu trong ZIP ghi `e19aebc0e7f66f7863659fd658c204739e199687`; **chưa xác minh bằng `.git`** vì GitHub ZIP không chứa lịch sử Git. Không coi SHA ghi trong tài liệu là bằng chứng branch HEAD tại thời điểm tải.

> **Phạm vi và giới hạn kiểm toán:** Đã giải nén và kiểm kê snapshot mã nguồn cụ thể người dùng tải lên; đọc trực tiếp các module quan trọng thuộc frontend, Python, Rust, mobile, cấu trúc dữ liệu, SQLAlchemy models, Alembic revisions, CI/CD, nội dung RBPC và tài liệu dự án; thực hiện kiểm tra cú pháp tĩnh Python/JSON và thử chạy test RBPC. Đây là **audit tĩnh toàn repo kết hợp deep-dive dựa trên rủi ro**, KHÔNG phải chứng nhận đã kiểm thử động tất cả endpoint, scan tất cả lỗ hổng, kiểm chứng cơ sở dữ liệu production hoặc xác nhận mọi claim trong 40 tài liệu RBPC. Những chức năng mô tả trong markdown nội bộ không tự động được xem là đã chạy production.

> **Quy tắc mức bằng chứng:** `[CODE]` hiện diện trong mã nguồn; `[DATA]` có trong snapshot dữ liệu; `[TEST-CODE]` có mã test nhưng chưa chắc đã chạy; `[DOC-CLAIM]` do tài liệu nội bộ tự báo cáo; `[STATIC-VERIFIED]` đã kiểm tra nội dung/cú pháp qua snapshot; `[RUN-BLOCKED]` test không thể chạy do môi trường; `[PLANNED]` chỉ là yêu cầu xây dựng mới; `[NEED-PROOF]` đòi minh chứng bên ngoài hoặc vận hành thực tế. Mọi hạng mục MUST phân biệt trạng thái này trong backlog và trong báo cáo khoa học.


> **Bản mở rộng V2 — 21/10/2026.** Phần đầu giữ nguyên nội dung audit V1 để không mất lịch sử; Phụ lục B bổ sung kiến trúc triển khai có hợp đồng, dòng trạng thái, bảng dữ liệu, API, UI, quy trình survey, an toàn và tickets. Các đoạn TARGET không được diễn giải là tính năng đã tồn tại. Đề xuất này không thay thế việc đọc/rà soát đầy đủ code trong CI/production hoặc xác minh thủ tục nghiên cứu.

---

