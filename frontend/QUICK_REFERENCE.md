# Quick Reference Guide - New Utilities

## 🎯 NetworkStatusIndicator

### What it does
Automatically shows a red banner when user goes offline, hides when back online.

### Already integrated
No action needed - already wrapped around the app in `layout.jsx`.

### Customization
Edit `src/components/NetworkStatusIndicator.jsx` to change:
- Banner color (change `bg-destructive` class)
- Message text (currently: "Không có kết nối mạng")
- Animation duration (change `duration-300` class)

---

## 🛠️ Error Handler

### Basic Usage
```javascript
import { showErrorToast } from "@/lib/errorHandler";
import toast from "react-hot-toast";

try {
  const result = await someApiCall();
} catch (error) {
  showErrorToast(error, toast);
}
```

### Custom Error Messages
```javascript
import { getErrorMessage } from "@/lib/errorHandler";

const errorMsg = getErrorMessage(error);
console.log(errorMsg); // Vietnamese message
```

### Error Message Examples
| Error Type | Vietnamese Message |
|-----------|-------------------|
| Network | "Không có kết nối mạng. Vui lòng kiểm tra và thử lại." |
| 401 | "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại." |
| 404 | "Không tìm thấy tài nguyên." |
| 500 | "Lỗi máy chủ. Vui lòng thử lại sau." |

---

## 🔄 Network Retry Utilities

### Simple Retry
```javascript
import { retryRequest } from "@/lib/networkUtils";

const data = await retryRequest(
  () => fetch("/api/data").then(r => r.json()),
  { maxRetries: 3 }
);
```

### Network-Aware Execution
```javascript
import { executeWithNetworkRetry } from "@/lib/networkUtils";

// Will wait if offline, then retry on failure
const data = await executeWithNetworkRetry(
  () => apiCall(),
  { 
    maxRetries: 3,
    initialDelayMs: 1000 
  }
);
```

### Wrap an API Function
```javascript
import { withNetworkRetry } from "@/lib/networkUtils";
import { getBadges } from "@/lib/api";

const safeGetBadges = withNetworkRetry(getBadges, {
  maxRetries: 3
});

// Use like normal function
const badges = await safeGetBadges();
```

### Custom Retry Logic
```javascript
import { retryRequest } from "@/lib/networkUtils";

const data = await retryRequest(
  () => apiCall(),
  {
    maxRetries: 5,
    initialDelayMs: 500,
    maxDelayMs: 5000,
    backoffMultiplier: 2,
    shouldRetry: (error) => {
      // Only retry on specific errors
      return error.status === 503;
    }
  }
);
```

---

## 🎨 Example: Complete API Call

### Before (Basic)
```javascript
const [data, setData] = useState([]);
const [error, setError] = useState(null);

useEffect(() => {
  async function load() {
    try {
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err.message);
    }
  }
  load();
}, []);
```

### After (Enhanced)
```javascript
import { retryRequest } from "@/lib/networkUtils";
import { showErrorToast } from "@/lib/errorHandler";
import toast from "react-hot-toast";

const [data, setData] = useState([]);
const [error, setError] = useState(null);

useEffect(() => {
  async function load() {
    try {
      const result = await retryRequest(
        () => apiCall(),
        { maxRetries: 3 }
      );
      setData(result);
    } catch (err) {
      setError(err.message);
      showErrorToast(err, toast);
    }
  }
  load();
}, []);
```

---

## 🧩 Integration Patterns

### Pattern 1: Simple Page
```javascript
"use client";

import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { showErrorToast } from "@/lib/errorHandler";
import { myApiCall } from "@/lib/api";

export default function MyPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await myApiCall();
        setData(result);
      } catch (error) {
        showErrorToast(error, toast);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div>Loading...</div>;
  return <div>{/* render data */}</div>;
}
```

### Pattern 2: With Retry Logic
```javascript
"use client";

import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { retryRequest } from "@/lib/networkUtils";
import { showErrorToast } from "@/lib/errorHandler";
import { myApiCall } from "@/lib/api";

export default function MyPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await retryRequest(
          () => myApiCall(),
          { maxRetries: 3, initialDelayMs: 1000 }
        );
        setData(result);
      } catch (error) {
        showErrorToast(error, toast);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div>Loading...</div>;
  return <div>{/* render data */}</div>;
}
```

### Pattern 3: Form Submission
```javascript
"use client";

import { useState } from "react";
import toast from "react-hot-toast";
import { showErrorToast } from "@/lib/errorHandler";
import { submitForm } from "@/lib/api";

export default function MyForm() {
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);

    try {
      const result = await submitForm(formData);
      toast.success("Thành công!");
      // Handle success
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button disabled={submitting}>
        {submitting ? "Đang gửi..." : "Gửi"}
      </button>
    </form>
  );
}
```

---

## 🎯 Best Practices

### DO ✅
- Use `showErrorToast` for all user-facing errors
- Wrap critical API calls with `retryRequest`
- Let `NetworkStatusIndicator` handle offline state
- Keep retry counts reasonable (3-5 max)
- Test offline scenarios

### DON'T ❌
- Don't retry on 4xx errors (except 429)
- Don't show technical error messages to users
- Don't retry forever (set max retries)
- Don't ignore errors silently
- Don't retry on authentication errors

---

## 🔍 Debugging Tips

### Check Network Status
```javascript
import { isOnline } from "@/lib/networkUtils";

console.log("Online:", isOnline()); // true/false
```

### Monitor Retries
Retries are logged in development mode:
```
Retrying request (attempt 1/3)...
Retrying request (attempt 2/3)...
```

### Test Offline Mode
1. Open DevTools
2. Go to Network tab
3. Set throttling to "Offline"
4. Try actions that use API
5. Set back to "No throttling"

### View Error Details
Errors are logged in development with full stack traces:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Error: ApiError {...}
Stack: ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📚 Related Files

- `src/components/NetworkStatusIndicator.jsx` - Network status UI
- `src/lib/errorHandler.js` - Error handling utilities
- `src/lib/networkUtils.js` - Retry and network utilities
- `src/lib/api.js` - Existing API layer
- `src/app/layout.jsx` - Root layout with integrations

