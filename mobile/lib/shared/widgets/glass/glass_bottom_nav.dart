import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../theme/glass_theme.dart';

/// Glass bottom navigation bar with glassmorphism effect
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
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: AppColors.border.withOpacity(0.4),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(
          items.length,
          (index) => _buildNavItem(
            items[index],
            index == currentIndex,
            () {
              HapticFeedback.lightImpact();
              onTap(index);
            },
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
    GlassBottomNavItem item,
    bool isSelected,
    VoidCallback onTap,
  ) {
    return Expanded(
      child: _NavItemButton(
        item: item,
        isSelected: isSelected,
        onTap: onTap,
      ),
    );
  }
}

/// Individual navigation item with animations
class _NavItemButton extends StatefulWidget {
  final GlassBottomNavItem item;
  final bool isSelected;
  final VoidCallback onTap;

  const _NavItemButton({
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
  bool _isPressed = false;

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
    setState(() => _isPressed = true);
    _pressController.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    setState(() => _isPressed = false);
    _pressController.reverse();
  }

  void _handleTapCancel() {
    setState(() => _isPressed = false);
    _pressController.reverse();
  }

  Widget _buildIcon(GlassBottomNavItem item) {
    final accent = item.primaryColor ?? GlassTheme.accentGold;
    final iconSize = item.isPrimary ? 30.0 : 24.0;
    final iconWidget = AnimatedContainer(
      duration: const Duration(milliseconds: 350),
      curve: Curves.elasticOut,
      transform: Matrix4.identity()
        ..translate(
          0.0,
          widget.isSelected ? -3.0 : 0.0,
        )
        ..scale(widget.isSelected ? 1.05 : 1.0),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        transitionBuilder: (child, animation) {
          return ScaleTransition(
            scale: animation,
            child: child,
          );
        },
        child: Icon(
          widget.isSelected ? item.activeIcon : item.icon,
          key: ValueKey(widget.isSelected),
          color: widget.isSelected ? accent : GlassTheme.textSecondary,
          size: iconSize,
        ),
      ),
    );

    if (!item.isPrimary) {
      return iconWidget;
    }

    return Transform.translate(
      offset: const Offset(0, -6),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: EdgeInsets.all(widget.isSelected ? 9 : 8),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              accent.withOpacity(widget.isSelected ? 0.35 : 0.25),
              accent.withOpacity(widget.isSelected ? 0.2 : 0.12),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: accent.withOpacity(widget.isSelected ? 0.9 : 0.6),
            width: widget.isSelected ? 1.6 : 1.2,
          ),
          boxShadow: [
            BoxShadow(
              color: accent.withOpacity(widget.isSelected ? 0.45 : 0.25),
              blurRadius: widget.isSelected ? 18 : 12,
              spreadRadius: widget.isSelected ? 2 : 1,
            ),
          ],
        ),
        child: iconWidget,
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
        splashColor: GlassTheme.accentGold.withOpacity(0.2),
        highlightColor: GlassTheme.accentGold.withOpacity(0.1),
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
                    _buildIcon(widget.item),
                    if (widget.item.badge != null)
                      Positioned(
                        right: -8,
                        top: -4,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: GlassTheme.accentRed,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: GlassTheme.textPrimary,
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
                                color: GlassTheme.textPrimary,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                // Label
                AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeOutCubic,
                  style: TextStyle(
                    color: widget.isSelected
                        ? (widget.item.primaryColor ?? GlassTheme.accentGold)
                        : GlassTheme.textSecondary,
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
  final bool isPrimary;
  final Color? primaryColor;

  const GlassBottomNavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    this.badge,
    this.isPrimary = false,
    this.primaryColor,
  });
}
