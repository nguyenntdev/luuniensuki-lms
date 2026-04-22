# Gems System

Gamification system for the web frontend using virtual currency (gems).

## Components

### GemsDisplay
Animated gem counter component for displaying user's gem balance.

**Props:**
- `showLabel` (boolean, default: true) - Show numeric gem count
- `size` ("sm" | "md" | "lg", default: "md") - Size variant
- `onClick` (function, optional) - Click handler, makes component clickable

**Features:**
- Animated scale effect when gem count changes
- Ping animation on gem changes
- Clickable variant for opening shop

**Usage:**
```jsx
import { GemsDisplay } from "@/components/gems";

// Basic usage
<GemsDisplay />

// Clickable variant
<GemsDisplay onClick={() => setShopOpen(true)} />

// Small size without label
<GemsDisplay size="sm" showLabel={false} />
```

### GemsShopModal
Modal component for purchasing items with gems.

**Props:**
- `isOpen` (boolean) - Controls modal visibility
- `onClose` (function) - Close handler
- `onPurchase` (function, optional) - Callback after successful purchase

**Features:**
- Grid layout of purchasable items
- Real-time affordability checking
- Toast notifications for purchases
- Loading states during purchase
- Keyboard (ESC) support
- Body scroll lock when open

**Shop Items:**
1. **Refill Hearts** (25 gems) - Instantly refill all hearts
2. **Streak Freeze** (50 gems) - Protect streak for 1 day
3. **Quiz Hint** (5 gems) - Get hint for quiz questions
4. **Double XP Boost** (100 gems) - 2x XP for 30 minutes

**Usage:**
```jsx
import { GemsShopModal } from "@/components/gems";

function MyComponent() {
  const [shopOpen, setShopOpen] = useState(false);

  return (
    <>
      <button onClick={() => setShopOpen(true)}>Open Shop</button>
      <GemsShopModal
        isOpen={shopOpen}
        onClose={() => setShopOpen(false)}
        onPurchase={(item) => console.log("Purchased:", item)}
      />
    </>
  );
}
```

## Store

### useGemsStore
Zustand store with localStorage persistence.

**State:**
- `gems` (number) - Current gem balance
- `transactions` (array) - Last 50 transactions

**Actions:**
- `addGems(amount, reason)` - Add gems and record transaction
- `spendGems(amount, reason)` - Spend gems (throws if insufficient)
- `canAfford(amount)` - Check if user can afford amount
- `getBalance()` - Get current gem balance
- `reset()` - Reset to initial state (100 gems)

**Constants:**
```javascript
import { GEM_AMOUNTS } from "@/stores/gemsStore";

GEM_AMOUNTS.COMPLETE_LESSON    // 10
GEM_AMOUNTS.PERFECT_QUIZ       // 25
GEM_AMOUNTS.DAILY_GOAL         // 20
GEM_AMOUNTS.STREAK_7_DAYS      // 50
GEM_AMOUNTS.HEART_REFILL       // -25
GEM_AMOUNTS.STREAK_FREEZE      // -50
GEM_AMOUNTS.QUIZ_HINT          // -5
GEM_AMOUNTS.DOUBLE_XP          // -100
```

**Usage:**
```jsx
import useGemsStore, { GEM_AMOUNTS } from "@/stores/gemsStore";

function RewardGems() {
  const addGems = useGemsStore((state) => state.addGems);
  
  const onLessonComplete = () => {
    addGems(GEM_AMOUNTS.COMPLETE_LESSON, "Completed lesson");
  };
}

function PurchaseItem() {
  const spendGems = useGemsStore((state) => state.spendGems);
  
  const onPurchase = () => {
    try {
      spendGems(25, "Heart refill");
    } catch (err) {
      console.error(err.message); // "Insufficient gems"
    }
  };
}
```

## Integration Example

Complete example with GemsDisplay in navbar and shop modal:

```jsx
import { useState } from "react";
import { GemsDisplay, GemsShopModal } from "@/components/gems";

export default function Navbar() {
  const [shopOpen, setShopOpen] = useState(false);

  return (
    <nav>
      <GemsDisplay onClick={() => setShopOpen(true)} />
      
      <GemsShopModal
        isOpen={shopOpen}
        onClose={() => setShopOpen(false)}
      />
    </nav>
  );
}
```

## Persistence

Gems data is persisted to localStorage under key `luuniensuki-gems-storage`.

**Storage format:**
```json
{
  "state": {
    "gems": 150,
    "transactions": [
      {
        "amount": 10,
        "reason": "Completed lesson",
        "timestamp": "2024-01-15T10:30:00.000Z"
      }
    ]
  },
  "version": 1
}
```

## Design Patterns

- Follows existing Hearts system patterns
- Uses Tailwind CSS for styling
- Toast notifications with react-hot-toast
- Glassmorphism modal design
- Animated transitions
- Accessible (ARIA labels, keyboard support)

