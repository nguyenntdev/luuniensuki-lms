# Nghiên cứu công nghệ đột phá để tích hợp vào Luuniensuki LMS (phiên bản 2026)

Ngày cập nhật: 2026-04-16 (trạng thái rà soát: 2026-05-20)

> **Trạng thái:** Tài liệu **đề xuất / roadmap nghiên cứu** — 6 công nghệ dưới đây phần lớn **chưa ship**. Ghi chú thực trạng:
> - 3.3 Guardrailed Tutor (hint-first): **đã có một phần** ở Live AI Teacher (`forced_hint_first`); chưa có `tutor_mode = direct|hint_first|socratic` cho `/api/v1/ai/tutor`.
> - 3.1 Realtime Multimodal Tutor: đã có Live AI Teacher (LiveKit, voice/chat) nhưng chưa có speech-to-speech + image-input grounding như mô tả.
> - 3.2 GraphRAG: **chưa có** — RAG hiện tại là hybrid keyword+semantic (`embeddings.py`, `rag_defaults.py`), AI tutor backed bởi DeepSeek.
> - 3.4 Knowledge Tracing: **chưa có** — learning path hiện rule-based + `adaptive_quiz` (ELO-like).
> - 3.5 On-device AI (WebGPU): **chưa có**.
> - 3.6 Evaluation Layer: **chưa có** pipeline graders tự động.

## 1) Bối cảnh hệ thống hiện tại

Dự án hiện đã có các khối năng lực phù hợp để làm nghiên cứu thực nghiệm:

- AI Tutor và AI Q&A: `main.py` (`/api/v1/ai/tutor`, `/api/v1/ai/tutor/stream`, `/api/v1/ai/qa`)
- RAG nội bộ và embedding + hybrid retrieval: `main.py` (`_collect_ai_sources`, `_score_rag_documents`, `_call_embedding`), admin RAG settings tại `/api/v1/admin/rag/settings`
- Cá nhân hóa lộ trình học: `/api/v1/learning-path/today`, `/api/v1/learning-path/generate`
- Hạ tầng thí nghiệm/feature flags/metric events: `/api/v1/experiments`, `/api/v1/experiments/{experiment_key}/events`, `/api/v1/experiments/{experiment_id}/metrics`, admin experiment results
- Mô hình dữ liệu đã sẵn cho đo lường: `models.py` (`Experiment`, `ExperimentEvent`, `ExperimentMetricEvent`, `AIConversation`, `RagSettings`)

=> Đây là nền tảng rất tốt để chạy nghiên cứu khoa học theo kiểu A/B test và RCT ngay trong sản phẩm.

## 2) Mục tiêu nghiên cứu

Mục tiêu tổng quát: tìm và kiểm chứng các tính năng công nghệ mới (2025-2026) có thể tăng **hiệu quả học**, **mức gắn kết**, và **độ tin cậy AI** trong bối cảnh học di sản Cửu Đỉnh.

### Câu hỏi nghiên cứu (Research Questions)

- RQ1: Voice + vision tutor thời gian thực có tăng learning gain so với chat text hiện tại không?
- RQ2: GraphRAG có tăng độ toàn diện/chính xác câu trả lời so với hybrid RAG hiện tại không?
- RQ3: Guardrails kiểu “hint-first” có giảm phụ thuộc AI (crutch effect) mà vẫn giữ hiệu quả luyện tập không?
- RQ4: Knowledge tracing thế hệ mới có cải thiện chất lượng learning path và retention 7/30 ngày không?
- RQ5: On-device AI (WebGPU) có cải thiện latency/privacy và tỉ lệ hoàn thành trên thiết bị yếu không?
- RQ6: Pipeline đánh giá bằng graders + human audit có giảm hallucination và tăng độ ổn định chất lượng không?

## 3) 6 tính năng công nghệ đột phá ưu tiên

## 3.1 Realtime Multimodal Tutor (Voice + Image)

### Tính mới

