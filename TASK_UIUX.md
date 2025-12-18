# 🎨 UI/UX IMPROVEMENT TASK - Imperial Vietnamese Heritage Theme

## 📋 OVERVIEW

Migrate LMS from generic light theme to **Imperial Vietnamese Heritage** dark theme matching reference website at `/root/luuniensuki/`.

**Assignees:**
- **GEMINI**: Phase A, B, C, D (Frontend - 90% of work)
- **CODEX**: Phase E (Backend verification - 10%)
- **AUGMENT**: Phase F (Testing & validation)

---

## 🎯 PHASE A: THEME MIGRATION (GEMINI)

### A.1 Update `frontend/tailwind.config.js`

**Reference:** `/root/luuniensuki/tailwind.config.ts`

Add these configurations:

```javascript
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        // Heritage colors
        jade: "hsl(var(--jade-green))",
        bronze: "hsl(var(--bronze))",
        ivory: "hsl(var(--ivory))",
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Be Vietnam Pro', 'Inter', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(1.15)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
      animation: {
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "float": "float 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
```

### A.2 Update `frontend/src/app/globals.css`

**Reference:** `/root/luuniensuki/src/index.css`

Add CSS variables and utilities. Copy the `:root` block with all CSS custom properties:

```css
@layer base {
  :root {
    --background: 222 47% 6%;
    --foreground: 43 20% 96%;
    --card: 222 40% 8%;
    --card-foreground: 43 20% 96%;
    --primary: 43 74% 49%;
    --primary-foreground: 222 47% 11%;
    --secondary: 222 35% 12%;
    --secondary-foreground: 43 20% 96%;
    --muted: 222 30% 15%;
    --muted-foreground: 43 15% 75%;
    --accent: 0 72% 51%;
    --accent-foreground: 43 20% 96%;
    --border: 222 30% 18%;
    --input: 222 30% 18%;
    --ring: 43 74% 49%;
    --radius: 0.75rem;
    --imperial-gold: 43 74% 49%;
    --imperial-red: 0 72% 51%;
    --deep-navy: 222 47% 6%;
    --jade-green: 160 45% 35%;
    --bronze: 25 60% 40%;
    --ivory: 43 30% 92%;
  }
}
```

Add utility classes:
- `.text-gradient-gold` - Gold gradient text
- `.glow-gold` - Gold text shadow
- `.hover-lift` - Card hover effect
- `.pattern-thuy-ba` - Vietnamese wave pattern

### A.3 Update `frontend/src/app/layout.jsx`

Change body classes from:
```jsx
<body className="min-h-dvh bg-white text-gray-900">
```
To:
```jsx
<body className="min-h-dvh bg-background text-foreground">
```

### A.4 Replace indigo-* colors

Search and replace in ALL components:
- `indigo-600` → `primary`
- `indigo-500` → `primary`
- `indigo-400` → `primary/80`
- `bg-white` → `bg-card` or `bg-background`
- `text-gray-900` → `text-foreground`
- `text-gray-600` → `text-muted-foreground`
- `border-gray-200` → `border-border`

**Files to update:**
- `frontend/src/components/Navbar.jsx`
- `frontend/src/components/UrnViewer.js`
- `frontend/src/components/LoginPage.js`
- `frontend/src/app/page.jsx`
- `frontend/src/app/collection/page.jsx`
- `frontend/src/app/motif/[motifId]/page.jsx`
- `frontend/src/app/leaderboard/page.jsx`
- `frontend/src/app/badges/page.jsx`

---

## 🧭 PHASE B: NAVIGATION REDESIGN (GEMINI)

### B.1 Create FloatingNavbar component

**Reference:** `/root/luuniensuki/src/components/Navbar.tsx`

Create `frontend/src/components/FloatingNavbar.jsx`:

**Features:**
- Fixed bottom position with glass morphism effect
- 5 nav items with icons: Home (🏠), Cửu Đỉnh (🏛️), Collection (📚), Leaderboard (🏆), Profile (👤)
- Active state with gold underline
- Responsive: hide on mobile scroll down, show on scroll up

**Example structure:**
```jsx
<nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/80 backdrop-blur-lg">
  <div className="mx-auto flex max-w-7xl items-center justify-around px-4 py-3">
    <Link href="/" className="flex flex-col items-center gap-1 text-xs">
      <span className="text-2xl">🏠</span>
      <span className="text-muted-foreground">Home</span>
    </Link>
    {/* ... other nav items */}
  </div>
</nav>
```

### B.2 Update layout.jsx

Replace `<Navbar />` with `<FloatingNavbar />`. Add bottom padding to main content:

```jsx
<body className="min-h-dvh bg-background text-foreground pb-20">
```

### B.3 Mobile responsiveness

Add scroll detection to hide/show navbar on mobile. Use `useState` + `useEffect` with scroll listener.

---

## 📚 PHASE C: ENRICHED CONTENT DISPLAY (GEMINI)

Update `frontend/src/app/motif/[motifId]/page.jsx` to display enriched fields.

### C.1 Historical Context Section

Add expandable section after main description:

```jsx
{motif.historical_context && (
  <div className="mt-6 rounded-lg border border-border bg-card p-4">
    <h3 className="flex items-center gap-2 text-lg font-semibold">
      <span>📖</span> Historical Context
    </h3>
    <p className="mt-2 text-sm text-muted-foreground">{motif.historical_context}</p>
  </div>
)}
```

