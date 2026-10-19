# LƯU NIÊN — RBPC 2026: HISTORICAL EVIDENCE EVALUATION & UNCERTAINTY REGISTER

**Document ID:** `DOC-RBPC-HISTEVAL-001`  
**Base Commit SHA:** `e19aebc0e7f66f7863659fd658c204739e199687`  
**Content Scope:** `RBPC_HUE`  
**Author:** AGENT 08 (Heritage Research & Content Specialist)  

---

## 1. Executive Summary & Epistemic Authority

This document formalizes the historical evidence evaluation, epistemic uncertainty register, and cross-cultural comparison rules for **LƯU NIÊN — The Living Heritage Bridge**.

Every historical fact, date, architectural measurement, and cultural narrative displayed on the platform or utilized in RAG retrieval must trace to primary imperial annals or peer-reviewed scholarship. Where historical records are silent, fragmentary, or contradictory, the platform explicitly displays an **Epistemic Uncertainty Badge** (`traditional_account`, `academic_interpretation`, or `evidence_gap`) rather than inventing artificial consensus.

---

## 2. Verification Audit for the 10 Primary Sources

| Source Code | Work Title & Authorship | Archival Category | Authority & Scope | Verification Status |
|---|---|---|---|:---:|
| `SRC-ARCH-DNTL` | *Đại Nam Thực Lục* (Quốc Sử Quán triều Nguyễn, 1844–1909) | Imperial Dynastic Chronicle | Official court chronicle recording daily imperial edicts, personnel appointments, and state ceremonies (560 volumes). | **EXPERT VERIFIED** |
| `SRC-ARCH-HDSL` | *Khâm Định Đại Nam Hội Điển Sự Lệ* (Nội các triều Nguyễn, 1851) | Imperial Administrative Compendium | Official statutory code and ministry regulations; books on Ministry of Public Works (*Công bộ*) record exact building dimensions and metallurgy allocations. | **EXPERT VERIFIED** |
| `SRC-ARCH-DNTC` | *Đại Nam Nhất Thống Chí* (Quốc Sử Quán triều Nguyễn, 1882) | Imperial Geography & Topography | Official gazetteer describing provinces, mountains, rivers, ancient monuments, pagodas, and craft village specialties. | **EXPERT VERIFIED** |
| `SRC-ARCH-DKDC` | *Đồng Khánh Địa Dư Chí* (Nội các triều Nguyễn, 1886–1888) | Imperial Topographical Survey | Administrative census and illustrated village maps documenting crafts, taxation, and river trade in Thừa Thiên府. | **EXPERT VERIFIED** |
| `SRC-UN-WHC678` | *Complex of Hué Monuments* (UNESCO World Heritage Inscription, 1993) | International Heritage Inscription | Official UNESCO demarcation of the 14 property components (Criteria iii, iv). | **EXPERT VERIFIED** |
| `SRC-ICH-NN00074` | *Nhã Nhạc, Vietnamese Court Music* (UNESCO Representative List, 2003/2008) | Intangible Cultural Heritage | Inscription dossier documenting royal court music repertoire, instrumentation (*Đại nhạc*, *Tiểu nhạc*), and rituals. | **EXPERT VERIFIED** |
| `SRC-MOWCAP-CD` | *Cửu Đỉnh - Hoàng cung Huế* (UNESCO Memory of the World, 2024) | Documentary Heritage Register | UNESCO dossier documenting the 162 bronze relief motifs as a visual encyclopedia of 19th-century Vietnam. | **EXPERT VERIFIED** |
| `SRC-SCHOL-BAVH` | *Bulletin des Amis du Vieux Hué* (Léopold Cadière et al., 1914–1944) | Peer-Reviewed Scholarly Journal | 30 volumes of architectural surveys, epigraphy, and cultural ethnography of royal and folk Huế. | **EXPERT VERIFIED** |
| `SRC-SCHOL-PTA` | *Kiến trúc Cố đô Huế* & *Quần thể di tích Huế* (Phan Thuận An, 1995/2000) | Scholarly Monograph | Definitive architectural and historical surveys of the Citadel, palaces, and royal tombs by senior Huế heritage researchers. | **EXPERT VERIFIED** |
| `SRC-SCHOL-TDS` | *Pháp Lam Huế* (TS. Trần Đức Anh Sơn, 2004) | Scholarly Monograph | Scientific study of imperial vitreous enamel technology, historical texts, chemical compositions, and kiln excavations. | **EXPERT VERIFIED** |

