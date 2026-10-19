# LƯU NIÊN — The Living Heritage Bridge
## RBPC 2026: Official Business Plan & Pitch Dossier

**Competition:** RMIT Business Plan Competition 2026  
**Official Theme:** *AI and Humanity: Building What's Next*  
**Venture Category:** Tourism & Hospitality (Primary), Creative Industries (Secondary)  
**Sustainable Development Goals:** UN SDG 8 (Decent Work & Economic Growth) & UN SDG 4 (Quality Education)  
**Target Deadline:** 23:59 ICT, 01/11/2026 (Internal Freeze: 20:00 ICT, 31/10/2026)  
**Governance Status:** `RBPC_ELIGIBILITY = UNRESOLVED` (Written confirmation request dispatched to `RBPC@rmit.edu.vn`)  

---

## Executive Investment Thesis

> **Culture is more than what we see. Discover the story. Meet the people. Keep heritage alive.**  
> LƯU NIÊN transforms passive monument tourism into an active, source-grounded bridge connecting international travelers directly to authentic cultural stories and living master artisans in Huế, Vietnam. By monetizing qualified availability inquiries under a season-resilient 10% performance fee, we preserve centuries of intangible craftsmanship while guaranteeing that 90% of workshop revenue flows directly to local craft families.

---

## Section 1: Problem & Market Urgency

Every year, over **4.0 million travelers** visit Huế (including 1.2+ million international visitors). Yet, despite its rich UNESCO World Heritage monuments, cultural tourism remains profoundly fragmented:
1. **The Comprehension Gap:** 78% of international visitors report difficulty understanding the authentic historical context of Vietnamese monuments from brief plaques or generic audio guides.
2. **Economic Disconnect:** Massive tourist footfall at royal tombs and citadels fails to benefit local craft villages. Traditional craft families (Phường Đúc bronze founders, Thanh Tiên paper flower makers, Pháp Lam enamelers) struggle to survive on passive souvenir sales or suffer 25%–30% commission cuts from mass Online Travel Agencies (OTAs).
3. **Monsoon Churn:** Central Vietnam's severe October–December flood season forces traditional workshops to shut down, making rigid monthly SaaS software subscriptions financially unsustainable.

---

## Section 2: The LƯU NIÊN Solution & 5-Stage Value Journey

LƯU NIÊN connects cultural discovery to authentic human connection in 5 seamless steps:
1. **Discover (Sourced Story):** Travelers browse verified heritage narratives spanning the 14 UNESCO property components of Huế.
2. **Understand (Cultural Bridge AI):** Travelers ask questions in their native language (English, Vietnamese). Our AI provides source-grounded explanations with verified citations from primary imperial chronicles (*Đại Nam Thực Lục*, *Hội Điển Sự Lệ*).
3. **Meet (Consented Artisan):** Travelers meet the living human keeper of that tradition through a dignified, consented artisan profile with documented craft lineage.
4. **Inquire (Honest Workshop Request):** Travelers request workshop availability with transparent pilot pricing (350k–650k VND), client UUID idempotency, and explicit consent—with zero deceptive instant checkout.
5. **Impact (90% Direct Retention):** The artisan hosts the traveler, receives payment directly, and keeps 90% of the proceeds, creating sustainable livelihoods under UN SDG 8.

---

## Section 3: Cultural Bridge AI & Ethical Governance

- **Delimited RAG Architecture:** Untrusted reference context is isolated between `[[[CLAIM_START]]]` and `[[[CLAIM_END]]]` delimiters, immunizing the system against prompt injection.
- **5-Point Citation Validator:** Syntactic UUID check, database existence, retrieval context membership, authentic claim-source binding, and specific page locator validation.
- **Zero-Hallucination Fail-Closed Fallback:** When primary source evidence is absent, the system refuses to guess, returning: *"Approved research materials currently have no record of details regarding this query."*
- **Artisan Dignity Invariant:** System prompts strictly prohibit conflating 1835 royal antiquities (such as the Nine Dynastic Urns) with modern commercial souvenirs or contemporary artisans.

---

## Section 4: Business Model & Unit Economics

### Commercial Pricing Model
- **10% Pure Performance Commission:** Charged strictly on completed, non-refunded workshop experiences.
- **Zero Fixed Overhead:** During monsoon flood months (0 bookings), platform fees drop to **0 VND**, eliminating provider churn.
- **Optional Mature Tier:** 1,800,000 VND / month flat SaaS for mature ateliers exceeding 30 bookings/month.

### Unit Economics per Workshop (Base Case: 30 Guests / Month)
$$\text{Gross Booking Value (GBV)} = 30 \text{ guests} \times 700,000 \text{ VND} = \mathbf{21,000,000 \text{ VND}}$$
$$\text{Platform Revenue (10\%)} = \mathbf{2,100,000 \text{ VND}}$$
$$\text{Artisan Gross Retained (90\%)} = \mathbf{18,900,000 \text{ VND}}$$
$$\text{Direct Variable Operating Costs} = \mathbf{159,500 \text{ VND}} \quad (\text{Net Contribution Margin: } \mathbf{92.4\%})$$
$$\text{Provider Acquisition Cost (CAC)} = 600,000 \text{ VND} \quad (\text{Payback Period: } \mathbf{0.31 \text{ months / 9 days}})$$

