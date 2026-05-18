# Sound Effects for Luuniensuki LMS

## Overview
This directory contains sound effect files used throughout the app for various user interactions and achievements.

## Sound Files

### Required Sound Effects

1. **correct.mp3** - Played when user answers correctly
   - Suggested: Pleasant chime, success tone (C-E-G chord)
   - Duration: 0.3-0.5s
   - Frequency: 523Hz (C5), 659Hz (E5), 784Hz (G5)

2. **wrong.mp3** - Played when user answers incorrectly
   - Suggested: Subtle error tone (low tone)
   - Duration: 0.2-0.4s
   - Frequency: 220Hz (A3) descending

3. **tap.mp3** - Generic button tap sound
   - Suggested: Short click sound
   - Duration: 0.05-0.1s
   - Frequency: 440Hz (A4)

4. **xp_gain.mp3** - Played when user gains XP
   - Suggested: Coins/points collection sound
   - Duration: 0.4-0.6s
   - Frequency: Ascending tones 523-659-784Hz

5. **level_up.mp3** - Played when user levels up
   - Suggested: Fanfare, celebration sound
   - Duration: 1-2s
   - Frequency: Full ascending scale

6. **streak_complete.mp3** - Played when completing a streak
   - Suggested: Achievement unlock sound
   - Duration: 0.5-0.8s
   - Frequency: Rapid ascending notes

7. **lesson_complete.mp3** - Played when completing a lesson
   - Suggested: Success jingle
   - Duration: 0.8-1.2s
   - Frequency: Melodic completion sequence

## Generating Placeholder Sounds

### Option 1: Using Online Tools
1. Visit: https://www.beepbox.co/ or https://sfxr.me/
2. Create simple beep tones with suggested frequencies
3. Export as MP3 (or WAV, then convert to MP3)

### Option 2: Using Audacity (Free, Open Source)
1. Install Audacity: https://www.audacityteam.org/
2. Generate > Tone:
   - For **correct**: Generate 0.4s tone at 659Hz (E5), add fade in/out
   - For **wrong**: Generate 0.3s tone at 220Hz (A3), add fade out
   - For **tap**: Generate 0.08s tone at 440Hz (A4)
   - For **xp_gain**: Generate chirp from 500Hz to 800Hz, 0.5s
   - For **level_up**: Combine multiple tones for fanfare effect
3. File > Export > Export as MP3

### Option 3: Using Python Script
```python
# Install: pip install pydub numpy
from pydub.generators import Sine
from pydub import AudioSegment

def create_tone(frequency, duration_ms, fade_ms=20):
    tone = Sine(frequency).to_audio_segment(duration=duration_ms)
    return tone.fade_in(fade_ms).fade_out(fade_ms)

# Correct sound (pleasant chord)
correct = create_tone(659, 400)
correct.export("correct.mp3", format="mp3")

# Wrong sound
wrong = create_tone(220, 300)
wrong.export("wrong.mp3", format="mp3")

# Tap sound
tap = create_tone(440, 80)
tap.export("tap.mp3", format="mp3")

# XP Gain (ascending tones)
xp_gain = create_tone(523, 150) + create_tone(659, 150) + create_tone(784, 200)
xp_gain.export("xp_gain.mp3", format="mp3")

# Level up (fanfare)
level_up = (create_tone(523, 200) + create_tone(659, 200) + 
            create_tone(784, 200) + create_tone(1047, 400))
level_up.export("level_up.mp3", format="mp3")

# Streak complete
streak = (create_tone(659, 100) + create_tone(784, 100) + 
          create_tone(1047, 150))
streak.export("streak_complete.mp3", format="mp3")

# Lesson complete
lesson = (create_tone(523, 200) + create_tone(659, 200) + 
          create_tone(784, 200) + create_tone(659, 400))
lesson.export("lesson_complete.mp3", format="mp3")
```

## Professional Sound Effects (Recommended)

For production use, consider using professional sound effects from:

1. **Free Sources:**
   - Freesound.org (CC licenses)
   - Zapsplat.com (free with attribution)
   - Mixkit.co (royalty-free)

2. **Paid Sources:**
   - AudioJungle (Envato Market)
   - Epidemic Sound
   - Artlist.io

## File Requirements

- **Format**: MP3 (for best compatibility)
- **Sample Rate**: 44.1kHz
- **Bit Rate**: 128-192kbps
- **Channels**: Mono (stereo optional)
- **Volume**: Normalized to -3dB to -6dB peak

## Integration

These sounds are automatically loaded by `SoundService` in `lib/core/services/sound_service.dart`.

The service will:
- Load all sounds on initialization
- Use haptic feedback as fallback if sound files are missing
- Respect user's sound settings preference

## Testing

To test sounds:
1. Enable sound effects in Settings
2. Play quiz and answer questions (correct/wrong sounds)
3. Earn XP (xp_gain sound)
4. Complete lessons (lesson_complete sound)
5. Level up (level_up sound)
6. Complete streaks (streak_complete sound)

