# Các tính năng mới dựa trên research EdTech (2024-2026)

Ngày cập nhật: 2026-04-16

## Giải nghĩa thuật ngữ (bản dễ hiểu)

- `AR-CH` (Augmented Reality for Cultural Heritage): Thực tế tăng cường cho di sản văn hóa.
- `AR` (Augmented Reality): Thực tế tăng cường (chèn lớp thông tin số lên hình ảnh thật).
- `MR` (Mixed Reality): Thực tế kết hợp (trộn vật thể ảo và không gian thật để tương tác).
- `XR` (Extended Reality): Thuật ngữ chung cho AR/VR/MR.
- `ITS` (Intelligent Tutoring System): Hệ thống gia sư thông minh.
- `SRL` (Self-Regulated Learning): Tự điều chỉnh học (tự đặt mục tiêu, tự theo dõi, tự điều chỉnh).
- `Guardrails`: Hàng rào an toàn sư phạm (không để AI “làm hộ” quá mức).
- `Adaptive scaffolding`: Gợi đỡ theo ngữ cảnh và đúng thời điểm.
- `Meta-analysis`: Phân tích gộp nhiều nghiên cứu để rút kết luận tổng quát.
- `RCT` (Randomized Controlled Trial): Thử nghiệm đối chứng ngẫu nhiên.
- `A/B test`: Chia người học thành 2 nhóm để so sánh phiên bản A và B.
- `KPI`: Chỉ số đo hiệu quả.
- `Cohort`: Nhóm người học cùng đặc điểm (ví dụ nhóm mới, nhóm học yếu, nhóm nâng cao).

## 1) Tóm tắt ngắn

Nếu mục tiêu là “cái mới” nhưng phải có bằng chứng nghiên cứu, 7 hướng sau đáng ưu tiên cho Luuniensuki LMS theo trọng tâm giáo dục di sản:

1. Gia sư AI thuyết minh di sản hai chế độ: `hint-first` mặc định + `direct answer` có kiểm soát.
2. Cảnh báo sớm “đứt mạch hành trình di sản” từ tín hiệu LMS (risk alert + can thiệp sớm).
3. SRL Copilot cho hành trình di sản (lập kế hoạch khám phá, tự theo dõi, phản tư).
4. Lộ trình thích ứng theo hồ sơ người học và cụm tri thức di sản (đỉnh/họa tiết/chủ đề).
5. Chatbot text-first chuyên biệt di sản, phiên học đủ dài, bám nguồn tư liệu.
6. Ôn tập nhắc lại ngắt quãng theo cụm di sản (không áp dụng cứng cho mọi nội dung).
7. AR-CH/MR micro-missions cho học di sản tại điểm chạm (nhiệm vụ ngắn tương tác không gian).

## 2) “Mới” ở đây là gì?

Không chỉ thêm tính năng AI. “Mới” theo research EdTech là:

- Thiết kế can thiệp theo cơ chế học (learning mechanism), không theo trend.
- Tất cả thay đổi đều có giả thuyết đo lường được.
- Triển khai bằng A/B test hoặc RCT ngay trong môi trường thật.

## 3) 7 đề xuất cụ thể

## 3.1 Guardrailed Heritage Tutor (gia sư di sản có hàng rào an toàn, mặc định gợi ý từng bước)

### Research signal

- RCT 2025 cho thấy gia sư AI thiết kế sư phạm tốt có thể tăng tốc độ học và tăng mức gắn kết.
- Nghiên cứu PNAS 2025 cho thấy dùng AI không có hàng rào an toàn có thể làm giảm năng lực tự học khi bỏ AI; cơ chế gợi ý từng bước giúp giảm hại.

### Thiết kế tính năng mới

- Mặc định: AI chỉ đưa gợi ý từng bước, câu hỏi dẫn dắt, không đưa đáp án ngay.
- Cho phép mở khóa “direct answer” theo điều kiện (ví dụ đã thử 2 lần).

### Cắm vào hệ hiện tại

- Mở rộng `/api/v1/ai/tutor`, `/api/v1/ai/tutor/stream` với `tutor_mode`.
- Log event vào `/api/v1/experiments/{experiment_key}/events`.

