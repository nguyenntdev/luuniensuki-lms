# Hearts System - Web Frontend

This directory contains the Hearts gamification system for the web frontend, matching the mobile app implementation.

## Overview

The Hearts system is a gamification feature that:
- Limits quiz attempts with a 5-heart system
- Automatically refills 1 heart every 4 hours
- Allows users to refill hearts with gems, streak freezes, or ads
- Shows countdown timer for next heart refill
- Displays current hearts status with animated icons

## Files

### `heartsStore.js`
Zustand store for hearts state management.

**State:**
- `hearts`: Current hearts count (0-5)
- `maxHearts`: Maximum hearts (default: 5)
- `nextRefillAt`: ISO timestamp for next auto-refill
- `unlimitedUntil`: ISO timestamp for unlimited hearts period
- `isLoading`: Loading state for API calls
- `error`: Error message if any

**Actions:**
- `fetchHearts()`: Fetch current hearts status from API
- `useHeart(reason, metadata)`: Use a heart (deduct 1)
- `refillHearts(type)`: Refill hearts via gems/ad/reward
- `useStreakFreeze()`: Use streak freeze to restore all hearts
- `isUnlimited()`: Check if user has unlimited hearts

### `HeartsDisplay.jsx`
Display component showing 5 heart icons with current count and countdown timer.

**Props:**
- `showLabel` (boolean, default: true): Show "X/5" label
- `showTimer` (boolean, default: true): Show countdown timer
- `size` (string, default: "md"): Icon size (not fully implemented)
- `onClick` (function, optional): Click handler for opening refill modal

**Features:**
- Animated heart icons (filled/empty states)
- Countdown timer showing time until next refill
- "Unlimited" badge when user has unlimited hearts
- Auto-fetches hearts status on mount

### `HeartsRefillModal.jsx`
Modal for refilling hearts when user runs out.

**Props:**
- `isOpen` (boolean): Control modal visibility
- `onClose` (function): Close handler
- `onSuccess` (function): Success callback after refill

**Features:**
- Refill with gems (350 gems for full refill)
- Use streak freeze to restore all hearts
- Wait for auto-refill option
- Loading states and error handling
- Keyboard support (ESC to close)

## Usage Examples

### Basic Hearts Display (in Navbar)

\`\`\`jsx
import { HeartsDisplay } from "@/components/hearts";

function Navbar() {
  return (
    <nav>
      <HeartsDisplay />
    </nav>
  );
}
\`\`\`

### Hearts Display with Refill Modal

\`\`\`jsx
import { useState } from "react";
import { HeartsDisplay, HeartsRefillModal } from "@/components/hearts";

function GameSection() {
  const [showRefillModal, setShowRefillModal] = useState(false);

  return (
    <>
      <HeartsDisplay onClick={() => setShowRefillModal(true)} />
      
      <HeartsRefillModal
        isOpen={showRefillModal}
        onClose={() => setShowRefillModal(false)}
        onSuccess={(result) => {
          console.log("Hearts refilled:", result);
          setShowRefillModal(false);
        }}
      />
    </>
  );
}
\`\`\`

### Using Hearts Store Directly

\`\`\`jsx
import useHeartsStore from "@/stores/heartsStore";

function QuizComponent() {
  const hearts = useHeartsStore((state) => state.hearts);
  const useHeart = useHeartsStore((state) => state.useHeart);

  const handleWrongAnswer = async () => {
    if (hearts <= 0) {
      // Show refill modal
      return;
    }

    try {
      await useHeart("quiz_wrong", { quiz_id: "123", question_id: "456" });
      // Continue with quiz logic
    } catch (error) {
      console.error("Failed to use heart:", error);
    }
  };

  return (
    <div>
      <p>Hearts remaining: {hearts}</p>
      <button onClick={handleWrongAnswer}>Submit Answer</button>
    </div>
  );
}
\`\`\`

### Checking Hearts Before Quiz

\`\`\`jsx
import useHeartsStore from "@/stores/heartsStore";

function QuizGuard({ children }) {
  const hearts = useHeartsStore((state) => state.hearts);
  const isUnlimited = useHeartsStore((state) => state.isUnlimited);

  if (!isUnlimited() && hearts <= 0) {
    return <NoHeartsOverlay />;
  }

  return children;
}
\`\`\`

## API Integration

The hearts system integrates with these backend endpoints:

- `GET /api/v1/hearts` - Get current hearts status
- `POST /api/v1/hearts/use` - Use a heart (body: `{reason, metadata}`)
- `POST /api/v1/hearts/refill` - Refill hearts (body: `{refill_type: "gems"|"ad"|"reward"}`)
- `POST /api/v1/hearts/use-streak-freeze` - Use streak freeze to restore all hearts

## Styling

All components use Tailwind CSS with project design tokens:
- Heart icons: `text-red-500 fill-red-500` (filled), `text-gray-400 fill-gray-300` (empty)
- Animations: Smooth transitions with staggered delays
- Modal: Backdrop blur, elegant shadows, gradient overlays

## Future Enhancements

- [ ] Heart lost animation when user gets answer wrong
- [ ] No hearts overlay component for quiz blocking
- [ ] Sound effects for heart loss/gain
- [ ] Confetti animation on heart refill
- [ ] Integration with quiz components
- [ ] Analytics tracking for heart usage

