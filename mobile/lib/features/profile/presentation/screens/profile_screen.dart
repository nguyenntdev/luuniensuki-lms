import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../../auth/domain/entities/user.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../collection/presentation/providers/collection_provider.dart';
import '../../../gems/presentation/widgets/gems_display.dart';
import '../../../streak/presentation/widgets/streak_display.dart';
import '../../../streak/presentation/widgets/buy_streak_freeze_button.dart';
import 'personal_info_screen.dart';

/// Profile screen showing user info, stats, and settings
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
      ),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: const Interval(0.2, 1.0, curve: Curves.easeOutCubic),
      ),
    );

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState.user;

    return AnimatedGradientBackground(
      child: SafeArea(
        child: user == null
            ? _buildNotLoggedIn(context)
            : _buildProfile(context, ref, user),
      ),
    );
  }

  Widget _buildNotLoggedIn(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated icon
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    AppColors.primary.withOpacity(0.3),
                    AppColors.primaryDark.withOpacity(0.1),
                  ],
                ),
                border: Border.all(
                  color: Colors.white.withOpacity(0.2),
                  width: 2,
                ),
              ),
              child: Icon(
                Icons.person_outline,
                size: 60,
                color: Colors.white.withOpacity(0.5),
              ),
            ),
            AppSpacing.verticalSpaceLG,
            Text(
              'Chưa đăng nhập',
              style: TextStyle(
                color: Colors.white.withOpacity(0.9),
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            AppSpacing.verticalSpaceSM,
            Text(
              'Đăng nhập để theo dõi tiến độ của bạn',
              style: TextStyle(
                color: Colors.white.withOpacity(0.6),
                fontSize: 14,
              ),
            ),
            AppSpacing.verticalSpaceXL,
            ElevatedButton(
              onPressed: () => context.go('/login'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
                ),
                elevation: 8,
                shadowColor: AppColors.primary.withOpacity(0.5),
              ),
              child: const Text(
                'Đăng nhập',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfile(BuildContext context, WidgetRef ref, User user) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: CustomScrollView(
          slivers: [
            // Beautiful header with gradient background
            _buildProfileHeader(user),

            // Content with padding
            SliverPadding(
              padding: const EdgeInsets.all(AppSpacing.md),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  // XP Progress Card
                  _buildXpCard(user),

                  AppSpacing.verticalSpaceMD,

                  // Stats Grid
                  _buildStatsGrid(ref, user),

                  AppSpacing.verticalSpaceMD,

                  // Enhanced Streak Display
                  const StreakDisplay(),

                  AppSpacing.verticalSpaceMD,

                  // Buy Streak Freeze Button
                  const BuyStreakFreezeButton(),

                  AppSpacing.verticalSpaceLG,

                  // Section header
                  Text(
                    'Cài đặt & Tài khoản',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  AppSpacing.verticalSpaceMD,

                  // Settings Cards
                  _buildSettingsCards(context, ref),

                  const SizedBox(height: 120), // Bottom padding for nav bar
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileHeader(User user) {
    return SliverToBoxAdapter(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppColors.primary.withOpacity(0.2),
              AppColors.primaryDark.withOpacity(0.1),
              Colors.transparent,
            ],
            stops: const [0.0, 0.5, 1.0],
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.md,
            AppSpacing.lg,
            AppSpacing.md,
            AppSpacing.xl,
          ),
          child: Column(
            children: [
              // Hero Avatar with glow effect
              Hero(
                tag: 'user_avatar_${user.id}',
                child: Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: AppColors.primaryGradient,
                    border: Border.all(
                      color: Colors.white.withOpacity(0.4),
                      width: 4,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.4),
                        blurRadius: 30,
                        spreadRadius: 5,
                      ),
                      BoxShadow(
                        color: AppColors.primaryDark.withOpacity(0.3),
                        blurRadius: 15,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: user.avatarUrl != null && user.avatarUrl!.isNotEmpty
                      ? ClipOval(
                          child: Image.network(
                            user.avatarUrl!,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) =>
                                _buildAvatarPlaceholder(user),
                          ),
                        )
                      : _buildAvatarPlaceholder(user),
                ),
              ),

              AppSpacing.verticalSpaceLG,

              // Display Name with shadow
              Text(
                user.displayName,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  shadows: [
                    Shadow(
                      color: Colors.black26,
                      blurRadius: 8,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
              ),

              AppSpacing.verticalSpaceSM,

              // Email with icon
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.email_outlined,
                    size: 14,
                    color: Colors.white.withOpacity(0.5),
                  ),
                  const SizedBox(width: 6),
                  Flexible(
                    child: Text(
                      user.email,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.6),
                        fontSize: 14,
                      ),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ),
                ],
              ),

              AppSpacing.verticalSpaceMD,

              // Rank badge with enhanced styling
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.lg,
                  vertical: AppSpacing.sm,
                ),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      AppColors.primary.withOpacity(0.3),
                      AppColors.primaryDark.withOpacity(0.2),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusRound),
                  border: Border.all(
                    color: AppColors.primary.withOpacity(0.6),
                    width: 1.5,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.2),
                      blurRadius: 8,
                      spreadRadius: 1,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.military_tech,
                      color: AppColors.primary,
                      size: 18,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      user.rank.name,
                      style: const TextStyle(
                        color: AppColors.primary,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),

              AppSpacing.verticalSpaceMD,

              // Gems display with tap to go to shop
              GemsDisplay(
                showLabel: true,
                iconSize: 24,
                textStyle: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                onTap: () => context.push('/gems-shop'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAvatarPlaceholder(User user) {
    final initial = user.displayName.isNotEmpty
        ? user.displayName[0].toUpperCase()
        : user.email[0].toUpperCase();
    return Center(
      child: Text(
        initial,
        style: TextStyle(
          color: AppColors.onPrimary,
          fontSize: 48,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildXpCard(User user) {
    final totalXp = user.totalXp;
    final xpToNext = user.xpToNextRank;
    final currentRank = user.rank.name;
    final nextRank = user.nextRank?.name;
    final xpProgress = xpToNext > 0 ? (totalXp % xpToNext) : totalXp.toDouble();
    final progress = xpToNext > 0 ? xpProgress / xpToNext : 1.0;

    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.lg),
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          AppColors.glassWhite,
          AppColors.primary.withOpacity(0.05),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.sm),
                        decoration: BoxDecoration(
                          gradient: AppColors.primaryGradient,
                          borderRadius:
                              BorderRadius.circular(AppSpacing.radiusSM),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primary.withOpacity(0.3),
                              blurRadius: 8,
                              spreadRadius: 1,
                            ),
                          ],
                        ),
                        child: Icon(
                          Icons.star,
                          color: AppColors.onPrimary,
                          size: 20,
                        ),
                      ),
                      AppSpacing.horizontalSpaceSM,
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Kinh nghiệm',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.7),
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            '$totalXp XP',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md,
                      vertical: AppSpacing.xs,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.2),
                      borderRadius:
                          BorderRadius.circular(AppSpacing.radiusMD),
                      border: Border.all(
                        color: AppColors.primary.withOpacity(0.4),
                      ),
                    ),
                    child: Text(
                      currentRank,
                      style: const TextStyle(
                        color: AppColors.primary,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (nextRank != null) ...[
                    AppSpacing.verticalSpaceXS,
                    Row(
                      children: [
                        Icon(
                          Icons.arrow_forward,
                          size: 12,
                          color: Colors.white.withOpacity(0.4),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          nextRank,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.5),
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ],
          ),

          AppSpacing.verticalSpaceLG,

          // XP Progress bar with enhanced styling
          Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    nextRank != null ? 'Còn $xpToNext XP để lên cấp' : 'Cấp tối đa',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.7),
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.sm,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.2),
                      borderRadius:
                          BorderRadius.circular(AppSpacing.radiusSM),
                    ),
                    child: Text(
                      '${(progress * 100).toInt()}%',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              AppSpacing.verticalSpaceSM,
              Stack(
                children: [
                  // Background
                  Container(
                    height: 10,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius:
                          BorderRadius.circular(AppSpacing.radiusSM),
                      border: Border.all(
                        color: Colors.white.withOpacity(0.1),
                      ),
                    ),
                  ),
                  // Progress with gradient
                  FractionallySizedBox(
                    alignment: Alignment.centerLeft,
                    widthFactor: progress.clamp(0.0, 1.0),
                    child: Container(
                      height: 10,
                      decoration: BoxDecoration(
                        gradient: AppColors.xpGradient,
                        borderRadius:
                            BorderRadius.circular(AppSpacing.radiusSM),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.xpGold.withOpacity(0.5),
                            blurRadius: 8,
                            spreadRadius: 1,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid(WidgetRef ref, User user) {
    final collectionState = ref.watch(collectionNotifierProvider);
    final discoveredCount = collectionState.collection?.stats.discovered ?? 0;
    final lessonsCompleted = user.totalXp ~/ 75; // Approximate

    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            icon: Icons.visibility,
            label: 'Đã khám phá',
            value: '$discoveredCount',
            color: AppColors.info,
            gradientColors: [
              AppColors.info.withOpacity(0.3),
              AppColors.info.withOpacity(0.1),
            ],
          ),
        ),
        AppSpacing.horizontalSpaceSM,
        Expanded(
          child: _buildStatCard(
            icon: Icons.school,
            label: 'Đã học',
            value: '$lessonsCompleted',
            color: AppColors.success,
            gradientColors: [
              AppColors.success.withOpacity(0.3),
              AppColors.success.withOpacity(0.1),
            ],
          ),
        ),
        AppSpacing.horizontalSpaceSM,
        Expanded(
          child: _buildStatCard(
            icon: Icons.emoji_events,
            label: 'Huy hiệu',
            value: '0',
            color: AppColors.badgePurple,
            gradientColors: [
              AppColors.badgePurple.withOpacity(0.3),
              AppColors.badgePurple.withOpacity(0.1),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
    required List<Color> gradientColors,
  }) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.lg,
        horizontal: AppSpacing.sm,
      ),
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: gradientColors,
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.sm),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          AppSpacing.verticalSpaceSM,
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          AppSpacing.verticalSpaceXS,
          Text(
            label,
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildStreakCard(User user) {
    final currentStreak = user.currentStreak;
    final longestStreak = user.longestStreak;
    final streakFreezes = user.streakFreezes;
    final hasStreak = currentStreak > 0;

    return GlassContainer(
      padding: const EdgeInsets.all(AppSpacing.lg),
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: hasStreak
            ? [
                AppColors.streakOrange.withOpacity(0.15),
                AppColors.streakOrange.withOpacity(0.05),
              ]
            : [
                AppColors.glassWhite,
                Colors.transparent,
              ],
      ),
      child: Row(
        children: [
          // Streak fire icon with animation-ready glow
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              gradient: hasStreak
                  ? LinearGradient(
                      colors: [
                        AppColors.streakOrange.withOpacity(0.3),
                        AppColors.streakOrange.withOpacity(0.1),
                      ],
                    )
                  : null,
              color: hasStreak ? null : Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
              boxShadow: hasStreak
                  ? [
                      BoxShadow(
                        color: AppColors.streakOrange.withOpacity(0.3),
                        blurRadius: 16,
                        spreadRadius: 2,
                      ),
                    ]
                  : null,
            ),
            child: Icon(
              Icons.local_fire_department,
              color: hasStreak
                  ? AppColors.streakOrange
                  : Colors.white.withOpacity(0.3),
              size: 36,
            ),
          ),

          AppSpacing.horizontalSpaceMD,

          // Streak info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      '$currentStreak',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        height: 1,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'ngày',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (hasStreak) ...[
                      const SizedBox(width: 6),
                      const Text('🔥', style: TextStyle(fontSize: 20)),
                    ],
                  ],
                ),
                AppSpacing.verticalSpaceXS,
                Text(
                  'Chuỗi học tập hiện tại',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),

          // Stats column with enhanced design
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                  border: Border.all(
                    color: AppColors.primary.withOpacity(0.3),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.emoji_events,
                      color: AppColors.primary,
                      size: 14,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '$longestStreak',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              AppSpacing.verticalSpaceXS,
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                decoration: BoxDecoration(
                  color: AppColors.info.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                  border: Border.all(
                    color: AppColors.info.withOpacity(0.3),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.ac_unit,
                      color: AppColors.info,
                      size: 14,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '$streakFreezes',
                      style: TextStyle(
                        color: AppColors.info,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsCards(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        // Account settings card
        _buildMenuCard(
          icon: Icons.person_outline,
          title: 'Thông tin cá nhân',
          subtitle: 'Chỉnh sửa hồ sơ và ảnh đại diện',
          color: AppColors.info,
          onTap: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (context) => const PersonalInfoScreen(),
              ),
            );
          },
        ),

        AppSpacing.verticalSpaceSM,

        // Friends card
        _buildMenuCard(
          icon: Icons.people_outline,
          title: 'Bạn bè',
          subtitle: 'Kết nối và thi đua với bạn bè',
          color: AppColors.primary,
          onTap: () => context.push('/friends'),
        ),

        AppSpacing.verticalSpaceSM,

        // Gems Shop card
        _buildMenuCard(
          icon: Icons.diamond_outlined,
          title: 'Cửa Hàng Gems',
          subtitle: 'Mua các vật phẩm hữu ích',
          color: AppColors.gemYellow,
          onTap: () => context.push('/gems-shop'),
        ),

        AppSpacing.verticalSpaceSM,

        // Notifications card
        _buildMenuCard(
          icon: Icons.notifications_outlined,
          title: 'Thông báo',
          subtitle: 'Quản lý nhắc nhở và thông báo',
          color: AppColors.warning,
          onTap: () => context.push('/notifications'),
        ),

        AppSpacing.verticalSpaceSM,

        // Settings card
        _buildMenuCard(
          icon: Icons.settings_outlined,
          title: 'Cài đặt',
          subtitle: 'Tùy chỉnh ứng dụng',
          color: AppColors.textSecondary,
          onTap: () => context.push('/settings'),
        ),

        AppSpacing.verticalSpaceSM,

        // Help & Support card
        _buildMenuCard(
          icon: Icons.help_outline,
          title: 'Trợ giúp & Hỗ trợ',
          subtitle: 'Câu hỏi thường gặp và liên hệ',
          color: AppColors.success,
          onTap: () {
            context.push('/help');
          },
        ),

        AppSpacing.verticalSpaceLG,

        // Logout button
        _buildLogoutButton(context, ref),
      ],
    );
  }

  Widget _buildMenuCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GlassCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      onTap: onTap,
      child: Row(
        children: [
          // Icon with gradient background
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  color.withOpacity(0.3),
                  color.withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
              border: Border.all(
                color: color.withOpacity(0.3),
              ),
            ),
            child: Icon(
              icon,
              color: color,
              size: 24,
            ),
          ),

          AppSpacing.horizontalSpaceMD,

          // Text content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                AppSpacing.verticalSpaceXS,
                Text(
                  subtitle,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.6),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),

          // Arrow icon
          Icon(
            Icons.chevron_right,
            color: Colors.white.withOpacity(0.3),
            size: 24,
          ),
        ],
      ),
    );
  }

  Widget _buildLogoutButton(BuildContext context, WidgetRef ref) {
    return GestureDetector(
      onTap: () => _showLogoutDialog(context, ref),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.error.withOpacity(0.15),
              AppColors.error.withOpacity(0.05),
            ],
          ),
          borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
          border: Border.all(
            color: AppColors.error.withOpacity(0.3),
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.logout,
              color: AppColors.error,
              size: 20,
            ),
            AppSpacing.horizontalSpaceSM,
            Text(
              'Đăng xuất',
              style: TextStyle(
                color: AppColors.error,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
          side: BorderSide(color: Colors.white.withOpacity(0.15)),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.error.withOpacity(0.3),
                    AppColors.error.withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
              ),
              child: Icon(
                Icons.logout,
                color: AppColors.error,
                size: 20,
              ),
            ),
            AppSpacing.horizontalSpaceSM,
            const Text(
              'Đăng xuất',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          'Bạn có chắc chắn muốn đăng xuất khỏi tài khoản?',
          style: TextStyle(
            color: Colors.white.withOpacity(0.8),
            fontSize: 15,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: AppSpacing.sm,
              ),
            ),
            child: Text(
              'Hủy',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ref.read(authNotifierProvider.notifier).logout();
              context.go('/login');
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: AppSpacing.sm,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
              ),
            ),
            child: const Text(
              'Đăng xuất',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
