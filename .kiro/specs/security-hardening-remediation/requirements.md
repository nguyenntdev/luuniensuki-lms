# Requirements Document

## Introduction

This specification defines a security- and quality-remediation initiative for the
**luuniensuki-lms** monorepo. The monorepo contains three deployable components:

- **Python_Backend**: a FastAPI application rooted at the repository root (`config.py`, `main.py`, `errors.py`, `rbac.py`, and supporting modules).
- **Rust_Backend**: an axum-based service under `backend-rust/` (`config.rs`, `auth.rs`).
- **Frontend**: a Next.js application under `frontend/` (`src/lib/api.js`, `middleware.ts`, component files).

An audit identified findings spanning authentication secrets, CORS policy, assessment
integrity, input validation, authorization, code structure, and type safety. This document
captures each finding as one or more discrete, testable requirements written in EARS-style
acceptance criteria, grouped by theme and ordered by severity (Critical → High → Medium → Low).
Requirements are implementation-agnostic but precise enough to verify through automated tests.

A cross-cutting section captures the shared JWT contract compatibility constraint between the
Python and Rust backends, an automated-test verification mandate for every fix, and a
secrets-management/rollout requirement that prohibits insecure secret defaults in any environment.

### Scope split

Two large structural efforts originally captured here have been moved to dedicated specs so the
security-critical fixes can ship independently:

- **`backend-modularization`** — decomposing the monolithic `main.py` (was Requirement 16).
- **`frontend-consolidation-typing`** — TypeScript migration, typed API models, and removing
  orphaned root-level duplicate components (was Requirement 21).

The narrow, security-relevant frontend behaviors (Requirements 4, 13, 22, 23) remain in this spec.
Requirement numbers 16 and 21 are retained as out-of-scope markers to keep cross-references stable.

## Glossary

- **Python_Backend**: The FastAPI service rooted at the repository root, entered via `main.py`.
- **Rust_Backend**: The axum service under `backend-rust/`, configured via `config.rs` and authenticated via `auth.rs`.
- **Frontend**: The Next.js client application under `frontend/`.
- **Config_Loader**: The configuration-loading component of a backend (`config.py` for Python_Backend, `config.rs` for Rust_Backend).
- **Auth_Service**: The component of a backend responsible for issuing and validating JWT access tokens.
- **JWT_Contract**: The shared agreement on JWT signing algorithm, signing secret, and claim set that allows tokens issued by one backend to be accepted by the other.
- **Production_Environment**: Any deployment whose configured environment indicator denotes production (as opposed to development or test).
- **Secret_Value**: A credential, signing key, or token used for authentication or service-to-service trust (e.g., JWT secret, Janus admin/api secrets, internal tokens, TURN auth secret).
- **Sentinel_Default**: A placeholder secret value shipped in source code such as `"CHANGE_ME_IN_PRODUCTION"`, `"CHANGE_ME_*"`, or an empty string, intended to be overridden before deployment.
- **CORS_Policy**: The Cross-Origin Resource Sharing configuration governing which origins may make credentialed requests.
- **Assessment_Service**: The component responsible for delivering exam questions and grading exam submissions.
- **Answer_Key**: The set of correct answers for an exam, including any `correct_answer` fields.
- **Rate_Limiter**: The component that restricts the number of requests a client may make to an endpoint within a time window.
- **Route_Guard**: The Frontend `middleware.ts` component that gates access to protected routes.
- **Upload_Validator**: The component that validates the content and type of uploaded files.
- **RBAC_Module**: The role-based access-control component (`rbac.py`).
- **Authenticated_User**: A request principal whose identity has been established by a valid JWT.
- **Resource_Owner**: The Authenticated_User to whom a given resource (identified by a path parameter such as `{user_id}`, `{content_id}`, or `{session_id}`) belongs.
- **Security_Headers**: The set of HTTP response headers comprising at minimum Content-Security-Policy (CSP), Strict-Transport-Security (HSTS), and X-Content-Type-Options.
- **Automated_Test**: A test executable in continuous integration without manual intervention that verifies a specific remediation.

---

## Requirements

## Critical Severity Requirements

### Requirement 1: Python JWT signing secret must fail closed in production

