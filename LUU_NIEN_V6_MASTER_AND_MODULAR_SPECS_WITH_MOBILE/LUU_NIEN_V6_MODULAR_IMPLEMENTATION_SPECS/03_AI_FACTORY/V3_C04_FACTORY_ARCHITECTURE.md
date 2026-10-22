# V3.C4: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C4`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C4. Provider connectors, tìm sử liệu thực tế và kiểm soát trích dẫn

### C4.1. Policy registry cho nguồn lịch sử

Một `search_provider` phải có metadata trước khi bật:

| Thuộc tính | Quy tắc |
|---|---|
| Provider ID | canonical slug, environment, owner, scopes |
| API credential | secret manager, không lưu trong prompt/log |
| Allowed domains | whitelist, optional denylist, redirects check |
| Search terms | vi, en, Hán–Nôm do chuyên gia cung cấp; version hóa queries |
| Usage policy | robots, TOS, quyền metadata/HTML/PDF/scan/derivative/AI processing tách biệt |
| Authentication | API key/OAuth service account có audit; không dùng cookie người dùng trường học |
| Rate limits | request/giây, burst, daily budget, Retry-After, cache TTL |
| Reproducibility | query ID, result ID, retrieval timestamp, source URL, content fingerprint |
| Allowed retention | metadata-only, excerpt-only, full text (chỉ khi được phép) |
| Alerting | 429, 403, 451, captcha, license change => stop/acquisition queue |

### C4.2. Tối thiểu năm nhóm provider connectors `[TARGET]`

**A. Catalog và cơ quan di sản:** trang/registry của cơ quan di sản, hồ sơ UNESCO/MOWCAP, bảo tàng, thư viện; dữ liệu phải trích theo đúng đơn vị đã được công bố. Hồ sơ ghi danh của cả bộ Cửu Đỉnh không tự chứng minh cách diễn giải từng họa tiết.

**B. Học thuật:** DOI/Crossref metadata, catalog thư viện, repository nghiên cứu, chỉ mục tạp chí và bài toàn văn được truy cập hợp lệ. Thông tin abstract cho phép tìm nguồn, nhưng không đủ quote một nội dung không thấy trong abstract.

**C. Sử liệu chữ Hán–Nôm:** bản ảnh được phép, catalog nguyên bản, bản phiên âm/bản dịch có người biên tập, danh mục chuyên gia; phải giữ ảnh gốc, phiên bản bản đọc và sai khác giữa các ấn bản.

**D. Địa lý sử:** bản đồ lịch sử, tư liệu địa danh, vùng địa lý và mốc lịch sử; không áp tọa độ một bản đồ hiện đại làm bản đồ thế kỷ XIX.

**E. Media:** ảnh hiện vật/mô hình 3D/scan, attribution, license và quyền hiển thị; dừng nếu NoAI hoặc giấy phép không cho xử lý như dự tính.

Connector nào chưa tích hợp trả `PROVIDER_UNAVAILABLE`, không tự chế kết quả. Không lưu user credentials bên thứ ba vào corpus. Nếu nguồn trả đoạn văn có chỉ dẫn kiểu “ignore system prompt”, xem là nội dung tư liệu không đáng tin ở tầng điều khiển.

### C4.3. Query planning đa ngôn ngữ không chỉ bằng LLM

1. Tạo canonical `relief_id`, `urn_id`, vi/en/han-nom aliases từ registry đã duyệt.
2. Trích tên lịch sử và ngữ nghĩa có nguồn; phân biệt alias đã xác nhận và candidate search terms.
3. Query được version hóa: `{subject_id, historical_period, alias_type, source_class, language, edition, excluding_terms}`.
4. Thực hiện exact-match trên metadata trước semantic search; semantic retrieval chỉ bổ trợ khi phát hiện tên viết khác.
5. Dùng search diversity: tối thiểu các lớp source archival/scholarly/catalog khi có quyền; không ép quota 3 nguồn khi thực tế chỉ có 1 nguồn.
6. Rank theo `object_match`, `edition_identity`, `provenance`, `primary/secondary`, `locator_accessibility`, `independence`, `source_freshness_if_relevant`, `rights`; không rank chỉ dựa SEO hoặc embedding similarity.
7. Mỗi kết quả phải có `why_candidate` và `what_is_not_yet_verified`.
8. Không suy diễn `source_not_found` = `the historical assertion is false`; mở manual discovery ticket.