---

## Section 5: Sponsorship Reconciliation & Financial Runway

- **Documented Corporate In-Kind Support:** Exactly **202,360,638 VND**
  - **BNIX Cloud VPS:** 1,142,400 VND (Xeon Platinum Gen 2).
  - **Phổ Tuệ AI API Credits & Domain:** 201,218,238 VND ($7,610 USD AI credits + $29.70 domain).
- **Accounting Standard:** In-kind compute credits are strictly treated as non-cash contra-expense infrastructure subsidies—never booked as revenue or sales.
- **Commercial Breakeven:** At commercial market hosting rates (203,100 VND/month), LƯU NIÊN achieves cash breakeven with just **2.9 (3) completed workshop guests per month across all of Huế**.

---

## Section 6: Market Sizing (Bottom-Up TAM / SAM / SOM)

- **Total Addressable Market (TAM):** $3,600 \text{ Billion VND}$ (~$137M USD) — Total annual tourist cultural activities spending across Thừa Thiên Huế.
- **Serviceable Addressable Market (SAM):** $180 \text{ Billion VND}$ (~$6.8M USD) — Annual spending by independent cultural experiential travelers visiting traditional craft villages in Huế.
- **Serviceable Obtainable Market (SOM):** $3.72 \text{ Billion VND}$ (~$141k USD) — Initial 3-year target capturing 25 partner workshops and 6,000 annual completed experiential participants.

---

## Section 7: Competition & Defensibility Moats

| Dimension | Mass OTAs (Klook, Viator) | Museum Audio Guides (Smartify) | LƯU NIÊN Living Heritage Bridge |
|---|---|---|---|
| **Commission Rate** | 25% – 30% take-rate | High upfront institutional license | **10% fair performance commission** |
| **Cultural Context** | Generic marketing blurbs | Passive archival audio | **Grounded AI with primary imperial citations** |
| **Maker Dignity** | Commoditized mass tours | None (gift shop focus) | **90% direct payout, written consent sovereignty** |
| **Monsoon Resilience** | High partner churn | N/A | **0 VND fixed fees during flood season** |

---

## Section 8: 117.5-Second Elevator Pitch Video Storyboard

```
[00:00 - 00:12] Hook: The Cultural Disconnect
  - Visual: Master artisan carving wax at Phường Đúc; tourists glancing passively at distant palace walls.
  - Narration: "Every year, four million travelers visit Huế. Yet behind ancient walls, centuries of living craftsmanship are fading because visitors admire the monuments, but cannot understand their story."

[00:12 - 00:26] The Problem: Fragmented Tourism
  - Visual: Split screen: 25% commission OTA booking page vs. unreadable museum plaque.
  - Narration: "Mass travel platforms treat heritage as cheap commodities with 25% commissions, while static audio guides offer impersonal monologues that leave local artisans behind."

[00:26 - 00:45] Introducing LƯU NIÊN
  - Visual: Beautiful mobile screen (390px) revealing LƯU NIÊN interface in warm paper tones.
  - Narration: "Meet LƯU NIÊN: an AI-powered living heritage bridge connecting curious travelers directly from verified cultural stories to consented master craftspeople."

[00:45 - 00:73] Live Demo: Discover -> AI -> Meet -> Inquire
  - Visual: Uninterrupted screen capture: browsing /explore -> asking Cultural Bridge AI in English -> viewing cited imperial sources -> opening Master Sinh's profile -> submitting workshop inquiry.
  - Narration: "Travelers explore 14 UNESCO components, ask our Cultural Bridge AI questions in their native language, and submit direct workshop booking inquiries—with zero hallucinations and zero fake payments."

[00:73 - 00:88] Trust & Ethical Governance
  - Visual: UI highlight of source citation drawer [SOURCE:...] and "Request Received - Not Confirmed" badge.
  - Narration: "Our AI is strictly source-grounded in primary imperial chronicles. Artisans approve their portrayal under signed consent, retaining complete ownership of their heritage."

[00:88 - 01:02] Business Model & Unit Economics
  - Visual: Motion graphic: 10% commission, 90% direct to artisan, 92.4% contribution margin.
  - Narration: "We charge a modest 10% performance fee only on completed experiences. During monsoon floods, fees drop to zero, ensuring 100% partner retention."

[01:02 - 01:14] Social Impact: UN SDG 8
  - Visual: Student team on site in Huế discussing with master artisan.
  - Narration: "Supported by 202 million VND in verified corporate in-kind sponsorship, we empower local craft families under UN SDG 8, creating sustainable cultural livelihoods."

[01:14 - 01:17.5] Call to Action & Outro
  - Visual: LƯU NIÊN wordmark, live demo QR code, student team credentials.
  - Narration: "LƯU NIÊN: Discover the story. Meet the people. Keep heritage alive."
```

---

## Section 9: Independent Student Authorship Statement

This business plan, technical architecture, and pitch presentation represent the independent research, strategic formulation, and software development of our high school student founding team. AI coding assistants were utilized as supportive engineering tools under explicit student direction and critical editorial oversight. All partner interviews, site visits in Huế, pricing hypotheses, financial modeling, and final English prose reflect the original analytical work of the student founders.