**User Story:** As a security engineer, I want the Python_Backend to refuse to start in production with a missing or placeholder JWT signing secret, so that HS256 token forgery via a known default secret is impossible.

#### Acceptance Criteria

1. IF the Python_Backend starts in a Production_Environment AND the JWT signing secret is unset, empty, or equal to the Sentinel_Default `"CHANGE_ME_IN_PRODUCTION"`, THEN THE Config_Loader SHALL halt startup with a fatal configuration error.
2. WHEN the Python_Backend starts in a Production_Environment AND the JWT signing secret is set to a value other than a Sentinel_Default, THE Config_Loader SHALL complete startup successfully.
3. THE Config_Loader SHALL define no usable default value for the JWT signing secret that permits token signing or verification in a Production_Environment.
4. IF the JWT signing secret fails the Production_Environment validation, THEN THE Config_Loader SHALL emit a diagnostic message that identifies the JWT signing secret as the cause without printing the secret value.

### Requirement 2: Rust JWT signing secret must fail closed and stay contract-compatible

**User Story:** As a security engineer, I want the Rust_Backend to refuse to start in production with a missing or placeholder JWT signing secret, so that the shared cross-service token trust cannot be exploited through a known default secret.

#### Acceptance Criteria

1. IF the Rust_Backend starts in a Production_Environment AND the JWT signing secret is unset, empty, or equal to a Sentinel_Default, THEN THE Config_Loader SHALL halt startup with a fatal configuration error.
2. WHEN the Rust_Backend starts in a Production_Environment AND the JWT signing secret is set to a value other than a Sentinel_Default, THE Config_Loader SHALL complete startup successfully.
3. THE Config_Loader SHALL define no usable default value for the JWT signing secret that permits token signing or verification in a Production_Environment.
4. WHEN both backends run in a Production_Environment, THE JWT_Contract SHALL require both backends to derive the JWT signing secret from the same externally supplied Secret_Value so that cross-service token acceptance continues to function.
5. THE Config_Loader SHALL require that no usable fallback default for the JWT signing secret exists before permitting startup with an externally supplied secret.

### Requirement 3: CORS must forbid credentialed wildcard origins

**User Story:** As a security engineer, I want credentialed cross-origin requests restricted to an explicit allowlist, so that the API cannot reflect arbitrary origins while accepting credentials.

#### Acceptance Criteria

1. IF the Python_Backend is configured to allow credentials AND the configured CORS origin list contains a wildcard `"*"`, THEN THE Config_Loader SHALL halt startup with a fatal configuration error.
2. WHEN credentials are allowed, THE CORS_Policy SHALL admit only origins present in an explicit, finite allowlist.
3. WHEN a request presents an Origin that is absent from the configured allowlist, THE Python_Backend SHALL NOT return that Origin in the `Access-Control-Allow-Origin` response header.
4. WHEN a request presents an Origin contained in the configured allowlist, THE Python_Backend SHALL return that exact Origin in the `Access-Control-Allow-Origin` response header.

### Requirement 4: Exam grading must be server-authoritative

**User Story:** As an instructor, I want exams graded only on the server with answer keys never delivered to the client, so that learners cannot bypass assessment integrity.

#### Acceptance Criteria

1. THE Assessment_Service SHALL be the sole authority that grades exam submissions and computes scores.
2. WHEN the Frontend requests exam questions, THE Assessment_Service SHALL return question content that excludes every Answer_Key field, including `correct_answer`.
3. IF a server assessment endpoint returns an error status such as 404 or 405, THEN THE Frontend SHALL surface the error and SHALL NOT grade the exam locally.
4. THE Frontend SHALL contain no static Answer_Key fallback data and SHALL NOT compute exam scores from client-side answer data.
5. WHEN an exam is submitted, THE Assessment_Service SHALL compute the score from server-held answer data and return the authoritative result.

### Requirement 5: Rust media and signaling secrets must fail closed in production

**User Story:** As a security engineer, I want all Rust_Backend service-to-service secrets required in production, so that no media or signaling component trusts a hardcoded placeholder credential.

#### Acceptance Criteria

