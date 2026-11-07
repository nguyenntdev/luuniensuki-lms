# LƯU NIÊN — The Living Heritage Platform
## RBPC 2026: MARKET CLAIMS EVIDENCE REGISTER & TRUTH TIER AUDIT

**Document ID:** `DOC-RBPC-EVID-001`  
**Version:** 1.0.0 Final  
**Date:** 05 November 2026  
**Auditor / Role:** W11-A08 (Ticket V5-T118)  
**Classification:** NEW_PRODUCT_FEATURE / GOVERNANCE  
**Status:** APPROVED FOR RBPC DOSSIER & PITCH REVIEWS  
**Controlling Documents:** `DOC-RBPC-BP-001` (`BUSINESS_PLAN_DRAFT.md`), `DOC-RBPC-VAL-001` (`VALIDATION.md`), `DOC-RBPC-METRICS-001` (`CUSTOMER_VALUE_METRICS.md`), `DOC-RBPC-FIN-001` (`FINANCIAL_ASSUMPTIONS.md`)

---

## 1. Executive Governance & Truth Tier Framework

To maintain the highest level of academic, ethical, and commercial integrity for the **RMIT Business Plan Competition (RBPC) 2026**, every qualitative and quantitative market assertion in the LƯU NIÊN business plan dossier is categorized across three immutable **Truth Tiers**:

1. **`OBSERVED`:**
   - Factually verified operational actuals, legally executed contracts, signed corporate sponsorship agreements, or empirical government census data.
   - Example: 202,360,638 VND corporate in-kind compute subsidy from BNIX & Phổ Tuệ; 4.05M official visitor arrivals reported by Thừa Thiên Huế Department of Tourism (2024).

2. **`HYPOTHESIS`:**
   - Grounded behavioral models, structured interview survey findings, or usability test results that represent plausible mechanisms but await long-term cohort validation.
   - Example: 15.0% inquiry conversion rate from engaged readers (>60s); ~4.5 hours/week operational time saved by workshop managers.

3. **`FORECAST`:**
   - Forward-looking financial and market sizing estimates (TAM, SAM, SOM) modeled for strategic planning and scale analysis.
   - Example: 28.5 Billion VND TAM Gross Booking Value; Year 1 SOM target of 1,100 completed workshop experiences across 5 partner studios.

---

## 2. Negative Abuse Invariant & Anti-Deception Guardrail

> **Non-Negotiable Rule:**
> **Unverified external benchmarks or TAM/SAM/SOM forward projections CANNOT be displayed as actual LƯU NIÊN operational KPIs.**
> Operational KPIs in platform dashboards (such as `/api/v1/rbpc/impact`) and pitch investor summaries must be backed strictly by `OBSERVED` actual transactions (e.g., closed inquiries and settled payout records). If a database has 0 closed inquiries, the operational metric displays strictly `0`, never a forecast number like 1,100 or 6,000.

---

## 3. Master Market Claims Evidence Register (15 Claims)

