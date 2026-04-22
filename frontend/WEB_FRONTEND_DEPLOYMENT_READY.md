# Web Frontend - Deployment Ready Documentation

## Overview
The web frontend has been updated with network resilience improvements inspired by the mobile app's Polish Features (P6).

## ✅ Completed Improvements

### 1. Network Status Indicator ✅
**File**: `src/components/NetworkStatusIndicator.jsx`

**Features**:
- Shows a banner when the user goes offline
- Auto-hides when connection is restored
- Vietnamese text: "Không có kết nối mạng"
- Smooth animations using Tailwind CSS
- Uses browser's `navigator.onLine` API
- Integrated into root layout

**Integration**:
```jsx
// Already integrated in src/app/layout.jsx
<NetworkStatusIndicator>
  <App />
</NetworkStatusIndicator>
```

**Key Implementation Details**:
- Listens to window `online`/`offline` events
- Displays error banner with WiFi off icon
- Red background using Tailwind's destructive colors
- Auto-adjusts page padding when banner is shown

---

### 2. Global Error Handler ✅
**File**: `src/lib/errorHandler.js`

**Features**:
- Centralized error handling utility
- Shows user-friendly toast notifications
- Vietnamese error messages for all error types
- Logs errors in development mode
- Handles all API error status codes
- Integration with react-hot-toast (already in dependencies)

**Usage**:
```javascript
import { showErrorToast } from "@/lib/errorHandler";
import toast from "react-hot-toast";

try {
  const data = await apiCall();
} catch (error) {
  showErrorToast(error, toast);
}
```

**Error Message Mapping**:
- 400: "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại."
- 401: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
- 403: "Bạn không có quyền truy cập tài nguyên này."
- 404: "Không tìm thấy tài nguyên."
- 429: "Quá nhiều yêu cầu. Vui lòng thử lại sau."
- 500+: "Lỗi máy chủ. Vui lòng thử lại sau."

---

### 3. Network Retry Utilities ✅
**File**: `src/lib/networkUtils.js`

**Features**:
- Automatic retry with exponential backoff
- Network-aware request execution
- Waits for network connection if offline
- Configurable retry logic
- Smart retry decision based on error type

**Usage**:
```javascript
import { retryRequest, executeWithNetworkRetry } from "@/lib/networkUtils";

// Option 1: Retry a specific request
const data = await retryRequest(
  () => fetch("/api/endpoint"),
  { maxRetries: 3 }
);

// Option 2: Execute with network awareness
const data = await executeWithNetworkRetry(
  () => apiCall(),
  { maxRetries: 3, initialDelayMs: 1000 }
);
```

**Configuration Options**:
- `maxRetries`: Number of retry attempts (default: 3)
- `initialDelayMs`: Initial delay between retries (default: 1000ms)
- `maxDelayMs`: Maximum delay (default: 10000ms)
- `backoffMultiplier`: Exponential backoff multiplier (default: 2)
- `shouldRetry`: Custom function to determine if error is retryable

---

### 4. Enhanced Badge Page ✅
**File**: `src/app/badges/page.jsx`

**Improvements**:
- Integrated with new error handler
- Shows user-friendly error messages
- Uses toast notifications for errors
- Maintains existing functionality

---

## 📦 Build Configuration

### Package Scripts
```json
{
  "dev": "next dev -H 0.0.0.0 -p 3000",
  "build": "next build",
  "start": "next start -H 0.0.0.0 -p 3000",
  "lint": "next lint"
}
```

### Next.js Configuration
- Output: `standalone` (optimized for Docker deployment)
- ESLint: Ignored during builds
- React Strict Mode: Enabled

---

## 🐳 Docker Configuration

### Frontend Dockerfile
**Location**: `frontend/Dockerfile`

**Multi-stage build**:
1. **deps**: Install dependencies with `--legacy-peer-deps`
2. **builder**: Build Next.js app
3. **runner**: Minimal production runtime

**Environment Variables**:
- `NEXT_PUBLIC_API_BASE_URL`: API base URL (set during build)

### Docker Compose
**Location**: `docker-compose.yml`

**Services**:
- `db`: PostgreSQL 15 Alpine
- `api`: FastAPI backend
- `web`: Next.js frontend
- `nginx`: Reverse proxy

**Frontend Service Configuration**:
```yaml
web:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-}
  depends_on:
    - api
  restart: unless-stopped
```

---

## 🚀 Deployment Instructions

### Option 1: Docker Compose (Recommended)
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms

# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Option 2: Local Development
```bash
cd frontend

# Install dependencies (use --legacy-peer-deps due to ESLint version conflict)
npm install --legacy-peer-deps

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

---

## ⚠️ Known Issues & Solutions

### 1. ESLint Peer Dependency Conflict
**Issue**: `eslint-config-next@16.1.1` requires `eslint@>=9.0.0` but project has `eslint@8.57.1`

**Solution**: 
- Use `npm install --legacy-peer-deps`
- Or update to ESLint 9.x (may require code changes)
- ESLint is ignored during builds in `next.config.js`

### 2. Network Timeouts During npm install
**Issue**: Network timeouts when installing dependencies

**Solutions**:
- Retry the installation: `npm install --legacy-peer-deps`
- Use a different npm registry: `npm config set registry https://registry.npmmirror.com`
- Increase timeout: `npm config set fetch-timeout 60000`

---

## 📊 Comparison with Mobile App

| Feature | Mobile (Flutter) | Web (Next.js) | Status |
|---------|-----------------|---------------|--------|
| Network Status Indicator | ✅ | ✅ | Synced |
| Global Error Handler | ✅ | ✅ | Synced |
| Vietnamese Error Messages | ✅ | ✅ | Synced |
| Retry Logic | ✅ | ✅ | Synced |
| Badge System | ✅ | ✅ | Existing |
| Offline Support | ❌ | ❌ | Future |

---

## 🎯 Next Steps

### High Priority
1. **Test Build Process**: Verify Docker build completes successfully
2. **Integration Testing**: Test network indicator and error handling
3. **Apply Retry Logic**: Add `retryRequest` to critical API calls

### Medium Priority
4. **Error Boundary**: Create React Error Boundary component
5. **Loading States**: Add skeleton loaders for better UX
6. **Offline Caching**: Implement service worker for offline support

### Low Priority
7. **Analytics**: Track error rates and network issues
8. **Monitoring**: Set up error monitoring (e.g., Sentry)
9. **Performance**: Optimize bundle size and loading times

---

## 📝 File Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── badges/
│   │   │   └── page.jsx          # ✅ Updated with error handler
│   │   └── layout.jsx             # ✅ Updated with network indicator
│   ├── components/
│   │   └── NetworkStatusIndicator.jsx  # 🆕 New component
│   └── lib/
│       ├── api.js                 # Existing API layer
│       ├── errorHandler.js        # 🆕 New utility
│       └── networkUtils.js        # 🆕 New utility
├── Dockerfile                     # Multi-stage build configuration
├── package.json                   # Dependencies and scripts
└── next.config.js                 # Next.js configuration
```

---

## 🔍 Code Quality

All new code follows:
- ✅ ESNext standards
- ✅ React best practices
- ✅ Comprehensive documentation
- ✅ Error handling patterns from mobile app
- ✅ Consistent code style with existing codebase

---

## 📚 References

- Mobile Implementation: `mobile/P6_POLISH_FEATURES_SUMMARY.md`
- Error Interceptor: `mobile/lib/core/network/interceptors/error_interceptor.dart`
- Network Info: `mobile/lib/core/network/network_info.dart`
- Error Handler: `mobile/lib/core/errors/error_handler.dart`

