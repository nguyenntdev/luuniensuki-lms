# V2 original archival technical chapter — SECTION_13

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 13. OBSERVABILITY, PERFORMANCE, OFFLINE AND SRE

### 13.1 Service-level indicators (đề xuất)

- Gateway: request p50/p95/p99 latency by path and `x-serve-mode`; Rust/Python error parity.
- DB: pool use, slow queries, blocked migrations, deadlocks; run `EXPLAIN ANALYZE` against top queries before performance claims.
- 3D: median asset MB, TTFB, load-to-interactive p75/p95 by device, crash/WebGL fallback rate, LOD success.
- AI: retrieved source coverage, valid citations per factual claim, abstention rate, unsupported assertion rate, model/provider outages, average spend.
- LMS: task completion separated from rubric grade; sync conflict rate, time spent not treated as learning outcome.
- Inquiry: 202 confirmed server commits, contact SLA, false-ack count target zero, lost idempotency retries target zero.
- Research: count of imported valid responses, numerator/denominator checks, all exports reproducible.

### 13.2 Disaster recovery targets (to approve)

Propose RPO ≤24h, RTO ≤4h for platform core; backup daily + pre-migration, restore exercise at least quarterly, media lifecycle version. RPO/RTO are **targets** and not measured current system characteristics. Recovery process must test restored migrations/permissions, not just container start.

### 13.3 Offline strategy

`lesson_pack_manifest` lists content version, sources, images/media licensed offline, quiz definitions, expiration; client caches minimum 2D first; evidence packet hash to detect stale, sync queue idempotency; no caching of revoked artisan PII across consent withdrawal beyond contractually permissible grace interval (ideally purge promptly).

### 13.4 Performance budgets (targets)

- Initial public route: no unconditional 30MB GLB; hero image compressed and lazy load model on click.
- 3D LOD target: mobile low memory ≤8MB compressed asset if achievable; actual 512 preview baseline ~5.2MB GLB but verify gzip/CDN and mesh anatomy.
- Keyboard and voice controls work when 3D fails; no blocking page render on AI provider.
- Test desktop mainstream + low-end Android throttled 3G/4G; tests include viewport 360px, tablet, classroom projector.

---

