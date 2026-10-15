FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false -M -d /app appuser

RUN pip install --no-cache-dir --upgrade pip

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=appuser:appgroup backend /app/backend
COPY --chown=appuser:appgroup services /app/services
COPY --chown=appuser:appgroup data /app/data
COPY --chown=appuser:appgroup alembic.ini /app/alembic.ini
COPY --chown=appuser:appgroup migrations /app/migrations

RUN mkdir -p /app/uploads /app/data && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
