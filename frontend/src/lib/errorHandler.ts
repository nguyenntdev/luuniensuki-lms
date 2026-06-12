/**
 * Error Handler Utility
 * Centralized error handling with user-friendly Vietnamese messages
 *
 * Inspired by mobile implementation: mobile/lib/core/errors/error_handler.dart
 */

export const ErrorMessages = {
  // Network errors
  NETWORK_ERROR: "Không có kết nối mạng. Vui lòng kiểm tra và thử lại.",
  TIMEOUT_ERROR: "Kết nối quá chậm. Vui lòng thử lại.",
  SERVER_ERROR: "Lỗi máy chủ. Vui lòng thử lại sau.",

  // Auth errors
  UNAUTHORIZED: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  FORBIDDEN: "Bạn không có quyền truy cập tài nguyên này.",

  // Resource errors
  NOT_FOUND: "Không tìm thấy tài nguyên.",
  CONFLICT: "Dữ liệu bị xung đột. Vui lòng thử lại.",

  // Validation errors
  VALIDATION_ERROR: "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.",

  // Rate limiting
  RATE_LIMIT: "Quá nhiều yêu cầu. Vui lòng thử lại sau.",

  // Generic
  UNKNOWN_ERROR: "Đã xảy ra lỗi. Vui lòng thử lại.",
} as const;

/** Loosely-typed error shape covering ApiError and native Error fields. */
interface ErrorLike {
  name?: string;
  status?: number;
  message?: string;
  stack?: string;
}

/** Minimal toast surface used here (compatible with react-hot-toast). */
interface ToastLike {
  error: (message: string, options?: Record<string, unknown>) => void;
}

/**
 * Get user-friendly error message based on error type
 */
export function getErrorMessage(error: unknown): string {
  if (!error) return ErrorMessages.UNKNOWN_ERROR;

  const err = error as ErrorLike;

  // Handle ApiError from api.ts
  if (err.name === "ApiError") {
    const status = err.status;

    switch (status) {
      case 400:
        return err.message || ErrorMessages.VALIDATION_ERROR;
      case 401:
        return ErrorMessages.UNAUTHORIZED;
      case 403:
        return ErrorMessages.FORBIDDEN;
      case 404:
        return ErrorMessages.NOT_FOUND;
      case 409:
        return ErrorMessages.CONFLICT;
      case 422:
        return err.message || ErrorMessages.VALIDATION_ERROR;
      case 429:
        return ErrorMessages.RATE_LIMIT;
      case 500:
      case 502:
      case 503:
      case 504:
        return ErrorMessages.SERVER_ERROR;
      default:
        return err.message || ErrorMessages.UNKNOWN_ERROR;
    }
  }

  // Handle network errors
  if (err.message?.includes("fetch") || err.message?.includes("network")) {
    return ErrorMessages.NETWORK_ERROR;
  }

  // Handle timeout errors
  if (err.message?.includes("timeout")) {
    return ErrorMessages.TIMEOUT_ERROR;
  }

  // Return error message or fallback
  return err.message || ErrorMessages.UNKNOWN_ERROR;
}

/**
 * Show error toast notification
 * Uses react-hot-toast which is already in package.json
 */
export function showErrorToast(error: unknown, toast?: ToastLike): void {
  const message = getErrorMessage(error);

  if (toast) {
    toast.error(message, {
      duration: 4000,
      position: "bottom-center",
      style: {
        background: "hsl(var(--destructive))",
        color: "hsl(var(--destructive-foreground))",
        borderRadius: "12px",
        padding: "16px",
      },
      icon: "⚠️",
    });
  }

  // Log in development
  if (process.env.NODE_ENV === "development") {
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.error("Error:", error);
    const stack = (error as ErrorLike)?.stack;
    if (stack) {
      console.error("Stack:", stack);
    }
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  }
}

/**
 * Error boundary error handler
 */
export function handleError(error: unknown, errorInfo?: unknown): void {
  if (process.env.NODE_ENV === "development") {
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.error("Error Boundary caught:", error);
    console.error("Error Info:", errorInfo);
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  }
}