1. IF the Rust_Backend starts in a Production_Environment AND the Janus admin secret, Janus api secret, or live internal token is unset, empty, or equal to a Sentinel_Default such as `"CHANGE_ME_*"`, THEN THE Config_Loader SHALL halt startup with a fatal configuration error.
2. IF the Rust_Backend starts in a Production_Environment AND the TURN static auth secret is unset or empty, THEN THE Config_Loader SHALL halt startup with a fatal configuration error.
3. THE Config_Loader SHALL define no usable default for the Janus admin secret, Janus api secret, live internal token, or TURN static auth secret that permits use in a Production_Environment.
4. WHEN every required Secret_Value is supplied with a non-default value in a Production_Environment, THE Config_Loader SHALL complete startup successfully.
5. THE Config_Loader SHALL validate all required Secret_Values during configuration loading and halt immediately before any backend component initializes, so that no partial startup state occurs when a required secret is missing.

---

## High Severity Requirements

### Requirement 6: Secure cookies must default on in production

**User Story:** As a security engineer, I want authentication cookies marked Secure in production by default, so that session credentials are never transmitted over plaintext connections.

#### Acceptance Criteria

1. WHEN the Python_Backend issues an authentication cookie in a Production_Environment, THE Python_Backend SHALL set the `Secure` attribute on that cookie by default.
2. WHERE an operator has not explicitly overridden the cookie security setting, THE Config_Loader SHALL resolve the secure-cookie setting to enabled in a Production_Environment.
3. IF the secure-cookie setting is enabled but the `Secure` attribute cannot be applied to an issued cookie, THEN THE Python_Backend SHALL NOT issue the cookie.

### Requirement 7: Module import roots must be standardized

**User Story:** As a developer, I want a single consistent import root across the Python_Backend, so that the application cannot raise a runtime ModuleNotFoundError due to inconsistent import paths.

#### Acceptance Criteria

1. THE Python_Backend SHALL reference internal service modules through a single, consistent import-root convention across all modules.
2. WHEN the Python_Backend is imported and initialized, THE Python_Backend SHALL resolve every internal module import without raising ModuleNotFoundError.
3. THE Python_Backend SHALL contain no mixed import forms (such as `services.*`, `backend.services.*`, and `.services.*`) that refer to the same module.

### Requirement 8: JWT tokens must require an expiration claim

**User Story:** As a security engineer, I want every accepted JWT to carry an expiration, so that tokens cannot remain valid indefinitely.

#### Acceptance Criteria

1. WHEN the Rust_Backend validates a JWT, THE Auth_Service SHALL require the presence of an `exp` claim.
2. IF a presented JWT lacks an `exp` claim, THEN THE Auth_Service SHALL reject the token as invalid.
3. IF a presented JWT carries an `exp` claim whose time has passed, THEN THE Auth_Service SHALL reject the token as expired.
4. THE Auth_Service SHALL NOT clear or omit the `exp` claim from the set of required token claims.

### Requirement 9: XP boost computation must guard against null multipliers

**User Story:** As a learner, I want XP awards to be computed reliably, so that a missing boost multiplier does not crash the request.

#### Acceptance Criteria

1. IF the XP boost multiplier is null or unset when XP is applied, THEN THE Python_Backend SHALL treat the multiplier as the neutral value and complete the operation without error.
2. WHEN the XP boost multiplier is a numeric value greater than the neutral value, THE Python_Backend SHALL apply the boost to the awarded XP.
3. WHEN XP is applied, THE Python_Backend SHALL NOT raise an unhandled exception due to the multiplier being null.
4. WHEN XP is applied, THE Python_Backend SHALL handle all error conditions arising during the XP application operation without raising an unhandled exception.

### Requirement 10: File uploads must be validated by content, not client-declared type

**User Story:** As a security engineer, I want uploaded files validated by their actual content and rejected fail-closed on validation failure, so that a client cannot smuggle a disallowed file by spoofing its declared type.

#### Acceptance Criteria

1. WHEN a file is uploaded to the avatar endpoint, THE Upload_Validator SHALL determine the file type from the file's content (magic bytes) rather than from the client-supplied Content-Type alone.
2. IF an uploaded avatar file's content-derived type is not in the allowed set, THEN THE Upload_Validator SHALL reject the upload.
3. IF validation of a RAG document upload cannot be completed successfully, THEN THE Upload_Validator SHALL reject the upload rather than silently substituting replacement characters for decode errors.
4. WHEN an upload is rejected, THE Python_Backend SHALL return an error response and SHALL NOT persist the rejected file.
5. IF the client-declared Content-Type does not match the content-derived type of an uploaded file, THEN THE Upload_Validator SHALL reject the upload even when both types are individually in the allowed set.
6. THE Upload_Validator SHALL treat content-format validation and allowed-type authorization as separate checks, each producing its own distinct error outcome.

