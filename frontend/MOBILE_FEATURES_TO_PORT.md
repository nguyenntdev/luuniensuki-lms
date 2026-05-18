# Mobile Features to Port to Web Frontend

## Executive Summary

This document analyzes the gamification and interactive features present in the Luuniensuki LMS mobile app (Flutter) that need to be ported to the web frontend (Next.js/React). The mobile app has extensive gamification systems that significantly enhance user engagement.

**Key Findings:**
- **Hearts System**: Fully implemented in mobile + backend API ready → **P0 (Critical)**
- **Gems System**: Fully implemented in mobile, client-side only → **P0 (Critical)**
- **Leaderboard**: Basic web implementation exists, needs enhancement → **P1 (High)**
- **Achievements/Badges**: Basic web implementation exists, needs unlock notifications → **P1 (High)**
- **Profile Gamification Hub**: Missing from web → **P1 (High)**
- **3D Viewer Enhancements**: Missing gesture hints, zoom indicator → **P2 (Medium)**

---

## 1. Hearts System [P0 - Critical]

### Mobile Implementation
- **Location**: `mobile/lib/features/hearts/`
- **State Management**: Riverpod with AsyncNotifier pattern
- **Persistence**: Hive for local storage
- **Key Files**:
  - `domain/entities/heart_state.dart` - Freezed entity with max_hearts (5), refill timer
  - `presentation/providers/hearts_provider.dart` - Auto-refill timer every 30 mins
  - `presentation/widgets/hearts_display.dart` - 5 heart icons with countdown timer
  - `presentation/screens/hearts_refill_screen.dart` - Refill options modal

### Features to Port
| Feature | Mobile | Web | Status |
|---------|--------|-----|--------|
| Hearts display (5 icons) | ✅ | ❌ | Missing |
| Countdown timer | ✅ | ❌ | Missing |
| Heart deduction on wrong answer | ✅ | ❌ | Missing |
| Refill with gems | ✅ | ❌ | Missing |
| Watch ad for heart | ✅ | ❌ | Missing |
| Streak freeze for hearts | ✅ | ❌ | Missing |

### Backend API Endpoints (READY ✅)
```
GET  /api/v1/hearts                    - Get current hearts status
POST /api/v1/hearts/use                - Use a heart (wrong answer)
POST /api/v1/hearts/refill             - Refill hearts (purchase/ad/reward)
POST /api/v1/hearts/use-streak-freeze  - Use streak freeze to restore all
GET  /api/v1/hearts/transactions       - Get transaction history
```

### Suggested Web Components
```
frontend/src/components/hearts/
├── HeartsDisplay.jsx          - 5 heart icons with current count
├── HeartsCountdownTimer.jsx   - Time until next refill
├── HeartsRefillModal.jsx      - Modal with refill options
├── HeartLostAnimation.jsx     - Animation when heart is lost
└── NoHeartsOverlay.jsx        - Overlay when hearts = 0

frontend/src/stores/heartsStore.js  - Zustand store for hearts state
frontend/src/hooks/useHearts.js     - Custom hook for hearts logic
```

---

## 2. Gems System [P0 - Critical]

### Mobile Implementation
- **Location**: `mobile/lib/features/gems/`
- **State Management**: Riverpod
- **Persistence**: Hive (client-side only, no backend sync)
- **Key Files**:
  - `domain/entities/gem_transaction.dart` - Transaction types enum
  - `presentation/providers/gems_provider.dart` - addGems(), spendGems(), canAfford()
  - `presentation/widgets/gems_display.dart` - Animated gem counter with scale effect
  - `presentation/screens/gems_shop_screen.dart` - Shop with purchasable items

### Gem Economy
| Action | Gems |
|--------|------|
| Complete lesson | +10 |
| Daily goal achieved | +20 |
| Perfect quiz score | +25 |
| Streak milestone (7 days) | +50 |
| Streak freeze purchase | -50 |
| Double XP boost | -100 |
| Quiz hint (remove 2 answers) | -5 |
| Heart refill | -25 |

### Features to Port
| Feature | Mobile | Web | Status |
|---------|--------|-----|--------|
| Gem balance display | ✅ | ❌ | Missing |
| Animated gem counter | ✅ | ❌ | Missing |
| Gems shop | ✅ | ❌ | Missing |
| Transaction history | ✅ | ❌ | Missing |
| Purchase items with gems | ✅ | ❌ | Missing |
| Quiz hints with gems | ✅ | ❌ | Missing |

### Backend API Status
**⚠️ NO BACKEND API** - Mobile uses client-side storage only.

