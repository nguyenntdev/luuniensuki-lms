# LƯU NIÊN SỬ KÍ — UI/UX REDESIGN MASTER SPEC

**Document type:** Product + UX + Design-System + Migration + Test contract.
**Target repository:** `nguyenntdev/luuniensuki-lms`.
**Status:** Authoritative implementation specification for the frontend consolidation.
**Audience:** Frontend engineers, designers, QA.
**Primary language:** Vietnamese UX; technical English identifiers.

---

## 0. Executive Directive

Lưu Niên Sử Kí must be consolidated into **one product**: an interactive
historical atlas, digital museum-learning platform, and evidence-aware knowledge
system focused on the Nine Dynastic Urns (Cửu Đỉnh). This is NOT a reskin and
NOT a greenfield rewrite. Working business logic, APIs, evidence semantics,
auth, learning, FSRS, progress, gamification, AI, 3D, map, timeline, stories,
sources, classrooms, live infrastructure, and production compatibility are
preserved.

The product mental model is:

> **Explore history first. Learn when desired. Gamification remains subordinate.
> Authentication personalizes the experience but never changes the identity of
> the product.**

The entire surface must feel like one coherent museum-editorial product — never
like a visitor was transferred between an unrelated museum site, an LMS, a game,
and an AI app.

---

## 1. Audited Current State (Phase 0 evidence)

Audited commit: latest `main` at time of writing. Source of truth = code/tests/config.

### 1.1 Route tree (49 page files)

Public history-first (no login): `/`, `/cuu-dinh`, `/cuu-dinh/[urnSlug]`,
`/atlas`, `/atlas/[urnSlug]/[reliefSlug]`, `/map`, `/timeline`, `/stories`,
`/stories/[slug]`, `/sources`, `/sources/[sourceId]`, `/explore/connections`,
`/compare`, `/explore`.

Authed/gamified: `/dashboard`, `/explore` (legacy learning hub), `/urns/[urnSlug]`
(+ `/exam`), `/motif/[motifId]` (+ `/quiz`), `/practice` (+`/smart`,`/results`),
`/collection`, `/trails`, `/profile`, `/ai`, `/quests`, `/achievements`,
`/friends`, `/leaderboard` (redirect), `/badges` (redirect), `/admin`,
`/admin/rag` (redirect), `/live/*`, `/u/[userId]`, `/share/[shareId]`,
`/certificates/*`, `/vr360`, `/tools/annotate`.

Redirects that already exist: `/badges`→`/achievements`,
`/leaderboard`→`/achievements`, `/admin/rag`→`/admin?tab=rag`.

### 1.2 Navigation / shell

- **`FloatingNavbar.tsx`** (ACTIVE): desktop top bar + mobile floating bottom pill
  + mobile sheet. **Auth-based nav swap**: authed → `/dashboard`,`/explore`,
  `/practice`,`/ai`,`/profile`; guest → history-first set. **Authed nav omits all
  public history routes.**
- **`Navbar.tsx`** (DEAD CODE, zero imports).
- **`CommandPalette.tsx`** (ACTIVE): ⌘K global search; history entities → canonical
  routes; static page commands.
- **`AuthGate.tsx`** / **`StartingPathGate.tsx`**: auth redirect + onboarding modal.
- **`NetworkStatusIndicator.tsx`**: offline banner.
- Root `layout.jsx` provider stack: ThemeProvider → NetworkStatusIndicator →
  ClientBodyWrapper → AuthGate → XpCelebrationProvider → BadgeUnlockProvider →
  FloatingNavbar → CommandPalette → StartingPathGate → Toaster.

### 1.3 Public path config + middleware

`src/lib/publicPaths.ts` is the single source of truth
(`/login`,`/register`,`/cuu-dinh`,`/atlas`,`/map`,`/timeline`,`/stories`,
`/sources`,`/compare`,`/explore`). `middleware.ts` enforces it in Edge.
Note: `/register` is public but has no page (registration is a tab in `/login`).

### 1.4 Design tokens

- Tailwind v3 + CSS vars in `globals.css` (`:root` light, `.dark`).
- Existing heritage tokens: `jade`, `bronze`, `ivory`, `xp-gold`, `success`,
  `warning`, `info`; `--imperial-*`, `--deep-navy` (unmapped/dead).
- Custom classes: `site-shell`, `heritage-*` (surface/hero/card/chip/stat),
  `focus-card`, `metric-pill`, `progress-*`, `page-kicker`, `section-grid`,
  `text-gradient-*`, `glow-*`, `shadow-*`, `focus-ring`, `skip-link`,
  `scrollbar-hide`, `hover-lift`, `ripple-*`, `shimmer`, keyframes.
