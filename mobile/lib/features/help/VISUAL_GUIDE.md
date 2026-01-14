# Help & Support Screen - Visual Guide

## 🎨 Screen Layout

```
┌─────────────────────────────────────┐
│  ← [Back]   Trợ Giúp & Hỗ Trợ      │ ← Header with back button
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ❓ Câu Hỏi Thường Gặp       │   │ ← FAQ Section (Glass)
│  │                             │   │
│  │  📝 Làm thế nào...? 🔽      │   │   Expandable items
│  │  📝 Điểm XP được tính...?   │   │
│  │  📝 Làm sao để đạt...?      │   │
│  │  📝 Tôi có thể học...?      │   │
│  │  📝 Làm thế nào...?         │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👥 Liên Hệ Hỗ Trợ           │   │ ← Support Section (Glass)
│  │                             │   │
│  │  📧 Gửi Email Hỗ Trợ    →   │   │
│  │     support@eduquest.vn     │   │
│  │                             │   │
│  │  🐛 Báo Lỗi             →   │   │
│  │     Giúp chúng tôi...       │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📚 Tài Nguyên               │   │ ← Resources Section (Glass)
│  │                             │   │
│  │  ▶️ Hướng Dẫn Sử Dụng   →   │   │
│  │     Video tutorial...       │   │
│  │                             │   │
│  │  📄 Tài Liệu Hướng Dẫn  →   │   │
│  │     Tài liệu PDF...         │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🔗 Kết Nối Với Chúng Tôi    │   │ ← Social Media (Glass)
│  │                             │   │
│  │   [f]        [▶️]       [Z]  │   │
│  │ Facebook   YouTube    Zalo   │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

## 🎯 Section Details

### 1️⃣ FAQ Section
- **Icon**: Gold ❓ help icon
- **Background**: Glass container with 10% white opacity
- **Items**: 5 expandable FAQ cards
- **Animation**: Smooth expand/collapse
- **Text**: White with 80% opacity for answers

**Example Expanded**:
```
┌─────────────────────────────────┐
│ Làm thế nào để khám phá...? 🔼 │
├─────────────────────────────────┤
│ Để khám phá mô hình 3D, bạn    │
│ chỉ cần chạm và vuốt trên...   │
│                                 │
│ • Một ngón tay: xoay           │
│ • Hai ngón tay: phóng to       │
│ • Vuốt: di chuyển              │
└─────────────────────────────────┘
```

### 2️⃣ Support Section
- **Icon**: Red 👥 support agent icon
- **Cards**: Two clickable cards
- **Action**: Opens email client

**Card Structure**:
```
┌─────────────────────────────────┐
│ 📧  Gửi Email Hỗ Trợ        →  │
│     support@eduquest.vn         │
└─────────────────────────────────┘
```

### 3️⃣ Resources Section
- **Icon**: Orange 📚 book icon
- **Cards**: Two clickable cards
- **Action**: Opens browser

### 4️⃣ Social Media Section
- **Icon**: Gradient 🔗 share icon
- **Layout**: 3 columns
- **Buttons**: Icon + label

**Button Layout**:
```
┌───┐   ┌───┐   ┌───┐
│ f │   │ ▶ │   │ Z │
└───┘   └───┘   └───┘
Facebook YouTube Zalo
```

## 🎨 Color Palette

### Section Icons
```dart
FAQ:       AppColors.primary      // Gold
Support:   AppColors.secondary    // Red
Resources: AppColors.accent       // Orange
Social:    Gradient (Primary+Secondary)
```

### Glass Effects
```dart
Background: Colors.white.withOpacity(0.1)
Border:     Colors.white.withOpacity(0.2)
Shadow:     Colors.black.withOpacity(0.2)
```

### Text Colors
```dart
Titles:   Colors.white
Subtitles: Colors.white.withOpacity(0.7)
Answers:  Colors.white.withOpacity(0.8)
```

## 📱 Interactions

### FAQ Item Tap
```
Tap → Expand/Collapse → Show/Hide Answer
Icon: 🔽 (collapsed) / 🔼 (expanded)
```

### Support Card Tap
```
Tap → Launch Email Client
mailto:support@eduquest.vn
Subject: Hỗ trợ EduQuest AR
```

### Resource Card Tap
```
Tap → Open Browser
Mode: External Application
```

### Social Button Tap
```
Tap → Open Social Media App/Website
Mode: External Application
```

## ✨ Animations

### Page Transition
- Slide from right
- Duration: 300ms
- Curve: easeInOut

### FAQ Expansion
- Height animation
- Arrow rotation (180°)
- Duration: 200ms

### Button Press
- Scale: 0.95
- Opacity: 0.8
- Ripple effect

## 📐 Spacing & Sizing

### Padding
```dart
Screen edges:  20px
Card padding:  20px
Card gap:      20px
Icon padding:  10px
```

### Sizes
```dart
Header icon:   20px
Section icon:  24px
Social icon:   32px
Arrow icon:    18px
```

### Font Sizes
```dart
Page title:    24px (bold)
Section title: 20px (bold)
Card title:    16px (w600)
Subtitle:      14px
Answer text:   14px
```

## 🔄 State Management

### Expanded Index
```dart
int? _expandedIndex; // null = all collapsed
```

### URL Launch States
- Loading: Show indicator
- Success: Open app
- Error: Show SnackBar

## 🎭 User Feedback

### Error Messages
```dart
"Không thể mở ứng dụng email"
"Không thể mở liên kết"
```

### Visual Feedback
- Button ripple effects
- Hover states (web/desktop)
- Loading indicators
- Error snackbars

## 📲 Platform Behavior

### iOS
- Opens Mail app for email
- Opens Safari for links
- Native share sheet potential

### Android
- Opens default email client
- Opens Chrome/default browser
- Custom app chooser

## 🌐 URLs

### Email
```
mailto:support@eduquest.vn?subject=Hỗ trợ EduQuest AR
```

### Social Media
```
Facebook: https://facebook.com/eduquestar
YouTube:  https://youtube.com/@eduquestar
Zalo:     https://zalo.me/eduquestar
```

### Resources
```
Tutorial: https://youtube.com/@eduquestar
Docs:     https://eduquest.vn/docs
```

---

**Design System**: Glass Morphism  
**Theme**: Dark with Gold Accents  
**Responsiveness**: Single column, scrollable  
**Accessibility**: High contrast, clear labels

