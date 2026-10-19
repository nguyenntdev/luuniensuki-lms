# LƯU NIÊN — RBPC 2026: MEDIA ASSETS & RIGHTS MANIFEST

**Document ID:** `DOC-RBPC-MEDIAMANIFEST-001`  
**Governing Policy:** Master Spec §V2-C & ADR 05  
**Author:** AGENT 09 (3D Media & Copyright Specialist)  

---

## 1. Executive Summary

This manifest catalogs every visual asset, 3D model, and archival photograph used in the LƯU NIÊN competition pitch deck, video presentation, and web demonstration. Every asset is verified for intellectual property compliance, creative commons licensing, and non-commercial integrity.

---

## 2. 3D Model Registry Status (Sketchfab SF-001 to SF-023)

### Approved Candidate Embeds (CC BY 4.0 — User-Initiated Lazy Iframe)
| Model ID | Site | Model Title & Author | Displayed License | Required Attribution Text |
|---|---|---|---|---|
| `SF-009` | Lăng Tự Đức | *Tomb of Tu Duc* by matousekfoto | `CC BY 4.0` | "3D photogrammetry by matousekfoto based on CyArk / Open Heritage 3D dataset (DOI: 10.26301/n06n-qa49) under CC BY 4.0." |
| `SF-011` | Bi Đình — Lăng Tự Đức | *Stele Building* by Vasilis Haroupas | `CC BY 4.0` | "3D mesh by Vasilis Haroupas based on CyArk dataset (DOI: 10.26301/n06n-qa49) under CC BY 4.0." |
| `SF-016` | Cung An Định | *An Dinh Palace* by Alexei MKLT | `CC BY 4.0` | "3D mesh by Alexei MKLT based on Open Heritage 3D dataset (DOI: 10.26301/4z5b-vz23) under CC BY 4.0." |

### Blocked Models (Quarantined from Commercial Views & AI Training)
| Model ID | Subject & Author | License / Restriction | Platform Enforcement |
|---|---|---|---|
| `SF-010` | *Tomb of Tu Duc* by Agisoft | `CC BY-NC-SA 4.0` | Blocked from commercial views and AI training; renders `ThreeDFallback.tsx` with outbound research link. |
| `SF-017` | *An Dinh Palace* by Miguel Bandera | `CC BY-NC-SA` + `NoAI` | Blocked from commercial views and strictly barred from AI RAG embeddings; renders `ThreeDFallback.tsx`. |
| `SF-020` | *Đại nội Huế Văn Hóa VN* by nguyenduc0 | **REJECTED ACCURACY** | Author acknowledged fantasy/imagined details; **PERMANENTLY REJECTED** from all documentary views. |

---

## 3. Documentary Living Artisan Portraits (100% Written Consent)

| Creator ID | Artisan Name | Tradition | Written Consent Reference | Commercial Usage Rights |
|---|---|---|---|:---:|
| `c1010001-0001-...` | NNND Nguyễn Văn Sinh | Đúc đồng Phường Đúc | `CONSENT-PD-001` (15/09/2026) | Verified for educational, competition, and booking inquiry display. |
| `c1010001-0002-...` | ThS. Đỗ Hữu Triết | Nghệ thuật Pháp lam Huế | `CONSENT-PL-002` (20/09/2026) | Verified for educational, competition, and booking inquiry display. |
| `c1010001-0003-...` | NNƯT Thân Văn Huy | Hoa giấy Thanh Tiên | `CONSENT-TT-003` (22/09/2026) | Verified for educational, competition, and booking inquiry display. |

---

## 4. Archival Photography & Historical Rubbings

- **Bản Đúc Nổi Cửu Đỉnh:** Imperial bronze rubbings and historical photographs (`ban-duc-noi/CAO DINH/`) are scholarly photographic records used under academic educational fair use with attribution to the Hue Monuments Conservation Centre (HMCC).
- **Public Domain Historical Photos:** 19th and early 20th-century historical photographs (*BAVH*, Albert Sallet collection) are in the public domain ($>70$ years post-publication).
