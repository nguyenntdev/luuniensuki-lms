# 📋 UX IMPROVEMENT IMPLEMENTATION PLAN

## Overview

Kế hoạch triển khai các cải tiến UX cho Luuniensuki LMS, phân công cho **Codex CLI** và **Gemini CLI**.

### Tool Assignment Rules
- **Codex CLI (`codex`)**: Code generation, refactoring, component creation
- **Gemini CLI (`gemini`)** với model `gemini-2.5-pro-preview-05-06`: Documentation, content writing, i18n translations, long text generation

---

## 🚀 PHASE 1: Quick Wins (1-2 days)

### Task 1.1: Simplify FloatingNavbar (4 items)
**Assignee: Codex CLI**

```bash
codex "Refactor FloatingNavbar.jsx to reduce navigation items from 6 to 4:
- Khám Phá (/explore) - Eye icon
- Bộ Sưu Tập (/collection) - BookOpen icon  
- Thành Tích (/achievements) - Trophy icon (NEW - combines badges + leaderboard)
- Hồ Sơ (/profile) - User icon (rename from /dashboard)

Keep: language switcher, user dropdown
Remove: separate Home, Dashboard, Badges, Leaderboard items
Update both desktop and mobile nav sections.
File: frontend/src/components/FloatingNavbar.jsx"
```

### Task 1.2: Create /achievements page (merge badges + leaderboard)
**Assignee: Codex CLI**

```bash
codex "Create new page frontend/src/app/achievements/page.jsx that combines:
1. Tab navigation: 'Huy Hiệu' (badges) | 'Bảng Xếp Hạng' (leaderboard)
2. Badges tab: Copy logic from /badges/page.jsx
3. Leaderboard tab: Copy logic from /leaderboard/page.jsx
4. Use Zustand state for active tab
5. Vietnamese UI text
6. Responsive grid layout"
```

### Task 1.3: Update translations for new nav
**Assignee: Gemini CLI**

```bash
gemini -m gemini-2.5-pro-preview-05-06 "Generate Vietnamese and English translations for the new navigation structure:

New nav items:
1. Khám Phá / Explore - for browsing urns
2. Bộ Sưu Tập / My Collection - for viewing discovered motifs  
3. Thành Tích / Achievements - for badges and leaderboard
4. Hồ Sơ / Profile - for user profile and stats

Also generate translations for:
- Tab labels: Huy Hiệu/Badges, Bảng Xếp Hạng/Leaderboard
- Empty states
- Loading states

Output as JSON object with 'vi' and 'en' keys."
```

### Task 1.4: Add Progress Stepper to LessonSidebar header
**Assignee: Codex CLI**

```bash
codex "Add a visual progress stepper component to LessonSidebar.js header:

1. Create ProgressStepper component showing 3 steps:
   - Step 1: Khám Phá (discovered) - 25 XP
   - Step 2: Bài Học (learned) - 50 XP  
   - Step 3: Trắc Nghiệm (mastered) - 75 XP

2. Visual states:
   - Completed: green checkmark, filled circle
   - Current: primary color, pulsing animation
   - Locked: gray, lock icon

3. Show connecting lines between steps
4. Display XP earned at each step
5. Place above the motif name in sidebar header

File: frontend/src/components/LessonSidebar.js"
```

---

## 🔄 PHASE 2: Core Flow Improvement (3-5 days)

### Task 2.1: Design Tab System for LessonSidebar
**Assignee: Gemini CLI**

```bash
gemini -m gemini-2.5-pro-preview-05-06 "Design the UX specification for a tabbed LessonSidebar:

Requirements:
1. Three tabs: Tổng Quan (Overview), Bài Học (Lesson), Trắc Nghiệm (Quiz)
2. Quiz tab should be disabled until lesson is completed
3. Tab should auto-switch after completing lesson
4. Quiz results should show inline, not navigate away

Please provide:
1. Detailed user interaction flow
2. State management requirements
3. Animation/transition specifications
4. Accessibility considerations (ARIA)
5. Mobile touch interactions
6. Error handling scenarios

Output as structured markdown specification."
```

### Task 2.2: Implement Tabbed LessonSidebar
**Assignee: Codex CLI**

```bash
codex "Refactor LessonSidebar.js to use a tabbed interface:

1. Add TabNavigation component with 3 tabs:
   - 'overview': Tổng Quan (default)
   - 'lesson': Bài Học  
   - 'quiz': Trắc Nghiệm (disabled if status !== 'learned' && status !== 'mastered')

2. Create tab content panels:
   - OverviewPanel: current motif info, thumbnail, category, rarity
   - LessonPanel: full lesson content (description, symbolism, historical_context, fun_fact)
   - QuizPanel: inline quiz (port logic from /motif/[id]/quiz/page.jsx)

3. State management:
   - activeTab in component state
   - Auto-switch to 'quiz' tab after completing lesson
   - Persist tab state in URL hash or localStorage

4. Keep existing sidebar animation and close behavior

File: frontend/src/components/LessonSidebar.js"
```

