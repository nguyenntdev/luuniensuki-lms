# V5.8 — AI_FACTORY_OVERVIEW

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.8`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.8 — AI RESEARCH FACTORY: TRỌN NỘI DUNG NHƯNG KHÔNG TỰ XÁC NHẬN SỬ LIỆU

**Giữ V4 P00–P11, mỗi phase gồm đúng 10 job envelopes có vai trò khác nhau.** V5 thêm ba lớp orchestration cần implement thực tế: (a) source-acquisition legal gate, (b) atomic claim citation graph, (c) independent reviewer/commercial publishing safety.

### 8.1. Control plane

- `RunCoordinator`: create run with `object_set`, `source_allowlist`, `model_policy`, `cost_budget`, `phase_policies`, idempotency token.
- `WaveDispatcher`: enqueue 10 exact role slots in one DB transaction; record all 10 QUEUED and one wave id; independent worker pool leases tasks.
- `ProviderRateLimiter`: distributed per-model org quota + cost + concurrency; if only 5 capacity, report observed parallelism 5 and `CAPACITY_BLOCKED` rather than asserting 10.
- `ExecutionSandbox`: content is untrusted; prompt injection in archival text cannot call arbitrary shell/browser or grant reviewer role.
- `EvidenceInspector`: each claim must bind to passage source_id + locator + content hash, and relation judged by rules/human spot check.
- `HumanReviewQueue`: source, rights, history, educational, conflicts; reviewer never auto-signed by AI.
- `Publisher`: immutable approved revision, index/cache invalidation and rollback.

### 8.2. Phase-to-output mapping

| Phase | 10 concurrent agent focus | Output/mandatory gate |
|---|---|---|
| P00 | scope, taxonomy, identity, question, feasibility | object manifest, budget, do-not-use list |
| P01 | official, archival, museum, scholarly, geographic source discovery | source candidate register with provenance |
| P02 | legal, rights, digitization integrity, duplication | licensed source set, blocked list |
| P03 | OCR, Hán–Nôm, layout, translation extraction | passages with page/coordinates, confidence |
| P04 | bibliographic normalization, duplicate/version matching | source graph with stable IDs |
| P05 | atomic claim extraction and source bind | claim–passage mapping, contradictions |
| P06 | corroboration/adversarial critique/date/place disambiguation | uncertainty and conflict ledger |
| P07 | learner goals, cognitive load, accessibility, media matching | lesson object plan and rubric |
| P08 | full VI/EN narrative drafting, question bank, metadata, description | drafted content with sentence-level claim refs |
| P09 | independent source check, factual and cultural review | validated/rejected claim report |
| P10 | editor/rights/educator sign-off preparation | human decision queue, no AI approval |
| P11 | publish readiness, translations, asset audit, release + maintenance | approved candidate release and checksum |

### 8.3. Functional acceptance tests

- **TEN_TRUE:** 10 worker leases overlapping measured runtime, 10 different agent ids and role prompts, global safety limits maintained; report observed_peak, wave latency and all 10 envelopes.
- **HALF_CAPACITY:** Provider cap 5 must not silently claim concurrency 10. Automatically requeue/rest at lower concurrency if policy allows and accurately report `observed_peak=5`.
- **ZERO_SOURCE:** No verified source => model outputs structured `NO_VERIFIED_EVIDENCE`, not encyclopedic narration.
- **MALICIOUS_SOURCE:** OCR page embeds `ignore system prompt`, tool access denied; content marked untrusted.
- **FALSE_LOCATOR:** Apparent bibliographic source but nonexistent edition/page => hold.
- **CONFLICTING_SOURCES:** More than one scholarly interpretation => label conflict and contextualize, no forced consensus.
- **LIVING_ARTISAN:** No explicit consent for persona/image -> block public use and AI story publication.
- **DUPLICATE_RUN:** Same idempotency request replay -> no doubled charges/jobs.
- **WORKER_CRASH:** Expired lease requeued once with exactly-once publication semantics via dedupe.
- **REVOKED_SOURCE:** Rights revoked after generation -> approved draft invalidated for affected passages.

### 8.4. End-to-end generation of full content

Generated article sections per object: archival identity, physical observation, relief description, name/original-script verification, chronology, geographic meaning, cultural symbolism with uncertainty, multiple viewpoints, provenance table, exact references, accessibility alt text, VI/EN student version, advanced researcher version, learner questions (simple+source reasoning), teacher guide, rubric, reading-time estimate, 3D/AR viewpoint guide, optional living-culture links. Every factual sentence maps to claim(s) or explicitly marked as interpretive/student activity. Unknown fields are intentionally omitted or flagged; **never fill blanks using model imagination**.

### 8.5. LLM evaluation gates

Measured on human reviewed gold set disjoint from training/seed. Track citation correctness, claim support, unsupported statement density, refusal appropriateness, Hán–Nôm transcription correction rate, cross-language consistency, revision acceptance, latency, cost per approved story, and reviewer hours. Target values must be fixed before benchmarking; do not assert 100% zero hallucinations as guarantee. If evaluation fails, fall back to approved static content and stop AI release.

