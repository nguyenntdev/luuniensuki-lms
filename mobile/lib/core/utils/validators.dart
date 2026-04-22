/// Form validators for authentication and user input.
/// Provides consistent validation logic across the app.
class Validators {
  Validators._();

  // Email validation regex
  static final _emailRegex = RegExp(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
  );

  // Password requirements
  static const int minPasswordLength = 8;
  static const int maxPasswordLength = 72; // bcrypt limitation

  // Display name requirements
  static const int minDisplayNameLength = 2;
  static const int maxDisplayNameLength = 50;

  // Username requirements
  static const int minUsernameLength = 3;
  static const int maxUsernameLength = 30;
  static final _usernameRegex = RegExp(r'^[a-zA-Z0-9_]+$');

  // ==========================================================================
  // EMAIL VALIDATION
  // ==========================================================================

  /// Validate email address
  /// Returns null if valid, error message if invalid
  static String? email(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email là bắt buộc';
    }

    final trimmed = value.trim();

    if (!_emailRegex.hasMatch(trimmed)) {
      return 'Email không hợp lệ';
    }

    return null;
  }

  /// Validate email for login (less strict)
  static String? loginEmail(String? value) {
    if (value == null || value.isEmpty) {
      return 'Vui lòng nhập email';
    }

    if (!value.contains('@')) {
      return 'Email không hợp lệ';
    }

    return null;
  }

  // ==========================================================================
  // PASSWORD VALIDATION
  // ==========================================================================

  /// Validate password (basic)
  /// Returns null if valid, error message if invalid
  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Mật khẩu là bắt buộc';
    }

    if (value.length < minPasswordLength) {
      return 'Mật khẩu phải có ít nhất $minPasswordLength ký tự';
    }

    if (value.length > maxPasswordLength) {
      return 'Mật khẩu không được quá $maxPasswordLength ký tự';
    }

    return null;
  }

  /// Validate password with strength requirements
  static String? strongPassword(String? value) {
    final basicError = password(value);
    if (basicError != null) return basicError;

    final pwd = value!;

    if (!pwd.contains(RegExp(r'[A-Z]'))) {
      return 'Mật khẩu phải có ít nhất 1 chữ hoa';
    }

    if (!pwd.contains(RegExp(r'[a-z]'))) {
      return 'Mật khẩu phải có ít nhất 1 chữ thường';
    }

    if (!pwd.contains(RegExp(r'[0-9]'))) {
      return 'Mật khẩu phải có ít nhất 1 chữ số';
    }

    return null;
  }

  /// Validate password confirmation
  static String? confirmPassword(String? value, String? original) {
    if (value == null || value.isEmpty) {
      return 'Vui lòng xác nhận mật khẩu';
    }

    if (value != original) {
      return 'Mật khẩu xác nhận không khớp';
    }

    return null;
  }

  /// Create a confirm password validator with the original password
  static String? Function(String?) confirmPasswordValidator(String? original) {
    return (value) => confirmPassword(value, original);
  }

  // ==========================================================================
  // DISPLAY NAME VALIDATION
  // ==========================================================================

  /// Validate display name
  static String? displayName(String? value) {
    if (value == null || value.isEmpty) {
      return 'Tên hiển thị là bắt buộc';
    }

    final trimmed = value.trim();

    if (trimmed.length < minDisplayNameLength) {
      return 'Tên hiển thị phải có ít nhất $minDisplayNameLength ký tự';
    }

    if (trimmed.length > maxDisplayNameLength) {
      return 'Tên hiển thị không được quá $maxDisplayNameLength ký tự';
    }

    return null;
  }

  // ==========================================================================
  // USERNAME VALIDATION
  // ==========================================================================

  /// Validate username
  static String? username(String? value) {
    if (value == null || value.isEmpty) {
      return 'Tên người dùng là bắt buộc';
    }

    final trimmed = value.trim();

    if (trimmed.length < minUsernameLength) {
      return 'Tên người dùng phải có ít nhất $minUsernameLength ký tự';
    }

    if (trimmed.length > maxUsernameLength) {
      return 'Tên người dùng không được quá $maxUsernameLength ký tự';
    }

    if (!_usernameRegex.hasMatch(trimmed)) {
      return 'Tên người dùng chỉ được chứa chữ cái, số và dấu gạch dưới';
    }

    return null;
  }

  // ==========================================================================
  // GENERIC VALIDATORS
  // ==========================================================================

  /// Validate required field
  static String? required(String? value, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) {
      return fieldName != null ? '$fieldName là bắt buộc' : 'Trường này là bắt buộc';
    }
    return null;
  }

  /// Validate minimum length
  static String? minLength(String? value, int min, {String? fieldName}) {
    if (value == null || value.isEmpty) {
      return null; // Let required validator handle empty
    }

    if (value.length < min) {
      return fieldName != null
          ? '$fieldName phải có ít nhất $min ký tự'
          : 'Phải có ít nhất $min ký tự';
    }

    return null;
  }

  /// Validate maximum length
  static String? maxLength(String? value, int max, {String? fieldName}) {
    if (value == null || value.isEmpty) {
      return null;
    }

    if (value.length > max) {
      return fieldName != null
          ? '$fieldName không được quá $max ký tự'
          : 'Không được quá $max ký tự';
    }

    return null;
  }

  /// Validate numeric value
  static String? numeric(String? value, {String? fieldName}) {
    if (value == null || value.isEmpty) {
      return null;
    }

    if (int.tryParse(value) == null && double.tryParse(value) == null) {
      return fieldName != null ? '$fieldName phải là số' : 'Giá trị phải là số';
    }

    return null;
  }

  /// Validate integer value
  static String? integer(String? value, {String? fieldName}) {
    if (value == null || value.isEmpty) {
      return null;
    }

    if (int.tryParse(value) == null) {
      return fieldName != null
          ? '$fieldName phải là số nguyên'
          : 'Giá trị phải là số nguyên';
    }

    return null;
  }

  /// Validate positive number
  static String? positive(String? value, {String? fieldName}) {
    if (value == null || value.isEmpty) {
      return null;
    }

    final number = double.tryParse(value);
    if (number == null || number <= 0) {
      return fieldName != null
          ? '$fieldName phải là số dương'
          : 'Giá trị phải là số dương';
    }

    return null;
  }

  // ==========================================================================
  // COMBINE VALIDATORS
  // ==========================================================================

  /// Combine multiple validators into one
  /// Runs each validator in order and returns the first error
  static String? Function(String?) combine(
      List<String? Function(String?)> validators) {
    return (value) {
      for (final validator in validators) {
        final error = validator(value);
        if (error != null) return error;
      }
      return null;
    };
  }
}
