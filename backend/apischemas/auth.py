# -*- coding: utf-8 -*-
"""Auth domain request/response models (relocated from ``backend.main``).

Backend-modularization task 4.1. Moved verbatim from ``main.py`` (field sets and
validators preserved exactly). ``backend.main`` imports these by their original
bare names, so ``response_model=AuthMeResponse`` etc. resolve unchanged.

These models are intentionally distinct from the same-named models in
``backend/schemas.py`` (see ``backend/apischemas/__init__.py``).
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    username: Optional[str] = None
    role: str
    total_xp: int
    starting_urn_id: Optional[UUID] = None
    is_profile_public: bool
    ai_personalization_enabled: bool


class RankOut(BaseModel):
    level: int
    name: str
    xp: int


class UserStatsOut(BaseModel):
    total_xp: int
    rank: RankOut
    xp_to_next_rank: int
    next_rank: Optional[RankOut] = None


class AuthMeResponse(BaseModel):
    user: UserOut
    stats: UserStatsOut


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=8, max_length=72)


class ResetPasswordResponse(BaseModel):
    success: bool = True
    message: str
