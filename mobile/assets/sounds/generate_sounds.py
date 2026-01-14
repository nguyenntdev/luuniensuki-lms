#!/usr/bin/env python3
"""
Sound Generator for Luuniensuki LMS
Generates simple beep tone placeholder sounds for the app.

Requirements:
    pip install pydub numpy

Usage:
    python3 generate_sounds.py
"""

import os
import sys

try:
    from pydub.generators import Sine, Square
    from pydub import AudioSegment
    import numpy as np
except ImportError:
    print("❌ Error: Required packages not installed")
    print("\nPlease install required packages:")
    print("  pip3 install pydub numpy")
    print("\nOptional (for MP3 export):")
    print("  brew install ffmpeg  # macOS")
    print("  apt-get install ffmpeg  # Ubuntu/Debian")
    sys.exit(1)

# Output directory
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_tone(frequency, duration_ms, fade_ms=20, wave_type='sine'):
    """Create a tone with specified frequency and duration."""
    if wave_type == 'square':
        tone = Square(frequency).to_audio_segment(duration=duration_ms)
    else:
        tone = Sine(frequency).to_audio_segment(duration=duration_ms)
    
    return tone.fade_in(fade_ms).fade_out(fade_ms)

def create_chord(frequencies, duration_ms, fade_ms=20):
    """Create a chord from multiple frequencies."""
    tones = [create_tone(freq, duration_ms, 0) for freq in frequencies]
    chord = tones[0]
    for tone in tones[1:]:
        chord = chord.overlay(tone)
    return chord.fade_in(fade_ms).fade_out(fade_ms)

def create_sequence(tones, gap_ms=0):
    """Create a sequence of tones with optional gap."""
    result = tones[0]
    silence = AudioSegment.silent(duration=gap_ms)
    for tone in tones[1:]:
        result = result + silence + tone
    return result

def export_sound(audio, filename, format='mp3'):
    """Export audio to file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        audio.export(filepath, format=format)
        duration_sec = len(audio) / 1000.0
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  ✅ {filename:<25} ({duration_sec:.2f}s, {size_kb:.1f}KB)")
        return True
    except Exception as e:
        print(f"  ❌ {filename:<25} Error: {e}")
        return False

def generate_all_sounds():
    """Generate all sound effects."""
    print("\n🎵 Generating Sound Effects for Luuniensuki LMS\n")
    print("=" * 60)
    
    success_count = 0
    total_count = 7
    
    # 1. Correct Sound - Pleasant major chord (C-E-G)
    print("\n1. Correct Answer Sound")
    correct = create_chord([523, 659, 784], 400, fade_ms=30)
    if export_sound(correct, "correct.mp3"):
        success_count += 1
    
    # 2. Wrong Sound - Descending tone
    print("\n2. Wrong Answer Sound")
    wrong_high = create_tone(330, 150, wave_type='square')
    wrong_low = create_tone(220, 200, wave_type='square')
    wrong = wrong_high + wrong_low
    if export_sound(wrong, "wrong.mp3"):
        success_count += 1
    
    # 3. Tap Sound - Short click
    print("\n3. Button Tap Sound")
    tap = create_tone(880, 60, fade_ms=10)
    if export_sound(tap, "tap.mp3"):
        success_count += 1
    
    # 4. XP Gain - Ascending chirp
    print("\n4. XP Gain Sound")
    xp1 = create_tone(523, 120)
    xp2 = create_tone(659, 120)
    xp3 = create_tone(784, 180)
    xp_gain = create_sequence([xp1, xp2, xp3], gap_ms=20)
    if export_sound(xp_gain, "xp_gain.mp3"):
        success_count += 1
    
    # 5. Level Up - Fanfare
    print("\n5. Level Up Sound")
    level1 = create_chord([523, 659], 180)
    level2 = create_chord([659, 784], 180)
    level3 = create_chord([784, 988], 180)
    level4 = create_chord([1047, 1319], 350)
    level_up = create_sequence([level1, level2, level3, level4], gap_ms=30)
    if export_sound(level_up, "level_up.mp3"):
        success_count += 1
    
    # 6. Streak Complete - Rising sequence
    print("\n6. Streak Complete Sound")
    streak1 = create_tone(659, 100)
    streak2 = create_tone(784, 100)
    streak3 = create_tone(988, 100)
    streak4 = create_tone(1047, 150)
    streak = create_sequence([streak1, streak2, streak3, streak4], gap_ms=30)
    if export_sound(streak, "streak_complete.mp3"):
        success_count += 1
    
    # 7. Lesson Complete - Success jingle
    print("\n7. Lesson Complete Sound")
    lesson1 = create_chord([523, 659], 200)
    lesson2 = create_chord([659, 784], 200)
    lesson3 = create_chord([784, 988], 200)
    lesson4 = create_chord([659, 784, 988], 400)
    lesson = create_sequence([lesson1, lesson2, lesson3, lesson4], gap_ms=40)
    if export_sound(lesson, "lesson_complete.mp3"):
        success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"\n✨ Generated {success_count}/{total_count} sound files successfully!")
    print(f"\n📂 Files saved to: {OUTPUT_DIR}\n")
    
    if success_count < total_count:
        print("⚠️  Some files failed to generate. Check errors above.")
        print("💡 Make sure ffmpeg is installed for MP3 export.")
        return False
    
    return True

if __name__ == "__main__":
    print("🎵 Luuniensuki LMS - Sound Generator")
    print("=" * 60)
    
    success = generate_all_sounds()
    
    if success:
        print("✅ All sounds generated successfully!")
        print("\n📝 Next steps:")
        print("  1. Listen to the generated sounds")
        print("  2. Run the Flutter app to test")
        print("  3. Replace with professional sounds if needed")
        sys.exit(0)
    else:
        print("\n❌ Some sounds failed to generate")
        sys.exit(1)

