import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../theme/glass_theme.dart';

/// Glass bottom navigation bar with glassmorphism effect
/// Enhanced with morphing icons, glow effects, and floating indicator
class GlassBottomNav extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;
  final List<GlassBottomNavItem> items;

  const GlassBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;
    return Container(
      height: AppSpacing.navBarHeight,
      margin: EdgeInsets.fromLTRB(
        AppSpacing.md,
        0,
        AppSpacing.md,
        AppSpacing.navBarMargin + bottomInset,
      ),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.surface.withOpacity(0.4),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: Colors.white.withOpacity(0.2),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 18,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Stack(
              children: [
                // Floating indicator dot
                _FloatingIndicator(
                  currentIndex: currentIndex,
                  itemCount: items.length,
                ),
                // Navigation items
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: List.generate(
                    items.length,
                    (index) => _buildNavItem(
                      index,
                      items[index],
                      index == currentIndex,
                      () {
                        HapticFeedback.lightImpact();
                        onTap(index);
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
    int index,
    GlassBottomNavItem item,
    bool isSelected,
    VoidCallback onTap,
  ) {
    return Expanded(
      child: _NavItemButton(
        index: index,
        item: item,
        isSelected: isSelected,
        onTap: onTap,
      ),
    );
  }
}

/// Floating indicator dot that follows the selected tab
class _FloatingIndicator extends StatelessWidget {
  final int currentIndex;
  final int itemCount;

  const _FloatingIndicator({
    required this.currentIndex,
    required this.itemCount,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedPositioned(
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeOutCubic,
      left: _calculatePosition(context),
      bottom: 4,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: 1),
        duration: const Duration(milliseconds: 400),
        curve: Curves.elasticOut,
        builder: (context, value, child) {
          return Transform.scale(
            scale: value,
            child: Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.6),
                    blurRadius: 8,
                    spreadRadius: 2,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  double _calculatePosition(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final navWidth = screenWidth - (AppSpacing.md * 2);
    final itemWidth = navWidth / itemCount;
    final centerOffset = (itemWidth - 6) / 2;
    return (itemWidth * currentIndex) + centerOffset;
  }
}

/// Individual navigation item with enhanced animations
class _NavItemButton extends StatefulWidget {
  final int index;
  final GlassBottomNavItem item;
  final bool isSelected;
  final VoidCallback onTap;

  const _NavItemButton({
    required this.index,
    required this.item,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_NavItemButton> createState() => _NavItemButtonState();
}

class _NavItemButtonState extends State<_NavItemButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _pressController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _pressController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.95).animate(
      CurvedAnimation(parent: _pressController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pressController.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    _pressController.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    _pressController.reverse();
  }

  void _handleTapCancel() {
    _pressController.reverse();
  }

  /// Build icon with morphing animation and glow effect
  Widget _buildMorphingIcon() {
    final accent = widget.item.primaryColor ?? AppColors.primary;
    final iconSize = widget.item.isPrimary ? 30.0 : 24.0;

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: widget.isSelected ? 1.0 : 0.0),
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(0, -4 * value),
          child: Transform.scale(
            scale: 1.0 + (0.15 * value),
            child: Container(
              decoration: BoxDecoration(
                boxShadow: [
                  BoxShadow(
                    color: accent.withOpacity(0.5 * value),
                    blurRadius: 16 * value,
                    spreadRadius: 3 * value,
                  ),
                ],
              ),
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                transitionBuilder: (child, animation) {
                  return ScaleTransition(
                    scale: animation,
                    child: FadeTransition(
                      opacity: animation,
                      child: child,
                    ),
                  );
                },
                child: Icon(
                  widget.isSelected ? widget.item.activeIcon : widget.item.icon,
                  key: ValueKey(widget.isSelected),
                  color: widget.isSelected ? accent : Colors.white60,
                  size: iconSize,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  /// Build primary (center) icon with enhanced container
  Widget _buildPrimaryIcon() {
    final accent = widget.item.primaryColor ?? AppColors.primary;

    return Transform.translate(
      offset: const Offset(0, -6),
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: widget.isSelected ? 1.0 : 0.0),
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOutCubic,
        builder: (context, value, child) {
          return Container(
            padding: EdgeInsets.all(8 + (value * 1)),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  accent.withOpacity(0.25 + (value * 0.1)),
                  accent.withOpacity(0.12 + (value * 0.08)),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: accent.withOpacity(0.6 + (value * 0.3)),
                width: 1.2 + (value * 0.4),
              ),
              boxShadow: [
                BoxShadow(
                  color: accent.withOpacity(0.25 + (value * 0.25)),
                  blurRadius: 12 + (value * 8),
                  spreadRadius: 1 + (value * 2),
                ),
              ],
            ),
            child: _buildMorphingIcon(),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: widget.onTap,
        onTapDown: _handleTapDown,
        onTapUp: _handleTapUp,
        onTapCancel: _handleTapCancel,
        borderRadius: BorderRadius.circular(16),
        splashColor: (widget.item.primaryColor ?? AppColors.primary).withOpacity(0.2),
        highlightColor: (widget.item.primaryColor ?? AppColors.primary).withOpacity(0.1),
        child: AnimatedBuilder(
          animation: _scaleAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _scaleAnimation.value,
              child: child,
            );
          },
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Icon with badge
                Stack(
                  clipBehavior: Clip.none,
                  children: [
                    widget.item.isPrimary
                        ? _buildPrimaryIcon()
                        : _buildMorphingIcon(),
                    if (widget.item.badge != null)
                      Positioned(
                        right: -8,
                        top: -4,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: AppColors.accent,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppColors.textPrimary,
                              width: 1.5,
                            ),
                          ),
                          constraints: const BoxConstraints(
                            minWidth: 18,
                            minHeight: 18,
                          ),
                          child: Center(
                            child: Text(
                              widget.item.badge!,
                              style: const TextStyle(
                                color: AppColors.textPrimary,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                      ),
                    if (widget.item.badgeCount != null && widget.item.badgeCount! > 0)
                      Positioned(
                        right: -6,
                        top: -4,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.red,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: Colors.red.withOpacity(0.5),
                                blurRadius: 4,
                                spreadRadius: 1,
                              ),
                            ],
                          ),
                          constraints: const BoxConstraints(
                            minWidth: 16,
                            minHeight: 16,
                          ),
                          child: Center(
                            child: Text(
                              widget.item.badgeCount! > 9
                                  ? '9+'
                                  : '${widget.item.badgeCount}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                // Label with enhanced animation
                AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeOutCubic,
                  style: TextStyle(
                    color: widget.isSelected
                        ? (widget.item.primaryColor ?? AppColors.primary)
                        : Colors.white60,
                    fontSize: 11,
                    fontWeight: widget.isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                  child: Text(
                    widget.item.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Navigation item for glass bottom nav
class GlassBottomNavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  final String? badge;
  final int? badgeCount;
  final bool isPrimary;
  final Color? primaryColor;

  const GlassBottomNavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    this.badge,
    this.badgeCount,
    this.isPrimary = false,
    this.primaryColor,
  });
}
