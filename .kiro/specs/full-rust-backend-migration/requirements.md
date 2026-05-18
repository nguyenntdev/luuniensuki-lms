# Requirements Document

## Introduction

This feature migrates the entire Luuniensuki LMS HTTP backend from the existing Python FastAPI service (`backend/main.py`, ~20,194 lines, 290 endpoints, 47 service modules) to a Rust service (`backend-rust/`) using a strangler-fig approach. The Rust service already exists as a partial gateway that natively serves a small set of endpoints (`/health`, `/api/v1/internal/db-health`, `/api/v1/content/ratings`, `/api/v1/tags`, `/api/v1/badges`, `/api/v1/users/me/streak`, `/api/v1/ranks`) and proxies the remainder to Python. The migration is complete when the Python API container is retired and the Rust service answers 100% of HTTP traffic with byte-compatible response shapes against the existing PostgreSQL schema. The live AI teacher worker (`services/ai_teacher_agent/`) remains in Python and is out of scope.

The migration MUST be observable: each endpoint group is tracked as a discrete phase, and phase completion is verifiable through automated contract tests, traffic metrics, and a checkbox-style progress ledger that can be ticked off as work lands.

## Glossary

- **Rust_Service**: The Rust HTTP server under `/opt/luuniensuki-lms/backend-rust/` that will own all production HTTP traffic at completion of this migration.
- **Python_Service**: The existing FastAPI server under `/opt/luuniensuki-lms/backend/` that currently serves all 290 endpoints.
- **Gateway_Mode**: Operational mode in which `Rust_Service` proxies a request to `Python_Service` because no native Rust handler is registered for the route.
- **Native_Mode**: Operational mode in which `Rust_Service` answers a request from its own handler without contacting `Python_Service`.
- **Endpoint_Group**: A coherent set of routes that share a service module in `backend/services/` (e.g., auth, quizzes, lessons, classrooms, badges) and are migrated together as one phase.
- **Contract_Test**: An automated test that issues the same request to `Python_Service` and `Rust_Service` and asserts that HTTP status, headers (subset), and JSON body are equivalent under a documented equivalence relation.
- **Response_Shape**: The JSON body schema, field names, field types, ordering of arrays where the Python implementation is deterministic, HTTP status code, and `Content-Type` header for a given route and request.
- **Migration_Ledger**: The markdown file tracked in the repository (`docs/plan/full-rust-backend-migration-ledger.md`) that lists every `Endpoint_Group` and every individual route as checkbox items, updated as each unit reaches `Native_Mode`.
- **Cutover**: The deployment event in which the Python API container is removed from the production deployment and `Rust_Service` becomes the sole HTTP backend.
- **Auth_Token**: A JSON Web Token issued by either `Python_Service` or `Rust_Service` that authenticates a user and is accepted by both services for the duration of the migration.
- **Password_Hash**: A stored credential hash in the `users` table produced by either bcrypt or argon2id, originally written by `Python_Service` and which `Rust_Service` MUST verify without rehashing on read.
- **Database**: The shared PostgreSQL instance whose schema is owned by SQLAlchemy models in `backend/models.py` and which both services read and write during the migration.
- **AI_Teacher_Worker**: The Python process under `backend/services/ai_teacher_agent/` that performs live AI tutoring; out of scope for migration but still reachable from `Rust_Service` over its existing interface.
- **Contract_Snapshot**: A recorded request/response pair captured from `Python_Service` for a specific route and input, stored in the contract test fixture directory and used as the golden reference for `Contract_Test` runs.
- **Phase**: A unit of migration work that covers one `Endpoint_Group`, has its own entry in the `Migration_Ledger`, and is considered complete only when all its acceptance criteria are met.

## Requirements

### Requirement 1: Migration Plan and Ledger

