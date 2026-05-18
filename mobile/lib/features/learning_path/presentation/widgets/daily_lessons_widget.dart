import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../routing/route_names.dart';

final _dailyLessonsProvider = FutureProvider<List<_DailyLesson>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);

  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.dashboardSummary,
      parser: (json) => json as Map<String, dynamic>,
    );
    final rawMotifs = response['path_motifs'];

    if (rawMotifs is List) {
      final lessons = rawMotifs
          .map((item) => _DailyLesson.fromDashboard(item))
          .whereType<_DailyLesson>()
          .toList();
      if (lessons.isNotEmpty) {
        return lessons;
      }
    }
  } catch (_) {
    // Fallback to mock data if dashboard summary is not available.
  }

  return _getMockLessons();
});

/// Widget showing today's recommended lessons in a horizontal scrollable list.
class DailyLessonsWidget extends ConsumerWidget {
  const DailyLessonsWidget({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lessonsAsync = ref.watch(_dailyLessonsProvider);

    return lessonsAsync.when(
      loading: () => const SizedBox(
        height: 190,
        child: Center(
          child: CircularProgressIndicator(color: AppColors.primary),
        ),
      ),
      error: (_, __) => _LessonsList(lessons: _getMockLessons()),
      data: (lessons) => _LessonsList(lessons: lessons.take(6).toList()),
    );
  }
}

class _LessonsList extends StatelessWidget {
  final List<_DailyLesson> lessons;

  const _LessonsList({required this.lessons});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final cardWidth = width < 360 ? 140.0 : 170.0;

    return SizedBox(
      height: 190,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
        scrollDirection: Axis.horizontal,
        itemCount: lessons.length,
        itemBuilder: (context, index) {
          final lesson = lessons[index];
          return Padding(
            padding: EdgeInsets.only(
              right: index < lessons.length - 1 ? AppSpacing.md : 0,
            ),
            child: _DailyLessonCard(
              lesson: lesson,
              width: cardWidth,
            ),
          );
        },
      ),
    );
  }
}

/// Card for a single daily lesson.
class _DailyLessonCard extends StatefulWidget {
  final _DailyLesson lesson;
  final double width;

  const _DailyLessonCard({required this.lesson, required this.width});

  @override
  State<_DailyLessonCard> createState() => _DailyLessonCardState();
}

class _DailyLessonCardState extends State<_DailyLessonCard> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    final isNew = widget.lesson.status == _LessonStatus.newLesson;
    final statusColor = isNew ? AppColors.info : AppColors.warning;

    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        final motifId = widget.lesson.motifId;
        if (motifId != null && motifId.isNotEmpty) {
          context.push(RoutePaths.motif(motifId));
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Bài học đang được cập nhật'),
            ),
          );
        }
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.96 : 1.0,
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeOut,
        child: Container(
          width: widget.width,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Colors.white.withOpacity(0.14),
                Colors.white.withOpacity(0.05),
              ],
            ),
            borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
            border: Border.all(
              color: Colors.white.withOpacity(0.18),
              width: 1.2,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.25),
                blurRadius: 18,
                offset: const Offset(0, 10),
              ),
              BoxShadow(
                color: statusColor.withOpacity(0.12),
                blurRadius: 26,
                spreadRadius: -6,
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              statusColor.withOpacity(0.2),
                              Colors.transparent,
                            ],
                          ),
                        ),
                      ),
                      Align(
                        alignment: Alignment.center,
                        child: Icon(
                          Icons.terrain,
                          size: widget.width * 0.5,
                          color: Colors.white.withOpacity(0.3),
                        ),
                      ),
                      Positioned(
                        top: AppSpacing.sm,
                        right: AppSpacing.sm,
                        child: _buildStatusBadge(statusColor, isNew),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.white.withOpacity(0.08),
                        Colors.white.withOpacity(0.03),
                      ],
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.lesson.name,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (widget.lesson.nameEn != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          widget.lesson.nameEn!,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 11,
                            fontStyle: FontStyle.italic,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                      AppSpacing.verticalSpaceXS,
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              widget.lesson.category,
                              style: TextStyle(
                                color: statusColor,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.xpGold.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  '+${widget.lesson.xpReward}',
                                  style: const TextStyle(
                                    color: AppColors.xpGold,
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(width: 4),
                                const Text(
                                  'XP',
                                  style: TextStyle(
                                    color: AppColors.xpGold,
                                    fontSize: 9,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatusBadge(Color statusColor, bool isNew) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: 4,
      ),
      decoration: BoxDecoration(
        color: statusColor.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: statusColor.withOpacity(0.5),
        ),
      ),
      child: Text(
        isNew ? 'Mới' : 'Ôn tập',
        style: TextStyle(
          color: statusColor,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

List<_DailyLesson> _getMockLessons() {
  return [
    _DailyLesson(
      name: 'Long vân',
      nameEn: 'Cloud Dragon',
      status: _LessonStatus.newLesson,
      xpReward: 10,
      category: 'Linh Thú',
    ),
    _DailyLesson(
      name: 'Hoa sen',
      nameEn: 'Lotus Flower',
      status: _LessonStatus.review,
      xpReward: 5,
      category: 'Thảo Mộc',
    ),
    _DailyLesson(
      name: 'Phượng hoàng',
      nameEn: 'Phoenix',
      status: _LessonStatus.newLesson,
      xpReward: 10,
      category: 'Linh Thú',
    ),
    _DailyLesson(
      name: 'Cây trúc',
      nameEn: 'Bamboo',
      status: _LessonStatus.review,
      xpReward: 5,
      category: 'Thảo Mộc',
    ),
  ];
}

/// Mock data model for daily lesson.
class _DailyLesson {
  final String name;
  final String? nameEn;
  final _LessonStatus status;
  final int xpReward;
  final String category;
  final String? motifId;

  _DailyLesson({
    required this.name,
    this.nameEn,
    required this.status,
    required this.xpReward,
    required this.category,
    this.motifId,
  });

  static _DailyLesson? fromDashboard(dynamic item) {
    if (item is! Map<String, dynamic>) return null;
    final id = item['id']?.toString();
    final name = item['name']?.toString();
    if (id == null || name == null) return null;

    final status = _LessonStatus.fromProgress(item['status']?.toString());
    final xpReward = status == _LessonStatus.newLesson ? 10 : 5;

    return _DailyLesson(
      name: name,
      status: status,
      xpReward: xpReward,
      category: 'Lộ trình',
      motifId: id,
    );
  }
}

/// Status of a daily lesson.
enum _LessonStatus {
  newLesson,
  review;

  static _LessonStatus fromProgress(String? status) {
    switch (status) {
      case 'learned':
      case 'mastered':
        return _LessonStatus.review;
      case 'hidden':
      case 'discovered':
      default:
        return _LessonStatus.newLesson;
    }
  }
}
