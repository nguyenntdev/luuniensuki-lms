import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/glass_container.dart';
import '../../domain/entities/notification_item.dart';

/// A single notification item widget with glass morphism styling
class NotificationItemWidget extends StatefulWidget {
  final NotificationItem notification;
  final VoidCallback onMarkAsRead;
  final VoidCallback onDelete;
  final int index;

  const NotificationItemWidget({
    super.key,
    required this.notification,
    required this.onMarkAsRead,
    required this.onDelete,
    required this.index,
  });

  @override
  State<NotificationItemWidget> createState() =>
      _NotificationItemWidgetState();
}

class _NotificationItemWidgetState extends State<NotificationItemWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    // Stagger animation based on index
    final delay = widget.index * 0.1;

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Interval(delay, 0.6 + delay, curve: Curves.easeOut),
      ),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0.3, 0),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Interval(delay, 0.8 + delay, curve: Curves.easeOutCubic),
      ),
    );

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTap() {
    // Mark as read
    if (!widget.notification.isRead) {
      widget.onMarkAsRead();
    }

    // Navigate if action URL exists
    if (widget.notification.actionUrl != null) {
      context.push(widget.notification.actionUrl!);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.md),
          child: Dismissible(
            key: Key(widget.notification.id),
            direction: DismissDirection.endToStart,
            background: Container(
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.only(right: AppSpacing.lg),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.transparent,
                    AppColors.error.withOpacity(0.3),
                  ],
                ),
                borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
              ),
              child: Icon(
                Icons.delete_outline,
                color: AppColors.error,
                size: 28,
              ),
            ),
            onDismissed: (_) => widget.onDelete(),
            child: _buildNotificationCard(),
          ),
        ),
      ),
    );
  }

  Widget _buildNotificationCard() {
    final notification = widget.notification;
    final isUnread = !notification.isRead;

    return GlassCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      onTap: _handleTap,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon with gradient background
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  notification.color.withOpacity(0.3),
                  notification.color.withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
              border: Border.all(
                color: notification.color.withOpacity(0.3),
              ),
              boxShadow: isUnread
                  ? [
                      BoxShadow(
                        color: notification.color.withOpacity(0.2),
                        blurRadius: 8,
                        spreadRadius: 1,
                      ),
                    ]
                  : null,
            ),
            child: Icon(
              notification.icon,
              color: notification.color,
              size: 24,
            ),
          ),

          AppSpacing.horizontalSpaceMD,

          // Content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    // Unread indicator
                    if (isUnread)
                      Container(
                        width: 8,
                        height: 8,
                        margin: const EdgeInsets.only(right: 6),
                        decoration: BoxDecoration(
                          color: notification.color,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: notification.color.withOpacity(0.4),
                              blurRadius: 4,
                              spreadRadius: 1,
                            ),
                          ],
                        ),
                      ),

                    // Title
                    Expanded(
                      child: Text(
                        notification.title,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight:
                              isUnread ? FontWeight.bold : FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),

                AppSpacing.verticalSpaceXS,

                // Message
                Text(
                  notification.message,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.7),
                    fontSize: 14,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),

                AppSpacing.verticalSpaceXS,

                // Timestamp
                Text(
                  notification.timeAgo,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

