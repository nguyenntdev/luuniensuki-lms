# Gems System Integration Checklist

## ✅ Files Created (6 files, 721 lines)

### Store
- [x] `frontend/src/stores/gemsStore.js` - Zustand store with persistence

### Components  
- [x] `frontend/src/components/gems/GemsDisplay.jsx` - Animated counter
- [x] `frontend/src/components/gems/GemsShopModal.jsx` - Shop modal
- [x] `frontend/src/components/gems/Example.jsx` - Usage examples
- [x] `frontend/src/components/gems/index.js` - Exports
- [x] `frontend/src/components/gems/README.md` - Documentation

## 🔧 Integration Steps

### Step 1: Add to Navigation Bar
**File:** `frontend/src/components/FloatingNavbar.jsx` (or main navbar)

```jsx
import { useState } from "react";
import { GemsDisplay, GemsShopModal } from "@/components/gems";

export default function FloatingNavbar() {
  const [shopOpen, setShopOpen] = useState(false);

  return (
    <nav>
      {/* Existing nav items */}
      
      {/* Add GemsDisplay */}
      <GemsDisplay onClick={() => setShopOpen(true)} />
      
      {/* Add Shop Modal */}
      <GemsShopModal
        isOpen={shopOpen}
        onClose={() => setShopOpen(false)}
      />
    </nav>
  );
}
```

### Step 2: Award Gems on Lesson Completion
**File:** Where lessons are completed

```jsx
import useGemsStore, { GEM_AMOUNTS } from "@/stores/gemsStore";
import toast from "react-hot-toast";

const addGems = useGemsStore((state) => state.addGems);

function onLessonComplete() {
  // Existing completion logic...
  
  // Award gems
  const newBalance = addGems(
    GEM_AMOUNTS.COMPLETE_LESSON,
    "Completed lesson"
  );
  
  toast.success(`+${GEM_AMOUNTS.COMPLETE_LESSON} gems! 💎`, {
    duration: 2000,
  });
}
```

### Step 3: Award Gems on Perfect Quiz
**File:** `frontend/src/app/motif/[motifId]/quiz/page.jsx` (or quiz submission)

```jsx
import useGemsStore, { GEM_AMOUNTS } from "@/stores/gemsStore";

const addGems = useGemsStore((state) => state.addGems);

async function handleSubmit() {
  // Existing quiz submission...
  
  if (res.passed && res.score === res.max_score) {
    // Perfect score
    addGems(GEM_AMOUNTS.PERFECT_QUIZ, "Perfect quiz score");
    toast.success(`Perfect! +${GEM_AMOUNTS.PERFECT_QUIZ} gems! ✨💎`);
  } else if (res.passed) {
    // Just passed
    const partialGems = Math.floor(GEM_AMOUNTS.PERFECT_QUIZ / 2);
    addGems(partialGems, "Completed quiz");
    toast.success(`+${partialGems} gems! 💎`);
  }
}
```

### Step 4: Daily Goal Gems (Optional)
**File:** Where daily progress is tracked

```jsx
import useGemsStore, { GEM_AMOUNTS } from "@/stores/gemsStore";

const addGems = useGemsStore((state) => state.addGems);

function checkDailyGoal(totalXpToday) {
  const DAILY_GOAL_XP = 100; // Adjust as needed
  
  if (totalXpToday >= DAILY_GOAL_XP) {
    addGems(GEM_AMOUNTS.DAILY_GOAL, "Reached daily goal");
    toast.success(`Daily goal reached! +${GEM_AMOUNTS.DAILY_GOAL} gems! 🎯💎`);
  }
}
```

### Step 5: Streak Bonus (Optional)
**File:** Where streaks are tracked

```jsx
import useGemsStore, { GEM_AMOUNTS } from "@/stores/gemsStore";

const addGems = useGemsStore((state) => state.addGems);

function checkStreakBonus(streakDays) {
  if (streakDays === 7) {
    addGems(GEM_AMOUNTS.STREAK_7_DAYS, "7 day streak bonus");
    toast.success(
      `7 day streak! +${GEM_AMOUNTS.STREAK_7_DAYS} gems! 🔥💎`,
      { duration: 4000 }
    );
  }
}
```

## 🎯 Shop Items Already Integrated

The shop modal already has integration points for:

