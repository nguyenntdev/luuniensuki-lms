import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../data/models/recommendation_dto.dart';
import '../providers/recommendations_provider.dart';

class RecommendationsCard extends ConsumerWidget {
  const RecommendationsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendationsAsync = ref.watch(recommendationsProvider(limit: 5));

    return recommendationsAsync.when(
      data: (data) {
        final continueItems = data.continueLearning ?? [];
        final discoverItems = data.discoverNew ?? [];
        
        if (continueItems.isEmpty && discoverItems.isEmpty) {
          return const SizedBox.shrink();
        }

        return GlassContainer(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.lightbulb_outline,
                    color: AppColors.primary,
                    size: 20,
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Text(
                    'Gợi ý cho bạn',
                    style: AppTypography.textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              
              if (continueItems.isNotEmpty) ...[
                _buildSectionTitle('Tiếp tục học'),
                const SizedBox(height: AppSpacing.xs),
                ...continueItems.take(2).map(
                      (item) => _buildRecommendationItem(context, item),
                    ),
              ],
              
              if (discoverItems.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.sm),
                _buildSectionTitle('Khám phá mới'),
                const SizedBox(height: AppSpacing.xs),
                ...discoverItems.take(2).map(
                      (item) => _buildRecommendationItem(context, item),
                    ),
              ],
            ],
          ),
        );
      },
      loading: () => GlassContainer(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.lightbulb_outline,
                  color: AppColors.primary,
                  size: 20,
                ),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  'Gợi ý cho bạn',
                  style: AppTypography.textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            const Center(
              child: CircularProgressIndicator(
                color: AppColors.primary,
                strokeWidth: 2,
              ),
            ),
          ],
        ),
      ),
      error: (error, stack) => const SizedBox.shrink(),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: AppTypography.textTheme.bodySmall?.copyWith(
        color: Colors.white.withOpacity(0.7),
        fontSize: 12,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
    );
  }

  Widget _buildRecommendationItem(BuildContext context, RecommendationItemDto item) {
    final IconData icon;
    final Color iconColor;
    
    switch (item.reason) {
      case 'continue_learning':
        icon = Icons.play_circle_outline;
        iconColor = AppColors.primary;
        break;
      case 'discover_new':
        icon = Icons.explore;
        iconColor = Colors.blue;
        break;
      case 'review_needed':
        icon = Icons.refresh;
        iconColor = Colors.orange;
        break;
      case 'popular':
        icon = Icons.trending_up;
        iconColor = Colors.purple;
        break;
      default:
        icon = Icons.article_outlined;
        iconColor = Colors.grey;
    }

    return InkWell(
      onTap: () => _navigateToContent(context, item),
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.xs),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: iconColor.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                icon,
                size: 18,
                color: iconColor,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.title,
                    style: AppTypography.textTheme.bodyMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w500,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (item.description != null)
                    Text(
                      item.description!,
                      style: AppTypography.textTheme.bodySmall?.copyWith(
                        color: Colors.white.withOpacity(0.6),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToContent(BuildContext context, RecommendationItemDto item) {
    if (item.contentType == 'lesson') {
      context.push('/lessons/${item.contentId}');
    } else if (item.contentType == 'motif') {
      context.push('/motifs/${item.contentId}');
    }
  }
}