### Requirement 11: Avatar storage and serving paths must be consistent

**User Story:** As a user, I want my uploaded avatar to be retrievable after upload, so that the stored file and the served URL refer to the same location.

#### Acceptance Criteria

1. WHEN the Python_Backend stores an uploaded avatar, THE Python_Backend SHALL write the file to a directory that is served by the static-asset mount used for avatar URLs.
2. WHEN an avatar URL is generated for a stored avatar, THE Python_Backend SHALL produce a URL that resolves to the same file that was written.
3. THE Python_Backend SHALL use a single configured base location for both writing and serving avatar files.

### Requirement 12: Authentication endpoints must be rate limited

**User Story:** As a security engineer, I want authentication endpoints throttled, so that brute-force and credential-stuffing attacks are constrained.

#### Acceptance Criteria

1. WHEN the configured request rate for an authentication endpoint is exceeded by a client within the configured window, THE Rate_Limiter SHALL reject further requests from that client with a rate-limit error response.
2. THE Python_Backend SHALL consume the configured `rate_limit_*` settings to enforce request limits on authentication endpoints.
3. WHILE a client is within the configured rate limit, THE Rate_Limiter SHALL allow the client's requests to proceed.
4. WHERE rate-limit settings are configured, THE Python_Backend SHALL apply them rather than leaving them unconsumed.

### Requirement 13: Frontend route protection must validate token validity

**User Story:** As a security engineer, I want the Frontend route guard to verify token validity rather than mere presence, so that an expired or malformed token cannot grant access to protected routes.

#### Acceptance Criteria

1. WHEN a request to a protected route is evaluated, THE Route_Guard SHALL determine access based on the validity of the authentication token, not solely on the presence of a cookie.
2. IF the authentication token is absent, expired, or malformed, THEN THE Route_Guard SHALL deny access to the protected route.
3. WHEN the authentication token is present and valid, THE Route_Guard SHALL permit access to the protected route.
4. WHERE additional security checks (such as account status or permission constraints) apply, THE Route_Guard SHALL allow those checks to deny access even when the authentication token is otherwise valid.

---

## Medium Severity Requirements

### Requirement 14: Validation error responses must not disclose full input

**User Story:** As a security engineer, I want validation error responses to avoid echoing full request input and to use correct type annotations, so that error handling does not leak sensitive data or carry incorrect contracts.

#### Acceptance Criteria

1. WHEN a request fails validation, THE Python_Backend SHALL return an error response that does not echo the complete submitted input back to the client.
2. THE Python_Backend error model SHALL annotate the error details field with a type that correctly reflects an optional mapping rather than a bare `dict = None` annotation.
3. WHEN a validation error is reported, THE Python_Backend SHALL include only the information required to identify the failing fields.
4. IF the failing-field information would itself reveal sensitive submitted data, THEN THE Python_Backend SHALL restrict or redact that information in the error response.

### Requirement 15: RBAC logic must match its documented contract and be the single source of truth

**User Story:** As a developer, I want role-management authorization to behave as documented and live in one place, so that authorization decisions do not drift across duplicated definitions.

#### Acceptance Criteria

1. WHEN the RBAC_Module evaluates whether one role may manage another, THE RBAC_Module SHALL produce a result consistent with its documented behavior for the super_admin-to-super_admin case.
2. THE Python_Backend SHALL derive role-management decisions from the RBAC_Module rather than from duplicated local role sets defined in `main.py`.
3. THE Python_Backend SHALL maintain a single authoritative definition of roles and their management relationships.
4. THE `main.py` module SHALL contain no local role definitions, whether or not they are used for authorization decisions.

### Out of Scope — formerly Requirement 16 (Python backend modularization)