- Tương tác hội thoại giọng nói trực tiếp (speech-to-speech), có thể nhận ảnh để “nhìn cùng người học” khi hỏi về họa tiết/chi tiết hình ảnh.
- Phù hợp đặc thù dự án Cửu Đỉnh vì dữ liệu học có tính thị giác cao (3D + hình tượng).

### Chứng cứ công nghệ

- OpenAI công bố `gpt-realtime` và Realtime API GA ngày 2025-08-28, hỗ trợ speech-to-speech production.
- Realtime hỗ trợ image input để grounding theo hình người học đang thấy.

### Tích hợp vào codebase

- Tạo biến thể mới của `/api/v1/ai/tutor/stream` cho voice session.
- Tái sử dụng `_collect_ai_sources` để giữ cơ chế trích dẫn [S#].
- Log sự kiện vào `/api/v1/experiments/{experiment_key}/events` với các metric: `response_latency_ms`, `voice_turn_count`, `session_completion`.

---

## 3.2 GraphRAG cho truy vấn lịch sử có ngữ cảnh sâu

### Tính mới

- Bổ sung tầng knowledge graph trên corpus Cửu Đỉnh để trả lời câu hỏi tổng hợp liên chủ đề (biểu tượng, triều đại, ngữ cảnh địa lý-văn hóa).

### Chứng cứ công nghệ

- Bài GraphRAG (arXiv:2404.16130, cập nhật 2025) báo cáo cải thiện đáng kể về độ toàn diện/đa dạng câu trả lời so với RAG truyền thống cho truy vấn sensemaking quy mô lớn.
- Hệ GraphRAG đã có release liên tục đến 2026 (PyPI `graphrag 3.0.9`, 2026-04-13).

### Tích hợp vào codebase

- Giữ pipeline hiện tại làm baseline (`_score_rag_documents` hybrid keyword+semantic).
- Bổ sung nhánh retrieval mới `retrieval_mode = hybrid|graphrag` trong `RagSettings`.
- A/B test giữa nhánh baseline và GraphRAG qua experiment framework sẵn có.

---

## 3.3 Guardrailed Tutor (Hint-First, không “nhả đáp án”)

### Tính mới

- Không cho AI giải hộ ngay; ưu tiên hint theo bậc, Socratic prompts, kiểm tra bước trung gian.
- Chống hiện tượng học sinh lệ thuộc AI khi luyện tập.

### Chứng cứ học thuật

- PNAS 2025 (Bastani et al.) cho thấy: AI tutoring không guardrails có thể làm giảm kết quả khi bỏ AI; guardrails kiểu gợi ý giúp giảm tác động tiêu cực.
- Scientific Reports 2025 (Harvard RCT) cho thấy AI tutor được thiết kế sư phạm tốt có thể tăng learning gain và engagement.

### Tích hợp vào codebase

- Thêm `tutor_mode = direct|hint_first|socratic` vào request/context của `/api/v1/ai/tutor`.
- Log metric: `hint_depth`, `final_answer_independence_score`, `post_quiz_without_ai`.
- Đưa guardrail thành feature flag để rollout từng phần.

---

## 3.4 Knowledge Tracing nâng cấp cho Learning Path thế hệ mới

### Tính mới

- Nâng từ rule-based personalization lên KT model (sparse attention + sequence modeling) để ước lượng mastery theo kỹ năng.
- Learning path tự điều chỉnh theo xác suất quên/độ thành thạo.

### Chứng cứ học thuật

- Scientific Reports 2025: các mô hình KT deep learning cải thiện mạnh trên dự đoán kết quả tương lai trong ITS, tập trung xử lý data sparsity.

### Tích hợp vào codebase

- Dùng dữ liệu hành vi sẵn có (quiz/review/completion) để huấn luyện KT offline.
- Inject điểm mastery vào service tạo path (`/api/v1/learning-path/generate`).
- Theo dõi tác động lên `path_completion_rate`, `review_retention_d7/d30`.

---

## 3.5 On-device AI trên WebGPU cho quyền riêng tư và độ trễ thấp

### Tính mới

- Chạy một số tác vụ AI trực tiếp trên trình duyệt (embedding nhỏ, ASR nhẹ, phân loại ảnh cơ bản) thay vì mọi thứ đều gọi server.
- Tăng khả năng hoạt động trên mạng yếu, giảm độ trễ đầu-cuối.

### Chứng cứ công nghệ

- ONNX Runtime Web + WebGPU (2024) cho thấy tăng tốc đáng kể, ví dụ tăng tốc encoder Segment Anything tới 19x trên demo.
- Transformers.js v3 (2024) mở rộng thực thi mô hình trên WebGPU, hỗ trợ nhiều task và định dạng lượng tử hóa.

### Tích hợp vào codebase

- Frontend Next.js: bổ sung fallback pipeline `device: webgpu -> wasm -> server`.
- Chỉ chọn tác vụ nhẹ và không nhạy cảm về kiểm soát nội dung cho on-device.
- KPI: `p95_latency`, `mobile_completion_rate`, `server_token_cost_per_user`.

---

## 3.6 AI Evaluation Layer (Graders + Human audit)

### Tính mới

- Chuẩn hóa đánh giá câu trả lời AI bằng model graders + text similarity + human spot-check.
- Đưa chất lượng AI thành chỉ số vận hành liên tục, không kiểm thử thủ công rời rạc.

### Chứng cứ công nghệ

- OpenAI Graders hỗ trợ score model graders/text similarity graders cho pipeline đánh giá có cấu trúc.

### Tích hợp vào codebase

- Tạo bộ eval dataset nội bộ theo chủ đề Cửu Đỉnh.
- Chạy đánh giá định kỳ theo version prompt/model.
- Đưa kết quả vào dashboard admin để quyết định rollout/rollback.

## 4) Thiết kế nghiên cứu khoa học đề xuất

### 4.1 Thiết kế thực nghiệm

- Giai đoạn 1 (4-6 tuần): A/B test online từng tính năng độc lập.
- Giai đoạn 2 (8-12 tuần): factorial experiment (kết hợp 2-3 tính năng) để xem hiệu ứng cộng hưởng.
- Giai đoạn 3: RCT crossover cho nhóm lớp học thật (nếu có hợp tác trường).

### 4.2 Giả thuyết định lượng

- H1: Realtime multimodal tutor tăng `post_test_gain` >= 12% so với text tutor.
- H2: GraphRAG tăng `answer_comprehensiveness_score` >= 15% và giảm `hallucination_rate` >= 20%.
- H3: Hint-first guardrails giảm `dependency_index` >= 25% nhưng không giảm `practice_performance`.
- H4: KT-based learning path tăng `d7_retention` >= 10%.
- H5: On-device pipeline giảm `p95_latency` >= 30% trên mobile.
- H6: Evaluation layer giảm sự cố chất lượng nghiêm trọng (severity high) >= 40% theo tháng.

### 4.3 Biến đo lường chính

- Hiệu quả học: pre/post test gain, quiz pass rate, delayed test (7 ngày).
- Hành vi học: completion rate, time-on-task, streak continuity.
- Chất lượng AI: grounded citation rate, hallucination rate, rubric score.
- Vận hành: latency, error rate, token cost.

### 4.4 Cỡ mẫu và phân tích

- Sử dụng random assignment qua hệ experiment sẵn có.
- Phân tích: difference-in-means, regression with controls, heterogeneity (new vs returning users).
- Điều chỉnh multiple testing (Benjamini-Hochberg) khi chạy nhiều metric.

## 5) Rủi ro và kiểm soát

- Rủi ro lệ thuộc AI: bắt buộc hint-first với nhiệm vụ luyện kỹ năng.
- Rủi ro sai lệch nội dung lịch sử: bắt buộc citation [S#], human review cho chủ đề nhạy cảm.
- Rủi ro riêng tư: ưu tiên on-device cho tác vụ phù hợp; tối thiểu hóa log raw conversation.
- Rủi ro chi phí: rollout theo feature flag + giới hạn cohort.

## 6) Lộ trình triển khai đề xuất (12 tuần)

- Tuần 1-2: chuẩn hóa metrics schema, dashboard, định nghĩa experiment keys.
- Tuần 3-4: triển khai Guardrailed Tutor (nhanh, impact cao).
- Tuần 5-7: Realtime multimodal tutor pilot + eval layer.
- Tuần 8-10: GraphRAG pilot trên một tập tài liệu Cửu Đỉnh.
- Tuần 11-12: KT model bản đầu, nối vào learning path generation.

## 7) Ưu tiên đầu tư (theo Impact/Feasibility)

1. Guardrailed Tutor (cao/cao)
2. Evaluation Layer (cao/cao)
3. Realtime Multimodal Tutor (cao/trung bình)
4. GraphRAG (trung bình-cao/trung bình)
5. KT nâng cấp (cao/trung bình-thấp)
6. On-device AI (trung bình/trung bình)

## 8) Kết luận hành động

- Dự án đã có hạ tầng hiếm có để làm nghiên cứu sản phẩm nghiêm túc (AI + experiments + analytics).
- Cần đi theo chiến lược "đo lường trước, rollout sau": mọi tính năng mới phải đi kèm giả thuyết và tiêu chí dừng/mở rộng.
- Nên bắt đầu ngay từ 2 hạng mục ít rủi ro nhưng tạo nền tảng lâu dài: **Guardrailed Tutor + Evaluation Layer**.

## 9) Tài liệu UX người học đi kèm

- Bản chi tiết cải thiện trải nghiệm người học (ưu tiên theo sprint, KPI, A/B test):
  `docs/LEARNER_EXPERIENCE_IMPROVEMENTS_2026.md`
- Bản tổng hợp tính năng mới theo research EdTech 2024-2026:
  `docs/EDTECH_RESEARCH_INNOVATIONS_2026.md`

## Tài liệu tham khảo (nguồn chính)

1. OpenAI, *Introducing gpt-realtime and Realtime API updates for production voice agents* (2025-08-28): https://openai.com/index/introducing-gpt-realtime/
2. OpenAI, *New tools for building agents* (2025-03-11): https://openai.com/index/new-tools-for-building-agents/
3. OpenAI Docs, *Realtime conversations* (hỗ trợ image input trong session): https://developers.openai.com/api/docs/guides/realtime-conversations
4. OpenAI Docs, *Graders*: https://developers.openai.com/api/docs/guides/graders
5. Anthropic, *Introducing the Model Context Protocol* (2024-11-25): https://www.anthropic.com/news/model-context-protocol
6. Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization* (arXiv:2404.16130): https://arxiv.org/abs/2404.16130
7. PyPI, *graphrag 3.0.9 released Apr 13, 2026*: https://pypi.org/project/graphrag/
8. Kerbl et al., *3D Gaussian Splatting for Real-Time Radiance Field Rendering* (arXiv:2308.04079): https://arxiv.org/abs/2308.04079
9. Microsoft Open Source Blog, *ONNX Runtime Web ... using WebGPU* (2024-02-29): https://opensource.microsoft.com/blog/2024/02/29/onnx-runtime-web-unleashes-generative-ai-in-the-browser-using-webgpu/
10. Hugging Face, *Transformers.js v3* (2024-10-22): https://huggingface.co/blog/transformersjs-v3
11. Kestin et al., *AI tutoring outperforms in-class active learning ...* Scientific Reports (2025): https://www.nature.com/articles/s41598-025-97652-6
12. Bastani et al., *Generative AI without guardrails can harm learning ...* PNAS (2025): https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/
13. Zhou et al., *Deep learning based knowledge tracing in intelligent tutoring systems* Scientific Reports (2025): https://www.nature.com/articles/s41598-025-07422-7
