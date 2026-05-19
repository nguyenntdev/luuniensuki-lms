# Minimal runtime image — binary is pre-built on host
FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV RUST_LOG=info \
    API_HOST=0.0.0.0 \
    API_PORT=8001

# Copy the pre-built release binary
COPY target/release/luuniensuki-api /usr/local/bin/luuniensuki-api

# Copy runtime configuration
COPY config/ /app/config/
COPY docs/route-inventory.json /app/docs/route-inventory.json

EXPOSE 8001

CMD ["luuniensuki-api"]
