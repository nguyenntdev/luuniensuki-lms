# -*- coding: utf-8 -*-
"""Offline write queue synchronization router.

Ticket: V5-T056 (Wave W05, Slot A06)
Spec: Offline queue idempotency for mobile and web PWA.

Endpoints:
- POST /api/v1/offline/sync: Single or batch idempotent operation processing
- POST /api/v1/offline/batch-sync: Explicit batch operation processing
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from ..apischemas.offline import (
    OfflineOperationItem,
    OfflineSyncRequest,
    OfflineSyncResponse,
)
from ..db import get_db
from ..deps import get_current_user
from ..errors import AppError
from ..models import User
from ..services import offline_sync_service

logger = logging.getLogger("luuniensuki.offline_sync")

router = APIRouter(prefix="/api/v1/offline", tags=["offline"])


@router.post(
    "/sync",
    response_model=OfflineSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronize offline write operations idempotently",
)
def sync_offline_operations(
    request: Request,
    payload: OfflineSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Synchronize queued offline actions (inspections, submissions, progression).

    Guarantees:
    - Reconnection retries never duplicate submissions or award multiple XP.
    - Idempotency key deduplication returns server-authoritative acknowledgment.
    - Conflict resolution preserves teacher-graded assessments.
    """
    idemp_header = x_idempotency_key or idempotency_key_header

    operations: list[OfflineOperationItem] = []
    if payload.operations:
        operations = payload.operations
    elif payload.operation_id and payload.resource:
        operations = [
            OfflineOperationItem(
                operation_id=payload.operation_id,
                resource=payload.resource,
                payload=payload.payload or {},
                created_at=payload.created_at,
                idempotency_key=payload.idempotency_key or idemp_header,
            )
        ]
    else:
        raise AppError(
            code="INVALID_OFFLINE_PAYLOAD",
            message="Payload must contain either an 'operations' list or 'operation_id' + 'resource'",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return offline_sync_service.sync_offline_batch(
        db=db,
        user=current_user,
        operations=operations,
        header_idempotency_key=idemp_header,
    )


@router.post(
    "/batch-sync",
    response_model=OfflineSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch synchronize multiple offline operations",
)
def batch_sync_offline_operations(
    payload: OfflineSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Batch synchronize multiple queued offline operations."""
    idemp_header = x_idempotency_key or idempotency_key_header
    operations = payload.operations or []
    if not operations and payload.operation_id and payload.resource:
        operations = [
            OfflineOperationItem(
                operation_id=payload.operation_id,
                resource=payload.resource,
                payload=payload.payload or {},
                created_at=payload.created_at,
                idempotency_key=payload.idempotency_key or idemp_header,
            )
        ]

    return offline_sync_service.sync_offline_batch(
        db=db,
        user=current_user,
        operations=operations,
        header_idempotency_key=idemp_header,
    )
