import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/theme/app_colors.dart';
import '../../theme/glass_theme.dart';
import 'glass_nav_metrics.dart';

/// Glass bottom navigation bar with glassmorphism effect
class GlassBottomNav extends StatefulWidget {
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
  State<GlassBottomNav> createState() => _GlassBottomNavState();
}

class _GlassBottomNavState extends State<GlassBottomNav> {
  final Map<int, GlobalKey> _itemKeys = {};
  final GlobalKey _stackKey = GlobalKey();
  double _indicatorLeft = 0;
  double _indicatorWidth = 0;

  @override
  void initState() {
    super.initState();
    for (int i = 0; i < widget.items.length; i++) {
      _itemKeys[i] = GlobalKey();
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updateIndicatorPosition();
    });
  }

  @override
  void didUpdateWidget(GlassBottomNav oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentIndex != widget.currentIndex) {
      _updateIndicatorPosition();
    }
  }

  void _updateIndicatorPosition() {
    final key = _itemKeys[widget.currentIndex];
    final stackContext = _stackKey.currentContext;

    if (key?.currentContext != null && stackContext != null) {
      final RenderBox itemBox =
          key!.currentContext!.findRenderObject() as RenderBox;
      final RenderBox stackBox = stackContext.findRenderObject() as RenderBox;

      // Get position relative to Stack, not screen
      final position =
          stackBox.globalToLocal(itemBox.localToGlobal(Offset.zero));
      final size = itemBox.size;

      setState(() {
        _indicatorWidth = size.width * 0.7; // 70% of item width for pill
        _indicatorLeft = position.dx + (size.width - _indicatorWidth) / 2;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: GlassNavMetrics.barHeight,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(26),
        boxShadow: GlassTheme.glassShadowStrong,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(26),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
          child: Container(
            decoration: BoxDecoration(
              color: GlassTheme.glassBackgroundStrong,
              borderRadius: BorderRadius.circular(26),
              border: Border.all(
                color: GlassTheme.glassBorder,
                width: GlassTheme.borderWidth,
              ),
            ),
            child: Stack(
              key: _stackKey,
              children: [
                Positioned.fill(
                  child: IgnorePointer(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.white.withOpacity(0.16),
                            Colors.white.withOpacity(0.06),
                            Colors.transparent,
                          ],
                          stops: const [0.0, 0.28, 0.72],
                        ),
                      ),
                    ),
                  ),
                ),
                // Floating pill indicator
                AnimatedPositioned(
                  duration: const Duration(milliseconds: 350),
                  curve: Curves.easeOutCubic,
                  left: _indicatorLeft,
                  top: 8,
                  bottom: 8,
                  width: _indicatorWidth,
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          GlassTheme.accentGold.withOpacity(0.3),
                          GlassTheme.accentGold.withOpacity(0.15),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: GlassTheme.accentGold.withOpacity(0.3),
                          blurRadius: 12,
                          spreadRadius: 0,
                        ),
                      ],
                    ),
                  ),
                ),
                // Navigation items
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: List.generate(
                    widget.items.length,
                    (index) => _buildNavItem(
                      widget.items[index],
                      index == widget.currentIndex,
                      () {
                        HapticFeedback.lightImpact();
                        widget.onTap(index);
                      },
                      index,
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
    GlassBottomNavItem item,
    bool isSelected,
    VoidCallback onTap,
    int index,
  ) {
    return Expanded(
      key: _itemKeys[index],
      child: _NavItemButton(
        item: item,
        isSelected: isSelected,
        onTap: onTap,
        prominent: item.prominent,
      ),
    );
  }
}

/// Individual navigation item with animations
class _NavItemButton extends StatefulWidget {
  final GlassBottomNavItem item;
  final bool isSelected;
  final VoidCallback onTap;
  final bool prominent;

  const _NavItemButton({
    required this.item,
    required this.isSelected,
    required this.onTap,
    required this.prominent,
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
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Icon with badge
                Stack(
                  clipBehavior: Clip.none,
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 350),
                      curve: Curves.elasticOut,
                      transform: Matrix4.identity()
                        ..translate(
                          0.0,
                          widget.prominent
                              ? (widget.isSelected ? -7.0 : -4.0)
                              : (widget.isSelected ? -2.0 : 0.0),
                        )
                        ..scale(widget.prominent
                            ? (widget.isSelected ? 1.08 : 1.04)
                            : (widget.isSelected ? 1.05 : 1.0)),
                      padding: widget.prominent
                          ? const EdgeInsets.all(8)
                          : EdgeInsets.zero,
                      decoration: widget.prominent
                          ? BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: LinearGradient(
                                colors: widget.isSelected
                                    ? [
                                        GlassTheme.accentGold.withOpacity(0.95),
                                        GlassTheme.accentGold.withOpacity(0.72),
                                      ]
                                    : [
                                        GlassTheme.accentGold.withOpacity(0.45),
                                        GlassTheme.accentGold.withOpacity(0.28),
                                      ],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              border: Border.all(
                                color: Colors.white.withOpacity(0.42),
                                width: 1.1,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: GlassTheme.accentGold.withOpacity(
                                    widget.isSelected ? 0.42 : 0.22,
                                  ),
                                  blurRadius: widget.isSelected ? 18 : 12,
                                  spreadRadius: widget.isSelected ? 1.2 : 0.3,
                                ),
                              ],
                            )
                          : null,
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 300),
                        transitionBuilder: (child, animation) {
                          return ScaleTransition(
                            scale: animation,
                            child: child,
                          );
                        },
                        child: Icon(
                          widget.isSelected
                              ? widget.item.activeIcon
                              : widget.item.icon,
                          key: ValueKey(widget.isSelected),
                          color: widget.prominent
                              ? AppColors.background
                              : (widget.isSelected
                                  ? GlassTheme.accentGold
                                  : GlassTheme.textSecondary),
                          size: widget.prominent ? 22 : 24,
                        ),
                      ),
                    ),
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
                        ? GlassTheme.accentGold
                        : GlassTheme.textSecondary,
                    fontSize: 11,
                    fontWeight:
                        widget.isSelected ? FontWeight.bold : FontWeight.normal,
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
  final bool prominent;

  const GlassBottomNavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    this.badge,
    this.prominent = false,
  });
}
