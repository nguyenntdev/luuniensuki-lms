import 'package:flutter/material.dart';

/// App color palette matching web design.
/// Dark theme with Vietnamese imperial gold accent.
class AppColors {
  AppColors._();

  // ==========================================================================
  // PRIMARY PALETTE - Refined Imperial Gold (warmer, more luminous)
  // ==========================================================================

  /// Primary gold color - Warmer, more luminous gold
  static const Color primary = Color(0xFFE8B44C);

  /// Darker gold for emphasis - Rich deep gold
  static const Color primaryDark = Color(0xFFD49B38);

  /// Lighter gold for highlights - Champagne gold
  static const Color primaryLight = Color(0xFFF5D078);

  /// Very light gold for subtle backgrounds
  static const Color primarySurface = Color(0xFF2A2520);

  // ==========================================================================
  // BACKGROUND COLORS - Deeper, richer navy
  // ==========================================================================

  /// Main background - Deep midnight
  static const Color background = Color(0xFF0A0E14);

  /// Card/surface background - Elevated dark
  static const Color surface = Color(0xFF141921);

  /// Elevated surface - Card surface
  static const Color surfaceElevated = Color(0xFF1C232D);

  /// Variant surface for alternating backgrounds
  static const Color surfaceVariant = Color(0xFF1C2128);

  // ==========================================================================
  // SECONDARY PALETTE - Imperial Red (refined)
  // ==========================================================================

  /// Secondary red - Refined imperial red
  static const Color secondary = Color(0xFFC41E3A);

  /// Secondary light variant
  static const Color secondaryLight = Color(0xFFE8415A);

  /// Text on secondary color backgrounds
  static const Color onSecondary = Color(0xFFFFFFFF);

  // ==========================================================================
  // BORDER & DIVIDER COLORS
  // ==========================================================================

  /// Border color
  static const Color border = Color(0xFF30363D);

  /// Divider color
  static const Color divider = Color(0xFF21262D);

  /// Input field background
  static const Color inputBackground = Color(0xFF21262D);

  // ==========================================================================
  // TEXT COLORS - Better contrast
  // ==========================================================================

  /// Primary text - Near white
  static const Color textPrimary = Color(0xFFF5F5F5);

  /// Secondary text - Clearer secondary
  static const Color textSecondary = Color(0xFFB8BCC5);

  /// Tertiary/hint text - Muted hints
  static const Color textHint = Color(0xFF6B7280);

  /// Disabled text
  static const Color textDisabled = Color(0xFF6E6A64);

  /// Text on primary (gold) backgrounds
  static const Color onPrimary = Color(0xFF1A1A1A);

  /// Text on surface
  static const Color onSurface = Color(0xFFF5F5F5);

  /// Muted foreground
  static const Color mutedForeground = Color(0xFFBFB8A8);

  // ==========================================================================
  // ACCENT COLORS
  // ==========================================================================

  /// Secondary accent - imperial red
  static const Color accent = Color(0xFFC41E3A);

  /// Accent light variant
  static const Color accentLight = Color(0xFFE8415A);

  // ==========================================================================
  // SEMANTIC COLORS - Softer, harmonized with gold palette
  // ==========================================================================

  /// Success green - Soft teal-green
  static const Color success = Color(0xFF34D399);

  /// Success light/surface
  static const Color successSurface = Color(0xFF1A3D1C);

  /// Error red - Warm coral
  static const Color error = Color(0xFFEF6B6B);

  /// Error light/surface
  static const Color errorSurface = Color(0xFF3D1A1A);

  /// Error light variant (for backgrounds)
  static const Color errorLight = Color(0xFFFFEBEE);

  /// Warning amber
  static const Color warning = Color(0xFFF59E0B);

  /// Warning light/surface
  static const Color warningSurface = Color(0xFF3D3018);

  /// Info blue - Soft blue
  static const Color info = Color(0xFF60A5FA);

  /// Info light/surface
  static const Color infoSurface = Color(0xFF1A2D3D);

  // ==========================================================================
  // GAMIFICATION COLORS
  // ==========================================================================

  /// XP gold - bright gold for XP displays
  static const Color xpGold = Color(0xFFFFD700);

