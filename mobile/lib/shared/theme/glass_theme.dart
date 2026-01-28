import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

/// Glass theme constants for the Cửu Đỉnh Ký LMS mobile app.
/// Defines the glassmorphism design system with colors, effects, and spacing.
class GlassTheme {
  GlassTheme._(); // Private constructor to prevent instantiation

  // ============================================================================
  // GLASS EFFECT COLORS
  // ============================================================================

  /// Background color for glass containers (10% white)
  static const Color glassBackground = Color(0x1AFFFFFF);

  /// Stronger background for emphasized glass containers (15% white)
  static const Color glassBackgroundStrong = Color(0x26FFFFFF);

  /// Border color for glass containers (20% white)
  static const Color glassBorder = Color(0x33FFFFFF);

  /// Border color for focused/active glass containers (30% white)
  static const Color glassBorderActive = Color(0x4DFFFFFF);

  // ============================================================================
  // GRADIENT BACKGROUNDS
  // ============================================================================

  /// Primary gradient background colors (matching updated AppColors)
  static const List<Color> gradientBackground = [
    Color(0xFF0A0E14), // Deep midnight
    Color(0xFF0C1016), // Dark variant
    Color(0xFF0B0F15), // Mid variant
    Color(0xFF0A0E14), // Deep midnight (loop)
  ];

  /// Alternative gradient for variety
  static const List<Color> gradientBackgroundAlt = [
    Color(0xFF0B0F15), // Mid variant
    Color(0xFF0C1016), // Dark variant
    Color(0xFF0A0E14), // Deep midnight
  ];

  // ============================================================================
  // ACCENT COLORS
  // ============================================================================

  /// Gold accent color (updated to warmer, more luminous gold)
  static const Color accentGold = Color(0xFFE8B44C);

  /// Light gold accent color (champagne gold)
  static const Color accentGoldLight = Color(0xFFF5D078);

  /// Gradient for gold elements
  static const List<Color> goldGradient = [
    accentGold,
    accentGoldLight,
  ];

  /// Blue accent for discovery/info (softer blue)
  static const Color accentBlue = Color(0xFF60A5FA);

  /// Green accent for learned/success (soft teal-green)
  static const Color accentGreen = Color(0xFF34D399);

  /// Red accent for errors/warnings (warm coral)
  static const Color accentRed = Color(0xFFEF6B6B);

  /// Orange accent for streaks/fire
  static const Color accentOrange = Color(0xFFFF6B35);

  // ============================================================================
  // BLUR & EFFECT CONSTANTS
  // ============================================================================

  /// Standard blur sigma for glass effect
  static const double blurSigma = 10.0;

  /// Strong blur for emphasized elements
  static const double blurSigmaStrong = 15.0;

  /// Light blur for subtle elements
  static const double blurSigmaLight = 5.0;

  /// Standard border radius
  static const double borderRadius = 20.0;

  /// Small border radius for compact elements
  static const double borderRadiusSmall = 12.0;

  /// Large border radius for prominent elements
  static const double borderRadiusLarge = 24.0;

  /// Border width for glass containers
  static const double borderWidth = 1.0;

  /// Border width for focused/active containers
  static const double borderWidthActive = 1.5;

  // ============================================================================
  // SPACING & SIZING
  // ============================================================================

  /// Extra small spacing (4px)
  static const double spaceXS = 4.0;

  /// Small spacing (8px)
  static const double spaceS = 8.0;

  /// Medium spacing (12px)
  static const double spaceM = 12.0;

  /// Large spacing (16px)
  static const double spaceL = 16.0;

  /// Extra large spacing (20px)
  static const double spaceXL = 20.0;

  /// Extra extra large spacing (24px)
  static const double spaceXXL = 24.0;

  // ============================================================================
  // TEXT COLORS
  // ============================================================================

  /// Primary text color (white)
  static const Color textPrimary = Colors.white;

  /// Secondary text color (70% white)
  static const Color textSecondary = Color(0xB3FFFFFF);

  /// Tertiary text color (50% white)
  static const Color textTertiary = Color(0x80FFFFFF);

  /// Disabled text color (30% white)
  static const Color textDisabled = Color(0x4DFFFFFF);

  /// Text color for dark backgrounds
  static const Color textOnDark = Color(0xFF1A1A2E);

  // ============================================================================
  // SHADOWS
  // ============================================================================

  /// Standard box shadow for glass containers
  static List<BoxShadow> get glassShadow => [
        BoxShadow(
          color: Colors.black.withOpacity(0.2),
          blurRadius: 20,
          offset: const Offset(0, 10),
        ),
      ];

