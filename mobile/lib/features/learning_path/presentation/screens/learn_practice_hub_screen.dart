import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../practice/presentation/screens/practice_screen.dart';
import 'learning_path_screen.dart';

class LearnPracticeHubScreen extends StatefulWidget {
  const LearnPracticeHubScreen({super.key});

  @override
  State<LearnPracticeHubScreen> createState() => _LearnPracticeHubScreenState();
}

class _LearnPracticeHubScreenState extends State<LearnPracticeHubScreen> {
  int _tabIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        IndexedStack(
          index: _tabIndex,
          children: const [
            LearningPathScreen(),
            PracticeScreen(),
          ],
        ),
        Positioned(
          left: AppSpacing.md,
          right: AppSpacing.md,
          top: MediaQuery.of(context).padding.top + 6,
          child: _buildSegmentedSwitcher(),
        ),
      ],
    );
  }

  Widget _buildSegmentedSwitcher() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: AppColors.surface.withOpacity(0.42),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.glassBorder.withOpacity(0.85)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 14,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(child: _tabButton(0, 'Học tập', Icons.school_rounded)),
          Expanded(
              child: _tabButton(1, 'Luyện tập', Icons.fitness_center_rounded)),
        ],
      ),
    );
  }

  Widget _tabButton(int index, String label, IconData icon) {
    final selected = _tabIndex == index;

    return GestureDetector(
      onTap: () => setState(() => _tabIndex = index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          gradient: selected
              ? LinearGradient(
                  colors: [
                    AppColors.primary.withOpacity(0.92),
                    AppColors.primaryDark.withOpacity(0.9),
                  ],
                )
              : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 17,
              color: selected ? AppColors.onPrimary : AppColors.textSecondary,
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: selected ? AppColors.onPrimary : AppColors.textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
