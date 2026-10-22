# V3.C10: research factory deep specification

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V3.C10`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## C10. Ticket backlog V3 — 45 hạng mục có thể giao PR, liên kết V2

Các ticket V3 bên dưới là **mới**, cộng thêm 64 ticket trong B11 V2; không tuyên bố 45 ticket đã triển khai. Ưu tiên xử lý các P0 source/legal/gate và an toàn release **trước** khi bật 120 vai trò agent vào production.

### C10.1. Tiêu chuẩn một ticket sẵn sàng giao dev

- **Definition of Ready:** source path, owner, schema/contract, dependency, negative case, fixtures/gold, estimate, roll-back strategy, research/rights impact.
- **Definition of Done:** code+tests+migrations (nếu có), reviewer của domain, log redacted, runbook, 10-agent concurrency trace nếu liên quan, CI passing trên môi trường mô tả, link artifact evidence.
- **Quy trình PR:** failing test → add schema/migration → service logic → UI/API → integration tests → adversarial negative → staging demo → human sign-off → feature flag rollout.
- **Không sửa chung những file phát hành của cả Rust gateway + frontend + Python backend trong một PR quá lớn**; API contract freeze để tối thiểu hóa drift.

### C10.2. Master ticket inventory

| ID | Priority | Deliverable | Primary path TARGET | Dependencies | Acceptance gate | Negative test |
|---|---|---|---|---|---|---|
| `AIR-001` | P0 | Create durable pipeline domain package | `backend/services/research_factory/` | `R0-006` | Run manifests and agent roles pinned | schema and unit |
| `AIR-002` | P0 | Add Alembic run/phase/job migrations | `backend/alembic/versions/` | `AIR-001` | 10-slot constraints and foreign keys pass | migration forward/back |
| `AIR-003` | P0 | Implement broker+worker engine selection ADR | `backend/services/research_factory/orchestrator.py` | `AIR-002` | restart-safe persistent jobs and gate | crash kill -9 |
| `AIR-004` | P0 | Implement strict 10-worker fan-out/fan-in | `backend/services/research_factory/orchestrator.py` | `AIR-003` | 10 distinct slots per wave; all terminal before fanin | CONC-001/002/003 |
| `AIR-005` | P0 | Implement global provider/concurrency quotas | `backend/services/research_factory/providers/base.py` | `AIR-003` | limits across all runs not just per process | CONC-003/004/012 |
| `AIR-006` | P0 | Add idempotency keys + leases + DLQ | `backend/services/research_factory/queues.py` | `AIR-003` | retry never double writes claims | CONC-005/006 |
| `AIR-007` | P0 | Implement private immutable artifacts+hashes | `backend/services/research_factory/artifacts.py` | `AIR-002` | mutations create new SHA objects | tamper/hash test |
| `AIR-008` | P0 | Admin RBAC and audit for research factory | `backend/routers/research_factory.py` | `AIR-002` | nonstaff denied; per-scope access | IDOR/role matrix |
| `AIR-009` | P0 | Rate and cost accounting | `backend/services/research_factory/budget.py` | `AIR-005` | hard stop at configured budget | quota simulation |
| `AIR-010` | P1 | Ten-lane frontend dashboard | `frontend/src/app/admin/research-factory/` | `AIR-004;AIR-008` | dispatched and actually running separate | playwright accessibility |
| `AIR-011` | P0 | Build source candidate registry | `backend/services/research_factory/discovery.py` | `AIR-007` | query traces and DOI lineage stored | fake metadata reject |
| `AIR-012` | P0 | Build provider allowlists and usage policies | `backend/services/research_factory/providers/` | `AIR-011` | forbidden domains/uses blocked | license/captcha negative |
| `AIR-013` | P1 | Official/museum/research metadata connectors | `backend/services/research_factory/providers/` | `AIR-012` | metadata candidates with exact URLs+times | stub adapter contracts |
| `AIR-014` | P1 | Authorized download & source snapshotter | `backend/services/research_factory/acquisition.py` | `AIR-012;AIR-007` | immutable snapshot only rights permitted | MIME/redirect/payload tests |
| `AIR-015` | P0 | Source rights action matrix | `backend/services/research_factory/rights.py` | `AIR-012` | no unknown=>grant conversion | rights decision fuzz |
| `AIR-016` | P0 | Source passages/pages schema migration | `backend/alembic/versions/` | `AIR-002` | page/index/bbox/span/edition linked | FK/deletion tests |
| `AIR-017` | P1 | PDF/HTML page parser + OCR quality ledger | `backend/services/research_factory/extraction.py` | `AIR-014;AIR-016` | source passage offsets verifiable | two-column/missing-glyph fixtures |
| `AIR-018` | P0 | Han-Nom transcription human review UI | `frontend/src/app/admin/research-factory/ocr/` | `AIR-017;AIR-008` | no unreviewed original strings published | EV-005 |
| `AIR-019` | P0 | Atomic claim/passage extraction pipeline | `backend/services/research_factory/claims.py` | `AIR-017` | claims must bind source passage or gap | EV-001/002/012 |
| `AIR-020` | P0 | Quote+locator deterministic verifier | `backend/services/research_factory/citations.py` | `AIR-016;AIR-019` | fake quote or wrong page blocked | EV-001/002 |
| `AIR-021` | P1 | Historical source independence graph | `backend/services/research_factory/source_graph.py` | `AIR-011` | two mirrors count one origin | EV-003 |
| `AIR-022` | P1 | Cross-source conflict detector | `backend/services/research_factory/corroboration.py` | `AIR-020;AIR-021` | contradictory evidence not discarded | EV-004 |
| `AIR-023` | P1 | Temporal geo+identity reviewer | `backend/services/research_factory/ontology.py` | `AIR-019` | date_precision, map status enforced | EV-006 |
| `AIR-024` | P0 | Evidence dossier builder 162 coverage | `backend/services/research_factory/dossiers.py` | `AIR-022` | no claims without bindings; gap flags | coverage grid tests |
| `AIR-025` | P0 | Full VI article source-bound writer | `backend/services/research_factory/writers.py` | `AIR-024` | long form segmented with sentence_claim_refs | unsupported sentence rejection |
| `AIR-026` | P1 | EN writer and bilingual sentence alignment | `backend/services/research_factory/writers_en.py` | `AIR-025` | EN adds no unsupported facts | EV-013 |
| `AIR-027` | P1 | Han-Nom editorial notes generator | `backend/services/research_factory/han_nom_writer.py` | `AIR-018;AIR-024` | no unverified transcript accepted | glyph review gate |
| `AIR-028` | P1 | Museum label/captions/3D-AR scripts | `backend/services/research_factory/media_writers.py` | `AIR-024` | rights + hotspot + citations + 2D fallback | asset rights blocked |
| `AIR-029` | P1 | ELLO/LMS assessment content generator | `backend/services/research_factory/lesson_writer.py` | `AIR-024;R3-001` | quiz answer source traceable | ELLO evidence rubric tests |
| `AIR-030` | P0 | Full article structured block assembly | `backend/services/research_factory/content_assembler.py` | `AIR-025;AIR-026` | all sections diff/version + citations | missing block alerts |
| `AIR-031` | P0 | Independent QA runner 10 agents | `backend/services/research_factory/qa.py` | `AIR-030;AIR-004` | P08 10 results; P0 blockers stop | CONC-007 |
| `AIR-032` | P0 | Adversarial injection/rights test suite | `tests/research_factory/` | `AIR-031` | high severity zero in pilot test suite | EV-007/008/014 |
| `AIR-033` | P0 | Two-human signed review/approval | `backend/services/research_factory/approvals.py` | `AIR-031;AIR-008` | AI cannot self-approve; 2 distinct users | CONC-008 |
| `AIR-034` | P1 | Editorial review UI + diff + conflict notes | `frontend/src/app/admin/research-factory/reviews/` | `AIR-033` | lineage and source viewer visible | multi-reviewer conflict |
| `AIR-035` | P0 | Atomic release manifest + pointer swap | `backend/services/research_factory/releases.py` | `AIR-033;AIR-007` | no partial public updates | CONC-009 |
| `AIR-036` | P0 | Connect approved content to History Tutor | `backend/services/history_tutor.py` | `AIR-035;R5-001` | draft never searchable; version lock | unreviewed leakage |
| `AIR-037` | P1 | Connect article/ELLO content UI and exports | `frontend/src/app/` | `AIR-035;AIR-029` | citation click resolves locators, 2D works | public e2e |
| `AIR-038` | P0 | Historical correction/rights revoke cascade | `backend/services/research_factory/corrections.py` | `AIR-035;AIR-015` | rights withdrawal invalidates public assets | EV-010/011 |
| `AIR-039` | P1 | Scheduled P11 watchers + incremental reruns | `backend/services/research_factory/monitoring.py` | `AIR-038` | changes create new run not overwrite | CONC-010 |
| `AIR-040` | P1 | Costs/latency/quality dashboard | `frontend/src/app/admin/research-factory/analytics/` | `AIR-009;AIR-031` | denominators and active concurrency shown | telemetry reproducibility |
| `AIR-041` | P0 | 3-relief pilot with experts | `docs/research_factory/pilot/` | `AIR-039` | all 12 phases with audited human signoff | pilot dossier review |
| `AIR-042` | P1 | 9×18 batch rollout controlled by global cap | `backend/services/research_factory/batch.py` | `AIR-041` | 162 scheduled fairly without quota storm | CONC-012 |
| `AIR-043` | P1 | Research reproducibility export for Q2/AI papers | `backend/services/research_factory/research_export.py` | `AIR-041` | provenance and eval release frozen, no student PII | paper audit |
| `AIR-044` | P1 | Deployment runbooks provider outage/rollback | `docs/runbooks/research_factory.md` | `AIR-035;AIR-041` | on-call steps and drills tested | recovery rehearsal |
| `AIR-045` | P1 | Per-provider permission and TDM compliance audit | `docs/legal/research_factory_rights.md` | `AIR-015;AIR-041` | evidence of approved scope and grant | lawyer/policy signoff |

### C10.3. Ticket detail và audit evidence bắt buộc

#### AIR-001 — Create durable pipeline domain package (P0)

**Target source:** `backend/services/research_factory/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `R0-006`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** Run manifests and agent roles pinned. **Negative regression:** schema and unit. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-002 — Add Alembic run/phase/job migrations (P0)

