# =============================================================================
# Multi-stage cargo-chef build for luuniensuki-api (Rust backend)
#
# Task 1.19: Replaces the single-stage build with a chef → planner → builder
# → runtime pipeline. Tuned for a low-memory build host (~3.9 GiB RAM).
#
# Validates: Req 11.1, 11.2, 11.3
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Chef — install cargo-chef for dependency caching
# ---------------------------------------------------------------------------
FROM rust:1.82-bookworm AS chef

RUN cargo install cargo-chef --locked
WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 2: Planner — generate the recipe (dependency graph snapshot)
# ---------------------------------------------------------------------------
FROM chef AS planner

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo chef prepare --recipe-path recipe.json

# ---------------------------------------------------------------------------
# Stage 3: Builder — compile dependencies then the application
# ---------------------------------------------------------------------------
FROM chef AS builder

# Memory-constrained build settings (Req 11.1, 11.3)
ENV CARGO_BUILD_JOBS=1
ENV CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1
ENV CARGO_PROFILE_RELEASE_LTO=thin

COPY --from=planner /app/recipe.json recipe.json

# Build dependencies only (cached layer)
RUN cargo chef cook --release --recipe-path recipe.json

# Copy full source and build the binary
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release -j 1

# ---------------------------------------------------------------------------
# Stage 4: Runtime — minimal image with only the binary + config
# ---------------------------------------------------------------------------
FROM debian:bookworm-slim AS runtime

# Install runtime dependencies (TLS root certs for reqwest/rustls)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV RUST_LOG=info \
    API_HOST=0.0.0.0 \
    API_PORT=8001

# Copy the release binary
COPY --from=builder /app/target/release/luuniensuki-api /usr/local/bin/luuniensuki-api

# Copy runtime configuration and documentation into the image
COPY config/ /app/config/
COPY docs/route-inventory.json /app/docs/route-inventory.json

EXPOSE 8001

CMD ["luuniensuki-api"]