- **Debt:** `--shadow-elegant` var collides with `.shadow-elegant` utility (different
  values); keyframes duplicated between globals.css and tailwind.config with
  different durations; `public/fonts/fonts.css` dead + mislabels Be Vietnam Pro;
  hardcoded hex in map markers, graph node colors, quiz hints, viewer hints;
  `--imperial-*` tokens dead.
- Fonts: Playfair Display (serif/editorial) + Inter (sans/body), self-hosted.

### 1.5 Components

- `ui/` has 10 primitives (alert, badge, button, card, EmptyState, input,
  select, skeleton, table, tabs). **Missing: Dialog, Sheet, Popover, DropdownMenu,
  Avatar, Toast, Tooltip.**
- `history/` kit (all token-based): `EntityCard`, `ClaimItem`, `SectionHeading`,
  `VerificationNote`, `EpistemicLabel`.
- `timeline/`, `trails/`, `profile/`, `badges/`, `live2/`, `viewer/`, `vr360/`.
- 3D: `UrnViewer.tsx` (lazy via `next/dynamic`), `UrnExperience.tsx`.

### 1.6 Data layer

- `api.ts` (180+ exports), `history.ts` (types/normalizers/labels),
  zustand stores (auth, motif, practice, hearts, badge, dailyGoal, dailyMissions,
  friends, gems, xpBoost), `lib/seo.js` (`setPageMeta`).

### 1.7 Tests / CI gate

- CI frontend gate: `lint:ci` (`--max-warnings=0`) → `build` (tsc via prebuild) →
  Playwright `@smoke` (only `smoke.spec.ts`). Vitest is local-only but must stay
  green. `next build` fails on type errors (`ignoreBuildErrors:false`).

---

## 2. Personas & Jobs-to-be-Done

1. **Người khám phá** (guest visitor): "In 30 seconds I understand what Cửu Đỉnh
   are, why the 162 reliefs matter, and that I can inspect them, see evidence,
   and place them in space/time — all without an account."
2. **Người học** (authed learner): "I explore history publicly, then optionally
   deepen through lessons, quizzes, FSRS review, trails, and gamified
   reinforcement without losing the historical context."
3. **Giáo viên / người biên tập**: "I curate collections, attach sources, review
   claims, and see the editorial pipeline clearly."
4. **Nhà nghiên cứu**: "I can trace a claim → source → locator, distinguish fact
   from interpretation, and see uncertainty honestly."
5. **Quản trị viên**: "I operate a dense staff workspace for content and users."

---

## 3. Revised Information Architecture (primary IA for everyone)

**Primary nav (guest AND authed):**
```
Cửu Đỉnh · Atlas 162 · Khám phá · Nguồn · [Global Search]
```

**Khám phá hub** exposes: Bản đồ, Dòng thời gian, Câu chuyện, Mạng lưới liên kết,
So sánh, Tham quan 360°.

**Auth only changes account/learning controls:**
- Guest: "Bắt đầu học" CTA + "Đăng nhập".
- Authed: "Học của tôi" + Profile/avatar.

**Mobile:** top app bar (brand/search/account) + bottom navigation
`Trang chủ / Atlas / Khám phá / Học / Cá nhân`.

---

## 4. Canonical Entity Consolidation

- `/cuu-dinh/[urnSlug]` = canonical urn experience (overview, reliefs, 3D,
  context, facts, interpretation, evidence, relations, map/timeline, learning).
- Atlas relief detail = canonical relief experience (identity, location, 3D
  hotspot, interpretation, geography, chronology, evidence, related, learning).
- `/urns/[urnSlug]` → shared/aliased rendering OR a full-screen 3D mode reached
  from the canonical page; legacy URL must keep working (redirect/alias).
- `/motif/[motifId]` → lesson/quiz mode reached from the canonical relief page;
  legacy URL keeps working.
- Generic entity destination for place/person/event/concept where required.
  Map/search must NOT send non-urn entities to urn pages.

---

## 5. Global Application Shell

Create `components/shell/`:
`GlobalHeader`, `MobileNavigation`, `GlobalSearch`, `SiteFooter`, `UserMenu`.
Retire `FloatingNavbar` after migration; delete dead `Navbar.tsx`.

---

## 6. Visual Direction

**Museum Editorial × Interactive Historical Atlas.**
Warm paper/ivory surfaces, ink typography, restrained bronze accents,
oxidized-bronze/jade secondary. Dark mode stays, tuned for 3D/maps/immersive.
Playfair Display for exhibition/editorial headings, Inter for body/controls.
No excessive serif, gradients, glow, glassmorphism, or decorative "imperial"
motifs. Small semantic token system (no feature-specific variables).

---

## 7. Landing Page Structure

1. Cửu Đỉnh hero (progressive: static poster first, heavy 3D optional, NOT
   blocking critical render; one primary + one secondary CTA).
2. 9-urn gallery (museum objects, not progress cards).
3. Atlas of 162 visual grid.
4. Explore by space/time/story.
5. 3D historical experience entry.
6. Evidence & source credibility.
7. Contextual History Tutor preview with citations.
8. Optional learning layer CTA.
9. Full project footer.

