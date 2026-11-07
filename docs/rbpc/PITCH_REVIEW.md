# LƯU NIÊN — The Living Heritage Platform
## RBPC 2026: INVESTOR DUE DILIGENCE & PITCH REVIEW EVALUATION PROTOCOL

**Document ID:** `DOC-RBPC-PITCH-REV-001`  
**Version:** 1.0.0 Final  
**Date:** 07 November 2026  
**Auditor / Role:** W11-A10 (Ticket V5-T120)  
**Classification:** NEW_PRODUCT_FEATURE / DUE DILIGENCE & GOVERNANCE  
**Status:** APPROVED FOR RMIT COMPETITION JURY & INVESTOR REVIEW  
**Controlling Documents:** `DOC-RBPC-EVID-ROOM-001` (`STARTUP_EVIDENCE_ROOM.md`), `DOC-RBPC-EXH-011` (`PITCH_EXHIBITS.md`), `DOC-RBPC-FIN-001` (`FINANCIAL_ASSUMPTIONS.md`)

---

## 1. Executive Protocol & RMIT Competition Evaluation Framework

In high-stakes academic and commercial startup competitions such as the **RMIT Business Plan Competition (RBPC) 2026**, juries require absolute evidentiary rigor. LƯU NIÊN implements an automated, cryptographic pitch claim auditing system that checks every quantitative slide statement against the **Startup Evidence Room** (`DOC-RBPC-EVID-ROOM-001`).

### The 5 RMIT Judging Criteria Alignment:
1. **Creativity & Innovation:** Provenance-backed 3D/AR WebGL models and delimited AI tutor pipelines (`EVID-PROD-001`, `EVID-PROD-002`).
2. **Feasibility & Viability:** Multi-scenario unit economics with 92.4% contribution margin and 2.9 bookings/month commercial breakeven (`EVID-FIN-001`, `EVID-FIN-003`).
3. **Corporate Partnerships:** Audited executed contracts for 202,360,638 VND in-kind infrastructure sponsorship (`EVID-FIN-002`, `EVID-LEG-002`).
4. **Social & Environmental Impacts:** UN SDG 8 (90% direct artisan share, 50% commission youth fund pledge) and UN SDG 4 (100% cited provenance) (`EVID-IMP-001`, `EVID-IMP-002`).
5. **Team Capability & Governance:** Multidisciplinary student founders (S1–S4) with 4-year vesting, 24-hour right of erasure SLA, and museum advisory oversight (`EVID-TEAM-001`, `EVID-LEG-001`, `EVID-TEAM-002`).

---

## 2. Negative Abuse Invariant & Anti-Inflation Guardrail

> **Mandatory Pitch Invariant (V5-T120):**
> **Every quantitative pitch claim must have an immutable evidence reference and status; ungrounded metrics are strictly flagged (`UNGROUNDED_FLAGGED`) and pitch readiness is marked `FLAGGED_UNREADY`.**

### Audit State Machine:
```
[ Pitch Claim Input ]
          │
          ├── Is Quantitative? ──────── No  ────► [ VERIFIED_OBSERVED ] (Qualitative Assertion)
          │            │
          │           Yes
          │            ▼
          ├── Evidence Pointer Provided? ─ No ──► [ UNGROUNDED_FLAGGED ] ──┐
          │            │                                                    │
          │           Yes                                                   │
          │            ▼                                                    │
          ├── Pointer Exists & Active? ─── No ──► [ UNGROUNDED_FLAGGED ] ──┤
          │            │                                                    │
          │           Yes                                                   │
          │            ▼                                                    │
          ├── Claim Matches Evidence? ──── No ──► [ UNGROUNDED_FLAGGED ] ──┤
          │            │                                                    │
          │           Yes                                                   │
          │            ▼                                                    │
          └── [ VERIFIED_OBSERVED / HYPOTHESIS / PROJECTION ]               │
                                                                            ▼
                       [ ALL Verified? ] ─── No ──────────────────► [ FLAGGED_UNREADY ]
                               │
                              Yes
                               ▼
                    [ APPROVED_FOR_PITCH ]
```