### KPI (chỉ số đo hiệu quả)

- `post_quiz_without_ai_score`, `hint_dependency_rate`, `retry_success_rate`.

---

## 3.2 Heritage Journey Risk Alert + Proactive Advising

### Research signal

- Nghiên cứu thực nghiệm 2026 (The Internet and Higher Education) cho thấy tín hiệu LMS đơn giản + tư vấn chủ động giúp tăng điểm và retention.

### Thiết kế tính năng mới

- Tạo “risk score nhẹ” theo tín hiệu đứt mạch: không quay lại họa tiết đã mở, bỏ dở quiz, giảm tần suất học.
- Dashboard hiển thị cảnh báo sớm + khuyến nghị hành động 5 phút theo đúng phần di sản đang dang dở.

### Cắm vào hệ hiện tại

- Dùng dữ liệu từ `dashboard summary`, `learning-path`, `quiz` events.
- Tạo job hàng ngày + card “At-risk nudge” trên Learning Hub.

### KPI (chỉ số đo hiệu quả)

- `d7_return_rate`, `at_risk_recovery_rate`, `course_completion_rate`.

---

## 3.3 SRL Copilot cho hành trình di sản

### Research signal

- Meta-analysis 2025 (Computers & Education) cho thấy các chiến lược tự điều chỉnh học (siêu nhận thức, quản lý thời gian, duy trì nỗ lực...) liên quan tích cực tới thành tích.

### Thiết kế tính năng mới

- Trước phiên học: mục tiêu 15 phút + chọn chủ đề di sản cần chinh phục.
- Trong phiên: nhắc checkpoint ngắn (“bạn đang hiểu đến đâu?”).
- Sau phiên: reflection 30 giây + kế hoạch ôn lại theo họa tiết/đỉnh vừa học.

### Cắm vào hệ hiện tại

- Layer mới trên `learning-path/today` và `practice/results`.
- Lưu “kế hoạch tự điều chỉnh học” theo ngày trong hồ sơ học tập.

### KPI (chỉ số đo hiệu quả)

- `plan_completion_rate`, `time_on_task`, `reflection_completion_rate`, `d7_retention`.

---

## 3.4 Adaptive Heritage Pathway theo điều kiện hiệu quả

### Research signal

- Meta-analysis 2024 về AI-enabled adaptive learning systems báo cáo hiệu quả dương mức trung bình-lớn (g ≈ 0.70), nhưng phụ thuộc moderator (độ dài can thiệp, cấp học, môn...).
- Meta-analysis GenAI 2025 ghi nhận dị hợp rất cao giữa bối cảnh (heterogeneity lớn).

### Thiết kế tính năng mới

- Không dùng 1 policy chung cho toàn bộ nội dung di sản.
- Mỗi phân khúc người học có policy khác theo cụm tri thức di sản (ví dụ: biểu tượng, địa lý, văn hóa cung đình).

### Cắm vào hệ hiện tại

- Nâng cấp service `learning-path/generate` với chính sách theo từng nhóm người học (cohort).
- Rollout bằng feature flags + experiments sẵn có.

### KPI (chỉ số đo hiệu quả)

- `path_completion_rate`, `mastery_velocity`, `variance_reduction_between_cohorts`.

---

## 3.5 Chatbot thuyết minh di sản: text-first, task-first

### Research signal

- Meta-analysis 2025 (Learning and Individual Differences) cho thấy chatbot có hiệu quả dương nhỏ-vừa sau hiệu chỉnh bias; text-based thường tốt hơn speech-based; can thiệp dài hơn cho hiệu quả tốt hơn.

### Thiết kế tính năng mới

- Ưu tiên chat text theo nhiệm vụ di sản cụ thể (giải thích biểu tượng, so sánh họa tiết, đặt câu hỏi kiểm tra hiểu biết).
- Bắt buộc trích dẫn nguồn nội bộ theo hiện vật/bài học, tránh chat mở không mục tiêu.

### Cắm vào hệ hiện tại

- Dùng lại AI Hub nhưng thêm “task templates” bám lesson/quiz.
- Chạy phiên dài có checkpoint thay vì one-shot prompt.

### KPI (chỉ số đo hiệu quả)