**Target source:** `backend/alembic/versions/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-001`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** 10-slot constraints and foreign keys pass. **Negative regression:** migration forward/back. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-003 — Implement broker+worker engine selection ADR (P0)

**Target source:** `backend/services/research_factory/orchestrator.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-002`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** restart-safe persistent jobs and gate. **Negative regression:** crash kill -9. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-004 — Implement strict 10-worker fan-out/fan-in (P0)

**Target source:** `backend/services/research_factory/orchestrator.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-003`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** 10 distinct slots per wave; all terminal before fanin. **Negative regression:** CONC-001/002/003. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-005 — Implement global provider/concurrency quotas (P0)

**Target source:** `backend/services/research_factory/providers/base.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-003`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** limits across all runs not just per process. **Negative regression:** CONC-003/004/012. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-006 — Add idempotency keys + leases + DLQ (P0)

**Target source:** `backend/services/research_factory/queues.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-003`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** retry never double writes claims. **Negative regression:** CONC-005/006. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-007 — Implement private immutable artifacts+hashes (P0)

**Target source:** `backend/services/research_factory/artifacts.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-002`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** mutations create new SHA objects. **Negative regression:** tamper/hash test. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-008 — Admin RBAC and audit for research factory (P0)

**Target source:** `backend/routers/research_factory.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-002`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** nonstaff denied; per-scope access. **Negative regression:** IDOR/role matrix. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-009 — Rate and cost accounting (P0)

