//! In-memory token-bucket rate limiter for unauthenticated endpoints.
//!
//! Designed for low-cardinality, anti-abuse use only — not a substitute for
//! a proper L7 limiter (nginx, cloudflare). Buckets are keyed by a string
//! (typically `"verify:<ip>"`) and stored in a global Mutex<HashMap>.
//!
//! Capacity and refill rate are per-bucket and supplied by the caller. The
//! map is pruned opportunistically when its size exceeds a soft cap so it
//! cannot grow without bound under attack.

use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};

/// Soft cap on the number of distinct keys held in the limiter map.
const MAX_BUCKETS: usize = 50_000;

#[derive(Clone, Copy, Debug)]
struct Bucket {
    /// Tokens available at `last_refill`.
    tokens: f64,
    /// When tokens were last refilled.
    last_refill: Instant,
}

static GLOBAL: Mutex<Option<HashMap<String, Bucket>>> = Mutex::new(None);

/// Attempt to consume one token from the named bucket.
///
/// Returns `true` if the request is permitted; `false` if the bucket is
/// exhausted.
///
/// `capacity`: maximum tokens the bucket can hold (also the burst).
/// `refill_per_second`: how quickly tokens regenerate.
pub fn try_acquire(key: &str, capacity: f64, refill_per_second: f64) -> bool {
    let now = Instant::now();
    let mut guard = match GLOBAL.lock() {
        Ok(g) => g,
        Err(p) => p.into_inner(),
    };
    let map = guard.get_or_insert_with(HashMap::new);

    // Prune occasionally to keep memory bounded.
    if map.len() > MAX_BUCKETS {
        prune(map, now);
    }

    let bucket = map.entry(key.to_string()).or_insert(Bucket {
        tokens: capacity,
        last_refill: now,
    });

    // Refill based on elapsed time.
    let elapsed = now.duration_since(bucket.last_refill).as_secs_f64();
    bucket.tokens = (bucket.tokens + elapsed * refill_per_second).min(capacity);
    bucket.last_refill = now;

    if bucket.tokens >= 1.0 {
        bucket.tokens -= 1.0;
        true
    } else {
        false
    }
}

/// Drop buckets that have been idle for more than 5 minutes. Callers don't
/// need to do this; we run it implicitly when the map grows past the cap.
fn prune(map: &mut HashMap<String, Bucket>, now: Instant) {
    let stale_after = Duration::from_secs(300);
    map.retain(|_, b| now.duration_since(b.last_refill) < stale_after);
}

/// Resets the global state. Test-only.
#[cfg(test)]
pub fn reset_for_tests() {
    let mut g = GLOBAL.lock().unwrap();
    *g = Some(HashMap::new());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn capacity_is_respected() {
        reset_for_tests();
        for _ in 0..5 {
            assert!(try_acquire("test:cap", 5.0, 1.0));
        }
        assert!(!try_acquire("test:cap", 5.0, 1.0));
    }

    #[test]
    fn keys_are_independent() {
        reset_for_tests();
        for _ in 0..3 {
            assert!(try_acquire("test:k1", 3.0, 1.0));
        }
        // k2 should still have its full capacity.
        assert!(try_acquire("test:k2", 3.0, 1.0));
    }

    #[test]
    fn refill_replenishes_over_time() {
        reset_for_tests();
        // Burn the bucket dry.
        for _ in 0..2 {
            assert!(try_acquire("test:refill", 2.0, 100.0));
        }
        assert!(!try_acquire("test:refill", 2.0, 100.0));
        // Wait long enough to refill at least one token at 100/s.
        std::thread::sleep(Duration::from_millis(50));
        assert!(try_acquire("test:refill", 2.0, 100.0));
    }
}