**User Story:** As the engineering owner, I want a single tracked migration plan that enumerates every endpoint group and every route as a checkable item, so that progress is visible and the user's request to "tick off each piece as it is finished" is honored.

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL publish a `Migration_Ledger` file at `docs/plan/full-rust-backend-migration-ledger.md` whose content lists every `Endpoint_Group` derived from `backend/services/` and `backend/routes/` as a top-level checkbox item, where the file is considered published only when its content satisfies this listing requirement.
2. THE Migration_Ledger SHALL list every HTTP route currently served by `Python_Service` (HTTP method plus path) as a nested checkbox under its owning `Endpoint_Group`.
3. WHEN a route reaches `Native_Mode` in production and passes its `Contract_Test`, THE Migration_Ledger SHALL be updated in the same pull request to mark that route's checkbox as completed.
4. WHEN every route inside an `Endpoint_Group` is checked, THE Migration_Ledger SHALL mark the group's top-level checkbox as completed.
5. THE Migration_Ledger SHALL record, for each `Endpoint_Group`, the commit SHA and date at which the group reached 100% native completion.
6. IF the count of routes in `Python_Service` changes (a route is added, removed, or renamed) during the migration, THEN THE Migration_Ledger SHALL be updated within the same pull request that introduces the change so that the ledger and the live route table stay in sync.

### Requirement 2: Endpoint Inventory and Coverage

**User Story:** As the engineering owner, I want a verifiable inventory of every endpoint that must be migrated, so that no route is silently missed during cutover.

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL produce a route inventory file at `backend-rust/docs/route-inventory.json` that lists every HTTP method and path served by `Python_Service` with the owning `Endpoint_Group`.
2. THE route inventory SHALL be generated by a reproducible script that introspects `Python_Service` (for example by importing the FastAPI app and walking `app.routes`) so that the inventory is regeneratable on demand.
3. WHEN the route inventory is regenerated, THE Rust_Service maintainer SHALL fail the build IF any route present in `Python_Service` is missing from `backend-rust/docs/route-inventory.json`.
4. THE Rust_Service SHALL expose an internal endpoint `GET /api/v1/internal/route-coverage` that returns, for each entry in the route inventory, whether the route is currently in `Native_Mode` or `Gateway_Mode`.
5. WHEN the inventory contains a route that is neither registered as a native handler nor matched by the proxy fallback, THE Rust_Service SHALL fail its startup health check with a non-zero exit code.

### Requirement 3: Strangler Gateway Behavior

**User Story:** As an operator, I want every request to be served correctly throughout the migration whether or not its handler has been ported, so that the system remains usable as work progresses.

#### Acceptance Criteria

1. WHEN the Rust_Service receives an HTTP request whose method and path match a registered native handler, THE Rust_Service SHALL serve the request in `Native_Mode` without contacting `Python_Service`.
2. WHEN the Rust_Service receives an HTTP request whose method and path do not match a registered native handler but do match the route inventory, THE Rust_Service SHALL serve the request in `Gateway_Mode` by proxying to `Python_Service` and returning its response unchanged in body and status code.
3. WHEN the Rust_Service serves a request in `Gateway_Mode`, THE Rust_Service SHALL forward all request headers required for authentication and content negotiation, including `Authorization`, `Cookie`, `Content-Type`, and `Accept`.
4. WHEN the Rust_Service serves a request in `Gateway_Mode`, THE Rust_Service SHALL preserve the response status code, response body bytes, and the `Content-Type` and `Content-Length` response headers as received from `Python_Service`.
5. IF the Rust_Service fails to reach `Python_Service` while attempting `Gateway_Mode`, THEN THE Rust_Service SHALL respond with HTTP status 502 and a JSON body of the shape `{"detail": "upstream unavailable"}`.
6. THE Rust_Service SHALL emit, on every served request, exactly one structured log entry that records the HTTP method, path, response status, latency in milliseconds, and the actual mode used to serve the request, where the mode field SHALL be exactly one of `native` or `gateway`.

### Requirement 4: Contract Parity with Python_Service

