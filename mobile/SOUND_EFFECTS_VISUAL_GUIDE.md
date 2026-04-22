# Sound Effects System - Visual Architecture Guide

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter App                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 ProviderScope (Riverpod)                  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         soundServiceProvider (Singleton)           │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌────────────────────────────────────────────┐  │  │  │
│  │  │  │          SoundService                       │  │  │  │
│  │  │  │  ┌──────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  Map<SoundEffect, AudioPlayer>       │  │  │  │  │
│  │  │  │  │  • correct.mp3  → AudioPlayer        │  │  │  │  │
│  │  │  │  │  • wrong.mp3    → AudioPlayer        │  │  │  │  │
│  │  │  │  │  • tap.mp3      → AudioPlayer        │  │  │  │  │
│  │  │  │  │  • xp_gain.mp3  → AudioPlayer        │  │  │  │  │
│  │  │  │  │  • level_up.mp3 → AudioPlayer        │  │  │  │  │
│  │  │  │  │  • streak_complete.mp3 → AudioPlayer │  │  │  │  │
│  │  │  │  │  • lesson_complete.mp3 → AudioPlayer │  │  │  │  │
│  │  │  │  └──────────────────────────────────────┘  │  │  │  │
│  │  │  │                                             │  │  │  │
│  │  │  │  Methods:                                   │  │  │  │
│  │  │  │  • playCorrect()                           │  │  │  │
│  │  │  │  • playWrong()                             │  │  │  │
│  │  │  │  • playTap()                               │  │  │  │
│  │  │  │  • playXpGain()                            │  │  │  │
│  │  │  │  • playLevelUp()                           │  │  │  │
│  │  │  │  • playStreakComplete()                    │  │  │  │
│  │  │  │  • playLessonComplete()                    │  │  │  │
│  │  │  │  • playHaptic() ← Fallback                │  │  │  │
│  │  │  └─────────────────────────────────────────┘  │  │  │
│  │  │                      ▲                          │  │  │
│  │  │                      │ checks setting           │  │  │
│  │  │                      │                          │  │  │
│  │  │  ┌──────────────────┴───────────────────────┐  │  │  │
│  │  │  │     settingsNotifierProvider             │  │  │  │
│  │  │  │     SettingsState {                      │  │  │  │
│  │  │  │       soundEffectsEnabled: bool          │  │  │  │
│  │  │  │     }                                     │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Integration Flow

### Quiz Answer Flow
```
User Selects Answer
       │
       ▼
┌──────────────────────┐
│  quiz_screen.dart    │
│  onAnswerSelected    │
└──────────┬───────────┘
           │
           ▼
    Check if Correct?
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
  Correct       Wrong
    │             │
    ▼             ▼
soundService   soundService
.playCorrect() .playWrong()
    │             │
    └──────┬──────┘
           │
           ▼
   ┌───────────────┐
   │ Check Setting │
   └───────┬───────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 Enabled      Disabled
    │             │
    ▼             ▼
Play Sound   Play Haptic
(just_audio) (vibration)
```

---

### XP Celebration Flow
```
User Earns XP
      │
      ▼
┌──────────────────────────┐
│ xp_celebration_service   │
│ showCelebration()        │
└──────────┬───────────────┘
           │
           ▼
  Calculate XP Amount
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
Level Up?     Normal XP?
    │             │
    ▼             ▼
soundService  soundService
.playLevelUp() .playXpGain()
    │             │
    └──────┬──────┘
           │
           ▼
  Show Overlay + Animation
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      User Actions                       │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┼─────────┬─────────────┬─────────────┐
    │         │         │             │             │
    ▼         ▼         ▼             ▼             ▼
Quiz Answer  Quiz    XP Earned   Level Up    Button Tap
             Complete
    │         │         │             │             │
    ▼         ▼         ▼             ▼             ▼
┌─────────────────────────────────────────────────────────┐
│              ref.read(soundServiceProvider)             │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│           SoundService.play(SoundEffect)                │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│    Check: settingsNotifierProvider.soundEffectsEnabled  │
└─────────────┬───────────────────────────────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
   Enabled       Disabled
       │             │
       ▼             ▼
┌────────────┐  ┌────────────┐
│ AudioPlayer│  │ Vibration  │
│ .play()    │  │ .vibrate() │
└────────────┘  └────────────┘
       │             │
       └──────┬──────┘
              │
              ▼
        User Feedback
      (Sound or Haptic)
```

---

## 🎨 Component Hierarchy