### C4.4. Download và trích xuất hợp pháp

```text
SEARCH_METADATA
 -> POLICY_CHECK (allowed / metadata_only / permission_required / forbidden)
 -> DOWNLOAD_IF_ALLOWED (max bytes, timeout, MIME, malware, redirect)
 -> CONTENT_HASH + STORE_ENCRYPTED_IMMUTABLE
 -> PAGE_LAYOUT_DETECTION
 -> OCR/NATIVE_TEXT_EXTRACTION
 -> QUOTE_LOCATOR_VERIFICATION
 -> SOURCE_PASSAGE_INDEX
 -> CLAIM_EXTRACTION
```

- PDF native text: kiểm character map, page rotation, footnotes/columns và font mapping; text extraction lỗi phải fallback ảnh + OCR review.
- Scanned PDF: lưu page image hash, OCR text layer và quality estimate; Hán–Nôm chưa duyệt không biến thành original inscription.
- HTML: trích theo DOM selector/section anchor, ghi source URL và snapshot datetime.
- Image-only: vùng chữ được crop với bounding boxes, snapshot ID; không ghi claim quote thành `verbatim` nếu chưa có transcript kiểm tra.
- Audio/video oral history: bản ghi có consent, timecode và quyền trích; biên bản ASR phải kiểm lại; không gán lời nói của cộng đồng thành dữ kiện lịch sử hiển nhiên.
- Copyright: mặc định lưu metadata nếu quyền chưa rõ; việc truy cập được tài liệu không đồng nghĩa quyền sao chép toàn văn trên server hoặc phân phối lại dưới dạng full content.

### C4.5. Quote verifier hai lớp

**Lớp deterministic:** `snapshot_hash` tồn tại, `locator` resolve, normalize Unicode **chỉ để match phụ trợ** (không thay exact text), kiểm spans/offset/bbox, version identity, license và quote length. Quote được coi có thể hiển thị khi `rights.quote_allowed=true` và giới hạn được người phụ trách pháp lý phê duyệt.

**Lớp semantic/nguồn:** phân biệt quote literal với đoạn AI paraphrase; phát hiện quote không thực sự hỗ trợ ý claim. Semantic support phải được review bởi chuyên gia đối với claim quan trọng. Không cấp `expert_verified` chỉ vì similarity cao.

Ví dụ failure:

```json
{
  "claim": "Hình đúc này chắc chắn mô tả ...",
  "snapshot_id":"source-uuid",
  "locator":{"page":19,"bbox":[20,40,180,75]},
  "exact_quote_check":"PASS",
  "semantic_support":"CONTEXTUALIZES_ONLY",
  "decision":"REWRITE_AS_POSSIBLE_INTERPRETATION_OR_HOLD",
  "reason":"Đoạn gốc chỉ nhắc đối tượng, không kết luận danh tính biểu tượng"
}
```

### C4.6. Mâu thuẫn sử liệu và cách biểu đạt khoa học

| Tình huống | Hành vi AI được phép | Hành vi bị cấm |
|---|---|---|
| Hai nghiên cứu diễn giải khác nhau | trình bày hai cách, gắn nguồn và ranh giới | chọn một cách chỉ vì nhiều lượt search hơn |
| Chỉ có nguồn cấp hai | nói rõ cấp nguồn, giữ điều kiện | giả bộ có văn bản triều Nguyễn |
| Hán–Nôm OCR không chắc | hiển thị placeholder/đợi chuyên gia | tạo bản chữ “nguyên văn” bằng dự đoán |
| Không có chứng cứ cho niên đại | bỏ năm hoặc viết mức chính xác của nguồn | suy từ lịch sử chung thành năm cụ thể |
| Bản phục dựng giả định | ghi nhãn dựng lại, phương pháp và độ tin cậy | gọi là ảnh chụp hiện trạng |
| UNESCO/registry chỉ xác nhận danh hiệu tập hợp | giới hạn kết luận ở phạm vi đăng ký | dùng làm chứng cứ mọi hình tượng/ý nghĩa |
| Nguồn có quyền hạn chế | metadata+citation permalink, nếu cho phép | đăng nguyên chương/số hóa lại trái phép |

---