**Target source:** `backend/services/research_factory/budget.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-005`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** hard stop at configured budget. **Negative regression:** quota simulation. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-010 — Ten-lane frontend dashboard (P1)

**Target source:** `frontend/src/app/admin/research-factory/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-004;AIR-008`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** dispatched and actually running separate. **Negative regression:** playwright accessibility. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-011 — Build source candidate registry (P0)

**Target source:** `backend/services/research_factory/discovery.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-007`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** query traces and DOI lineage stored. **Negative regression:** fake metadata reject. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-012 — Build provider allowlists and usage policies (P0)

**Target source:** `backend/services/research_factory/providers/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-011`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** forbidden domains/uses blocked. **Negative regression:** license/captcha negative. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-013 — Official/museum/research metadata connectors (P1)

**Target source:** `backend/services/research_factory/providers/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-012`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** metadata candidates with exact URLs+times. **Negative regression:** stub adapter contracts. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-014 — Authorized download & source snapshotter (P1)

**Target source:** `backend/services/research_factory/acquisition.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-012;AIR-007`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** immutable snapshot only rights permitted. **Negative regression:** MIME/redirect/payload tests. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-015 — Source rights action matrix (P0)

**Target source:** `backend/services/research_factory/rights.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-012`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** no unknown=>grant conversion. **Negative regression:** rights decision fuzz. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-016 — Source passages/pages schema migration (P0)

**Target source:** `backend/alembic/versions/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-002`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** page/index/bbox/span/edition linked. **Negative regression:** FK/deletion tests. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-017 — PDF/HTML page parser + OCR quality ledger (P1)

**Target source:** `backend/services/research_factory/extraction.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-014;AIR-016`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** source passage offsets verifiable. **Negative regression:** two-column/missing-glyph fixtures. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-018 — Han-Nom transcription human review UI (P0)