**Recommendation**: Either:
1. Create backend Gems API (sync across devices) - Preferred
2. Use localStorage/IndexedDB (web-only, no sync)

### Suggested Web Components
```
frontend/src/components/gems/
├── GemsDisplay.jsx            - Animated gem balance in header
├── GemsShopModal.jsx          - Shop with purchasable items
├── GemTransactionToast.jsx    - Toast notification for gem changes
├── GemPurchaseConfirm.jsx     - Confirmation dialog for purchases
└── GemsHistoryPanel.jsx       - Transaction history

frontend/src/stores/gemsStore.js  - Zustand store for gems
```

---

## 3. Leaderboard [P1 - High Priority]

### Current Web State
- **Location**: `frontend/src/app/leaderboard/page.jsx`
- **API Used**: `GET /api/v1/leaderboard?limit=50`
- Basic table display exists but lacks mobile features

### Mobile Features Missing in Web
| Feature | Mobile | Web | Status |
|---------|--------|-----|--------|
| Global leaderboard | ✅ | ✅ | Exists |
| Current user highlighting | ✅ | ❌ | Missing |
| User rank badge/title | ✅ | ❌ | Missing |
| Friends leaderboard tab | ✅ | ❌ | Missing |
| Weekly/All-time toggle | ✅ | ❌ | Missing |
| Animated rank changes | ✅ | ❌ | Missing |

### Backend API Endpoints (READY ✅)
```
GET /api/v1/leaderboard              - Global leaderboard
GET /api/v1/leaderboard/friends      - Friends only (if implemented)
```

### Suggested Enhancements
```
frontend/src/components/leaderboard/
├── LeaderboardTable.jsx       - Enhanced table with user highlight
├── LeaderboardTabs.jsx        - Global/Friends/Weekly tabs
├── RankBadge.jsx              - Visual rank badge (Gold/Silver/Bronze)
├── UserRankCard.jsx           - Current user's rank summary
└── LeaderboardSkeleton.jsx    - Loading skeleton
```

---

## 4. Achievements & Badges [P1 - High Priority]

### Current Web State
- **Location**: `frontend/src/app/achievements/page.jsx`
- Basic badges grid and leaderboard tabs exist
- API calls: `getAllBadges()`, `getMyBadges()`

### Mobile Features Missing in Web
| Feature | Mobile | Web | Status |
|---------|--------|-----|--------|
| Badge grid display | ✅ | ✅ | Exists (basic) |
| Badge unlock notification | ✅ | ❌ | Missing |
| Badge detail modal | ✅ | ❌ | Missing |
| Badge categories filter | ✅ | ❌ | Missing |
| Badge progress indicators | ✅ | ❌ | Missing |
| Celebration animation on unlock | ✅ | ❌ | Missing |

### Backend API Endpoints (READY ✅)
```
GET /api/v1/badges              - Get all available badges
GET /api/v1/users/me/badges     - Get user's earned badges
```

### Suggested Enhancements
```
frontend/src/components/badges/
├── BadgeGrid.jsx              - Enhanced grid with categories
├── BadgeCard.jsx              - Individual badge with progress
├── BadgeDetailModal.jsx       - Detailed badge info on click
├── BadgeUnlockToast.jsx       - Toast when badge unlocked
├── BadgeCelebration.jsx       - Full-screen celebration animation
└── BadgeCategoryFilter.jsx    - Category tabs (achievement/streak/mastery)
```

---

## 5. Profile & Gamification Hub [P1 - High Priority]

### Current Web State
- **Location**: `frontend/src/app/profile/page.jsx`, `frontend/src/components/UserProfile.js`
- Basic stats display exists (rank, XP, streak, badges count)
- Missing the gamification "hub" feel from mobile

### Mobile Features Missing in Web
| Feature | Mobile | Web | Status |
|---------|--------|-----|--------|
| XP progress bar (to next level) | ✅ | ✅ | Exists (basic) |
| Streak calendar (7-day view) | ✅ | ❌ | Missing |
| Streak freeze badges display | ✅ | ❌ | Missing |
| Gamification hub section | ✅ | ❌ | Missing |
| Daily goal progress | ✅ | ❌ | Missing |
| Level/Title display | ✅ | ❌ | Missing |
| Stats grid (detailed) | ✅ | ❌ | Missing |

### Backend API Endpoints (READY ✅)
```
GET /api/v1/users/me/streak     - Get streak data
GET /api/v1/auth/me             - Get user profile with XP
GET /api/v1/dashboard/summary   - Dashboard stats
```

