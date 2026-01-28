import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/utils/url_utils.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/animations/index.dart';
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';

final _dailyLessonsProvider = FutureProvider<List<_DailyLesson>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);

  try {
    debugPrint('🔍 [DailyLessons] Fetching user learning path motifs...');
    // First try to get user's learning path motifs
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.dashboardSummary,
      parser: (json) => json as Map<String, dynamic>,
    );
    final rawMotifs = response['path_motifs'];
    debugPrint('[DailyLessons] Dashboard response: path_motifs = $rawMotifs');

    if (rawMotifs is List && rawMotifs.isNotEmpty) {
      final lessons = rawMotifs
          .map((item) {
            final lesson = _DailyLesson.fromDashboard(item);
            if (lesson != null) {
              debugPrint(
                  '[DailyLessons] Parsed lesson from dashboard: ${lesson.name}, thumbnailUrl: ${lesson.thumbnailUrl}');
            }
            return lesson;
          })
          .whereType<_DailyLesson>()
          .toList();
      if (lessons.isNotEmpty) {
        debugPrint(
            '[DailyLessons] Loaded ${lessons.length} lessons from dashboard');
        return lessons;
      }
    }
  } catch (e, stackTrace) {
    debugPrint('[DailyLessons] Error fetching dashboard: $e');
    debugPrint('[DailyLessons] Stack trace: $stackTrace');
    // Continue to fallback
  }

  // Fallback: fetch recommended motifs from cao-dinh urn (demo urn)
  try {
    debugPrint(
        '🔍 [DailyLessons] Fallback: Fetching motifs from cao-dinh urn...');
    final urnResponse = await apiClient.get<Map<String, dynamic>>(
      '/api/v1/urns/cao-dinh',
      parser: (json) => json as Map<String, dynamic>,
    );
    final motifs = urnResponse['motifs'] as List<dynamic>?;
    debugPrint('[DailyLessons] Urn response: motifs count = ${motifs?.length}');

    if (motifs != null && motifs.isNotEmpty) {
      final lessons = motifs
          .take(6)
          .map((item) {
            final lesson = _DailyLesson.fromMotif(item as Map<String, dynamic>);
            if (lesson != null) {
              debugPrint(
                  '[DailyLessons] Parsed lesson from motif: ${lesson.name}, thumbnailUrl: ${lesson.thumbnailUrl}');
            }
            return lesson;
          })
          .whereType<_DailyLesson>()
          .toList();
      if (lessons.isNotEmpty) {
        debugPrint('[DailyLessons] Loaded ${lessons.length} lessons from urn');
        return lessons;
      }
    }
  } catch (e, stackTrace) {
    debugPrint('[DailyLessons] Error fetching urn motifs: $e');
    debugPrint('[DailyLessons] Stack trace: $stackTrace');
    // Continue to mock fallback
  }

  debugPrint('[DailyLessons] Falling back to mock lessons');
  return _getMockLessons();
});

