# LƯU NIÊN — Post-Launch 30/60/90-Day Operational & Strategic Plan

**Document ID:** `PLAN-POST-LAUNCH-30-60-90`  
**Version:** 1.0.0 (Immutable Release)  
**Ticket:** `V5-T130` (Wave W12, Slot A10)  
**Role:** W12-A10  
**Classification:** `PRODUCTION_COMPLETION`  
**Date:** 2026-11-07  
**Status:** APPROVED & LOCKED  

---

## 1. Executive Summary & Objective

This document formalizes the post-launch operational, review, and expansion roadmap for **LƯU NIÊN (Cửu Đỉnh Heritage LMS & Marketplace)** across the initial 90-day post-launch window (Days 1–30, Days 31–60, Days 61–90).

The plan enforces rigorous engineering, pedagogical, and commercial governance:
1. **Weekly Quality, Retention, and Partner Support Cadence**: Cross-functional review every Monday morning evaluating telemetry, crash reports, customer SLA compliance, and artisan feedback.
2. **Hypothesis-Driven Feature Prioritization**: New features are scheduled strictly according to validated empirical evidence (observed user retention, rubric completion rates, verified booking transaction data), not speculative pitches.
3. **Negative Abuse Guardrail Invariant**:
   > **CRITICAL INVARIANT:** No feature scale-up, infrastructure expansion, or capital investment shall be authorized based solely on ungrounded demo applause, exhibition compliments, pitch deck sentiment, or subjective verbal praise. Every proposed feature scale-up must cite audited quantitative metrics from the Evidence Room / Analytics Ledger.

---

## 2. 30 / 60 / 90-Day Milestone Architecture

```
+-------------------------------------------------------------------------------------------------------+
|                                    LƯU NIÊN 90-DAY POST-LAUNCH HORIZON                                |
+------------------------------------+----------------------------------+-------------------------------+
| DAYS 1 - 30: STABILIZATION & TRUST | DAYS 31 - 60: DEPTH & RETENTION  | DAYS 61 - 90: EXPANSION & B2B |
| * Zero-defect runtime telemetry    | * FSRS spaced retrieval tuning   | * Multi-school pilot rollout  |
| * 24h partner SLA enforcement      | * Cohort Day-7 / Day-14 retention| * Artisan co-creation studio  |
| * 162 Relics source lock audit     | * Offline rubbing sync reliability| * Self-serve tour agency API  |
| * In-kind sponsorship burn monitor | * Socratic AI tutor rubric check | * Production unit economics QA|
+------------------------------------+----------------------------------+-------------------------------+
```

### 2.1 Phase 1: Days 1–30 — Operational Stabilization & Trust Verification
- **Primary Focus**: Platform reliability, bug triage, inquiry delivery SLAs, and strict source integrity.
- **Key Milestones**:
  - `M30-01`: 99.9% uptime across Axum gateway and Python backend; zero unhandled 5xx errors on critical inquiry submissions.
  - `M30-02`: 100% adherence to the partner 24h inquiry response SLA; notification outbox dead-letter queues monitored continuously.
  - `M30-03`: Zero fabricated or unreviewed claim leakage in AI tutor RAG pipelines; all 162 relics locked to primary archival citations.
  - `M30-04`: Verification of initial real visitor inquiries (Target: >= 50 real inquiries, zero synthetic production records).
  - `M30-05`: Strict accounting of in-kind infrastructure sponsorship burn (VPS, AI tokens, domain renewals) against the 202,360,638 VND budget cap.

### 2.2 Phase 2: Days 31–60 — Learning Depth & Cohort Retention
- **Primary Focus**: Student learning progression, teacher rubric engagement, and mobile offline resilience.
- **Key Milestones**:
  - `M60-01`: Spaced repetition (FSRS-5) learning retention evaluation across student cohorts; audit against burst click abuse.
  - `M60-02`: Partner feedback integration from Hue bronze-casting and traditional paper artisans; review of booking settlement turnaround (< 48h).
  - `M60-03`: Mobile client performance check: ensure thermal and memory budgets (< 200MB RAM, < 60fps stable) during 3D model inspection.
  - `M60-04`: Teacher grading workflow audit: ensure 100% of rubric grading scores strictly follow the 0–3 criteria without IDOR exposure.
  - `M60-05`: K-anonymity privacy check: guarantee any displayed learning analytics suppress cohorts where $n < 5$.

