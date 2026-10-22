# V3.C5: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C5`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C5. Contracts cho `full content generation` — nội dung cuối đủ sâu, đa bề mặt

### C5.1. Một `FullReliefArticle` có cấu trúc, không chỉ một đoạn văn AI

**Bắt buộc dưới dạng JSON blocks versioned**, không chỉ `body_html`:

| Block | Mục đích | Trường cần có | Quy tắc evidence |
|---|---|---|---|
| `identity` | tên, đỉnh, thứ tự, danh hiệu đúng | vi/en/han_nom verified aliases, ID | inventory/description source |
| `lead` | đoạn mở đầu 100–160 từ | text_vi/en, claim_refs, inline cite | mọi factual assertion có nguồn |
| `visual_observation` | mô tả chi tiết quan sát | observable features, crop/hotspot | ảnh hiện vật bản quyền phù hợp |
| `historical_context` | bối cảnh thời Nguyễn | scoped chronology, dates with precision | claim historical sources |
| `subject_identification` | danh tính hình tượng | alternative identifications, reasoning | identification evidence |
| `iconography_interpretation` | ý nghĩa biểu tượng | interpretations + certainty qualifier | phân biệt tác giả diễn giải và dữ kiện |
| `han_nom` | chữ/phiên âm/bản dịch khi có | image, transcript, translation, reviewer | human han-nom approval required |
| `geography` | địa danh và liên hệ không gian | historical/modern geographic mapping | precision+period metadata |
| `craft_and_material` | kỹ thuật/chất liệu có bằng chứng | claim refs, edition details | avoid analogical leap |
| `evidence_comparison` | nguồn khác nhau và mâu thuẫn | bibliography/quote locators/counterclaims | preserve disagreement |
| `historical_significance` | tầm quan trọng có giới hạn | reasoned interpretation, source refs | no unsupported prestige claims |
| `learning_objectives` | kiến thức/kỹ năng theo lớp | subject, level, objectives, measurable verbs | alignment to evidence tasks |
| `source_inquiry` | học sinh đánh giá chứng cứ | source A/B, question, student response prompt | supports historical reasoning |
| `quiz_and_rubric` | đánh giá và phản hồi | item bank, explanations, rubric scale | not just click completion |
| `media_3d_ar` | bản đồ/3D/AR | validated asset URI, fallback, hotspot | rights+accuracy gate |
| `short_label` | nhãn bảo tàng | 80–150 words and citations link | same claim versions |
| `references` | danh mục có thể kiểm | source/version/locator/rights | no fake DOI/ISBN/pages |
| `editorial_status` | trạng thái nội dung | draft/verified/published, reviewers, release | no silent overwrite |

`full article` **không có nghĩa bắt buộc đủ dung lượng khi thiếu nguồn**. Target độ dài 1.500–3.000 từ cho bài tiếng Việt chuyên sâu là *mục tiêu biên tập theo độ đủ chứng cứ*, không phải yêu cầu ép AI kéo dài nội dung. Một số hình có ít nguồn chỉ nên có bản ngắn chính xác; field `coverage_gap` phải rõ ràng.

### C5.2. Ví dụ hợp đồng section (không phải nội dung sử liệu thực tế)

```json
{
  "content_release_schema":"relief-article/v1",
  "canonical_relief_id":"<UUID from 162 registry>",
  "target_locale":"vi-VN",
  "audience":"secondary_history",
  "status":"AI_DRAFT",
  "sections":[
    {
      "key":"subject_identification",
      "heading":"Nhận diện hình tượng",
      "paragraphs":[
        {
          "text":"<nội dung do AI đề xuất sau khi có hồ sơ nguồn>",
          "sentence_claim_refs":["<historical_claim UUID>"],
          "citation_anchors":["<source_passage UUID>"],
          "claim_state":"source_attached",
          "interpretation_type":"factual|qualified_inference|disputed"
        }
      ],
      "missing_evidence":["<ghi rõ chỗ chưa có căn cứ>"]
    }
  ],
  "release_gate":{"source_coverage":"PENDING", "human_signoff":"PENDING"}
}
```

V3 không tự bịa tên/định danh relief trong ví dụ; dữ liệu thật sẽ do canonical 162 registry resolve.

### C5.3. Nội dung 10 agent P07 phải hòa nhập như thế nào