**Target source:** `frontend/src/app/admin/research-factory/ocr/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-017;AIR-008`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** no unreviewed original strings published. **Negative regression:** EV-005. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-019 — Atomic claim/passage extraction pipeline (P0)

**Target source:** `backend/services/research_factory/claims.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-017`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** claims must bind source passage or gap. **Negative regression:** EV-001/002/012. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-020 — Quote+locator deterministic verifier (P0)

**Target source:** `backend/services/research_factory/citations.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-016;AIR-019`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** fake quote or wrong page blocked. **Negative regression:** EV-001/002. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-021 — Historical source independence graph (P1)

**Target source:** `backend/services/research_factory/source_graph.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-011`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** two mirrors count one origin. **Negative regression:** EV-003. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-022 — Cross-source conflict detector (P1)

**Target source:** `backend/services/research_factory/corroboration.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-020;AIR-021`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** contradictory evidence not discarded. **Negative regression:** EV-004. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-023 — Temporal geo+identity reviewer (P1)

**Target source:** `backend/services/research_factory/ontology.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-019`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** date_precision, map status enforced. **Negative regression:** EV-006. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-024 — Evidence dossier builder 162 coverage (P0)

**Target source:** `backend/services/research_factory/dossiers.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-022`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** no claims without bindings; gap flags. **Negative regression:** coverage grid tests. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-025 — Full VI article source-bound writer (P0)

**Target source:** `backend/services/research_factory/writers.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-024`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** long form segmented with sentence_claim_refs. **Negative regression:** unsupported sentence rejection. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-026 — EN writer and bilingual sentence alignment (P1)

**Target source:** `backend/services/research_factory/writers_en.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-025`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** EN adds no unsupported facts. **Negative regression:** EV-013. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-027 — Han-Nom editorial notes generator (P1)

**Target source:** `backend/services/research_factory/han_nom_writer.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-018;AIR-024`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** no unverified transcript accepted. **Negative regression:** glyph review gate. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-028 — Museum label/captions/3D-AR scripts (P1)

**Target source:** `backend/services/research_factory/media_writers.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-024`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** rights + hotspot + citations + 2D fallback. **Negative regression:** asset rights blocked. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-029 — ELLO/LMS assessment content generator (P1)

**Target source:** `backend/services/research_factory/lesson_writer.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-024;R3-001`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** quiz answer source traceable. **Negative regression:** ELLO evidence rubric tests. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-030 — Full article structured block assembly (P0)

**Target source:** `backend/services/research_factory/content_assembler.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-025;AIR-026`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** all sections diff/version + citations. **Negative regression:** missing block alerts. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-031 — Independent QA runner 10 agents (P0)

**Target source:** `backend/services/research_factory/qa.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-030;AIR-004`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** P08 10 results; P0 blockers stop. **Negative regression:** CONC-007. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-032 — Adversarial injection/rights test suite (P0)

**Target source:** `tests/research_factory/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-031`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** high severity zero in pilot test suite. **Negative regression:** EV-007/008/014. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-033 — Two-human signed review/approval (P0)

**Target source:** `backend/services/research_factory/approvals.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-031;AIR-008`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** AI cannot self-approve; 2 distinct users. **Negative regression:** CONC-008. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-034 — Editorial review UI + diff + conflict notes (P1)

**Target source:** `frontend/src/app/admin/research-factory/reviews/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-033`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** lineage and source viewer visible. **Negative regression:** multi-reviewer conflict. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-035 — Atomic release manifest + pointer swap (P0)

**Target source:** `backend/services/research_factory/releases.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-033;AIR-007`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** no partial public updates. **Negative regression:** CONC-009. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-036 — Connect approved content to History Tutor (P0)

**Target source:** `backend/services/history_tutor.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-035;R5-001`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** draft never searchable; version lock. **Negative regression:** unreviewed leakage. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-037 — Connect article/ELLO content UI and exports (P1)

**Target source:** `frontend/src/app/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-035;AIR-029`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** citation click resolves locators, 2D works. **Negative regression:** public e2e. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-038 — Historical correction/rights revoke cascade (P0)

**Target source:** `backend/services/research_factory/corrections.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-035;AIR-015`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** rights withdrawal invalidates public assets. **Negative regression:** EV-010/011. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-039 — Scheduled P11 watchers + incremental reruns (P1)

**Target source:** `backend/services/research_factory/monitoring.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-038`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** changes create new run not overwrite. **Negative regression:** CONC-010. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-040 — Costs/latency/quality dashboard (P1)

**Target source:** `frontend/src/app/admin/research-factory/analytics/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-009;AIR-031`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** denominators and active concurrency shown. **Negative regression:** telemetry reproducibility. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-041 — 3-relief pilot with experts (P0)

