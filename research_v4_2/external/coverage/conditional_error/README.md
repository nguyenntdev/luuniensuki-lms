The covariate-augmented correctness selector increased worst-course error to 66.63%. Maximum confidence yielded 65.73%, the matched learned control 65.33%, and negative entropy 66.43%. The paired increases versus confidence and the learned control were 0.90 points (95% interval 0.14–1.71) and 1.30 points (0.55–2.08). Pooled errors were 53.89%, 53.67%, 53.59% and 54.56%, respectively, in the same order as the methods above. The prespecified win criterion failed.

This reuses the previously studied 2014J presentation with a day-zero enrollment landmark. The estimates condition on the fitted models, quotas and test presentation. They do not measure across-presentation or retraining uncertainty. CCC was unseen in training. A missing unregistration date is treated as no known withdrawal. Quotas require a batch of enrollment records per course. Maximum softmax probability implements the ranking of Hendrycks and Gimpel (https://openreview.net/forum?id=Hkg4TI9xl). Negative entropy implements the local P01 uncertainty comparator. The comparisons apply to the shared enrollment-only base model.

From this directory run the following with the extracted public OULAD CSV directory. The result records input hashes and course counts in eligible, accepted, error order. Predictions contain original join keys, outcomes, predictions, scores and acceptance masks.

    sha256sum -c protocol.sha256
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 24-35 python evaluate.py /path/to/oulad

Source: Kuzilek et al., Open University Learning Analytics Dataset, https://doi.org/10.1038/sdata.2017.171 (CC BY 4.0).

On CCC, each learned selector accepted 998 registrations. They shared 967 selections and 639 errors. Of the 31 registrations newly admitted by the augmented selector, it misclassified 26. The matched control misclassified 13 of the 31 displaced registrations. Those exchanges account for all 13 additional errors. The [course-level counts](exchanges.csv) reproduce with `python exchanges.py` in this directory.
