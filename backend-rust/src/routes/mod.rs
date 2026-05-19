//! Route handlers organized by domain.
//!
//! Task 1.16: migrates native routes from inline handlers to dedicated modules.
//! Task 3.1: adds auth module skeleton (Phase 2).
//! Task 4.1: adds users module (Phase 3).
//! Tasks 6–10: adds quizzes, progress, quests, classrooms, leaderboard (Phases 5–9).

pub mod auth;
pub mod badges;
pub mod classrooms;
pub mod content;
pub mod health;
pub mod leaderboard;
pub mod lessons;
pub mod metrics;
pub mod progress;
pub mod quests;
pub mod quizzes;
pub mod users;