### Task 2.3: Create Inline QuizPanel Component
**Assignee: Codex CLI**

```bash
codex "Create QuizPanel component for inline quiz in LessonSidebar:

1. Port quiz logic from frontend/src/app/motif/[motifId]/quiz/page.jsx
2. Adapt for sidebar context (narrower width, scrollable)
3. Features:
   - Question navigation (prev/next)
   - Progress indicator
   - Timer display
   - Answer selection (radio buttons for multiple choice)
   - Submit button
   - Results display inline (score, XP, explanations)
   - 'Làm lại' (retry) button

4. Props interface:
   - motifId: string
   - onComplete: (result) => void
   - onClose: () => void

5. Use existing API functions: getMotifQuiz, submitQuiz

Create: frontend/src/components/QuizPanel.jsx"
```

### Task 2.4: Create Smart Homepage for Authenticated Users
**Assignee: Codex CLI**

```bash
codex "Modify frontend/src/app/page.jsx to show different content for authenticated users:

1. If NOT authenticated: show current landing page (hero + CTAs)
2. If authenticated: show Smart Dashboard with:

   a. Continue Learning Card:
      - Current/last urn being explored
      - Progress bar (X/Y motifs discovered)
      - 'Tiếp tục' button → /urns/[slug]

   b. Stats Row (3 cards):
      - Streak: current_streak with fire emoji
      - Total XP: total_xp with star emoji
      - Badges: earned/total with medal emoji

   c. Recent Discoveries:
      - Last 5 discovered motifs as small thumbnails
      - Click to open in 3D viewer

3. Use useAuthStore to check authentication
4. Fetch data: getMyCollection, getMyStreak, getUrns

File: frontend/src/app/page.jsx"
```

### Task 2.5: Write Homepage Content
**Assignee: Gemini CLI**

```bash
gemini -m gemini-2.5-pro-preview-05-06 "Write Vietnamese UI text for the authenticated user homepage:

Sections needed:
1. Welcome message with user name placeholder
2. 'Continue Learning' card:
   - Title
   - Progress label (e.g., 'Đã khám phá X/Y họa tiết')
   - Button text
3. Stats cards:
   - Streak card title and subtitle
   - XP card title and subtitle
   - Badges card title and subtitle
4. Recent discoveries section:
   - Section title
   - Empty state message
5. Quick tips/hints for new users

Make it engaging, use Vietnamese cultural tone.
Output as JSON for easy integration."
```

---

## 📋 PHASE 3: Polish (2-3 days)

### Task 3.1: Redirect /dashboard to /profile
**Assignee: Codex CLI**

```bash
codex "Update routing to rename dashboard to profile:

1. Rename frontend/src/app/dashboard/ to frontend/src/app/profile/
2. Add redirect from /dashboard to /profile in middleware or page
3. Update all internal links from /dashboard to /profile
4. Update FloatingNavbar links
5. Update UrnExperience.js header links

Files to modify:
- frontend/src/app/dashboard/page.jsx → frontend/src/app/profile/page.jsx
- frontend/src/components/FloatingNavbar.jsx
- frontend/src/components/UrnExperience.js
- frontend/src/components/LoginPage.js (redirect after login)"
```

### Task 3.2: Deprecate Standalone Motif Pages
**Assignee: Codex CLI**

```bash
codex "Add redirects for deprecated motif pages:

1. /motif/[motifId] → redirect to /explore with toast 'Mở họa tiết từ trình xem 3D'
2. /motif/[motifId]/quiz → redirect to /explore with toast 'Làm trắc nghiệm từ trình xem 3D'

Keep the page files but add redirect logic at top.
Show toast notification explaining the change.

Files:
- frontend/src/app/motif/[motifId]/page.jsx
- frontend/src/app/motif/[motifId]/quiz/page.jsx"
```

### Task 3.3: Update Onboarding Modal Content
**Assignee: Gemini CLI**

```bash
gemini -m gemini-2.5-pro-preview-05-06 "Rewrite the onboarding modal slides for the new UX flow:

Current slides cover:
1. Welcome
2. 3D Exploration
3. Learning Flow
4. Gamification

New slides should explain:
1. Welcome - Giới thiệu Lưu Niên Sử Kí
2. Khám Phá - Chọn đỉnh và khám phá 3D
3. Học Tập - Click họa tiết → đọc bài học → làm trắc nghiệm (all in sidebar)
4. Thành Tích - XP, badges, leaderboard, streak

For each slide provide:
- title (Vietnamese)
- description (Vietnamese, 2-3 sentences)
- icon (emoji)

Output as JavaScript array matching DEFAULT_SLIDES format in OnboardingModal.jsx"
```