**User Story:** As a frontend developer, I want every migrated endpoint to return the same response shape as the current Python implementation, so that the Next.js frontend continues to work without changes.

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL maintain a `Contract_Test` suite at `backend-rust/tests/contract/` that runs the same request against `Python_Service` and `Rust_Service` and compares the responses.
2. WHEN a `Contract_Test` runs for a route in `Native_Mode`, THE Contract_Test SHALL assert that the HTTP status code from `Rust_Service` equals the HTTP status code from `Python_Service` for the same input.
3. WHEN a `Contract_Test` runs for a route in `Native_Mode`, THE Contract_Test SHALL assert that the JSON body from `Rust_Service` is structurally equal to the JSON body from `Python_Service` under a documented equivalence relation that allows for differences only in fields explicitly listed as ignored (for example `server_time` or `request_id`).
4. WHEN a `Contract_Test` runs for a route in `Native_Mode`, THE Contract_Test SHALL assert that the `Content-Type` response header from `Rust_Service` equals the `Content-Type` response header from `Python_Service`.
5. WHERE a route's response is an array whose order is deterministic in `Python_Service` (for example sorted by `created_at`), THE Rust_Service SHALL produce the same order.
6. THE Contract_Test suite SHALL include `Contract_Snapshot` fixtures captured from `Python_Service` so that contract tests can run when `Python_Service` is offline.
7. WHEN a `Contract_Test` fails for any route, THE Rust_Service maintainer SHALL block that route from being marked complete in the `Migration_Ledger` until the test passes.
8. WHEN a route is migrated, THE Contract_Test suite SHALL include at minimum one happy-path test, one input-validation-error test, and one authentication-or-authorization-error test for that route.

### Requirement 5: Authentication and Authorization Compatibility

**User Story:** As an existing user, I want my current login session and password to keep working during and after the migration, so that I am not forced to re-register or reset my password.

#### Acceptance Criteria

1. THE Rust_Service SHALL accept and verify any `Auth_Token` issued by `Python_Service` whose signature, claims, and expiry are valid under the current shared JWT secret and algorithm.
2. THE Python_Service SHALL accept and verify any `Auth_Token` issued by `Rust_Service` for as long as both services run in production during the migration.
3. WHEN a user submits credentials to the Rust_Service login endpoint, THE Rust_Service SHALL verify the submitted password against the stored `Password_Hash` whether the hash is bcrypt or argon2id, without rehashing the stored value on a successful match.
4. WHEN a user registers through the Rust_Service, THE Rust_Service SHALL produce a `Password_Hash` using the same algorithm and parameters that the Python_Service currently uses for new registrations.
5. WHEN the Rust_Service issues an `Auth_Token`, THE Rust_Service SHALL produce a token that contains the same claims (subject, issued-at, expiry, role) as a token issued by `Python_Service` for the same user.
6. IF an `Auth_Token` presented to Rust_Service is expired, malformed, or signed with an unknown key, THEN THE Rust_Service SHALL return HTTP status 401 with a JSON body that exactly matches the shape and field values currently returned by `Python_Service` for the same condition, and any deviation in the JSON body SHALL block migration of the affected route.
7. WHILE both services are running, THE Rust_Service and Python_Service SHALL share the same JWT signing key and the same `users.password_hash` column without separate copies.

### Requirement 6: Database Schema Stability

**User Story:** As a database owner, I want the migration to leave the PostgreSQL schema unchanged, so that no data migration or downtime is required for schema changes.

#### Acceptance Criteria

1. THE Rust_Service SHALL read from and write to the same PostgreSQL `Database` and the same tables that `Python_Service` reads and writes.
2. THE Rust_Service maintainer SHALL NOT introduce schema migrations that alter, drop, or rename existing tables, columns, indexes, or constraints owned by `Python_Service` as part of this feature.
3. WHERE the Rust_Service requires a new index for performance, THE Rust_Service maintainer SHALL add the index as a non-breaking, additive migration that `Python_Service` continues to function against without code change.
4. WHEN the Rust_Service writes a row that is also written by `Python_Service` (for example a `quiz_attempt` insert), THE Rust_Service SHALL produce a row whose column values, including auto-generated fields such as timestamps, UUIDs, and database-assigned identifiers, are identical to what `Python_Service` would have written for the same input under the same business rules and the same database state.
5. IF a database constraint violation occurs during a write, THEN THE Rust_Service SHALL return the same HTTP status code that `Python_Service` returns for the same violation on the same route.

### Requirement 7: Per-Phase Migration of Endpoint Groups