| Claim ID | Truth Tier | Category | Metric / Statement | Date Recorded | Methodology | Sample Size | Source Ref | Operational KPI? |
|---|---|---|---|---|---|---|---|---|
| **MC-001** | `OBSERVED` | PROBLEM_URGENCY | Over 4.0 million travelers visit Huế annually (1.2M+ international). (*4,050,000 total visitors*) | 2025-01-15 | Official provincial tourism statistics bulletin | N=4,050,000 annual arrivals | `DOC-RBPC-FIN-001` / Dept Tourism 2024 | ❌ NO (Macro Census) |
| **MC-002** | `HYPOTHESIS` | PROBLEM_URGENCY | 78% of international visitors report difficulty understanding authentic historical context from brief plaques. (*78.0% difficulty*) | 2026-10-16 | Field discovery intercepts & bilingual survey sampling in Citadel | N=50 international cultural FITs | `DOC-RBPC-VAL-001` (EVID-USER-001) | ❌ NO (Survey Hypothesis) |
| **MC-003** | `OBSERVED` | COMPETITIVE_BENCHMARK | Mass OTAs (Klook, Viator) charge 25%–30% commissions on cultural tours. (*25.0% - 30.0% take rate*) | 2026-10-16 | Partner merchant contract review & competitor supplier terms audit | N=5 local operator interviews & published OTA terms | `DOC-RBPC-VAL-001` (EVID-PARTNER-001) | ❌ NO (Competitor Market Rate) |
| **MC-004** | `OBSERVED` | OPERATIONAL_EFFICIENCY | Traditional workshop operators spend 5.8 hours/week on manual messaging, translation, and scheduling. (*5.8 hrs/wk burden*) | 2026-10-16 | Time-motion study and semi-structured operator field interviews | N=5 independent craft studios in Huế | `DOC-RBPC-METRICS-001` §2.1 | ❌ NO (Pre-Platform Baseline) |
| **MC-005** | `HYPOTHESIS` | OPERATIONAL_EFFICIENCY | LƯU NIÊN automates the top 80% of inbound friction, saving ~4.5 hours per week per studio manager. (*4.5 hrs/wk saved*) | 2026-10-18 | Pilot intake workflow simulation & operator task timing audit | N=5 workshop operators | `DOC-RBPC-METRICS-001` §2.1.2 | ❌ NO (Pilot Hypothesis) |
| **MC-006** | `HYPOTHESIS` | USER_BEHAVIOR | ~20% of unique story readers engage deeply (>60s) with historical annals, 3D artifacts, or AI tutor. (*20.0% engagement*) | 2026-10-17 | Web analytics dwell-time instrumentation & interactive session sampling | N=1,500 monthly simulated cohort | `DOC-RBPC-FIN-001` §3.3 | ❌ NO (Funnel Parameter) |
| **MC-007** | `HYPOTHESIS` | USER_BEHAVIOR | 15% of deeply engaged story readers submit an authentic workshop availability inquiry. (*15.0% conversion rate*) | 2026-10-18 | Controlled UX inquiry form usability trials and click-through tracking | N=120 prospective traveler sessions | `DOC-RBPC-METRICS-001` §2.2.2 | ❌ NO (Conversion Hypothesis) |
| **MC-008** | `OBSERVED` | UNIT_ECONOMICS | LƯU NIÊN charges a 10% performance fee strictly on completed experiences (0 VND fixed monthly fees). (*10.0% platform fee*) | 2026-10-16 | Executed partner agreements and pricing policy formulation | N=5 pilot artisan partner contracts | `DOC-RBPC-FIN-001` §1.2 / `DOC-RBPC-BP-001` | ✅ YES (Platform Policy) |
| **MC-009** | `OBSERVED` | UNIT_ECONOMICS | 90% of workshop booking revenue is retained directly by the craft family (e.g. 630k out of 700k VND). (*90.0% artisan share*) | 2026-10-16 | Bilingual partner consent agreements and payout ledger policy | N=5 artisan studios | `DOC-RBPC-FIN-001` §1.2 / UN SDG 8 Policy | ✅ YES (Platform Governance) |
| **MC-010** | `OBSERVED` | SPONSORSHIP_RUNWAY | Secured exactly 202,360,638 VND in documented corporate in-kind sponsorship (BNIX + Phổ Tuệ). (*202,360,638 VND non-cash*) | 2026-10-17 | Signed corporate partnership contract reconciliation & audit | N=2 corporate sponsorship agreements | `BASELINE.md` §5 / `DOC-RBPC-FIN-001` | ✅ YES (Audited Contract Asset) |
| **MC-011** | `HYPOTHESIS` | UNIT_ECONOMICS | At full commercial market hosting rates, LƯU NIÊN achieves commercial breakeven at 2.9 (3) bookings/month across Huế. (*2.9 bookings/mo breakeven*) | 2026-10-17 | Dual P&L financial modeling under shadow replacement cost | Analytical cost modeling (70k commission/booking) | `DOC-RBPC-FIN-001` §4.4 | ❌ NO (Model Calculation) |
| **MC-012** | `FORECAST` | MARKET_SIZING | Total Addressable Market (TAM) for cultural tourist participatory craft experiences across Thừa Thiên Huế is 28.5B VND (~$1.08M USD) GBV. (*28.5B VND GMV*) | 2026-10-18 | Bottom-up sizing from official 4.05M visitor arrivals & 14.8% cultural segment | Province-wide macro projection | `DOC-RBPC-FIN-001` §2.3.1 | ❌ NO (Macro Forecast) |
| **MC-013** | `FORECAST` | MARKET_SIZING | Serviceable Addressable Market (SAM) across ~50–60 master craft studios in historic quarters is 5.7B VND GMV (570M platform rev). (*5.7B VND GMV*) | 2026-10-18 | Bottom-up guild inventory filtering (Kim Long, Phường Đúc, Thủy Biều) | N=55 traditional master studios | `DOC-RBPC-FIN-001` §2.3.2 | ❌ NO (Segment Forecast) |
| **MC-014** | `FORECAST` | MARKET_SIZING | Serviceable Obtainable Market (SOM Year 1) targets 5 active partner workshops, 1,100 completed experiences, and 570M VND GMV. (*1,100 experiences / 570M VND*) | 2026-10-18 | Operational capacity constraint modeling for 3-4 student founder team | N=5 workshops over 10 operational months | `DOC-RBPC-FIN-001` §2.3.3 | ❌ NO (Forward Target) |
| **MC-015** | `OBSERVED` | OPERATIONAL_EFFICIENCY | Operational actuals display strictly verified closed inquiries and approved settlements; empty DB returns 0. (*0 baseline to N closed*) | 2026-11-05 | Strict database aggregation (state == 'closed', status == 'settled') | Real PostgreSQL inquiry event records | `backend/routers/rbpc.py` (V5-T110) | ✅ YES (Database Actual) |

---

## 4. Pitch Review Export & Verification Utility

For pitch evaluations, the register can be programmatically verified and exported via:
- Python service: `backend/services/rbpc_market_claims.py` (`MarketClaimsEvidenceRegister`)
- Command line / JSON export: `python -c "from backend.services.rbpc_market_claims import default_market_claims_register; print(default_market_claims_register.export_json())"`
- Markdown export: `python -c "from backend.services.rbpc_market_claims import default_market_claims_register; print(default_market_claims_register.export_markdown_table())"`

---
**RBPC 2026 Verification Stamp:** All claims checked against truth tier constraints and negative abuse rules.
