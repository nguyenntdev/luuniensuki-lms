# 3D Interactivity + UI Modernization Plan (Desktop, Imperial-Minimal, Gamified)

## Scope
- Improve 3D interactivity and in-scene actions on the urn experience.
- Modernize the HUD/journey panels to a minimal imperial look.
- Emphasize gamified progression and quick next-step guidance.

## Target Experience
- Device: Desktop only.
- Style: Imperial Vietnamese heritage with a minimal contemporary layout.
- Tone: Edtech gamification (quests, progress, rewards).

## Out of Scope
- Mobile-specific UI changes.
- New 3D assets or GLB updates.
- Backend changes or new APIs.
- Multi-user or real-time collaboration features.

## Key Files (Current System)
- `frontend/src/components/UrnExperience.js`
- `frontend/src/components/UrnViewer.js`
- `frontend/src/components/LessonSidebar.js`
- `frontend/src/stores/motifStore.js`
- `frontend/src/app/globals.css`

## Requirements (EARS)
- WHEN a user opens an urn 3D scene THE SYSTEM SHALL show a minimal HUD with progress and the next step.
- WHEN a user selects a motif in 3D THE SYSTEM SHALL smoothly focus the camera on that motif.
- WHEN a motif is selected THE SYSTEM SHALL show an in-scene action chip with Lesson and Quiz actions.
- WHEN the user switches to Scan mode THE SYSTEM SHALL reveal undiscovered motifs with subtle pulses.
- WHEN the user switches to Mastery mode THE SYSTEM SHALL highlight unmastered motifs and dim mastered motifs.
- WHEN a motif becomes mastered THE SYSTEM SHALL update its 3D visual state and HUD progress.
- WHEN the user presses desktop shortcuts THE SYSTEM SHALL trigger the mapped actions.
- WHEN no motif is selected THE SYSTEM SHALL hide the in-scene action chip.
- WHEN WebGL fails THE SYSTEM SHALL keep the fallback view functional without broken overlays.

## Non-Functional Constraints
- No new dependencies.
- Keep overlays light (selected + next motifs only).
- Maintain consistent Tailwind tokens and spacing.

## Interaction Modes
| Mode     | Hidden Motifs | Discovered Motifs | Mastered Motifs | Unmastered Focus |
|----------|----------------|-------------------|------------------|------------------|
| Standard | Hidden          | Normal            | Subtle halo      | No               |
| Scan     | Visible + pulse | Normal            | Dim              | No               |
| Mastery  | Hidden          | Dim               | Dim              | Highlight only   |

## UI Direction (Imperial-Minimal)
- Keep Playfair for headings, Inter for UI.
- Use fewer gradients; keep jade/bronze accents.
- Unified card system for HUD and journey.
- Motion: one focus animation + a single "next motif" pulse.

## Implementation Plan (Detailed Tasks)

### Phase 1: State and Interaction Foundation
T1. Define motif state mapping for UI and 3D
- Update local logic to normalize status: hidden, discovered, learned, mastered.
- Acceptance: a single helper map drives hotspot styling and HUD status.
- Files: `frontend/src/components/UrnViewer.js`, `frontend/src/components/UrnExperience.js`

T2. Add derived selectors for next motif and mastery counts
- Simple selectors in store (no new abstractions).
- Acceptance: UrnExperience reads next/unmastered from a single source.
- Files: `frontend/src/stores/motifStore.js`, `frontend/src/components/UrnExperience.js`

T3. Keyboard shortcuts (desktop)
- Map: N=Next motif, H=toggle hints, L=lesson, Q=quiz.
- Acceptance: shortcuts trigger expected actions without page refresh.
- Files: `frontend/src/components/UrnViewer.js` or `frontend/src/components/UrnExperience.js`

### Phase 2: 3D Interactivity
T4. Camera focus on selection and "next motif"
- Wire `CameraController` to selected motif and focus requests.
- Acceptance: selecting a motif moves camera smoothly to it.
- Files: `frontend/src/components/UrnViewer.js`

T5. In-scene action chip
- Anchor a single Html overlay to the selected motif.
- Actions: Lesson, Quiz (links).
- Acceptance: overlay appears only for selected motif and hides on deselect.
- Files: `frontend/src/components/UrnViewer.js`

T6. Mode toggles (Standard/Scan/Mastery)
- Replace the single hint toggle with three modes.
- Acceptance: modes update hotspot visibility/brightness rules.
- Files: `frontend/src/components/UrnExperience.js`, `frontend/src/components/UrnViewer.js`

T7. Hotspot visual system by status
- Hidden: invisible.
- Discovered: normal opacity.
- Mastered: subtle halo ring.
- Unmastered: highlight in Mastery mode.
- Acceptance: visual states match the table above.
- Files: `frontend/src/components/UrnViewer.js`

T8. "Next motif" pulse
- Only one pulse at a time, short duration.
- Acceptance: next motif is clearly guided without persistent noise.
- Files: `frontend/src/components/UrnViewer.js`, `frontend/src/components/UrnExperience.js`

### Phase 3: HUD and Journey Modernization
T9. Consolidate HUD + journey into a unified card system
- Reduce visual noise, consistent spacing and typography.
- Acceptance: top HUD and bottom journey feel part of one system.
- Files: `frontend/src/components/UrnExperience.js`

T10. Add quest/next action capsule
- Compact display for next step, quest name, and progress.
- Acceptance: next action is visible without leaving 3D.
- Files: `frontend/src/components/UrnExperience.js`

T11. Lesson sidebar alignment
- Reduce density and keep "next step" clear.
- Acceptance: lesson sidebar looks consistent with the new HUD.
- Files: `frontend/src/components/LessonSidebar.js`

### Phase 4: Gamified Feedback
T12. Local reward burst near motif
- Small in-scene XP/badge pop near selected motif on success.
- Acceptance: reward feels tied to the motif, not only global toast.
- Files: `frontend/src/components/UrnViewer.js`

T13. Streak/progress hint in HUD
- Small indicator for daily progress or streak (read-only).
- Acceptance: visible but unobtrusive.
- Files: `frontend/src/components/UrnExperience.js`

### Phase 5: Visual Tokens and Polish
T14. Update global tokens (minimal imperial tuning)
- Reduce glow intensity, unify card radius/shadow.
- Acceptance: modernized look without losing imperial palette.
- Files: `frontend/src/app/globals.css`

T15. Motion polish
- Ensure transitions are consistent (focus, overlay, panel entry).
- Acceptance: no excessive micro-animations.
- Files: `frontend/src/components/UrnExperience.js`, `frontend/src/components/UrnViewer.js`

### Phase 6: Validation
T16. Manual QA checklist
- Selection -> focus -> action chip -> lesson/quiz.
- Scan/Mastery toggles update hotspots correctly.
- Keyboard shortcuts function and do not conflict with browser defaults.
- WebGL fallback unaffected.

## Acceptance Criteria
- Users can select a motif and see an immediate in-scene action chip.
- Camera focus feels intentional and smooth on desktop.
- Scan and Mastery modes clearly communicate what to do next.
- HUD and journey panel look modern, minimal, and imperial.
- Progress updates reflect mastery in both UI and 3D.

## Risks and Mitigations
- Too many overlays -> limit to selected and next motifs only.
- Motion discomfort -> use short, gentle camera transitions.
- Visual noise -> only one pulse at a time; dim non-target motifs.
