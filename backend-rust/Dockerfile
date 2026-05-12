FROM rust:1.82-bookworm AS builder

WORKDIR /app

ENV PATH="/usr/local/cargo/bin:${PATH}"
ENV CARGO_PROFILE_DEV_DEBUG=0

COPY Cargo.toml Cargo.toml
COPY Cargo.lock Cargo.lock
COPY src src

RUN cargo build -j 1

FROM debian:bookworm-slim AS runner

WORKDIR /app

ENV RUST_LOG=info \
    API_HOST=0.0.0.0 \
    API_PORT=8001

COPY --from=builder /app/target/debug/luuniensuki-api /usr/local/bin/luuniensuki-api

EXPOSE 8001

CMD ["luuniensuki-api"]
