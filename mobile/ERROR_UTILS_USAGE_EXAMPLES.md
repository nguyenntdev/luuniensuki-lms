# ErrorUtils Usage Examples

## Overview
`ErrorUtils` is a centralized utility class for formatting error messages into user-friendly Vietnamese text. It provides consistent error messaging across the entire app.

## File Location
```
mobile/lib/core/utils/error_utils.dart
```

## Basic Usage

### 1. Format Errors for User Display

```dart
import 'package:mobile/core/utils/error_utils.dart';

// In your widget or provider
try {
  await fetchQuizData();
} catch (e) {
  final userMessage = ErrorUtils.formatForUser(e);
  
  if (mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(userMessage),
        backgroundColor: AppColors.error,
      ),
    );
  }
}
```

### 2. Check if Error is Network-Related

```dart
import 'package:mobile/core/utils/error_utils.dart';

try {
  await repository.syncData();
} catch (e) {
  if (ErrorUtils.isNetworkError(e)) {
    // Show offline indicator or cached data
    showOfflineMode();
  } else {
    // Show generic error
    showErrorDialog(ErrorUtils.formatForUser(e));
  }
}
```

### 3. Refactoring Existing Error Handling

**Before (quiz_screen.dart):**
```dart
String _formatErrorForUser(String rawError) {
  if (rawError.contains('SocketException') || rawError.contains('NetworkException')) {
    return 'Không có kết nối mạng';
  }
  if (rawError.contains('NotFoundException') || rawError.contains('404')) {
    return 'Không tìm thấy bài trắc nghiệm';
  }
  // ... more patterns
}
```

**After (using ErrorUtils):**
```dart
import 'package:mobile/core/utils/error_utils.dart';

Widget _buildErrorState(Object error) {
  final displayMessage = ErrorUtils.formatForUser(error);
  
  return Center(
    child: Column(
      children: [
        Icon(Icons.error_outline, size: 64, color: AppColors.error),
        Text(displayMessage),
        if (ErrorUtils.isNetworkError(error))
          ElevatedButton(
            onPressed: _retry,
            child: Text('Thử lại'),
          ),
      ],
    ),
  );
}
```

## Supported Error Types

### Network Errors
- `SocketException` → "Không có kết nối mạng. Vui lòng kiểm tra lại."
- `NetworkException` → "Không có kết nối mạng. Vui lòng kiểm tra lại."
- `TimeoutException` → "Kết nối quá chậm. Vui lòng thử lại."

### Authentication Errors
- `AuthException` → "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại."
- HTTP 401 → "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại."

### HTTP Status Codes
- 400 → "Yêu cầu không hợp lệ."
- 403 → "Bạn không có quyền truy cập."
- 404 → "Không tìm thấy dữ liệu."
- 500 → "Lỗi máy chủ. Vui lòng thử lại sau."
- 502 → "Máy chủ tạm thời quá tải. Vui lòng thử lại sau."
- 503 → "Dịch vụ tạm thời không khả dụng. Vui lòng thử lại sau."

### Custom Exceptions
- `NotFoundException` → "Không tìm thấy dữ liệu."
- `ForbiddenException` → "Bạn không có quyền truy cập. Vui lòng liên hệ quản trị viên."
- `ServerException` → Maps to appropriate HTTP status code message

### Default
- Any other error → "Đã xảy ra lỗi. Vui lòng thử lại."

## Integration with Riverpod

```dart
@riverpod
class QuizNotifier extends _$QuizNotifier {
  @override
  Future<QuizState> build(String motifId) async {
    try {
      final quiz = await ref.read(quizRepositoryProvider).getQuiz(motifId);
      return QuizState.loaded(quiz);
    } catch (e, stack) {
      debugPrint('Error loading quiz: $e');
      
      // Return user-friendly error message
      return QuizState.error(ErrorUtils.formatForUser(e));
    }
  }
}
```

## API

### `formatForUser(dynamic error) → String`
Converts any error into a user-friendly Vietnamese message.

**Parameters:**
- `error`: Can be an Exception, Error, String, or any object

**Returns:** Vietnamese error message suitable for display to users

### `isNetworkError(dynamic error) → bool`
Checks if the error is network-related.

**Parameters:**
- `error`: Any error object

**Returns:** `true` if error is network-related, `false` otherwise

## Benefits

1. **Consistency**: All error messages follow the same Vietnamese formatting
2. **Centralized**: Single source of truth for error message mapping
3. **Type-safe**: Handles both typed exceptions and string errors
4. **User-friendly**: Technical errors converted to readable Vietnamese
5. **Easy refactoring**: Replace scattered error formatting logic with single utility

## Migration Guide

To migrate existing code:

1. Import ErrorUtils:
   ```dart
   import 'package:mobile/core/utils/error_utils.dart';
   ```

2. Replace local error formatting methods:
   ```dart
   // Old
   final message = _formatErrorForUser(error.toString());
   
   // New
   final message = ErrorUtils.formatForUser(error);
   ```

3. Remove duplicate error handling logic across screens

## Testing

```dart
void main() {
  test('formatForUser handles SocketException', () {
    final error = SocketException('Connection failed');
    expect(
      ErrorUtils.formatForUser(error),
      'Không có kết nối mạng. Vui lòng kiểm tra lại.',
    );
  });
  
  test('isNetworkError returns true for network errors', () {
    expect(ErrorUtils.isNetworkError(SocketException('')), true);
    expect(ErrorUtils.isNetworkError(NetworkException('')), true);
    expect(ErrorUtils.isNetworkError(TimeoutException('')), true);
    expect(ErrorUtils.isNetworkError(Exception('Other')), false);
  });
}
```

