# Frontend UI/UX Improvements — Log & Roadmap

Stack: Next.js 15 (App Router) · React 19 · Tailwind + HSL design tokens · three.js
/ @react-three/fiber. Mature heritage dark theme with a11y utilities
(skip-link, reduced-motion, focus-ring), shimmer/skeleton loaders.

## Shipped (this initiative — all built, deployed, verified 200)

### Navigation & global
- **Command palette (Cmd/Ctrl-K)** for instant nav + jump-to-đỉnh.
- **VR360 wired into the navbar** (was an orphaned route).
- **Accessibility**: real skip-to-content link + `#main-content` landmark
  (the `.skip-link` CSS existed but was never used).

### Dashboard
- **"Khám phá nhanh" journeys hub** — four rich cards (3D explore, live AI
  teacher, 360° tour, practice) with gradient icons, hover-lift, focus rings.

### Explore (course catalog)
- Per-đỉnh **progress bar + status counts** (discovered/learned/mastered),
  completion %, **3D badge**, context-aware CTA.

### Lesson page (motif)
- **Reading-progress bar** (scroll-based) for long lessons.

### Collection ("Kho Tàng")
- **Vietnamese category labels** on cards (was raw enum like `linh_thu`).
- **Overall mastery progress bar** + unlocked count.

### Live classroom
- **Mobile overlay** for the side panel + teacher console (was squeezing the
  avatar column on phones); inline side-column preserved on md+.
- **Streaming caption cursor** on interim transcript bubbles.

### App-level resilience
- **Branded 404 / route-error / loading / global-error pages** (App Router had
  none → users hit unstyled default Next.js screens). Now heritage-themed with
  retry + error digest.

## Researched roadmap (not yet done — prioritized)

1. **Urn 3D viewer (`UrnExperience`)** — the centerpiece. High value, higher
   risk (three.js + hotspots). Opportunities: hotspot legend, motif progress
   rail, mobile controls hint, loading state for the GLB.
2. **Achievements page (723 lines)** — badge grid polish, earned vs locked
   clarity, share affordances; leaderboard is merged here (`/leaderboard`
   redirects to `/achievements`).
3. **Profile page (855 lines)** — settings grouping, avatar upload UX.
4. **Quiz flow** — progress indicator, per-question feedback animation,
   results summary with weak-area links.
5. **Performance** — audit bundle size of the 3D routes; lazy-load three.js
   only on viewer routes; image `next/image` adoption for thumbnails.
6. **Empty/error states** — a shared `<EmptyState>`/`<ErrorState>` component
   for consistency across pages. (App-level error/404/loading pages: DONE.)

## Constraints / methodology
- No dev server available for visual QA → changes are additive + verified via
  `getDiagnostics` + production build + smoke (HTTP 200), not blind rewrites.
- Each change: implement → diagnostics → commit → push → rebuild `web` →
  recreate container → verify.
