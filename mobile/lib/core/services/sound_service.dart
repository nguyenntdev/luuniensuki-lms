import 'package:flutter/services.dart';
import 'package:just_audio/just_audio.dart';
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
          print('Warning: Sound file not found for $effect at $assetPath');
          _players[effect] = player; // Keep player for haptic fallback
        }
      }

      _initialized = true;
    } catch (e) {
      print('Error initializing sound service: $e');
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
      switch (effect) {
        case SoundEffect.correct:
          await HapticFeedback.lightImpact();
          break;
        case SoundEffect.wrong:
          await HapticFeedback.heavyImpact();
          await Future.delayed(const Duration(milliseconds: 100));
          await HapticFeedback.heavyImpact();
          break;
        case SoundEffect.tap:
          await HapticFeedback.selectionClick();
          break;
        case SoundEffect.xpGain:
          await HapticFeedback.mediumImpact();
          break;
        case SoundEffect.levelUp:
          await HapticFeedback.heavyImpact();
          await Future.delayed(const Duration(milliseconds: 50));
          await HapticFeedback.heavyImpact();
          await Future.delayed(const Duration(milliseconds: 50));
          await HapticFeedback.vibrate();
          break;
        case SoundEffect.streakComplete:
          await HapticFeedback.lightImpact();
          await Future.delayed(const Duration(milliseconds: 40));
          await HapticFeedback.mediumImpact();
          await Future.delayed(const Duration(milliseconds: 40));
          await HapticFeedback.heavyImpact();
          break;
        case SoundEffect.lessonComplete:
          await HapticFeedback.mediumImpact();
          await Future.delayed(const Duration(milliseconds: 60));
          await HapticFeedback.heavyImpact();
          break;
      }
    } catch (e) {
      // Haptic feedback not supported or error occurred
      print('Haptic feedback error: $e');
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

