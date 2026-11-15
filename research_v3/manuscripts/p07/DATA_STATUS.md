# P07 — Data Status & Rights Assessment (P07-T02/T04)

**Status: PARTIAL** — one external rights-cleared source usable; one BLOCKED
(API key); synthetic stress suites labeled and license-declared.

## A. External sources attempted

### A.1 Smithsonian Open Access — **USABLE (CC0 subset)**

| Item | Value |
|---|---|
| Endpoint tried | `https://api.si.edu/openaccess/api/v1.0/search?q=...` → **HTTP 403** (API key required, registration via api.data.gov) |
| Working alternative | S3 Open Access metadata repository (no key): `https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/fsg/index.txt` and per-unit shards (`fsg/00..05.txt`); announced in the official repo https://github.com/Smithsonian/OpenAccess (repo license: CC0-1.0; GitHub repo frozen 2021-12-21, data now on the S3 registry https://registry.opendata.aws/smithsonian-open-access/) |
| Terms | FAQ https://www.si.edu/openaccess/faq — assets designated CC0 are dedicated to the public domain; "usage conditions apply" assets are NOT CC0. **Only items marked CC0 used; per-media `usage.access == "CC0"` enforced in code** (`research_v3/methods/p07/external.py`). |
| License text captured | `private_data/raw/smithsonian_open_access/2021-12-21/si_license_CC0-1.0.txt` — SHA-256 `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499` |
| Raw snapshot hashes | see `research_artifacts_v3/runs/p07/p07-wave1/results.json` + registry card `smithsonian-open-access-fsg` (`fsg_00..05.txt` SHA-256 pinned in private_data dir) |
| What was derived | 6 FSG shards scanned; **102 records adapted** where rights were exactly CC0; 99 objects pass both record-level and media-level CC0 checks (1 flagged inscription record excluded as ambiguous); 1 record (F1911.145a-c, "Vase shaped like an archaic gu", https://asia.si.edu/object/F1911.145a-c/) states an explicit inscription transcription+translation → `inscription_text=True`; 98 records with NO Inscriptions field → `inscription_text=False` (verified absence); ambiguous records (e.g. F1909.172 "Spurious inscription.", F2017.13.4 verse rendering) → curator abstain, excluded |
| Media downloaded | 2 CC0 JPEGs (gu vessel F1911.145a-c 001: `57b45e7c…5241`, bodhisattva F1907.115 001: `a6694567…0ab6f`) into private_data (gitignored) as provenance verification only — no third-party media is redistributed in Git |
| Scored use | 8 external cases (`research_v3/methods/p07/data/smithsonian_fsg_external.jsonl`): 4 POS/NEG pairs. POS pool contains the transcription-bearing record; NEG pool is identical minus that record (image-exists-missing-inscription stratum on real records) |

### A.2 Europeana — **BLOCKED (API key)**

| Item | Value |
|---|---|
| Endpoint tried | `https://api.europeana.eu/record/v2/search.json?query=bronze&wskey=` → **HTTP 401** (valid wskey required) |
| Registration | https://pro.europeana.eu/page/apis ; terms https://pro.europeana.eu/page/terms-of-use |
| Policy noted | Metadata generally CC0; **media item-level rights vary per object/provider** — must be captured per item |
| Action | BLOCKED card `europeana-api-key-blocked` in `research_v3/datasets/registry.yaml`. **No object metadata invented.** Unblocking requires an API key + per-item rights capture. |

## B. Data actually used for scoring

1. **Synthetic stress suite (n=17 cases)** — `generate_stress_cases(seed=20261115)`,
   deterministic, LICENSE `synthetic, no third-party rights`, `synthetic: true`.
   Strata S1–S7 (see prereg). Used for: identifiability (G16), regression canary,
   mechanism ablations. NEVER pooled with external scores.
2. **External Smithsonian FSG suite (n=8 cases)** — 4 POS/NEG pairs from real
   CC0 records with derivational-fact affordances. Used for: external validity
   of the derivational-fact pipeline on real provider metadata.

## C. Honest limitations of the data

- Single external provider ⇒ cross-provider generalization UNVERIFIED.
- n=8 external cases is illustrative, not powered; no population claim.
- External affordance axes beyond image/inscription are NOT_APPLICABLE (the
  Open Access metadata records used contain no keyboard/ARIA/transcript facts)
  ⇒ the external suite exercises the rights screen + inscription axis only.
- No task-outcome labels from learners exist; gold verdicts are
  derivational-fact oracles (rule-based, from the records themselves), NOT
  human annotations. Human annotation agreement (spec P07) requires real
  raters — BLOCKED for the human-only tasks P07-T19/T20/T21.
- Ambiguity policy: when a record's inscription status cannot be auto-judged
  (explicit-statement rule fails), the record is curator-abstained — we never
  guess absence/presence of transcription.