---

## 3. Epistemic Uncertainty Register (Documented Historical Gaps)

| Gap ID | Heritage Domain / Topic | Nature of Historical Uncertainty | Platform Rule & Representation |
|---|---|---|---|
| `GAP-01` | **Individual Foundry Masters of 1835 Cửu Đỉnh** | The imperial annals (*Đại Nam Thực Lục*, *Hội Điển Sự Lệ*) record the total bronze allocation, dates, and ministry supervisors, but **do not name individual foundry craftsmen** from Phường Đúc who sculpted the reverse wax motifs. | The platform explicitly disclaims individual attribution: *"Tư liệu triều Nguyễn ghi nhận công lao của đội ngũ thợ đúc Phường Đúc dưới sự chỉ đạo của Công bộ, nhưng không ghi danh tính từng nghệ nhân cụ thể."* |
| `GAP-02` | **Oral Transmission in Thanh Tiên Paper Flowers** | The 300-year history of Thanh Tiên paper flowers is preserved through oral family genealogy rather than official imperial decrees. | Tagged as `traditional_account`. The platform states: *"Lịch sử 300 năm được truyền tụng qua gia phả các dòng họ làng Thanh Tiên, không có sắc phong triều đình riêng cho làng nghề."* |
| `GAP-03` | **Origins of Cham Musical Transmission in Nhã Nhạc** | While scholars agree that Central Vietnamese folk music and certain court modes (*Nam ai*, *Nam bình*) assimilated ancient Cham musical scales, the exact historical transmission mechanism remains academically debated. | Tagged as `academic_interpretation`. Explicitly notes: *"Giả thuyết học thuật về sự giao thoa thang âm Chăm; chưa có văn bản chính sử khẳng định con đường tiếp nhận cụ thể."* |
| `GAP-04` | **Pháp Lam Bureau Disruption (1885)** | The imperial Enamel Bureau (*Pháp lam tượng cục*) ceased operations after the 1885 fall of the capital (*Biến cố kinh thành Huế*). The exact fate of the master craftsmen and workshop records is unrecorded. | Explicitly labeled as a historical discontinuity (*giai đoạn đứt gãy lịch sử*), contrasting imperial history with 21st-century scientific reconstruction. |

---

## 4. Cross-Cultural Comparison Guidelines

To ensure cultural dignity and avoid superficial or false equivalences:

1. **Huế Royal Enamel (*Pháp Lam*) vs European Cloisonné / Canton Enamel:**
   - *Nuance:* While imperial decrees cite foreign inspirations, Huế artisans adapted French and Cantonese techniques to withstand tropical humidity by developing unique copper-alloy bases and specific silicate fluxes.
   - *Rule:* Always label comparisons as *"Điểm tương đồng kỹ thuật — không phải sự đồng nhất lịch sử."* (Technical similarity — not historical equivalence).
2. **Khải Định Mosaic (*Khảm sành sứ*) vs Roman/Byzantine Mosaic:**
   - *Nuance:* Roman mosaic utilized pre-formed stone/glass *tesserae*; Khải Định mosaic utilized reclaimed, sheared antique porcelain plates and bottles embedded in resin mortar.
   - *Rule:* Highlight the transformative folk recycling ethos rather than equating it to classical mosaic traditions.
3. **Imperial Relics vs Modern Artisan Workshops (Artisan Dignity Invariant):**
   - *Rule:* Contemporary artisans are independent creators continuing heritage lineages. **Never** describe a living workshop as an "imperial factory" or imply modern artisans manufactured 19th-century antiquities.
