# Explore Screen Fix - Flow Diagram

## Before Fix (Broken Flow) ❌

```
App Launch
    │
    ├─→ Auth Provider Init (Future.microtask)
    │       │
    │       └─→ Initialize auth session
    │               │
    │               └─→ Load auth token (async)
    │
    └─→ Explore Screen Build
            │
            └─→ ExploreNotifier Build (Future.microtask)
                    │
                    └─→ loadUrns() called IMMEDIATELY
                            │
                            └─→ API call to /api/v1/urns
                                    │
                                    ├─→ [SUCCESS if auth ready] ✅
                                    │       └─→ Display urns
                                    │
                                    └─→ [RACE CONDITION!] 🏁
                                            │
                                            └─→ Auth not ready yet
                                                    │
                                                    └─→ 401 Unauthorized ❌
                                                            │
                                                            └─→ Error state
                                                                    │
                                                                    └─→ AutoDispose kicks in 💀
                                                                            │
                                                                            └─→ Provider disposed
                                                                                    │
                                                                                    └─→ BLANK WHITE SCREEN 🤍
```

## After Fix (Working Flow) ✅

```
App Launch
    │
    ├─→ Auth Provider Init
    │       │
    │       └─→ Initialize auth session
    │               │
    │               └─→ Load auth token
    │                       │
    │                       └─→ authState.isAuthenticated = true ✓
    │
    └─→ Explore Screen Build
            │
            ├─→ Watch authState
            │       │
            │       └─→ isAuthenticated? false
            │               │
            │               └─→ Show loading state, wait... ⏳
            │
            └─→ Screen Rebuilds (auth state changed)
                    │
                    ├─→ Watch authState
                    │       │
                    │       └─→ isAuthenticated? true ✓
                    │
                    └─→ Trigger in postFrameCallback
                            │
                            └─→ loadUrns() called SAFELY
                                    │
                                    └─→ API call to /api/v1/urns
                                            │
                                            └─→ Auth token included ✓
                                                    │
                                                    ├─→ [SUCCESS] ✅
                                                    │       │
                                                    │       └─→ Display 9 urns
                                                    │               │
                                                    │               └─→ State persists (keepAlive) ♾️
                                                    │
                                                    ├─→ [ERROR] ❌
                                                    │       │
                                                    │       └─→ Show error message + retry button
                                                    │
                                                    └─→ [EMPTY] 📭
                                                            │
                                                            └─→ Show empty message + retry button
```

## State Management Comparison

### Before (AutoDispose)
```
Navigation Flow:
Explore Tab → Profile Tab → Explore Tab
     ↓              ↓              ↓
  Load data    Dispose! 💀    Load again 🔄
                               (unnecessary)
```

### After (KeepAlive)
```
Navigation Flow:
Explore Tab → Profile Tab → Explore Tab
     ↓              ↓              ↓
  Load data    Keep data ✓   Show cached data ⚡
                             (instant!)
```

## Error Handling States

```
┌─────────────────────────────────┐
│   Explore Screen State Machine  │
└─────────────────────────────────┘
                │
                ├─→ LOADING 🔄
                │   │
                │   └─→ Show circular progress indicator
                │
                ├─→ SUCCESS ✅
                │   │
                │   ├─→ Has data? Display grid of urns
                │   │
                │   └─→ Empty? Show empty state 📭
                │
                └─→ ERROR ❌
                    │
                    └─→ Show error message + retry button


┌────────────────────────────────┐
│   Empty State Flow             │
└────────────────────────────────┘

API returns []
    │
    ├─→ !isLoading ✓
    ├─→ !hasError ✓
    └─→ urns.isEmpty ✓
            │
            └─→ Display:
                ├─→ 📭 Icon
                ├─→ "Không có dữ liệu"
                ├─→ "Vui lòng thử lại sau"
                └─→ [Thử lại] button
```

## Key Changes Summary

| Aspect | Before | After |
|--------|--------|-------|
| Provider Type | `@riverpod` (auto-dispose) | `@Riverpod(keepAlive: true)` |
| Loading Trigger | `Future.microtask()` immediate | Wait for auth, then load |
| Auth Check | None (race condition) | Explicit check before loading |
| Empty State | Not handled | Handled with UI |
| State Persistence | Lost on navigation | Persists across navigation |
| API Calls | Multiple unnecessary calls | Single call, cached |

## Benefits of the Fix

1. **No Race Conditions** ✅
   - Auth completes before API calls
   - Guaranteed valid auth token

2. **Better UX** ✅
   - Clear loading states
   - Helpful error messages
   - Empty state guidance
   - Faster navigation (cached data)

3. **Fewer API Calls** ✅
   - Data persists in memory
   - Only reload on explicit refresh
   - Better performance

4. **Maintainable** ✅
   - Clear separation of concerns
   - Explicit state management
   - Easy to debug

5. **User Feedback** ✅
   - Always shows appropriate state
   - No confusing blank screens
   - Actionable error messages