---

## 3. Comparative Case Studies: Pitch Due Diligence Walkthrough

### Case Study A: The Golden RBPC Pitch Deck (Approved)
- **Deck Title:** `Luu Nien - RBPC 2026 Finals Deck` (v1.0.0)
- **Claims Audited:** 5 Quantitative Assertions
  1. *202,360,638 VND secured in documented in-kind sponsorship from BNIX and Phổ Tuệ.* $\rightarrow$ Anchored to `EVID-FIN-002`, key `total_in_kind_sponsorship_vnd`. (`VERIFIED_OBSERVED`)
  2. *Intimate workshops priced at 700,000 VND with 90% retained directly by the craft family.* $\rightarrow$ Anchored to `EVID-FIN-001`, key `artisan_share_percent`. (`VERIFIED_OBSERVED`)
  3. *Unit contribution margin of 92.4% with commercial breakeven at 2.9 bookings/month across Huế.* $\rightarrow$ Anchored to `EVID-FIN-001`, key `base_contribution_margin_percent`. (`VERIFIED_OBSERVED`)
  4. *78% of international visitors report difficulty understanding authentic heritage context.* $\rightarrow$ Anchored to `EVID-CUST-001`, key `comprehension_difficulty_percent`. (`VERIFIED_HYPOTHESIS`)
  5. *TAM of 28.5 Billion VND in cultural workshop experiences across Thừa Thiên Huế.* $\rightarrow$ Anchored to `EVID-MKT-001`, key `tam_gbv_vnd`. (`VERIFIED_PROJECTION`)
- **Audit Result:** 5/5 Grounded Claims, 0 Ungrounded.
- **Pitch Readiness:** `APPROVED_FOR_PITCH` ✅

### Case Study B: The Unverified / Inflated Pitch Deck (Rejected)
- **Deck Title:** `Luu Nien - Draft Pitch Deck Unaudited` (v0.9.0)
- **Claims Audited:** 4 Quantitative Assertions
  1. *"We secured over 206M VND in verbal corporate sponsorship commitments."* $\rightarrow$ Contradicts `EVID-FIN-002` audited actual of 202,360,638 VND. **Flagged:** Rejected verbal approximation (-3,639,362 VND variance). (`UNGROUNDED_FLAGGED`)
  2. *"95% of all booking revenues go directly to the artisan."* $\rightarrow$ Contradicts `EVID-FIN-001` platform policy of 90%. (`UNGROUNDED_FLAGGED`)
  3. *"Platform has 5,000 active monthly booking subscribers."* $\rightarrow$ Missing evidence pointer reference entirely. (`UNGROUNDED_FLAGGED`)
  4. *"TAM is 28.5B VND."* $\rightarrow$ Anchored to `EVID-MKT-001`. (`VERIFIED_PROJECTION`)
- **Audit Result:** 1/4 Grounded Claims, 3 Ungrounded.
- **Pitch Readiness:** `FLAGGED_UNREADY` ❌

---

## 4. Programmatic Evaluation API & Usage

Developers and jury coordinators can submit pitch decks for audit via:

```bash
# Evaluate Pitch Deck
curl -X POST http://localhost:8000/api/v1/rbpc/pitch-review/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "pitch_deck_title": "Luu Nien RBPC 2026 Finals Deck",
    "deck_version": "1.0.0",
    "claims": [
      {
        "claim_text": "202,360,638 VND in documented in-kind corporate compute support",
        "domain": "finances",
        "evidence_pointer_id": "EVID-FIN-002",
        "metric_key": "total_in_kind_sponsorship_vnd",
        "claimed_value": 202360638,
        "is_quantitative": true,
        "truth_tier": "OBSERVED"
      }
    ]
  }'
```

---
**RBPC 2026 Verification Stamp:** Due diligence audit engine fully verified against `rbpc_pitch_reviews` table.
