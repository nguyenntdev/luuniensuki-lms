# V2 B7: source-derived engineering detail

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V2.B7`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## B7. PIPELINE NGHIÊN CỨU 1.502 GOOGLE FORMS — REPRODUCIBILITY WITHOUT OVERCLAIMING

### B7.1 Tài liệu cần thu từ nhóm nghiên cứu (ngoài ZIP)

(1) Bản xuất CSV/XLSX gốc đã lọc PII; (2) bản sao mẫu Google Forms có tiêu đề và lựa chọn từng mục; (3) cấu hình chọn đơn/nhiều/rẽ nhánh; (4) thời gian thu thập và trường tham gia; (5) cách mời học sinh/cơ chế đồng ý; (6) quy tắc loại bản ghi; (7) bảng tổng hợp được đưa vào bài; (8) giải thích về hai nhóm câu hỏi (thực trạng và đánh giá), liệu cùng cohort; (9) sản phẩm/phiên bản học liệu và thời gian tiếp xúc thực tế; (10) ai phụ trách duyệt dữ liệu. Không cần công bố raw file cho toàn xã hội nếu vi phạm quyền riêng tư.

### B7.2 ETL 12 bước có nhật ký

1. File received -> virus scan + encrypted store; 2. SHA-256; 3. read spreadsheet as data, no spreadsheet macros/formulas; 4. detect encoding/timezone/headers; 5. map question wording to immutable item IDs; 6. parse responses with multi-select escaping; 7. identify empty/duplicate candidates without xóa tự động; 8. pseudonymize & separate linkage key; 9. validate range, category, skip logic; 10. generate item frequencies and missingness; 11. compare against 1,502 figures, log difference reason; 12. freeze analysis release with dictionary+code+counts.

### B7.3 Data dictionary schema template

| Field | Example | Quy tắc |
|---|---|---|
| `item_id` | `AWARENESS_RELIEF_01` | stable independent of displayed question text |
| `original_question_vi` | verbatim from form | không diễn giải lại khi mapping |
| `response_type` | `single_choice`, `multi_choice`, `scale`, `text` | determines denominator and validation |
| `options` | coded id + literal Vietnamese | giữ gốc và nhãn hiện tại riêng |
| `allowed_max_choices` | 3 or null | dùng kiểm 4,506 lượt chọn |
| `skip_logic` | JSON predicate | giải thích N từng mục |
| `analysis_group` | awareness/preferences/appraisal | group không đồng nghĩa timepoint |
| `missing_code` | skipped/blank/unknown/import_error | tách missing mechanisms |
| `positive_grouping` | list coded options | aggregate “muốn+rất muốn” reproducibly |

### B7.4 Tái lập các bảng bằng công thức công khai

Với item `j`, `N_j = n_valid_j` phải được kiểm từ dữ liệu gốc; tỷ lệ `p_jk = 100*n_jk/N_j`. Bản thảo trước dùng mẫu số báo cáo `1502`; nếu có item missing thì công bố cả `N_j` thực tế và cách xử lý. Câu multi-select: mỗi đáp án được tính số người chọn riêng, không dùng tổng lượt tick làm denominator. Cần xử lý option “other” đúng encoding và tránh split chuỗi nếu dấu phẩy là một phần nhãn.

**Bảng kiểm số liệu paper** (điều kiện `N_j=1502` phải kiểm):

| Item | Expected count | Expected % 1 digit | Phân tích hợp lệ |
|---|---:|---:|---|
| never heard/studied selected reliefs | 958 | 63.8 | nhận biết được tự báo cáo |
| wanted/strongly wanted digital access | 1412 | 94.0 | ý định/ưu tiên |
| interested/very interested newer formats | 1308 | 87.1 | quan tâm được tự báo cáo |
| content interesting/very interesting | 1413 | 94.1 | thái độ với nội dung |
| self-assessed understanding clear/very clear | 1420 | 94.5 | *perceived* understanding, không phải bài test |
| school implementation effective/very effective | 1435 | 95.5 | *perceived* effectiveness |
| awareness/pride perceived increased | 1465 | 97.5 | cảm nhận thay đổi, không chứng minh actual change |
| willing to share | 1393 | 92.7 | willingness, không phải hành vi chia sẻ |

### B7.5 Kiểm toán 2 anomaly đã phát hiện

**A. 4.506 selections:** với câu cho tối đa 3 lựa chọn, `1350+1250+1220+686=4506=3*1502`; khi load Google Forms, cần đếm selection_count theo participant, histogram `0/1/2/3/>3`, số `other`, số skip, số bản ghi trống và các phương án ẩn. Nếu tất cả chọn 3, kết quả hoàn toàn khả dĩ; nếu không, xác định nguồn lệch từ formula/tổng hợp. Không tự sửa số để khớp.

**B. Awareness vs channel:** item 544 prior heard/studied reliefs và 812 textbook contacts không nhất thiết conflict; đối chiếu nguyên văn (relief vs Cửu Đỉnh chung), skip logic, population/timepoint. Không tạo “tỷ lệ đã biết” mới từ tổng lượt chọn nguồn thông tin.

### B7.6 Phân tích bổ sung có điều kiện

Có respondent-level, school, grade: có thể kiểm mô tả theo nhóm và liên hệ giữa nhận biết/sở thích/cảm nhận (chi-square, ordinal methods khi điều kiện phù hợp); lưu ý cluster by classroom/school và cách lấy mẫu. Không khẳng định khả năng đại diện chỉ từ N=1,502; không chạy Cronbach alpha nếu câu hỏi thuộc nhiều constructs độc lập, chưa chứng minh cùng thang. Nếu có hai thời điểm khảo sát mà không có mã ghép/cùng item/điều kiện exposure, không gọi paired pre/post. Không dùng Fisher/ANOVA/SEM vì tên gọi “Q2” nếu không phục vụ câu hỏi và thang đo.

### B7.7 Khung công bố bảng và phát hiện

Dataset `research_release_YYYYMMDD` chỉ chứa aggregate; bảng tần số cần có `item_id`, verbatim wording, response categories, numerator, denominator, missing, survey window, cohort definition. Một câu kết luận phải map tới `analysis_snapshot_id`, script hash và đúng figure/table trong bài. Để external reviewer tái lập trong điều kiện không thể chia sẻ raw minor data, công bố data dictionary, mã tổng hợp, aggregate outputs và toy/synthetic data (gắn nhãn synthetic).

### B7.8 Giao thức nghiên cứu kết quả học tập sau này (không hồi tố khảo sát)

- Định nghĩa primary outcome trước: chất lượng lập luận dựa trên nguồn theo rubric 0–x với các mức mô tả rõ, không lấy Likert self-report làm điểm đạt kiến thức.
- Thiết kế 2D vs guided 3D/AR có thời lượng, nội dung, hướng dẫn tương đương; nếu randomize ở lớp, sample size dựa số lớp/ICC chứ không chỉ số học sinh.
- Có baseline về historical reasoning, nhiệm vụ transfer trên hiện vật chưa học, delayed assessment; giáo viên/rater được blinded khi có thể.
- Rubric được expert-review, thử trước và sau đó mới tính inter-rater agreement; định nghĩa protocol cho bất đồng điểm.
- Đạo đức, quyền sử dụng tư liệu, consent/assent và công khai protocol phải xác minh trước triển khai.
- Nếu báo cáo chỉ acceptance/usability, dùng đúng nhãn nghiên cứu và không claim causal knowledge gain.

### B7.9 Ma trận hồ sơ bằng chứng phục vụ hội nghị/paper

| Paper | Dataset snapshot | Product snapshot | Chỉ số được phép báo | Chỉ số cần nghiên cứu mới |
|---|---|---|---|---|
| Q2 EN/VI | verified 1,502 aggregate | ELLO/six-step release | awareness/preferences/perceptions | historical reasoning increase |
| HCMUS | cùng survey, cite reuse | demo 3D/AR/LMS snapshot | perceptions with disclaimers | comparison learning gains |
| ICTIM | 1,502 chỉ là student context | experience/atlas/interpretation | student preferences | tourist satisfaction/visitor conversion |
| GLoCALL | current dataset không đo language outcome | CALL lesson mới | design showcase nếu đúng scope | vocab/reading gains |
| ICETAI | current survey không đánh giá AI | new AI corpus/eval set | AI groundedness measured if conducted | AI learning impact nếu không có experiment |
| EAUT | architectural docs/code | reproducible deploy benchmark | measured architecture properties | nationwide efficacy/scalability untested |

---

