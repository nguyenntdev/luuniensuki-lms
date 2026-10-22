# V2 original archival technical chapter — SECTION_04

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 4. KIẾN TRÚC ĐÍCH VÀ LỘ TRÌNH KHÔNG PHÁ VỠ LEGACY

### 4.1 C4 container architecture (đề xuất)

```text
                    WEB / FLUTTER / LOW-BANDWIDTH / OFFLINE
                              | HTTPS + OIDC/JWT
                      EDGE CDN + WAF + trusted proxy
                              |
                    Next.js SSR/BFF + Rust Axum API
                              |
              +---------------+----------------+------------------+
              |               |                |                  |
         History Core     LMS/Assessment   Discovery/Inquiry   Research Gateway
              |               |                |                  |
              +---------------+-------+--------+------------------+
                                      |
                          PostgreSQL + durable jobs
                                      |
             +------------------------+---------------------------+
             |                        |                           |
       S3-compatible media      Versioned evidence store       Restricted research vault
       signed/hashed assets     claims/sources/audit            anonymized imports
             |                        |                           |
       2D/GLB/AR renditions    Source-grounded retrieval       reproducible aggregates
                                      |
                              AI provider abstraction
                           (deterministic fallback)
```

**Migration strategy:** giữ Python nghiệp vụ đang có, Rust xử lý route đã contract-verified; không chuyển AI/complex transaction chỉ để thuần Rust; cấm hai service cùng thay đổi một schema chưa có ownership rõ. Dùng explicit route inventory, response envelope, auth parity tests và shadow read comparison trước cutover.

### 4.2 Architecture decisions (ADR)

| ADR | Quyết định | Trade-off | Test/Gate |
|---|---|---|---|
| ADR-01 | PostgreSQL là OLTP source of truth, không lấy JSON frontend làm authority | yêu cầu seed/import chặt | count + constraints |
| ADR-02 | Core History entity–claim–source là knowledge authority | liên kết phức tạp hơn text tĩnh | lineage query |
| ADR-03 | Media object store bằng hash, biến thể 512/1k/2k | cần storage pipeline | integrity + LOD budgets |
| ADR-04 | Research vault logic + physical isolation ở prod | vận hành thêm | access controls |
| ADR-05 | AI RAG chỉ từ nguồn published, citation verified | abstention có thể nhiều | benchmark |
| ADR-06 | 3D/AR tùy chọn, 2D phải tương đương sư phạm | giới hạn tính bắt mắt | task parity |
| ADR-07 | Inquiry only, không coi là booking tức thời | conversion phức tạp hơn | false-confirmation test |
| ADR-08 | Feature flags production fail-closed | demo khó hơn | flag matrix |
| ADR-09 | Bilingual VI/EN là content fields có review | cần translation QA | translation coverage |
| ADR-10 | Rust strangler theo API contracts | tạm duy trì hai backend | snapshot + parity |
| ADR-11 | Heritage copyright + artisan consent là release gates | tốc độ xuất bản chậm | fail-closed publish |
| ADR-12 | Events xếp loại educational/analytics vs research | quản trị phức tạp | privacy retention |

### 4.3 Migration plan tối thiểu

1. Sao lưu DB, collect current Alembic revisions `alembic heads --verbose`, `alembic current --verbose`, schema-only dump; không chạy auto merge production.
2. Lập bảng endpoint Rust-native/proxied từ inventory config; assert every route reachable, cấm duplicate mutation handlers.
3. Chuẩn hóa response/error JSON giữa Rust và Python; OpenAPI contract generation, CI drift check.
4. Trích stable `HistoricalEntity/Claim/Source` API, append-only versions và stable motif IDs.
5. Đưa dataset AI seed vào quarantine + build editor workflow; chỉ dùng published authority ở public.
6. Triển khai LMS ELLO/v1; giữ quizzes hiện tại để tương thích.
7. Triển khai research ingestion độc lập, consent verified, aggregate export, no public raw.
8. Migrate demo/inquiry responses production fail-closed; then automated tests.

---

