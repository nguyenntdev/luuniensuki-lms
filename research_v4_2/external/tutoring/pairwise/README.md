# MRBench tutor switching

The gated policy selected the training-best tutor on all 300 conversations (206 opening prompts). No contrast cleared the frozen support rule. Ungated switching changed 136 choices, gaining 13 Yes labels and losing 20 relative to fixed selection. This study found no incremental value for the gated method on the publicly labeled development set. The endpoint is the human Providing_Guidance annotation.

Run from this directory with the public devset path supplied as the argument.

    sha256sum -c protocol.sha256
    OPENBLAS_NUM_THREADS=1 taskset -c 12-23 python evaluate.py /tmp/mrbench_v3_devset.json

The existing grader_scores.csv input has SHA-256 6c202eda873b938e1debb512b9cfd9d6f21e087aceb3b6c9aa908293e369c73b. Each results.txt row gives the comparator, its Yes count, gated wins, gated losses and the prompt-cluster bootstrap interval for gated minus comparator. Intervals are descriptive and conditional on the fitted folds.
