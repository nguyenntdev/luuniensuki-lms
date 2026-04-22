import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Extension methods for BuildContext
extension BuildContextX on BuildContext {
  /// Get the current theme
  ThemeData get theme => Theme.of(this);

  /// Get the current color scheme
  ColorScheme get colorScheme => Theme.of(this).colorScheme;

  /// Get the current text theme
  TextTheme get textTheme => Theme.of(this).textTheme;

  /// Get screen size
  Size get screenSize => MediaQuery.sizeOf(this);

  /// Get screen width
  double get screenWidth => MediaQuery.sizeOf(this).width;

  /// Get screen height
  double get screenHeight => MediaQuery.sizeOf(this).height;

  /// Get safe area padding
  EdgeInsets get safeAreaPadding => MediaQuery.paddingOf(this);

  /// Check if keyboard is visible
  bool get isKeyboardVisible => MediaQuery.viewInsetsOf(this).bottom > 0;

  /// Get keyboard height
  double get keyboardHeight => MediaQuery.viewInsetsOf(this).bottom;

  /// Check if dark mode is enabled
  bool get isDarkMode => Theme.of(this).brightness == Brightness.dark;

  /// Show a snackbar with the given message
  void showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? colorScheme.error : null,
      ),
    );
  }

  /// Show a success snackbar
  void showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle, color: Colors.white),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: Colors.green,
      ),
    );
  }

  /// Show an error snackbar
  void showErrorSnackBar(String message) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error, color: Colors.white),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: colorScheme.error,
      ),
    );
  }

  /// Hide current snackbar
  void hideSnackBar() {
    ScaffoldMessenger.of(this).hideCurrentSnackBar();
  }

  /// Pop the current route
  void pop<T>([T? result]) => Navigator.of(this).pop(result);

  /// Check if device is tablet (screen width >= 600)
  bool get isTablet => screenWidth >= 600;

  /// Check if device is in landscape orientation
  bool get isLandscape => screenWidth > screenHeight;
}

/// Extension methods for String
extension StringX on String {
  /// Capitalize first letter
  String get capitalize {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }

  /// Capitalize first letter of each word
  String get titleCase {
    if (isEmpty) return this;
    return split(' ').map((word) => word.capitalize).join(' ');
  }

  /// Check if string is a valid email
  bool get isValidEmail {
    final emailRegex = RegExp(
      r'^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+',
    );
    return emailRegex.hasMatch(this);
  }

  /// Check if string is a valid password (min 8 chars)
  bool get isValidPassword => length >= 8;

  /// Truncate string with ellipsis
  String truncate(int maxLength) {
    if (length <= maxLength) return this;
    return '${substring(0, maxLength - 3)}...';
  }

  /// Convert to slug (lowercase, hyphenated)
  String get toSlug {
    return toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9\s-]'), '')
        .replaceAll(RegExp(r'\s+'), '-');
  }

  /// Remove HTML tags
  String get stripHtml {
    return replaceAll(RegExp(r'<[^>]*>'), '');
  }

  /// Check if string contains only digits
  bool get isNumeric => RegExp(r'^\d+$').hasMatch(this);

  /// Convert to int or return null
  int? get toIntOrNull => int.tryParse(this);

  /// Convert to double or return null
  double? get toDoubleOrNull => double.tryParse(this);
}

/// Extension methods for String? (nullable)
extension NullableStringX on String? {
  /// Check if string is null or empty
  bool get isNullOrEmpty => this == null || this!.isEmpty;

  /// Check if string is not null and not empty
  bool get isNotNullOrEmpty => this != null && this!.isNotEmpty;

  /// Return this or default value if null/empty
  String orDefault(String defaultValue) {
    return isNullOrEmpty ? defaultValue : this!;
  }
}

/// Extension methods for int
extension IntX on int {
  /// Format number with thousand separators
  String get formatted => NumberFormat('#,##0').format(this);

  /// Format as XP value
  String get asXp => '${formatted} XP';

  /// Convert to duration in seconds
  Duration get seconds => Duration(seconds: this);

  /// Convert to duration in milliseconds
  Duration get milliseconds => Duration(milliseconds: this);

  /// Convert to duration in minutes
  Duration get minutes => Duration(minutes: this);

  /// Convert to duration in hours
  Duration get hours => Duration(hours: this);

  /// Convert to duration in days
  Duration get days => Duration(days: this);

  /// Check if value is within range
  bool isBetween(int min, int max) => this >= min && this <= max;

  /// Pad with leading zeros
  String padLeft(int width) => toString().padLeft(width, '0');
}

/// Extension methods for double
extension DoubleX on double {
  /// Round to specified decimal places
  double roundTo(int places) {
    final multiplier = 10.0 * places;
    return (this * multiplier).round() / multiplier;
  }

  /// Format as percentage
  String get asPercent => '${(this * 100).round()}%';

  /// Format as percentage with value already being 0-100
  String get asPercentDirect => '${round()}%';
}

/// Extension methods for DateTime
extension DateTimeX on DateTime {
  /// Format as relative time (e.g., "2 hours ago")
  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(this);

