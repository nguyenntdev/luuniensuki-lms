//! In-memory token-bucket rate limiter for unauthenticated endpoints.
//!
//! Designed for low-cardinality, anti-abuse use only — not a substitute for
//! a proper L7 limiter (nginx, cloudflare).
//!
//! Features:
//! - Sharded hash maps (64 shards) with per-shard `Mutex` to minimize thread contention.
//! - Bounded TTL token bucket: idle buckets older than 60s are opportunistically evicted.
//! - Hard memory bounds: capped at `MAX_BUCKETS` total across shards (~781 per shard).
//!   If capacity is exceeded, oldest entries are evicted safely without locking all worker threads.

use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};

/// Number of lock shards to prevent global mutex contention under high concurrency.
const NUM_SHARDS: usize = 64;

/// Soft cap on the total number of distinct keys held in the limiter map.
const MAX_BUCKETS: usize = 50_000;

/// Max buckets allowed in an individual shard before eviction triggers.
const MAX_BUCKETS_PER_SHARD: usize = MAX_BUCKETS / NUM_SHARDS;

/// Buckets idle for longer than 60s are considered stale and eligible for eviction.
const BUCKET_TTL: Duration = Duration::from_secs(60);

/// Minimum interval between periodic opportunistic pruning sweeps on a shard.
const PRUNE_INTERVAL: Duration = Duration::from_secs(10);

/// Number of operations on a shard before checking for opportunistic prune.
const PRUNE_OP_THRESHOLD: usize = 256;

#[derive(Clone, Copy, Debug)]
struct Bucket {
    /// Tokens available at `last_refill`.
    tokens: f64,
    /// When tokens were last refilled.
    last_refill: Instant,
}

struct Shard {
    map: HashMap<String, Bucket>,
    last_prune: Instant,
    op_count: usize,
}

struct ShardedLimiter {
    shards: Vec<Mutex<Shard>>,
}

fn limiter() -> &'static ShardedLimiter {
    static LIMITER: OnceLock<ShardedLimiter> = OnceLock::new();
    LIMITER.get_or_init(|| {
        let now = Instant::now();
        let mut shards = Vec::with_capacity(NUM_SHARDS);
        for _ in 0..NUM_SHARDS {
            shards.push(Mutex::new(Shard {
                map: HashMap::new(),
                last_prune: now,
                op_count: 0,
            }));
        }
        ShardedLimiter { shards }
    })
}

fn shard_index(key: &str) -> usize {
    let mut hasher = std::hash::DefaultHasher::new();
    key.hash(&mut hasher);
    (hasher.finish() as usize) % NUM_SHARDS
}

/// Attempt to consume one token from the named bucket.
///
/// Returns `true` if the request is permitted; `false` if the bucket is
/// exhausted.
///
/// `capacity`: maximum tokens the bucket can hold (also the burst).
/// `refill_per_second`: how quickly tokens regenerate.
pub fn try_acquire(key: &str, capacity: f64, refill_per_second: f64) -> bool {
    let now = Instant::now();
    let idx = shard_index(key);
    let shard_mutex = &limiter().shards[idx];

    let mut shard = match shard_mutex.lock() {
        Ok(g) => g,
        Err(p) => p.into_inner(),
    };

    shard.op_count = shard.op_count.saturating_add(1);

    // Opportunistically prune stale buckets (> 60s) if threshold reached or over cap
    let should_prune = shard.op_count >= PRUNE_OP_THRESHOLD
        || shard.map.len() > MAX_BUCKETS_PER_SHARD
        || now.duration_since(shard.last_prune) >= PRUNE_INTERVAL;

    if should_prune {
        prune_shard(&mut shard, now);
    }

    let bucket = shard.map.entry(key.to_string()).or_insert(Bucket {
        tokens: capacity,
        last_refill: now,
    });

    // Refill based on elapsed time.
    let elapsed = now.duration_since(bucket.last_refill).as_secs_f64();
    if elapsed >= BUCKET_TTL.as_secs_f64() {
        // Idle longer than TTL: treat as fully refilled bucket
        bucket.tokens = capacity;
    } else {
        bucket.tokens = (bucket.tokens + elapsed * refill_per_second).min(capacity);
    }
    bucket.last_refill = now;

    if bucket.tokens >= 1.0 {
        bucket.tokens -= 1.0;
        true
    } else {
        false
    }
}

