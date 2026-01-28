import 'package:flutter/material.dart';

/// Utility class for badge category-related operations
class BadgeCategoryUtils {
  BadgeCategoryUtils._(); // Private constructor to prevent instantiation

  /// Get the icon for a badge category
  static IconData getIcon(String category) {
    switch (category.toLowerCase()) {
      case 'discovery':
        return Icons.visibility;
      case 'learning':
        return Icons.school;
      case 'mastery':
        return Icons.star;
      case 'social':
        return Icons.people;
      case 'streak':
        return Icons.local_fire_department;
      case 'collection':
        return Icons.collections;
      case 'achievement':
        return Icons.workspace_premium;
      case 'special':
        return Icons.auto_awesome;
      default:
        return Icons.military_tech;
    }
  }

  /// Get the display name for a badge category
  static String getName(String category) {
    switch (category.toLowerCase()) {
      case 'discovery':
        return 'Khám Phá';
      case 'learning':
        return 'Học Tập';
      case 'mastery':
        return 'Thành Thạo';
      case 'social':
        return 'Xã Hội';
      case 'streak':
        return 'Chuỗi Ngày';
      case 'collection':
        return 'Sưu Tập';
      case 'achievement':
        return 'Thành Tích';
      case 'special':
        return 'Đặc Biệt';
      default:
        return category;
    }
  }
}

