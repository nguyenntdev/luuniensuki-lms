# Web Frontend - Pre-Deployment Checklist

## 🔍 Pre-Deployment Verification

### 1. Code Quality ✅
- [x] New components created with proper documentation
- [x] Error handling patterns match mobile implementation
- [x] Vietnamese error messages for all scenarios
- [x] Code follows React best practices
- [x] All imports are correct

### 2. Dependencies ⚠️
- [ ] Run `npm install --legacy-peer-deps`
- [ ] Verify no critical security vulnerabilities
- [ ] Check for outdated packages (optional)

### 3. Build Process 🔄
- [ ] Test build: `npm run build`
- [ ] Verify standalone output in `.next/standalone`
- [ ] Check for build warnings/errors
- [ ] Test production server: `npm start`

### 4. Docker Build 🐳
- [ ] Build frontend image: `docker-compose build web`
- [ ] Verify image size is reasonable
- [ ] Test container startup
- [ ] Check container logs for errors

### 5. Integration Testing 🧪
- [ ] Test network status indicator (go offline/online)
- [ ] Verify error toasts appear correctly
- [ ] Check badge page loads properly
- [ ] Test error handling on failed API calls
- [ ] Verify Vietnamese error messages display

### 6. Environment Variables 🔐
- [ ] Set `NEXT_PUBLIC_API_BASE_URL` in .env or docker-compose.yml
- [ ] Verify API base URL is correct for deployment
- [ ] Check other environment variables

---

## 🚀 Deployment Steps

### Step 1: Install Dependencies
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/frontend
npm install --legacy-peer-deps
```

### Step 2: Test Local Build
```bash
npm run build
npm start
# Visit http://localhost:3000
```

### Step 3: Docker Build
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
docker-compose build web
```

### Step 4: Deploy with Docker Compose
```bash
docker-compose up -d
```

### Step 5: Verify Deployment
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f web

# Test endpoints
curl http://localhost:80
```

---

## 🧪 Testing Checklist

### Manual Testing

#### Network Status Indicator
- [ ] Open DevTools → Network tab
- [ ] Set throttling to "Offline"
- [ ] Verify red banner appears: "Không có kết nối mạng"
- [ ] Set throttling back to "No throttling"
- [ ] Verify banner disappears smoothly

#### Error Handling
- [ ] Navigate to `/badges` page
- [ ] Trigger an API error (e.g., disconnect backend)
- [ ] Verify toast notification appears
- [ ] Check error message is in Vietnamese
- [ ] Verify error icon is displayed

#### Badge System
- [ ] Login as a user
- [ ] Navigate to `/badges`
- [ ] Verify all badges load correctly
- [ ] Check earned badges have checkmark
- [ ] Verify unearned badges are grayed out
- [ ] Test loading states

#### Responsive Design
- [ ] Test on mobile viewport (375px)
- [ ] Test on tablet viewport (768px)
- [ ] Test on desktop viewport (1920px)
- [ ] Verify network banner doesn't break layout

---

## 📊 Performance Checks

### Build Metrics
- [ ] Bundle size is acceptable (< 500KB for main JS)
- [ ] No circular dependencies
- [ ] Tree-shaking is working
- [ ] Images are optimized

### Runtime Metrics
- [ ] First Contentful Paint < 2s
- [ ] Time to Interactive < 3s
- [ ] No layout shifts (CLS < 0.1)
- [ ] No memory leaks

---

## 🔒 Security Checks

### Code Security
- [ ] No hardcoded secrets or API keys
- [ ] Environment variables used correctly
- [ ] No console.log in production (except errors)
- [ ] API calls use HTTPS in production

### Dependencies
- [ ] Run `npm audit`
- [ ] Fix critical vulnerabilities
- [ ] Update vulnerable packages if possible

---

## 🐛 Troubleshooting Guide

### Issue: npm install fails
**Symptoms**: ESLint peer dependency conflict

**Solution**:
```bash
npm install --legacy-peer-deps
```

### Issue: Build fails with module not found
**Symptoms**: Cannot find module '@/lib/errorHandler'

**Solution**:
- Verify file exists at correct path
- Check jsconfig.json has correct path mapping
- Restart dev server

### Issue: Network indicator doesn't show
**Symptoms**: No banner when going offline

**Solution**:
- Check component is imported in layout.jsx
- Verify window.addEventListener is working
- Check Tailwind classes are compiled

### Issue: Toast notifications not appearing
**Symptoms**: Errors don't show toast

**Solution**:
- Verify react-hot-toast is installed
- Check Toaster component is in layout
- Import toast correctly: `import toast from "react-hot-toast"`

### Issue: Docker build fails
**Symptoms**: npm install fails in Docker

**Solution**:
- Check Dockerfile uses `--legacy-peer-deps`
- Verify network connectivity in Docker
- Try building with `--no-cache`

### Issue: API calls fail after deployment
**Symptoms**: All API calls return errors

**Solution**:
- Check `NEXT_PUBLIC_API_BASE_URL` is set correctly
- Verify nginx is routing correctly
- Check backend service is running
- Test API directly: `curl http://localhost:8000/api/v1/health`

---

## 📝 Post-Deployment Tasks

### Immediate
- [ ] Monitor error logs for 1 hour
- [ ] Check user-facing errors
- [ ] Verify all pages load correctly
- [ ] Test critical user flows

### First 24 Hours
- [ ] Monitor server resources (CPU, memory)
- [ ] Check error rates in logs
- [ ] Gather user feedback
- [ ] Watch for network-related issues

### First Week
- [ ] Analyze error patterns
- [ ] Optimize based on metrics
- [ ] Plan next improvements
- [ ] Update documentation

---

## 🎯 Success Criteria

### Must Have ✅
- [ ] All pages load without errors
- [ ] Network indicator works correctly
- [ ] Error messages are user-friendly
- [ ] Badge system functions properly
- [ ] Docker deployment succeeds

### Should Have ✅
- [ ] Error toasts appear for all failures
- [ ] Vietnamese messages display correctly
- [ ] Retry logic works for network errors
- [ ] Loading states are smooth

### Nice to Have 🎁
- [ ] Performance metrics are good
- [ ] No console errors in production
- [ ] Accessibility score > 90
- [ ] SEO score > 90

---

## 📞 Support

### Documentation
- Main docs: `WEB_FRONTEND_DEPLOYMENT_READY.md`
- Mobile reference: `mobile/P6_POLISH_FEATURES_SUMMARY.md`
- API docs: Backend README

### Key Files to Check if Issues Occur
1. `src/components/NetworkStatusIndicator.jsx`
2. `src/lib/errorHandler.js`
3. `src/lib/networkUtils.js`
4. `src/app/badges/page.jsx`
5. `src/app/layout.jsx`

### Common Commands
```bash
# View logs
docker-compose logs -f web

# Restart service
docker-compose restart web

# Rebuild
docker-compose up -d --build web

# Check service health
docker-compose ps
```

