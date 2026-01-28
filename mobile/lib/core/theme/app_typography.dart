import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Typography system for Luuniensuki LMS app.
/// Provides consistent text styles across the application.
class AppTypography {
  AppTypography._();

  // Font families
  static const String fontFamily = 'Roboto';
  static const String displayFontFamily = 'Roboto';

  // Font weights
  static const FontWeight light = FontWeight.w300;
  static const FontWeight regular = FontWeight.w400;
  static const FontWeight medium = FontWeight.w500;
  static const FontWeight semiBold = FontWeight.w600;
  static const FontWeight bold = FontWeight.w700;

  // Text Theme for MaterialApp
  static TextTheme get textTheme => const TextTheme(
        // Display styles - for very large text
        displayLarge: TextStyle(
          fontSize: 57,
          fontWeight: regular,
          letterSpacing: -0.25,
          height: 1.12,
          color: AppColors.textPrimary,
        ),
        displayMedium: TextStyle(
          fontSize: 45,
          fontWeight: regular,
          letterSpacing: 0,
          height: 1.16,
          color: AppColors.textPrimary,
        ),
        displaySmall: TextStyle(
          fontSize: 36,
          fontWeight: regular,
          letterSpacing: 0,
          height: 1.22,
          color: AppColors.textPrimary,
        ),

        // Headline styles - for section headings
        headlineLarge: TextStyle(
          fontSize: 32,
          fontWeight: semiBold,
          letterSpacing: 0,
          height: 1.25,
          color: AppColors.textPrimary,
        ),
        headlineMedium: TextStyle(
          fontSize: 28,
          fontWeight: semiBold,
          letterSpacing: 0,
          height: 1.29,
          color: AppColors.textPrimary,
        ),
        headlineSmall: TextStyle(
          fontSize: 24,
          fontWeight: semiBold,
          letterSpacing: 0,
          height: 1.33,
          color: AppColors.textPrimary,
        ),

        // Title styles - for card titles, list items
        titleLarge: TextStyle(
          fontSize: 22,
          fontWeight: medium,
          letterSpacing: 0,
          height: 1.27,
          color: AppColors.textPrimary,
        ),
        titleMedium: TextStyle(
          fontSize: 16,
          fontWeight: medium,
          letterSpacing: 0.1,
          height: 1.5,
          color: AppColors.textPrimary,
        ),
        titleSmall: TextStyle(
          fontSize: 14,
          fontWeight: medium,
          letterSpacing: 0.05,
          height: 1.43,
          color: AppColors.textPrimary,
        ),

        // Body styles - for regular text content
        bodyLarge: TextStyle(
          fontSize: 16,
          fontWeight: regular,
          letterSpacing: 0.2,
          height: 1.5,
          color: AppColors.textPrimary,
        ),
        bodyMedium: TextStyle(
          fontSize: 14,
          fontWeight: regular,
          letterSpacing: 0.15,
          height: 1.43,
          color: AppColors.textPrimary,
        ),
        bodySmall: TextStyle(
          fontSize: 12,
          fontWeight: regular,
          letterSpacing: 0.2,
          height: 1.33,
          color: AppColors.textSecondary,
        ),

        // Label styles - for buttons, chips, captions
        labelLarge: TextStyle(
          fontSize: 14,
          fontWeight: medium,
          letterSpacing: 0.2,
          height: 1.43,
          color: AppColors.textPrimary,
        ),
        labelMedium: TextStyle(
          fontSize: 12,
          fontWeight: medium,
          letterSpacing: 0.3,
          height: 1.33,
          color: AppColors.textPrimary,
        ),
        labelSmall: TextStyle(
          fontSize: 11,
          fontWeight: medium,
          letterSpacing: 0.3,
          height: 1.45,
          color: AppColors.textSecondary,
        ),
      ).apply(fontFamily: fontFamily);

  // Custom styles for specific use cases

  /// XP counter style - bold gold text
  static TextStyle get xpCounter => const TextStyle(
        fontSize: 18,
        fontWeight: bold,
        color: AppColors.xpGold,
        letterSpacing: 0.5,
      );

  /// Streak counter style - bold orange text
  static TextStyle get streakCounter => const TextStyle(
        fontSize: 18,
        fontWeight: bold,
        color: AppColors.streakOrange,
        letterSpacing: 0.5,
      );

  /// Badge name style
  static TextStyle get badgeName => const TextStyle(
        fontSize: 14,
        fontWeight: semiBold,
        color: AppColors.badgePurple,
      );

  /// Rank name style - for displaying user rank
  static TextStyle get rankName => const TextStyle(
        fontSize: 16,
        fontWeight: bold,
        color: AppColors.primary,
        letterSpacing: 0.5,
      );

  /// Lesson title style
  static TextStyle get lessonTitle => const TextStyle(
        fontSize: 20,
        fontWeight: semiBold,
        color: AppColors.textPrimary,
        height: 1.3,
      );