1. `P07-A01` là tác giả nội dung VI; chỉ viết dựa trên dossier P06 và claim IDs.
2. `P07-A02` tạo tiếng Anh độc lập với mapping câu–claim, rồi translation QA so vi/en; không tạo claim mới do bản dịch.
3. `P07-A03` tạo nhãn ngắn không đánh mất giới hạn nguồn; có thể ít citation inline hơn nhưng phải có clickable evidence source.
4. `P07-A04` chỉ soạn Hán–Nôm khi passage transcript đã được duyệt; các mục chưa duyệt hiển thị `pending specialist review`.
5. `P07-A05` tạo narration 3D/AR gắn canonical hotspot ID và media rights, có 2D text equivalent.
6. `P07-A06` tạo timeline/map với `geo_precision`/`date_precision`, không vẽ ranh giới bị suy đoán.
7. `P07-A07` tạo sáu bước ELLO: object→question→sources→observation→argument→feedback; kịch bản là pedagogical design, không tự gọi thực nghiệm đã diễn ra.
8. `P07-A08` tạo câu hỏi phân biệt quan sát, chứng cứ và diễn giải; trường `correct_answer_evidence` bắt buộc; claim tranh cãi tránh kiểm tra một đáp án.
9. `P07-A09` tạo plain language, dyslexia-friendly layout suggestions, alternative image text và low-bandwidth route; kiểm phiên bản song ngữ.
10. `P07-A10` ghép content: inline sentence claims, source list, no citation laundering; chỉ assembly, không sáng tác thêm dữ kiện.

### C5.4. Nội dung chuyên biệt cho sáu track bài báo/hội nghị

| Track | AI có thể tự động hỗ trợ | Minh chứng bắt buộc ngoài AI draft |
|---|---|---|
| Q2 source-linked learning | soạn 1 ELLO mẫu, nguồn và nhiệm vụ, outline Method | dạy học thực tế/measurement nếu claim hiệu quả học tập |
| HCMUS poster | 162 content cards, abstracts, figure captions, QR sources | 1.502 survey gốc và quy trình khảo sát nếu công bố thống kê |
| ICTIM digital heritage experience | heritage narrative, virtual tour scripts, rights catalogue | dữ liệu khách du lịch nếu nói tourist outcomes |
| GLoCALL language learning | bilingual texts/vocabulary/glosses/reading tasks | kiểm nội dung CALL, đánh giá năng lực ngoại ngữ nếu claim improvement |
| ICETAI trustworthy AI | corpus audit, retrieval citation, evaluation benchmark | gold labels độc lập, measured results, agent execution traces |
| EAUT architecture | generated API docs/ERD, deployment and performance report drafts | test/deploy logs và benchmark thực |

**Không AI tự tạo “thống kê khảo sát”, “hiệu quả giáo dục”, “nhận xét người tham gia” hoặc “kết quả thực nghiệm” nếu không có bộ dữ liệu đo tương ứng.**

### C5.5. Chuẩn văn phong và cấu trúc bài dài

**Trước khi viết:** chọn audience/length/locale/reading level/citation style/allowed source release; đưa context pack gồm only approved claims, rejected claims chỉ nhằm cảnh báo, và unresolved gaps. **Không** để model truy cập web bất kỳ trong bước viết nếu nguồn chưa qua P01–P05.

**Trong khi viết:** mỗi paragraph mang `_citation_anchors`; nhận định quan sát có visual source ID, nhận định lịch sử có passage ID; các khái niệm nghi vấn dùng “có thể”, “được một số tác giả giải thích là”, “theo ấn bản ...”, không biến qualifier thành câu chắc chắn.

**Sau khi viết:** tách từng câu thành `statement→claim_refs`; nếu một câu sinh thông tin mới, đưa về `CLAIM_CANDIDATE` và chạy lại P04–P08 cho phần đó; không bọc citation của đoạn lân cận để hợp thức hóa.

### C5.6. Một bộ bài giảng ELLO đủ đưa vào lớp học

| Bước | AI tạo draft | Giáo viên/học sinh | Minh chứng lưu |
|---|---|---|---|
| 1. Định danh hiện vật | ảnh và provenance, mục tiêu | học sinh xác định đúng đối tượng | object choice |
| 2. Quan sát/đặt nhận định tạm | evidence prompts và crop | ghi 2 chi tiết nhìn thấy | observation text |
| 3. Đối chiếu nguồn | 1–3 nguồn có locator được quyền hiển thị | đánh giá nguồn nào hỗ trợ luận điểm | source selection+rationale |
| 4. Chọn hình thức biểu đạt | ảnh, 3D, AR, 2D fallback | thao tác phù hợp thiết bị | treatment media + duration |
| 5. Viết giải thích | sentence starters không đưa sẵn kết luận | trình bày claim–evidence–reasoning | student response |
| 6. Phản hồi/chỉnh sửa | rubric suggestion chỉ để giáo viên xem xét | sửa lập luận | rubric score+revision |

Giáo viên có thể sử dụng bản draft đã duyệt như học liệu; tuy nhiên học sinh chỉ thấy phiên bản `published_lesson_release_id` được giáo viên phân công, không thấy nguồn riêng tư hoặc claim chưa duyệt.

---
