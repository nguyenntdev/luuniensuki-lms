import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/shimmer/shimmer_skeleton.dart';
import '../../../../shared/widgets/icons/status_icon.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../streak/presentation/widgets/compact_streak_widget.dart';
import '../../domain/entities/urn.dart';
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
  ProviderSubscription<AuthState>? _authSubscription;

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

    // If already authenticated, load immediately
    if (authState.isAuthenticated) {
      _hasInitialized = true;
      ref.read(exploreNotifierProvider.notifier).loadUrns();
      return;
    }

    // If still loading auth or unauthenticated, set up listener with fireImmediately
    _authSubscription = ref.listenManual<AuthState>(
      authNotifierProvider,
      (previous, next) {
        if (!_hasInitialized && next.isAuthenticated) {
          _hasInitialized = true;
          ref.read(exploreNotifierProvider.notifier).loadUrns();
          _authSubscription?.close();
        }
      },
      fireImmediately: true, // CRITICAL: This ensures we catch the current state
    );
  }

  @override
  void dispose() {
    _authSubscription?.close();
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
          child: _buildBody(context, state, progress, authState),
        ),
      ),
    );
  }

  Widget _buildBody(
    BuildContext context,
    ExploreState state,
    ExploreProgress progress,
    AuthState authState,
  ) {
    return RefreshIndicator(
      onRefresh: () => ref.read(exploreNotifierProvider.notifier).refreshUrns(),
      color: AppColors.primary,
      backgroundColor: AppColors.surface,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverToBoxAdapter(
            child: _buildHeader(context, progress, authState, state),
          ),
          const SliverToBoxAdapter(
            child: SizedBox(height: AppSpacing.sm),
          ),
          if (state.isLoading && !state.hasData)
            _buildLoadingGridSliver(context)
          else if (state.hasError && !state.hasData)
            SliverFillRemaining(
              hasScrollBody: false,
              child: _buildErrorState(state.errorMessage!),
            )
          else if (!state.isLoading && !state.hasError && state.urns.isEmpty)
            SliverFillRemaining(
              hasScrollBody: false,
              child: _buildEmptyState(),
            )
          else
            _buildGridSliver(context, state),
        ],
      ),
    );
  }

  Widget _buildHeader(
    BuildContext context,
    ExploreProgress progress,
    AuthState authState,
    ExploreState state,
  ) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;
    final continueUrn = _findContinueUrn(state);

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.sm,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'Khám phá',
                style: AppTypography.textTheme.headlineSmall?.copyWith(
                  color: Colors.white,
                  fontSize: isCompact ? 20 : 24,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.3,
                ),
              ),
              const Spacer(),
              const CompactStreakWidget(),
              const SizedBox(width: AppSpacing.sm),
              _buildUserAvatar(authState),
            ],
          ),
          SizedBox(height: isCompact ? AppSpacing.xs : AppSpacing.sm),
          _buildStatsCard(progress),
          const SizedBox(height: AppSpacing.sm),
          _buildActionRow(context, continueUrn),
          if (continueUrn != null) ...[
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Tiếp tục: ${continueUrn.name}',
              style: AppTypography.textTheme.bodySmall?.copyWith(
                color: Colors.white.withOpacity(0.7),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildUserAvatar(AuthState authState) {
    if (!authState.isAuthenticated || authState.user == null) {
      return const SizedBox.shrink();
    }

    final user = authState.user!;
    final initial = user.displayName.isNotEmpty
        ? user.displayName[0].toUpperCase()
        : user.email[0].toUpperCase();
    final level = user.rank.level;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white.withOpacity(0.1),
            border: Border.all(
              color: Colors.white.withOpacity(0.3),
              width: 1.5,
            ),
          ),
          child: user.avatarUrl != null && user.avatarUrl!.isNotEmpty
              ? ClipOval(
                  child: Image.network(
                    user.avatarUrl!,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Center(
                      child: Text(
                        initial,
                        style: TextStyle(
                          color: AppColors.onPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                )
              : Center(
                  child: Text(
                    initial,
                    style: TextStyle(
                      color: AppColors.onPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
        ),
        Positioned(
          bottom: -4,
          right: -4,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.xpGold,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: Colors.white.withOpacity(0.9),
                width: 1,
              ),
            ),
            child: Text(
              '$level',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStatsCard(ExploreProgress progress) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.08),
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        border: Border.all(
          color: Colors.white.withOpacity(0.12),
          width: 1,
        ),
      ),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        spacing: AppSpacing.md,
        runSpacing: AppSpacing.xs,
        children: [
          _buildStatItem(
            status: MotifStatus.discovered,
            value: '${progress.discoveredMotifs}/${progress.totalMotifs}',
            label: 'Khám phá',
          ),
          _buildStatItem(
            status: MotifStatus.learned,
            value: '${progress.learnedMotifs}',
            label: 'Đã học',
          ),
          _buildStatItem(
            status: MotifStatus.mastered,
            value: '${progress.masteredMotifs}',
            label: 'Thành thạo',
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required MotifStatus status,
    required String value,
    required String label,
  }) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        StatusIcon(
          status: status,
          size: 16,
        ),
        const SizedBox(width: 6),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                color: Colors.white.withOpacity(0.6),
                fontSize: 11,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionRow(BuildContext context, Urn? continueUrn) {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: continueUrn == null
                ? null
                : () => _navigateToUrn(context, continueUrn.slug),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.onPrimary,
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            icon: const Icon(Icons.play_arrow),
            label: const Text('Tiếp tục'),
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: () => context.push('/practice'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              side: BorderSide(color: Colors.white.withOpacity(0.4)),
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            icon: const Icon(Icons.fitness_center),
            label: const Text('Luyện tập'),
          ),
        ),
      ],
    );
  }

  Urn? _findContinueUrn(ExploreState state) {
    if (state.urns.isEmpty) {
      return null;
    }
    return state.urns.firstWhere(
      (urn) => urn.hasProgress && !urn.isCompleted,
      orElse: () => state.urns.first,
    );
  }

  SliverPadding _buildGridSliver(BuildContext context, ExploreState state) {
    final screenWidth = MediaQuery.of(context).size.width;
    int crossAxisCount = 2;
    if (screenWidth > 600) {
      crossAxisCount = 3;
    }
    if (screenWidth > 900) {
      crossAxisCount = 4;
    }

    return SliverPadding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.lg,
      ),
      sliver: SliverGrid(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: crossAxisCount,
          childAspectRatio: 0.72,
          crossAxisSpacing: AppSpacing.md,
          mainAxisSpacing: AppSpacing.md,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            final urn = state.urns[index];
            return TweenAnimationBuilder<double>(
              tween: Tween(begin: 0.0, end: 1.0),
              duration: Duration(milliseconds: 350 + (index * 80)),
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
          childCount: state.urns.length,
        ),
      ),
    );
  }

  SliverPadding _buildLoadingGridSliver(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    int crossAxisCount = 2;
    if (screenWidth > 600) {
      crossAxisCount = 3;
    }
    if (screenWidth > 900) {
      crossAxisCount = 4;
    }

    return SliverPadding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.lg,
      ),
      sliver: SliverGrid(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: crossAxisCount,
          childAspectRatio: 0.72,
          crossAxisSpacing: AppSpacing.md,
          mainAxisSpacing: AppSpacing.md,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            return const ShimmerUrnCard();
          },
          childCount: 9,
        ),
      ),
    );
  }

  Widget _buildErrorState(String message) {
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

  Widget _buildEmptyState() {
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
