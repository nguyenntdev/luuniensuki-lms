import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../widgets/backgrounds/modern_gradient_background.dart';
import '../widgets/glass/glass_container.dart';

/// Example screen demonstrating all modern background variants
/// Shows different use cases and performance characteristics
class ModernBackgroundExample extends StatefulWidget {
  const ModernBackgroundExample({super.key});

  @override
  State<ModernBackgroundExample> createState() =>
      _ModernBackgroundExampleState();
}

class _ModernBackgroundExampleState extends State<ModernBackgroundExample> {
  int _selectedIndex = 0;

  final List<_BackgroundDemo> _demos = const [
    _BackgroundDemo(
      title: 'Standard Gradient',
      description: 'Static mesh gradient with noise overlay. Best performance.',
      type: _BackgroundType.standard,
    ),
    _BackgroundDemo(
      title: 'Animated Mesh',
      description: 'Smooth animated mesh gradient. Moderate performance.',
      type: _BackgroundType.mesh,
    ),
    _BackgroundDemo(
      title: 'Animated Particles',
      description: 'Floating particles with blur. Rich visuals.',
      type: _BackgroundType.particles,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _buildBackground(),
    );
  }

  Widget _buildBackground() {
    final demo = _demos[_selectedIndex];

    switch (demo.type) {
      case _BackgroundType.standard:
        return ModernGradientBackground(
          child: _buildContent(demo),
        );
      case _BackgroundType.mesh:
        return ModernGradientBackgroundMesh(
          child: _buildContent(demo),
        );
      case _BackgroundType.particles:
        return ModernGradientBackgroundAnimated(
          particleCount: 15,
          child: _buildContent(demo),
        );
    }
  }

  Widget _buildContent(_BackgroundDemo demo) {
    return SafeArea(
      child: Column(
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: GlassContainer(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      demo.title,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      demo.description,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Content area
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              children: [
                _buildFeatureCard(
                  'Deep Purple (#1a0a2e)',
                  'Rich imperial purple base',
                  AppColors.modernPurple,
                ),
                const SizedBox(height: AppSpacing.md),
                _buildFeatureCard(
                  'Rich Blue (#16213e)',
                  'Deep ocean blue accent',
                  AppColors.modernBlue,
                ),
                const SizedBox(height: AppSpacing.md),
                _buildFeatureCard(
                  'Warm Gold (#e8b44c)',
                  'Vietnamese imperial gold',
                  AppColors.primary,
                ),
                const SizedBox(height: AppSpacing.md),
                _buildInfoCard(),
              ],
            ),
          ),

          // Bottom navigation
          _buildBottomNav(),
        ],
      ),
    );
  }

  Widget _buildFeatureCard(String title, String description, Color color) {
    return GlassContainer(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Row(
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [
                  BoxShadow(
                    color: color.withOpacity(0.4),
                    blurRadius: 15,
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return GlassContainer(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.info_outline, color: AppColors.primary, size: 20),
                SizedBox(width: 8),
                Text(
                  'Design Features',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            _buildFeatureRow('✓ Animated mesh gradients'),
            _buildFeatureRow('✓ Floating particles with blur'),
            _buildFeatureRow('✓ Noise texture overlay'),
            _buildFeatureRow('✓ 60fps smooth animations'),
            _buildFeatureRow('✓ RepaintBoundary optimized'),
            _buildFeatureRow('✓ Dark theme compatible'),
            _buildFeatureRow('✓ Glassmorphism friendly'),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureRow(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 13,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      margin: const EdgeInsets.all(AppSpacing.md),
      child: GlassContainer(
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.sm,
            vertical: AppSpacing.xs,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(_demos.length, (index) {
              final isSelected = index == _selectedIndex;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _selectedIndex = index),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: AppSpacing.sm,
                    ),
                    decoration: BoxDecoration(
                      gradient: isSelected ? AppColors.primaryGradient : null,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Center(
                      child: Text(
                        _demos[index].title.split(' ')[0],
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight:
                              isSelected ? FontWeight.bold : FontWeight.w500,
                          color: isSelected
                              ? AppColors.onPrimary
                              : AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

/// Background demo configuration
class _BackgroundDemo {
  final String title;
  final String description;
  final _BackgroundType type;

  const _BackgroundDemo({
    required this.title,
    required this.description,
    required this.type,
  });
}

/// Background type enum
enum _BackgroundType {
  standard,
  mesh,
  particles,
}
