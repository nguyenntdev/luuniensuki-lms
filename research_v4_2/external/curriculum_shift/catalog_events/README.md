# Locating published curriculum edits

The Odin Project publishes merged curriculum change records and structured Content labels on its [pull requests](https://github.com/TheOdinProject/curriculum/pulls?q=is%3Apr+is%3Amerged). The endpoint is whether a merged edit carries the Foundations label, conditional on having at least one Content label. Labels are recorded separately from the title. Their authorship and possible path-based automation are unverified. This measures localization of documented edits. It cannot establish a change in learning outcomes or detect an unannounced revision.

## Protocol fixed before scoring

Extract the 100 closed PR records retrieved on 2026-11-21, bounded by PR numbers 31349–31544 and creation dates August 30–November 17, 2026 UTC. Retain merged, Content-labeled records. Order by PR number and train on the earliest two thirds (integer floor), then score the remainder. Compare character 3–5 gram TF-IDF cosine nearest neighbor with word unigram TF-IDF nearest neighbor and training-majority prediction. All use the same split and title-only inputs. Break similarity ties by earliest training record. Report balanced accuracy, confusion counts and per-record predictions. Exploratory convenience sample, one repository, no tuning or superiority criterion.

The extract stores PR numbers, dates, label flags and truncated SHA-256 fingerprints of lowercase title tokens. To preserve character overlap for scoring, it also stores hashed character grams. No lesson text or raw PR titles are redistributed. See the upstream [curriculum license](https://github.com/TheOdinProject/curriculum/blob/main/license.md).

Run `python study.py` in this directory. To reconstruct features from the original GitHub REST /pulls response array use `python study.py original.json`. Mutable upstream labels may differ on a later retrieval.

The Odin Project credits Erik Trautman and licenses the curriculum under CC BY-NC-SA 4.0. The derived feature extract is offered under the same license.

Of 77 eligible records, 51 trained the models and 26 were held out. Character matching identified 2 of 13 Foundations edits with zero false positives. Word matching identified the same number with two false positives. Balanced accuracy was 0.577 versus 0.500 for both controls. The two-error difference on this small sample supports only an exploratory comparison. PR number orders creation, and merge order can differ. The experiment uses a frozen retrospective split.

A [subsequent path audit](../path_labels/README.md) located an automatic labeler keyed to edited paths. Landed paths reconstructed all 26 held-out labels. Individual label authorship remains unknown.