/// Widget showing today's recommended lessons in a horizontal scrollable list.
class DailyLessonsWidget extends ConsumerWidget {
  const DailyLessonsWidget({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lessonsAsync = ref.watch(_dailyLessonsProvider);

    return lessonsAsync.when(
      loading: () => SizedBox(
        height: 190,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
          itemCount: 3,
          itemBuilder: (context, index) => Padding(
            padding: EdgeInsets.only(
              right: index < 2 ? AppSpacing.md : 0,
            ),
            child: _DailyLessonShimmerCard(),
          ),
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
            child: StaggeredAnimationWrapper(
              index: index,
              child: _DailyLessonCard(
                lesson: lesson,
                width: cardWidth,
              ),
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

class _DailyLessonCardState extends State<_DailyLessonCard>
    with TickerProviderStateMixin {
  bool _isPressed = false;
  late AnimationController _floatController;
  late AnimationController _pulseController;
  late Animation<double> _floatAnimation;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();

    // Floating animation - 3 second cycle, -2px to +2px
    _floatController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    )..repeat(reverse: true);

    _floatAnimation = Tween<double>(
      begin: -2.0,
      end: 2.0,
    ).animate(
      CurvedAnimation(
        parent: _floatController,
        curve: Curves.easeInOut,
      ),
    );

    // Pulse animation for high-value XP (>50)
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.15,
    ).animate(
      CurvedAnimation(
        parent: _pulseController,
        curve: Curves.easeInOut,
      ),
    );

    if (widget.lesson.xpReward > 50) {
      _pulseController.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _floatController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isNew = widget.lesson.status == _LessonStatus.newLesson;
    final statusColor = isNew ? AppColors.info : AppColors.warning;

    return AnimatedBuilder(
      animation: _floatAnimation,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, _floatAnimation.value),
          child: child,
        );
      },
      child: GestureDetector(
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
                        _buildThumbnail(statusColor),
                        Positioned(
                          top: AppSpacing.sm,
                          right: AppSpacing.sm,
                          child: _buildStatusBadge(statusColor, isNew),
                        ),
                        // Progress ring for review lessons
                        if (!isNew &&
                            widget.lesson.status == _LessonStatus.review)
                          Positioned(
                            top: AppSpacing.sm,
                            left: AppSpacing.sm,
                            child: _buildProgressRing(),
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
                            _buildXpBadge(),
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

  Widget _buildProgressRing() {
    // Simple circular progress indicator for review lessons
    // Assuming review lessons have some progress (60-80%)
    const progress = 0.7; // Mock progress value

    return Container(
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        shape: BoxShape.circle,
      ),
      child: Padding(
        padding: const EdgeInsets.all(4),
        child: CircularProgressIndicator(
          value: progress,
          strokeWidth: 2.5,
          backgroundColor: Colors.white.withOpacity(0.2),
          valueColor: const AlwaysStoppedAnimation<Color>(AppColors.warning),
        ),
      ),
    );
  }

  Widget _buildXpBadge() {
    final isHighValue = widget.lesson.xpReward > 50;

    Widget badge = Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 6,
        vertical: 2,
      ),
      decoration: BoxDecoration(
        color: AppColors.xpGold.withOpacity(0.2),
        borderRadius: BorderRadius.circular(6),
        // Add subtle glow for all XP badges
        boxShadow: [
          BoxShadow(
            color: AppColors.xpGold.withOpacity(0.3),
            blurRadius: 8,
            spreadRadius: 0,
          ),
        ],
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
    );

    // Add pulse animation for high-value XP
    if (isHighValue) {
      return ScaleTransition(
        scale: _pulseAnimation,
        child: badge,
      );
    }

    return badge;
  }

  Widget _buildThumbnail(Color statusColor) {
    final rawUrl = widget.lesson.thumbnailUrl;
    if (rawUrl == null || rawUrl.trim().isEmpty) {
      return _buildPlaceholder(statusColor);
    }

    final imageUrl = UrlUtils.getImageUrl(rawUrl);
    if (imageUrl.isEmpty) {
      return _buildPlaceholder(statusColor);
    }

    return CachedNetworkImage(
      imageUrl: imageUrl,
      fit: BoxFit.cover,
      placeholder: (_, __) => _buildPlaceholder(statusColor),
      errorWidget: (_, __, ___) => _buildPlaceholder(statusColor),
    );
  }

  Widget _buildPlaceholder(Color statusColor) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            statusColor.withOpacity(0.15),
            Colors.white.withOpacity(0.05),
          ],
        ),
      ),
      child: Center(
        child: Icon(
          Icons.terrain,
          size: widget.width * 0.45,
          color: Colors.white.withOpacity(0.35),
        ),
      ),
    );
  }
}

/// Shimmer loading card for daily lesson
class _DailyLessonShimmerCard extends StatelessWidget {
  const _DailyLessonShimmerCard();

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final cardWidth = width < 360 ? 140.0 : 170.0;

