//! Pure-Rust FSRS-style scheduler.
//!
//! Implements the core DSR (Difficulty-Stability-Retrievability) update
//! formulas from the FSRS algorithm wiki[^1] without pulling in an external
//! crate, to stay within the project's build memory budget.
//!
//! [^1]: open-spaced-repetition/fsrs4anki (paraphrased for compliance).
//!
//! The implementation is parameterised over the standard 21-weight vector
//! `w0..w20` so per-user optimization can substitute different weights.
//!
//! Spec: `.kiro/specs/fsrs-spaced-repetition/`

use crate::models::fsrs::{CardState, FsrsRating};

/// 21 default weights (FSRS-5 reference), matching the cohort defaults
/// seeded by the migration.
pub const DEFAULT_W: [f64; 21] = [
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0589, 1.5747, 0.1070, 1.0070,
    1.9523, 0.1110, 0.3255, 2.2698, 0.2315, 2.9898, 0.5163, 0.6136, 0.0000, 0.0000,
];

/// Result of a scheduling update.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ScheduleResult {
    pub state: CardState,
    pub difficulty: f64,
    pub stability: f64,
    /// Next interval in days (>= 0).
    pub interval_days: f64,
}

/// Map a numeric quiz score plus an "easy" flag onto a discrete rating.
///
/// Thresholds (from the spec):
/// - `easy_flag = true`        → Easy
/// - `score >= 0.9`            → Good
/// - `0.6 <= score < 0.9`      → Hard
/// - `score < 0.6`             → Again
pub fn map_score_to_rating(score: f64, easy_flag: bool) -> FsrsRating {
    if easy_flag {
        return FsrsRating::Easy;
    }
    if score >= 0.9 {
        FsrsRating::Good
    } else if score >= 0.6 {
        FsrsRating::Hard
    } else {
        FsrsRating::Again
    }
}

/// Apply the scheduler.
///
/// `delta_t_days` is the elapsed time since `fsrs_last_review` in days.
/// `optimal_retention` is the user's target retention rate (e.g. 0.9).
pub fn schedule(
    state: CardState,
    difficulty: Option<f64>,
    stability: Option<f64>,
    delta_t_days: f64,
    rating: FsrsRating,
    w: &[f64; 21],
    optimal_retention: f64,
) -> ScheduleResult {
    let optimal_retention = optimal_retention.clamp(0.5, 0.99);

    match state {
        CardState::New => {
            // First review: stability = w[rating-1], difficulty seeded from w[4..6].
            let s0 = match rating {
                FsrsRating::Again => w[0],
                FsrsRating::Hard => w[1],
                FsrsRating::Good => w[2],
                FsrsRating::Easy => w[3],
            }
            .max(0.1);
            let d0 = init_difficulty(rating, w);
            let next_state = if rating == FsrsRating::Again {
                CardState::Learning
            } else {
                CardState::Review
            };
            ScheduleResult {
                state: next_state,
                difficulty: d0,
                stability: s0,
                interval_days: next_interval(s0, optimal_retention),
            }
        }
        CardState::Learning | CardState::Relearning => {
            let s_prev = stability.unwrap_or(0.5).max(0.1);
            let d_prev = difficulty.unwrap_or(5.0).clamp(1.0, 10.0);
            let s_new = if rating == FsrsRating::Again {
                s_prev
            } else {
                s_prev * (1.0 + 0.5 * rating_factor(rating))
            };
            let d_new = update_difficulty(d_prev, rating, w);
            let next_state = if rating == FsrsRating::Again {
                state
            } else {
                CardState::Review
            };
            ScheduleResult {
                state: next_state,
                difficulty: d_new,
                stability: s_new,
                interval_days: next_interval(s_new, optimal_retention),
            }
        }
        CardState::Review => {
            let s_prev = stability.unwrap_or(1.0).max(0.1);
            let d_prev = difficulty.unwrap_or(5.0).clamp(1.0, 10.0);
            let r = retrievability(delta_t_days, s_prev);

            let s_new = if rating == FsrsRating::Again {
                // Failure → reset towards small stability.
                forgetting_stability(d_prev, s_prev, r, w)
            } else {
                recall_stability(d_prev, s_prev, r, rating, w)
            };
            let d_new = update_difficulty(d_prev, rating, w);
            let next_state = if rating == FsrsRating::Again {
                CardState::Relearning
            } else {
                CardState::Review
            };
            ScheduleResult {
                state: next_state,
                difficulty: d_new,
                stability: s_new,
                interval_days: next_interval(s_new, optimal_retention),
            }
        }
    }
}

