import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/sound_service.dart';

/// Extension to add sound/haptic feedback to buttons easily
extension SoundButtonExtension on Widget {
  /// Wrap a button with automatic tap sound on press
  /// 
  /// Example:
  /// ```dart
  /// ElevatedButton(
  ///   onPressed: () => print('Clicked'),
  ///   child: Text('Click me'),
  /// ).withTapSound(ref)
  /// ```
  Widget withTapSound(WidgetRef ref) {
    return _TapSoundWrapper(
      soundService: ref.read(soundServiceProvider),
      child: this,
    );
  }

  /// Wrap a button with haptic feedback only (no sound)
  /// 
  /// Example:
  /// ```dart
  /// TextButton(
  ///   onPressed: () => print('Clicked'),
  ///   child: Text('Click me'),
  /// ).withHaptic(ref)
  /// ```
  Widget withHaptic(WidgetRef ref) {
    return _HapticWrapper(
      soundService: ref.read(soundServiceProvider),
      child: this,
    );
  }
}

/// Internal wrapper widget for tap sound
class _TapSoundWrapper extends StatelessWidget {
  final Widget child;
  final SoundService soundService;

  const _TapSoundWrapper({
    required this.child,
    required this.soundService,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => soundService.playTap(),
      child: child,
    );
  }
}

/// Internal wrapper widget for haptic only
class _HapticWrapper extends StatelessWidget {
  final Widget child;
  final SoundService soundService;

  const _HapticWrapper({
    required this.child,
    required this.soundService,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => soundService.playHaptic(),
      child: child,
    );
  }
}

/// Enhanced button widgets with built-in sound effects
class SoundButton extends ConsumerWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final ButtonStyle? style;
  final bool playSound;

  const SoundButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.style,
    this.playSound = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final soundService = ref.read(soundServiceProvider);

    return ElevatedButton(
      onPressed: onPressed == null
          ? null
          : () {
              if (playSound) {
                soundService.playTap();
              }
              onPressed!();
            },
      style: style,
      child: child,
    );
  }
}

/// Text button with sound effects
class SoundTextButton extends ConsumerWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final ButtonStyle? style;
  final bool playSound;

  const SoundTextButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.style,
    this.playSound = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final soundService = ref.read(soundServiceProvider);

    return TextButton(
      onPressed: onPressed == null
          ? null
          : () {
              if (playSound) {
                soundService.playTap();
              }
              onPressed!();
            },
      style: style,
      child: child,
    );
  }
}

/// Outlined button with sound effects
class SoundOutlinedButton extends ConsumerWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final ButtonStyle? style;
  final bool playSound;

  const SoundOutlinedButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.style,
    this.playSound = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final soundService = ref.read(soundServiceProvider);

    return OutlinedButton(
      onPressed: onPressed == null
          ? null
          : () {
              if (playSound) {
                soundService.playTap();
              }
              onPressed!();
            },
      style: style,
      child: child,
    );
  }
}

/// Icon button with sound effects
class SoundIconButton extends ConsumerWidget {
  final VoidCallback? onPressed;
  final Widget icon;
  final double? iconSize;
  final Color? color;
  final String? tooltip;
  final bool playSound;

  const SoundIconButton({
    super.key,
    required this.onPressed,
    required this.icon,
    this.iconSize,
    this.color,
    this.tooltip,
    this.playSound = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final soundService = ref.read(soundServiceProvider);

    return IconButton(
      onPressed: onPressed == null
          ? null
          : () {
              if (playSound) {
                soundService.playTap();
              }
              onPressed!();
            },
      icon: icon,
      iconSize: iconSize,
      color: color,
      tooltip: tooltip,
    );
  }
}

