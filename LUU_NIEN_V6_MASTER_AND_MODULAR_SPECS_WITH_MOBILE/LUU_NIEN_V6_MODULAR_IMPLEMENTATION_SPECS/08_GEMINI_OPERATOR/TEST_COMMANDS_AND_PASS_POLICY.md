# Executable test commands and NOT_RUN policy

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.D`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

# PHỤ LỤC V4.D — BỘ LỆNH KIỂM TRA THÔNG MINH, KHÔNG TỰ NHẬN PASS

### Check `repo_snapshot`

```bash
git rev-parse HEAD && git status --short && git branch --show-current
```
**Interpretation:** repo SHA and clean status or ZIP limitation. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `python_syntax`

```bash
python -m compileall -q backend
```
**Interpretation:** 0 only if Python import-independent syntax OK. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `json_syntax`

```bash
python -m json.tool data/05_Data_CaoDinh.json >/dev/null
```
**Interpretation:** 0 JSON well-formed. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `alembic_heads`

```bash
DATABASE_URL="$DISPOSABLE_DATABASE_URL" alembic heads
```
**Interpretation:** heads listed; DB must be disposable. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `backend_tests`

```bash
DATABASE_URL="$DISPOSABLE_DATABASE_URL" pytest -q tests/backend
```
**Interpretation:** may drop/recreate tables; whitelist DB required. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `research_factory_tests`

```bash
DATABASE_URL="$DISPOSABLE_DATABASE_URL" pytest -q tests/research_factory
```
**Interpretation:** requires code created in AIR tickets. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `frontend_typecheck`

```bash
cd frontend && npm run type-check
```
**Interpretation:** node_modules available. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `frontend_tests`

```bash
cd frontend && npm run test
```
**Interpretation:** vitest available. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `frontend_lint`

```bash
cd frontend && npm run lint:ci
```
**Interpretation:** strict lint. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `frontend_e2e`

```bash
cd frontend && npx playwright test
```
**Interpretation:** needs browsers + running services. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `rust_format`

```bash
cd backend-rust && cargo fmt --check
```
**Interpretation:** rustfmt installed. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `rust_unit`

```bash
cd backend-rust && cargo test
```
**Interpretation:** toolchain installed. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `migration_safety`

```bash
./scripts/ci/lint-migration-safety.sh
```
**Interpretation:** repo script exists and executable. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `pin_routing`

```bash
./scripts/ci/lint-ai-tutor-pinning.sh
```
**Interpretation:** route pin consistent. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.

### Check `diff_sanity`

```bash
git diff --check && git diff --stat
```
**Interpretation:** no whitespace artifacts; scope reviewed. Log command+exitcode+environment; absence of tool/deps = `NOT_RUN`/`RUN_BLOCKED`, not PASS. Never run destructive DB commands without disposable DB whitelist.


