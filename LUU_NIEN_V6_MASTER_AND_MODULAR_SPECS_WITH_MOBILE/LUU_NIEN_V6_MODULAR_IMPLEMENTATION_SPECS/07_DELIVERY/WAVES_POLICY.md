# WAVES POLICY: 13 waves × 10 development agents

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.14`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.14 — 13 IMPLEMENTATION WAVES, MỖI WAVE 10 CONCURRENT DEVELOPMENT SUBAGENTS

**Cấu trúc task thực thi:** 13 development waves `W00`–`W12`; mỗi wave có **đúng 10 vai trò/ticket độc lập** khởi tạo `QUEUED` cùng transaction rồi được worker pool thực thi đồng thời theo mức cho phép. Với API provider không cho đạt 10 physical concurrent executions, `CAPACITY_BLOCKED` và log thực tế; không che giấu bằng lời. Mỗi agent được giao một *output envelope*, có thể là code/test/docs/verification report; agent có thể đọc shared files nhưng không cùng edit shared files. Coordinator nhận 10 kết quả và merge theo thứ tự. 12 waves P00–P11 của historical content factory bên V4 là **một loại khác** (120 historical research roles), không bị thay bởi 130 dev roles.

### 14.1. Development executor envelope schema

```json
{
 "wave_id":"W01", "ticket_id":"V5-T011", "agent_slot":1,
 "role":"task-specific engineer", "base_sha":"<live-git-SHA>",
 "input_manifest_hash":"sha256:<...>",
 "allowed_read_paths":["..."], "exclusive_write_paths":["..."],
 "dependencies":["V5-T001"], "token_budget":12000,
 "timeout_seconds":900, "cost_max_usd":0.75,
 "expected_artifacts":["patch.diff","test.log","handoff.json"],
 "state":"QUEUED", "lease_owner":null, "retry_limit":2
}
```

`token_budget`, timeout and cost are example configurable limits, not assumed provider entitlements. Permission-denied or unavailable tool must be `BLOCKED`. Shared `backend/models.py`, central migrations and API types require coordinator-controlled serial integration. Subagents may produce proposed diff files in isolated worktrees, but **must not simultaneously overwrite** a shared file.

### 14.2. Review / merge algorithm

```text
COORDINATOR:
  verify clean live checkout, inputs, 10 slots, scope and shared lock map
  create 10 assignment records atomically
  run 10 independent tasks concurrently within provider + compute quota
  await all terminal outcomes; on partial failure retry only failed idempotent slots
  inspect 10 artifacts + overlaps; store observed_peak
  select non-overlapping changes, code review, integrate serial where needed
  run full module contract tests + negative tests; migration/test DB dry-run
  write signed wave gate report PASS/FAIL/BLOCKED
  human approves merge; otherwise phase remains not done
```

### 14.3. Wave policy

- Wave W00: 10 roles chủ yếu audit/read-only, chỉ coordinator tạo baseline docs/scripts.
- W01–W08: production completion; P0 first; all route changes may require coordinating Rust gateway path routing.
- W09–W11: **new features** can be built behind disabled flags after core domain contracts stabilize; no public launch before dependencies.
- W12: 10 verification reviewers, mostly read-only; no self-approval of code authored by same agent.
- Snapshot ZIP thiếu `.git`: mọi package ghi `SNAPSHOT_ONLY`, không invent SHA. Khi lên checkout thật, compare drift vs ZIP.

**Ticket ID mapping:** `V5-T001` = W00 agent 1; `V5-T010` = W00 agent 10; `V5-T011` = W01 agent 1 ... `V5-T130` = W12 agent 10. Mỗi packet bên dưới có phụ thuộc wave, đường dẫn hiện có/đề xuất, failure case, nghiệm thu và evidence.