### 2.3 Phase 3: Days 61–90 — Sustainable Expansion & Value Scaling
- **Primary Focus**: B2B school pilot onboarding, revenue reconciliation, and evidence-backed feature roadmap commits.
- **Key Milestones**:
  - `M90-01`: Onboarding of 3 verified pilot high schools (Grade 10–12 history curriculum alignment with 2018 General Education Program).
  - `M90-02`: Revenue reconciliation: audit of actual GMV transactions and 90% direct artisan payout distribution.
  - `M90-03`: Execution of formal research evaluation protocols (LN-01 through LN-10) using empirical student cohort data.
  - `M90-04`: Feature prioritization committee meeting: committing Phase 4 roadmap tickets strictly validated by observed metrics.
  - `M90-05`: Post-launch audited evidence room update with full 90-day empirical results for investors and heritage partners.

---

## 3. Weekly Review Cadence (Quality, Retention, Partner Support)

Every Monday at 09:00 ICT, the engineering and operational leads conduct a structured 45-minute post-launch review spanning three non-negotiable operational pillars:

### 3.1 Pillar 1: Platform Quality & Reliability Review
- **Telemetry Sources**: Prometheus / AlertRouter logs, Sentry issue reports, and database slow-query logs.
- **Key Indicators Tracked**:
  - API p95 response latency (SLA: <= 300ms for read requests).
  - WebGL context loss recovery rate (> 99.5%).
  - Zero PII leaks in structured logs (validated by recursive PII redaction filters).
  - Failed transaction rate on `/api/v1/rbpc/inquiries` (must be 0.00%).

### 3.2 Pillar 2: Cohort Engagement & Learning Retention Review
- **Telemetry Sources**: Analytics event bus (`backend/services/analytics.py`), FSRS review queues, and classroom progress records.
- **Key Indicators Tracked**:
  - Day-1, Day-7, and Day-28 active student retention.
  - Lesson completion rate (`hidden -> discovered -> learned -> mastered`).
  - Cognitive dwell time verification (flagging brute-force clicking faster than minimum reading threshold).
  - Diagnostic feedback accuracy on historical misconception detection.

### 3.3 Pillar 3: Partner Support & Marketplace Health Review
- **Telemetry Sources**: RBPC inquiry ledger, partner notification outbox, and settlement ledger.
- **Key Indicators Tracked**:
  - Partner inquiry response time (target: < 12h, mandatory SLA: < 24h).
  - SLA breach count (immediate escalation if > 0).
  - Settlement disbursement timeline (target: < 48 hours from experience completion).
  - Artisan satisfaction score and feedback submissions (processed via anonymized discovery feedback store).

---

## 4. Validated Value Hypotheses

The post-launch plan tracks 5 core business and pedagogical hypotheses, each paired with empirical metrics and pre-registered falsification triggers:

| Hypothesis ID | Title | Statement | Target Metric | Falsification Trigger | Truth Status |
|---------------|-------|-----------|---------------|-----------------------|--------------|
| `HYP-PL-01` | Socratic AI Retention | Students using hint-first AI guidance retain 25% more motif facts at Day-14 vs direct answer reveal. | Day-14 retention >= 65.0% | Day-14 retention < 45.0% | HYPOTHESIS |
| `HYP-PL-02` | Offline Rubbing Parity | Schools with bandwidth < 1 Mbps achieve identical rubric pass rates using printable monochrome rubbings. | Pass rate delta <= 5.0% | Pass rate delta > 12.0% | HYPOTHESIS |
| `HYP-PL-03` | Artisan Wage Uplift | Transparent 90% direct payout yields >= 4,200,000 VND monthly wage uplift for active craft masters. | Uplift >= 4,200,000 VND | Uplift < 2,000,000 VND | HYPOTHESIS |
| `HYP-PL-04` | Teacher Wizard Adoption | Pre-formatted 45-minute lesson wizard reduces lesson planning preparation time by >= 40%. | Prep time <= 25 mins | Prep time > 40 mins | HYPOTHESIS |
| `HYP-PL-05` | Verified Inquiry Conversion | Visitors who inspect 3D rubbing details convert to booking inquiries at >= 3x higher rate than text-only visitors. | Conversion ratio >= 3.0x | Conversion ratio < 1.5x | HYPOTHESIS |

