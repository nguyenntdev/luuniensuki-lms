# Course-specific calibration for future-term review

Across 4,967 eligible 2013J learners, transporting course-specific calibration replaced 111 of 496 unrestricted selections. Worst-group recall increased from 10.53% to 17.32% (paired difference 4.39 to 8.92 percentage points, 95% interval). The uncalibrated threshold policy and pooled-calibration ablation selected exactly the same learners as course-specific calibration. The quota differed by three seats and tied on observed worst-group recall. There is no evidence here of an incremental practical gain over the strongest alternatives at any positive threshold. Precision increased from 34.27% to 34.88%, but its paired difference interval of −2.06 to +3.25 points crossed the −1-point margin.

Run from the repository root with the previously downloaded checksum-pinned OULAD archive in private_data/raw.

    OPENBLAS_NUM_THREADS=1 taskset -c 0-15 python research_v4_2/external/allocation/transport/run.py

The runner recomputes source scores from the original feature pipeline, fetches withdrawal labels by registration key, asserts paired capacity, and prints the digest of ordered keys, scores and decisions before reporting results. Expected digest is 5b9ba93e2f36fa5400dbbe9ccfaa0dd18ed4aaca294d5a3833cbd31b7f8f9462. All models use the same 2013B fit. The earlier cohort loader uses 2014J identifiers to exclude overlapping learners. No 2014 outcomes enter the study. Intervals condition on fitted policies and this single evaluation term. Review benefit was never observed.
