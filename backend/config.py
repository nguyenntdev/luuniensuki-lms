"""
Centralized configuration for Luuniensuki LMS.

This module provides a single source of truth for all application settings,
loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Sentinel values that are never acceptable for secrets in production. Used by
# the startup validator to fail closed when a real secret has not been supplied.
SENTINELS = {"", "CHANGE_ME_IN_PRODUCTION"}


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
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    # Shared identity claims for the cross-backend JWT contract (Req 26.3).
    # Must match the Rust backend's JWT_ISSUER / JWT_AUDIENCE defaults.
    jwt_issuer: str = "luuniensuki"
    jwt_audience: str = "luuniensuki-app"
    # Issue-then-enforce transition flag for the iss/aud identity claims
    # (Req 26.4). When False (default), tokens are accepted whether or not
    # they carry iss/aud, so a rolling deploy where one backend has not yet
    # started issuing the new claims does not break cross-backend auth. When
    # True, both backends are known to issue the claims, so iss/aud become
    # required and are validated against jwt_issuer / jwt_audience.
    jwt_validate_new_claims: bool = False
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30
    password_reset_return_token: bool = False

    # Cookie settings for JWT tokens
    access_cookie_name: str = "luuniensuki_access"
    refresh_cookie_name: str = "luuniensuki_refresh"
    cookie_domain: Optional[str] = None
    # When unset (None), the secure flag resolves based on the environment:
    # enabled in production, disabled otherwise. An operator may force a value
    # by setting the COOKIE_SECURE env var explicitly.
    cookie_secure: Optional[bool] = None
    cookie_samesite: str = "lax"
    cookie_path: str = "/"

    # ==========================================================================
    # Application
    # ==========================================================================
    environment: str = "development"
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
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_fallback_model: str = "deepseek-v3.1"
    deepseek_timeout_seconds: int = 45
    deepseek_max_retries: int = 1
    live_data_encryption_key: Optional[str] = None

    # ==========================================================================
    # Backend Voice (STT/TTS)
    # ==========================================================================
    voice_api_key: Optional[str] = None
    voice_base_url: Optional[str] = None
    voice_stt_model: str = "gpt-4o-transcribe"
    voice_stt_language: str = "vi"
    voice_stt_prompt: str = (
        "Đây là đoạn hội thoại tiếng Việt về lịch sử và di sản Cố đô Huế, "
        "Cửu Đỉnh và triều Nguyễn."
    )
    voice_tts_model: str = "tts-1"
    voice_tts_voice: str = "shimmer"
    voice_tts_instructions: str = (
        "Bạn là cô giáo người Việt thân thiện, ấm áp, kiên nhẫn đang giảng bài cho học sinh. "
        "Nói với ngữ điệu tự nhiên, trìu mến và truyền cảm; nhấn nhá hợp lý, ngắt nghỉ theo dấu câu, "
        "không đọc đều đều như máy. Giữ nhịp vừa phải, rõ ràng."
    )
    voice_tts_allow_edge_fallback: bool = True
    voice_tts_allow_gtts_fallback: bool = True
    voice_edge_tts_voice: str = "vi-VN-HoaiMyNeural"
    voice_edge_tts_rate: str = "+0%"
    voice_edge_tts_pitch: str = "+0Hz"
    voice_edge_tts_volume: str = "+0%"
    voice_gtts_lang: str = "vi"
    voice_gtts_tld: str = "com.vn"
    voice_gtts_slow: bool = False
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
    live_default_grade_level: str = "middle_school"
    live_ai_persona_overrides: Optional[str] = None
    live_transcript_retention_days: int = 30
    live_summary_retention_days: int = 90
    live_audio_retention_days: int = 7
    live_summary_max_turns: int = 120

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
    # Single configured base location used for BOTH writing uploaded avatars
    # and serving them via the static mount, so the stored file and the served
    # URL always resolve to the same location (Req 11.1, 11.2, 11.3).
    avatar_dir: str = "uploads/avatars"
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
    live_rate_limit_requests_per_minute: int = 120
    live_ai_rate_limit_requests_per_minute: int = 45
    live_rate_limit_window_seconds: int = 60

    # ==========================================================================
    # Live AI Safety / Reliability / Cost
    # ==========================================================================
    live_ai_enable_guardrails: bool = True
    live_ai_block_unsafe_content: bool = True
    live_ai_enable_observability: bool = True
    live_ai_observability_max_points: int = 5000
    live_ai_circuit_breaker_failures: int = 5
    live_ai_circuit_breaker_recovery_seconds: int = 45
    live_ai_cost_ceiling_usd: float = 3.0
    live_ai_input_cost_per_1m_tokens: float = 0.14
    live_ai_output_cost_per_1m_tokens: float = 0.28
    live_ai_stt_cost_per_minute_usd: float = 0.006
    live_ai_tts_cost_per_1k_chars_usd: float = 0.015

    # Real-time conversational AI teacher (Path B). Per-deployment default voice
    # mode; a classroom may override via session_metadata.voice_mode.
    #   "legacy"   — turn-based polled STT->DeepSeek->TTS (current behavior)
    #   "realtime" — continuous speech-to-speech loop (requires the audio bridge)
    live_voice_mode: str = "legacy"
    # Per-session realtime audio-minute budget (input+output). 0 = unlimited.
    live_realtime_audio_minute_ceiling: float = 30.0
    # Hard cap on concurrent realtime audio bridges on this host (resource bound;
    # the constrained box is internal-testing only). Over-cap sessions fall back
    # to the legacy turn-based loop.
    live_realtime_max_sessions: int = 2

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
        return self.environment.lower() == "production"

    @property
    def cookie_secure_effective(self) -> bool:
        """Resolve the effective secure-cookie setting.

        When the operator has not explicitly overridden ``cookie_secure``
        (i.e. it is ``None`` because ``COOKIE_SECURE`` was not supplied), the
        secure flag defaults to enabled in production and disabled otherwise.
        An explicit value always takes precedence.
        """
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.is_production

    # ==========================================================================
    # Validators
    # ==========================================================================

    @model_validator(mode="after")
    def _validate_production_security(self) -> "Settings":
        """Fail closed when insecure settings are detected in production.

        Collects offending configuration keys and raises a fatal error naming
        them. Secret values are never included in the error message.
        """
        if self.is_production:
            problems: list[str] = []

            if self.jwt_secret_key in SENTINELS:
                problems.append("JWT_SECRET_KEY")

            if self.cors_allow_credentials and "*" in self.cors_origins_list:
                problems.append("CORS_ORIGINS (wildcard with credentials)")

            if self.password_reset_return_token:
                problems.append("PASSWORD_RESET_RETURN_TOKEN")

            if problems:
                raise RuntimeError(
                    f"Insecure production configuration: {', '.join(problems)}"
                )

        return self


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
