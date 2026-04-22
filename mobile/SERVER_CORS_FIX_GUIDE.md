# Server-Side Fix: CORS Headers for 3D Model Loading

## Problem
The nginx server is not sending CORS (Cross-Origin Resource Sharing) headers for 3D model files. This causes browsers to block the model loading due to security restrictions.

## Error Symptoms
- 3D models show black screen in mobile app
- Browser console shows CORS policy errors:
  ```
  Access to fetch at 'https://store.histolab.icu/...' from origin 'https://lms.histolab.icu' 
  has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
  ```

## Solution

### File to Edit
```
/etc/nginx/sites-enabled/nginx-lms-histolab.conf
```

### Current Configuration (Missing CORS)
```nginx
location ^~ /assets/models/ {
  proxy_ssl_server_name on;
  proxy_ssl_name store.histolab.icu;
  proxy_set_header Host store.histolab.icu;
  proxy_buffering off;
  proxy_pass https://store.histolab.icu/;

  access_log off;
  expires 30d;
  add_header Cache-Control "public, max-age=2592000, immutable";
  # ← CORS header is MISSING here!
}
```

### Fixed Configuration (With CORS)
```nginx
location ^~ /assets/models/ {
  proxy_ssl_server_name on;
  proxy_ssl_name store.histolab.icu;
  proxy_set_header Host store.histolab.icu;
  proxy_buffering off;
  proxy_pass https://store.histolab.icu/;

  access_log off;
  expires 30d;
  add_header Cache-Control "public, max-age=2592000, immutable";
  add_header 'Access-Control-Allow-Origin' '*' always;  # ← ADD THIS LINE
}
```

## Step-by-Step Instructions

### 1. SSH into Server
```bash
ssh user@lms.histolab.icu
# Replace 'user' with your actual username
```

### 2. Backup Current Configuration
```bash
sudo cp /etc/nginx/sites-enabled/nginx-lms-histolab.conf \
        /etc/nginx/sites-enabled/nginx-lms-histolab.conf.backup
```

### 3. Edit Configuration File
```bash
sudo nano /etc/nginx/sites-enabled/nginx-lms-histolab.conf
```

Or use vim:
```bash
sudo vim /etc/nginx/sites-enabled/nginx-lms-histolab.conf
```

### 4. Add CORS Header
Find the `location ^~ /assets/models/` block and add this line:
```nginx
add_header 'Access-Control-Allow-Origin' '*' always;
```

**Important:** Add it AFTER the existing `add_header Cache-Control` line.

### 5. Test Configuration
```bash
sudo nginx -t
```

**Expected Output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If you see errors:**
- Check syntax carefully (quotes, semicolon, etc.)
- Restore backup: `sudo cp /etc/nginx/sites-enabled/nginx-lms-histolab.conf.backup /etc/nginx/sites-enabled/nginx-lms-histolab.conf`
- Try again

### 6. Reload Nginx
```bash
sudo systemctl reload nginx
```

Or restart if reload doesn't work:
```bash
sudo systemctl restart nginx
```

### 7. Verify Nginx is Running
```bash
sudo systemctl status nginx
```

Should show: `Active: active (running)`

## Verification

### Test CORS Headers with curl
```bash
curl -I https://lms.histolab.icu/assets/models/BIHUANHOA-v1.glb
```

**Look for this line in the output:**
```
Access-Control-Allow-Origin: *
```

### Test from Browser Console
1. Open https://lms.histolab.icu
2. Open browser DevTools (F12)
3. Go to Console tab
4. Run this JavaScript:
```javascript
fetch('https://lms.histolab.icu/assets/models/BIHUANHOA-v1.glb')
  .then(r => console.log('✅ CORS Success!', r))
  .catch(e => console.error('❌ CORS Error:', e));
```

**Expected:** `✅ CORS Success!`

### Test from Mobile App
1. Open mobile app
2. Go to Collections
3. Tap any urn
4. Model should load successfully (no black screen)

## Understanding CORS Headers

### What is CORS?
Cross-Origin Resource Sharing (CORS) is a security feature in browsers that restricts web pages from making requests to a different domain than the one serving the web page.

### Why `'*'` is Safe Here
- `Access-Control-Allow-Origin: *` means "allow requests from any origin"
- This is safe for **public static content** like 3D models
- Models are meant to be viewed by all users
- No sensitive data or user information in model files

### Alternative: Specific Origins (More Restrictive)
If you want to be more restrictive:
```nginx
add_header 'Access-Control-Allow-Origin' 'https://lms.histolab.icu' always;
```

But this would block:
- Mobile app requests
- Other subdomains
- Future features

**Recommendation:** Use `'*'` for maximum compatibility.

## Troubleshooting

### Issue: nginx -t shows syntax error
**Solution:** Check for:
- Missing semicolon `;`
- Missing quotes `''`
- Extra spaces or tabs
- Make sure you're in the right `location` block

### Issue: Still getting CORS errors after reload
**Solutions:**
1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Check nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```
4. Verify configuration was actually loaded:
   ```bash
   sudo nginx -T | grep -A 10 "location.*models"
   ```

### Issue: Nginx won't reload
**Solution:**
```bash
# Check for errors
sudo journalctl -u nginx -n 50

# Force restart
sudo systemctl restart nginx
```

## Security Considerations

### Is `Access-Control-Allow-Origin: *` Secure?
**Yes, for public static assets.** The models are:
- Public content (not user-specific)
- Read-only (can't modify via CORS)
- No authentication required
- Already publicly accessible

### What CORS Does NOT Protect Against
- Direct downloads (users can always download public files)
- Hotlinking (other sites can link to your models)

### What CORS DOES Protect Against
- JavaScript running on other domains from accessing model metadata
- XMLHttpRequest/fetch API access from unauthorized origins

## Additional Notes

### Browser Caching
After fixing CORS, users may still see cached responses. The `always` parameter in the CORS header ensures it's sent even with cached responses.

### CDN Considerations
If using a CDN (like the current setup with `store.histolab.icu`), ensure:
- CDN forwards CORS headers from origin
- Or CDN adds its own CORS headers

### Testing Different Model URLs
Test all model URL patterns:
```bash
curl -I https://lms.histolab.icu/assets/models/BIHUANHOA-v1.glb
curl -I https://lms.histolab.icu/assets/models/ANOTHER-URN-v1.glb
```

All should return the CORS header.

## Rollback Plan

If issues occur after the change:

```bash
# Restore backup
sudo cp /etc/nginx/sites-enabled/nginx-lms-histolab.conf.backup \
        /etc/nginx/sites-enabled/nginx-lms-histolab.conf

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

## Questions?

Contact server admin or DevOps team with:
- This document
- Error logs from `/var/log/nginx/error.log`
- Output of `nginx -T`

