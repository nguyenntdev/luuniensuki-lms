//! Route handlers organized by domain.
//!
//! Task 1.16: migrates native routes from inline handlers to dedicated modules.
//! Task 3.1: adds auth module skeleton (Phase 2).
//! Task 4.1: adds users module (Phase 3).

pub mod auth;
pub mod badges;
pub mod content;
pub mod health;
pub mod metrics;
pub mod users;
