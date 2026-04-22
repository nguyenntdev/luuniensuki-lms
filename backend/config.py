"""
Centralized configuration for Luuniensuki LMS.

This module provides a single source of truth for all application settings,
loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Database
    # ==========================================================================
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki"
    )

    # ==========================================================================
    # JWT Authentication
    # ==========================================================================
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30
    password_reset_return_token: bool = True

    # Cookie settings for JWT tokens
    access_cookie_name: str = "luuniensuki_access"
    refresh_cookie_name: str = "luuniensuki_refresh"
    cookie_domain: Optional[str] = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_path: str = "/"

    # ==========================================================================
    # Application
    # ==========================================================================
    log_level: str = "info"
    debug: bool = False
    app_name: str = "Cửu Đỉnh Ký"
    app_version: str = "0.1.0"

    # ==========================================================================
    # XP System
    # ==========================================================================
    xp_discovery: int = 25
    xp_lesson: int = 50
    xp_mastery: int = 75
    xp_urn_exam_pass: int = 300
    quiz_pass_threshold: float = 0.8  # 80%

    # ==========================================================================
    # Quiz Settings
    # ==========================================================================
    urn_exam_question_count: int = 15
    default_quiz_time_limit_seconds: int = 300  # 5 minutes
    urn_exam_time_limit_seconds: int = 1800  # 30 minutes

    # ==========================================================================
    # Certificate
    # ==========================================================================
    certificate_issuer_name: str = "Lưu Niên Sử Kí"

    # ==========================================================================
    # Gamification
    # ==========================================================================
    interaction_tolerance_multiplier: float = 1.25

    # ==========================================================================
    # Server Settings
    # ==========================================================================
    gunicorn_workers: int = 2
    gunicorn_timeout: int = 180

    # ==========================================================================
    # External Services (Optional)
    # ==========================================================================
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.yescale.vip/v1"
    deepseek_model: str = "deepseek-v3"
    deepseek_timeout_seconds: int = 60
    deepseek_max_retries: int = 1

    # ==========================================================================
    # Backend Voice (STT/TTS)
    # ==========================================================================
    voice_api_key: Optional[str] = None
    voice_base_url: Optional[str] = None
    voice_stt_model: str = "gpt-4o-mini-transcribe"
    voice_tts_model: str = "gpt-4o-mini-tts"
    voice_tts_voice: str = "alloy"
    voice_timeout_seconds: int = 45
    voice_max_audio_bytes: int = 15 * 1024 * 1024

    # ==========================================================================
    # Demo Live Classroom (Optional)
    # ==========================================================================
    demo_live_entry_enabled: bool = False
    demo_live_entry_key: Optional[str] = None
    demo_live_teacher_email: Optional[str] = None
    demo_live_teacher_password: Optional[str] = None
    demo_live_teacher_name: str = "Live Demo Teacher"
    demo_live_class_name: str = "AI Teacher 3D Demo Class"
    demo_live_session_title: str = "AI Teacher 3D Live Session"
    demo_live_max_students: int = 60
    demo_live_base_url: str = "https://lms.histolab.icu"

    # Internal URL used by backend service-to-service calls (RoomService/Twirp).
    livekit_url: Optional[str] = None
    # Public URL returned to clients for browser/mobile LiveKit connection.
    # If not set, falls back to livekit_url.
    livekit_public_url: Optional[str] = None
    livekit_api_key: Optional[str] = None
    livekit_api_secret: Optional[str] = None
    livekit_token_ttl_minutes: int = 120
    livekit_room_prefix: str = "lms-live"
    livekit_room_empty_timeout_seconds: int = 600
    livekit_server_api_timeout_seconds: int = 10
    livekit_server_api_retry_attempts: int = 3
    livekit_server_api_retry_backoff_seconds: float = 0.4
    livekit_webhook_secret: Optional[str] = None

    embedding_api_key: Optional[str] = None
    embedding_base_url: str = "https://api.yescale.vip/v1/embeddings"
    embedding_model: str = "text-embedding-3-small"
    embedding_timeout_seconds: int = 30

    sentry_dsn: Optional[str] = None

    # ==========================================================================
    # Push Notifications
    # ==========================================================================
    fcm_credentials_path: Optional[str] = None  # Path to Firebase service account JSON
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    apns_key_path: Optional[str] = None  # Path to APNs auth key (.p8)
    apns_bundle_id: str = "com.luuniensuki.lms"
    push_notification_batch_size: int = 500  # FCM allows up to 500 per batch
    push_notification_max_retries: int = 3

    # ==========================================================================
    # File Storage
    # ==========================================================================
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png,image/gif,image/webp"

    # ==========================================================================
    # CORS Settings
    # ==========================================================================
    cors_origins: str = "*"
    cors_allow_credentials: bool = True

    # ==========================================================================
    # Rate Limiting (Future)
    # ==========================================================================
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10

    # ==========================================================================
    # Computed Properties
    # ==========================================================================

    @property
    def allowed_image_types_list(self) -> list[str]:
        """Return allowed image types as a list."""
        return [t.strip() for t in self.allowed_image_types.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and self.log_level.lower() != "debug"


# XP Ranks definition
XP_RANKS = [
    {"title": "Lính Mới", "min_xp": 0, "max_xp": 99},
    {"title": "Học Viên", "min_xp": 100, "max_xp": 299},
    {"title": "Tập Sự", "min_xp": 300, "max_xp": 599},
    {"title": "Khám Phá", "min_xp": 600, "max_xp": 999},
    {"title": "Thám Hiểm", "min_xp": 1000, "max_xp": 1499},
    {"title": "Nghiên Cứu", "min_xp": 1500, "max_xp": 2099},
    {"title": "Học Giả", "min_xp": 2100, "max_xp": 2799},
    {"title": "Chuyên Gia", "min_xp": 2800, "max_xp": 3599},
    {"title": "Bậc Thầy", "min_xp": 3600, "max_xp": 4499},
    {"title": "Sử Quan", "min_xp": 4500, "max_xp": None},
]


def get_rank_for_xp(total_xp: int) -> dict:
    """Get the rank info for a given XP amount."""
    for rank in reversed(XP_RANKS):
        if total_xp >= rank["min_xp"]:
            return rank
    return XP_RANKS[0]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
