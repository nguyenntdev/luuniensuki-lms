# P12 Novelty Counterexample

## The Failure of Prior Art
Prior retrieval+NLI verifiers (e.g. CoVeGAT, AVeriTeC) operate on flat text snippets retrieved by embedding or BM25 similarity.
When a student cites a historical assertion:
1. If the citation references a modernized publication edition where page numbers differ from the woodblock manuscript, prior systems fail with 404/UNVERIFIED.
2. If an archival page contains negation ('dụ đính chính ... không phải khắc nhầm, bác bỏ lời tấu sai'), standard NLI systems misinterpret the high keyword overlap as SUPPORT for the myth rather than REFUTE.

## Proposed Candidate Mechanism
PageVerifiableArchivalLedger:
- Maps edition aliases via formal registry.
- Enforces exact page digests and checks refutation keywords to output a clean 3-way verdict (SUPPORT, REFUTE, UNVERIFIED).
- Appends cryptographic Merkle block containing (claim_id, locator_digest, page_hash, prev_hash).
