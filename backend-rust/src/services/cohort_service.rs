//! Deterministic FSRS A/B cohort assignment.
//!
//! Hash `"fsrs_v1_" || user_id.as_bytes()` with SHA-256; the first byte
//! decides treatment (FSRS) vs control (legacy SM-2). Sticky by construction:
//! the same UUID always lands in the same bucket.
//!
//! Spec: `.kiro/specs/fsrs-spaced-repetition/`

use sha2::{Digest, Sha256};
use uuid::Uuid;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Cohort {
    Treatment,
    Control,
}

impl Cohort {
    pub fn name(&self) -> &'static str {
        match self {
            Cohort::Treatment => "fsrs_v1_treatment",
            Cohort::Control => "fsrs_v1_control",
        }
    }
}

pub fn assign_cohort(user_id: &Uuid) -> Cohort {
    let mut hasher = Sha256::new();
    hasher.update(b"fsrs_v1_");
    hasher.update(user_id.as_bytes());
    let hash = hasher.finalize();
    if hash[0] < 128 {
        Cohort::Treatment
    } else {
        Cohort::Control
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deterministic() {
        let u = Uuid::new_v4();
        let a = assign_cohort(&u);
        let b = assign_cohort(&u);
        assert_eq!(a, b);
    }

    #[test]
    fn approximate_5050() {
        let mut treatment = 0;
        let mut control = 0;
        for _ in 0..5_000 {
            match assign_cohort(&Uuid::new_v4()) {
                Cohort::Treatment => treatment += 1,
                Cohort::Control => control += 1,
            }
        }
        // Expect within ~5 percentage points of 50/50.
        let ratio = treatment as f64 / (treatment + control) as f64;
        assert!(
            (0.45..=0.55).contains(&ratio),
            "expected ~50/50 split, got treatment={treatment}, control={control}",
        );
    }
}


#[cfg(test)]
mod property_tests {
    //! Loop-based property tests for cohort assignment.

    use super::*;

    /// Property 6 (determinism): same UUID always lands in the same cohort.
    #[test]
    fn property_determinism_dense() {
        for _ in 0..1_000 {
            let u = Uuid::new_v4();
            let first = assign_cohort(&u);
            for _ in 0..5 {
                assert_eq!(assign_cohort(&u), first, "cohort flipped on retry");
            }
        }
    }
}
