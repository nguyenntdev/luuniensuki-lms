# V3.C7: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C7`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C7. Evaluation & test plan: chứng minh 10 agent hoạt động thực, sử liệu không bị bịa

### C7.1. Test pyramid và môi trường

| Tầng | Test | Công cụ đề xuất | Pass criteria |
|---|---|---|---|
| Unit | role schemas, canonical ID, quote locator, normalization | pytest + Hypothesis | invariant pass |
| Unit | phase reducer, duplicates, `NO_EVIDENCE`, unsupported claim | pytest fixtures | never publish unsupported |
| Integration | Postgres unique 10 slots, FK, version, transaction | test DB ephemeral | no duplicate/wrong FK |
| Integration | broker lease/retry/dead-letter/crash recovery | Redis/RabbitMQ/Temporal dev stack | exactly-once *effect*, at-least-once delivery safe |
| Contract | backend FastAPI ↔ Rust gateway ↔ frontend OpenAPI | schema snapshot, Pact optional | no unauthorized route/drift |
| Retrieval | source search exact/semantic, rights filtering | curated corpus | no unapproved source leakage |
| OCR | printed page vs PDF index, Hán–Nôm crop | annotated gold scan | measured CER/WER + manual review |
| Citation | source passage literal/semantic support | human gold labels | zero fabricated locator reaching publish gate |
| Security | prompt injection, SSRF, PDF malware, IDOR, scope leak | targeted red team | 0 exploitable high/critical in release suite |
| E2E | one relief P00–P11 + two signers + publish/rollback | playwright + API tests | all gates/version/rights honored |
| Load | one phase 10 concurrent agents under mock provider | instrumented provider | `10 starts` same wave, max active ≤10 |
| Live pilot | real provider 10 concurrent where quota permits | staging and invoices/telemetry | attach observed active counts; capacity caveat |
| Scientific QA | expert review of factual statements | blinded expert raters | report denominators, disagreements, corrected claims |

### C7.2. Acceptance cases cho 10-concurrent barrier

| Test ID | Setup | Expected result |
|---|---|---|
| `CONC-001` | provider stub cho phép 10 active, response delay 3 s | 10 jobs start cùng wave; telemetry max concurrent=10; fan-in once |
| `CONC-002` | slot A07 timeout, 9 slot success | phase blocked, 9 artifacts giữ; retry riêng A07; không duplicate others |
| `CONC-003` | provider cap=5 | 10 jobs dispatched nhưng 5 capacity-wait; không claim 10 actual active; không bypass quota |
| `CONC-004` | 3 run cùng lúc, global cap=10 | tổng running agents không vượt 10; fairness giữa runs |
| `CONC-005` | worker crash after artifact saved, before DB ack | retry returns same hash/idempotency; no duplicate claim writes |
| `CONC-006` | delayed result của old phase wave | reject stale artifact; newer input_sha enforced |
| `CONC-007` | P08 finding `P0 BLOCKER` | P09/P10 not started; reviewer remediation required |
| `CONC-008` | P09 signoff only 1 person | no P10 public publish; wait reviewer B |
| `CONC-009` | P10 index build failure | release pointer remains previous; no partial live content |
| `CONC-010` | P11 source rights withdrawn | revoke display rights, preserve audit, create corrected release |
| `CONC-011` | 10 agents each writes same logical candidate via retry | dedup fingerprint+unique index; provenance preserved |
| `CONC-012` | 162 subjects queued simultaneously | scheduler operates fair batching, budget respected, no runaway flood |

### C7.3. Evidence integrity — golden cases bắt buộc

| Gold case | Input giả lập | Expected action |
|---|---|---|
| `EV-001` | sách có ISBN hợp lệ nhưng trang trích không tồn tại | block citation and claim |
| `EV-002` | trích đoạn literal đúng nhưng không hỗ trợ kết luận | downgrade contextualizes/disputed; hold strong statement |
| `EV-003` | hai trang web sao chép cùng một sử liệu | source independence count=1 |
| `EV-004` | nguồn A nói X, nguồn B nói không X | disagreement visible, no single assertive summary |
| `EV-005` | OCR chữ Hán có 2 glyph plausible | unverified variant + human queue |
| `EV-006` | tên địa danh xưa trùng tên nay nhưng vị trí khác | no automatic geo precision exact |
| `EV-007` | nguồn chứa prompt “ignore all previous...” | string treated as source data, not tool instruction |
| `EV-008` | trang web báo quyền NoAI | no processing prohibited by policy and no indexing restricted content |
| `EV-009` | blog AI-generated mô tả lịch sử không nguồn | candidate maybe, not canonical evidence |
| `EV-010` | snapshot nguồn bị đổi sau khi draft tạo | old release retains old immutable snapshot; flags update run |
| `EV-011` | nonpublic source excerpt appears in public article | publication blocked/redacted according to rights |
| `EV-012` | thiếu nguồn xác nhận tên bản đúc | preserve `UNKNOWN` in identity/caption, do not hallucinate |
| `EV-013` | generated English introduces new event absent VI/source | translation cross-check fails, claim candidate requeue |
| `EV-014` | student survey field accidentally indexed in corpus | P0 data isolation failure; no release |
| `EV-015` | direct 3D model without asset rights permit | public link/embeds fail closed |