```
lib/
├── core/
│   ├── services/
│   │   └── sound_service.dart ◄──────────┐
│   │       ├── SoundService             │
│   │       ├── SoundEffect enum          │
│   │       └── soundServiceProvider      │
│   │                                     │
│   └── widgets/                          │
│       └── sound_button.dart             │
│           ├── SoundButton               │
│           ├── SoundTextButton           │
│           ├── SoundIconButton           │
│           └── Extensions                │
│                                         │
├── features/                             │
│   ├── quiz/                             │
│   │   └── presentation/                 │
│   │       └── screens/                  │
│   │           ├── quiz_screen.dart ─────┤ Uses
│   │           │   (plays correct/wrong) │
│   │           └── quiz_result_screen.dart ┤
│   │               (plays lesson complete)│
│   │                                     │
│   └── settings/                         │
│       └── presentation/                 │
│           ├── providers/                │
│           │   └── settings_provider.dart│
│           │       (soundEffectsEnabled) │
│           └── screens/                  │
│               └── settings_screen.dart  │
│                   (toggle UI)           │
│                                         │
└── shared/                               │
    └── services/                         │
        └── xp_celebration_service.dart ──┘
            (plays xp/level up sounds)
```

---

## 🔄 Lifecycle Diagram

```
App Startup
    │
    ▼
┌─────────────────┐
│ ProviderScope   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ First access to             │
│ soundServiceProvider        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ SoundService constructor    │
│ • Create instance           │
│ • Store Ref                 │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ initialize()                │
│ • Create AudioPlayers       │
│ • Load all sound files      │
│ • Pre-load assets           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Service Ready               │
│ • Sounds pre-loaded         │
│ • Zero delay on play        │
└────────┬────────────────────┘
         │
         ▼
    Runtime Usage
    (play sounds)
         │
         ▼
┌─────────────────────────────┐
│ Provider disposed           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ dispose()                   │
│ • Stop all players          │
│ • Release resources         │
│ • Clear cache               │
└─────────────────────────────┘
```

---

## 🎮 State Machine

```
          ┌─────────────┐
          │   INITIAL   │
          └──────┬──────┘
                 │
                 ▼
          initialize()
                 │
          ┌──────┴──────┐
          │             │
          ▼             ▼
    Loading OK    Loading Failed
          │             │
          ▼             ▼
    ┌─────────┐   ┌─────────┐
    │ READY   │   │ FALLBACK│
    └────┬────┘   └────┬────┘
         │             │
         │             │
         ▼             ▼
     play()        playHaptic()
         │             │
         │             │
    ┌────┴─────────────┴────┐
    │                        │
    ▼                        ▼
Check soundEffectsEnabled
    │                        │
    │                        │
┌───┴───┐              ┌─────┴─────┐
│Enabled│              │ Disabled  │
└───┬───┘              └─────┬─────┘
    │                        │
    ▼                        ▼
Play Sound              Play Haptic
(AudioPlayer)           (Vibration)
```

---

## 📱 User Experience Flow

```
┌─────────────────────────────────────────────────────┐
│                  User Opens App                     │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ Navigate to Settings│
            └──────────┬──────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Toggle "Hiệu ứng âm thanh"   │
        │ ON ←→ OFF                    │
        └──────────┬───────────────────┘
                   │
            ┌──────┴──────┐
            │             │
            ▼             ▼
        Enabled       Disabled
            │             │
            ▼             ▼
      Save to Hive   Save to Hive
            │             │
            └──────┬──────┘
                   │
                   ▼
         ┌─────────────────┐
         │  User Uses App  │
         │ • Plays Quiz    │
         │ • Earns XP      │
         │ • Taps Buttons  │
         └────────┬────────┘
                  │
           ┌──────┴──────┐
           │             │
           ▼             ▼
    Sounds ON      Sounds OFF
           │             │
           ▼             ▼
   🔊 Audio Play  📳 Vibration
           │             │
           └──────┬──────┘
                  │
                  ▼
        👂 User gets feedback
```

---

## 🎯 Integration Points Map

```
┌────────────────────────────────────────────────────────┐
│                    SoundService                        │
│                   (Central Hub)                        │
└────┬──────────┬──────────┬──────────┬─────────────┬───┘
     │          │          │          │             │
     │          │          │          │             │
     ▼          ▼          ▼          ▼             ▼
┌─────────┐ ┌────────┐ ┌──────┐ ┌─────────┐ ┌──────────┐
│  Quiz   │ │ Result │ │  XP  │ │Settings │ │ Buttons  │
│ Screen  │ │ Screen │ │Celebr│ │         │ │ (Future) │
└─────────┘ └────────┘ └──────┘ └─────────┘ └──────────┘
    │            │         │          │            │
    │            │         │          │            │
    ▼            ▼         ▼          ▼            ▼
 correct/     lesson    xp/level  enable/       tap
  wrong      complete     up      disable      sound
```

---

**This visual guide helps understand the complete architecture and data flow of the Sound Effects System.**

