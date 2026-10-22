# V3.C2: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C2`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C2. Triển khai orchestrator production: hàng đợi, 10-slot barrier, retries, idempotency

### C2.1. Quyết định kiến trúc (ADR-AIR-001)

- **Backend control plane:** `backend/routers/research_factory.py` (đề xuất mới), `backend/services/research_factory/*` (đề xuất mới), dùng FastAPI cho API admin nội bộ; Rust gateway chỉ forward qua route allowlist và bảo toàn auth claims.
- **Persistent job queue:** đề xuất Celery + Redis/RabbitMQ **hoặc** Temporal workflow engine, chọn một sau technical spike; không dùng background task in-memory của FastAPI cho job nhiều giờ, không dựa trên Python `asyncio` duy nhất để đảm bảo crash recovery. Nếu chọn Celery, lưu stage durable ở PostgreSQL và lease/visibility timeout rõ ràng; Redis chỉ broker/cache, **không là nguồn chân lý** của trạng thái nghiên cứu.
- **Artifact store:** object storage versioning + encryption + signed internal URL; snapshots/document crops/content drafts không lưu hết vào JSONB duy nhất.
- **PostgreSQL:** transaction cho run/phase/job/gate/claim/source/approval; optimistic locking cho editorial changes; audit append-only.
- **Provider adapters:** `SearchProvider`, `ScholarlyCatalogProvider`, `DocumentAcquirer`, `OCRProvider`, `LLMProvider`, `TranscriptionProvider`, `CitationResolver`, `PermissionResolver`, `EmbeddingProvider`; mọi provider có quotas, budget, request ID.
- **Concurrency:** `max_concurrent_subagents_per_phase=10` và `required_subagents_per_phase=10`; `max_active_phases_per_run=1`; `max_global_provider_requests` cấu hình theo key/provider; `max_concurrent_subject_runs` từ ngân sách tổ chức. Không tăng các giới hạn này khi lỗi rate limit.
- **Mode:** `STRICT_PRODUCTION` (default; có human gates), `DRY_RUN` (mock tool output có nhãn), `EVAL_ONLY` (không đụng DB public), `PILOT` (cấu hình nhóm review). Demo fixture tuyệt đối không được trộn corpus thật.

### C2.2. State machine cấp run, phase và agent

| Đối tượng | Trạng thái | Trigger / điều kiện | Hành động tiếp theo |
|---|---|---|---|
| Run | `CREATED` | Admin khởi tạo scope/version | kiểm policy/rights |
| Run | `VALIDATED` | manifest+budget+permission hợp lệ | enqueue P00 |
| Run | `RUNNING` | phase hiện tại `DISPATCHED` | monitor barrier |
| Run | `NEEDS_HUMAN_REVIEW` | P09 tạo packet | chờ người thật ký |
| Run | `BLOCKED` | blocker/capacity/rate/quyền/mismatch | remediation ticket |
| Run | `FAILED` | nonretryable invariant violation | giữ artifact để điều tra |
| Run | `CANCELED` | Admin cancel | revoke leases; giữ audit |
| Run | `READY_TO_PUBLISH` | P09 human signoff, P10 prepared | atomic pointer switch |
| Run | `PUBLISHED` | publication transaction success | P11 watch scheduled |
| Run | `ROLLED_BACK` | release rollback signed | giữ bản đã publish cũ |
| Phase | `QUEUED→DISPATCHED→RUNNING→FAN_IN→GATED` | đủ 10 agent terminal + reducer OK | phase kế tiếp |
| Phase | `PARTIAL/RETRYING/BLOCKED` | một hoặc nhiều agent lỗi | finite retry / human review |
| Agent | `QUEUED→LEASED→RUNNING→SUCCEEDED` | envelope hash/schema valid | immutable store |
| Agent | `RETRYABLE_FAILURE→RETRY_SCHEDULED` | timeouts/429/5xx | exponential backoff+jitter |
| Agent | `TERMINAL_FAILURE` | rights deny, fabricated locator, invalid input | no gate pass |
| Agent | `NO_EVIDENCE` | hoàn thành kiểm tra nhưng không tìm thấy bằng chứng | explicit gap; status terminal (not VERIFIED) |

