# Gems System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GEMS SYSTEM OVERVIEW                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERACTIONS                         │
└──────────────────────────────────────────────────────────────────┘

    Complete        Complete        Perfect         7-Day
    Lesson          Daily Goal      Quiz            Streak
       │               │              │                │
       ├──► +10       ├──► +20       ├──► +5         ├──► +50
       │               │              │                │
       └───────────────┴──────────────┴────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   GemsNotifier (State)  │
              │   ┌──────────────────┐  │
              │   │ balance: 100     │  │
              │   │ transactions: [] │  │
              │   │ isLoading: false │  │
              │   └──────────────────┘  │
              └─────────────────────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
                   ▼                 ▼
          ┌──────────────┐   ┌──────────────┐
          │ HiveStorage  │   │ UI Displays  │
          │ - balance    │   │ - Profile    │
          │ - history    │   │ - Shop       │
          └──────────────┘   └──────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                        SPENDING GEMS                             │
└──────────────────────────────────────────────────────────────────┘

    Shop Item           Balance Check        Purchase
       │                      │                   │
       ▼                      ▼                   ▼
   ┌──────────┐         ┌──────────┐        ┌──────────┐
   │ Streak   │         │ Can      │        │ Deduct   │
   │ Freeze   ├────────►│ Afford?  ├───────►│ Gems     │
   │ 50 gems  │         │ Yes/No   │        │ Record   │
   └──────────┘         └──────────┘        └──────────┘


┌──────────────────────────────────────────────────────────────────┐
│                     TRANSACTION TYPES                            │
└──────────────────────────────────────────────────────────────────┘

EARNED (Positive)                   SPENT (Negative)
┌──────────────────────┐           ┌──────────────────────┐
│ earnedLesson   (+10) │           │ spentStreakFreeze    │
│ earnedStreak   (+50) │           │        (-50)         │
│ earnedPerfect   (+5) │           │ spentDoubleXp (-100) │
│ earnedBonus    (+20) │           │ spentHint     (-25)  │
└──────────────────────┘           └──────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                      DATA FLOW                                   │
└──────────────────────────────────────────────────────────────────┘

1. Award Gems
   ───────────
   Event (e.g., lesson complete)
        │
        ▼
   addGems(amount, type, description)
        │
        ▼
   Create GemTransaction
        │
        ├─► Update balance in state
        ├─► Add to transaction history
        └─► Save to HiveStorage
        │
        ▼
   UI updates automatically (Riverpod)

2. Spend Gems
   ───────────
   User taps shop item
        │
        ▼
   spendGems(amount, type, description)
        │
        ▼
   Check if balance >= amount
        │
        ├─► Yes: Proceed
        └─► No: Return false
        │
        ▼
   Create GemTransaction (negative)
        │
        ├─► Subtract from balance
        ├─► Add to transaction history
        └─► Save to HiveStorage
        │
        ▼
   Return true (success)


┌──────────────────────────────────────────────────────────────────┐
│                    STORAGE STRUCTURE                             │
└──────────────────────────────────────────────────────────────────┘

HiveStorage (userBox)
│
├── gems_balance: int
│   └── Current gem count (e.g., 100)
│
└── gems_transactions: List<Map>
    └── [
          {
            id: "gem_1234567890123",
            amount: 10,
            type: "earnedLesson",
            description: "Hoàn thành bài học: Rồng",
            createdAt: "2024-01-15T10:30:00Z"
          },
          ...
        ]
```

