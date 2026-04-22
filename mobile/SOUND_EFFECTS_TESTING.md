# Sound Effects System - Testing Checklist

## ✅ Pre-Testing Setup

### 1. Install Dependencies
```bash
cd mobile
flutter pub get
```

### 2. Generate Sound Files (Optional - for testing without real sounds)
```bash
cd mobile/assets/sounds

# Option 1: Using Python script
pip3 install pydub numpy
python3 generate_sounds.py

# Option 2: Download from free sources
# See README.md in this directory for sources
```

### 3. Verify Files
```bash
ls -lh mobile/assets/sounds/
# Should see: correct.mp3, wrong.mp3, tap.mp3, etc.
```

---

## 🧪 Testing Scenarios

### A. Sound Effects Enable/Disable

- [ ] **Test 1: Enable Sounds**
  1. Open app → Settings
  2. Enable "Hiệu ứng âm thanh"
  3. Go to quiz or demo screen
  4. Verify sounds play when tapping buttons
  5. Verify no vibration (or very subtle)

- [ ] **Test 2: Disable Sounds**
  1. Open app → Settings
  2. Disable "Hiệu ứng âm thanh"
  3. Go to quiz or demo screen
  4. Verify NO sounds play
  5. Verify haptic feedback works instead (vibration)

- [ ] **Test 3: Settings Persistence**
  1. Toggle sound settings ON
  2. Close app completely
  3. Reopen app
  4. Verify setting is still ON
  5. Repeat with OFF

---

### B. Quiz Screen Integration

- [ ] **Test 4: Correct Answer Sound**
  1. Start a quiz
  2. Select correct answer
  3. Verify "correct" sound plays immediately
  4. Sound should be pleasant, positive tone

- [ ] **Test 5: Wrong Answer Sound**
  1. Start a quiz
  2. Select wrong answer
  3. Verify "wrong" sound plays immediately
  4. Sound should be different from correct
  5. Should also show heart lost animation

- [ ] **Test 6: Multiple Answers**
  1. Answer several questions in a row
  2. Mix correct and wrong answers
  3. Verify each plays appropriate sound
  4. No sound overlap or delay

---

### C. Quiz Result Screen

- [ ] **Test 7: Lesson Complete (Pass)**
  1. Complete a quiz with passing score (≥80%)
  2. On result screen, verify:
     - Confetti animation plays
     - "Lesson complete" sound plays
     - Mascot shows celebration

- [ ] **Test 8: Lesson Complete (Perfect)**
  1. Complete a quiz with 100% score
  2. Verify:
     - Confetti animation plays
     - "Lesson complete" sound plays
     - Bonus gems awarded
     - Mascot shows perfect score message

- [ ] **Test 9: Lesson Fail**
  1. Complete a quiz with failing score (<80%)
  2. Verify:
     - No celebration sound
     - No confetti
     - Mascot shows encouragement

---

### D. XP Celebration Integration

- [ ] **Test 10: Small XP Gain (25 XP)**
  1. Complete discovery or earn 25 XP
  2. Verify:
     - XP badge appears
     - "XP gain" sound plays
     - Quick animation

- [ ] **Test 11: Medium XP Gain (50-75 XP)**
  1. Complete lesson or earn 50 XP
  2. Verify:
     - XP badge + particles
     - "XP gain" sound plays
     - Medium animation

- [ ] **Test 12: Large XP Gain (300+ XP)**
  1. Pass urn exam or earn 300 XP
  2. Verify:
     - Full confetti blast
     - "Level up" sound plays
     - Dramatic animation

- [ ] **Test 13: Actual Level Up**
  1. Gain enough XP to level up
  2. Verify:
     - "Level up" sound plays
     - Level up badge shown
     - New rank displayed
     - Confetti celebration

---

### E. Sound Button Widgets

- [ ] **Test 14: Sound Demo Screen**
  1. Navigate to sound demo screen (if added to app)
  2. Test each button:
     - Correct answer button
     - Wrong answer button
     - XP gain button
     - Level up button
     - Streak complete button
     - Lesson complete button
  3. Verify each plays unique sound