**User Story:** As an engineer, I want each endpoint group to be migrated as a discrete phase with clear entry and exit criteria, so that work is reviewable in bounded chunks and the system stays releasable.

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL migrate endpoints in `Phase` units, where each `Phase` covers exactly one `Endpoint_Group` from `backend/services/`.
2. WHEN a `Phase` begins, THE Rust_Service maintainer SHALL open a tracking entry in the `Migration_Ledger` for that `Phase` that lists every route in the group as an unchecked checkbox.
3. WHEN every route inside a `Phase` reaches `Native_Mode`, every route's `Contract_Test` passes in continuous integration, and the `Migration_Ledger` entry for that `Phase` exists with all route checkboxes present, THE Rust_Service maintainer SHALL mark the `Phase` as complete in the `Migration_Ledger` and record the commit SHA and date; IF any of these prerequisites is unmet, THEN THE `Phase` SHALL NOT be marked complete.
4. THE Rust_Service maintainer SHALL complete the following Phases (each a separate `Endpoint_Group`) before declaring the migration finished: auth (register, login, refresh, logout, password reset, age verify), users and profile, lessons, quizzes and quiz attempts, progress and streaks, badges and quests, classrooms and memberships, leaderboards, notifications, push notifications, file uploads (avatars and lesson media), admin content management, admin analytics, crash reports, RAG and AI tutor proxy or native rewrite, and any remaining miscellaneous routes from the inventory.
5. WHILE a `Phase` is in progress and `Python_Service` is reachable, THE Rust_Service SHALL serve routes from that `Endpoint_Group` in `Gateway_Mode` if their native handler is not yet registered; IF `Python_Service` is unreachable while a `Phase` is in progress, THEN THE Rust_Service SHALL respond per Requirement 3.5 (HTTP 502 with `{"detail": "upstream unavailable"}`) for routes whose native handler is not yet registered, and routes without a native handler MAY remain unavailable until they are migrated.
6. WHEN a `Phase` is in progress and its first route is registered as a native handler, THE Rust_Service SHALL pass `Contract_Test` for that route in continuous integration before the route's checkbox is marked complete.

### Requirement 8: File Upload Handling

**User Story:** As a user, I want to upload my avatar and lesson media to the Rust backend without behavioral change, so that uploads continue to work after migration.

#### Acceptance Criteria

1. WHEN the Rust_Service receives an `multipart/form-data` upload on a migrated upload route, THE Rust_Service SHALL accept the same field names, file size limits, and MIME types that `Python_Service` accepts for that route.
2. WHEN the Rust_Service stores an uploaded file, THE Rust_Service SHALL write to the same storage location and produce the same publicly addressable URL pattern that `Python_Service` produces for the same route.
3. IF an upload exceeds the file size limit defined for a route, THEN THE Rust_Service SHALL return the same HTTP status code and JSON error body that `Python_Service` returns for the same condition.
4. WHEN the Rust_Service rejects an upload due to MIME type, THE Rust_Service SHALL return the same HTTP status code and JSON error body that `Python_Service` returns for the same condition.

### Requirement 9: AI Tutor and RAG Routing

**User Story:** As a learner using the AI tutor, I want my requests to keep reaching the live Python AI worker, so that the in-scope HTTP migration does not break the out-of-scope tutoring feature.

#### Acceptance Criteria

1. WHEN the Rust_Service receives a request on a route owned by the `AI_Teacher_Worker`, THE Rust_Service SHALL forward the request to the existing AI worker interface (HTTP or queue) used by `Python_Service` today.
2. THE Rust_Service maintainer SHALL document, in `backend-rust/docs/ai-tutor-routing.md`, every route that depends on `AI_Teacher_Worker` and the chosen routing strategy (proxy versus native rewrite) for each route.
3. IF a decision is made to natively rewrite a non-live RAG route in Rust, THEN THE rewrite SHALL satisfy the same `Contract_Test` requirements as any other migrated route.
4. WHILE the migration is in progress, THE Rust_Service SHALL NOT alter the `AI_Teacher_Worker` Python process or its public interface.

### Requirement 10: Cutover and Python Retirement

**User Story:** As an operator, I want a controlled cutover that retires the Python API container only after the Rust service fully covers HTTP traffic, so that production stays healthy.

#### Acceptance Criteria

