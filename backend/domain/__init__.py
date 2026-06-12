# -*- coding: utf-8 -*-
"""Domain logic for the Luuniensuki backend.

Pure(ish) gamification/progression helpers extracted from ``backend.main``
(backend-modularization task 3.1). See ``backend.domain.gamification``.
"""
from __future__ import annotations

from .gamification import (
    CERTIFICATE_ISSUER_NAME,
    XP_RANKS,
    _apply_xp_boost,
    _award_badge,
    _compute_rank,
    _issue_certificate,
    _update_streak,
)

__all__ = [
    "CERTIFICATE_ISSUER_NAME",
    "XP_RANKS",
    "_apply_xp_boost",
    "_award_badge",
    "_compute_rank",
    "_issue_certificate",
    "_update_streak",
]