Các transition bất hợp lệ phải trả `409 INVALID_STATE_TRANSITION` và ghi audit; `FAILED` không tự chuyển `PUBLISHED`; rerun tạo `run_id` mới hoặc `attempt` mới có parent link. `NO_EVIDENCE` từ agent nguồn có thể đi qua gate tìm nguồn ở mức đã audit khoảng trống, nhưng **không** đủ tạo nội dung fact claim công khai.

### C2.3. Thuật toán fan-out 10 và fan-in có chịu lỗi (pseudocode Python)

```python
# TARGET PSEUDOCODE; chưa chạy trên repository hiện tại.
PHASES = [f"P{i:02d}" for i in range(12)]
SUBAGENT_COUNT = 10

async def run_phase(run_id: str, phase_code: str, input_sha: str):
    assert phase_code in PHASES
    phase = await db.acquire_phase_lease(run_id, phase_code, input_sha)
    await budgets.reserve_for_phase(run_id, phase_code, 10)
    roles = registry.pinned_roles(phase_code)
    assert len(roles) == SUBAGENT_COUNT
    start_together = asyncio.Event()

    async def run_one(slot: int, role):
        await start_together.wait()
        key = f"{run_id}:{phase_code}:{phase.wave}:{slot}:{input_sha}"
        # Persistence stores attempt, lease and immutable completion envelope.
        existing = await db.get_successful_agent_result(key)
        if existing is not None:
            return existing
        try:
            async with global_quotas.acquire(role.provider):
                payload = await asyncio.wait_for(
                    agent_runner.execute(role, phase.read_only_input, idempotency_key=key),
                    timeout=role.timeout_seconds,
                )
            envelope = await validate_schema_hash_rights_and_provenance(payload, role)
            return await artifact_store.persist_immutable(key, envelope)
        except Exception as exc:
            # Never swallow; returns durable, classified error result.
            return await db.persist_failure_result(key, classify_error(exc))

    tasks = [asyncio.create_task(run_one(i, roles[i - 1]))
             for i in range(1, SUBAGENT_COUNT + 1)]
    start_together.set()                 # barrier release for 10 scheduled jobs
    results = await asyncio.gather(*tasks)
    assert len(results) == 10 and len({r.agent_index for r in results}) == 10
    if not terminal_policy_allows_fanin(results):
        await db.mark_phase_blocked(phase.id, results)
        raise PhaseBlocked(phase_code)
    merged = await reducer.merge_without_overwriting_evidence(results)
    gate = await deterministic_checks(phase_code, merged)
    if not gate.passed:
        await db.mark_phase_blocked(phase.id, gate)
        raise PhaseBlocked(phase_code)
    return await db.commit_phase_output_snapshot(phase.id, merged, gate)

async def run_research_pipeline(run_id: str):
    for phase_code in PHASES:
        # P09 is allowed to finish packet assembly, but needs signed human
        # approval before P10 is enqueued; P10 only prepares immutable payloads.
        await run_phase(run_id, phase_code, await db.get_current_input_sha(run_id))
        if phase_code == "P09":
            await human_review.await_two_person_signed_approval(run_id)
        if phase_code == "P10":
            await publish_pointer.atomic_swap_only_after_release_gate(run_id)
```

**Giải thích quan trọng:** Ví dụ trên dùng `asyncio` để minh họa 10 nhiệm vụ được khởi động trong cùng wave, không phải giải pháp production cuối cùng. Worker process có thể chết giữa chừng; production cần broker, durable lease, restart-safe coordinator, crash recovery, DB-backed barrier, và globally enforced provider rate limit. Không dùng pseudocode này như bằng chứng hệ thống đã hỗ trợ 10 request thực sự song song.

### C2.4. Chính sách lỗi và phục hồi

