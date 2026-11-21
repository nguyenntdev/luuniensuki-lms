"""Check whether the public trace contains the earlier practice implied by item counts."""
import json

import study

# Restrict this diagnostic to the registered training learners. Different strings in
# different languages are separate items, exactly as in the feature constructor.
frame = study.cohort(10, 11)
item = ["user_id", "learning_language", "lexeme_string"]
occasion = item + ["timestamp"]
grouped = frame.groupby(occasion, sort=True)
blocks = grouped.agg(
    rows=("delta", "size"),
    delta=("delta", "first"),
    seen=("session_seen", "sum"),
    correct=("session_correct", "sum"),
    history_seen=("history_seen", "first"),
    history_correct=("history_correct", "first"),
).reset_index()
items = blocks.groupby(item, sort=False)
prior_time = items.timestamp.shift()
prior_seen = items.history_seen.shift() + items.seen.shift()
prior_correct = items.history_correct.shift() + items.correct.shift()
first = prior_time.isna()
# Multirow item/timestamp groups can have different internal counts. Exclude both
# ends of such transitions from the one-step history reconciliation.
comparable = ~first & blocks.rows.eq(1) & items.rows.shift().eq(1)
elapsed_ok = blocks.timestamp.sub(prior_time).eq(blocks.delta)
seen_ok = blocks.history_seen.eq(prior_seen)
correct_ok = blocks.history_correct.eq(prior_correct)
result = dict(
    input_sha256=study.digest(study.ARCHIVE),
    train_buckets=[10, 11],
    learners=int(frame.user_id.nunique()),
    rows=len(frame),
    learner_item_timestamps=len(blocks),
    tied_item_timestamps=int(blocks.rows.gt(1).sum()),
    first_item_encounters=int(first.sum()),
    first_with_prior_exposure=int((first & blocks.history_seen.gt(0)).sum()),
    consecutive_singleton_transitions=int(comparable.sum()),
    exact_elapsed_seconds=int((comparable & elapsed_ok).sum()),
    exact_prior_seen=int((comparable & seen_ok).sum()),
    exact_prior_correct=int((comparable & correct_ok).sum()),
    all_three_reconcile=int((comparable & seen_ok & correct_ok & elapsed_ok).sum()),
)
print(json.dumps(result, indent=2))