fn init_difficulty(rating: FsrsRating, w: &[f64; 21]) -> f64 {
    let r = rating_value(rating);
    (w[4] - (w[5] * (r - 3.0)).exp() + 1.0).clamp(1.0, 10.0)
}

fn update_difficulty(d_prev: f64, rating: FsrsRating, w: &[f64; 21]) -> f64 {
    let delta_d = -w[6] * (rating_value(rating) - 3.0);
    let target = d_prev + delta_d * (10.0 - d_prev) / 9.0;
    target.clamp(1.0, 10.0)
}

fn retrievability(t: f64, s: f64) -> f64 {
    if s <= 0.0 || t <= 0.0 {
        return 1.0;
    }
    (1.0 + t / (9.0 * s)).powf(-1.0)
}

fn recall_stability(d: f64, s: f64, r: f64, rating: FsrsRating, w: &[f64; 21]) -> f64 {
    let hard_penalty = if rating == FsrsRating::Hard { w[15] } else { 1.0 };
    let easy_bonus = if rating == FsrsRating::Easy { w[16] } else { 1.0 };
    let inc = (w[8].exp())
        * (11.0 - d)
        * (s.powf(-w[9]))
        * (((1.0 - r) * w[10]).exp() - 1.0)
        * hard_penalty
        * easy_bonus;
    (s * (1.0 + inc.max(0.0))).max(0.1)
}

fn forgetting_stability(d: f64, s: f64, r: f64, w: &[f64; 21]) -> f64 {
    let v = w[11]
        * d.powf(-w[12])
        * ((s + 1.0).powf(w[13]) - 1.0)
        * ((1.0 - r) * w[14]).exp();
    v.max(0.1)
}

fn rating_value(rating: FsrsRating) -> f64 {
    match rating {
        FsrsRating::Again => 1.0,
        FsrsRating::Hard => 2.0,
        FsrsRating::Good => 3.0,
        FsrsRating::Easy => 4.0,
    }
}

fn rating_factor(rating: FsrsRating) -> f64 {
    match rating {
        FsrsRating::Again => 0.0,
        FsrsRating::Hard => 0.5,
        FsrsRating::Good => 1.0,
        FsrsRating::Easy => 1.5,
    }
}

