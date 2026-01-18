import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../theme/app_colors.dart';
import 'exceptions.dart';
import 'failures.dart';
import 'error_messages.dart';

part 'error_handler.g.dart';

class ErrorHandler {
  final BuildContext? context;

  ErrorHandler({this.context});

  void handleException(Object error, StackTrace stackTrace) {
    logError(error, stackTrace);

    final errorMessage = _getErrorMessage(error);

    if (context != null && context!.mounted) {
      _showErrorSnackBar(context!, errorMessage);
    }
  }

  void handleFailure(Failure failure) {
    logError(failure, StackTrace.current);

    final errorMessage = failure.vietnameseMessage;

    if (context != null && context!.mounted) {
      _showErrorSnackBar(context!, errorMessage);
    }
  }

  void showError(String message, {bool isWarning = false}) {
    if (context != null && context!.mounted) {
      _showErrorSnackBar(context!, message, isWarning: isWarning);
    }
  }

  void logError(Object error, StackTrace stackTrace) {
    if (kDebugMode) {
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      print('Error: $error');
      print('StackTrace: $stackTrace');
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    }
  }

  String _getErrorMessage(Object error) {
    if (error is ServerException) {
      return ErrorMessages.getErrorMessage(
        error.code,
        statusCode: error.statusCode,
      );
    } else if (error is NetworkException) {
      return ErrorMessages.getErrorMessage('NETWORK_ERROR');
    } else if (error is CacheException) {
      return ErrorMessages.getErrorMessage('CACHE_ERROR');
    } else if (error is AuthException) {
      return ErrorMessages.getErrorMessage(error.code);
    } else if (error is ValidationException) {
      return ErrorMessages.getErrorMessage('VALIDATION_ERROR');
    } else if (error is TimeoutException) {
      return ErrorMessages.getErrorMessage('TIMEOUT');
    } else if (error is ForbiddenException) {
      return ErrorMessages.getErrorMessage('PERMISSION_DENIED');
    } else if (error is NotFoundException) {
      return ErrorMessages.getErrorMessage('NOT_FOUND');
    }

    return ErrorMessages.getErrorMessage(null);
  }

  void _showErrorSnackBar(
    BuildContext context,
    String message, {
    bool isWarning = false,
  }) {
    final messenger = ScaffoldMessenger.of(context);

    messenger.clearSnackBars();

    messenger.showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              isWarning ? Icons.warning_rounded : Icons.error_outline_rounded,
              color: AppColors.white,
              size: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(
                  color: AppColors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
        backgroundColor: isWarning ? AppColors.warning : AppColors.error,
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        duration: const Duration(seconds: 4),
        elevation: 4,
      ),
    );
  }
}

@Riverpod(keepAlive: true)
ErrorHandler errorHandler(Ref ref) {
  return ErrorHandler();
}

@riverpod
ErrorHandler errorHandlerWithContext(Ref ref, BuildContext context) {
  return ErrorHandler(context: context);
}
