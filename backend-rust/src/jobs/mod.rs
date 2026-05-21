//! Background jobs spawned at startup.
//!
//! See `.kiro/specs/streak-repair-economy/` for the requirements behind each
//! job.

pub mod friend_streak_job;
pub mod streak_rollover_job;
pub mod trail_certificate_retry_job;
pub mod trail_reminder_job;