  /// Lesson body text style
  static TextStyle get lessonBody => const TextStyle(
        fontSize: 16,
        fontWeight: regular,
        color: AppColors.textPrimary,
        height: 1.6,
      );

  /// Quiz question style
  static TextStyle get quizQuestion => const TextStyle(
        fontSize: 18,
        fontWeight: medium,
        color: AppColors.textPrimary,
        height: 1.4,
      );

  /// Quiz answer option style
  static TextStyle get quizOption => const TextStyle(
        fontSize: 16,
        fontWeight: regular,
        color: AppColors.textPrimary,
        height: 1.4,
      );

  /// Vietnamese text style - slightly larger for better readability
  static TextStyle get vietnameseText => const TextStyle(
        fontSize: 17,
        fontWeight: regular,
        color: AppColors.textPrimary,
        height: 1.7,
        letterSpacing: 0.3,
      );

  /// Motif name style
  static TextStyle get motifName => const TextStyle(
        fontSize: 18,
        fontWeight: semiBold,
        color: AppColors.textPrimary,
      );

  /// Urn name style
  static TextStyle get urnName => const TextStyle(
        fontSize: 20,
        fontWeight: bold,
        color: AppColors.primary,
        letterSpacing: 0.5,
      );

  /// Empty state message style
  static TextStyle get emptyState => const TextStyle(
        fontSize: 16,
        fontWeight: regular,
        color: AppColors.textHint,
        height: 1.5,
      );

  /// Error message style
  static TextStyle get errorMessage => const TextStyle(
        fontSize: 14,
        fontWeight: regular,
        color: AppColors.error,
      );

  /// Success message style
  static TextStyle get successMessage => const TextStyle(
        fontSize: 14,
        fontWeight: regular,
        color: AppColors.success,
      );

  /// Button text style
  static TextStyle get buttonText => const TextStyle(
        fontSize: 16,
        fontWeight: semiBold,
        letterSpacing: 0.5,
      );

  /// Tab label style
  static TextStyle get tabLabel => const TextStyle(
        fontSize: 14,
        fontWeight: medium,
        letterSpacing: 0.1,
      );

  /// Navigation label style
  static TextStyle get navLabel => const TextStyle(
        fontSize: 12,
        fontWeight: medium,
        letterSpacing: 0.5,
      );

  /// Card subtitle style
  static TextStyle get cardSubtitle => const TextStyle(
        fontSize: 12,
        fontWeight: regular,
        color: AppColors.textSecondary,
      );

  /// Progress percentage style
  static TextStyle get progressPercent => const TextStyle(
        fontSize: 24,
        fontWeight: bold,
        color: AppColors.primary,
      );

  /// Leaderboard rank number style
  static TextStyle get leaderboardRank => const TextStyle(
        fontSize: 20,
        fontWeight: bold,
        color: AppColors.primary,
      );

  /// Leaderboard XP style
  static TextStyle get leaderboardXp => const TextStyle(
        fontSize: 14,
        fontWeight: medium,
        color: AppColors.xpGold,
      );

  /// Helper to apply custom color to any style
  static TextStyle withColor(TextStyle style, Color color) {
    return style.copyWith(color: color);
  }

  /// Helper to apply custom size to any style
  static TextStyle withSize(TextStyle style, double size) {
    return style.copyWith(fontSize: size);
  }

  /// Helper to make any style bold
  static TextStyle asBold(TextStyle style) {
    return style.copyWith(fontWeight: bold);
  }

  // ==========================================================================
  // PREMIUM TEXT STYLES - Enhanced typography for better readability
  // ==========================================================================

  /// Premium heading style with increased letter spacing
  static TextStyle get premiumHeading => const TextStyle(
        letterSpacing: 0.5,
        fontWeight: FontWeight.w700,
        height: 1.2,
      );

  /// Premium body text optimized for Vietnamese
  static TextStyle get premiumBody => const TextStyle(
        letterSpacing: 0.2,
        height: 1.7, // Better for Vietnamese diacritics
      );

  /// Gold gradient text style for XP/rewards (requires ShaderMask)
  static TextStyle goldAccent(Rect bounds) => TextStyle(
        fontWeight: FontWeight.bold,
        letterSpacing: 0.3,
        foreground: Paint()
          ..shader = const LinearGradient(
            colors: [
              AppColors.primaryLight,
              AppColors.primary,
              AppColors.primaryDark,
            ],
          ).createShader(bounds),
      );

  /// Screen title style
  static TextStyle get screenTitle => const TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.bold,
        letterSpacing: -0.5,
        height: 1.2,
      );

  /// Card title style
  static TextStyle get cardTitle => const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.2,
      );

  /// Stat number style (large numbers in stats)
  static TextStyle get statNumber => const TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.bold,
        letterSpacing: 0.3,
      );
}