**Target source:** `docs/research_factory/pilot/` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-039`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** all 12 phases with audited human signoff. **Negative regression:** pilot dossier review. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-042 — 9×18 batch rollout controlled by global cap (P1)

**Target source:** `backend/services/research_factory/batch.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-041`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** 162 scheduled fairly without quota storm. **Negative regression:** CONC-012. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-043 — Research reproducibility export for Q2/AI papers (P1)

**Target source:** `backend/services/research_factory/research_export.py` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-041`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** provenance and eval release frozen, no student PII. **Negative regression:** paper audit. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-044 — Deployment runbooks provider outage/rollback (P1)

**Target source:** `docs/runbooks/research_factory.md` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-035;AIR-041`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** on-call steps and drills tested. **Negative regression:** recovery rehearsal. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

#### AIR-045 — Per-provider permission and TDM compliance audit (P1)

**Target source:** `docs/legal/research_factory_rights.md` (`[PLANNED PATH]` nếu chưa có). **Dependency:** `AIR-015;AIR-041`. **Scope:** code/config/schema/UI/infra tối thiểu để hoàn thành đúng chức năng tên ticket; không cho agent tự mở rộng sang dữ liệu học sinh, quyền partner hoặc public content ngoài nhiệm vụ. **Input:** versioned artifact từ các phase trước hoặc nguồn đã được human cấp quyền. **Output:** record/artifact immutable có ID, hash, request_id và trạng thái. **Acceptance:** evidence of approved scope and grant. **Negative regression:** lawyer/policy signoff. **Definition of Done:** test có fixture/expected output, API/schema migration backward compatibility, staging smoke/telemetry, reviewer approval và bằng chứng có thể audit trong CI. Nếu không chứng minh acceptance, đánh trạng thái `BLOCKED` hoặc `NOT_VERIFIED` và không claim feature complete.

### C10.4. Kế hoạch triển khai thực tế theo dependency waves, không chạy big-bang

| Wave | Thời gian tương đối (đề xuất, không cam kết) | Tickets | Điều kiện hoàn thành |
|---|---|---|---|
| `W0 — Foundation` | 2–4 sprint tùy đội | AIR-001..AIR-010 | durable 10 worker scheduler, DB, RBAC, budget và UI pilot |
| `W1 — Source Integrity` | 2–4 sprint | AIR-011..AIR-018 | candidate→rights→snapshot→OCR/locator đạt gate |
| `W2 — Evidence Graph` | 2–3 sprint | AIR-019..AIR-024 | claims/contradictions/dossier không bịa nguồn |
| `W3 — Complete Content` | 2–4 sprint | AIR-025..AIR-030 | full VI/EN + ELLO/3D-AR packages có claim refs |
| `W4 — QA & Review` | 2–3 sprint | AIR-031..AIR-034 | independent 10-agent QA và human approval |
| `W5 — Publish & Monitoring` | 2–3 sprint | AIR-035..AIR-040 | atomic public release, rollback/correction |
| `W6 — Pilot/Scale/Research` | 3–6 sprint tùy kết quả | AIR-041..AIR-045 | 3-relief pilot, 9×18 controlled rollout, verified evidence exports |

Sprint duration/team size phải được thống nhất khi giao việc; lịch trên không phải cam kết hoàn thành trong 15 sprint và không có nghĩa 162 bản ghi sẽ được duyệt đủ nhanh nếu tư liệu/nhân sự chuyên môn còn thiếu. Có thể làm song song trong wave giữa backend/frontend/QA khi dependencies rõ, nhưng **bên trong một research run luôn barrier theo P00–P11**.

### C10.5. Definition of MVP và Version 1 production

**MVP (trước khi tự tìm sử liệu diện rộng):** một pilot 3 relief có 10 agent mỗi phase ở staging; ít nhất một nguồn hợp lệ được human kiểm, một claim có page locator đúng, full VI/EN article AI_DRAFT, ELL0, 10-reviewer agent QA, human signoff và publish/rollback thành công. Nếu một mục không đạt, không tuyên bố production-ready.

**Version 1:** 162 subjects registered, source acquisition rights registry vận hành, 9×18 dashboard, migration/queue resilient, multi-version long-form drafts, human review queue, release manifests và public citation viewer. **Không bắt buộc xuất bản đủ 162 mục nếu thiếu nguồn**; báo công khai coverage từng trạng thái.

**Version 2:** source monitoring, correction cascade, language content and independent validation benchmark, scaling policy theo token/cost/provider quota, research export reproducibility đủ để kiểm tra paper claims.

---