  /// Strong shadow for elevated elements
  static List<BoxShadow> get glassShadowStrong => [
        BoxShadow(
          color: Colors.black.withOpacity(0.3),
          blurRadius: 30,
          offset: const Offset(0, 15),
        ),
      ];

  /// Light shadow for subtle elements
  static List<BoxShadow> get glassShadowLight => [
        BoxShadow(
          color: Colors.black.withOpacity(0.1),
          blurRadius: 10,
          offset: const Offset(0, 5),
        ),
      ];

  /// Gold glow shadow
  static List<BoxShadow> get goldGlow => [
        BoxShadow(
          color: accentGold.withOpacity(0.3),
          blurRadius: 20,
          spreadRadius: 2,
        ),
      ];

  // ============================================================================
  // DECORATIONS
  // ============================================================================

  /// Standard glass container decoration
  static BoxDecoration get glassDecoration => BoxDecoration(
        color: glassBackground,
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(
          color: glassBorder,
          width: borderWidth,
        ),
        boxShadow: glassShadow,
      );

  /// Glass decoration with custom radius
  static BoxDecoration glassDecorationWithRadius(double radius) =>
      BoxDecoration(
        color: glassBackground,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(
          color: glassBorder,
          width: borderWidth,
        ),
        boxShadow: glassShadow,
      );

  /// Strong glass container decoration (more opaque)
  static BoxDecoration get glassDecorationStrong => BoxDecoration(
        color: glassBackgroundStrong,
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(
          color: glassBorderActive,
          width: borderWidthActive,
        ),
        boxShadow: glassShadowStrong,
      );

  /// Gold gradient decoration
  static BoxDecoration get goldGradientDecoration => BoxDecoration(
        gradient: const LinearGradient(
          colors: goldGradient,
        ),
        borderRadius: BorderRadius.circular(borderRadius),
        boxShadow: goldGlow,
      );

  // ============================================================================
  // ANIMATIONS
  // ============================================================================

  /// Standard animation duration
  static const Duration animationDuration = Duration(milliseconds: 300);

  /// Fast animation duration
  static const Duration animationDurationFast = Duration(milliseconds: 150);

  /// Slow animation duration
  static const Duration animationDurationSlow = Duration(milliseconds: 500);

  /// Standard animation curve
  static const Curve animationCurve = Curves.easeInOut;

  /// Bounce animation curve
  static const Curve animationCurveBounce = Curves.elasticOut;

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

  /// Get glass decoration with custom opacity
  static BoxDecoration glassDecorationWithOpacity(double opacity) =>
      BoxDecoration(
        color: Colors.white.withOpacity(opacity),
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(
          color: Colors.white.withOpacity(opacity * 2),
          width: borderWidth,
        ),
        boxShadow: glassShadow,
      );

  /// Get glass decoration with custom color
  static BoxDecoration glassDecorationWithColor(Color color) => BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(
          color: color.withOpacity(0.2),
          width: borderWidth,
        ),
        boxShadow: glassShadow,
      );

  /// Creates a card decoration with colored gradient and matching border.
  /// Commonly used for feature cards, mode cards, and stat cards.
  static BoxDecoration coloredCardDecoration({
    required Color color,
    double gradientStartOpacity = 0.15,
    double gradientEndOpacity = 0.05,
    double borderOpacity = 0.3,
    double radius = 20,
    double borderWidth = 1.5,
    bool isDisabled = false,
  }) {
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          color.withOpacity(isDisabled ? 0.05 : gradientStartOpacity),
          color.withOpacity(isDisabled ? 0.02 : gradientEndOpacity),
        ],
      ),
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(
        color: isDisabled
            ? Colors.white.withOpacity(0.1)
            : color.withOpacity(borderOpacity),
        width: borderWidth,
      ),
    );
  }

  /// Creates a status badge decoration (for completed/pending states).
  static BoxDecoration statusBadgeDecoration({
    required bool isActive,
    required Color activeColor,
    double radius = 12,
  }) {
    return BoxDecoration(
      gradient: isActive
          ? LinearGradient(colors: [activeColor, activeColor.withOpacity(0.8)])
          : LinearGradient(colors: [
              AppColors.surface.withOpacity(0.9),
              AppColors.surface.withOpacity(0.85),
            ]),
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(
        color: isActive ? activeColor : Colors.white.withOpacity(0.25),
        width: 1.5,
      ),
      boxShadow: [
        BoxShadow(
          color: isActive
              ? activeColor.withOpacity(0.3)
              : Colors.black.withOpacity(0.3),
          blurRadius: 8,
          offset: const Offset(0, 2),
        ),
      ],
    );
  }
}
