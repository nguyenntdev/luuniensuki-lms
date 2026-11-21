# Anki transfer feasibility

The FSRS-Anki-20k release describes repeated flashcard reviews from a different platform than the Duolingo training release. Its preprocessed schema provides per-card elapsed seconds, review order and self-rated recall (Again = failure, Hard/Good/Easy = success). This changes the outcome from a graded fraction correct to a self-reported binary response. The first collection download returned HTTP 401 anonymously. The release's public benchmark predictions provide an independently downloadable example of labeled forecasts, but the inspected record lacks elapsed times, card identifiers and review history. No external model comparison or practical gain was established.

Reproduce the two source checks from a temporary directory. The second request retrieves a bounded prefix and parses only its first complete line.

```bash
cd "$(mktemp -d)"
curl -fLsS https://huggingface.co/datasets/open-spaced-repetition/FSRS-Anki-20k/resolve/982db773ab401c1ce5994d28c5730550479e053c/dataset/1/1.csv -o collection.csv
curl -fLsS -r 0-4194303 'https://huggingface.co/datasets/open-spaced-repetition/srs-benchmark-raw/resolve/6b7ddc14b567dd895a9f65967154cdb16a25276d/HLR.jsonl?prefix=4m' -o prefix
taskset -c 0-9 python -c 'import json; d=json.loads(open("prefix").readline()); print(sorted(d), d["user"], len(d["p"]), len(d["y"]))'
```

Observed output was `['p', 'user', 'y'] 1 2450 2450`. The two releases have separate revision histories. Their row alignment has not been verified.

An exact replay of the sealed confirmatory ensemble also requires absolute timestamp features for hour of day and between-item learner gaps. Review order and same-card elapsed seconds alone do not identify those features. With authorized timestamped review logs, a transfer protocol could freeze a mapping for unseen item and language categories, reconstruct history strictly before each encounter, and score the sealed ensemble and matched CatBoost on identical repeated-card events. Report paired learner-average binary log loss and resample whole learners. Any clock imputation would require a separately identified sensitivity analysis.

[Anki collection schema](https://huggingface.co/datasets/open-spaced-repetition/FSRS-Anki-20k/blob/982db773ab401c1ce5994d28c5730550479e053c/README.md) · [Benchmark prediction archive](https://huggingface.co/datasets/open-spaced-repetition/srs-benchmark-raw/tree/6b7ddc14b567dd895a9f65967154cdb16a25276d) · [Frozen model features](../confirmatory/study.py)