/// Prunes stale buckets (idle for >= 60s) from a single shard. If the shard
/// remains over capacity, evicts oldest entries to enforce hard memory bounds.
fn prune_shard(shard: &mut Shard, now: Instant) {
    shard.op_count = 0;
    shard.last_prune = now;

    // Drop buckets idle for more than BUCKET_TTL (60s)
    shard
        .map
        .retain(|_, b| now.duration_since(b.last_refill) < BUCKET_TTL);

    // If still exceeding MAX_BUCKETS_PER_SHARD, evict the oldest buckets
    if shard.map.len() > MAX_BUCKETS_PER_SHARD {
        let excess = shard.map.len() - MAX_BUCKETS_PER_SHARD;
        let mut entries: Vec<(String, Instant)> = shard
            .map
            .iter()
            .map(|(k, v)| (k.clone(), v.last_refill))
            .collect();
        entries.sort_unstable_by_key(|(_, t)| *t);
        for (k, _) in entries.into_iter().take(excess) {
            shard.map.remove(&k);
        }
    }
}

/// Resets the global state. Test-only.
#[cfg(test)]
pub fn reset_for_tests() {
    let now = Instant::now();
    for shard in &limiter().shards {
        let mut guard = shard.lock().unwrap_or_else(|p| p.into_inner());
        guard.map.clear();
        guard.last_prune = now;
        guard.op_count = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn capacity_is_respected() {
        let key = "test:capacity_respected_isolated";
        for _ in 0..5 {
            assert!(try_acquire(key, 5.0, 1.0));
        }
        assert!(!try_acquire(key, 5.0, 1.0));
    }

    #[test]
    fn keys_are_independent() {
        let k1 = "test:k1_independent_isolated";
        let k2 = "test:k2_independent_isolated";
        for _ in 0..3 {
            assert!(try_acquire(k1, 3.0, 1.0));
        }
        // k2 should still have its full capacity.
        assert!(try_acquire(k2, 3.0, 1.0));
    }

    #[test]
    fn refill_replenishes_over_time() {
        let key = "test:refill_replenishes_isolated";
        // Burn the bucket dry (capacity 2.0, refill rate 10.0 tokens/sec = 1 token per 100ms).
        for _ in 0..2 {
            assert!(try_acquire(key, 2.0, 10.0));
        }
        assert!(!try_acquire(key, 2.0, 10.0));
        // Wait long enough to refill at least one token at 10/s.
        std::thread::sleep(Duration::from_millis(150));
        assert!(try_acquire(key, 2.0, 10.0));
    }

    #[test]
    fn stale_buckets_pruned_on_ttl() {
        let key = "test:ttl_expire_isolated";
        let idx = shard_index(key);

        assert!(try_acquire(key, 5.0, 1.0));

        {
            let mut shard = limiter().shards[idx].lock().unwrap();
            assert!(shard.map.contains_key(key));
            // Simulate 61 seconds passing
            let past = Instant::now() - Duration::from_secs(61);
            if let Some(b) = shard.map.get_mut(key) {
                b.last_refill = past;
            }
            prune_shard(&mut shard, Instant::now());
            assert!(
                !shard.map.contains_key(key),
                "Expired bucket should have been pruned"
            );
        }
    }

    #[test]
    fn shard_bounds_enforced_under_overflow() {
        let idx = shard_index("test:overflow_0_isolated");
        let now = Instant::now();

        {
            let mut shard = limiter().shards[idx].lock().unwrap();
            // Artificially insert more than MAX_BUCKETS_PER_SHARD
            for i in 0..(MAX_BUCKETS_PER_SHARD + 50) {
                shard.map.insert(
                    format!("overflow_key_isolated_{}", i),
                    Bucket {
                        tokens: 1.0,
                        last_refill: now,
                    },
                );
            }
            assert!(shard.map.len() > MAX_BUCKETS_PER_SHARD);
            prune_shard(&mut shard, now);
            assert_eq!(shard.map.len(), MAX_BUCKETS_PER_SHARD);
        }
    }
}