### C.2 Symbolism Section

```jsx
{motif.symbolism && (
  <div className="mt-4 rounded-lg border border-border bg-card p-4">
    <h3 className="flex items-center gap-2 text-lg font-semibold">
      <span>🔮</span> Symbolism
    </h3>
    <p className="mt-2 text-sm text-muted-foreground">{motif.symbolism}</p>
  </div>
)}
```

### C.3 Fun Fact Highlight Card

```jsx
{motif.fun_fact && (
  <div className="mt-4 rounded-lg border-2 border-primary/30 bg-primary/5 p-4">
    <h3 className="flex items-center gap-2 text-lg font-semibold text-primary">
      <span>⭐</span> Fun Fact
    </h3>
    <p className="mt-2 text-sm">{motif.fun_fact}</p>
  </div>
)}
```

### C.4 Quiz Explanation Display

Update `frontend/src/app/motif/[motifId]/quiz/page.jsx`:

After user submits answer, show explanation:

```jsx
{submitted && currentQuestion.explanation && (
  <div className={`mt-4 rounded-lg p-4 ${isCorrect ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
    <p className="text-sm font-medium">{isCorrect ? '✅ Correct!' : '❌ Incorrect'}</p>
    <p className="mt-2 text-sm text-muted-foreground">{currentQuestion.explanation}</p>
  </div>
)}
```

### C.5 Improve Lesson Page Layout

Restructure page with better visual hierarchy:
1. Hero image (if available)
2. Title + metadata (category, rarity)
3. Main description
4. Historical context (expandable)
5. Symbolism
6. Fun fact (highlighted)
7. Action buttons (Take Quiz, Complete Lesson)

---

## 🏠 PHASE D: HOMEPAGE & UX FLOW (GEMINI)

### D.1 Redesign Homepage

Update `frontend/src/app/page.jsx`:

**New structure:**
```jsx
<main className="flex min-h-screen items-center justify-center px-6">
  <div className="text-center">
    <h1 className="text-5xl font-serif font-bold text-gradient-gold">
      Lưu Niên Sử Kí
    </h1>
    <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
      Explore the Nine Dynastic Urns (Cửu Đỉnh) and unlock motifs to learn Vietnamese heritage.
    </p>
    <div className="mt-8 flex gap-4 justify-center">
      <Link href="/explore" className="rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground hover:bg-primary/90">
        Start Learning
      </Link>
      <Link href="/collection" className="rounded-lg border border-border px-6 py-3 font-medium hover:bg-card">
        View Collection
      </Link>
    </div>
  </div>
</main>
```

Remove redundant links (Dashboard, Leaderboard, Badges) - they're in navbar now.

### D.2 Onboarding Flow (Optional)

Add first-time user modal explaining Cửu Đỉnh. Use localStorage to track if user has seen it.

---

## 🔧 PHASE E: BACKEND VERIFICATION (CODEX)

### E.1 Verify API returns enriched fields

Check `backend/main.py` endpoint `GET /motifs/{motif_id}`:

Ensure response includes:
- `historical_context`
- `symbolism`
- `fun_fact`
- `quiz_questions[].explanation`

If missing, update the endpoint to include these fields from database.

---

## ✅ PHASE F: TESTING & VALIDATION (AUGMENT)

### F.1 Run seed with enriched data

```bash
cd /root/luuniensuki-lms
docker compose down -v
docker compose up -d db
docker compose exec db psql -U postgres -d luuniensuki -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python3 backend/seed.py
```

### F.2 Manual UI testing

1. Visit homepage - check dark theme, hero section
2. Click "Start Learning" - check explore page
3. Open 3D viewer - check colors match theme
4. View motif lesson - check enriched content sections display
5. Take quiz - check explanation shows after answer
6. Check navbar - floating bottom, icons, active states

### F.3 Quiz flow testing

1. Start quiz for any motif
2. Answer questions (both correct and incorrect)
3. Verify explanation displays after each answer
4. Check styling (green for correct, red for incorrect)

### F.4 Deploy to production

```bash
cd /root/luuniensuki-lms
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 📊 ACCEPTANCE CRITERIA

- [ ] Dark theme applied across all pages
- [ ] Imperial gold/navy colors replace indigo
- [ ] Floating bottom navbar with icons
- [ ] Homepage simplified to hero + 2 CTAs
- [ ] Motif lesson page displays historical_context, symbolism, fun_fact
- [ ] Quiz shows explanation after answer
- [ ] All pages responsive on mobile
- [ ] No console errors
- [ ] Backend returns all enriched fields

---

## 🚀 RUN COMMANDS

**Start dev server:**
```bash
cd /root/luuniensuki-lms
docker compose up -d
```

**View logs:**
```bash
docker compose logs -f web
```

**Test API:**
```bash
curl http://localhost:8000/motifs/1 | jq
```

---

## 📝 NOTES

- **GEMINI**: Focus on frontend. Use reference files from `/root/luuniensuki/` for design patterns.
- **CODEX**: Quick backend check. Should be minimal work since enriched fields already in database.
- **AUGMENT**: Final validation. Report any issues found during testing.

**Priority:** GEMINI > CODEX > AUGMENT (to save Augment credits)
