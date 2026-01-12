import 'package:flutter/material.dart';
import '../shared/widgets/glass/glass_bottom_nav.dart';
import '../shared/theme/glass_theme.dart';

/// Demo page showcasing the modernized glass bottom navigation
class GlassBottomNavDemo extends StatefulWidget {
  const GlassBottomNavDemo({super.key});

  @override
  State<GlassBottomNavDemo> createState() => _GlassBottomNavDemoState();
}

class _GlassBottomNavDemoState extends State<GlassBottomNavDemo> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const _DemoPage(
      title: 'Home',
      icon: Icons.home,
      color: Colors.blue,
    ),
    const _DemoPage(
      title: 'Search',
      icon: Icons.search,
      color: Colors.purple,
    ),
    const _DemoPage(
      title: 'Messages',
      icon: Icons.message,
      color: Colors.green,
    ),
    const _DemoPage(
      title: 'Profile',
      icon: Icons.person,
      color: Colors.orange,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GlassTheme.backgroundDark,
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  GlassTheme.backgroundDark,
                  GlassTheme.backgroundDark.withBlue(40),
                ],
              ),
            ),
          ),
          // Page content
          IndexedStack(
            index: _currentIndex,
            children: _pages,
          ),
        ],
      ),
      bottomNavigationBar: GlassBottomNav(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          GlassBottomNavItem(
            icon: Icons.home_outlined,
            activeIcon: Icons.home,
            label: 'Home',
          ),
          GlassBottomNavItem(
            icon: Icons.search_outlined,
            activeIcon: Icons.search,
            label: 'Search',
          ),
          GlassBottomNavItem(
            icon: Icons.message_outlined,
            activeIcon: Icons.message,
            label: 'Messages',
            badge: '3',
          ),
          GlassBottomNavItem(
            icon: Icons.person_outline,
            activeIcon: Icons.person,
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

class _DemoPage extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;

  const _DemoPage({
    required this.title,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            size: 80,
            color: color,
          ),
          const SizedBox(height: 24),
          Text(
            title,
            style: const TextStyle(
              color: GlassTheme.textPrimary,
              fontSize: 32,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 48),
            child: Text(
              'Modernized bottom navigation with:\n'
              '• Reduced height (64px)\n'
              '• True glassmorphism with backdrop blur\n'
              '• Floating pill indicator animation\n'
              '• InkWell ripple effects\n'
              '• Haptic feedback\n'
              '• Enhanced micro-interactions',
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: GlassTheme.textSecondary,
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