---

## 5. Feature Prioritization Framework & Decision Matrix

To protect engineering resources and maintain pedagogical rigor, candidate features are evaluated through an objective, weighted RICE-grounded decision scoring engine:

$$\text{Priority Score} = \frac{\text{Reach} \times \text{Impact} \times \text{Confidence}}{\text{Effort}}$$

Where:
- **Reach**: Estimated active users affected per month ($1 - 10$).
- **Impact**: Pedagogical or transactional uplift ($1 - 5$).
- **Confidence**: Grounded empirical evidence score ($0.1 - 1.0$). **CRITICAL:** Speculative features or verbal feedback alone receive a maximum Confidence score of $0.2$, while observed metric proofs receive $\ge 0.8$.
- **Effort**: Engineering person-weeks ($1 - 8$).

### 5.1 Backlog Candidate Matrix

| Feature ID | Feature Name | Target Horizon | Reach (1-10) | Impact (1-5) | Confidence (0.1-1.0) | Effort (Weeks) | Priority Score | Status |
|------------|--------------|----------------|--------------|--------------|----------------------|----------------|----------------|--------|
| `FEAT-01` | Offline Sync Conflict Resolution v2 | Days 31–60 | 8 | 4 | 0.90 (Observed sync logs) | 2 | **14.40** | APPROVED_NEXT |
| `FEAT-02` | Teacher Rubric Batch Export (Excel/PDF) | Days 31–60 | 6 | 4 | 0.85 (School pilot demand) | 2 | **10.20** | APPROVED_NEXT |
| `FEAT-03` | Multi-Urn Comparative Lens (3D Split) | Days 61–90 | 7 | 3 | 0.80 (Curriculum mapping) | 3 | **5.60** | SCHEDULED |
| `FEAT-04` | Zalo Mini-App Inquiry Integration | Days 61–90 | 9 | 4 | 0.75 (Partner survey N=18) | 4 | **6.75** | SCHEDULED |
| `FEAT-05` | Speculative VR Metaverse Exhibition Room | Backlog | 3 | 2 | 0.10 (Verbal conference praise) | 8 | **0.08** | **REJECTED_UNGROUNDED** |
| `FEAT-06` | AI Voice Clone for Historical Monarchs | Backlog | 2 | 1 | 0.05 (Demo applause) | 6 | **0.02** | **REJECTED_UNGROUNDED** |

---

## 6. Negative Abuse Guardrail Invariant Enforcement

### 6.1 Formal Rule Definition
> **INVARIANT V5-T130-NEG:**
> Any request to scale up features, expand cloud capacity, allocate sprint tickets, or release capital based exclusively on:
> - Competition stage applause or audience voting;
> - Casual conference compliments or judge compliments;
> - Unsubstantiated verbal feedback from unverified third parties;
> - Raw vanity page views or clickthroughs without authenticated completion;
>
> **SHALL BE REJECTED AUTOMATICALLY BY THE PRIORITIZATION GATE.**
> Rejection code: `UNGROUNDED_DEMO_APPLAUSE_REJECTED`.
> Every scale-up proposal MUST reference an immutable Evidence Room Pointer (`EVID-*`), observed metric key, sample size $N \ge 10$, and verifiable audit trail.

### 6.2 Audit Procedures
1. **Intake Screening**: Feature requests must include an `evidence_ref` pointing to an active verified evidence pointer or analytics event.
2. **Confidence Normalization**: Any feature lacking transactional or telemetry validation is capped at $Confidence = 0.20$, rendering it mathematically non-viable against high-impact operational improvements.
3. **Audit Log Persistence**: All prioritization decisions, rejections, and reviews are written to the post-launch audit ledger with cryptographic timestamping.

---

## 7. Sign-Off & Verification Metadata

- **Review Lead:** Technical Architecture & Pedagogical Governance Board  
- **Approved Date:** 2026-11-07  
- **Artifact Reference:** `artifacts/implementation/W12/W12_A10_post_launch_plan.json`  
- **Test Suite:** `tests/v5/test_v5_t130.py`  
- **Hash Fingerprint (SHA-256):** Verified during test execution  
