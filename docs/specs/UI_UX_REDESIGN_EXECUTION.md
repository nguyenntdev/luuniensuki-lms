# UI/UX REDESIGN EXECUTION LEDGER

Maintained during the Lưu Niên Sử Kí UI/UX consolidation. Master spec:
`docs/specs/UI_UX_REDESIGN_MASTER_SPEC.md`. Source of truth = code/tests/config.

## Audited commit

Latest `main` at audit time (Phase 0).

## Current phase

Phase 1 — Design tokens, layout primitives, design system foundation.

## Current branch

`main`

## Completed task IDs

- Phase 0: repository/route/component/token/test audit (see master spec §1).

## In-progress task IDs

- Phase 1 foundation (globals.css token cleanup, semantic primitives,
  ui primitives additions: Dialog/Sheet/Popover/DropdownMenu/Avatar/Tooltip).
- Phase 2 global shell (GlobalHeader, MobileNavigation, GlobalSearch,
  SiteFooter, UserMenu) replacing FloatingNavbar.

## Tests run and results

- Baseline: lint:ci green, type-check green, vitest 29 pass, build green.

## Migrations added

- (none — frontend-only)

## API contracts changed

- (none)

## Frontend routes changed

- (none yet)

## Mobile changes

- (none)

## Architectural decisions

- Keep the public/authed IA identical: Cửu Đỉnh · Atlas 162 · Khám phá · Nguồn ·
  Search; auth only swaps account/learning controls.
- `/cuu-dinh/[urnSlug]` and Atlas relief detail become the canonical object
  experiences; `/urns` and `/motif` become full-screen/mode renderings reached
  from canonical pages (legacy URLs keep working via alias/redirect).

## Known blockers

- (none)

## Next executable tasks

1. Build semantic token system (globals.css) + tailwind config cleanup.
2. Add missing ui primitives (Dialog, Sheet, Popover, DropdownMenu, Avatar, Tooltip).
3. Global shell components; wire into layout; retire FloatingNavbar.
4. Landing page without mounted gate.
5. Canonical urn/relief consolidation with cross-links + redirects.
6. Khám phá hub (map/timeline/stories/connections/compare/360).
7. Dashboard → "Học của tôi"; AI → one grounded tutor surface.
8. Admin workspace.
9. Responsive/a11y/perf hardening.
10. Obsolete-UI removal, docs reconciliation, final regression.
