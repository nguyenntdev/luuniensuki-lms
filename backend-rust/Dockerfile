# =============================================================================
# Multi-stage cargo-chef build for luuniensuki-api (Rust backend)
#
# Tuned for memory-constrained build host (~3.9 GiB RAM).
# Validates: Req 11.1, 11.2, 11.3
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Chef — base image with cargo-chef pre-installed
# ---------------------------------------------------------------------------
FROM lukemathwalker/cargo-chef:latest-rust-1-bookworm AS chef

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
ENV CARGO_BUILD_JOBS=2
ENV CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1
ENV CARGO_PROFILE_RELEASE_LTO=thin

COPY --from=planner /app/recipe.json recipe.json

# Build dependencies only (cached layer)
RUN cargo chef cook --release --recipe-path recipe.json

# Copy full source and build the binary
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release -j 2

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

# Create non-root user and setup directories
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false -M -d /app appuser && \
    mkdir -p /app/config /app/docs /app/uploads && \
    chown -R appuser:appgroup /app

# Copy the release binary from builder
COPY --from=builder --chown=appuser:appgroup /app/target/release/luuniensuki-api /usr/local/bin/luuniensuki-api

# Copy runtime configuration and documentation into the image
COPY --chown=appuser:appgroup config/ /app/config/
COPY --chown=appuser:appgroup docs/route-inventory.json /app/docs/route-inventory.json

USER appuser

EXPOSE 8001

CMD ["luuniensuki-api"]
