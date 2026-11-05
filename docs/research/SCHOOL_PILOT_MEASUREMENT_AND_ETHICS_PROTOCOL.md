# School Pilot Measurement & Ethics Research Protocol (V5-T100 / Wave W09)

> **Status:** APPROVED & AUTHORITATIVE  
> **Classification:** Production Governance & Research Ethics  
> **Regulatory Basis:** Vietnamese Law on Education (2019), Decree No. 13/2023/ND-CP on Personal Data Protection, UNESCO Recommendation on the Ethics of AI in Education.  
> **Target Audience:** School Principals, Lead Educators, Independent Assessors, IRB Boards, EdTech Researchers.

---

## 1. Executive Summary & Purpose

The LƯU NIÊN School Pilot Measurement & Ethics Protocol establishes an institutional research and assessment framework for deploying digital heritage learning systems (Cửu Đỉnh / Imperial Citadel of Huế) into secondary and upper-secondary classrooms.

The protocol enforces five foundational integrity pillars:
1. **Institutional Ethics Governance (IRB):** All empirical pilot assessments are governed by an approved, active Institutional Review Board (IRB) research protocol.
2. **Guardian Informed Consent Verification:** Prior verified parental/guardian consent is mandatory for any minor participant (<18 years old) prior to collecting research data or conducting empirical assessments.
3. **Teacher Workload Assessment & Burnout Defense:** Continuous quantitative tracking of educator workload (preparation, direct delivery, rubric grading duration, and NASA-TLX cognitive load index) with strict safety thresholds to prevent burnout.
4. **Student Data Retention & Purging Policy:** Minimization of student data retention (standard 365-day academic research cycle) with automated audit and PII purging to `[RETENTION_PURGED]` compliant with Decree 13/2023/ND-CP.
5. **Dual-Assessor Rubric Calibration:** Server-enforced objective multi-criteria rubric evaluation (S1–S4) conducted by independent educators, with inter-rater reliability calculation and divergence flags (>15% discrepancy).
6. **Negative Abuse Firewalled Rule:** Subjective sentiment, self-reported feelings, or satisfaction ratings (including the 1,502 survey) CANNOT be claimed or labeled as evidence of learning improvement. Valid learning improvement evidence strictly requires objective paired pre/post source inquiry assessments evaluated by independent calibrated raters.

---

## 2. Institutional Review Board (IRB) Protocol Governance

### 2.1 Governance Structure
Every school pilot must register under an accredited research institution or university Institutional Review Board (e.g., Hue Heritage Research Ethics Board, VNU University of Education IRB).

```
   ┌───────────────┐
   │     Draft     │ (Initial protocol design & curriculum alignment)
   └───────┬───────┘
           │ Submit for Review
           ▼
   ┌───────────────┐
   │   Submitted   │ (Institutional Review Board scrutiny & safety checks)
   └───────┬───────┘
           │ Institutional Approval
           ▼
   ┌───────────────┐        Expiry / Violation       ┌───────────────┐
   │   Approved    │ ───────────────────────────────► │    Expired    │
   └───────┬───────┘                                  └───────────────┘
           │ Immediate Safety Revocation
           ▼
   ┌───────────────┐
   │    Revoked    │ (Data collection immediately halted; access blocked)
   └───────────────┘
```

### 2.2 Protocol Lifecycle Rules
- **Approved Status Required:** Only protocols in `approved` status with an unexpired `valid_until` timestamp can register new inquiry assessments or accept student submissions.
- **Immediate Suspension:** If a protocol transitions to `revoked` or `expired`, backend routers immediately reject new assessment authoring (`HTTP 422 ETHICS_PROTOCOL_REQUIRED`) and student submissions.
- **Immutable Audit Trail:** All protocol approval timestamps, approving committee members, and retention parameters are immutably logged in `history_ethics_protocols`.

---

## 3. Guardian Informed Consent Verification Protocol

### 3.1 Regulatory Compliance (Decree 13/2023/ND-CP)
Under Article 20 of Decree 13/2023/ND-CP, the processing of personal data of children (under 16) and adolescents (under 18) requires explicit consent from both the minor (if aged 7 or older) and their parent or legal guardian.

