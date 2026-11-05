# -*- coding: utf-8 -*-
"""Distributed provider semaphore for AI Research Factory — V5 Wave W07.

Spec reference: V4.3.2 / V3.C3.
Cross-process concurrency control for external AI and OCR provider APIs.
Prevents HTTP 429 quota storms and thundering herds across multiple worker pods.
Backed by PostgreSQL transactions with atomic expiration and TTL renewal.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from backend.research_factory_models import (
    ProviderConcurrencyConfig,
    ProviderSemaphoreLease,
)


class SemaphoreError(Exception):
    """Base exception for provider semaphore operations."""


class SemaphoreTimeoutError(SemaphoreError):
    """Raised when a worker fails to acquire a permit within the configured timeout."""


class SemaphoreCapacityError(SemaphoreError):
    """Raised when requested permit weight exceeds maximum allowable provider capacity."""


def acquire_provider_slot(
    db: Session,
    provider: str,
    holder_id: str,
    max_concurrency: int = 10,
    ttl_seconds: int = 60,
    weight: int = 1,
) -> ProviderSemaphoreLease | None:
    """Atomically acquire concurrency slots for a provider.

    Uses PostgreSQL transaction advisory lock or row-level serialization:
    1. Removes expired leases.
    2. Inspects provider configuration if defined.
    3. Calculates current active weight.
    4. If capacity permits, inserts lease and commits immediately.
    """
    now_utc = datetime.now(timezone.utc)

    # 1. Purge expired leases for this provider
    db.execute(
        delete(ProviderSemaphoreLease).where(
            ProviderSemaphoreLease.provider == provider,
            ProviderSemaphoreLease.expires_at <= now_utc,
        )
    )

    # 2. Acquire transaction-level lock to serialize slot allocation per provider
    # On PostgreSQL, use pg_advisory_xact_lock to prevent race conditions across pods
    bind = db.get_bind()
    if bind and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:provider))"),
            {"provider": provider},
        )

    # 3. Check configured provider limits if present
    cfg = db.execute(
        select(ProviderConcurrencyConfig).where(
            ProviderConcurrencyConfig.provider == provider,
            ProviderConcurrencyConfig.is_active == True,
        )
    ).scalars().first()

    effective_max = cfg.max_concurrency if cfg is not None else max_concurrency

    if weight > effective_max:
        db.rollback()
        raise SemaphoreCapacityError(
            f"Requested weight {weight} exceeds provider maximum concurrency {effective_max}"
        )

    # 4. Sum current active allocations
    active_weight_query = select(
        func.coalesce(func.sum(ProviderSemaphoreLease.weight), 0)
    ).where(
        ProviderSemaphoreLease.provider == provider,
        ProviderSemaphoreLease.expires_at > now_utc,
    )
    current_active_weight = db.execute(active_weight_query).scalar() or 0

    if current_active_weight + weight <= effective_max:
        # Sufficient capacity available
        token = uuid.uuid4().hex
        lease = ProviderSemaphoreLease(
            provider=provider,
            holder_id=holder_id,
            lease_token=token,
            weight=weight,
            expires_at=now_utc + timedelta(seconds=ttl_seconds),
        )
        db.add(lease)
        db.commit()
        db.refresh(lease)
        return lease

    # Capacity exhausted
    db.commit()
    return None


def release_provider_slot(
    db: Session,
    lease_id: uuid.UUID,
    lease_token: str,
) -> bool:
    """Atomically release an acquired provider semaphore permit."""
    result = db.execute(
        delete(ProviderSemaphoreLease).where(
            ProviderSemaphoreLease.id == lease_id,
            ProviderSemaphoreLease.lease_token == lease_token,
        )
    )
    db.commit()
    return result.rowcount > 0


def renew_provider_slot(
    db: Session,
    lease_id: uuid.UUID,
    lease_token: str,
    extension_seconds: int = 60,
) -> bool:
    """Extend TTL of an active provider semaphore permit."""
    now_utc = datetime.now(timezone.utc)
    new_expiry = now_utc + timedelta(seconds=extension_seconds)

    lease = db.execute(
        select(ProviderSemaphoreLease)
        .where(
            ProviderSemaphoreLease.id == lease_id,
            ProviderSemaphoreLease.lease_token == lease_token,
        )
        .with_for_update()
    ).scalars().first()

    if not lease or lease.expires_at <= now_utc:
        db.rollback()
        return False

    lease.expires_at = new_expiry
    db.commit()
    return True


class DistributedProviderSemaphore:
    """Multi-pod provider semaphore context manager.

    Supports both sync (`with`) and async (`async with`) blocks.
    Polls until a permit is acquired or timeout is reached.
    """

    def __init__(
        self,
        session_factory: Any,
        provider: str,
        holder_id: str | None = None,
        max_concurrency: int = 10,
        ttl_seconds: int = 60,
        timeout_seconds: float = 10.0,
        poll_interval: float = 0.05,
        weight: int = 1,
    ) -> None:
        self.session_factory = session_factory
        self.provider = provider
        self.holder_id = holder_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.max_concurrency = max_concurrency
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self.weight = weight
        self.current_lease: Optional[ProviderSemaphoreLease] = None

    def __enter__(self) -> ProviderSemaphoreLease:
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            with self.session_factory() as session:
                lease = acquire_provider_slot(
                    db=session,
                    provider=self.provider,
                    holder_id=self.holder_id,
                    max_concurrency=self.max_concurrency,
                    ttl_seconds=self.ttl_seconds,
                    weight=self.weight,
                )
                if lease:
                    self.current_lease = lease
                    return lease
            time.sleep(self.poll_interval)

        raise SemaphoreTimeoutError(
            f"Timed out after {self.timeout_seconds}s waiting for permit on provider '{self.provider}'"
        )

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.current_lease:
            with self.session_factory() as session:
                release_provider_slot(
                    db=session,
                    lease_id=self.current_lease.id,
                    lease_token=self.current_lease.lease_token,
                )
            self.current_lease = None

    async def __aenter__(self) -> ProviderSemaphoreLease:
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            with self.session_factory() as session:
                lease = acquire_provider_slot(
                    db=session,
                    provider=self.provider,
                    holder_id=self.holder_id,
                    max_concurrency=self.max_concurrency,
                    ttl_seconds=self.ttl_seconds,
                    weight=self.weight,
                )
                if lease:
                    self.current_lease = lease
                    return lease
            await asyncio.sleep(self.poll_interval)

        raise SemaphoreTimeoutError(
            f"Timed out after {self.timeout_seconds}s waiting for permit on provider '{self.provider}'"
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.current_lease:
            with self.session_factory() as session:
                release_provider_slot(
                    db=session,
                    lease_id=self.current_lease.id,
                    lease_token=self.current_lease.lease_token,
                )
            self.current_lease = None
