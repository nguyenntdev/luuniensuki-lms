# -*- coding: utf-8 -*-
"""API Router for Pilot Go/No-Go Decision Board (Ticket V5-T129 / Wave W12 Slot A09).

Endpoints:
- GET  /api/v1/rbpc/go-no-go/board (Public/Internal: get current authoritative board state)
- POST /api/v1/rbpc/go-no-go/evaluate (Staff/DevOps: evaluate board input against negative abuse invariants)
- GET  /api/v1/rbpc/go-no-go/evaluations/{board_ref} (Retrieve saved evaluation from database)
- GET  /api/v1/rbpc/go-no-go/export (Export board report as Markdown or JSON)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..apischemas.pilot_go_no_go import (
    PilotGoNoGoBoardOut,
    PilotGoNoGoEvaluateIn,
    PilotGoNoGoExportOut,
)
from ..db import get_db
from ..errors import AppError
from ..services.pilot_go_no_go import default_pilot_go_no_go_service

router = APIRouter(tags=["rbpc_pilot_go_no_go"])


@router.get(
    "/api/v1/rbpc/go-no-go/board",
    response_model=PilotGoNoGoBoardOut,
)
def get_canonical_go_no_go_board(
    db: Session = Depends(get_db),
) -> PilotGoNoGoBoardOut:
    """Retrieve the current authoritative Pilot Go/No-Go Board state.
    
    Includes 5 signed owner decisions, blocking issue register,
    feature flag plan, rollback triggers, and 24/7 on-call contacts.
    """
    return default_pilot_go_no_go_service.evaluate_board()


@router.post(
    "/api/v1/rbpc/go-no-go/evaluate",
    response_model=PilotGoNoGoBoardOut,
)
def evaluate_go_no_go_board(
    body: PilotGoNoGoEvaluateIn,
    persist: bool = Query(True, description="Whether to persist evaluation to database"),
    db: Session = Depends(get_db),
) -> PilotGoNoGoBoardOut:
    """Evaluate a proposed or updated Pilot Go/No-Go Board.
    
    NEGATIVE ABUSE INVARIANT:
    Launch is strictly BLOCKED if any P0 issue remains unresolved in the
    blocking issue register, regardless of votes or approvals.
    """
    board = default_pilot_go_no_go_service.evaluate_board(input_data=body, db=db, persist=persist)
    return board


@router.get(
    "/api/v1/rbpc/go-no-go/evaluations/{board_ref}",
    response_model=PilotGoNoGoBoardOut,
)
def get_saved_go_no_go_evaluation(
    board_ref: str,
    db: Session = Depends(get_db),
) -> PilotGoNoGoBoardOut:
    """Retrieve a previously audited evaluation by its unique board_ref."""
    row = default_pilot_go_no_go_service.get_evaluation_by_ref(board_ref=board_ref, db=db)
    if not row:
        raise AppError(
            code="EVALUATION_NOT_FOUND",
            message=f"Evaluation with ref '{board_ref}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return PilotGoNoGoBoardOut(
        board_ref=row.board_ref,
        release_version=row.release_version,
        target_environment=row.target_environment,
        verdict=row.verdict,
        is_launch_blocked=row.is_launch_blocked,
        open_p0_count=row.open_p0_count,
        open_p1_count=row.open_p1_count,
        open_p2_count=row.open_p2_count,
        signed_owners_count=row.signed_owners_count,
        blocking_reasons=row.blocking_reasons or [],
        owner_decisions=row.owner_decisions or [],
        blocking_issues=row.blocking_issues or [],
        feature_flags=row.feature_flags or [],
        rollback_triggers=row.rollback_triggers or [],
        support_contacts=row.support_contacts or [],
        evaluated_at=row.evaluated_at.isoformat() if row.evaluated_at else "",
        evaluated_by=row.evaluated_by,
    )


@router.get(
    "/api/v1/rbpc/go-no-go/export",
    response_model=PilotGoNoGoExportOut,
)
def export_go_no_go_board(
    format: str = Query("markdown", description="Export format: 'markdown' or 'json'"),
    db: Session = Depends(get_db),
) -> PilotGoNoGoExportOut:
    """Export the current Pilot Go/No-Go Board report in Markdown or JSON format."""
    board = default_pilot_go_no_go_service.evaluate_board()
    content = default_pilot_go_no_go_service.export_board(board, format_type=format)
    return PilotGoNoGoExportOut(
        format=format,
        board_ref=board.board_ref,
        verdict=board.verdict,
        content=content,
    )