### 3.2 Consent Workflow
1. **Consent Registration:** Prior to pilot commencement, parents/guardians receive the *LƯU NIÊN Heritage Inquiry Information Sheet* describing the 3D exploration tasks, source inquiry assessments, and data handling procedures.
2. **Verification Methods:**
   - `digital_signature`: Authenticated digital signature or verified portal confirmation.
   - `sms_otp`: Two-factor SMS confirmation to the guardian's verified phone number.
   - `paper_signed`: Physical signed consent form counter-signed by the classroom teacher.
   - `school_roster`: Administrative institutional consent roster attested by the school principal.
3. **Consent States:**
   - `pending`: Record created, awaiting verification. Minor submissions are blocked (`HTTP 403 GUARDIAN_CONSENT_REQUIRED`).
   - `verified`: Consent authenticated and timestamped by teacher or administrator. Participant is eligible for assessment and research inclusion.
   - `withdrawn`: Guardian or student exercises the right to withdraw. Submissions are immediately halted (`HTTP 403 GUARDIAN_CONSENT_WITHDRAWN`), and student records are excluded from research cohort metrics.

---

## 4. Teacher Workload Assessment Framework

### 4.1 Motivation & Ethical Duty of Care
Pilot interventions often fail due to hidden teacher burden: excessive rubric grading time, unfamiliar 3D tools, and administrative overhead. The LƯU NIÊN protocol operationalizes an active **Workload Safety Monitor** to protect educators.

### 4.2 Workload Dimensions & Metrics
| Dimension | Description | Target Metric | Excessive Threshold |
|---|---|---|---|
| **Preparation Time** | Lesson customization, 3D hotspot inspection, source review | 15–30 min/lesson | > 60 min/lesson |
| **Instruction Time** | Direct facilitation of historical inquiry | 45 min standard | > 90 min/session |
| **Rubric Grading Time** | Evaluating S1–S4 criteria per student submission | 5–10 min/student | > 15 min/student |
| **Cognitive Load Index** | NASA-TLX adapted index (Mental Demand, Effort, Frustration, 0–100) | Index < 60 | Index > 70 |

### 4.3 Automated Classification & Alerting
- **`optimal`**: Grading <= 8 min/student, TLX < 40, administrative time <= 60 min/week.
- **`acceptable`**: Grading 8–15 min/student, TLX 40–70, administrative time <= 120 min/week.
- **`excessive`**: Grading > 15 min/student OR TLX > 70 OR weekly overhead > 120 min. Triggers automated warning notifications, recommendation for secondary rater deployment, and inquiry task simplification.

---

## 5. Student Data Retention & Scheduled Purging Policy

### 5.1 Data Minimization
Student assessment data is collected strictly for validating learning effectiveness. No unnecessary demographic, behavioral, or biometric information is captured.

### 5.2 Retention Schedule
- **Active Research Window:** Retained for the duration of the ethics protocol (standard: 365 calendar days).
- **Automated Expiration Audit:** Backend jobs query `history_learning_outcome_submissions` and `history_subjective_surveys` where `submitted_at + INTERVAL 'data_retention_days' < NOW()`.
- **Permanent Purge Execution:**
  * Student submission responses are overwritten with `{"_purged": True, "policy": "Decree_13_2023_ND_CP"}`.
  * Citations and free-text notes are cleared to empty lists.
  * Evaluation feedback and assessor notes are redacted to `[RETENTION_PURGED]`.
  * Survey likert responses and comments are scrubbed.
  * De-identified aggregate statistics (cohort effect size, mean normalized gain) are preserved for scientific reporting without any linkable student keys.

---

## 6. Dual-Assessor Rubric Calibration Protocol

### 6.1 Assessment Instrument: 4-Criteria Inquiry Rubric (S1–S4)
Student responses to primary source inquiry tasks are evaluated against four standardized criteria (0–25 points each, total 100 points):
1. **`S1_SPATIAL` (Spatial & Geographic Context):** Accurate identification of coordinates, provinces, mountains, rivers engraved on Cửu Đỉnh (e.g., Biển Đông on Cao Đỉnh, Sông Hương on Nhân Đỉnh).
2. **`S2_TEMPORAL` (Chronological Context):** Accurate contextualization within the 1835–1837 Minh Mạng casting timeline and historical sequence of the Nguyễn Dynasty.
3. **`S3_EVIDENCE` (Primary Source Usage):** Proper citation and interpretation of *Khâm Định Đại Nam Hội Điển Sự Lệ*, *Đại Nam Thực Lục Chính Biên*, and authentic rubbing inscriptions.
4. **`S4_ARGUMENT` (Historical Argumentation):** Coherent historical synthesis regarding sovereignty, statehood, and cultural symbolism.