1. ✅ **Heart Refill** - Calls `refillHearts("gems")` from heartsStore
2. ✅ **Streak Freeze** - Ready for backend integration
3. ✅ **Quiz Hint** - Ready for quiz system integration
4. ✅ **Double XP** - Ready for XP system integration

### Extending Shop Integration

To add backend calls for other items, edit `GemsShopModal.jsx`:

```jsx
const handlePurchase = async (item) => {
  // ... existing code ...
  
  try {
    // Add more item handlers
    if (item.id === "heart_refill") {
      await refillHearts("gems");
    } else if (item.id === "streak_freeze") {
      // Add your streak freeze API call
      await apiRequest("/api/v1/streaks/freeze", { method: "POST" });
    } else if (item.id === "quiz_hint") {
      // Store hint purchase for next quiz
      // This might be handled differently
    } else if (item.id === "double_xp") {
      // Add your double XP API call
      await apiRequest("/api/v1/boosts/double-xp", { method: "POST" });
    }
    
    // ... rest of existing code ...
  }
}
```

## 📱 UI Placement Suggestions

### Option 1: Top Navigation Bar (Recommended)
```
┌─────────────────────────────────────────┐
│ [Logo] [Nav] [Hearts ❤️] [Gems 💎] [User] │
└─────────────────────────────────────────┘
```

### Option 2: Floating Action Button
```jsx
<div className="fixed bottom-6 right-6 z-50">
  <GemsDisplay
    size="lg"
    onClick={() => setShopOpen(true)}
  />
</div>
```

### Option 3: Profile/Stats Panel
```jsx
<div className="stats-panel">
  <HeartsDisplay />
  <GemsDisplay onClick={() => setShopOpen(true)} />
  <XpDisplay />
</div>
```

## 🧪 Testing Procedures

### Manual Testing
1. [ ] Click GemsDisplay to open shop
2. [ ] Try to purchase with insufficient gems (should show error)
3. [ ] Purchase heart refill (should work)
4. [ ] Check localStorage for persistence
5. [ ] Reload page, verify gems persist
6. [ ] Award gems via actions, verify animation
7. [ ] Press ESC to close modal
8. [ ] Click backdrop to close modal

### Automated Testing (Optional)
```jsx
// Example test
import { render, screen, fireEvent } from '@testing-library/react';
import { GemsDisplay } from '@/components/gems';

test('GemsDisplay shows correct balance', () => {
  render(<GemsDisplay />);
  expect(screen.getByText(/100/)).toBeInTheDocument();
});
```

## 📊 Monitoring & Analytics (Optional)

Track gem economy:

```jsx
import useGemsStore from "@/stores/gemsStore";

function trackGemTransaction(amount, reason) {
  // Send to analytics
  if (window.gtag) {
    window.gtag('event', 'gem_transaction', {
      amount,
      reason,
      balance: useGemsStore.getState().gems,
    });
  }
}
```

## 🔍 Troubleshooting

### Issue: Gems not persisting
**Solution:** Check browser localStorage is enabled

### Issue: Animation not working
**Solution:** Verify Tailwind CSS animation classes are available

### Issue: Shop modal not closing
**Solution:** Check z-index conflicts with other modals

### Issue: Heart refill not working
**Solution:** Verify heartsStore is properly initialized

## ✨ Enhancement Ideas

1. **Gem History Modal** - Show transaction history
2. **Gem Packages** - Sell gem bundles for real money
3. **Daily Login Bonus** - Award gems for logging in
4. **Achievement Gems** - Bonus gems for achievements
5. **Referral Gems** - Reward for inviting friends
6. **Gem Leaderboard** - Show top gem earners
7. **Seasonal Events** - 2x gems during events
8. **Gem Animations** - More elaborate gem particle effects

## 🎉 Deployment Checklist

- [ ] All files committed to git
- [ ] Integration tested locally
- [ ] GemsDisplay added to navigation
- [ ] Gem awards added to key actions
- [ ] Shop tested with all items
- [ ] localStorage working correctly
- [ ] Mobile responsive verified
- [ ] Accessibility tested
- [ ] Performance verified (no lag)
- [ ] Ready for production deploy

## 📝 Notes

- Starting balance: 100 gems
- LocalStorage key: `luuniensuki-gems-storage`
- Transaction history: Last 50 entries
- All animations: 300ms duration
- Toast notifications: 3-4s duration

**Status:** ✅ Implementation Complete - Ready for Integration

