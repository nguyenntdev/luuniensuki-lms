# Báo Cáo Sửa Lỗi (Bug Fix Summary)

**Ngày:** 2025-12-18  
**Người thực hiện:** Codex CLI + Gemini CLI (gemini-3-pro-preview)

---

## Tóm Tắt

Đã phát hiện và sửa thành công **2 lỗi nghiêm trọng** ảnh hưởng đến trải nghiệm người dùng:

1. ✅ **Lỗi ảnh không hiển thị** - Tất cả thumbnail của urns và motifs không load
2. ✅ **Lỗi height 3D viewer** - 3D viewer không full height như thiết kế

---

## 1. Lỗi Ảnh Không Hiển Thị

### 📋 Mô Tả
- Tất cả ảnh thumbnail của urns và motifs không hiển thị trên trang `/explore`, `/collection`, và các trang khác
- Browser console hiển thị lỗi 404 cho các URL dạng `/assets/ban-duc-noi/...`

### 🔍 Nguyên Nhân Gốc
Volume mount trong `docker-compose.yml` (development) không đúng:

```yaml
# SAI - mount từ host path không tồn tại
- /var/www/assets:/var/www/assets:ro
```

Trong khi đó:
- Ảnh thực tế nằm ở `./ban-duc-noi/` trong project
- Database lưu thumbnail_url dạng: `/assets/ban-duc-noi/CAO%20DINH/CAO%20DINH.jpg`
- Nginx config mong đợi file ở `/var/www/assets/ban-duc-noi/`
- Nhưng `/var/www/assets/` trên host **TRỐNG**

### ✅ Cách Sửa
**File:** `docker-compose.yml`

```yaml
# ĐÚNG - mount từ project directory
- ./ban-duc-noi:/var/www/assets/ban-duc-noi:ro
```

**Lệnh thực hiện:**
```bash
# Restart nginx container để apply volume mount mới
docker compose down nginx && docker compose up -d nginx
```

### 📁 Files Đã Thay Đổi
- `docker-compose.yml` (line 56)

### ✨ Kết Quả
- ✅ Tất cả ảnh thumbnail hiển thị bình thường
- ✅ Nginx có thể serve static files từ `/var/www/assets/ban-duc-noi/`
- ✅ Đồng bộ với `docker-compose.prod.yml`

---

## 2. Lỗi Height 3D Viewer

### 📋 Mô Tả
- 3D viewer trên trang `/urns/[urnSlug]` không full height
- Có khoảng trống ở phía dưới (80px)
- Ảnh hưởng trải nghiệm xem 3D model

### 🔍 Nguyên Nhân Gốc
`body` tag trong `layout.jsx` có class `pb-20` (padding-bottom: 5rem = 80px):

```jsx
// SAI - pb-20 áp dụng cho TẤT CẢ trang
<body className="min-h-dvh bg-background text-foreground pb-20">
```

Vấn đề:
- `pb-20` được thêm cho FloatingNavbar (bottom navigation)
- Nhưng trang 3D viewer dùng `fixed inset-0` (full screen)
- Padding này gây ra khoảng trống không mong muốn

### ✅ Cách Sửa
Tạo **conditional wrapper** để chỉ apply `pb-20` cho các trang cần:

**1. Tạo file mới:** `frontend/src/components/ClientBodyWrapper.jsx`

```jsx
'use client';

import { usePathname } from 'next/navigation';

export default function ClientBodyWrapper({ children }) {
  const pathname = usePathname();
  // Check if current path is a urns page
  const isUrnPage = pathname?.startsWith('/urns/');

  return (
    <div className={isUrnPage ? "" : "pb-20"}>
      {children}
    </div>
  );
}
```

**2. Sửa file:** `frontend/src/app/layout.jsx`

```jsx
import ClientBodyWrapper from "@/components/ClientBodyWrapper";

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body className="min-h-dvh bg-background text-foreground">
        <ClientBodyWrapper>
          <FloatingNavbar />
          <Toaster position="top-center" reverseOrder={false} />
          {children}
        </ClientBodyWrapper>
      </body>
    </html>
  );
}
```

**Lệnh thực hiện:**
```bash
# Restart web container để apply changes
docker compose restart web
```

### 📁 Files Đã Thay Đổi
- `frontend/src/components/ClientBodyWrapper.jsx` (file mới)
- `frontend/src/app/layout.jsx`

### ✨ Kết Quả
- ✅ Trang `/urns/*` có full height (không có pb-20)
- ✅ Các trang khác vẫn có pb-20 cho FloatingNavbar
- ✅ 3D viewer hiển thị đúng thiết kế

---

## Công Cụ Sử Dụng

| Công cụ | Model | Task |
|---------|-------|------|
| **Codex CLI** | gpt-5.2 | Fix image loading bug (verify docker-compose.yml) |
| **Gemini CLI** | gemini-3-pro-preview | Fix 3D viewer height bug (create ClientBodyWrapper) |

---

## Kiểm Tra Sau Khi Sửa

### ✅ Checklist
- [x] Ảnh thumbnail hiển thị trên `/explore`
- [x] Ảnh thumbnail hiển thị trên `/collection`
- [x] 3D viewer full height trên `/urns/cao-dinh`
- [x] FloatingNavbar không bị che trên các trang thường
- [x] Không có lỗi console
- [x] Docker containers chạy bình thường

### 🧪 Test Commands
```bash
# Verify nginx có thể access images
docker compose exec nginx ls -la /var/www/assets/ban-duc-noi/

# Check web container logs
docker compose logs web --tail 50

# Restart all services nếu cần
docker compose restart
```

---

## Ghi Chú

- Lỗi ảnh đã tồn tại từ trước do config development khác production
- Lỗi height là design issue - cần conditional logic cho layout
- Cả 2 lỗi đều đã được fix hoàn toàn và test thành công

