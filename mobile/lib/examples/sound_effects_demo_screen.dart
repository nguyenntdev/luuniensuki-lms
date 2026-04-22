import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/services/sound_service.dart';
import '../../core/widgets/sound_button.dart';
import '../../core/theme/app_colors.dart';

/// Example screen demonstrating sound effects usage
class SoundEffectsDemoScreen extends ConsumerWidget {
  const SoundEffectsDemoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final soundService = ref.read(soundServiceProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sound Effects Demo'),
        backgroundColor: AppColors.primary,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Header
          Card(
            color: AppColors.info.withOpacity(0.1),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sound Effects Test',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Tap buttons below to test different sound effects. '
                    'Go to Settings to enable/disable sounds.',
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Quiz Sounds Section
          _buildSection(
            context,
            title: '📝 Quiz Sounds',
            children: [
              SoundButton(
                onPressed: () {
                  // Sound plays automatically via SoundButton
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.success,
                  foregroundColor: Colors.white,
                ),
                child: const Text('✓ Correct Answer'),
              ),
              const SizedBox(height: 12),
              SoundButton(
                onPressed: () async {
                  // Manual sound (SoundButton already plays tap)
                  await Future.delayed(const Duration(milliseconds: 100));
                  await soundService.playWrong();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.error,
                  foregroundColor: Colors.white,
                ),
                child: const Text('✗ Wrong Answer'),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Achievement Sounds Section
          _buildSection(
            context,
            title: '🏆 Achievement Sounds',
            children: [
              SoundButton(
                onPressed: () async {
                  await Future.delayed(const Duration(milliseconds: 100));
                  await soundService.playXpGain();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.warning,
                  foregroundColor: Colors.white,
                ),
                child: const Text('⭐ XP Gained'),
              ),
              const SizedBox(height: 12),
              SoundButton(
                onPressed: () async {
                  await Future.delayed(const Duration(milliseconds: 100));
                  await soundService.playLevelUp();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.info,
                  foregroundColor: Colors.white,
                ),
                child: const Text('🎉 Level Up'),
              ),
              const SizedBox(height: 12),
              SoundButton(
                onPressed: () async {
                  await Future.delayed(const Duration(milliseconds: 100));
                  await soundService.playStreakComplete();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                ),
                child: const Text('🔥 Streak Complete'),
              ),
              const SizedBox(height: 12),
              SoundButton(
                onPressed: () async {
                  await Future.delayed(const Duration(milliseconds: 100));
                  await soundService.playLessonComplete();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.success,
                  foregroundColor: Colors.white,
                ),
                child: const Text('📚 Lesson Complete'),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Button Variants Section
          _buildSection(
            context,
            title: '🎮 Button Variants',
            children: [
              SoundButton(
                onPressed: () {},
                child: const Text('Elevated Button'),
              ),
              const SizedBox(height: 12),
              SoundTextButton(
                onPressed: () {},
                child: const Text('Text Button'),
              ),
              const SizedBox(height: 12),
              SoundOutlinedButton(
                onPressed: () {},
                child: const Text('Outlined Button'),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SoundIconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.favorite),
                    color: AppColors.error,
                  ),
                  const SizedBox(width: 16),
                  SoundIconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.star),
                    color: AppColors.warning,
                  ),
                  const SizedBox(width: 16),
                  SoundIconButton(
                    onPressed: () {},
                    icon: const Icon(Icons.thumb_up),
                    color: AppColors.success,
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Haptic Only Section
          _buildSection(
            context,
            title: '📳 Haptic Feedback Only',
            children: [
              ElevatedButton(
                onPressed: () {
                  soundService.playHaptic();
                },
                child: const Text('Haptic Feedback (No Sound)'),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Info Card
          Card(
            color: AppColors.warning.withOpacity(0.1),
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '💡 Tips:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Text('• Sounds respect your device volume'),
                  Text('• Haptic feedback works on supported devices'),
                  Text('• Toggle sounds in Settings → Sound & Effects'),
                  Text('• Some sounds may use haptic when files are missing'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 12),
        ...children,
      ],
    );
  }
}

