# -*- coding: utf-8 -*-
"""Users/profile/onboarding/public-profile request/response models.

Relocated verbatim from ``backend.main`` (backend-modularization task 4.1).
``backend.main`` imports these under their original names. ``UserOut`` and
``RankOut`` are imported from ``.auth`` (the same relocated definitions main
used inline), keeping cross-model references intact.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from .auth import RankOut, UserOut


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    is_profile_public: Optional[bool] = None
    ai_personalization_enabled: Optional[bool] = None


class UpdateProfileResponse(BaseModel):
    user: UserOut
    message: str


class StartingPathRequest(BaseModel):
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None

    @model_validator(mode="after")
    def _validate_reference(self) -> "StartingPathRequest":
        if self.urn_id is None and not self.urn_slug:
            raise ValueError("Either urn_id or urn_slug is required.")
        return self


class StartingPathResponse(BaseModel):
    starting_urn_id: UUID
    starting_urn_slug: str


class OnboardingGoalRequest(BaseModel):
    goal: str = Field(
        ...,
        description="User's learning goal",
        examples=["learn_culture", "pass_exam", "curiosity"],
    )


class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    onboarding_goal: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None


class OnboardingCompleteResponse(BaseModel):
    success: bool
    message: str
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None


class PublicBadgeOut(BaseModel):
    name: str
    icon: str
    description: Optional[str] = None


class PublicMotifOut(BaseModel):
    id: UUID
    name: str
    category: str
    rarity: str
    status: str
    thumbnail_url: Optional[str] = None
    urn_id: UUID
    urn_name: str
    urn_slug: str


class UserPublicStatsOut(BaseModel):
    discovered_count: int
    learned_count: int
    mastered_count: int
    quizzes_passed: int


class UserPublicProfile(BaseModel):
    id: UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    total_xp: int
    rank: RankOut
    badges: list[PublicBadgeOut]
    certificates: list[Any] = Field(default_factory=list)
    stats: UserPublicStatsOut
    motifs: list[PublicMotifOut] = Field(default_factory=list)