| Tình huống | Phân loại | Policy | Gate |
|---|---|---|---|
| HTTP 429/provider capacity | `CAPACITY_BLOCKED` | backoff dùng Retry-After; giới hạn retry | không pass khi thiếu agent |
| DNS fail/502/504 tạm thời | `TRANSIENT` | retries 3–5 lần, jitter; không nhân bản nguồn | không pass khi thiếu kết quả |
| Paywall, robots disallow, license denied | `NONRETRYABLE_RIGHTS` | metadata-only; xin phép thủ công | không ingest body |
| OCR confidence thấp | `QUALITY_BLOCKED` | review crop/page; cho xuất missing | không approve text |
| Quote mismatch | `EVIDENCE_MISMATCH` | quarantine claim; yêu cầu re-extract | không synthesis như verified |
| Source bị prompt injection | `SECURITY_BLOCKED` | sandbox/quarantine, log fingerprint | không giao source lệnh hệ thống |
| One agent timeout | `PARTIAL` | hoàn thành 9 agent khác, retry slot đó | barrier chưa mở |
| Provider billing exceeded | `BUDGET_BLOCKED` | ngưng run, không tự nạp tiền | cần admin reauthorize |
| Human reviewer absent | `AWAITING_APPROVAL` | giữ bản draft; gửi nhắc có giới hạn | cấm publish |
| Publish API/index fail | `RELEASE_FAILED` | rollback pointer/version; retry prepared manifests | không half publish |

### C2.5. Retry correctness, global budget và tránh thác request

- `N_run_active_phases <= 1`, `N_phase_active_subagents <= 10`, `N_agent_index_distinct == 10`.
- `max_global_llm_calls` (phụ thuộc provider), `max_global_search_calls`, `max_provider_daily_cost`, `max_document_download_bytes`, `max_ocr_pages`, `max_runs_per_day` có owner cấu hình.
- Tất cả call phải có `timeout_seconds`, `max_output_tokens`, `max_pages`, `max_search_results`, `max_sources_per_relief`, giới hạn theo content scope.
- Token/cost hard stop đặt trước gọi; estimate `tokens_per_agent × 10 × 12 × target_subjects` và overhead from retries, embeddings, OCR; báo dự toán **không bịa số USD** khi chưa có giá vendor/quota.
- Nếu API provider chỉ cho 5 concurrent requests, chỉ có 5 request hoạt động còn 5 job `CAPACITY_WAIT`; telemetry phải ghi rõ không đạt yêu cầu 10 thực thi đồng thời và không tăng key/account trái chính sách.
- Batch cap: có thể chạy 1–3 relief pilot trước khi scale 162; không đồng thời khởi chạy 162 pipelines mà mỗi pipeline chiếm 10 slots.

### C2.6. Bộ metric vận hành 10-agent scheduler

| Tên metric | Định nghĩa | Điều kiện cảnh báo |
|---|---|---|
| `research_phase_dispatched_agents` | số job dispatched theo `(run,phase,wave)` | khác 10 |
| `research_phase_active_agents` | số agent đang thực thi hiện thời | >10 hoặc <10 kéo dài do capacity cần ghi status |
| `research_phase_barrier_wait_seconds` | thời gian job cuối hoàn thành trừ job đầu | vượt SLO phase |
| `research_agent_retry_count` | retry theo provider/role | đột tăng |
| `research_job_duplicate_suppressed_total` | lượt retry bị chặn bởi idempotency | spike cần kiểm queue |
| `research_source_rights_block_total` | số nguồn bị chặn do quyền | không được giảm bằng bypass |
| `research_claim_locator_mismatch_total` | số mệnh đề có locator sai | P0 nếu lọt vào publish |
| `research_human_review_wait_days` | thời gian chờ chuyên gia | chuyển queue/nhắc, không auto-approve |
| `research_content_reviewed_coverage` | số relief có dossier đã duyệt / 162 | hiển thị mẫu số |
| `research_agent_cost_usd` | usage theo run/phase/role/provider | chạm hard budget |
| `research_auto_release_without_approval_total` | số release thiếu signed approval | **bắt buộc = 0** |

---

