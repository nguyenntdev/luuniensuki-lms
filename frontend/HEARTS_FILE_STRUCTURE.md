# Hearts System - File Structure

```
frontend/
├── src/
│   ├── stores/
│   │   ├── authStore.js              (existing)
│   │   ├── motifStore.js             (existing)
│   │   └── heartsStore.js            ✨ NEW - Hearts state management
│   │
│   └── components/
│       └── hearts/                   ✨ NEW - Hearts components directory
│           ├── index.js              ✨ Export barrel
│           ├── HeartsDisplay.jsx     ✨ Hearts display with countdown
│           ├── HeartsRefillModal.jsx ✨ Refill modal
│           ├── Example.jsx           ✨ Usage example
│           └── README.md             ✨ Component documentation
│
├── HEARTS_IMPLEMENTATION_SUMMARY.md  ✨ Implementation summary
└── HEARTS_INTEGRATION_CHECKLIST.md   ✨ Integration guide

```

## File Sizes

| File | Lines | Size |
|------|-------|------|
| heartsStore.js | 142 | 3.4 KB |
| HeartsDisplay.jsx | 134 | 3.6 KB |
| HeartsRefillModal.jsx | 219 | 7.1 KB |
| index.js | 2 | 129 B |
| README.md | 175 | 5.0 KB |
| Example.jsx | 113 | 3.4 KB |
| **Total** | **785** | **22.6 KB** |

## Import Paths

```javascript
// Store
import useHeartsStore from "@/stores/heartsStore";

// Components (via barrel export)
import { HeartsDisplay, HeartsRefillModal } from "@/components/hearts";

// Or individual imports
import HeartsDisplay from "@/components/hearts/HeartsDisplay";
import HeartsRefillModal from "@/components/hearts/HeartsRefillModal";
```

## Component API

### HeartsDisplay

```typescript
interface HeartsDisplayProps {
  showLabel?: boolean;   // Show "X/5" label (default: true)
  showTimer?: boolean;   // Show countdown timer (default: true)
  size?: "sm" | "md" | "lg"; // Icon size (default: "md")
  onClick?: () => void;  // Click handler (optional)
}
```

### HeartsRefillModal

```typescript
interface HeartsRefillModalProps {
  isOpen: boolean;                    // Control visibility
  onClose: () => void;                // Close handler
  onSuccess?: (result: any) => void;  // Success callback
}
```

### useHeartsStore

```typescript
interface HeartsStore {
  // State
  hearts: number;
  maxHearts: number;
  nextRefillAt: string | null;
  unlimitedUntil: string | null;
  isLoading: boolean;
  error: string | null;
  lastFetchTime: string | null;

  // Actions
  fetchHearts: () => Promise<any>;
  useHeart: (reason?: string, metadata?: any) => Promise<any>;
  refillHearts: (type?: string) => Promise<any>;
  useStreakFreeze: () => Promise<any>;
  isUnlimited: () => boolean;
  decrementHearts: () => void;
  incrementHearts: () => void;
  reset: () => void;
}
```

## Dependencies Used

All dependencies are already installed in the project:

- ✅ `zustand@^5.0.9` - State management
- ✅ `lucide-react@^0.561.0` - Icons (Heart, Gem, Clock, Sparkles, X)
- ✅ `react@^19.2.3` - React framework
- ✅ Tailwind CSS - Styling

## Backend API Endpoints

All endpoints are already implemented and ready:

- ✅ `GET /api/v1/hearts`
- ✅ `POST /api/v1/hearts/use`
- ✅ `POST /api/v1/hearts/refill`
- ✅ `POST /api/v1/hearts/use-streak-freeze`

## Features Implemented

### Core Features ✅
- [x] 5 heart icons with filled/empty states
- [x] Current hearts count display (X/5)
- [x] Real-time countdown timer
- [x] Unlimited hearts badge
- [x] Auto-fetch hearts on mount
- [x] Smooth animations

### Refill Modal ✅
- [x] Refill with Gems option
- [x] Use Streak Freeze option
- [x] Wait for auto-refill option
- [x] Loading states
- [x] Error handling
- [x] Keyboard support (ESC)
- [x] Backdrop click to close

### State Management ✅
- [x] Zustand store
- [x] API integration
- [x] Error handling
- [x] Loading states
- [x] Optimistic updates

### Documentation ✅
- [x] Component README
- [x] Usage examples
- [x] Integration checklist
- [x] API documentation

## Quick Start

1. **Add to Navbar** (5 min)
   ```jsx
   import { HeartsDisplay } from "@/components/hearts";
   <HeartsDisplay onClick={() => setShowRefillModal(true)} />
   ```

2. **Integrate with Quiz** (10 min)
   ```jsx
   import useHeartsStore from "@/stores/heartsStore";
   const useHeart = useHeartsStore((state) => state.useHeart);
   await useHeart("quiz_wrong", { quiz_id, question_id });
   ```

3. **Test** (5 min)
   - Load page and verify hearts display
   - Click hearts to open modal
   - Test refill options

**Total Integration Time**: ~20 minutes

## Status

✅ **Implementation Complete**
✅ **Documentation Complete**
✅ **Ready for Integration**

No blockers. All files created and ready to use!