    if (difference.inDays > 365) {
      return '${(difference.inDays / 365).floor()} năm trước';
    } else if (difference.inDays > 30) {
      return '${(difference.inDays / 30).floor()} tháng trước';
    } else if (difference.inDays > 7) {
      return '${(difference.inDays / 7).floor()} tuần trước';
    } else if (difference.inDays > 0) {
      return '${difference.inDays} ngày trước';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} giờ trước';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} phút trước';
    } else {
      return 'Vừa xong';
    }
  }

  /// Format as date string (dd/MM/yyyy)
  String get formattedDate => DateFormat('dd/MM/yyyy').format(this);

  /// Format as time string (HH:mm)
  String get formattedTime => DateFormat('HH:mm').format(this);

  /// Format as full date time (dd/MM/yyyy HH:mm)
  String get formattedDateTime => DateFormat('dd/MM/yyyy HH:mm').format(this);

  /// Format as short month day (dd MMM)
  String get shortMonthDay => DateFormat('dd MMM').format(this);

  /// Check if date is today
  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }

  /// Check if date is yesterday
  bool get isYesterday {
    final yesterday = DateTime.now().subtract(const Duration(days: 1));
    return year == yesterday.year && month == yesterday.month && day == yesterday.day;
  }

  /// Check if date is this week
  bool get isThisWeek {
    final now = DateTime.now();
    final startOfWeek = now.subtract(Duration(days: now.weekday - 1));
    final endOfWeek = startOfWeek.add(const Duration(days: 6));
    return isAfter(startOfWeek.subtract(const Duration(days: 1))) &&
        isBefore(endOfWeek.add(const Duration(days: 1)));
  }

  /// Start of day
  DateTime get startOfDay => DateTime(year, month, day);

  /// End of day
  DateTime get endOfDay => DateTime(year, month, day, 23, 59, 59, 999);
}

/// Extension methods for Duration
extension DurationX on Duration {
  /// Format as mm:ss
  String get formatted {
    final minutes = inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  /// Format as hh:mm:ss
  String get formattedLong {
    final hours = inHours.toString().padLeft(2, '0');
    final minutes = inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$hours:$minutes:$seconds';
  }

  /// Format as human readable (e.g., "2h 30m")
  String get humanReadable {
    if (inDays > 0) {
      return '${inDays}d ${inHours.remainder(24)}h';
    } else if (inHours > 0) {
      return '${inHours}h ${inMinutes.remainder(60)}m';
    } else if (inMinutes > 0) {
      return '${inMinutes}m ${inSeconds.remainder(60)}s';
    } else {
      return '${inSeconds}s';
    }
  }
}

/// Extension methods for List
extension ListX<T> on List<T> {
  /// Get first element or null if empty
  T? get firstOrNull => isEmpty ? null : first;

  /// Get last element or null if empty
  T? get lastOrNull => isEmpty ? null : last;

  /// Get element at index or null if out of bounds
  T? getOrNull(int index) {
    if (index < 0 || index >= length) return null;
    return this[index];
  }

  /// Separate list into chunks of given size
  List<List<T>> chunked(int chunkSize) {
    final List<List<T>> chunks = [];
    for (var i = 0; i < length; i += chunkSize) {
      chunks.add(sublist(i, i + chunkSize > length ? length : i + chunkSize));
    }
    return chunks;
  }
}

/// Extension methods for Map
extension MapX<K, V> on Map<K, V> {
  /// Get value or default if key not found
  V getOrDefault(K key, V defaultValue) {
    return this[key] ?? defaultValue;
  }
}

/// Extension methods for Color
extension ColorX on Color {
  /// Create a MaterialColor swatch from this color
  MaterialColor get asMaterialColor {
    final Map<int, Color> swatch = {};
    final int r = red;
    final int g = green;
    final int b = blue;

    for (final strength in <int>[50, 100, 200, 300, 400, 500, 600, 700, 800, 900]) {
      final double ds = 0.5 - (strength / 1000);
      swatch[strength] = Color.fromRGBO(
        (r + ((ds < 0 ? r : (255 - r)) * ds).round()).clamp(0, 255),
        (g + ((ds < 0 ? g : (255 - g)) * ds).round()).clamp(0, 255),
        (b + ((ds < 0 ? b : (255 - b)) * ds).round()).clamp(0, 255),
        1,
      );
    }
    return MaterialColor(red << 16 | green << 8 | blue, swatch);
  }

  /// Darken the color by a percentage (0-100)
  Color darken([int percent = 10]) {
    assert(percent >= 0 && percent <= 100);
    final f = 1 - percent / 100;
    return Color.fromARGB(
      alpha,
      (red * f).round().clamp(0, 255),
      (green * f).round().clamp(0, 255),
      (blue * f).round().clamp(0, 255),
    );
  }

  /// Lighten the color by a percentage (0-100)
  Color lighten([int percent = 10]) {
    assert(percent >= 0 && percent <= 100);
    final f = percent / 100;
    return Color.fromARGB(
      alpha,
      (red + ((255 - red) * f)).round().clamp(0, 255),
      (green + ((255 - green) * f)).round().clamp(0, 255),
      (blue + ((255 - blue) * f)).round().clamp(0, 255),
    );
  }
}

/// Extension methods for Widget
extension WidgetX on Widget {
  /// Wrap widget with Padding
  Widget padded([EdgeInsets padding = const EdgeInsets.all(16)]) {
    return Padding(padding: padding, child: this);
  }

  /// Wrap widget with horizontal padding
  Widget paddedH([double padding = 16]) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: padding),
      child: this,
    );
  }

  /// Wrap widget with vertical padding
  Widget paddedV([double padding = 16]) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: padding),
      child: this,
    );
  }

  /// Center the widget
  Widget centered() => Center(child: this);

  /// Expand the widget to fill available space
  Widget expanded([int flex = 1]) => Expanded(flex: flex, child: this);

  /// Make widget flexible
  Widget flexible([int flex = 1]) => Flexible(flex: flex, child: this);

  /// Add SizedBox spacing below widget
  Widget withSpaceBelow([double space = 16]) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [this, SizedBox(height: space)],
    );
  }

  /// Add SizedBox spacing after widget (for Row)
  Widget withSpaceAfter([double space = 16]) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [this, SizedBox(width: space)],
    );
  }
}
