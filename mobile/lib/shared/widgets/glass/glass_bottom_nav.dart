import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../theme/glass_theme.dart';

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
      final RenderBox itemBox = key!.currentContext!.findRenderObject() as RenderBox;
      final RenderBox stackBox = stackContext.findRenderObject() as RenderBox;

      // Get position relative to Stack, not screen
      final position = stackBox.globalToLocal(itemBox.localToGlobal(Offset.zero));
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
      height: 64,
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        boxShadow: GlassTheme.glassShadowStrong,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            decoration: BoxDecoration(
              color: GlassTheme.glassBackgroundStrong,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: GlassTheme.glassBorder,
                width: GlassTheme.borderWidth,
              ),
            ),
            child: Stack(
              key: _stackKey,
              children: [
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
                          widget.isSelected ? -2.0 : 0.0,
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
                          widget.isSelected ? widget.item.activeIcon : widget.item.icon,
                          key: ValueKey(widget.isSelected),
                          color: widget.isSelected
                              ? GlassTheme.accentGold
                              : GlassTheme.textSecondary,
                          size: 24,
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

  const GlassBottomNavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
    this.badge,
  });
}