    return Container(
      width: cardWidth,
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
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Top image area shimmer
            Expanded(
              child: ShimmerSkeleton(
                width: double.infinity,
                height: double.infinity,
                borderRadius: BorderRadius.zero,
              ),
            ),
            // Bottom content area
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
                  // Lesson name shimmer
                  ShimmerSkeleton(
                    width: cardWidth * 0.7,
                    height: 14,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  const SizedBox(height: 4),
                  // English name shimmer
                  ShimmerSkeleton(
                    width: cardWidth * 0.5,
                    height: 11,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  AppSpacing.verticalSpaceXS,
                  // Category and XP badge shimmer
                  Row(
                    children: [
                      Expanded(
                        child: ShimmerSkeleton(
                          width: 50,
                          height: 10,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      ShimmerSkeleton(
                        width: 50,
                        height: 16,
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
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
      thumbnailUrl:
          'https://lms.histolab.icu/assets/ban-duc-noi/CAO%20DINH/CAO%20DINH.jpg',
    ),
    _DailyLesson(
      name: 'Hoa sen',
      nameEn: 'Lotus Flower',
      status: _LessonStatus.review,
      xpReward: 5,
      category: 'Thảo Mộc',
      thumbnailUrl:
          'https://lms.histolab.icu/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg',
    ),
    _DailyLesson(
      name: 'Phượng hoàng',
      nameEn: 'Phoenix',
      status: _LessonStatus.newLesson,
      xpReward: 10,
      category: 'Linh Thú',
      thumbnailUrl:
          'https://lms.histolab.icu/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg',
    ),
    _DailyLesson(
      name: 'Cây trúc',
      nameEn: 'Bamboo',
      status: _LessonStatus.review,
      xpReward: 5,
      category: 'Thảo Mộc',
      thumbnailUrl:
          'https://lms.histolab.icu/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg',
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
  final String? thumbnailUrl;

  _DailyLesson({
    required this.name,
    this.nameEn,
    required this.status,
    required this.xpReward,
    required this.category,
    this.motifId,
    this.thumbnailUrl,
  });

  static _DailyLesson? fromDashboard(dynamic item) {
    if (item is! Map<String, dynamic>) return null;
    final id = item['id']?.toString();
    final name = item['name']?.toString();
    if (id == null || name == null) return null;

    final status = _LessonStatus.fromProgress(item['status']?.toString());
    final xpReward = status == _LessonStatus.newLesson ? 10 : 5;
    final thumbnailUrl =
        item['thumbnail_url']?.toString() ?? item['thumbnailUrl']?.toString();

    return _DailyLesson(
      name: name,
      nameEn: item['name_en']?.toString(),
      status: status,
      xpReward: xpReward,
      category: 'Lộ trình',
      motifId: id,
      thumbnailUrl: thumbnailUrl,
    );
  }

  /// Create from motif API response (fallback for new users)
  static _DailyLesson? fromMotif(Map<String, dynamic> item) {
    final id = item['id']?.toString();
    final name = item['name']?.toString();
    if (id == null || name == null) return null;

    // Map category to Vietnamese display name
    final category = item['category']?.toString() ?? 'other';
    final categoryDisplay = _getCategoryDisplay(category);

    return _DailyLesson(
      name: name,
      nameEn: item['name_en']?.toString(),
      status: _LessonStatus.newLesson, // All are new for new users
      xpReward: 10,
      category: categoryDisplay,
      motifId: id,
      thumbnailUrl: item['thumbnail_url']?.toString(),
    );
  }

  static String _getCategoryDisplay(String category) {
    switch (category) {
      case 'linh_thu':
        return 'Linh Thú';
      case 'thao_moc':
        return 'Thảo Mộc';
      case 'nong_nghiep':
        return 'Nông Nghiệp';
      case 'kien_truc':
        return 'Kiến Trúc';
      case 'thien_nhien':
        return 'Thiên Nhiên';
      case 'dong_vat':
        return 'Động Vật';
      case 'vu_khi':
        return 'Vũ Khí';
      case 'do_vat':
        return 'Đồ Vật';
      default:
        return 'Họa Tiết';
    }
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
