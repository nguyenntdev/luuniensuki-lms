# 💖 Hearts/Energy System

A Duolingo-inspired hearts system for the Luuniensuki LMS app.

## Quick Start

1. **Generate code:**
   ```bash
   cd mobile
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

2. **Read the docs:**
   - Start: [Quick Reference](../../../HEARTS_QUICK_REFERENCE.md)
   - Testing: [Next Steps](../../../HEARTS_NEXT_STEPS.md)
   - Full guide: [System README](HEARTS_SYSTEM_README.md)

## What's This?

Users have 5 hearts. Each wrong answer in a quiz costs 1 heart. Hearts auto-refill (1 per 30 min). When out of hearts, users can:
- Wait for free refill
- Spend 50 gems
- Practice mode (TODO)
- Watch ad (TODO)

## Files

```
domain/entities/
  - heart_state.dart           # Hearts state entity

presentation/
  - providers/hearts_provider.dart      # State management
  - screens/hearts_refill_screen.dart   # Refill options UI
  - widgets/hearts_display.dart         # Hearts widget
  - widgets/heart_lost_animation.dart   # Loss animation
```

## Documentation

All documentation at: [HEARTS_DOCUMENTATION_INDEX.md](../../../HEARTS_DOCUMENTATION_INDEX.md)

## Status

✅ **Complete** - Ready for testing

---

**Version**: 1.0.0 | **Last Updated**: 2024-01-15