/// Next interval in days, computed so the predicted retrievability equals
/// the optimal retention.
fn next_interval(stability: f64, optimal_retention: f64) -> f64 {
    if stability <= 0.0 {
        return 1.0;
    }
    let r = optimal_retention.clamp(0.5, 0.99);
    let interval = 9.0 * stability * ((1.0 / r) - 1.0);
    interval.max(1.0).min(36500.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn map_score_thresholds() {
        assert_eq!(map_score_to_rating(0.95, false), FsrsRating::Good);
        assert_eq!(map_score_to_rating(0.75, false), FsrsRating::Hard);
        assert_eq!(map_score_to_rating(0.30, false), FsrsRating::Again);
        assert_eq!(map_score_to_rating(0.30, true), FsrsRating::Easy);
        assert_eq!(map_score_to_rating(0.95, true), FsrsRating::Easy);
    }

    #[test]
    fn boundary_cases() {
        assert_eq!(map_score_to_rating(0.9, false), FsrsRating::Good);
        assert_eq!(map_score_to_rating(0.6, false), FsrsRating::Hard);
        assert_eq!(map_score_to_rating(0.5999, false), FsrsRating::Again);
    }

    #[test]
    fn new_card_good_produces_review_state() {
        let r = schedule(
            CardState::New,
            None,
            None,
            0.0,
            FsrsRating::Good,
            &DEFAULT_W,
            0.9,
        );
        assert_eq!(r.state, CardState::Review);
        assert!(r.difficulty >= 1.0 && r.difficulty <= 10.0);
        assert!(r.stability > 0.0);
        assert!(r.interval_days >= 1.0);
    }

    #[test]
    fn new_card_again_goes_to_learning() {
        let r = schedule(
            CardState::New,
            None,
            None,
            0.0,
            FsrsRating::Again,
            &DEFAULT_W,
            0.9,
        );
        assert_eq!(r.state, CardState::Learning);
    }

    #[test]
    fn review_again_relearning() {
        let r = schedule(
            CardState::Review,
            Some(5.0),
            Some(10.0),
            5.0,
            FsrsRating::Again,
            &DEFAULT_W,
            0.9,
        );
        assert_eq!(r.state, CardState::Relearning);
    }

    #[test]
    fn difficulty_clamped() {
        for rating in [FsrsRating::Again, FsrsRating::Hard, FsrsRating::Good, FsrsRating::Easy] {
            let r = schedule(
                CardState::Review,
                Some(1.0),
                Some(1.0),
                1.0,
                rating,
                &DEFAULT_W,
                0.9,
            );
            assert!(r.difficulty >= 1.0);
            assert!(r.difficulty <= 10.0);
            assert!(r.stability > 0.0);
        }
    }
}


#[cfg(test)]
mod property_tests {
    //! Loop-based property tests for the FSRS scheduler.
    //!
    //! These mirror the Properties documented in
    //! `.kiro/specs/fsrs-spaced-repetition/design.md` without pulling in a
    //! property-testing crate (the build host is memory-constrained).

    use super::*;

    /// Property 1: scheduling preserves invariants regardless of inputs.
    #[test]
    fn property_scheduling_invariants() {
        let states = [
            CardState::New,
            CardState::Learning,
            CardState::Review,
            CardState::Relearning,
        ];
        let ratings = [
            FsrsRating::Again,
            FsrsRating::Hard,
            FsrsRating::Good,
            FsrsRating::Easy,
        ];
        // Sweep difficulty in [1.0, 10.0], stability in [0.1, 1000.0],
        // delta_t in [0.0, 365.0].
        let mut difficulties = vec![];
        let mut stabilities = vec![];
        let mut deltas = vec![];
        for i in 0..6 {
            difficulties.push(1.0 + (i as f64) * 1.8);
            stabilities.push(0.1 + (i as f64) * 100.0);
            deltas.push((i as f64) * 60.0);
        }
        let retentions = [0.7, 0.85, 0.9, 0.95];

        for &state in &states {
            for &rating in &ratings {
                for &d in &difficulties {
                    for &s in &stabilities {
                        for &t in &deltas {
                            for &r in &retentions {
                                let res = schedule(
                                    state,
                                    Some(d),
                                    Some(s),
                                    t,
                                    rating,
                                    &DEFAULT_W,
                                    r,
                                );
                                assert!(
                                    res.difficulty >= 1.0 && res.difficulty <= 10.0,
                                    "difficulty out of range: {}",
                                    res.difficulty
                                );
                                assert!(res.stability > 0.0, "stability not positive");
                                assert!(
                                    res.interval_days >= 1.0,
                                    "interval too short: {}",
                                    res.interval_days
                                );
                            }
                        }
                    }
                }
            }
        }
    }

    /// Property 2: score-to-rating mapping respects thresholds.
    #[test]
    fn property_score_thresholds() {
        // Sweep score in [0.0, 1.0] with step 0.01.
        for i in 0..=100 {
            let score = i as f64 / 100.0;
            // easy_flag = false: thresholds at 0.6 and 0.9
            let r = map_score_to_rating(score, false);
            if score < 0.6 {
                assert_eq!(r, FsrsRating::Again, "score={score}");
            } else if score < 0.9 {
                assert_eq!(r, FsrsRating::Hard, "score={score}");
            } else {
                assert_eq!(r, FsrsRating::Good, "score={score}");
            }
            // easy_flag = true is always Easy regardless of score
            assert_eq!(map_score_to_rating(score, true), FsrsRating::Easy);
        }
    }
}
