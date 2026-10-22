# V5.15 — HANDOFF AND REVIEW

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.15`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## V5.15 — MẪU BÀN GIAO, QUY TẮC ĐÓNG TICKET, RELEASE VÀ PHỐI HỢP VỚI V4

### 15.1. Tạo tệp evidence cho mỗi ticket

Mỗi `V5-Txxx` phải tạo (đường dẫn mang tính TARGET; điều chỉnh theo cấu trúc thật sau preflight):

```text
artifacts/implementation/V5-Txxx/
  baseline.json            # SHA, branch, môi trường, phụ thuộc, trạng thái trước sửa
  changed-files.md         # đường dẫn, hàm, dòng trước/sau, mục đích
  contracts.md             # request/response, trạng thái, invariant, role
  implementation.diff      # patch kiểm soát bởi integrator
  test-results.json        # tên test, lệnh, pass/fail/not_run, thời gian
  negative-tests.md        # lỗi backend/mạng/quyền/trùng mutation/rollback
  security-review.md       # auth/RBAC/PII/rights/secrets/rate limit
  data-migration.md        # up/down và kết quả test disposable DB
  operations.md            # logs/metrics/traces/alert/runbook/backup
  reviewer-signoff.json    # human approvals và release flag
  handoff.json             # handoff chuẩn dưới đây
```

Tuyệt đối không tạo nội dung `PASS` giả: mỗi test phải có tên, command, exit code và trích đoạn log. Không commit bí mật, dữ liệu học sinh hoặc token thật vào artifacts.

```json
{
  "ticket_id":"V5-T001",
  "base_commit":"<verified-live-SHA-or-UNKNOWN>",
  "branch":"feat/rbpc-cultural-bridge-2026",
  "agent_slot":"W00-A01",
  "goal":"<defined-ticket-goal>",
  "changed_files":[],
  "contracts_changed":[],
  "migrations":[],
  "checks":[{"name":"typecheck","command":"<actual-command>","status":"NOT_RUN","exit_code":null,"evidence_path":null}],
  "negative_cases":[],
  "mock_runtime_eliminated":false,
  "api_db_e2e_verified":false,
  "privacy_rights_source_gates":{"privacy":"NOT_REVIEWED","rights":"NOT_REVIEWED","source":"NOT_REVIEWED"},
  "observed_peak_agent_concurrency":null,
  "blocking_issues":[],
  "release_flag":"OFF",
  "reviewer":"PENDING",
  "status":"BLOCKED"
}
```

### 15.2. Gate đóng các mock/skeleton

- `CODE_REPLACED`: mock runtime không còn reachable từ production route; test fixture vẫn hợp lệ.
- `CONTRACT_VERIFIED`: endpoint có request/response versioned và typed errors được frontend xử lý.
- `DB_VERIFIED`: transaction đã commit, dữ liệu tồn tại qua restart; tenant/user boundary đúng.
- `NEGATIVE_VERIFIED`: 401/403/404/409/429/5xx, timeout, offline, retry, idempotency và race có tests.
- `REVIEWED`: independent review security/rights/privacy/historical provenance khi áp dụng.
- `OBSERVED`: dashboard log/metrics trace được test; không fake business traction.
- `DEPLOYED`: canary được duyệt, rollout/rollback đã thử, release gate P0=0.

Thiếu bất kỳ bước nào thì ticket chưa phải `PRODUCTION_DONE`; một UI có `200 OK` từ mock không tính.

### 15.3. Phối hợp hai dàn agents

**Development orchestration:** V5 W00–W12 = 13 waves × 10 development roles = 130 slots, nhằm hoàn thiện codebase và phát triển tính năng; không đồng nghĩa 130 con người hoặc 130 model executions thực tế.

**Historical research orchestration:** V4/V3 P00–P11 = 12 phases × 10 historical-research roles = 120 slots, nhằm tạo hồ sơ nguồn, kiểm tra quyền, trích đoạn, đối chiếu, viết bài, QA và human release. Nội dung AI luôn đi qua hệ thống review, không được tự publish.

Các wave có thể được lập kế hoạch song song khi **không có dependency**; phải bảo đảm cùng nguồn chân lý DB, RBAC, source/rights registry và content version. Bất kỳ agent nào không thể chạy do giới hạn provider đều là `CAPACITY_BLOCKED`, không thay bằng nhiều lượt tuần tự mà gọi là concurrent.

### 15.4. Bộ prompt giao việc tối thiểu cho Gemini Flash

```text
ROLE: Implementer of exactly one V5 ticket; never claim production readiness without tests.
INPUT: Verified branch SHA, one V5-Txxx ticket, dependencies, allowed paths, V5 gates, relevant V4 contract, at most 3-8 source files.
WORKFLOW: inspect -> map call graph -> write failing regression test -> implement smallest safe diff -> run targeted tests -> run negative cases -> document DB/API/frontend compatibility -> handoff.
CONSTRAINTS: never edit obsolete root monolith; never return mock-success; never fabricate source or citation; do not run migrations on production; no student PII in prompts/logs; no hidden changes to shared schema; no claiming tests passed if not run.
OUTPUT: changed file/line mapping, diff summary, test commands+logs, risks, HANDOFF_JSON, status PASS/FAIL/BLOCKED/NOT_RUN and proposed next ticket.
STOP: missing rights, source approval, credential, consent, unresolved P0 security blocker, provider limit or ambiguous migration => BLOCKED and request coordinator/human decision.
```

### 15.5. Thứ tự đọc tài liệu lớn

1. `V5.0–V5.6` + `V5.15`: chính sách production-completion, trạng thái và giao việc.
2. Ticket `V5-Txxx` cụ thể, kiểm tra mã nguồn thực và yêu cầu acceptance.
3. `V5.7–V5.13` khi ticket liên quan nội dung/AI/startup/security/research.
4. Phụ lục V4/V3 bên dưới: mở theo anchor của AIR/research packet liên quan; không nạp cả >1 MB context trong một lượt.
5. Kiểm thử và viết biên bản không tự nhận test chưa chạy.

---

