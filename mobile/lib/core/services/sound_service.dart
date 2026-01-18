import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:just_audio/just_audio.dart';
import 'package:vibration/vibration.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../features/settings/presentation/providers/settings_provider.dart';

/// Sound effect types available in the app
enum SoundEffect {
  correct,
  wrong,
  tap,
  xpGain,
  levelUp,
  streakComplete,
  lessonComplete,
}

/// Service for managing sound effects and haptic feedback
class SoundService {
  final Map<SoundEffect, AudioPlayer> _players = {};
  final Ref _ref;
  bool _initialized = false;

  SoundService(this._ref);

  /// Initialize all audio players
  Future<void> initialize() async {
    if (_initialized) return;

    try {
      // Pre-load all sound effects
      for (final effect in SoundEffect.values) {
        final player = AudioPlayer();
        final assetPath = _getAssetPath(effect);
        
        try {
          await player.setAsset(assetPath);
          _players[effect] = player;
        } catch (e) {
          // Sound file not found - use haptic feedback as fallback
          if (kDebugMode) {
            print('Warning: Sound file not found for $effect at $assetPath');
          }
          _players[effect] = player; // Keep player for haptic fallback
        }
      }

      _initialized = true;
    } catch (e) {
      if (kDebugMode) {
        print('Error initializing sound service: $e');
      }
    }
  }

  /// Play a sound effect
  Future<void> play(SoundEffect effect) async {
    // Check if sound effects are enabled in settings
    final settings = _ref.read(settingsNotifierProvider);
    if (!settings.soundEffectsEnabled) {
      // Play haptic feedback instead
      await _playHaptic(effect);
      return;
    }

    if (!_initialized) {
      await initialize();
    }

    final player = _players[effect];
    if (player == null) return;

    try {
      // Check if sound file exists by checking duration
      final duration = player.duration;
      
      if (duration != null && duration.inMilliseconds > 0) {
        // Sound file exists, play it
        await player.seek(Duration.zero);
        await player.play();
      } else {
        // Sound file doesn't exist, use haptic feedback
        await _playHaptic(effect);
      }
    } catch (e) {
      // Fallback to haptic feedback on error
      await _playHaptic(effect);
    }
  }

  /// Play haptic feedback as fallback or complement
  Future<void> _playHaptic(SoundEffect effect) async {
    try {
      // Check if device supports vibration
      final hasVibrator = await Vibration.hasVibrator() ?? false;
      if (!hasVibrator) return;

      switch (effect) {
        case SoundEffect.correct:
          // Light success vibration
          await Vibration.vibrate(duration: 50, amplitude: 128);
          break;
        
        case SoundEffect.wrong:
          // Double tap for error
          await Vibration.vibrate(duration: 100, amplitude: 200);
          await Future.delayed(const Duration(milliseconds: 100));
          await Vibration.vibrate(duration: 100, amplitude: 200);
          break;
        
        case SoundEffect.tap:
          // Very light tap
          await Vibration.vibrate(duration: 30, amplitude: 64);
          break;
        
        case SoundEffect.xpGain:
          // Medium celebration
          await Vibration.vibrate(duration: 80, amplitude: 150);
          break;
        
        case SoundEffect.levelUp:
          // Strong celebration pattern
          await Vibration.vibrate(duration: 100, amplitude: 255);
          await Future.delayed(const Duration(milliseconds: 50));
          await Vibration.vibrate(duration: 100, amplitude: 255);
          await Future.delayed(const Duration(milliseconds: 50));
          await Vibration.vibrate(duration: 200, amplitude: 255);
          break;
        
        case SoundEffect.streakComplete:
          // Ascending pattern
          await Vibration.vibrate(duration: 60, amplitude: 128);
          await Future.delayed(const Duration(milliseconds: 40));
          await Vibration.vibrate(duration: 60, amplitude: 180);
          await Future.delayed(const Duration(milliseconds: 40));
          await Vibration.vibrate(duration: 80, amplitude: 230);
          break;
        
        case SoundEffect.lessonComplete:
          // Success sequence
          await Vibration.vibrate(duration: 80, amplitude: 180);
          await Future.delayed(const Duration(milliseconds: 60));
          await Vibration.vibrate(duration: 150, amplitude: 200);
          break;
      }
    } catch (e) {
      // Vibration not supported or error occurred
      if (kDebugMode) {
        print('Haptic feedback error: $e');
      }
    }
  }

  /// Get asset path for sound effect
  String _getAssetPath(SoundEffect effect) {
    final fileName = switch (effect) {
      SoundEffect.correct => 'correct.mp3',
      SoundEffect.wrong => 'wrong.mp3',
      SoundEffect.tap => 'tap.mp3',
      SoundEffect.xpGain => 'xp_gain.mp3',
      SoundEffect.levelUp => 'level_up.mp3',
      SoundEffect.streakComplete => 'streak_complete.mp3',
      SoundEffect.lessonComplete => 'lesson_complete.mp3',
    };
    return 'assets/sounds/$fileName';
  }

  /// Play haptic feedback without sound (for button taps)
  Future<void> playHaptic() async {
    await _playHaptic(SoundEffect.tap);
  }

  /// Convenience methods for common sounds
  Future<void> playCorrect() => play(SoundEffect.correct);
  Future<void> playWrong() => play(SoundEffect.wrong);
  Future<void> playTap() => play(SoundEffect.tap);
  Future<void> playXpGain() => play(SoundEffect.xpGain);
  Future<void> playLevelUp() => play(SoundEffect.levelUp);
  Future<void> playStreakComplete() => play(SoundEffect.streakComplete);
  Future<void> playLessonComplete() => play(SoundEffect.lessonComplete);

  /// Dispose all audio players
  void dispose() {
    for (final player in _players.values) {
      player.dispose();
    }
    _players.clear();
    _initialized = false;
  }
}

/// Provider for sound service
final soundServiceProvider = Provider<SoundService>((ref) {
  final service = SoundService(ref);

  // Initialize on first access
  service.initialize();

  // Dispose when provider is destroyed
  ref.onDispose(() {
    service.dispose();
  });

  return service;
});