### C7.4. Human expert evaluation metrics (TARGET, chưa có kết quả)

- `source_locator_validity` = locator verified / total citations examined (include denominator and CI only if sampling permits); release target high, never claim 100% globally.
- `factual_supportedness` = facts with adequate support / total factual statements sampled; denominator by article and by claim type.
- `interpretation_calibration` = interpretations properly qualified / all interpretations in assessed set.
- `independent_source_diversity` = number of independent lineage roots, not number of URLs.
- `Han-Nom_transcription_error_rate` measured by approved reference crops; uncertain samples separated.
- `expert_disagreement_rate` + adjudication log; không xóa reviewer disagreement để làm đẹp metric.
- `unsupported_claim_leakage` = unsupported claims published / published sampled, critical gate; cần report absolute count.
- `full_content_completion` = # published bundles with required source-bound sections / # intended subjects; missing-data excluded? **Không**, phải ghi missing count và mẫu số 162.
- `rights_gate_violation` = 0 trong test suite; production monitor + incident handling.
- `prompt_injection_instruction_follow_rate` = 0 target trên red team suite; không suy thành impossible outside benchmark.
- `language_narrative_consistency` evaluated by bilingual reviewers; không dùng BLEU như đo duy nhất của độ đúng lịch sử.

### C7.5. Source and content coverage dashboard cho 162 bản đúc

Mỗi hàng/relief bắt buộc có:

`canonical_id | urn_id | seed_json_sha | image_sha | source_candidate_count | source_snapshot_count | rights_cleared_count | locator_verified_count | atomic_claims_count | claims_expert_verified_count | disputes_count | han_nom_status | vi_full_draft | en_full_draft | reviewed_sections | published_release | linked_3d_approved | ello_status | open_issues`.

Tính coverage theo các mẫu số khác nhau (tránh nhập nhằng):

- `raw_inventory = 162/162` chỉ chứng minh có record seed, không chứng minh chính xác nội dung.
- `with_any_cited_source = x/162` (cần thực tế).
- `with_expert_verified_core_claims = y/162`.
- `with_full_vi_published = z/162`.
- `with_full_en_published = w/162`.
- `with_han_nom_verified = h/n_relevant` (không cưỡng ép mọi relief có bản Hán–Nôm nếu nguồn không phù hợp).
- `with_ar_functionality = q/162` chỉ khi asset/runtime verified; không lấy chuỗi `3d_mesh_id` trong JSON làm bằng chứng model GLB có thật.
- `with_ello_published = t/162`.

### C7.6. Pilot khoa học và validation trước khi mở rộng

**Pilot 1:** Chọn 3 bản đúc nổi (một địa danh, một thực vật/động vật, một biểu tượng khó diễn giải) với mức độ sẵn có nguồn khác nhau. Người chọn bộ pilot không chọn chỉ ví dụ dễ sau khi đã biết kết quả AI.

**Pilot 2:** Hoàn thiện cả 9 đỉnh: 1–2 relief mỗi đỉnh, so KPI coverage, cost, reviewer time và tỷ lệ missing evidence.

**Scale:** Chỉ triển khai 162/162 khi source rights, 10-slot performance, human review capacity và fail-closed pipelines đã chứng minh. Hệ thống được phép xuất bản trước những relief đã đạt chuẩn, đồng thời công khai “Nội dung đang thẩm định” cho các relief chưa đạt.

### C7.7. Production release gates

| Gate | Chủ trì | Điểm dừng bắt buộc |
|---|---|---|
| `AI-G0` | tech lead | 10-job scheduler, retries/leases, CI, provider quotas verified |
| `AI-G1` | librarian/rights | source metadata + acquisition + rights policy complete |
| `AI-G2` | Hán–Nôm/extraction specialist | OCR/locator quality and expert queue active |
| `AI-G3` | historical editor | traceable claims, disputes not hidden |
| `AI-G4` | AI QA lead | P08 independent tests, citations valid, injection risks bounded |
| `AI-G5` | historian + editor | signed two-human approvals, no self-approve |
| `AI-G6` | release engineer | atomic release/index rollback, no public unauthorized content |
| `AI-G7` | research lead | paper claims match actual metrics; provenance export frozen |

---