- `task_completion_after_chat`, `session_depth`, `quality_rating`.

---

## 3.6 Spaced retrieval theo cụm di sản (không áp dụng cứng)

### Research signal

- Nghiên cứu 2024 trên nhiều môn STEM cho thấy spaced retrieval hứa hẹn, chi phí thấp, nhưng mức hiệu quả khác nhau theo môn và bối cảnh.

### Thiết kế tính năng mới

- Dùng spaced review “mặc định mềm”: bật trước cho cụm di sản phù hợp (đỉnh, họa tiết, chủ đề lịch sử).
- Theo dõi hiệu quả theo từng cụm nội dung di sản, không giả định hiệu quả đồng đều.

### Cắm vào hệ hiện tại

- Tăng cường `/api/v1/review/*` với lịch ôn theo content cluster.
- Dashboard hiển thị “nội dung nào spacing đang hiệu quả với bạn”.

### KPI (chỉ số đo hiệu quả)

- `review_hit_rate`, `forgetting_curve_slope`, `delayed_quiz_gain`.

---

## 3.7 AR-CH/MR Heritage Missions (nhiệm vụ di sản bằng AR/MR)

### Research signal

- Meta-analysis 2025 (Mixed Reality trong giáo dục) báo cáo hiệu quả mức trung bình, nhưng phụ thuộc thời lượng triển khai và hỗ trợ của giáo viên.
- Systematic review 2024 về AR cho di sản văn hóa chỉ ra nhiều ca sử dụng tiềm năng, nhưng phải thiết kế sát bối cảnh địa phương.

### Thiết kế tính năng mới

- Micro-mission AR-CH/MR 3-5 phút: “tìm biểu tượng”, “so sánh hoa văn”, “ghép ngữ cảnh lịch sử”.
- Kết nối trực tiếp mission -> lesson -> quiz item.

### Cắm vào hệ hiện tại

- Mở rộng viewer/quiz với mode nhiệm vụ không gian.
- Log tương tác tọa độ/hotspot để cá nhân hóa học tiếp theo.

### KPI (chỉ số đo hiệu quả)

- `mission_to_lesson_conversion`, `spatial_quiz_accuracy`, `engagement_time`.

## 4) Thứ tự ưu tiên triển khai (theo impact/feasibility)

1. Guardrailed Heritage Tutor
2. Heritage Journey Risk Alert + Proactive Advising
3. SRL Copilot cho hành trình di sản
4. Adaptive Heritage Pathway theo từng nhóm người học (cohort)
5. Chatbot thuyết minh di sản text-first theo nhiệm vụ
6. Spaced retrieval theo cụm di sản
7. AR-CH/MR Heritage Missions

## 5) Thiết kế đo lường khuyến nghị

- Bắt buộc A/B test cho mọi tính năng mới.
- Không dùng một metric duy nhất; tối thiểu gồm: learning gain + retention + behavioral completion.
- Báo cáo theo từng nhóm người học (cohort) để tránh “trung bình đẹp nhưng nhóm yếu bị thiệt”.

## 6) Mapping nhanh vào codebase hiện tại

Các khối đã có sẵn và nên tận dụng:

- AI: `/api/v1/ai/tutor`, `/api/v1/ai/tutor/stream`, `/api/v1/ai/qa`
- Learning path: `/api/v1/learning-path/today`, `/api/v1/learning-path/generate`
- Review: `/api/v1/review/*`
- Experimentation: `/api/v1/experiments`, `/api/v1/experiments/{experiment_key}/events`, `/api/v1/experiments/{experiment_id}/metrics`
- Dashboard summary: `/api/v1/dashboard/summary`

=> Dự án đủ nền để chạy research-to-product nhanh, không cần xây lại từ đầu.

## 7) Nghiên cứu nền cho 7 đề xuất

1. `Guardrailed Heritage Tutor`:
Kestin et al. (2025); Bastani et al. (2025).
2. `Heritage Journey Risk Alert + Proactive Advising`:
Rust & Motz (2026).
3. `SRL Copilot cho hành trình di sản`:
Zhao et al. (2025).
4. `Adaptive Heritage Pathway`:
Wang et al. (2024); Han et al. (2025); Chen & Cheung (2025).
5. `Chatbot thuyết minh di sản text-first`:
Laun & Wolff (2025).
6. `Spaced retrieval theo cụm di sản`:
Bego et al. (2024).
7. `AR-CH/MR Heritage Missions`:
Huang et al. (2025); Ramtohul & Khedo (2024).

