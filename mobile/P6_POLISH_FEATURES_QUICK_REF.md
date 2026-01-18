# P6 Polish Features - Quick Reference

## 1. Network Status Indicator

### Import
```dart
import 'package:luuniensuki_lms/shared/widgets/network_status_indicator.dart';
```

### Usage
```dart
// Wrap your app root
NetworkStatusIndicator(
  child: MaterialApp(...),
)
```

### What it does
- Shows red banner with "Không có kết nối mạng" when offline
- Auto-hides when connection restored
- Smooth slide animations

---

## 2. Error Handler

### Import
```dart
import 'package:luuniensuki_lms/core/errors/error_handler.dart';
```

### Basic Usage
```dart
// In a widget with BuildContext
final errorHandler = ref.watch(errorHandlerWithContextProvider(context));

// Handle failure
errorHandler.handleFailure(failure);

// Handle exception
try {
  // code
} catch (e, st) {
  errorHandler.handleException(e, st);
}

// Show custom message
errorHandler.showError('Lỗi tùy chỉnh', isWarning: true);
```

### Without Context
```dart
final errorHandler = ref.read(errorHandlerProvider);
errorHandler.logError(error, stackTrace);
```

---

## 3. Vietnamese Error Messages

### Import
```dart
import 'package:luuniensuki_lms/core/errors/error_messages.dart';
```

### Get Message from Error Code
```dart
final message = ErrorMessages.getErrorMessage('NETWORK_ERROR');
// "Không có kết nối mạng. Vui lòng kiểm tra kết nối internet của bạn."
```

### Get Message from HTTP Status
```dart
final message = ErrorMessages.getHttpStatusMessage(404);
// "Không tìm thấy tài nguyên."
```

### Get Validation Message
```dart
final message = ErrorMessages.getValidationMessage('email_invalid');
// "Email không hợp lệ."
```

### Use with Failures
```dart
final failure = NetworkFailure();
print(failure.vietnameseMessage); // Automatic Vietnamese translation
```

---

## 4. Common Error Messages

| Code | Vietnamese Message |
|------|-------------------|
| `NETWORK_ERROR` | Không có kết nối mạng. Vui lòng kiểm tra kết nối internet của bạn. |
| `SESSION_EXPIRED` | Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại. |
| `INVALID_CREDENTIALS` | Email hoặc mật khẩu không đúng. |
| `PERMISSION_DENIED` | Bạn không có quyền truy cập. |
| `NOT_FOUND` | Không tìm thấy tài nguyên. |
| `TIMEOUT` | Yêu cầu đã hết thời gian chờ. |
| `SERVER_ERROR` | Lỗi máy chủ. Vui lòng thử lại sau. |

---

## 5. HTTP Status Codes

| Code | Vietnamese Message |
|------|-------------------|
| 400 | Yêu cầu không hợp lệ. |
| 401 | Bạn chưa đăng nhập. |
| 403 | Bạn không có quyền truy cập. |
| 404 | Không tìm thấy tài nguyên. |
| 408 | Yêu cầu đã hết thời gian chờ. |
| 500 | Lỗi máy chủ nội bộ. |
| 503 | Dịch vụ tạm thời không khả dụng. |

---

## 6. Example: Complete Error Handling in Repository

```dart
class MyRepository {
  final Ref _ref;
  
  Future<Either<Failure, Data>> fetchData() async {
    try {
      // Check network
      final networkInfo = _ref.read(networkInfoProvider);
      if (!await networkInfo.isConnected) {
        return Left(NetworkFailure());
      }
      
      // Make API call
      final response = await api.getData();
      return Right(response);
      
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        code: e.code,
        statusCode: e.statusCode,
      ));
    } on NetworkException catch (e) {
      return Left(NetworkFailure());
    } catch (e, st) {
      final errorHandler = _ref.read(errorHandlerProvider);
      errorHandler.logError(e, st);
      return Left(UnexpectedFailure());
    }
  }
}
```

---

## 7. Example: Showing Errors in UI

```dart
class MyScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final errorHandler = ref.watch(errorHandlerWithContextProvider(context));
    final dataAsync = ref.watch(dataProvider);
    
    return dataAsync.when(
      data: (data) => DataView(data),
      loading: () => LoadingView(),
      error: (error, stack) {
        // Show error to user
        if (error is Failure) {
          errorHandler.handleFailure(error);
        } else {
          errorHandler.handleException(error, stack);
        }
        return ErrorView();
      },
    );
  }
}
```

---

## 8. Testing Network Status

```dart
// To test offline behavior:
// 1. Enable airplane mode on device/emulator
// 2. Should see red banner: "Không có kết nối mạng"
// 3. Disable airplane mode
// 4. Banner should slide up and disappear
```

---

## Files Reference

| Feature | File Path |
|---------|-----------|
| Network Status Indicator | `lib/shared/widgets/network_status_indicator.dart` |
| Error Handler | `lib/core/errors/error_handler.dart` |
| Error Messages | `lib/core/errors/error_messages.dart` |
| Failures (updated) | `lib/core/errors/failures.dart` |
| App Icon/Splash Docs | `docs/APP_ICON_SPLASH_SCREEN.md` |

---

## Quick Commands

```bash
# Run code generation
flutter pub run build_runner build --delete-conflicting-outputs

# Format code
dart format lib/shared/widgets/network_status_indicator.dart \
            lib/core/errors/error_handler.dart \
            lib/core/errors/error_messages.dart

# Analyze code
flutter analyze
```

