# Institutional Ethics & Human Subjects Research Protocol for Educational Field Studies
## Protocol Code: `IRB-VN-2026-LN09`
**Title:** Empirical Evaluation of Immersive Heritage Learning Technologies, Primary Source Inquiry, and AI Scaffolding in Secondary & High School Classrooms and Museum Field Environments  
**Governing Institution:** Hue Educational & Heritage Research Ethics Committee (H-EHREC) in collaboration with University of Education, Hue University & Center for Conservation of Hue Monuments (HMCC)  
**Regulatory Compliance:**
- Constitution of the Socialist Republic of Vietnam (2013)
- Law on Children No. 102/2016/QH13 (Articles 6, 21, 33, 34)
- Decree No. 13/2023/ND-CP on Personal Data Protection (Articles 9, 11, 20, 21)
- Law on Education No. 43/2019/QH14
- Law on Cultural Heritage No. 28/2001/QH10 & Amended Law No. 10/2009/QH12
- International Standards: UNESCO Recommendation on the Ethics of Artificial Intelligence (2021), GDPR-K (Regulation EU 2016/679 Recital 38 / Article 8), US Children's Online Privacy Protection Act (COPPA, 15 U.S.C. §§ 6501–6506), Belmont Report (1979), Declaration of Helsinki (amended 2013).

---

## 1. Executive Summary & Foundational Invariants

This institutional-grade research protocol establishes mandatory ethical requirements, human subjects protections, and methodological firewalls for conducting empirical research on the LƯU NIÊN Learning Management System (LMS) across:
1. Secondary schools (THCS) and upper-secondary high schools (THPT) in Thừa Thiên Huế and neighboring Central Vietnam provinces.
2. Field-based learning expeditions at the Imperial Citadel of Huế (*Đại Nội Huế*), specifically the Nine Dynastic Urns (*Cửu Đỉnh*) at the courtyard of *Thế Miếu*.

### Core Ethical Invariants
- **INV-ETH-01 (Dual Informed Consent/Assent):** No data collection or empirical assessment of any minor participant (<18 years old) may occur without verifiable legal guardian consent and developmental assent from the minor.
- **INV-ETH-02 (Negative Abuse & Non-Coercion):** Declining or withdrawing consent carries **zero educational, disciplinary, academic, or social penalty**. Opt-out students receive standard curriculum activities of identical instructional value.
- **INV-ETH-03 (Zero-PII & Cryptographic Quarantine):** Real student names, national identification numbers, student card numbers, facial biometrics, and home addresses are never captured or stored in research databases. Research identifiers use high-entropy salted HMAC SHA-256 tokens.
- **INV-ETH-04 ($k$-Anonymity & Differential Privacy):** Aggregate analytics enforce $k$-anonymity ($k \ge 5$) across all demographic slices and query interfaces. Cohort cells with $n < 5$ are automatically suppressed.
- **INV-ETH-05 (Teacher Workload Ceiling):** Total research-related grading and administrative overhead is bounded to **$\le 30$ minutes per educator per week**. Dual-assessor workflows offload grading to certified independent raters.
- **INV-ETH-06 (Epistemic Firewall):** Subjective self-reported sentiment surveys (satisfaction, ease-of-use, self-confidence ratings) are structurally and cryptographically isolated from objective learning outcome metrics. No causal learning claims can be derived from survey sentiment (HTTP 422 `CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY`).
- **INV-ETH-07 (Equal Modality Access):** Students with sensory limitations, low-bandwidth devices, or denied camera permissions are afforded 100% equivalent learning, rubric scoring, and XP progression through 2D tactile rubbings, high-contrast monochrome kits, and verbatim transcripts.

---

## 2. Regulatory Alignment & Legal Framework

### 2.1 Vietnam Law on Children No. 102/2016/QH13
- **Article 21 (Right to Privacy):** Children possess inviolable rights to the confidentiality of their personal lives, family secrets, and personal information in learning environments. Research systems are strictly barred from recording or disseminating minor identification without explicit consent.
- **Article 33 (Right of Participation & Expression):** Children aged 7 and above have the legal right to receive clear, age-appropriate information and express their voluntary assent or objection to participating in educational research.

