# LƯU NIÊN — RBPC 2026: 3D ASSET LINEAGE, COPYRIGHT & PERFORMANCE REPORT

**Document ID:** `DOC-RBPC-3D-001`  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687`  
**Governing Standard:** Master Spec §V2-C & ADR 05  
**Author:** AGENT 09 (3D Media & Copyright Specialist)  

---

## 1. Executive Summary & Rights Inventory

This document details the complete lineage, dataset provenance, copyright terms, WebGL memory profiling, and fallback architecture for all 3D assets on **LƯU NIÊN — The Living Heritage Platform**.

The platform maintains a strict **Rights Decision Gate**:
- `SF-020` is **PERMANENTLY REJECTED** due to acknowledged fantasy architectural details.
- `SF-010` and `SF-017` are **BLOCKED** from commercial self-hosting and AI training due to `CC BY-NC-SA` and `NoAI` restrictions.
- `SF-009`, `SF-011`, and `SF-016` are approved for user-initiated lazy iframe embedding with prominent creator credit and DOI citation.
- For all unreviewed or unavailable models, the platform fails closed to high-resolution 2D archival photography via `ThreeDFallback.tsx`.

---

## 2. Dataset Lineage & Photogrammetric Provenance

### 2.1 The CyArk / Open Heritage 3D Heritage Collection
Several approved and reference models on Sketchfab originate from terrestrial laser scanning and photogrammetric surveys conducted by **CyArk** in partnership with the **Hue Monuments Conservation Centre (HMCC)**:

| Model ID | Site & Subject | Original Surveyor / Creator | Survey Methodology | Dataset DOI / Archive Link |
|---|---|---|---|---|
| `SF-009` | Lăng Tự Đức (Tomb of Tự Đức) | CyArk / processed by matousekfoto | Terrestrial LiDAR + High-res DSLR Photogrammetry | [DOI: 10.26301/n06n-qa49](https://doi.org/10.26301/n06n-qa49) |
| `SF-011` | Bi Đình — Lăng Tự Đức (Stele Pavilion) | CyArk / processed by Vasilis Haroupas | Close-range photogrammetric photomeshing | [DOI: 10.26301/n06n-qa49](https://doi.org/10.26301/n06n-qa49) |
| `SF-016` | Cung An Định (An Định Palace) | CyArk / processed by Alexei MKLT | Drone photogrammetry + ground laser scanning | [DOI: 10.26301/4z5b-vz23](https://doi.org/10.26301/4z5b-vz23) |

**Attribution Template for CyArk Derived Models:**
> *"3D model derived from Open Heritage 3D / CyArk LiDAR and photogrammetric survey data (DOI: 10.26301/n06n-qa49), created by [Author Name] under Creative Commons Attribution 4.0 International (CC BY 4.0)."*

---

## 3. WebGL Memory Profiling & Mobile Performance Guardrails

### 3.1 VRAM & Geometry Benchmarks
- **Local Cao Đỉnh Meshes:**
  - `CAO-DINH-v1-512.glb` (5.0 MB): Peak VRAM ~28 MB. Safe for mobile devices.
  - `CAO-DINH-v1-1k.glb` (27 MB): Peak VRAM ~92 MB. Desktop only.
  - `CAO-DINH-v1-2k.glb` (29 MB): Peak VRAM ~140 MB. Restricted to high-tier desktop GPUs.
- **Embedded Sketchfab Iframes:**
  - Standard iframe memory consumption: ~45–65 MB per active instance.
  - **Memory Guardrail:** The `SketchfabExhibit.tsx` component automatically unmounts the iframe upon tab switch or modal dismissal, calling `iframe.src = 'about:blank'` to force the browser to garbage-collect the WebGL context.

### 3.2 Mobile Iframe Policy
1. **Never Autoplay:** Every iframe embed must set `autostart=0`.
2. **User-Initiated Mounting:** The iframe is injected into the DOM ONLY when the user explicitly clicks the *"Xem mô hình 3D tương tác"* button on `SketchfabExhibit.tsx`.
3. **Bandwidth Throttling Detection:** On slow 3G connections (or when `navigator.connection.saveData == true`), the 3D button is replaced with an explicit prompt: *"Kết nối mạng tiết kiệm dữ liệu — xem ảnh tư liệu 2D thay thế."*

---

## 4. Rights Withdrawal SLA & Takedown Protocol (<15 Minutes)

In strict alignment with `docs/rbpc/CONTENT_RIGHTS.md` (§7.3) and Master Spec §V2-C.4:
- **Takedown SLA:** Maximum **15 minutes** from verified notice receipt to complete edge purge.
- **Protocol & Operational Steps:**
  1. **Flagged State Transition:** Asset status toggled to `withdrawn` or `revoked` in `sketchfab-curated.yaml` / database.
  2. **Edge Cache Invalidation:** Cloudflare CDN and Redis application cache keys for all affected media endpoints (`/api/v1/heritage/places/{slug}/media`, etc.) purged within <15 minutes.
  3. **Fail-Closed Fallback:** The front-end client automatically degrades to `ThreeDFallback.tsx` with verified archival 2D imagery and citations. No broken containers, missing assets, or 404 errors are exposed.
  4. **Immutable Audit Entry:** All takedown events, correspondence verification hashes, and timestamps are permanently recorded in `rbpc_content_audits`.