### Task 3.4: Consistent Card Styling
**Assignee: Codex CLI**

```bash
codex "Create shared card components for consistent styling:

1. Create frontend/src/components/ui/Card.jsx with variants:
   - default: standard card with border
   - elevated: with shadow
   - interactive: hover effects for clickable cards

2. Create frontend/src/components/ui/StatusBadge.jsx:
   - Props: status ('hidden' | 'discovered' | 'learned' | 'mastered')
   - Consistent colors across app:
     - hidden: gray
     - discovered: blue/info
     - learned: green/success
     - mastered: gold/bronze

3. Update these files to use new components:
   - LessonSidebar.js
   - Collection page
   - UserProfile.js
   - Badges page"
```

### Task 3.5: Write Tooltip Content for New Features
**Assignee: Gemini CLI**

```bash
gemini -m gemini-2.5-pro-preview-05-06 "Write tooltip/hint content for new UX features:

1. Progress Stepper tooltips:
   - Step 1 (Khám Phá): explain discovery
   - Step 2 (Bài Học): explain lesson completion
   - Step 3 (Trắc Nghiệm): explain quiz mastery

2. Tab hints in LessonSidebar:
   - Overview tab hint
   - Lesson tab hint
   - Quiz tab hint (when locked)
   - Quiz tab hint (when unlocked)

3. Homepage hints for new users:
   - Continue learning card hint
   - Stats explanation
   - How to earn XP

Output as JSON with keys for each tooltip.
Vietnamese language, concise (max 2 sentences each)."
```

---

## 📊 EXECUTION CHECKLIST

### Phase 1 Checklist
- [ ] Task 1.1: FloatingNavbar simplification (Codex)
- [ ] Task 1.2: /achievements page creation (Codex)
- [ ] Task 1.3: Navigation translations (Gemini)
- [ ] Task 1.4: Progress Stepper component (Codex)

### Phase 2 Checklist
- [ ] Task 2.1: Tab system UX spec (Gemini)
- [ ] Task 2.2: Tabbed LessonSidebar (Codex)
- [ ] Task 2.3: QuizPanel component (Codex)
- [ ] Task 2.4: Smart Homepage (Codex)
- [ ] Task 2.5: Homepage content (Gemini)

### Phase 3 Checklist
- [ ] Task 3.1: Dashboard → Profile redirect (Codex)
- [ ] Task 3.2: Deprecate motif pages (Codex)
- [ ] Task 3.3: Onboarding content update (Gemini)
- [ ] Task 3.4: Consistent card styling (Codex)
- [ ] Task 3.5: Tooltip content (Gemini)

---

## 🔧 EXECUTION COMMANDS

### Run Codex Tasks
```bash
# Phase 1
codex "Task 1.1 prompt here..."
codex "Task 1.2 prompt here..."
codex "Task 1.4 prompt here..."

# Phase 2
codex "Task 2.2 prompt here..."
codex "Task 2.3 prompt here..."
codex "Task 2.4 prompt here..."

# Phase 3
codex "Task 3.1 prompt here..."
codex "Task 3.2 prompt here..."
codex "Task 3.4 prompt here..."
```

### Run Gemini Tasks
```bash
# Phase 1
gemini -m gemini-2.5-pro-preview-05-06 "Task 1.3 prompt here..."

# Phase 2
gemini -m gemini-2.5-pro-preview-05-06 "Task 2.1 prompt here..."
gemini -m gemini-2.5-pro-preview-05-06 "Task 2.5 prompt here..."

# Phase 3
gemini -m gemini-2.5-pro-preview-05-06 "Task 3.3 prompt here..."
gemini -m gemini-2.5-pro-preview-05-06 "Task 3.5 prompt here..."
```

---

## 📝 NOTES

### Dependencies
- Task 2.2 depends on Task 2.1 (need UX spec before implementation)
- Task 2.3 depends on Task 2.2 (QuizPanel is part of tabbed sidebar)
- Task 3.2 depends on Task 2.2 (need working sidebar before deprecating pages)

### Testing Requirements
After each phase:
1. Run `npm run build` to check for errors
2. Test on mobile viewport
3. Test authentication flow
4. Verify Vietnamese text displays correctly

### Rollback Plan
Keep original files with `.backup` extension until all phases complete successfully.

