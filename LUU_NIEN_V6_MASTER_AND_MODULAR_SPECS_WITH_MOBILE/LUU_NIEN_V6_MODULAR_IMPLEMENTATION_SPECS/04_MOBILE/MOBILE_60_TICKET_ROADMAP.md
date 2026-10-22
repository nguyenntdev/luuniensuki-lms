# MOBILE — index for 60 tickets in 6 waves

> Tài liệu nguyên khối đã được tách thành các module nhỏ. Các nội dung không bị lược bỏ; bản V5 nguyên vẹn vẫn có trong `99_ARCHIVE/`. Không load cả danh mục vào một model context.

# MOBILE ROADMAP — 6 WAVES × 10 CONCURRENT DEVELOPMENT SUBAGENTS

> **Concurrency rule:** Start 10 independent agent tasks *concurrently* only with separate worktrees and file ownership. Shared schema/router/migrations have coordinator serialized integration. If backend/model quota permits fewer than 10 simultaneous executions, report `CAPACITY_BLOCKED`, not "10 concurrently completed". Ten slots in the plan ≠ ten physical workers automatically.

## Global mobile phase barriers

- M00 baseline & guard → M01 auth/contracts → M02 content/product completion → M03 ELLO/notifications → M04 AI/QA → M05 startup/release.
- Dependencies can be refined at the ticket level; blocked source approval prevents publication but need not block UI prototype behind demo tenant flags.
- Every wave has 10/10 terminal handoff reports; `PASS` means verified test evidence; `BLOCKED` for unverified rights, credentials, schema, child safety or release signing.
- Do not dispatch subagents to edit same source files. If a shared path overlaps, appoint a single owner and other agents provide patch suggestions/tests-only in distinct files.


## Spec đã tách

- [WAVE_M00](WAVE_M00.md)
- [WAVE_M01](WAVE_M01.md)
- [WAVE_M02](WAVE_M02.md)
- [WAVE_M03](WAVE_M03.md)
- [WAVE_M04](WAVE_M04.md)
- [WAVE_M05](WAVE_M05.md)
