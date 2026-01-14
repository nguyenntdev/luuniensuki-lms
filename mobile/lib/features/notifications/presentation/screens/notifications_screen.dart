import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../providers/notifications_provider.dart';
import '../widgets/notification_item_widget.dart';
import '../widgets/notification_preferences_widget.dart';

/// Notifications screen with beautiful animations and glass morphism
class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() =>
      _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  bool _showPreferences = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOut,
      ),
    );

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _onRefresh() async {
    await ref.read(notificationsNotifierProvider.notifier).refresh();
  }

  void _markAllAsRead() {
    ref.read(notificationsNotifierProvider.notifier).markAllAsRead();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Đã đánh dấu tất cả là đã đọc'),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
        ),
      ),
    );
  }

  void _showClearAllDialog() {
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
                Icons.delete_outline,
                color: AppColors.error,
                size: 20,
              ),
            ),
            AppSpacing.horizontalSpaceSM,
            const Text(
              'Xóa tất cả',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          'Bạn có chắc chắn muốn xóa tất cả thông báo?',
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
              ref.read(notificationsNotifierProvider.notifier).clearAll();
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
              'Xóa tất cả',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final notificationsState = ref.watch(notificationsNotifierProvider);
    final hasNotifications = notificationsState.notifications.isNotEmpty;
    final unreadCount = notificationsState.unreadCount;

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: _buildAppBar(unreadCount, hasNotifications),
        body: FadeTransition(
          opacity: _fadeAnimation,
          child: _showPreferences
              ? _buildPreferences()
              : hasNotifications
                  ? _buildNotificationsList(notificationsState)
                  : _buildEmptyState(),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(int unreadCount, bool hasNotifications) {
    return AppBar(
      backgroundColor: Colors.transparent,
      elevation: 0,
      leading: IconButton(
        icon: Icon(
          Icons.arrow_back,
          color: Colors.white.withOpacity(0.9),
        ),
        onPressed: () {
          if (_showPreferences) {
            setState(() => _showPreferences = false);
          } else {
            context.pop();
          }
        },
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _showPreferences ? 'Cài đặt thông báo' : 'Thông báo',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (!_showPreferences && unreadCount > 0)
            Text(
              '$unreadCount chưa đọc',
              style: TextStyle(
                color: AppColors.primary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
        ],
      ),
      actions: !_showPreferences && hasNotifications
          ? [
              // Settings button
              IconButton(
                icon: Icon(
                  Icons.settings,
                  color: Colors.white.withOpacity(0.7),
                ),
                onPressed: () {
                  setState(() => _showPreferences = true);
                },
                tooltip: 'Cài đặt',
              ),

              // Mark all as read
              if (unreadCount > 0)
                IconButton(
                  icon: Icon(
                    Icons.done_all,
                    color: Colors.white.withOpacity(0.7),
                  ),
                  onPressed: _markAllAsRead,
                  tooltip: 'Đánh dấu tất cả đã đọc',
                ),

              // Clear all
              PopupMenuButton<String>(
                icon: Icon(
                  Icons.more_vert,
                  color: Colors.white.withOpacity(0.7),
                ),
                color: AppColors.surface,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
                  side: BorderSide(color: Colors.white.withOpacity(0.15)),
                ),
                onSelected: (value) {
                  if (value == 'clear') {
                    _showClearAllDialog();
                  }
                },
                itemBuilder: (context) => [
                  PopupMenuItem(
                    value: 'clear',
                    child: Row(
                      children: [
                        Icon(
                          Icons.delete_outline,
                          color: AppColors.error,
                          size: 20,
                        ),
                        AppSpacing.horizontalSpaceSM,
                        Text(
                          'Xóa tất cả',
                          style: TextStyle(
                            color: AppColors.error,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ]
          : null,
    );
  }

  Widget _buildPreferences() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: const NotificationPreferencesWidget(),
    );
  }

  Widget _buildNotificationsList(NotificationsState state) {
    return RefreshIndicator(
      onRefresh: _onRefresh,
      color: AppColors.primary,
      backgroundColor: AppColors.surface,
      child: ListView.builder(
        padding: const EdgeInsets.all(AppSpacing.md),
        itemCount: state.notifications.length,
        itemBuilder: (context, index) {
          final notification = state.notifications[index];
          return NotificationItemWidget(
            notification: notification,
            index: index,
            onMarkAsRead: () {
              ref
                  .read(notificationsNotifierProvider.notifier)
                  .markAsRead(notification.id);
            },
            onDelete: () {
              ref
                  .read(notificationsNotifierProvider.notifier)
                  .deleteNotification(notification.id);

              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: const Text('Đã xóa thông báo'),
                  backgroundColor: AppColors.surface,
                  behavior: SnackBarBehavior.floating,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppSpacing.radiusSM),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
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
                  AppColors.primary.withOpacity(0.2),
                  AppColors.primaryDark.withOpacity(0.1),
                ],
              ),
              border: Border.all(
                color: Colors.white.withOpacity(0.2),
                width: 2,
              ),
            ),
            child: Icon(
              Icons.notifications_none,
              size: 60,
              color: Colors.white.withOpacity(0.5),
            ),
          ),

          AppSpacing.verticalSpaceLG,

          Text(
            'Chưa có thông báo',
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),

          AppSpacing.verticalSpaceSM,

          Text(
            'Bạn sẽ nhận được thông báo về\ncác hoạt động và thành tích của mình',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white.withOpacity(0.6),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

