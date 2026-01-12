import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../providers/explore_provider.dart';
import '../widgets/urn_card.dart';

/// Main explore screen showing a grid of all 9 urns
class ExploreScreen extends ConsumerStatefulWidget {
  const ExploreScreen({super.key});

  @override
  ConsumerState<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends ConsumerState<ExploreScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  bool _hasInitialized = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeOut),
    );
    _animationController.forward();

    // Schedule the initial data load check after first frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkAndLoadData();
    });
  }

  void _checkAndLoadData() {
    if (_hasInitialized) return;

    final authState = ref.read(authNotifierProvider);
    if (authState.isAuthenticated) {
      _hasInitialized = true;
      ref.read(exploreNotifierProvider.notifier).loadUrns();
    } else {
      // Listen for auth state changes
      ref.listenManual(authNotifierProvider, (previous, next) {
        if (!_hasInitialized && next.isAuthenticated) {
          _hasInitialized = true;
          ref.read(exploreNotifierProvider.notifier).loadUrns();
        }
      });
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(exploreNotifierProvider);
    final progress = ref.watch(exploreProgressProvider);
    final authState = ref.watch(authNotifierProvider);

    return AnimatedGradientBackground(
      child: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: Column(
            children: [
              // Header
              _buildHeader(context, progress, authState),

              // Content
              Expanded(
                child: _buildContent(context, ref, state),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(
      BuildContext context, ExploreProgress progress, dynamic authState) {
    // Get user name if authenticated
    String? userName;
    if (authState.isAuthenticated && authState.user != null) {
      userName = authState.user!.name;
    }

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.lg,
        AppSpacing.md,
        AppSpacing.lg,
        AppSpacing.sm,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Welcome message
          if (userName != null) ...[
            Text(
              'Xin chào, $userName!',
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
            AppSpacing.verticalSpaceSM,
          ],

          // Title row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Cửu Đỉnh',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                    AppSpacing.verticalSpaceXS,
                    Text(
                      'Khám phá 9 chiếc đỉnh triều Nguyễn',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 15,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ],
                ),
              ),
              AppSpacing.horizontalSpaceMD,
              // Overall progress
              _buildOverallProgress(progress),
            ],
          ),

          AppSpacing.verticalSpaceLG,

          // Search/Filter placeholder
          _buildSearchBar(context),

          AppSpacing.verticalSpaceMD,

          // Progress summary card
          _buildProgressSummary(progress),
        ],
      ),
    );
  }

  Widget _buildSearchBar(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        border: Border.all(
          color: Colors.white.withOpacity(0.15),
          width: 1,
        ),
      ),
      child: TextField(
        enabled: false, // Placeholder for now
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Tìm kiếm đỉnh... (sắp ra mắt)',
          hintStyle: TextStyle(
            color: Colors.white.withOpacity(0.4),
            fontSize: 15,
          ),
          prefixIcon: Icon(
            Icons.search,
            color: Colors.white.withOpacity(0.5),
          ),
          suffixIcon: Icon(
            Icons.filter_list,
            color: Colors.white.withOpacity(0.5),
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.md,
          ),
        ),
      ),
    );
  }

  Widget _buildOverallProgress(ExploreProgress progress) {
    final percent = (progress.masteryPercent * 100).round();

    return Container(
      width: 64,
      height: 64,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.15),
            Colors.white.withOpacity(0.05),
          ],
        ),
        border: Border.all(
          color: AppColors.primary.withOpacity(0.3),
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.2),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Progress circle
          SizedBox(
            width: 54,
            height: 54,
            child: CircularProgressIndicator(
              value: progress.masteryPercent,
              strokeWidth: 5,
              backgroundColor: Colors.white.withOpacity(0.1),
              valueColor: AlwaysStoppedAnimation<Color>(
                AppColors.primary,
              ),
            ),
          ),
          // Percentage text
          Text(
            '$percent%',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressSummary(ExploreProgress progress) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.12),
            Colors.white.withOpacity(0.06),
          ],
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
        border: Border.all(
          color: Colors.white.withOpacity(0.15),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatColumn(
            icon: Icons.visibility,
            label: 'Khám phá',
            value: '${progress.discoveredMotifs}/${progress.totalMotifs}',
            color: AppColors.info,
          ),
          _buildDivider(),
          _buildStatColumn(
            icon: Icons.school,
            label: 'Học xong',
            value: '${progress.learnedMotifs}/${progress.totalMotifs}',
            color: AppColors.success,
          ),
          _buildDivider(),
          _buildStatColumn(
            icon: Icons.star,
            label: 'Thành thạo',
            value: '${progress.masteredMotifs}/${progress.totalMotifs}',
            color: AppColors.primary,
          ),
        ],
      ),
    );
  }

  Widget _buildStatColumn({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(AppSpacing.sm),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 26),
        ),
        AppSpacing.verticalSpaceXS,
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 17,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.3,
          ),
        ),
        AppSpacing.verticalSpaceXS,
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withOpacity(0.65),
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildDivider() {
    return Container(
      width: 1.5,
      height: 50,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.white.withOpacity(0.0),
            Colors.white.withOpacity(0.2),
            Colors.white.withOpacity(0.0),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    WidgetRef ref,
    ExploreState state,
  ) {
    if (state.isLoading && !state.hasData) {
      return _buildLoadingState();
    }

    if (state.hasError && !state.hasData) {
      return _buildErrorState(ref, state.errorMessage!);
    }

    // Check for empty state
    if (!state.isLoading && !state.hasError && state.urns.isEmpty) {
      return _buildEmptyState(ref);
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(exploreNotifierProvider.notifier).refreshUrns(),
      color: AppColors.primary,
      backgroundColor: AppColors.surface,
      child: LayoutBuilder(
        builder: (context, constraints) {
          // Responsive grid based on width
          int crossAxisCount = 2;
          if (constraints.maxWidth > 600) {
            crossAxisCount = 3;
          }
          if (constraints.maxWidth > 900) {
            crossAxisCount = 4;
          }

          return GridView.builder(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.md,
              AppSpacing.sm,
              AppSpacing.md,
              100,
            ),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: crossAxisCount,
              childAspectRatio: 0.75,
              crossAxisSpacing: AppSpacing.md,
              mainAxisSpacing: AppSpacing.md,
            ),
            itemCount: state.urns.length,
            itemBuilder: (context, index) {
              final urn = state.urns[index];
              return TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.0, end: 1.0),
                duration: Duration(milliseconds: 400 + (index * 100)),
                curve: Curves.easeOutCubic,
                builder: (context, value, child) {
                  return Transform.scale(
                    scale: value,
                    child: Opacity(
                      opacity: value,
                      child: child,
                    ),
                  );
                },
                child: UrnCard(
                  urn: urn,
                  onTap: () => _navigateToUrn(context, urn.slug),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
          ),
          const SizedBox(height: 16),
          Text(
            'Đang tải...',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(WidgetRef ref, String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.white.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  ref.read(exploreNotifierProvider.notifier).loadUrns(),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState(WidgetRef ref) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.inbox_outlined,
              size: 64,
              color: Colors.white.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            Text(
              'Không có dữ liệu',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Vui lòng thử lại sau.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withOpacity(0.5),
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  ref.read(exploreNotifierProvider.notifier).loadUrns(),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFD4A84B),
                foregroundColor: const Color(0xFF1A1A2E),
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToUrn(BuildContext context, String urnSlug) {
    context.push('/urns/$urnSlug');
  }
}
