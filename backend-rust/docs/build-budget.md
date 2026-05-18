# Rust Build Memory Budget

Updated in lockstep with `Cargo.toml`. The CI build-budget lint enforces parity:
every direct dependency in `Cargo.toml` MUST have a row in this table, and
every row in this table MUST correspond to a direct dependency.

## Build host envelope

The Rust service is currently built on a host with ~3.9 GiB of RAM and
~6 GiB of swap, of which only ~140–250 MiB is typically free at build
time. To keep the release build within that envelope (Requirement 11.1,
11.3):

- `CARGO_BUILD_JOBS=1` — single-threaded compile to bound peak RSS.
- `[profile.release].codegen-units = 1` — one codegen unit, lower peak.
- `[profile.release].lto = "thin"` — thin LTO instead of full.
- `[profile.release].opt-level = 3` — unchanged from default.
- `[profile.release].strip = true` — drop symbols from the final binary.
- `[profile.dev].debug = 1` — minimal debug info for `cargo check` / `cargo test`.

Future dependency additions that push peak RSS over the headroom on the
build host MUST either be deferred, replaced with a lighter alternative,
or accompanied by a documented build-host memory bump.

## Per-dependency peak release-build RSS

Peak RSS is captured with `/usr/bin/time -v cargo build --release` on the
build host. The "Peak RSS (MiB)" column records the cumulative peak with
that dep present and pinned at the listed exact version.

| Dependency           | Pinned version | Features                                                                          | Added in task | Peak RSS (MiB) | Notes |
|----------------------|----------------|------------------------------------------------------------------------------------|---------------|----------------|-------|
| tokio                | =1.40.0        | macros, rt-multi-thread, signal, net, time, sync                                  | 1.1           | 380            | Async runtime |
| axum                 | =0.7.7         | http1, json, tokio, matched-path, tracing (default-features = false)              | 1.1           | 380            | HTTP framework |
| tower                | =0.5.1         | util (default-features = false)                                                   | 1.1           | 380            | Service abstraction |
| tower-http           | =0.6.1         | trace (default-features = false)                                                  | 1.1           | 380            | Request tracing layer |
| serde                | =1.0.210       | derive                                                                            | 1.1           | 380            | DTO derive |
| serde_json           | =1.0.128       | (default)                                                                         | 1.1           | 380            | JSON encode/decode |
| anyhow               | =1.0.89        | (default)                                                                         | 1.1           | 380            | Error in `main()` |
| thiserror            | =1.0.64        | (default)                                                                         | 1.1           | 380            | Typed errors |
| dotenvy              | =0.15.7        | (default)                                                                         | 1.1           | 380            | `.env` loading |
| tracing              | =0.1.40        | (default)                                                                         | 1.1           | 380            | Span/event API |
| tracing-subscriber   | =0.3.18        | fmt, json, env-filter, tracing-log (default-features = false)                     | 1.1           | 380            | JSON log output |
| sqlx                 | =0.7.4         | runtime-tokio-rustls, postgres, chrono, uuid, json (default-features = false)     | 1.2           | TODO           | Async Postgres pool |
| chrono               | =0.4.38        | serde                                                                             | 1.2           | TODO           | Timestamp types |
| uuid                 | =1.10.0        | v4, serde                                                                         | 1.2           | TODO           | UUID types |
| arc-swap             | =1.7.1         | (default)                                                                         | 1.5           | TODO           | Hot-reload dispatcher |
| reqwest              | =0.12.7        | rustls-tls, stream, json (default-features = false)                               | 1.5           | TODO           | Gateway proxy |
| toml                 | =0.5.11        | (default)                                                                         | 1.5           | TODO           | Route-modes config |

The `Peak RSS` cells will be filled in after the first successful release
build on the build host. If `/usr/bin/time -v` is unavailable in a given
environment, peak RSS may be approximated via `ps -o rss=` polling and
the row annotated accordingly.

## Measurement procedure

```bash
# From backend-rust/ on the build host:
/usr/bin/time -v env CARGO_BUILD_JOBS=1 cargo build --release 2>&1 \
  | tee build.log
grep "Maximum resident set size" build.log
```

Record the reported `Maximum resident set size (kbytes)` divided by 1024
in the table above and commit alongside the dependency change.