### 6.2 Assessor Independence & Anti-Self-Grading
- **Strict Independence:** All evaluations must be conducted by certified educators or researchers (`is_independent=True`).
- **Student Self-Grading Forbidden:** Any attempt by a student to grade their own submission is rejected with `HTTP 403 INDEPENDENT_ASSESSOR_REQUIRED`.

### 6.3 Inter-Rater Reliability & Calibration Algorithm
When two independent evaluators grade the same student submission:
$$\text{Score Difference} = |Score_A - Score_B|$$
$$\text{Divergence Percentage} = \frac{|Score_A - Score_B|}{\text{Max Score}}$$
$$\text{Inter-Rater Agreement} = 1.0 - \text{Divergence Percentage}$$

- **`calibrated` Status:** Divergence $\le 15\%$ (Agreement $\ge 85\%$). The authoritative consensus score is the arithmetic mean:
  $$\text{Consensus Score} = \frac{Score_A + Score_B}{2}$$
- **`divergent_requires_review` Status:** Divergence $> 15\%$. Triggers an adjudication flag requiring a third senior educator or consensus conference. No automatic consensus score is awarded until reconciled.

---

## 7. Negative Abuse Rule: Isolation of Subjective Sentiment

### 7.1 Methodological Firewall
In EdTech research, a common unethical practice is presenting student feelings or satisfaction ratings as evidence of learning. LƯU NIÊN enforces an absolute technical firewall:

| Instrument Type | Purpose | Permitted Claim | Prohibited Claim |
|---|---|---|---|
| **Subjective Survey** (e.g. Likert 1–5, 1,502 survey) | Measure perceived user experience, engagement, emotional response | "92% of students felt engaged by 3D models" | ❌ "The app increased student history learning by 40%" |
| **Objective Rubric Assessment** (Paired Pre/Post S1–S4) | Measure actual historical inquiry mastery & evidence evaluation | "Normalized learning gain $g = 0.52$; Cohen's $d = 1.34$" | N/A (Standard empirical evidence) |

### 7.2 Backend Invariant Enforcement
Any API call attempting to:
1. Pass survey responses into `compute_causal_learning_outcome`, OR
2. Submit a claim labeling subjective sentiment as `learning_improvement`, OR
3. Alter student mastery levels from survey data
is **immediately rejected with HTTP 422** (`CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY` / `SENTIMENT_NOT_LEARNING_EVIDENCE`).

---

## 8. Summary of API Endpoints

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/api/v1/history/learning-outcomes/ethics-protocols` | `POST` | Staff/Admin | Register new IRB ethics protocol |
| `/api/v1/history/learning-outcomes/ethics-protocols/{id}/consent` | `POST` | User/Staff | Register guardian informed consent |
| `/api/v1/history/learning-outcomes/ethics-protocols/{id}/consent/{cid}/verify` | `POST` | Staff/Admin | Verify guardian informed consent |
| `/api/v1/history/learning-outcomes/ethics-protocols/{id}/consent/{cid}/withdraw` | `POST` | User/Staff | Withdraw guardian consent (halts research) |
| `/api/v1/history/learning-outcomes/ethics-protocols/{id}/consent/{uid}/status` | `GET` | User/Staff | Query consent status for student |
| `/api/v1/history/learning-outcomes/teacher-workload` | `POST` | Teacher/Staff | Log educator workload and NASA-TLX index |
| `/api/v1/history/learning-outcomes/teacher-workload/summary` | `GET` | Teacher/Staff | Workload summary, burnout risk, alerts |
| `/api/v1/history/learning-outcomes/rubric-calibration` | `POST` | Staff/Admin | Dual-assessor calibration & divergence audit |
| `/api/v1/history/learning-outcomes/retention/audit` | `POST` | Admin | Audit expired records past retention limit |
| `/api/v1/history/learning-outcomes/retention/purge` | `POST` | Admin | Scrub PII from expired pilot records |
| `/api/v1/history/learning-outcomes/validate-learning-claim` | `POST` | Staff/Admin | Anti-abuse validation blocking sentiment claims |

---
*Signed by LƯU NIÊN Research Ethics Committee & Product Engineering.*