---

## 8. Page-Specific Requirements

- **Cửu Đỉnh**: nine urns as museum objects.
- **Urn detail**: sectional nav Overview / Reliefs / 3D / Context / Evidence /
  Sources / Learning.
- **Atlas**: image-first + historical taxonomy; never "sort by slug" as primary
  UX; search + urn + thematic + verification filters.
- **Relief detail**: identity, object location, 3D hotspot, interpretation,
  geography, chronology, evidence, related entities, optional learning.
- **Map**: uncertainty visualization, localized types, tokens, desktop
  filter-rail + detail panel, mobile fullscreen + bottom sheet, list fallback.
- **Timeline**: preserve keyboard/deep-link/compare; same visual system.
- **Stories**: editorial/magazine hierarchy, featured, long-form.
- **Sources**: research catalogue with bibliographic metadata + rights.
- **AI**: one source-grounded History Tutor; coach/summarize/quiz/review-plan as
  contextual actions, not an API toolbox.
- **Dashboard** → "Học của tôi": history stays the product; dashboard is the
  personalized learning layer.
- **Admin**: dense staff workspace inheriting core tokens.

---

## 9. Server/Client Architecture

- Public history → Server Components where practical (page identity, SEO,
  initial entities/claims/sources).
- Client islands: global search, Atlas filtering, map, timeline interaction,
  graph, 3D, quiz, AI, authed learning state.
- Homepage MUST NOT depend on a post-hydration `mounted` gate.
- Avoid shipping gamification providers to public history pages.
- Use route groups for public-history vs learning layouts without changing URLs.

---

## 10. Design System Primitives

Page shell, content width, editorial width, page hero, object hero, section
heading, cards, image frames, badges, epistemic states, citations, source
previews, tabs, filter bars, drawers, sheets, dialog, breadcrumbs, skeletons,
empty states, error states. States: hover, focus-visible, selected, active,
loading, disabled, empty, error, offline.

---

## 11. Accessibility (WCAG 2.2 AA)

Semantic landmarks, one H1, keyboard nav, visible focus, accessible dialogs,
≥44×44 targets, contrast, alt text, skip links, no color-only status, SR labels,
prefers-reduced-motion, accessible map fallback, focus restoration, mobile safe
areas. Do not regress timeline keyboard accessibility.

---

## 12. Responsiveness

320/375, 768, 1024, 1280, 1440+. Dedicated mobile patterns for maps, 3D,
filters, evidence panels, source drawers.

---

## 13. Performance

LCP ≤ 2.5s p75, CLS < 0.1, INP < 200ms for normal public non-3D pages.
Lazy-load Three.js/map. Responsive images, stable aspect ratios, skeletons.
Minimize root-level client providers.

---

## 14. Testing

Keep all current tests green. Add Playwright journeys: guest
homepage→urn→relief→source→map/timeline→3D; generic search→canonical page;
auth keeps history-first IA; mobile bottom nav/search/drawers/Atlas filters/map
sheet; accessibility keyboard/dialogs/timeline/reduced-motion; visual regression
375/768/1280/1440. CI gate: lint:ci + build + Playwright @smoke.

---

## 15. Execution Ledger

Maintain `docs/specs/UI_UX_REDESIGN_EXECUTION.md` with audited commit, current
phase, completed/in-progress tasks, tests, routes changed, decisions, blockers.

---

## 16. Implementation Phases

- Phase 0: audit + baseline (done — this spec).
- Phase 1: tokens, layout primitives, design system.
- Phase 2: global header, mobile nav, search, footer.
- Phase 3: landing + discovery hub.
- Phase 4: Cửu Đỉnh + Atlas + canonical entity consolidation.
- Phase 5: Map + Timeline + Stories + Sources + Connections + Compare.
- Phase 6: 3D integration into canonical journeys.
- Phase 7: Dashboard ("Học của tôi") + Practice + Collection + Trails + AI + Profile.
- Phase 8: staff/admin workspace.
- Phase 9: responsive, accessibility, performance, visual hardening.
- Phase 10: remove obsolete UI, redirects, reconcile docs, final regression.

A phase is complete only when its user journey works, responsive behavior is
verified, automated checks pass, and the ledger records evidence.

---

## 17. Acceptance Criteria (DOD)

- Guest understands the product in 30s.
- Golden journey works without login: Cửu Đỉnh → urn → relief → meaning →
  fact vs interpretation → evidence → geography/chronology → 3D → related
  history → grounded tutor → optional learning.
- One coherent product feel across museum/atlas/map/timeline/3D/learning.
- Authed users keep the history-first IA.
- No color-only epistemic meaning; tokens used instead of hardcoded palette in
  public surfaces.
- lint:ci, type-check, Vitest, Playwright, production build all green.
