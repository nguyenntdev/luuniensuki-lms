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
      fireImmediately: true,  // CRITICAL: This ensures we catch the current state
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
          child: Column(
            children: [
              // Header
              _buildHeader(context, progress, authState, state),

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
    BuildContext context,
    ExploreProgress progress,
    dynamic authState,
    ExploreState state,
  ) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;
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
          // Clean top bar: Title + Streak + Avatar
          Wrap(
            alignment: WrapAlignment.spaceBetween,
            crossAxisAlignment: WrapCrossAlignment.center,
            runSpacing: AppSpacing.xs,
            children: [
              Text(
                'Khám Phá',
                style: AppTypography.textTheme.headlineSmall?.copyWith(
                  color: Colors.white,
                  fontSize: isCompact ? 20 : 24,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.4,
                ),
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CompactStreakWidget(),
                  const SizedBox(width: AppSpacing.sm),
                  _buildUserAvatar(authState),
                ],
              ),
            ],
          ),

          SizedBox(height: isCompact ? AppSpacing.xs : AppSpacing.sm),

          // Compact progress stats row
          _buildCompactStats(progress),

          SizedBox(height: isCompact ? AppSpacing.xs : AppSpacing.sm),

          // Quick actions to improve flow
          _buildQuickActions(context, state),
        ],
      ),
    );
  }

  Widget _buildUserAvatar(dynamic authState) {
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
        // Avatar circle
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              colors: [
                AppColors.primary.withOpacity(0.5),
                AppColors.primaryDark.withOpacity(0.3),
              ],
            ),
            border: Border.all(
              color: Colors.white.withOpacity(0.4),
              width: 2,
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withOpacity(0.3),
                blurRadius: 8,
                spreadRadius: 1,
              ),
            ],
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
                          fontSize: 18,
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
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
        ),

        // Level badge
        Positioned(
          bottom: -4,
          right: -4,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.xpGold, AppColors.xpGoldDark],
              ),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: Colors.white,
                width: 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.xpGold.withOpacity(0.5),
                  blurRadius: 6,
                  spreadRadius: 1,
                ),
              ],
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

  Widget _buildCompactStats(ExploreProgress progress) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs + 2,
      ),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withOpacity(0.1),
            Colors.white.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
        border: Border.all(
          color: Colors.white.withOpacity(0.15),
          width: 1,
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final stats = [
            _buildCompactStat(
              status: MotifStatus.discovered,
              value: '${progress.discoveredMotifs}/${progress.totalMotifs}',
            ),
            _buildCompactStat(
              status: MotifStatus.learned,
              value: '${progress.learnedMotifs}',
            ),
            _buildCompactStat(
              status: MotifStatus.mastered,
              value: '${progress.masteredMotifs}',
            ),
          ];

          if (constraints.maxWidth < 320) {
            return Wrap(
              alignment: WrapAlignment.center,
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.xs,
              children: stats,
            );
          }

          return Row(
            children: [
              Expanded(child: Center(child: stats[0])),
              _buildCompactDivider(),
              Expanded(child: Center(child: stats[1])),
              _buildCompactDivider(),
              Expanded(child: Center(child: stats[2])),
            ],
          );
        },
      ),
    );
  }

  Widget _buildCompactStat({required MotifStatus status, required String value}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        StatusIcon(
          status: status,
          size: 16,
        ),
        const SizedBox(width: 6),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.2,
          ),
        ),
      ],
    );
  }

  Widget _buildQuickActions(BuildContext context, ExploreState state) {
    final continueUrn = _findContinueUrn(state);
    final screenWidth = MediaQuery.of(context).size.width;
    final isCompact = screenWidth < 360;

    return Wrap(
      spacing: AppSpacing.sm,
      runSpacing: AppSpacing.xs,
      children: [
        _buildActionPill(
          label: 'Tiếp tục',
          icon: Icons.play_arrow,
          isEnabled: continueUrn != null,
          onTap: continueUrn == null
              ? null
              : () => _navigateToUrn(context, continueUrn.slug),
        ),
        _buildActionPill(
          label: 'Luyện tập',
          icon: Icons.fitness_center,
          isEnabled: true,
          onTap: () => context.push('/practice'),
          minWidth: isCompact ? 0 : 120,
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

  Widget _buildActionPill({
    required String label,
    required IconData icon,
    required bool isEnabled,
    required VoidCallback? onTap,
    double? minWidth,
  }) {
    return Opacity(
      opacity: isEnabled ? 1 : 0.45,
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusRound),
        onTap: isEnabled ? onTap : null,
        child: Container(
          constraints: minWidth != null
              ? BoxConstraints(minWidth: minWidth)
              : const BoxConstraints(),
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.sm,
          ),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Colors.white.withOpacity(0.12),
                Colors.white.withOpacity(0.05),
              ],
            ),
            borderRadius: BorderRadius.circular(AppSpacing.radiusRound),
            border: Border.all(
              color: Colors.white.withOpacity(0.2),
              width: 1,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: Colors.white, size: 16),
              const SizedBox(width: AppSpacing.sm),
              Text(
                label,
                style: AppTypography.textTheme.labelLarge?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCompactDivider() {
    return Container(
      width: 1,
      height: 20,
      color: Colors.white.withOpacity(0.2),
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

          return CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md,
                  AppSpacing.sm,
                  AppSpacing.md,
                  100,
                ),
                sliver: SliverGrid(
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: crossAxisCount,
                    childAspectRatio: 0.7,
                    crossAxisSpacing: AppSpacing.md,
                    mainAxisSpacing: AppSpacing.md,
                  ),
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
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
                    childCount: state.urns.length,
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildLoadingState() {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Responsive grid based on width
        int crossAxisCount = 2;
        if (constraints.maxWidth > 600) {
          crossAxisCount = 3;
        }
        if (constraints.maxWidth > 900) {
          crossAxisCount = 4;
        }

        return CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.md,
                AppSpacing.sm,
                AppSpacing.md,
                100,
              ),
              sliver: SliverGrid(
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: crossAxisCount,
                  childAspectRatio: 0.7,
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
            ),
          ],
        );
      },
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
