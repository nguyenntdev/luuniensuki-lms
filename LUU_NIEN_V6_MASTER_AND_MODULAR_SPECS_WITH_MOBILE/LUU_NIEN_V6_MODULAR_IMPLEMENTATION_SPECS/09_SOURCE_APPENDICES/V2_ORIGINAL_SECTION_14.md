# V2 original archival technical chapter — SECTION_14

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 14. UX INFORMATION ARCHITECTURE V2

### 14.1 Site map

```text
/
├── /explore                   public heritage discovery
│   ├── /collections           documentary/world/intangible distinctions
│   ├── /urns                  9 urns
│   ├── /atlas                 162 motifs
│   ├── /sources               historical source register
│   ├── /stories               context narratives
│   ├── /map                   locations (precision flags)
│   └── /timeline              contextual chronology
├── /learn                     learner route, start / resume
│   ├── /lessons/:id           ELLO
│   ├── /inquiry/:attempt      CER steps with sources
│   ├── /practice              FSRS/quiz separate
│   └── /portfolio             submissions/revisions
├── /teacher                   class/course/rubric/content review
├── /research                  privileged reproducibility dashboard
├── /ai                        source-bounded tutor
├── /living-heritage           creators / craft / experience inquiry
└── /account                   consent / settings / export
```

### 14.2 UI state matrix

For every component support: `loading`, `empty`, `error`, `offline`, `permission-denied`, `unverified-data`, `published`, `withdrawn`, `stale-cache`, `demo-only`. `success` only when server confirms durable change. Language toggle persists with clear fallback labeling. Provide source/uncertainty badge near content, not buried in legal footer.

### 14.3 Accessibility QA

- Semantic landmarks/headings, 44×44 interactive target where applicable, skip links and focus traps in modals.
- 3D viewer text alternative including same observations needed for learning; no forced camera permissions.
- Audio guide captions/transcript, playback controls; avoid autonomous sound.
- Culturally sensitive images with appropriate descriptions and source/context.
- Screen reader Vietnamese/English, contrast and reduced motion; cognitive load minimization progressive disclosure.

---