### 2.2 Decree No. 13/2023/ND-CP on Personal Data Protection
- **Article 11 (Data Subject Rights):** Guardians and minors maintain the unconditional right to withdraw consent at any time and demand the permanent deletion, anonymization, or restriction of their personal data.
- **Article 20 (Processing of Children's Personal Data):**
  1. For children under 7 years old: Data processing requires explicit consent of a parent or legal guardian.
  2. For children aged 7 to under 16 years old: Data processing requires explicit consent of **both** the parent/guardian **and** the child.
  3. For adolescents aged 16 to under 18 years old: Informed consent is obtained directly from the student with written notice and opt-out rights provided to the parent/guardian.
- **Article 21 (Data Protection Impact Assessment):** Formal risk assessment conducted prior to deploying digital systems involving youth data in schools.

### 2.3 International Standards (GDPR-K & COPPA)
- **GDPR Recital 38 & Article 8:** Specific protection for children regarding personal data used for profiling, analytics, or behavioral tracking. Behavioral profiling of minors is disabled by default in research deployments.
- **COPPA (15 U.S.C. §§ 6501–6506):** Verifiable parental consent (VPC) mechanisms prior to data collection; strict data minimization; prohibition on conditioning participation on unnecessary disclosures.

---

## 3. Informed Consent & Assent Workflows

```
                           STUDENT & GUARDIAN OUTREACH
                                       │
           ┌───────────────────────────┴───────────────────────────┐
           ▼                                                       ▼
   Guardian Information Pack                               Age-Appropriate Assent
   (Vietnamese / English)                                  (Grades 6–9 / Grades 10–12)
           │                                                       │
           ▼                                                       ▼
  Consent Verification Mode                                 Assent Dialogue
  [SMS OTP | Digital Sig | Paper]                          [Yes / No / Questions]
           │                                                       │
           └───────────────────────────┬───────────────────────────┘
                                       ▼
                       Verification & Status Evaluation
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
      [PENDING]                   [VERIFIED]                 [WITHDRAWN / OPT-OUT]
  • Study features locked    • Anonymized ID generated   • Synchronous data purge
  • Parallel standard task   • Research logging active   • Excluded from stats
  • HTTP 403 blocks API      • Dual assessment allowed   • Zero academic impact
```

### 3.1 Age-Stratified Assent and Consent Protocol
| Cohort | Minor Age | Minor Role | Legal Guardian Role | Verification Channel |
|---|---|---|---|---|
| **Secondary (THCS)** | 11–14 (Grades 6–9) | Written Minor Assent (simplified plain-language Vietnamese, comic-illustrated format) | Affirmative Written Guardian Consent (mandatory) | Signed physical consent slip, SMS OTP confirmation, or school portal verification |
| **High School (THPT)** | 15–17 (Grades 10–12) | Informed Minor Assent / Consent | Affirmative Written Guardian Consent (mandatory under Decree 13) | Digital signature, authenticated school SMS OTP, or signed physical slip |
| **Adult Learners** | 18+ (Grade 12 / Higher Ed) | Adult Informed Consent | Notification copy (optional) | Institutional SSO / Cryptographic digital signature |

### 3.2 Dual-Tier Verification Lifecycle
Every student participant is tracked via the backend `HistoryPilotGuardianConsent` state machine:
1. **`pending`:** Information sheet dispatched; guardian consent slip not yet verified by classroom teacher. The student cannot participate in research-tracked assessment tasks. Any API submission fails with `HTTP 403 GUARDIAN_CONSENT_REQUIRED`.
2. **`verified`:** Consent document inspected, verified, and counter-signed by the classroom teacher or research liaison. Student is assigned a salted cryptographic research identifier (`UUIDv4`). Data logging commences.
3. **`withdrawn`:** Guardian or student communicates withdrawal (digitally or via paper note). The state transitions instantly to `withdrawn`. Submissions fail with `HTTP 403 GUARDIAN_CONSENT_WITHDRAWN`. All identifiable logs and free-text inputs are purged synchronously within 24 hours.

### 3.3 Inclusive Alternative Instruction (Negative Abuse Defense)
To prevent ethical coercion or peer stigmatization:
- Students whose guardians opt out or who decline assent are placed in the **Identical Parallel Learning Activity (IPLA)**.
- IPLA utilizes the same primary historical sources (*Khâm Định Đại Nam Hội Điển Sự Lệ*, *Đại Nam Thực Lục Chính Biên*) and identical curricular inquiry questions using standard school materials or offline standalone tablets.
- Teachers grade both groups with the same standard rubrics for class credit. Research telemetry is strictly disabled for IPLA students.

---

## 4. Zero-PII Anonymization & Data Privacy Architecture

### 4.1 Salted Cryptographic Identifiers
Student identities are decoupled at system ingress. Real student identities never enter the analytical pipeline.
$$\text{Research ID} = \text{HMAC-SHA256}(\text{Salt}_{\text{cohort}} \,\|\, \text{SchoolCode} \,\|\, \text{StudentMasterID})$$
- **High-Entropy Ephemeral Salt:** Generated uniquely per school semester, stored in an encrypted vault accessible only to the principal investigator and the ethics compliance officer.
- **One-Way Transformation:** Research IDs cannot be inverted back to student names or school student roster IDs by platform developers, cloud operators, or AI workers.
- **Key Rotation & Shredding:** At protocol termination (maximum 365 days), the salt is cryptographically shredded, rendering all stored research IDs mathematically un-linkable to any physical person.

### 4.2 $k$-Anonymity and Demographic Privacy ($k \ge 5$)
To prevent quasi-identifier re-identification (e.g., combining School + Grade + Gender + Relic Choice):
- **Cohort Threshold:** Any analytical report, SQL query, or research visualization displaying demographic breakdowns requires a minimum cell count of $k \ge 5$ distinct students.
- **Automated Suppression:** If any sub-group slice has fewer than 5 observations ($n < 5$):
  * The backend reporting engine replaces the entire distribution with `"[SUPPRESSED_K_ANONYMITY_THRESHOLD_N<5]"`.
  * Individual score distributions, means, and variances are masked.
- **Generalization:** Outlier categories (e.g., specific age outliers or rare motif queries) are generalized into broader categories (e.g., "Grade 10 General", "Urn Reliefs Category: Flora/Fauna").

### 4.3 Differential Privacy ($\epsilon, \delta$-DP) Considerations
For open data publication and query auditing across teacher dashboards:
- Query responses apply Laplace noise calibrated to global sensitivity:
  $$M(x) = f(x) + \text{Laplace}\left(0, \frac{\Delta f}{\epsilon}\right)$$
- Privacy budget set at $\epsilon = 0.5$, $\delta = 10^{-5}$ per reporting semester.
- Prevents membership inference attacks when comparing pre-test and post-test aggregate statistics.

### 4.4 Multimedia & Sensor Privacy Gating
1. **Camera & AR Feeds:** WebXR and camera sessions execute purely within the browser's local memory (`HTMLCanvasElement`). Frames are never transmitted over the network or saved to disk.
2. **Audio & Voice Interaction:** Real-time speech-to-text (STT) during Socratic inquiries processes audio in 200ms ephemeral buffers. Buffers are discarded immediately upon transcription. Audio recordings are **never saved** to persistent storage.
3. **Text Anonymization:** Free-text submissions and peer comments pass through an automated PII detector filtering phone numbers, Vietnamese national ID patterns (CCCD / CMND), emails, and personal addresses before storage.

### 4.5 Scheduled Data Retention and Purging Lifecycle
- **Retention Period:** 365 calendar days from the date of final assessment under the approved protocol.
- **Automated Audit Job (`audit_pilot_data_retention`):** Evaluates all records past `valid_until`.
- **Permanent Purge Execution (`purge_expired_pilot_data`):**
  * Student submission texts $\to$ `{"_purged": true, "policy": "Decree_13_2023_ND_CP"}`.
  * Free-text evidence essays, citations, notes $\to$ cleared to empty structures.
  * Rater free-form feedback $\to$ `"[RETENTION_PURGED]"`.
  * Preserves purely de-identified, un-linkable aggregated summary statistics ($n$, mean gain $g$, Cohen's $d$) for formal scientific publication.

---

## 5. Teacher Workload Protection Boundaries

### 5.1 Ethical Duty of Care to Educators
Educational field studies often induce severe educator burnout through uncompensated grading burdens, complex tech administration, and auxiliary reporting. LƯU NIÊN establishes a legally binding workload protection ceiling.

```
+-------------------------------------------------------------------------+
|                  WEEKLY TEACHER WORKLOAD BUDGET                        |
|                                                                         |
|  Total Weekly Burden Ceiling: <= 30 minutes / educator                  |
|                                                                         |
|  [0...................15 min..................30 min] > 30 min          |
|  |     OPTIMAL        |       ACCEPTABLE       |      EXCESSIVE (ALERT) |
|  | (1-5 min/sub)      | (6-8 min/sub)          | (Halt & Deploy Raters) |
+-------------------------------------------------------------------------+
```

### 5.2 Workload Monitoring & Alerting Matrix
| Parameter | Optimal Status | Acceptable Status | Excessive (Burnout Violation) |
|---|---|---|---|
| **Grading Overhead** | $\le 15$ min/week | $16$–$30$ min/week | $> 30$ min/week |
| **Per-Submission Duration** | $\le 5$ min/submission | $6$–$8$ min/submission | $> 8$ min/submission |
| **NASA-TLX Load Index** | $\text{TLX} \le 40$ | $41 \le \text{TLX} \le 60$ | $\text{TLX} > 60$ |
| **System Intervention** | Normal operation | Weekly summary notification | Automated circuit breaker: offload remaining submissions to independent raters |

### 5.3 Workload Mitigation Controls
1. **Certified Independent Secondary Raters:** The research program funds and deploys trained external university teaching assistants and history researchers to handle S1–S4 rubric scoring.
2. **Voluntary Opt-In / Opt-Out Guarantee:**
   - Teacher participation is 100% voluntary.
   - Teachers may withdraw their classroom from the pilot at any moment without justification.
   - School administrations sign a binding covenant affirming that pilot participation or withdrawal **shall not affect teacher annual performance evaluations (*đánh giá viên chức*)**, promotion decisions, or departmental allocations.

---

## 6. Epistemic Separation & Methodological Firewall

### 6.1 Strict Invariant: Anti-Hype Methodological Boundary
A pervasive flaw in EdTech literature is mistaking subjective student enthusiasm ("I loved the 3D model", "I felt like an emperor") for verified cognitive gain. 

LƯU NIÊN operationalizes an immutable technical and cryptographic firewall:

$$\text{Subjective Survey Sentiment} \quad \not\longrightarrow \quad \text{Objective Causal Learning Claims}$$

```
   ┌───────────────────────────────────┐       ┌───────────────────────────────────┐
   │       SUBJECTIVE INSTRUMENTS      │       │        OBJECTIVE INSTRUMENTS      │
   │  • Likert Satisfaction Surveys    │       │  • Paired Pre-Test / Post-Test    │
   │  • User Experience Questionnaires │       │  • Delayed Retention Tests        │
   │  • Emotional Engagement Self-Rates│       │  • S1–S4 Primary Source Rubric    │
   └─────────────────┬─────────────────┘       └─────────────────┬─────────────────┘
                     │                                           │
                     ▼                                           ▼
             [SURVEY LEDGER]                             [EVALUATION LEDGER]
                     │                                           │
         ========================= TECHNICAL FIREWALL ========================
                     │                                           │
                     ▼                                           ▼
          PERMITTED ASSERTIONS:                       PERMITTED ASSERTIONS:
       "94.1% of students found                    "Statistically significant gain
        relic models engaging"                      in S3 Evidence analysis:
                                                    g = 0.54, Cohen's d = 1.18"
```

### 6.2 Enforced Technical Rules
1. **Schema Separation:** Survey data resides in `history_subjective_surveys`. Empirical learning assessments reside in `history_learning_outcome_submissions` and `history_learning_outcome_evaluations`.
2. **Backend Guardrail (`verify_causal_learning_eligibility`):**
   ```python
   def verify_causal_learning_eligibility(instrument_type, is_subjective_self_report=False):
       if is_subjective_self_report or instrument_type == "self_report_survey":
           raise SubjectiveSurveyCannotProduceCausalMetricsError(
               "Subjective survey responses cannot produce causal learning mastery metrics."
           )
   ```
3. **API Rejection:** Any endpoint invocation attempting to feed survey identifiers into normalized gain calculations or causal effect models is terminated with `HTTP 422 CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY`.

---

## 7. Independent Multi-Criteria Evaluation & Inter-Rater Reliability

### 7.1 The Four-Dimensional Historical Inquiry Rubric (S1–S4)
Student inquiry responses are evaluated against four standardized criteria aligned with the Vietnamese 2018 General Education Program (*Chương trình Giáo dục phổ thông 2018* - Môn Lịch sử):

| Criterion | Dimension | Focus & Epistemic Standard | Point Scale |
|---|---|---|---|
| **`S1_SPATIAL`** | Spatial & Geographic Reasoning | Identifying geographical entities engraved on Cửu Đỉnh (mountains, rivers, sea territories such as *Biển Đông* / *Đại Nam Hải* on Cao Đỉnh) and mapping them to geopolitical reality. | 0 – 25 points |
| **`S2_TEMPORAL`** | Chronological & Historical Context | Contextualizing the casting of Cửu Đỉnh (1835–1837) under Emperor Minh Mạng; recognizing succession of sovereign eras. | 0 – 25 points |
| **`S3_EVIDENCE`** | Primary Source Evaluation | Sourcing and corroborating with imperial archival records (*Đại Nam Thực Lục*, *Khâm Định Đại Nam Hội Điển Sự Lệ*, rubbing epigraphy); detecting discrepancies. | 0 – 25 points |
| **`S4_ARGUMENT`** | Historical Synthesis & Argument | Constructing evidence-based thesis on national unity, territorial integrity, and cultural identity; avoiding presentism and unsubstantiated claims. | 0 – 25 points |
| **TOTAL** | **Composite Inquiry Mastery** | **Sum of S1 + S2 + S3 + S4** | **0 – 100 points** |

### 7.2 Dual-Assessor Calibration & Divergence Resolution
To eliminate rater bias, submissions are blind-scored by two independent certified evaluators:
1. **Assessor Independence:** Raters cannot evaluate submissions from their own children, relatives, or students whom they directly instruct in non-research contexts (`validate_assessor_independence`).
2. **Calibration Metric:**
   $$\text{Divergence Percentage} = \frac{|Score_A - Score_B|}{\text{Max Score (100)}} \times 100\%$$
   $$\text{Inter-Rater Agreement} = 1.0 - \frac{|Score_A - Score_B|}{100}$$
3. **Threshold Actions:**
   - **Agreement $\ge 85\%$ (Divergence $\le 15\%$):** Evaluation marked `calibrated`. Final authoritative score is the arithmetic mean:
     $$\text{Final Score} = \frac{Score_A + Score_B}{2}$$
   - **Divergence $> 15\%$:** Evaluation flagged as `divergent_requires_review`. Consensus scores are locked. A third senior adjudicator evaluates the submission, followed by a blind reconciliation conference.

---

## 8. Pre-Registration Plan Template for Field Trials

This template complies with Open Science Framework (OSF) and AsPredicted pre-registration standards for prospective field studies in secondary and high schools.

### 8.1 Study Metadata
- **Protocol Code:** `PRE-REG-VN2026-HUE-RCT01`
- **Study Title:** Randomized Evaluation of Socratic 3D Heritage Scaffolding versus Conventional Textual Instruction on Historical Evidence Literacy in Hue Secondary Schools.
- **Principal Investigators:** Research Consortium on Heritage Education & AI Scaffolding (Hue University & LƯU NIÊN Team).
- **Registration Repository:** OSF Registries (Open Science Framework).

### 8.2 Research Questions & Hypotheses
- **Primary Research Question:** Does engagement with 3D Cửu Đỉnh primary source inquiries scaffolded by citation-grounded AI tutors produce higher historical reasoning gains ($S3$ Evidence and $S4$ Argumentation) compared to standard textbook instruction?
- **Hypothesis 1 ($H_1$ - Learning Gain):** Students in the experimental condition will exhibit significantly higher normalized learning gains ($g \ge 0.40$) on S3/S4 criteria than control group students ($g \le 0.25$), with an estimated effect size Cohen's $d \ge 0.60$ ($p < 0.05$).
- **Hypothesis 2 ($H_2$ - Longitudinal Retention):** At 4-week delayed post-test, experimental students will retain $\ge 80\%$ of their post-test historical reasoning gain, whereas control students will retain $\le 60\%$.
- **Negative Abuse Hypothesis ($H_0$ - Modality Equivalence):** Students utilizing low-bandwidth 2D monochrome rubbing kits will achieve statistically indistinguishable learning gains compared to students using high-fidelity 3D WebXR models ($|g_{3D} - g_{2D}| \le 0.05$), proving pedagogical accessibility.

### 8.3 Experimental Design & Randomization
- **Design Type:** Cluster-Randomized Controlled Trial (Cluster-RCT) or Quasi-Experimental Difference-in-Differences (DiD) with school/grade fixed effects.
- **Cluster Unit:** Entire classrooms within participating schools (to avoid within-class treatment spillovers).
- **Target Population & Stratification:**
  * Secondary Cohort: Grade 7 & Grade 8 students at THCS Nguyễn Tri Phương, THCS Chu Văn An, and THCS Thống Nhất.
  * High School Cohort: Grade 10 & Grade 11 students at THPT Chuyên Quốc Học Huế and THPT Hai Bà Trưng.
  * Stratified block randomization balancing baseline academic performance and socio-economic demographics across treatment arms.
- **Treatment Arms:**
  1. **Arm A (Active Experimental):** LƯU NIÊN Interactive 3D/AR + Socratic Citation-Grounded AI Tutor.
  2. **Arm B (Active Equivalence):** LƯU NIÊN Low-Bandwidth 2D Printable Rubbing Kit + Paper Source Reader.
  3. **Arm C (Standard Active Control):** Traditional 2018 General Education curriculum textbook instruction on the Nguyễn Dynasty and Imperial Hue heritage.

### 8.4 Statistical Power & Sample Size Determination
- **Parameters:** $\alpha = 0.05$ (two-tailed), Power ($1 - \beta$) = $0.80$, minimum detectable effect size (MDES) $\delta = 0.35$ SD.
- **Clustering Adjustment:** Intraclass Correlation Coefficient (ICC) $\rho = 0.10$; average cluster size $m = 35$ students per classroom.
- **Design Effect (DE):**
  $$\text{DE} = 1 + (m - 1)\rho = 1 + (35 - 1)(0.10) = 4.40$$
- **Required Sample Size:**
  $$N_{\text{adj}} = N_{\text{ind}} \times \text{DE} \approx 260 \times 4.40 = 1,144 \text{ students}$$
  Planned enrollment: **36 classrooms across 6 schools ($\approx 1,260$ students)** to allow for up to 10% student attrition.

### 8.5 Primary & Secondary Outcome Measures
1. **Primary Endpoints:**
   - Pre-to-Post Normalized Learning Gain ($g$):
     $$g = \frac{\text{PostScore} - \text{PreScore}}{\text{MaxScore} - \text{PreScore}}$$
   - S3 (Primary Source Evidence Citation) rubric delta ($0$–$25$ scale).
   - S4 (Historical Synthesis Argumentation) rubric delta ($0$–$25$ scale).
2. **Secondary Endpoints:**
   - 4-week delayed post-test retention score.
   - Time-on-task with authentic historical records.
   - Source verification query frequency.
3. **Firewalled Observational Endpoints (Non-Causal):**
   - User engagement metrics, satisfaction ratings, NASA-TLX cognitive load (reported strictly in descriptive tables).

### 8.6 Econometric & Statistical Specification (Difference-in-Differences)
For quasi-experimental setups across semesters or school rollout waves:
$$Y_{ict} = \beta_0 + \beta_1 (\text{Treat}_i \times \text{Post}_t) + \mathbf{X}'_{ict}\boldsymbol{\gamma} + \alpha_c + \delta_t + \varepsilon_{ict}$$
Where:
- $Y_{ict}$: S1–S4 rubric outcome for student $i$ in classroom $c$ at assessment period $t$ ($\text{pre}, \text{post}$).
- $\text{Treat}_i$: Indicator variable equal to 1 if student is assigned to LƯU NIÊN experimental intervention.
- $\text{Post}_t$: Indicator variable equal to 1 for post-intervention measurements.
- $\beta_1$: The causal DiD treatment effect estimator.
- $\mathbf{X}'_{ict}$: Vector of baseline student characteristics (prior history GPA, reading comprehension baseline).
- $\alpha_c$: Classroom fixed effects absorbing teacher quality and school-level invariants.
- $\delta_t$: Time fixed effects absorbing temporal macroeconomic or curriculum calendar shocks.
- $\varepsilon_{ict}$: Error term clustered at the classroom level ($c$).

### 8.7 Statistical Analysis Plan (SAP) & Invariant Rules
- **Missing Data & Attrition:** Intention-to-Treat (ITT) primary analysis using Full Information Maximum Likelihood (FIML) and multiple imputation for missing post-test values.
- **Multiple Hypothesis Testing:** Benjamini-Hochberg False Discovery Rate (FDR) adjustment ($\alpha = 0.05$) applied across secondary criteria comparisons.
- **Stopping Rules:** A formal interim safety review occurs after 20% of data is collected. The trial will be paused if:
  * Any arm reports severe adverse psychological distress or parental grievance.
  * Teacher workload exceeds the 30 min/week threshold in $> 20\%$ of participating schools.

---

## 9. Museum Field Study Protocols (Imperial Citadel of Huế)

### 9.1 Physical Site Safety & Heritage Monument Ethics
Field studies conducted around the Nine Dynastic Urns at *Thế Miếu* (Huế Citadel) adhere to strict monument preservation ethics established by the Hue Monuments Conservation Center (HMCC):
1. **Physical Non-Contact Mandate:** Students and researchers must not touch, lean on, apply stickers, or physically probe bronze urn surfaces or stone pedestals.
2. **Visual & Sensor Range:** AR markers, QR codes, and digital sensors are placed on non-invasive freestanding stanchions approved by HMCC conservators. No equipment may be affixed to historical masonry.
3. **Crowd Flow & Respectful Decorum:** Educational groups are capped at 15 students per guide. Exploration routes must not block regular pilgrims, visitors, or heritage ceremonies.

### 9.2 Mobile Device & Connectivity Fallback in Field Settings
- **Zero Cellular Dependency:** All museum field tasks must be 100% pre-downloadable onto tablets via offline Service Workers and SQLite caches.
- **Low-Battery & Glare Defense:** High-contrast text modes, audio tour alternatives, and paper tactile rubbing guides are available on-site.
- **Offline Action Ledger:** On-site evidence observations queue securely on the device and sync only when connected to school or museum Wi-Fi.

---

## 10. Research Governance, Oversight & Incident Response

### 10.1 Ethics Committee Membership
The independent oversight committee comprises:
1. **Chair:** Senior Ethicist / Representative from Hue University Research Ethics Board.
2. **Historiographical Representative:** Heritage Scholar from Center for Conservation of Hue Monuments (HMCC).
3. **Pedagogical Representative:** High School Master Teacher / History Specialist from Thừa Thiên Huế Department of Education & Training (DOET).
4. **Child Rights / Legal Advisor:** Vietnamese Legal Practitioner specializing in Decree 13/2023/ND-CP and youth protection.
5. **Community / Parent Representative:** Chair of School Parent-Teacher Association (PTA).

### 10.2 Incident Management & Whistleblower Protocol
- **Anonymous Reporting Channel:** Direct web portal and telephone hotline managed independently by H-EHREC.
- **Data Breach Protocol:** If any security breach exposes student records, notifications to parents, school leadership, and the Department of Cyber Security & High-Tech Crime Prevention (Ministry of Public Security) will occur within 72 hours in strict compliance with Decree 13/2023/ND-CP Article 23.
- **Protocol Deviation Reporting:** Any deviation from the pre-registered analysis plan or consent rules must be logged in the public OSF registry within 14 calendar days.

---

## 11. Document History & Approvals

| Version | Date | Status | Description of Changes | Lead Author / Approver |
|---|---|---|---|---|
| `1.0.0` | 2026-09-15 | Draft | Initial formulation of pilot governance | Dr. Tran Research Lead |
| `1.5.0` | 2026-10-20 | Under Review | Integrated Decree 13/2023/ND-CP and S1–S4 rubrics | Legal & Ethics Workgroup |
| `2.0.0` | 2026-11-08 | **APPROVED** | Production institutional-grade protocol; Zero-PII, Pre-Registration RCT template, Teacher Workload Ceiling ($\le 30$ min/week), Epistemic Firewall | H-EHREC Review Board |

---
*End of Institutional Ethics Protocol `IRB-VN-2026-LN09`.*
