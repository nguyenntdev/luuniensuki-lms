# V2 original archival technical chapter — SECTION_12

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 12. SECURITY & PRIVACY HARDENING SPEC

### 12.1 Threat model STRIDE (baseline)

| Threat | Attack surface | Controls | Gate |
|---|---|---|---|
| Spoofing | JWT cookies, student login, partner login | session rotation, MFA admin, argon2/bcrypt review, secure cookies | token replay/revocation tests |
| Tampering | historical claims, reviews, audit | append-only decisions, content hash, DB transaction controls | editor diff + alert |
| Repudiation | inquiry, consent | signed audit event, immutable receipt, correlation id | chain verify + DB replay |
| Information disclosure | minor/student, partner contacts, research raw | scoped API, encryption, masking, retention | IDOR suite |
| Denial of service | AI endpoint, auth, inquiry | trusted proxy IP, L7 distributed limits, cost caps, queues | load test + forged XFF |
| Elevation | roles, feature switches, route fallback | RBAC/ABAC checks BOTH Python/Rust, permission matrix | negative tests |

### 12.2 Web security

- Nginx/cloud edge chính thức overwrite trusted-forwarded IP; frontend không được dùng client-provided XFF trực tiếp.
- Cookies HttpOnly, Secure production, SameSite theo threat model; verify CSRF cho mọi cookie-authenticated mutation (Lax không tự thay CSRF strategy).
- CSP per frontend/Sketchfab/AR carefully defined, không bật wildcard không cần thiết; escape untrusted HTML/markdown.
- `redirectUrl` allowlist, image/media URL allowlist, server-side SSRF guard, file MIME + magic bytes and max sizes.
- Query ORM parameterized; pagination and bounding for expensive filters.
- Short-lived signed URLs for asset downloads not public by rights; audit private downloads.
- Public `inquiry status` token high-entropy and indistinguishable 404; rate limit status lookup; localStorage storage risk documented.

### 12.3 Secrets and dependencies

- Secrets only Vault/GitHub Environments/secret manager; `git-secrets`/gitleaks detect tokens; rotate any exposed secret after audit.
- Lock/pin npm/pip/Rust/Flutter where practical; `npm audit`, `pip-audit`, `cargo audit` and license SBOM in CI (online tooling required); supply chain signing.
- Remove shipped `.apk` from source control to release artifacts, if Git history and distribution policies permit; don't delete original evidence without archival.
- Sanitize logs: no passwords, bearer tokens, personal phone/email, student submissions or secrets.

### 12.4 Minor/student data handling

- Age-aware policies; guardian consent where legally/procedurally required; no public leaderboards by default for minors; no third-party ads/behavioral profiling.
- Data minimization: learning logs need only task/step timings or codes required for research, optional privacy opt-in.
- DSR workflow: export/delete/correct with teacher/research records retention exception governed by policy; separate identifier mapping protected.

---

