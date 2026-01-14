# Personal Info Screen - Visual Structure

```
┌─────────────────────────────────────────────────────┐
│  ← Thông tin cá nhân                                │  <- App Bar
├─────────────────────────────────────────────────────┤
│                                                     │
│              ┌─────────────────┐                    │
│              │    ╭─────╮      │                    │
│              │   │  👤  │      │  <- Avatar Circle  │
│              │    ╰─────╯      │     (120x120)      │
│              │      📷          │  <- Camera Button  │
│              └─────────────────┘                    │
│     Nhấn vào biểu tượng để thay đổi ảnh đại diện    │
│                                                     │
├─────────────────────────────────────────────────────┤
│  ╔═════════════════════════════════════════════╗    │
│  ║ 👤 Tên hiển thị                             ║    │
│  ║ ┌─────────────────────────────────────────┐ ║    │
│  ║ │ Nguyễn Văn A                            │ ║  <- Display Name  
│  ║ └─────────────────────────────────────────┘ ║    │  (GlassTextField)
│  ║ Tên này sẽ được hiển thị công khai          ║    │
│  ╚═════════════════════════════════════════════╝    │
├─────────────────────────────────────────────────────┤
│  ╔═════════════════════════════════════════════╗    │
│  ║ @ Tên người dùng                            ║    │
│  ║ ┌─────────────────────────────────────────┐ ║    │
│  ║ │ nguyenvana                              │ ║  <- Username
│  ║ └─────────────────────────────────────────┘ ║    │  (GlassTextField)
│  ║ Tên người dùng duy nhất để chia sẻ hồ sơ    ║    │
│  ╚═════════════════════════════════════════════╝    │
├─────────────────────────────────────────────────────┤
│  ╔═════════════════════════════════════════════╗    │
│  ║ ✉️  Email                        🔒          ║    │
│  ║                                             ║    │
│  ║ user@example.com                            ║  <- Email (Read-only)
│  ║                                             ║    │  (Dimmed container)
│  ║ 🔒 Email không thể thay đổi                 ║    │
│  ╚═════════════════════════════════════════════╝    │
├─────────────────────────────────────────────────────┤
│  ╔═════════════════════════════════════════════╗    │
│  ║ 🌐 Hiển thị hồ sơ công khai          ◯──◉  ║  <- Visibility Toggle
│  ║                                             ║    │  (Animated Switch)
│  ║ ┌─────────────────────────────────────────┐ ║    │
│  ║ │ ℹ️  Hồ sơ của bạn sẽ hiển thị công khai │ ║    │
│  ║ │    cho người khác                       │ ║    │
│  ║ └─────────────────────────────────────────┘ ║    │
│  ╚═════════════════════════════════════════════╝    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │         💾 Lưu thay đổi                     │  <- Save Button
│  └─────────────────────────────────────────────┘    │  (GlassButton - Primary)
│                                                     │
└─────────────────────────────────────────────────────┘

COLORS:
- Background: Animated gradient (dark navy)
- Containers: Glass morphism (semi-transparent white)
- Borders: 20% white opacity
- Accents: Vietnamese gold (#E8B44C)
- Text: White with varying opacity

ANIMATIONS:
1. Screen Entry
   - Fade in: 0 → 1 opacity (600ms)
   - Slide up: 20% offset → 0 (cubic ease-out)

2. Interactive
   - Switch glow when enabled
   - Button opacity changes with edits
   - Smooth state transitions

SPACING:
- Screen padding: 16px
- Section spacing: 16-24px
- Container padding: 16px
- Text spacing: 8px

FUNCTIONALITY:
✓ Display name editing (required)
✓ Username editing (optional)
✓ Email display (read-only)
✓ Profile visibility toggle
✓ Change detection
✓ Save with validation
✓ Success/error feedback
⏳ Avatar upload (placeholder)
```

## State Flow

```
User enters screen
    ↓
Initialize controllers with current user data
    ↓
User edits field
    ↓
_onFieldChanged() detects change
    ↓
_hasChanges = true
    ↓
Save button becomes enabled (opacity: 1.0)
    ↓
User taps Save
    ↓
_saveChanges() validates & calls API
    ↓
updateProfile() on authNotifier
    ↓
Success → Show snackbar, reset _hasChanges
Failure → Show error snackbar
```

## Component Hierarchy

```
AnimatedGradientBackground
└── Scaffold (transparent)
    └── SafeArea
        └── FadeTransition
            └── SlideTransition
                └── CustomScrollView
                    ├── SliverAppBar (← back button)
                    └── SliverPadding
                        └── SliverList
                            ├── Avatar Section
                            ├── Display Name (GlassContainer + GlassTextField)
                            ├── Username (GlassContainer + GlassTextField)
                            ├── Email (GlassContainer - read-only)
                            ├── Visibility Toggle (GlassContainer + Switch)
                            └── Save Button (GlassButton)
```