- [ ] **Test 15: Button Variants**
  1. Test SoundButton widget
  2. Test SoundTextButton widget
  3. Test SoundOutlinedButton widget
  4. Test SoundIconButton widget
  5. Verify all play tap sound on press

---

### F. Edge Cases & Error Handling

- [ ] **Test 16: Missing Sound Files**
  1. Rename or remove one sound file (e.g., correct.mp3)
  2. Trigger action that would play that sound
  3. Verify:
     - No crash or error dialog
     - Haptic feedback plays instead
     - Console shows warning (optional)
  4. Restore file and test again

- [ ] **Test 17: Device Without Vibration**
  1. Test on device/emulator without vibration support
  2. Disable sounds in settings
  3. Trigger various actions
  4. Verify:
     - No crash
     - Silent operation (no sound, no vibration)

- [ ] **Test 18: Low Volume**
  1. Set device volume to minimum
  2. Enable sounds
  3. Trigger actions
  4. Verify:
     - No crash
     - Sounds play (but quiet)
     - Can hear with headphones

- [ ] **Test 19: Rapid Fire Sounds**
  1. Quickly answer multiple quiz questions
  2. Verify:
     - Each sound plays
     - No sound overlap issues
     - No lag or performance issues

- [ ] **Test 20: Background App**
  1. Play quiz with sounds enabled
  2. Switch to another app mid-quiz
  3. Return to quiz app
  4. Continue answering questions
  5. Verify sounds still work

---

### G. Performance Testing

- [ ] **Test 21: Initial Load Time**
  1. Fresh app install
  2. First launch
  3. Navigate to quiz
  4. Answer first question
  5. Verify:
     - Sound plays without delay
     - No lag on first play

- [ ] **Test 22: Memory Usage**
  1. Enable sounds
  2. Complete multiple quizzes
  3. Monitor memory usage
  4. Verify:
     - No memory leaks
     - Consistent memory usage

- [ ] **Test 23: Battery Impact**
  1. Use app with sounds for extended period
  2. Monitor battery usage
  3. Verify:
     - Reasonable battery consumption
     - No excessive drain

---

### H. Platform Testing

- [ ] **Test 24: Android Testing**
  1. Test on Android device/emulator
  2. Run all core tests (1-15)
  3. Verify haptic feedback works
  4. Test different Android versions if possible

- [ ] **Test 25: iOS Testing**
  1. Test on iOS device/simulator
  2. Run all core tests (1-15)
  3. Verify haptic feedback works
  4. Test different iOS versions if possible

---

## 🐛 Known Issues & Workarounds

### Issue 1: Sound Delay on First Play
**Cause:** Sound files not pre-loaded  
**Fix:** Already implemented - sounds pre-load on service initialization

### Issue 2: Vibration Permission (Android)
**Cause:** Missing permission in AndroidManifest.xml  
**Fix:** Add permission if needed:
```xml
<uses-permission android:name="android.permission.VIBRATE" />
```

### Issue 3: Sound Not Audible in Silent Mode
**Cause:** Device in silent/do-not-disturb mode  
**Expected:** Haptic feedback should work instead

---

## ✅ Success Criteria

All tests should pass with:
- ✅ Sounds play when enabled
- ✅ Haptic feedback works when sounds disabled
- ✅ No crashes or errors
- ✅ Settings persist correctly
- ✅ Performance is smooth
- ✅ Works on both Android and iOS

---

## 📊 Test Report Template

```
Date: ___________
Tester: __________
Device: __________
OS Version: ______

Tests Passed: _____ / 25
Tests Failed: _____ / 25

Failed Tests:
- Test #___: _________________________
  Issue: _____________________________
  
- Test #___: _________________________
  Issue: _____________________________

Notes:
_____________________________________
_____________________________________

Overall Status: [ ] PASS  [ ] FAIL
```

---

## 🚀 Next Steps After Testing

1. **If tests pass:**
   - Deploy to staging
   - Beta test with users
   - Collect feedback
   - Prepare for production

2. **If tests fail:**
   - Document issues
   - Create bug tickets
   - Fix issues
   - Re-test

3. **Optional enhancements:**
   - Add more sound effects
   - Create sound packs
   - Add volume control
   - Add sound preview in settings

