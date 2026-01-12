/// Asset paths for the Luuniensuki LMS app
class AssetPaths {
  AssetPaths._();

  // Base paths
  static const String _imagesPath = 'assets/images';
  static const String _iconsPath = 'assets/icons';
  static const String _animationsPath = 'assets/animations';

  // Logo and branding
  static const String logo = '$_imagesPath/logo.png';
  static const String logoWhite = '$_imagesPath/logo_white.png';
  static const String appIcon = '$_imagesPath/app_icon.png';

  // Placeholder images
  static const String placeholderUrn = '$_imagesPath/placeholder_urn.png';
  static const String placeholderMotif = '$_imagesPath/placeholder_motif.png';
  static const String placeholderAvatar = '$_imagesPath/placeholder_avatar.png';

  // Onboarding images
  static const String onboarding1 = '$_imagesPath/onboarding_1.png';
  static const String onboarding2 = '$_imagesPath/onboarding_2.png';
  static const String onboarding3 = '$_imagesPath/onboarding_3.png';
  static const String onboarding4 = '$_imagesPath/onboarding_4.png';

  // Icons
  static const String iconExplore = '$_iconsPath/explore.svg';
  static const String iconCollection = '$_iconsPath/collection.svg';
  static const String iconAchievements = '$_iconsPath/achievements.svg';
  static const String iconProfile = '$_iconsPath/profile.svg';
  static const String iconXp = '$_iconsPath/xp.svg';
  static const String iconStreak = '$_iconsPath/streak.svg';
  static const String iconBadge = '$_iconsPath/badge.svg';
  static const String iconQuiz = '$_iconsPath/quiz.svg';
  static const String iconLesson = '$_iconsPath/lesson.svg';

  // Status icons
  static const String iconHidden = '$_iconsPath/status_hidden.svg';
  static const String iconDiscovered = '$_iconsPath/status_discovered.svg';
  static const String iconLearned = '$_iconsPath/status_learned.svg';
  static const String iconMastered = '$_iconsPath/status_mastered.svg';

  // Rarity icons
  static const String iconRarityCommon = '$_iconsPath/rarity_common.svg';
  static const String iconRarityUncommon = '$_iconsPath/rarity_uncommon.svg';
  static const String iconRarityRare = '$_iconsPath/rarity_rare.svg';
  static const String iconRarityEpic = '$_iconsPath/rarity_epic.svg';
  static const String iconRarityLegendary = '$_iconsPath/rarity_legendary.svg';

  // Animations (Lottie)
  static const String animationLoading = '$_animationsPath/loading.json';
  static const String animationSuccess = '$_animationsPath/success.json';
  static const String animationError = '$_animationsPath/error.json';
  static const String animationXpGain = '$_animationsPath/xp_gain.json';
  static const String animationBadgeUnlock = '$_animationsPath/badge_unlock.json';
  static const String animationStreak = '$_animationsPath/streak.json';
  static const String animationConfetti = '$_animationsPath/confetti.json';
  static const String animationLevelUp = '$_animationsPath/level_up.json';

  // 3D Models (GLB format)
  static const String model3dPath = 'assets/models';
  static String urnModel(String urnSlug) => '$model3dPath/$urnSlug.glb';
}
