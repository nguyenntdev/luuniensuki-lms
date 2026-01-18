class ErrorMessages {
  ErrorMessages._();

  static const Map<String, String> vietnamese = {
    'NETWORK_ERROR':
        'Không có kết nối mạng. Vui lòng kiểm tra kết nối internet của bạn.',
    'CACHE_ERROR': 'Lỗi lưu trữ dữ liệu cục bộ.',
    'UNAUTHENTICATED': 'Bạn chưa đăng nhập.',
    'SESSION_EXPIRED': 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
    'INVALID_CREDENTIALS': 'Email hoặc mật khẩu không đúng.',
    'ACCOUNT_DISABLED': 'Tài khoản đã bị vô hiệu hóa.',
    'VALIDATION_ERROR': 'Dữ liệu nhập không hợp lệ.',
    'NOT_FOUND': 'Không tìm thấy tài nguyên.',
    'PERMISSION_DENIED': 'Bạn không có quyền truy cập.',
    'TIMEOUT': 'Yêu cầu đã hết thời gian chờ.',
    'UNEXPECTED_ERROR': 'Đã xảy ra lỗi không mong muốn.',
    'SERVER_ERROR': 'Lỗi máy chủ. Vui lòng thử lại sau.',
    'GUEST_RESTRICTED': 'Nội dung này không khả dụng cho người dùng khách.',
    'NOT_DISCOVERED': 'Bạn phải khám phá motif này trước.',
    'MOTIF_NOT_FOUND': 'Không tìm thấy motif.',
    'URN_NOT_FOUND': 'Không tìm thấy urn.',
  };

  static const Map<String, String> validationMessages = {
    'email_required': 'Email là bắt buộc.',
    'email_invalid': 'Email không hợp lệ.',
    'password_required': 'Mật khẩu là bắt buộc.',
    'password_too_short': 'Mật khẩu phải có ít nhất 6 ký tự.',
    'password_mismatch': 'Mật khẩu xác nhận không khớp.',
    'field_required': 'Trường này là bắt buộc.',
    'name_required': 'Tên là bắt buộc.',
    'phone_invalid': 'Số điện thoại không hợp lệ.',
  };

  static const Map<int, String> httpStatusMessages = {
    400: 'Yêu cầu không hợp lệ.',
    401: 'Bạn chưa đăng nhập.',
    403: 'Bạn không có quyền truy cập.',
    404: 'Không tìm thấy tài nguyên.',
    408: 'Yêu cầu đã hết thời gian chờ.',
    422: 'Dữ liệu không hợp lệ.',
    429: 'Quá nhiều yêu cầu. Vui lòng thử lại sau.',
    500: 'Lỗi máy chủ nội bộ.',
    502: 'Máy chủ tạm thời không khả dụng.',
    503: 'Dịch vụ tạm thời không khả dụng.',
    504: 'Máy chủ không phản hồi.',
  };

  static String getErrorMessage(String? code, {int? statusCode}) {
    if (statusCode != null && httpStatusMessages.containsKey(statusCode)) {
      return httpStatusMessages[statusCode]!;
    }

    if (code != null && vietnamese.containsKey(code)) {
      return vietnamese[code]!;
    }

    return vietnamese['UNEXPECTED_ERROR']!;
  }

  static String getValidationMessage(String key) {
    return validationMessages[key] ?? validationMessages['field_required']!;
  }

  static String getHttpStatusMessage(int statusCode) {
    return httpStatusMessages[statusCode] ??
        'Lỗi không xác định (Mã: $statusCode)';
  }
}