  /// XP gold dark
  static const Color xpGoldDark = Color(0xFFD4A200);

  /// Streak orange
  static const Color streakOrange = Color(0xFFFF6B35);

  /// Streak surface
  static const Color streakSurface = Color(0xFF3D2818);

  /// Badge purple
  static const Color badgePurple = Color(0xFF9C27B0);

  /// Badge surface
  static const Color badgeSurface = Color(0xFF2D1A3D);

  /// Quest blue
  static const Color questBlue = Color(0xFF3F51B5);

  /// Level up green
  static const Color levelUpGreen = Color(0xFF00C853);

  /// Gem yellow (cyan-yellow for gems)
  static const Color gemYellow = Color(0xFFFFD700);

  // ==========================================================================
  // PROGRESS STATUS COLORS
  // ==========================================================================

  /// Hidden/undiscovered
  static const Color statusHidden = Color(0xFF6E6A64);

  /// Discovered
  static const Color statusDiscovered = Color(0xFF4CAF50);

  /// Learned
  static const Color statusLearned = Color(0xFF2196F3);

  /// Mastered
  static const Color statusMastered = Color(0xFF9C27B0);

  // ==========================================================================
  // RARITY COLORS
  // ==========================================================================

  /// Common
  static const Color rarityCommon = Color(0xFF6E6A64);

  /// Uncommon
  static const Color rarityUncommon = Color(0xFF4CAF50);

  /// Rare
  static const Color rarityRare = Color(0xFF2196F3);

  /// Epic
  static const Color rarityEpic = Color(0xFF9C27B0);

  /// Legendary
  static const Color rarityLegendary = Color(0xFFFFD700);

  // ==========================================================================
  // PURE COLORS
  // ==========================================================================

  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);
  static const Color transparent = Colors.transparent;

  // ==========================================================================
  // GLASS EFFECTS
  // ==========================================================================

  /// Glass white for glass containers
  static const Color glassWhite = Color(0x1AFFFFFF);

  /// Glass border
  static const Color glassBorder = Color(0x33FFFFFF);

  // ==========================================================================
  // GRADIENTS
  // ==========================================================================

  /// Primary gradient (gold)
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primaryLight, primary, primaryDark],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Background gradient (matching updated background colors)
  static const LinearGradient backgroundGradient = LinearGradient(
    colors: [
      Color(0xFF0A0E14),
      Color(0xFF0C1016),
      Color(0xFF0B0F15),
      Color(0xFF090D13),
    ],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  /// XP gradient
  static const LinearGradient xpGradient = LinearGradient(
    colors: [xpGold, xpGoldDark],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  /// Card gradient overlay
  static const LinearGradient cardGradient = LinearGradient(
    colors: [
      Color(0xFF141921),
      Color(0xFF1C232D),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ==========================================================================
  // SHADOWS
  // ==========================================================================

  /// Gold glow shadow
  static List<BoxShadow> get goldGlow => [
        BoxShadow(
          color: primary.withOpacity(0.3),
          blurRadius: 20,
          offset: const Offset(0, 8),
        ),
      ];

  /// Elegant shadow
  static List<BoxShadow> get elegantShadow => [
        BoxShadow(
          color: black.withOpacity(0.45),
          blurRadius: 50,
          offset: const Offset(0, 18),
        ),
      ];

  /// Card shadow
  static List<BoxShadow> get cardShadow => [
        BoxShadow(
          color: black.withOpacity(0.2),
          blurRadius: 10,
          offset: const Offset(0, 4),
        ),
      ];

  // ==========================================================================
  // HELPER METHODS
  // ==========================================================================

  /// Get color for progress status
  static Color forStatus(String status) {
    switch (status.toLowerCase()) {
      case 'discovered':
        return statusDiscovered;
      case 'learned':
        return statusLearned;
      case 'mastered':
        return statusMastered;
      case 'hidden':
      default:
        return statusHidden;
    }
  }

  /// Get color for rarity level
  static Color forRarity(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'uncommon':
        return rarityUncommon;
      case 'rare':
        return rarityRare;
      case 'epic':
        return rarityEpic;
      case 'legendary':
        return rarityLegendary;
      case 'common':
      default:
        return rarityCommon;
    }
  }
}