1. WHEN every entry in `backend-rust/docs/route-inventory.json` is marked as native in `GET /api/v1/internal/route-coverage` and every route's `Contract_Test` passes in continuous integration, THE Rust_Service maintainer SHALL declare the migration ready for `Cutover`.
2. WHEN `Cutover` is performed, THE deployment configuration SHALL stop routing external HTTP traffic to `Python_Service` and route 100% of external HTTP traffic to `Rust_Service`.
3. WHEN `Cutover` is performed, THE Rust_Service SHALL no longer require `Python_Service` to be reachable for any route in the route inventory.
4. WHEN the Python API container is retired, THE deployment configuration SHALL remove the `Python_Service` container from the production compose or orchestration manifests in the same change set, except for the separate `AI_Teacher_Worker` deployment which SHALL remain.
5. WHILE the migration is in progress and `Cutover` has not occurred, THE Rust_Service SHALL be able to fall back to `Gateway_Mode` for any inventory route, so that an emergency revert to Python handling is possible without redeployment.
6. IF the post-`Cutover` error rate measured at the Rust_Service edge exceeds the pre-`Cutover` baseline by more than 1 percentage point over a rolling 15-minute window, THEN THE Rust_Service maintainer SHALL roll the deployment back to a configuration that re-enables `Gateway_Mode` against `Python_Service`.

### Requirement 11: Build, Memory, and Toolchain Constraints

**User Story:** As an operator on a low-memory build host, I want the Rust build to remain feasible on the existing infrastructure, so that introducing Axum and SQLx does not break the build pipeline.

#### Acceptance Criteria

1. THE Rust_Service SHALL build successfully on the existing build host configuration without exceeding the documented host memory budget recorded in `backend-rust/docs/build-budget.md`.
2. WHEN a new dependency is introduced (for example Axum, SQLx, or a JSON library), THE Rust_Service maintainer SHALL record in `backend-rust/docs/build-budget.md` the resulting peak resident set size of the release build, measured on the build host.
3. WHERE the build host cannot complete a release build due to memory pressure, THE Rust_Service maintainer SHALL configure the build (for example via `CARGO_BUILD_JOBS`, `codegen-units`, or `lto` settings) so that the build completes within the documented memory budget.
4. THE Rust_Service maintainer SHALL pin every direct dependency to an exact version in `backend-rust/Cargo.toml` for the duration of the migration.

### Requirement 12: Observability and Operational Readiness

**User Story:** As an operator, I want logs, metrics, and health checks from the Rust service to match or exceed what Python provides, so that I can run the system in production with confidence.

#### Acceptance Criteria

1. THE Rust_Service SHALL expose `GET /health` returning HTTP status 200 with a JSON body of the shape `{"status": "ok"}` when the process is up and the database connection is healthy.
2. THE Rust_Service SHALL expose `GET /api/v1/internal/db-health` returning HTTP status 200 when a round-trip query against `Database` succeeds, and HTTP status 503 otherwise.
3. WHEN the Rust_Service serves any request, THE Rust_Service SHALL emit a structured log line containing a request identifier, HTTP method, path, status code, latency in milliseconds, and serving mode (`native` or `gateway`).
4. WHEN the Rust_Service handler returns HTTP status 5xx, THE Rust_Service SHALL emit a structured log line at `error` level that includes the request identifier, the route, and a stack trace or error chain.
5. THE Rust_Service SHALL expose a Prometheus-compatible metrics endpoint at `GET /metrics` that publishes per-route request counts, per-route latency histogram, and per-route error counts segmented by serving mode (`native` or `gateway`).

### Requirement 13: Rollback Safety per Phase

**User Story:** As an operator, I want any individual migrated phase to be revertible without redeploying, so that a regression in one endpoint group does not require rolling back the whole release.

#### Acceptance Criteria

1. THE Rust_Service SHALL read a runtime configuration map (file or environment variable) that, for any route in the inventory, can force that route into `Gateway_Mode` even if a native handler is registered.
2. WHEN a route is configured in the runtime map as `gateway`, THE Rust_Service SHALL serve that route in `Gateway_Mode` without restarting the process.
3. WHEN a route is configured in the runtime map as `native`, THE Rust_Service SHALL serve that route from its native handler if one is registered, and SHALL fail startup health check IF no native handler exists for that route after `Cutover`.
4. WHEN the runtime map is updated while the process is running, THE Rust_Service SHALL re-read the map and apply the new mode to subsequent requests, where the re-read SHALL occur within 30 seconds of the update under normal operation; THE Rust_Service SHALL preserve in-flight requests across map re-reads even if a re-read exceeds the 30-second target, and THE Rust_Service MAY drop in-flight requests during any re-read operation regardless of whether configuration changed only when explicitly required by an operator-triggered restart.
