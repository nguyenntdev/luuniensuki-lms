# Requirements Document

## Introduction

This specification covers consolidating the Frontend into a single typed application and
introducing typed API models. It was split out of the **security-hardening-remediation** spec
(originally Requirement 21) because migrating the untyped JavaScript client to TypeScript and
removing orphaned duplicate files is a large, structural effort distinct from the bounded
security fixes.

The narrow, security-relevant frontend behaviors (server-authoritative exam grading, route-guard
token validity, the i18n table fix, and the route-matching regex fix) remain in the
security-hardening-remediation spec. This spec covers the broader typing and consolidation work.

## Glossary

- **Frontend**: The Next.js client application under `frontend/`.
- **Typed_API_Model**: A TypeScript type/interface describing data exchanged with the backends.
- **Authoritative_Schema_Source**: The source of truth for API shapes, such as an OpenAPI specification emitted by a backend.
- **Orphaned_Component**: A repository-root component file that duplicates a maintained component under `frontend/src/` (e.g., `FloatingNavbar.jsx`, `StartingPathGate.jsx`, `page.jsx`, `MediaPlayer.jsx`).
- **Critical_Path**: Frontend request and authentication code (API client, auth store, route guard).

## Requirements

### Requirement 1: Provide typed API models

**User Story:** As a frontend developer, I want typed models for backend data, so that API misuse is caught at compile time.

#### Acceptance Criteria

1. THE Frontend SHALL provide Typed_API_Models for the data it exchanges with the backends, and SHALL NOT satisfy this requirement by omitting typed models entirely.
2. THE Typed_API_Models SHALL be derived from an Authoritative_Schema_Source such as an OpenAPI specification rather than hand-maintained in isolation.
3. WHEN a backend response shape changes, THE Frontend SHALL be able to regenerate its Typed_API_Models from the Authoritative_Schema_Source.

### Requirement 2: Migrate critical paths to TypeScript

**User Story:** As a frontend developer, I want the critical request and auth paths typed, so that the most security-sensitive code has compile-time guarantees.

#### Acceptance Criteria

1. THE Frontend SHALL migrate its Critical_Path code to TypeScript.
2. WHEN type checking runs, THE Frontend SHALL report no type errors on the migrated Critical_Path code.
3. THE Frontend SHALL configure type checking so that a type error located directly in a Critical_Path file fails the build immediately, including during active migration.

### Requirement 3: Remove orphaned duplicate components

**User Story:** As a developer, I want no duplicated root-level components, so that maintained code has a single home.

#### Acceptance Criteria

1. THE repository SHALL contain no Orphaned_Component files that duplicate maintained components under `frontend/src/`.
2. WHEN a component exists under `frontend/src/`, THE repository SHALL NOT carry any copy of it at the repository root, whether divergent or identical, including during migration or refactoring.

### Requirement 4: Declare real dependencies in the manifest

**User Story:** As a developer, I want the package manifest to declare actual dependencies, so that the build is reproducible.

#### Acceptance Criteria

1. THE Frontend package manifest SHALL declare the build and runtime dependencies the application actually imports.
2. THE repository SHALL NOT rely on a root-level manifest that declares only a single unrelated devDependency for a buildable component.
