# Implementation Plan: Frontend Consolidation & Typing

## Overview

This plan introduces TypeScript to the Next.js frontend, generates typed API models from the backend
OpenAPI schema, migrates the security-sensitive critical paths first, removes orphaned root-level
duplicate components, and fixes the package manifest. Migration is incremental (`allowJs`) so the app
stays runnable throughout.

## Tasks

- [x] 1. Add TypeScript tooling
  - [x] 1.1 Add `tsconfig.json` with `allowJs: true`, `strict: true`, and Next.js settings; remove/replace `jsconfig.json`. _Requirements: 2.1, 2.3_
  - [x] 1.2 Add TypeScript and type dependencies to `frontend/package.json` and a `type-check` script (`tsc --noEmit`). _Requirements: 2.3, 4.1_
  - [x] 1.3 Wire `type-check` into the build/CI so critical-path type errors fail the build. _Requirements: 2.2, 2.3_

- [ ] 2. Generate typed API models
  - [x] 2.1 Add a `gen:api` script that reads the backend OpenAPI schema and emits `frontend/src/types/api.ts`. _Requirements: 1.1, 1.2_
  - [ ] 2.2 Generate `src/types/api.ts` and commit it; verify regeneration is deterministic (running twice yields identical output). _Requirements: 1.2, 1.3_

- [x] 3. Migrate critical paths to TypeScript
  - [x] 3.1 Convert `lib/api.js → lib/api.ts`, typing request bodies and return values against `src/types/api.ts`; preserve runtime behavior (`ApiError`, refresh-on-401). _Requirements: 2.1, 2.2_
  - [x] 3.2 Convert `stores/authStore.js → stores/authStore.ts` with typed state and actions. _Requirements: 2.1, 2.2_
  - [x] 3.3 Run `type-check`; confirm zero type errors on the critical paths. _Requirements: 2.2_

- [x] 4. Remove orphaned duplicates and fix the manifest
  - [x] 4.1 Identify and delete repository-root component files that duplicate maintained components under `frontend/src/` (e.g. `FloatingNavbar.jsx`, `StartingPathGate.jsx`, `page.jsx`, `MediaPlayer.jsx`). _Requirements: 3.1, 3.2_
  - [x] 4.2 Ensure `frontend/package.json` declares all build/runtime dependencies the app imports; remove reliance on the root shadcn-only manifest for the build. _Requirements: 4.1, 4.2_
  - [x] 4.3 Add a duplicate-scan check that fails if a root-level component duplicates one under `frontend/src/`. _Requirements: 3.1_

- [x] 5. Incrementally convert remaining modules
  - [x] 5.1 Convert hooks and shared utilities under `frontend/src/` to `.ts`. _Requirements: 2.1_
  - [x] 5.2 Convert components under `frontend/src/components/` to `.tsx` in reviewable batches, keeping `type-check` green after each batch. _Requirements: 2.1, 2.2_

- [ ] 6. Final verification
  - [x] 6.1 Run `type-check` across the project; confirm zero errors. _Requirements: 2.2_
  - [ ] 6.2 Run the existing Playwright e2e suite to confirm no behavior change. _Requirements: 2.1_
  - [x] 6.3 Verify a deliberate type error on a critical path fails the build, then revert it. _Requirements: 2.3_

## Task Dependency Graph

```json
{
  "waves": [
    {"tasks": ["1"]},
    {"tasks": ["2", "4"]},
    {"tasks": ["3"]},
    {"tasks": ["5"]},
    {"tasks": ["6"]}
  ]
}
```

## Notes

- Incremental `allowJs` migration keeps the app runnable; convert files module by module.
- `src/types/api.ts` is generated, not hand-edited — regenerate via `gen:api` when the backend contract changes.
- Critical paths (api client, auth store, route guard) are typed first; `middleware.ts` is already TS.
- Orphaned-duplicate removal (Task 4) is independent of typing and can proceed in parallel with model generation.
- This spec is sequenced after `security-hardening-remediation`, so it relocates/types already-corrected behavior.
