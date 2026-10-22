# V5.12 — GOOGLE_FORMS_ANALYTICS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.12`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.12 — DATA RESEARCH VS STARTUP ANALYTICS: PHẢI TÁCH

### 12.1. 1.502 Google Forms

Khoảng 1.502 phản hồi từ 6 trường là **survey tự báo cáo về nhận thức, mong muốn và cảm nhận**. Nhóm có thể giữ Google Forms gốc; khi xuất file, phải khử định danh, chuẩn hóa câu hỏi, metadata về học sinh, thời gian thu thập và số thiếu. Tài liệu nghiên cứu Q2/HCMUS có thể mô tả người dùng ưa thích công nghệ nhưng không được tuyên bố tăng historical reasoning nếu chưa có bài kiểm tra khách quan. Chưa thể dự đoán CAC, paying customers, revenue từ dataset đó.

### 12.2. Research system riêng

Tạo `study`, `instrument_version`, `survey_import_batch`, `variable_codebook`, `response_anonymized`, `analysis_run`, `dataset_fingerprint`, `ethics_approval_ref`, `publication_claim`. Raw identifier/phụ huynh thông tin để kho riêng, role restricted; chỉ import data hợp pháp. Mọi bảng nghiên cứu phải có query/codebook có thể tái lập, không tự điều chỉnh số lượng phản hồi trùng sau khi nhìn kết quả. Nếu cần nghiên cứu học tập sâu, pre-register outcomes and ethics before new data collection.

### 12.3. Product analytics riêng

Tách events platform (usage, error, inquiry), direct learning assessment (teacher-reviewed), sales (verified completed), product survey (consented). Không gộp các định nghĩa vì có thể gây double-counting hoặc vi phạm mục đích thu thập thông tin.

### 12.4. Data dictionary bản nộp nghiên cứu

`question_id`, `question_text_vi`, `question_text_en`, `response_type`, `allowed_options`, `multiple_max`, `skip_logic`, `respondent_count`, `nonresponse_count`, `source_form_version`, `school_id_if_permitted`, `collection_period`, `ethics_status`, `analysis_sql_or_notebook`, `table_number`, `publication_version`. Validate đặc biệt: số lượt chọn dạng tối đa 3 bằng 4506 (3×1502) và câu biết di sản so với 812 lượt qua SGK; giữ nguyên bảng gốc nhưng yêu cầu human verification nguyên văn/logic rẽ nhánh.

