//! Route handlers organized by domain.
//!
//! Task 1.16: migrates native routes from inline handlers to dedicated modules.
//! Task 3.1: adds auth module skeleton (Phase 2).
//! Task 4.1: adds users module (Phase 3).
//! Tasks 6–10: adds quizzes, progress, quests, classrooms, leaderboard (Phases 5–9).
//! Tasks 11–14: adds notifications, sessions, crash_reports, admin (Phases 10–13).
//! Task 16.2: adds misc module (Phase 15 — preview, collection, leftovers).

pub mod admin;
pub mod admin_render;
pub mod auth;
pub mod badges;
pub mod classrooms;
pub mod content;
pub mod crash_reports;
pub mod health;
pub mod leaderboard;
pub mod lessons;
pub mod live;
pub mod metrics;
pub mod misc;
pub mod notifications;
pub mod progress;
pub mod quests;
pub mod quizzes;
pub mod reviews;
pub mod route_helpers;
pub mod sessions;
pub mod streak_admin;
pub mod streak_comeback;
pub mod streak_friend;
pub mod streak_repair;
pub mod timeline;
pub mod trail_admin;
pub mod trail_teacher;
pub mod trails;
pub mod users;