> **Moved to the `backend-modularization` spec.** Decomposing the ~17,900-line `main.py`
> is a large, higher-risk, behavior-preserving refactor that is sequenced independently so the
> security-critical fixes in this spec can land first against the existing monolith. This number
> is retained to keep cross-references stable; no acceptance criteria are tracked here.

### Requirement 17: JWT tokens must carry identity claims and support revocation

**User Story:** As a security engineer, I want issued tokens to include identifying claims and a revocation path, so that tokens can be uniquely identified, scoped, and invalidated.

#### Acceptance Criteria

1. WHEN a backend issues a JWT, THE Auth_Service SHALL include a unique token identifier (`jti`), an issuer (`iss`), and an audience (`aud`) claim.
2. WHEN a refresh token is revoked, THE Auth_Service SHALL reject subsequent attempts to use that refresh token.
3. WHEN a backend validates a JWT, THE Auth_Service SHALL verify that the `iss` and `aud` claims match the expected values.
4. IF the `iss` or `aud` claim of a presented JWT does not match the expected value, THEN THE Auth_Service SHALL reject the token.
5. WHEN the `iss` and `aud` claims of a presented JWT match the expected values, THE Auth_Service SHALL accept the token with respect to those claims.

### Requirement 18: Current-user resolution must be consolidated

**User Story:** As a developer, I want a single token-decoding implementation shared by the required and optional current-user dependencies, so that decode logic does not diverge.

#### Acceptance Criteria

1. THE Python_Backend SHALL resolve the current user and the optional current user through a single shared token-decoding implementation.
2. WHEN either current-user dependency decodes a token, THE Python_Backend SHALL apply identical validation rules.
3. THE Python_Backend SHALL NOT maintain duplicate token-decoding logic across the required and optional current-user dependencies.
4. WHERE a migration toward the shared implementation is in progress, THE Python_Backend MAY retain temporary duplication until the migration completes, after which no duplication SHALL remain.

### Requirement 19: Analytics recording must not commit the shared request session

**User Story:** As a developer, I want analytics event recording to avoid committing the shared request database session, so that request transaction atomicity is preserved.

#### Acceptance Criteria

1. WHEN an analytics event is recorded, THE Python_Backend SHALL NOT commit the database session that is shared with the surrounding request.
2. IF the surrounding request later fails, THEN THE Python_Backend SHALL NOT have prematurely persisted partial request state through the analytics recording path.
3. WHEN an analytics event is persisted, THE Python_Backend SHALL use a transaction boundary that does not interfere with the request's atomicity.

### Requirement 20: Resource endpoints must enforce ownership and authorization

**User Story:** As a user, I want object-level authorization enforced on endpoints that take resource identifiers, so that I cannot access or modify another user's resources.

#### Acceptance Criteria

1. WHEN an endpoint that accepts a `{user_id}`, `{content_id}`, or `{session_id}` path parameter is invoked, THE Python_Backend SHALL verify that the Authenticated_User is the Resource_Owner or holds an explicit authorization to act on that resource.
2. IF the Authenticated_User is neither the Resource_Owner nor explicitly authorized for the referenced resource, THEN THE Python_Backend SHALL deny the request with a generic "not found" response that does not reveal whether the resource exists.
3. WHEN the Authenticated_User is the Resource_Owner or explicitly authorized, THE Python_Backend SHALL permit the operation on the referenced resource.

---

## Low Severity / Type-Safety / Maintainability Requirements

### Out of Scope — formerly Requirement 21 (frontend consolidation and typing)

> **Moved to the `frontend-consolidation-typing` spec.** Migrating the untyped `.jsx` client to
> TypeScript, generating typed API models, removing orphaned root-level duplicate components, and
> fixing the package manifest is a large structural effort distinct from the bounded security fixes.
> The narrow security-relevant frontend behaviors remain here: server-authoritative exam grading
> (Requirement 4), route-guard token validity (Requirement 13), the i18n table fix (Requirement 22),
> and the route-matching regex fix (Requirement 23). This number is retained to keep cross-references
> stable; no acceptance criteria are tracked here.

### Requirement 22: Language toggle must use distinct translations safely

**User Story:** As a user, I want the language toggle to switch between distinct languages without errors, so that selecting English produces English text.

#### Acceptance Criteria

