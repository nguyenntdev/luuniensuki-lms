# Leaderboard Enhancement - Visual Guide

## Component Hierarchy

```
LeaderboardPage
├── UserRankCard (if user is authenticated and in leaderboard)
│   ├── RankBadge
│   └── User Info (rank, name, title, XP)
└── Leaderboard Table
    └── For each entry:
        ├── RankBadge
        ├── Display Name + "(Bạn)" if current user
        ├── Title
        └── Total XP
```

## RankBadge Component

```
Rank 1: 🥇 (yellow-500 background)
Rank 2: 🥈 (gray-300 background)
Rank 3: 🥉 (amber-600 background)
Rank 4+: [number] (muted background)
```

## UserRankCard Layout

```
┌─────────────────────────────────────────────────────┐
│  🥇  Hạng của bạn                          XP       │
│      [User Name]                         [12,345]   │
│      [User Title]                                   │
└─────────────────────────────────────────────────────┘
```

- Gradient background: `from-primary/10 to-primary/5`
- Border: `border-2 border-primary`
- Shadow: `shadow-lg`

## Table Row Highlighting

### Current User Row
```
┌─────────────────────────────────────────────────────┐
│ 🥇 │ User Name (Bạn)  │ Title │ 12,345             │ ← bg-primary/10
└─────────────────────────────────────────────────────┘
```

### Other User Rows
```
┌─────────────────────────────────────────────────────┐
│ 🥈 │ Other User       │ Title │ 10,234             │ ← hover:bg-muted/50
└─────────────────────────────────────────────────────┘
```

## Color Scheme

- **Gold Medal**: `bg-yellow-500`
- **Silver Medal**: `bg-gray-300`
- **Bronze Medal**: `bg-amber-600`
- **Current User Highlight**: `bg-primary/10`
- **Hover State**: `bg-muted/50`
- **User Indicator**: `text-primary`

## Responsive Behavior

- Card and table maintain full width
- Text truncation for long names
- Proper spacing on mobile devices
- Touch-friendly tap targets