## 8) Tài liệu tham khảo (APA 7)

Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakci, O., & Mariman, R. (2025). Generative AI without guardrails can harm learning: Evidence from high school mathematics. *Proceedings of the National Academy of Sciences of the United States of America, 122*(26), e2422633122. https://doi.org/10.1073/pnas.2422633122

Bego, C. R., Lyle, K. B., Ralston, P. A. S., Immekus, J. C., Chastain, R. J., Haynes, L. D., Hoyt, L. K., Pigg, R. M., Rabin, S. D., Scobee, M. W., & Starr, T. L. (2024). Single-paper meta-analyses of the effects of spaced retrieval practice in nine introductory STEM courses: Is the glass half full or half empty? *International Journal of STEM Education, 11*, 9. https://doi.org/10.1186/s40594-024-00468-5

Chen, L., & Cheung, S. K. S. (2025). The impact of generative artificial intelligence on university students' learning outcomes: A meta-analysis. *Educational Research Review, 48*, 100716. https://doi.org/10.1016/j.edurev.2025.100716

Han, X., Peng, H., & Liu, M. (2025). The impact of GenAI on learning outcomes: A systematic review and meta-analysis of experimental studies. *Educational Research Review, 48*, 100714. https://doi.org/10.1016/j.edurev.2025.100714

Huang, T.-C., Chen, C.-H., & Tseng, C.-Y. (2025). Exploring learning effectiveness of integrating mixed reality in educational settings: A systematic review and meta-analysis. *Computers & Education, 234*, 105327. https://doi.org/10.1016/j.compedu.2025.105327

Kestin, G., Miller, K., Klales, A., Milbourne, T., & Ponti, G. (2025). AI tutoring outperforms in-class active learning: An RCT introducing a novel research-based design in an authentic educational setting. *Scientific Reports, 15*, 17458. https://doi.org/10.1038/s41598-025-97652-6

Laun, M., & Wolff, F. (2025). Chatbots in education: Hype or help? A meta-analysis. *Learning and Individual Differences, 119*, 102646. https://doi.org/10.1016/j.lindif.2025.102646

Letourneau, S. M., Lin, S. A. A. Z., Huang, C. C., Singh, S., Dao, D. K., Jackson, C. R., Gasca, S., Gauvin, S., Brookhouse, M., Chen, Y., Ma, A., Murillo-Izquierdo, L. R., Nguyen, M. C., Staller, P. A., Sanders, H. A., ... Reich, J. (2025). A systematic review of intelligent and robot tutoring systems: Evolution, pedagogical design, and AI-driven classification. *npj Science of Learning, 10*(1), 27. https://doi.org/10.1038/s41539-025-00320-7

Ramtohul, A., & Khedo, K. K. (2024). Augmented reality systems in the cultural heritage domains: A systematic review. *Digital Applications in Archaeology and Cultural Heritage, 32*, e00317. https://doi.org/10.1016/j.daach.2024.e00317

Rust, M. M., & Motz, B. A. (2026). Incorporating an LMS learning analytic into proactive advising: Validity and use in a randomized experiment. *The Internet and Higher Education, 68*, 101057. https://doi.org/10.1016/j.iheduc.2025.101057

Wang, X., Huang, R. T., Sommer, M., Pei, B., Shidfar, P., Rehman, M. S., Ritzhaupt, A. D., & Martin, F. (2024). The efficacy of artificial intelligence-enabled adaptive learning systems from 2010 to 2022 on learner outcomes: A meta-analysis. *Journal of Educational Computing Research, 62*(6), 1568-1603. https://doi.org/10.1177/07356331241240459

Zhao, Y., Li, Y., Ma, S., Xu, Z., & Zhang, B. (2025). A meta-analysis of the correlation between self-regulated learning strategies and academic performance in online and blended learning environments. *Computers & Education, 230*, 105279. https://doi.org/10.1016/j.compedu.2025.105279