### Suggested Components
```
frontend/src/components/profile/
├── XpProgressBar.jsx          - Visual XP bar with level
├── StreakCalendar.jsx         - 7-day streak view
├── StreakFreezeDisplay.jsx    - Streak freeze count
├── GamificationHub.jsx        - Links to achievements, leaderboard
├── DailyGoalProgress.jsx      - Today's goal completion
├── StatsGrid.jsx              - Detailed statistics
└── LevelBadge.jsx             - Current level/title badge
```

---

## 6. Interactive 3D Viewer Enhancements [P2 - Medium Priority]

### Current Web State
- **Location**: `frontend/src/components/UrnViewer.js`
- 3D model rendering with Three.js/React Three Fiber
- OrbitControls for rotation/zoom
- Hotspots for motifs

### Mobile Features Missing in Web
| Feature | Mobile | Web | Status |
|---------|--------|-----|--------|
| 3D model display | ✅ | ✅ | Exists |
| Hotspots/motif markers | ✅ | ✅ | Exists |
| Camera controls | ✅ | ✅ | Exists |
| Gesture hints overlay | ✅ | ❌ | Missing |
| Zoom level indicator | ✅ | ❌ | Missing |
| Camera reset button | ✅ | ❌ | Missing |
| AR mode button | ✅ | ❌ | N/A for web |
| Loading progress bar | ✅ | ✅ | Exists |

### Suggested Enhancements
```
frontend/src/components/viewer/
├── GestureHintsOverlay.jsx    - First-time touch/mouse instructions
├── ZoomIndicator.jsx          - Current zoom level display
├── CameraResetButton.jsx      - Reset to default view button
├── ViewerControls.jsx         - Control panel (zoom/rotate buttons)
└── ViewerTouchInstructions.jsx - Touch device instructions
```

---

## 7. Priority Matrix Summary

### P0 - Critical (Must Have)
| Feature | Effort | Impact | Dependencies |
|---------|--------|--------|--------------|
| Hearts System | High | Very High | Backend API ready |
| Gems System | High | Very High | Need backend API |
| Hearts integration in Quiz | Medium | Very High | Hearts System |

### P1 - High Priority (Should Have)
| Feature | Effort | Impact | Dependencies |
|---------|--------|--------|--------------|
| Leaderboard enhancements | Medium | High | None |
| Badge unlock notifications | Low | High | XP celebration exists |
| Profile gamification hub | Medium | High | None |
| Streak calendar | Low | Medium | Streak API ready |

### P2 - Medium Priority (Nice to Have)
| Feature | Effort | Impact | Dependencies |
|---------|--------|--------|--------------|
| 3D viewer gesture hints | Low | Low | None |
| Zoom indicator | Low | Low | None |
| Camera reset button | Low | Low | None |

---

## 8. Implementation Recommendations

### Phase 1: Core Gamification (2-3 weeks)
1. Create `heartsStore.js` with Zustand
2. Implement `HeartsDisplay.jsx` component
3. Integrate hearts with quiz submission
4. Create `gemsStore.js` (consider backend API)
5. Implement `GemsDisplay.jsx` in header

### Phase 2: Enhanced Engagement (1-2 weeks)
1. Enhance leaderboard with user highlighting
2. Add badge unlock notifications
3. Create profile gamification hub
4. Implement streak calendar

### Phase 3: Polish (1 week)
1. Add 3D viewer gesture hints
2. Implement zoom indicator
3. Add camera reset button
4. Animation polish

### Technical Considerations
- **State Management**: Use Zustand (already in use)
- **API Integration**: Existing `apiRequest` helper in `lib/api.js`
- **Styling**: Tailwind CSS (consistent with existing)
- **Animations**: Framer Motion recommended

---

## 9. API Endpoints Summary

### Available (Backend Ready) ✅
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/hearts` | GET | Get hearts status |
| `/api/v1/hearts/use` | POST | Use a heart |
| `/api/v1/hearts/refill` | POST | Refill hearts |
| `/api/v1/hearts/use-streak-freeze` | POST | Use streak freeze |
| `/api/v1/leaderboard` | GET | Global leaderboard |
| `/api/v1/badges` | GET | All badges |
| `/api/v1/users/me/badges` | GET | User's badges |
| `/api/v1/users/me/streak` | GET | Streak data |

### Needed (Backend Implementation Required) ⚠️
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/gems` | GET | Get gems balance |
| `/api/v1/gems/transactions` | GET | Gems history |
| `/api/v1/gems/spend` | POST | Spend gems |
| `/api/v1/gems/earn` | POST | Earn gems |

---

*Document generated: Analysis of mobile app features for web porting*
*Last updated: Based on current codebase state*