1. WHEN a user selects the English language option, THE Frontend SHALL display English translation strings that are distinct from the Vietnamese strings.
2. WHEN a translation key is missing, THE Frontend translation lookup SHALL resolve safely without raising an error.
3. THE Frontend SHALL maintain separate, non-duplicated translation tables for each supported language.

### Requirement 23: Route-matching regex must use a correct pattern

**User Story:** As a developer, I want the route guard's path normalization to use a correct regular expression, so that `.json` suffixes are stripped as intended.

#### Acceptance Criteria

1. WHEN the Route_Guard normalizes a request path, THE Route_Guard SHALL match a literal `.json` suffix using a correctly escaped pattern.
2. WHEN a request path ends with `.json`, THE Route_Guard SHALL strip exactly the `.json` suffix.
3. THE Route_Guard SHALL NOT use a double-escaped backslash pattern that fails to match the intended `.json` suffix.

### Requirement 24: Database dependency must use a correct return type

**User Story:** As a developer, I want the database session dependency annotated accurately, so that its generator nature is reflected in its type.

#### Acceptance Criteria

1. THE Python_Backend database session dependency SHALL be annotated with an iterator type that reflects its generator behavior rather than a bare session return type.
2. WHEN type checking is run, THE Python_Backend SHALL report no type error for the database session dependency's declared return type.

### Requirement 25: Security headers must be present on both backends

**User Story:** As a security engineer, I want standard security headers on responses from both backends, so that browsers enforce content and transport protections.

#### Acceptance Criteria

1. WHEN the Python_Backend returns an HTTP response, THE Python_Backend SHALL include Content-Security-Policy, Strict-Transport-Security, and X-Content-Type-Options headers.
2. WHEN the Rust_Backend returns an HTTP response, THE Rust_Backend SHALL include Content-Security-Policy, Strict-Transport-Security, and X-Content-Type-Options headers.
3. THE Security_Headers SHALL be applied uniformly across all routes of each backend.

---

## Cross-Cutting / Non-Functional Requirements

### Requirement 26: Shared JWT contract backward compatibility

**User Story:** As a platform operator, I want the shared JWT contract between the Python and Rust backends preserved through these changes, so that tokens issued by one backend continue to be accepted by the other.

#### Acceptance Criteria

1. WHEN the JWT_Contract is modified by any requirement in this specification, THE JWT_Contract SHALL keep the signing algorithm, signing secret source, and required claim set consistent between the Python_Backend and the Rust_Backend.
2. WHEN one backend issues a token under the updated JWT_Contract, THE other backend SHALL validate and accept that token, provided the token passes all standard validation checks (signature, expiration, and format).
3. IF a claim is added to the JWT_Contract (such as `exp`, `jti`, `iss`, or `aud`), THEN both backends SHALL agree on the claim's name, format, and validation rule.
4. WHILE a rolling deployment leaves the two backends on inconsistent versions of the JWT_Contract, THE backends SHALL block cross-backend token validation until both backends are consistent.

### Requirement 27: Automated test coverage for every remediation

**User Story:** As an engineering lead, I want each remediation backed by an automated test, so that regressions are caught in continuous integration.

#### Acceptance Criteria

1. THE remediation effort SHALL provide at least one Automated_Test for each requirement in this specification that is verifiable through code.
2. WHEN a remediation Automated_Test runs against unfixed code, THE Automated_Test SHALL fail.
3. WHEN a remediation Automated_Test runs against fixed code, THE Automated_Test SHALL pass.
4. THE Automated_Test suite SHALL be executable in continuous integration without manual intervention.

### Requirement 28: Secrets management and rollout with no insecure defaults

**User Story:** As a platform operator, I want no insecure secret defaults in any environment and a safe rollout path, so that deployments cannot run with placeholder credentials.

#### Acceptance Criteria

1. THE source code SHALL contain no Sentinel_Default Secret_Value usable as a working credential in any environment.
2. WHEN any backend starts in a Production_Environment, THE Config_Loader SHALL require every Secret_Value to be supplied externally rather than from a committed default.
3. WHERE a development or test environment is used, THE Config_Loader SHALL obtain Secret_Values from explicit local configuration rather than hardcoded source defaults.
4. THE rollout SHALL document the externally supplied Secret_Values required by each backend so operators can provision them before deployment.
