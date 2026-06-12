/**
 * Network Utilities
 * Retry logic and network-aware request handling
 *
 * Inspired by mobile implementation: mobile/lib/core/network/retry_service.dart
 */

interface ErrorLike {
  name?: string;
  status?: number;
  message?: string;
}

export interface RetryOptions {
  maxRetries?: number;
  initialDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
  shouldRetry?: (error: unknown) => boolean;
  networkTimeoutMs?: number;
}

/**
 * Check if user is online
 */
export function isOnline(): boolean {
  return navigator.onLine;
}

/**
 * Wait for network connection
 */
export function waitForNetwork(timeoutMs = 30000): Promise<boolean> {
  return new Promise((resolve, reject) => {
    if (navigator.onLine) {
      resolve(true);
      return;
    }

    const timeout = setTimeout(() => {
      window.removeEventListener("online", handleOnline);
      reject(new Error("Network timeout"));
    }, timeoutMs);

    const handleOnline = () => {
      clearTimeout(timeout);
      window.removeEventListener("online", handleOnline);
      resolve(true);
    };

    window.addEventListener("online", handleOnline);
  });
}

/**
 * Retry a failed request with exponential backoff
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  options: RetryOptions = {},
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelayMs = 1000,
    maxDelayMs = 10000,
    backoffMultiplier = 2,
    shouldRetry = (error: unknown) => {
      // Retry on network errors or 5xx errors
      const err = error as ErrorLike;
      if (err.name === "ApiError") {
        const status = err.status ?? 0;
        return status >= 500 && status < 600;
      }
      return Boolean(
        err.message?.includes("fetch") || err.message?.includes("network"),
      );
    },
  } = options;

  let lastError: unknown;
  let delay = initialDelayMs;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Check network before retrying
      if (attempt > 0 && !navigator.onLine) {
        await waitForNetwork();
      }

      const result = await requestFn();
      return result;
    } catch (error) {
      lastError = error;

      // Don't retry if we've exhausted retries or error is not retryable
      if (attempt >= maxRetries || !shouldRetry(error)) {
        throw error;
      }

      // Wait before retrying with exponential backoff
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * backoffMultiplier, maxDelayMs);

      if (process.env.NODE_ENV === "development") {
        console.log(
          `Retrying request (attempt ${attempt + 1}/${maxRetries})...`,
        );
      }
    }
  }

  throw lastError;
}

/**
 * Execute request with network awareness
 * Automatically waits for network if offline and retries on failure
 */
export async function executeWithNetworkRetry<T>(
  requestFn: () => Promise<T>,
  options: RetryOptions = {},
): Promise<T> {
  // If offline, wait for network
  if (!navigator.onLine) {
    await waitForNetwork(options.networkTimeoutMs);
  }

  // Execute with retry logic
  return retryRequest(requestFn, options);
}

/**
 * Create a network-aware version of an API function
 * Usage: const safeFetch = withNetworkRetry(fetch)
 */
export function withNetworkRetry<TArgs extends unknown[], TReturn>(
  fn: (...args: TArgs) => Promise<TReturn>,
  options: RetryOptions = {},
): (...args: TArgs) => Promise<TReturn> {
  return async (...args: TArgs) => {
    return executeWithNetworkRetry(() => fn(...args), options);
  };
}
